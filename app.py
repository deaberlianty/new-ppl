import os
from flask import Flask, render_template, request
import psycopg2

app = Flask(__name__)

# Ambil variabel lingkungan
user = "cahyadiiyoga"
password = "7wZcc3zufRLcGJ3khHOero34gsp01RPV"
host = "dpg-csuoak9u0jms73as3ab0-a.singapore-postgres.render.com"
port = "5432"
database = "db_mahasiswa"

# Konfigurasi database
DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{database}"

def convert_to_gpa(nilai):
    """Konversi nilai akhir (NA) ke nilai skala 0-4"""
    if nilai < 45:
        return 0.0  # E
    elif nilai < 50:
        return 1.0  # D
    elif nilai < 55:
        return 1.5  # D+
    elif nilai < 60:
        return 2.0  # C
    elif nilai < 65:
        return 2.5  # C+
    elif nilai < 75:
        return 3.0  # B
    elif nilai < 80:
        return 3.5  # B+
    elif nilai <= 100:
        return 4.0  # A
    else:
        return None  # Nilai tidak valid

def get_last_semester_and_year(nim):
    """Fungsi untuk mendapatkan semester dan tahun terakhir"""
    try:
        with psycopg2.connect(DATABASE_URL, sslmode='require') as conn:
            with conn.cursor() as cur:
                query = """
                SELECT semester, tahun 
                FROM tb_krs 
                WHERE id_mahasiswa = (SELECT id_mahasiswa FROM tb_mahasiswa WHERE nim = %s)
                ORDER BY tahun DESC, semester DESC 
                LIMIT 1
                """
                cur.execute(query, (nim,))
                last_record = cur.fetchone()

                if last_record:
                    return {
                        'semester': last_record[0],
                        'tahun': last_record[1],
                    }
                elif last_record:
                    return {
                        'semester': 1,  # Default semester jika tidak ada data
                        'tahun': 2021,  # Default tahun jika tidak ada data
                    }
                elif last_record:
                    return {
                        'semester': 1,  # Default semester jika tidak ada data
                        'tahun': 2022,  # Default tahun jika tidak ada data
                    }
                elif last_record:
                    return {
                        'semester': 2,  # Default semester jika tidak ada data
                        'tahun': 2021,  # Default tahun jika tidak ada data
                    }
                else:
                    return {
                        'semester': 2,  # Default semester jika tidak ada data
                        'tahun': 2022,  # Default tahun jika tidak ada data
                    }
    except Exception as e:
        print(f"Error fetching last semester and year: {e}")
        return {
            'semester': 1,  # Nilai default jika ada kesalahan
            'tahun': 2021,  # Nilai default jika ada kesalahan
        }

