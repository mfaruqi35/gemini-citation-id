# Dataset keterkutipan artikel oleh Gemini

Penelitian menggunakan query asli Google Trends dan People Also Ask pada domain kesehatan, keuangan, dan teknologi. Kandidat artikel berasal dari Google Top-10 serta sumber yang disitasi Gemini, dengan tiga percobaan per query dan minimal dua percobaan valid.

## Mulai dari sini

- [Panduan dataset utama](docs/MAIN_DATASET.md): pengumpulan, seleksi query, penambahan query, penggabungan kandidat, dan penggabungan CSV Trends.
- [Notebook 04](notebooks/04_inspect_main_dataset.ipynb): memeriksa hasil pengumpulan utama.
- [Notebook 05](notebooks/05_review_query_expansion.ipynb): meninjau kandidat query tambahan.
- [Catatan progres](docs/PROGRESS.md): riwayat keputusan dan hasil penelitian.
- [Pengumpulan PAA](docs/PAA_COLLECTION.md) dan [pilot grounding](docs/GEMINI_GROUNDING_PILOT.md): dokumentasi tahap sebelumnya.

## Status dan tahap berikutnya

Batch `main_01` memiliki 41 query, 123 percobaan Gemini, 983 pasangan query?artikel, dan 903 URL unik sebelum pemeriksaan canonical dan kelayakan halaman. Sebanyak 38 query memenuhi syarat pengumpulan. Angka kandidat belum merupakan jumlah artikel siap digunakan.

Tahap berikutnya adalah mengambil isi halaman, memeriksa kelayakan artikel, menyelesaikan pencocokan URL, menetapkan ambang label, lalu mengekstrak fitur. Setelah jumlah artikel layak diketahui, tambahkan query melalui batch baru sesuai kebutuhan dan anggaran.

`src/` berisi skrip, `notebooks/` berisi peninjauan interaktif, dan `configs/` berisi konfigurasi batch. Data mentah dan checkpoint ada di `data/`; cadangan pemulihan ada di `outputs/`. Skrip pilot tetap dipertahankan karena digunakan oleh kolektor utama.
