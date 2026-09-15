# Dataset keterkutipan artikel oleh Gemini

Penelitian menggunakan query asli Google Trends dan People Also Ask pada domain kesehatan, keuangan, dan teknologi. Dataset utama berisi artikel Google Top-10 dengan label keterkutipan Gemini; sitasi Gemini di luar Top-10 menjadi dataset tambahan. Pengumpulan memakai tiga percobaan per query dan minimal dua percobaan valid, dengan label positif pada proporsi sitasi >=0,5.

## Mulai dari sini

- [Panduan dataset utama](docs/MAIN_DATASET.md): pengumpulan, seleksi query, penambahan query, penggabungan kandidat, dan penggabungan CSV Trends.
- [Notebook 04](notebooks/04_inspect_main_dataset.ipynb): memeriksa hasil pengumpulan utama.
- [Notebook 05](notebooks/05_review_query_expansion.ipynb): meninjau kandidat query tambahan.
- [Notebook 06](notebooks/06_inspect_article_dataset.ipynb): memeriksa hasil scraping, fitur, label, dan kredibilitas; melanjutkan URL berikutnya.
- [Catatan progres](docs/PROGRESS.md): riwayat keputusan dan hasil penelitian.
- [Pengumpulan PAA](docs/PAA_COLLECTION.md) dan [pilot grounding](docs/GEMINI_GROUNDING_PILOT.md): dokumentasi tahap sebelumnya.

## Status dan tahap berikutnya

Batch `main_01` memiliki 41 query, 123 percobaan Gemini, 983 pasangan query?artikel, dan 903 URL unik sebelum pemeriksaan canonical dan kelayakan halaman. Sebanyak 38 query memenuhi syarat pengumpulan. Angka kandidat belum merupakan jumlah artikel siap digunakan.

Uji 20 URL menghasilkan 17 halaman yang dapat diekstrak dan 15 artikel Indonesia yang lolos review isi. Pada pemisahan 14 September 2026, dataset utama (`dataset.csv`) berisi 13 pasangan query-artikel Google Top-10, sedangkan dataset tambahan (`dataset_gemini_only.csv`) berisi 11 pasangan sitasi di luar Top-10. Tiga pasangan utama masuk `model_ready.csv`; empat pasangan tambahan lolos pemeriksaan untuk analisis tambahan. `dataset_union.csv` menyimpan 24 pasangan sebagai audit. Lihat [panduan scraping dan fitur](docs/MAIN_DATASET.md#scraping-dan-fitur) atau [panduan menambah dataset](docs/PANDUAN_MENAMBAH_DATASET.md) untuk melanjutkan.

`src/` berisi skrip, `notebooks/` berisi peninjauan interaktif, dan `configs/` berisi konfigurasi batch. Data mentah dan checkpoint ada di `data/`; cadangan pemulihan ada di `outputs/`. Skrip pilot tetap dipertahankan karena digunakan oleh kolektor utama.
