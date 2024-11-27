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

            # Menghitung IPK dan IPS
            def convert_nilai(nilai):
                if nilai >= 80:
                    return 4.0
                elif nilai >= 70:
                    return 3.0
                elif nilai >= 60:
                    return 2.0
                elif nilai >= 50:
                    return 1.0
                else:
                    return 0.0  # Untuk nilai di bawah 50, kembalikan 0

            total_sks = 0
            total_nilai = 0
            for row in results:
                sks = row[5]
                nilai = convert_nilai (row[6])
                total_sks += sks
                total_nilai += nilai * sks

            if total_sks > 0:
                ips = total_nilai / total_sks  # Menghitung IPS
                ipk = ips  # Jika hanya satu semester, dianggap sama dengan IPS

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

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

    return render_template("index.html", results=results, mahasiswa_data=mahasiswa_data, ipk=ipk, ips=ips, mahasiswa_list=mahasiswa_list, mata_kuliah_data=mata_kuliah_data)

if __name__ == "__main__":
    app.run(debug=True)