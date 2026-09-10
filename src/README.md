# Penggabungan sumber Google Trends

Jalankan dari direktori utama proyek:

```powershell
.\venv\Scripts\python.exe .\src\merge_trends.py
```

Skrip menggunakan library standar Python (`csv` dan `pathlib`), tanpa instalasi tambahan.
Lokasi masukan dihitung dari lokasi skrip sehingga tidak bergantung pada direktori kerja.

Masukan adalah enam file `data/top_{domain}.csv` dan
`data/rising_{domain}.csv` untuk kesehatan, keuangan, dan teknologi.
Folder `data/before` tidak dibaca. Hasil ditulis ke
`data/interim/trends_sources.csv`; menjalankan ulang akan mengganti hasil tersebut.

Semua baris dipertahankan, termasuk duplikasi dan sumber yang belum diseleksi.
Nilai minat pencarian dan persentase kenaikan disalin sebagai teks tanpa konversi.
Skrip memvalidasi kolom, kelengkapan baris, dan query kosong sebelum menulis hasil.

| Kolom | Keterangan |
|---|---|
| `source_id` | ID berdasarkan domain, jenis daftar, dan urutan baris data |
| `source_type` | `google_trends` |
| `domain` | Pemetaan berdasarkan nama file, bukan hasil penilaian relevansi |
| `source_list` | `top` atau `rising` |
| `source_file` | Path relatif file masukan |
| `source_row` | Urutan baris data, dimulai dari 1 setelah header |
| `source_text` | Isi asli kolom `query` |
| `search_interest` | Isi asli kolom `search interest` |
| `increase_percent` | Isi asli kolom `increase percent` |

ID dapat berubah jika urutan atau isi baris sumber diubah. Bekukan file masukan
sebelum ID digunakan oleh tabel penilaian atau sintesis. Metadata kategori asli,
periode, wilayah, dan tautan pengambilan belum ditambahkan karena belum tersedia
di CSV masukan. File hasil dapat dibaca dari Jupyter dengan `pandas.read_csv`.