@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    mahasiswa_data = {}
    ipk = None
    ips = None
    mahasiswa_list = []
    mata_kuliah_data = []
    search_nim = request.form.get("searchNIM")  # Ambil input pencarian NIM
    search_mk = request.form.get("searchMK")  # Ambil input pencarian Mata Kuliah

    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cur = conn.cursor()

        # Pencarian Mahasiswa
        if search_nim:
            query_mahasiswa = """
            SELECT id_mahasiswa, nim, nama FROM tb_mahasiswa WHERE nim = %s
            """
            cur.execute(query_mahasiswa, (search_nim,))
            mahasiswa_list = cur.fetchall()  # Ambil data mahasiswa berdasarkan NIM
        else:
            query_all_mahasiswa = """
            SELECT id_mahasiswa, nim, nama FROM tb_mahasiswa
            """
            cur.execute(query_all_mahasiswa)
            mahasiswa_list = cur.fetchall()  # Ambil semua data mahasiswa

        # Jika ada input NIM, Semester, dan Tahun, tampilkan KHS untuk mahasiswa tersebut
        if request.method == "POST" and not search_nim:
            nim = request.form.get("nimKHS")
            semester = request.form.get("semesterKHS")
            tahun = request.form.get("tahunKHS")

            # Query untuk mendapatkan data mahasiswa berdasarkan NIM
            query_mahasiswa = """
            SELECT id_mahasiswa, nim, nama FROM tb_mahasiswa WHERE nim = %s
            """
            cur.execute(query_mahasiswa, (nim,))
            mahasiswa = cur.fetchone()

            if mahasiswa:
                mahasiswa_data['id_mahasiswa'] = mahasiswa[0]
                mahasiswa_data['nim'] = mahasiswa[1]
                mahasiswa_data['nama'] = mahasiswa[2]

        # Pencarian Mata Kuliah
        if search_mk:
            query_mata_kuliah = """
            SELECT id_mk, kode, nama_mk, sks FROM tb_mk 
            WHERE kode ILIKE %s OR nama_mk ILIKE %s
            """
            search_pattern = f"%{search_mk}%"
            cur.execute(query_mata_kuliah, (search_pattern, search_pattern))
            mata_kuliah_data = cur.fetchall()  # Ambil data mata kuliah berdasarkan pencarian
        else:
            # Query untuk menampilkan semua mata kuliah
            query_mata_kuliah = """
            SELECT id_mk, kode, nama_mk, sks FROM tb_mk
            """
            cur.execute(query_mata_kuliah)
            mata_kuliah_data = cur.fetchall()  # Ambil semua data mata kuliah
            
            # Query untuk mendapatkan detail KHS berdasarkan NIM, Semester, dan Tahun
            query_khs = """
            SELECT 
                tb_mahasiswa.nama, 
                tb_krs.semester, 
                tb_krs.tahun, 
                tb_mk.kode, 
                tb_mk.nama_mk, 
                tb_mk.sks, 
                detail_krs.nilai
            FROM 
                detail_krs 
            JOIN 
                tb_krs ON tb_krs.id_krs = detail_krs.id_krs
            JOIN 
                tb_mahasiswa ON tb_krs.id_mahasiswa = tb_mahasiswa.id_mahasiswa
            JOIN 
                tb_mk ON tb_mk.id_mk = detail_krs.id_mk
            WHERE 
                tb_mahasiswa.nim = %s AND tb_krs.semester = %s AND tb_krs.tahun = %s
            """
            cur.execute(query_khs, (nim, semester, tahun))
            results = cur.fetchall()

            # Menghitung IPS
            total_sks = 0
            total_nilai = 0
            for row in results:
                sks = row[5]
                nilai = convert_to_gpa(row[6])
                if nilai is not None:
                    total_sks += sks
                    total_nilai += nilai * sks

            if total_sks > 0:
                ips = total_nilai / total_sks  # Menghitung IPS
            else:
                ips = 0.0  # Jika tidak ada SKS, IPS adalah 0

            # Menghitung IPK
            last_semester_year = get_last_semester_and_year(nim)
            last_semester = last_semester_year['semester']
            last_tahun = last_semester_year['tahun']

            query_all_khs = """
            SELECT 
                tb_mk.sks, 
                detail_krs.nilai
            FROM 
                detail_krs 
            JOIN 
                tb_krs ON tb_krs.id_krs = detail_krs.id_krs
            JOIN 
                tb_mahasiswa ON tb_krs.id_mahasiswa = tb_mahasiswa.id_mahasiswa
            JOIN 
                tb_mk ON tb_mk.id_mk = detail_krs.id_mk
            WHERE 
                tb_mahasiswa.nim = %s AND 
                (tb_krs.semester < %s OR (tb_krs.semester = %s AND tb_krs.tahun < %s))
            """
            cur.execute(query_all_khs, (nim, last_semester, last_semester, last_tahun))
            all_results = cur.fetchall()

            total_sks_kumulatif = 0
            total_nilai_kumulatif = 0

            for row in all_results:
                sks_kumulatif = row[0]  # SKS
                nilai_kumulatif = convert_to_gpa(row[1])  # Konversi nilai ke GPA
                if nilai_kumulatif is not None:
                    total_sks_kumulatif += sks_kumulatif
                    total_nilai_kumulatif += nilai_kumulatif * sks_kumulatif

            if total_sks_kumulatif > 0:
                ipk = total_nilai_kumulatif / total_sks_kumulatif  # Menghitung IPK
            else:
                ipk = 0.0  # Jika tidak ada SKS, IPK adalah 0
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

    return render_template("index.html", results=results, mahasiswa_data=mahasiswa_data, ipk=ipk, ips=ips, mahasiswa_list=mahasiswa_list, mata_kuliah_data=mata_kuliah_data)

if __name__ == "__main__":
    app.run(debug=True)
