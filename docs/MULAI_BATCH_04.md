# Memilih dan menjalankan batch utama `main_04`

Pemilihan query batch 4 dilakukan dengan [select_main_batch_queries.py](../src/select_main_batch_queries.py), menggunakan [582 PAA accepted yang belum terjadwal](../data/interim/query_expansion/query_expansion_01/accepted_unused_20261009.csv). Berkas [main_04_queries.csv](../data/manual/main_04_queries.csv) sudah berisi **45 query: 15 kesehatan, 15 keuangan, 15 teknologi**. Pertanyaan asli dan kolom asal PAA dipertahankan.

Skrip mengacak urutan kandidat dengan `seed=20261009`, mengambil satu query dari tiap `topic_id` terlebih dahulu, lalu mengulang topik jika jumlah yang diminta melebihi jumlah topik tersedia. Hasilnya mencakup 15 topik kesehatan, 15 topik keuangan, dan 13 topik teknologi. Urutan CSV berselang-seling antar-domain agar pengumpulan bertahap tetap mencakup ketiganya. Metode dan ID terpilih tersimpan di [main_04_query_selection.json](../configs/main_04_query_selection.json). Pemilihan ini otomatis dan dapat diulang; kelayakan masing-masing query berasal dari review rubrik sebelumnya, bukan dinilai ulang oleh skrip.

Untuk **melihat rencana pemilihan** tanpa menulis berkas:

```powershell
python src/select_main_batch_queries.py --batch-id main_05 --count-per-domain 15 --seed 20261009
```

Ganti `main_05` dengan ID batch baru yang belum memiliki berkas/manifest. Skrip mengecualikan query yang sudah tercatat dalam snapshot batch lain; karena itu pratinjau `main_05` saat ini menunjukkan **537 kandidat belum terjadwal** dari sumber 582 baris. Tambahkan `--run` hanya ketika ingin menyimpan pilihan baru. Skrip melindungi CSV yang sudah berisi data dan manifest batch yang sudah berjalan. Jika ingin mengganti pilihan `main_04`, periksa [CSV batch 4](../data/manual/main_04_queries.csv) sebelum pengumpulan API dan catat setiap perubahan di metadata pemilihan agar jejak metode tetap sesuai.

Konfigurasi batch 4 sudah disiapkan:

| Konfigurasi | Isi utama |
| --- | --- |
| [main_dataset_04.json](../configs/main_dataset_04.json) | 45 query, Google Top 10, tiga percobaan Gemini, minimal dua valid, cadangan SerpApi 10. |
| [article_dataset_04.json](../configs/article_dataset_04.json) | Scraping dari sumber `main_04` ke `articles_main_04`. |
| [article_features_04.json](../configs/article_features_04.json) | Fitur dan label sitasi ≥0,5 untuk artikel batch 4. |

Pratinjau pengumpulan tanpa pemanggilan API:

```powershell
python src/continue_main_dataset.py --config configs/main_dataset_04.json --max-queries 5
```

Setelah melihat daftar query, mulai lima query pertama:

```powershell
python src/continue_main_dataset.py --config configs/main_dataset_04.json --run --max-queries 5 --check-every 5
```

Ulangi perintah terakhir secara bertahap. `--max-queries 5` membatasi pekerjaan tiap eksekusi, bukan ukuran batch. Seluruh 45 query membutuhkan sekitar 45 pencarian SerpApi dan maksimal 135 percobaan Gemini normal; ketersediaan kuota dan saldo diperiksa saat pengumpulan. Runner hanya dapat membaca pemakaian token Gemini, bukan saldo rupiah.

Setelah hasil query tersedia, pratinjau scraping Google Top 10:

```powershell
python src/scrape_articles.py --config configs/article_dataset_04.json --extend-manifest --primary-only --max-new-urls 50
```

Lalu jalankan pengambilan dan build fitur:

```powershell
python src/scrape_articles.py --config configs/article_dataset_04.json --extend-manifest --primary-only --run --max-new-urls 50
python src/build_article_dataset.py --config configs/article_features_04.json --with-embeddings
```

Scraping dan build lokal tidak mengurangi kuota SerpApi/Gemini. Artikel yang membutuhkan verifikasi dapat ditinjau lalu dibangun ulang mengikuti [panduan penambahan dataset](PANDUAN_MENAMBAH_DATASET.md).
