# SAKSIKAN - Sistem Pemesanan Tiket Pertunjukan

## Deskripsi
SAKSIKAN adalah platform pemesanan tiket pertunjukan berbasis web yang memungkinkan pengguna untuk memesan tiket pertunjukan secara online. Sistem ini dibangun menggunakan Flask framework dan menyediakan antarmuka yang mudah digunakan untuk pengguna dan admin.

## Fitur Utama
- Manajemen pengguna (registrasi, login, profil)
- Pencarian dan pemesanan tiket
- Manajemen pertunjukan dan jadwal
- Dashboard admin
- Sistem pembayaran
- Riwayat pemesanan

## Teknologi yang Digunakan
- Python 3.12
- Flask Framework
- SQLAlchemy
- SQLite Database
- HTML/CSS/JavaScript
- Bootstrap

## Persyaratan Sistem
- Python 3.12 atau lebih tinggi
- pip (Python package manager)
- Web browser modern
- Koneksi internet

## Instalasi
1. Clone repositori
   ```bash
   git clone https://github.com/username/saksikan.git
   cd saksikan
   ```

2. Buat virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. Install dependensi
   ```bash
   pip install -r requirements.txt
   ```

4. Inisialisasi database
   ```bash
   python
   >>> from app import db
   >>> db.create_all()
   ```

5. Jalankan aplikasi
   ```bash
   python app.py
   ```

## Penggunaan
1. Akses aplikasi melalui browser: http://localhost:5000
2. Registrasi akun baru atau login
3. Jelajahi pertunjukan yang tersedia
4. Pilih jadwal dan pesan tiket
5. Lakukan pembayaran
6. Cek riwayat pemesanan di halaman profil

## Fitur Admin
1. Login sebagai admin
2. Akses dashboard admin
3. Kelola pertunjukan dan jadwal
4. Monitor pemesanan
5. Kelola pengguna

## Kontribusi
1. Fork repositori
2. Buat branch fitur baru
3. Commit perubahan
4. Push ke branch
5. Buat Pull Request

## Lisensi
Hak Cipta 2024 SAKSIKAN. Seluruh hak dilindungi.

## Kontak
Email: admin@saksikan.com
Website: www.saksikan.com
