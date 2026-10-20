# Pengumpulan batch 7

Batch `main_07` memuat 105 query PAA accepted: masing-masing 35 query kesehatan, keuangan, dan teknologi. Pemilihan memakai `seed=20261011`, mengecualikan query yang sudah terjadwal pada batch sebelumnya, dan mencatat urutan serta asal query di `configs/main_07_query_selection.json`. Pool awal yang belum terjadwal berisi 402 query. Karena topik teknologi yang tersedia lebih sedikit, 35 query teknologi berasal dari sembilan topik induk; hal ini perlu diperhatikan saat pemisahan data untuk pemodelan.

Konfigurasi pengumpulan ada di `configs/main_dataset_07.json`. Protokolnya tetap Google Top 10, tiga percobaan Gemini per query, minimal dua percobaan valid, jendela enam jam per query, dan label positif jika proporsi sitasi minimal 0,5. Na ma model ditulis langsung sebagai `gemini-3.6-flash`, yaitu model efektif yang tercatat pada respons batch 5–6. Batas batch 105 pencarian SerpApi dengan cadangan kuota 10 pencarian.

Pengumpulan dapat dilanjutkan dari checkpoint tanpa mengulang query selesai:

```powershell
python -X utf8 src/continue_main_dataset.py --config configs/main_dataset_07.json --run --max-queries 105 --check-every 5
```

`-X utf8` diperlukan di terminal Windows ketika query mengandung karakter Unicode di luar halaman kode konsol. Tanpa opsi ini, proses dapat berhenti saat mencetak query meskipun respons API sudah tersimpan. Pemakaian token Gemini dan sisa pencarian SerpApi tercatat di `data/raw/main/main_07/usage_latest.json`. Saldo uang Gemini tidak tersedia melalui API generate-content dan perlu dilihat pada Billing Google AI Studio.

Sesudah URL baru terkumpul, pratinjau dan ambil kandidat Google Top 10 untuk dataset utama:

```powershell
python -X utf8 src/scrape_articles.py --config configs/article_dataset_07.json --extend-manifest --primary-only --max-new-urls 500
python -X utf8 src/scrape_articles.py --config configs/article_dataset_07.json --extend-manifest --primary-only --run --max-new-urls 500
python -X utf8 src/build_article_dataset.py --config configs/article_features_07.json --with-embeddings
```

Ulangi scraper hingga pratinjau menunjukkan nol URL baru. `--primary-only` hanya mengambil kandidat Google Top 10, termasuk irisannya dengan sitasi Gemini. Kandidat Gemini-only tetap dicatat sebagai dataset tambahan. Scraping dan build tidak memakai token Gemini atau pencarian SerpApi.

## Melanjutkan setelah timeout SerpApi pada 12 Oktober 2026

Pada pemeriksaan lokal, 100 dari 105 query sudah selesai. Dua pencarian Google berstatus `timeout` tanpa respons tersimpan, dua query belum dimulai, dan percobaan ketiga Gemini untuk pertanyaan cetirizine berstatus `started` tanpa respons tersimpan. Catatan kuota terakhir menunjukkan 19 pencarian tersisa dengan cadangan 10. Angka ini dapat berubah; skrip memeriksa kuota lagi saat dijalankan.

Pulihkan dua checkpoint Google satu per satu. Setiap perintah dapat memakai satu pencarian SerpApi, tetapi tidak memanggil Gemini. Jika timeout berulang, hentikan dan periksa riwayat pencarian/kuota SerpApi sebelum mencoba lagi.

```powershell
python -X utf8 src/recover_main_google.py --config configs/main_dataset_07.json --query-id query_ad0528d5918bcb542edff5f7 --run
python -X utf8 src/recover_main_google.py --config configs/main_dataset_07.json --query-id query_2c814c9f35b461e6116dacc4 --run
```

Setelah keduanya berhasil, lanjutkan dua query tersebut dan dua query yang belum dimulai. Opsi `--skip-uncertain` melewati checkpoint Gemini cetirizine yang belum jelas hasilnya; checkpoint itu tidak diubah atau dikirim ulang. Maksimum empat query pada perintah ini dapat memakai dua pencarian SerpApi untuk query baru dan hingga 12 panggilan Gemini untuk empat query. Bila hanya satu pemulihan Google berhasil, jangan jalankan langkah ini dahulu: checkpoint Google yang masih `error` akan tetap menghentikan kolektor.

```powershell
python -X utf8 src/continue_main_dataset.py --config configs/main_dataset_07.json --run --skip-uncertain --max-queries 4 --check-every 1
```

Query `Apakah cetirizine bisa untuk rhinitis?` masih mempunyai dua percobaan valid dan satu percobaan ketiga berstatus `started` tanpa respons. Skrip pemulihan Gemini menandainya `uncertain_trial_checkpoint` dan sengaja tidak mengulangnya. Jangan mengubah statusnya menjadi gagal atau selesai tanpa audit atas permintaan yang terputus; sampai selesai diaudit, query tersebut belum masuk pasangan berlabel siap model.
