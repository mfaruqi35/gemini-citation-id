# Panduan menambah dataset: PAA sampai artikel dan fitur

Batch baru `main_03` telah disiapkan pada 7 Oktober 2026 dari PAA yang tersimpan di respons Google `main_02`: **75 kueri terpilih**, 25 per domain. Perintah yang sudah disesuaikan untuk batch ini ada di [MULAI_BATCH_03.md](MULAI_BATCH_03.md). Bagian contoh `main_02` di bawah tetap menjadi riwayat alur umum.

## Menggunakan 10 pencarian terakhir akun SerpApi saat ini (5 Oktober 2026)

Snapshot pemantauan terakhir pada 4 Oktober mencatat 240/250 pencarian terpakai dan 81 query `main_02` belum dimulai. Konfigurasi batch yang sudah dibekukan menyimpan `serp_quota_reserve: 10`, sehingga perintah biasa berhenti ketika kuota tinggal 10. Gunakan opsi **runtime** berikut untuk memakai cadangan tersebut pada query `main_02` tanpa mengubah manifest atau aturan penelitian:

```powershell
# Preview lokal; tidak memakai API
python src/continue_main_dataset.py --unstarted-only --max-queries 10 --check-every 1 --quota-reserve 0

# Jalankan maksimal 10 query baru dengan key SerpApi yang aktif
python src/continue_main_dataset.py --run --unstarted-only --max-queries 10 --check-every 1 --quota-reserve 0
```

Runner memeriksa sisa kuota sebelum setiap query dan kolektor melakukan pemeriksaan lagi sebelum meminta pencarian. Jumlah query yang benar-benar berhasil bisa kurang dari 10 jika permintaan SerpApi/Gemini gagal; respons dan checkpoint lama tetap dipertahankan. `--unstarted-only` melewati checkpoint gagal atau terputus, tidak memulihkannya. Satu query baru memakai kira-kira satu pencarian SerpApi dan tiga panggilan Gemini. Periksa saldo Gemini di AI Studio sebelum `--run`; runner hanya dapat menghitung token, bukan saldo rupiah. Setelah akun pertama habis, ganti key SerpApi pada environment yang aktif, lalu jalankan perintah biasa tanpa `--quota-reserve 0` untuk kembali menyisakan cadangan 10 pada akun berikutnya.

## Review jenis halaman oleh peneliti (22 September 2026)

Sebanyak 50 artikel yang diteruskan dari review bahasa sudah diperiksa peneliti. Keputusan aktif dari kelompok ini: **47 accepted, 2 excluded, dan 1 needs_extraction_review**. Catatan halaman informasi/panduan dipetakan ke accepted; daftar harga emas dan formulir dengan informasi terbatas dipetakan ke excluded. Artikel JDIH Sukoharjo diterima jenis halamannya tetapi tetap ditahan karena salinan HTML/teks yang tersimpan terputus. Bersama tiga masalah sebelumnya, ada empat artikel dalam kelompok review ini yang masih membutuhkan pemeriksaan/perbaikan salinan teks.

Gunakan [article_review.csv](../data/manual/article_review.csv) untuk keputusan aktif dan [audit review manual](../data/manual/article_page_type_review_20260922.csv) untuk catatan asli serta riwayat pemetaan. Angka/status pada bagian 21 September di bawah adalah snapshot sebelum review manual ini. Lihat [catatan review](REVIEW_BAHASA_ARTIKEL.md) untuk detail. Kandidat jenis halaman lain di luar 50 artikel ini tetap mengikuti statusnya masing-masing.

Build terbaru menghasilkan **153 + 146 = 299 pasangan utama model-ready**, bertambah 50 dari 249. Sebanyak **244 baris lengkap seluruh fitur**, sementara **55 baris** masih membutuhkan penanganan nilai kosong saat prapemrosesan. File yang digunakan tetap `data/processed/articles_main_01/model_ready.csv` dan `data/processed/articles_main_02/model_ready.csv`. Di luar daftar 50 artikel yang sudah ditinjau, masih ada **79 artikel / 87 pasangan utama** pada antrean `needs_page_type_review`. Empat kasus ekstraksi tetap ditahan sampai teks yang memadai tersedia. Tidak ada panggilan Gemini atau SerpApi untuk pembaruan ini.

## Review bahasa kandidat Top-10 (21 September 2026)

Sebanyak 101 artikel / 106 pasangan utama sudah ditinjau oleh asisten LLM: 96 artikel menggunakan bahasa Indonesia dan 5 didominasi Inggris. Keputusan aktif ada di `data/manual/article_review.csv`; [catatan review bahasa](REVIEW_BAHASA_ARTIKEL.md) menjelaskan hasil, bukti dan langkah verifikasi ulang. Sebanyak 43 artikel diterima, 50 masih membutuhkan review jenis halaman, dan 3 berstatus `needs_extraction_review` karena masalah teks ekstraksi. Kelulusan bahasa saja tidak memastikan kelayakan artikel.

Build setelah review menghasilkan **133 + 116 = 249 pasangan model-ready**, naik dari 204. Sebanyak 210 baris lengkap seluruh prediktor; 39 baris masih membutuhkan penanganan nilai kosong. Angka 204 pada bagian pemulihan teknis di bawah merupakan snapshot sebelum review bahasa ini.

Jika memeriksa ulang, ubah baris sesuai `article_id` pada `article_review.csv`, termasuk alasan, reviewer dan tanggal; jangan membuat ID duplikat. CSV audit `article_language_review_20260921.csv` menyimpan keputusan awal asisten, bukan sumber aktif builder. Status `needs_extraction_review` harus tetap ditahan sampai teks ekstraksi diperiksa/diperbaiki. Jalankan build ulang batch terkait setelah koreksi keputusan.

## Pemulihan teknis sumber dan artikel (21 September 2026)

Pemulihan ini tidak meminta jawaban Gemini baru atau pencarian SerpApi. Status artikel yang masih `needs_language_review`/`needs_page_type_review` tetap menunggu keputusan di `article_review.csv`. Kriteria bahasa, panjang minimal, ambang sitasi dan jumlah percobaan tetap sama.

Hasil perbaikan 21 September tercatat di [PROGRESS.md](PROGRESS.md): **110 + 94 = 204 pasangan utama model-ready**, meningkat dari 131. Kedua CSV tetap berada dalam direktori batch masing-masing. Sebanyak 23 baris tidak memiliki tanggal publikasi dan dua baris tidak memiliki rerata panjang paragraf karena elemen `<p>` tidak tersedia. Total 24 baris membutuhkan penanganan nilai kosong saat prapemrosesan, dengan aturan yang di-fit pada data train. Angka pada bagian 20 September dan bagian yang lebih lama di bawah adalah snapshot historis.

```powershell
# Periksa URL sumber tersimpan yang belum diketahui tujuannya
python src/recover_article_sources.py

# Pulihkan maksimal 100 URL, dengan bukti terpisah dari respons API mentah
python src/recover_article_sources.py --run --max-new-urls 100

# Jika diperlukan pada kesempatan berikutnya: coba ulang resolusi yang gagal
python src/recover_article_sources.py --run --retry-failed --max-new-urls 30

# Retry hanya kegagalan sementara pada kandidat Top-10 (preview jika --run dihilangkan)
python src/scrape_articles.py --config configs/article_dataset.json --retry-transient-only --primary-only --run --max-new-urls 20
python src/scrape_articles.py --config configs/article_dataset_02.json --retry-transient-only --primary-only --run --max-new-urls 20

# Bangun ulang dari HTML, percobaan Gemini tersimpan dan bukti pemulihan
python src/build_article_dataset.py --config configs/article_features.json --with-embeddings
python src/build_article_dataset.py --config configs/article_features_02.json --with-embeddings
```

Jika sumber scraper bertambah, tambahkan `--extend-manifest` sesuai bagian berikutnya. `--retry-transient-only` tidak boleh digabung dengan `--retry-failed`; robots disallowed, HTTP 403/404, dan halaman non-HTML tidak dipilih dalam retry sementara. Tidak ada bypass robots atau penonaktifan verifikasi TLS.

`data/interim/article_repair/url_resolutions.json` menyimpan hasil pemulihan dan riwayatnya. Status `destination_redirect_observed` berarti header redirect Google menunjukkan URL tujuan, bukan jaminan halaman dapat diunduh atau artikelnya layak. Respons Gemini dan manifest asli tetap disimpan. Builder memakai bukti baru sebagai lapisan turunan sehingga tidak perlu mengubah label dalam manifest scraper yang dibekukan.

Alias disatukan untuk pencocokan bila ada redirect yang diamati saat scraping sukses, atau canonical sama disertai judul dan teks lengkap identik (minimal 100 kata). Canonical saja tidak cukup untuk menggabungkan dua halaman. `source_matching_audit.json` mencatat bukti, hash file sumber mentah/cache pemulihan, dan salinan bukti pemulihan yang benar-benar dipakai. `article_identity_url` adalah identitas audit/pengelompokan, **bukan fitur prediksi**. Label dihitung ulang per percobaan valid; dua alias dalam satu jawaban dihitung satu kali. Kolom `original_*` mempertahankan nilai sebelum pencocokan ulang.

Pasangan alias ganda untuk query yang sama tetap berada dalam ekspor audit dengan `duplicate_pair_of`, tetapi hanya satu wakil dapat masuk model_ready. Wakil Google Top-10 diprioritaskan atas tambahan Gemini-only. Halaman dengan isi berbeda atau alias belum pasti tetap tertahan. Ketidakpastian yang tersisa tidak dijadikan label negatif.

Ekstraktor diperbaiki untuk konten Elementor serta beberapa situs yang HTML lengkapnya dahulu hanya terbaca sebagai cuplikan. Artikel yang tetap membutuhkan penilaian manusia tidak otomatis diterima; pengaturan `preserve_pending_manual_reviews` mempertahankan status review lama sampai keputusan eksplisit dicatat. Setelah pemulihan, jumlah model_ready mengikuti build terbaru, tidak boleh diperkirakan dengan menjumlah semua kategori kegagalan yang tumpang tindih.

## Perbaikan manifest scraping setelah data sumber bertambah (21 September 2026)

Jika muncul `ValueError: Manifest berbeda`, gunakan `--extend-manifest` untuk memeriksa dan menerima **penambahan data dalam batch sumber yang sama**. Tidak perlu mengganti `dataset_id` untuk kasus ini. Semua pasangan lama harus tetap identik, termasuk URL, label dan status kelayakan. Penghapusan pasangan atau perubahan konfigurasi tetap ditolak dan perlu ditinjau atau dibuatkan dataset artikel baru.

Saat pemeriksaan, manifest `articles_main_02` berisi 584 URL/610 pasangan, sedangkan ekspor sumber terbarunya berisi 917 URL/986 pasangan eligible. Ada 333 URL dan 376 pasangan tambahan; seluruh pasangan lama identik. Dari manifest lama, 500 URL telah dicoba dan 84 belum dicoba. Setelah perluasan tersedia 417 URL belum dicoba dan 67 URL berstatus yang diizinkan untuk retry. Angka ini adalah snapshot saat pemeriksaan, bukan jumlah hasil scraping yang pasti berhasil.

```powershell
# Preview perluasan dan URL belum dicoba; tidak mengubah data atau mengakses jaringan
python src/scrape_articles.py --config configs/article_dataset_02.json --extend-manifest --max-new-urls 10

# Simpan perluasan, lalu ambil maksimal 10 URL belum dicoba
python src/scrape_articles.py --config configs/article_dataset_02.json --extend-manifest --run --max-new-urls 10

# Alternatif: simpan perluasan dan coba kembali maksimal 10 URL gagal saja
python src/scrape_articles.py --config configs/article_dataset_02.json --extend-manifest --retry-failed --run --max-new-urls 10

# Setelah scraping/retry, perbarui dataset utama, tambahan, dan model_ready
python src/build_article_dataset.py --config configs/article_features_02.json --with-embeddings
```

Pilih perintah URL baru atau retry sesuai pekerjaan yang ingin dilakukan. `--retry-failed` **hanya** memilih checkpoint gagal yang diperbolehkan untuk dicoba ulang; URL belum dicoba tidak diambil dalam mode ini. Untuk preview retry, hilangkan `--run`. URL berhasil tidak diunduh ulang. Jika URL lama muncul pada query baru, pasangan baru ditambahkan dan hasil scraping URL tersebut digunakan kembali.

Preview selalu baca saja. Manifest baru baru disimpan ketika `--run` diberikan, setelah memperoleh `running.lock` dan memvalidasi ulang manifest aktif. Manifest sebelumnya diarsipkan di `data/raw/articles/articles_main_02/manifest_history/` sebelum diganti. HTML, ekstraksi, dan riwayat percobaan lama dipertahankan. Setelah tersimpan, `--extend-manifest` boleh tetap dicantumkan atau dihilangkan selama sumber tidak berubah lagi. Tidak ada penggabungan otomatis yang menerima perubahan label lama.

Scraping/retry mengakses website langsung; **tidak memakai token Gemini atau kredit pencarian SerpApi**. Build memakai HTML lokal dan cache embedding; model embedding dapat diunduh jika belum tersedia, tetapi tidak memakai kedua API tersebut. Build diperlukan untuk memperbarui CSV final setelah scraping. Penambahan pasangan tetap dipisahkan per query: Top-10 masuk dataset utama dan Gemini-only masuk dataset tambahan.

Saat fitur ini ditambahkan, hanya pengujian offline dan preview data aktual yang dijalankan. Manifest riil dan hasil dataset belum diperluas/dibangun ulang oleh perbaikan kode ini. Angka pada bagian bertanggal lebih lama di bawah adalah riwayat; instruksi perluasan pada bagian ini menggantikan keharusan membuat snapshot baru untuk setiap penambahan data.

## Rute terbaru menuju 2.000–3.000 baris utama (20 September 2026)

Bagian ini menjelaskan rute pengumpulan dan snapshot pada 20 September; untuk jumlah data terbaru setelah pemulihan, baca bagian 21 September di atas dan [PROGRESS.md](PROGRESS.md). Target dihitung sebagai **pasangan query–artikel Google Top-10 yang layak dan memiliki label pasti**, bukan jumlah URL gabungan. Artikel Gemini-only tetap menjadi dataset tambahan dan tidak dihitung untuk memenuhi target model utama. URL sama pada dua query menghasilkan dua pasangan, tetapi bukan dua artikel unik; laporkan keduanya.

### Posisi saat pemeriksaan

| Tahap | Posisi |
| --- | --- |
| Query dalam dua manifest utama | 306: `main_01` 41 dan `main_02` 265 |
| `main_02` | 27 query selesai, 1 terputus, 237 belum dimulai |
| Scraping `articles_main_01` | 870 dari 870 URL telah dicoba |
| Scraping `articles_main_02` | 500 dari 584 URL telah dicoba |
| Sisa 84 URL pada snapshot artikel kedua | **Semua Gemini-only**; tidak menambah kandidat model utama |
| Dataset utama dari dua snapshot artikel | 325 + 232 = 557 pasangan dari 65 query eligible |
| `model_ready` pada pemeriksaan | 72 + 37 = 109 pasangan; ini bukan gabungan final untuk training |

Sebanyak 109 pasangan tersebut mewakili 105 URL unik, dengan label 0 sebanyak 54 dan label 1 sebanyak 55. Distribusi domainnya: kesehatan 25, keuangan 61 dan teknologi 23. Ini hitungan gabungan untuk pemantauan, belum ekspor training gabungan dengan korpus BM25 bersama.

Snapshot berbayar terakhir tersimpan pada 17 September: SerpApi tersisa 124 pencarian. **Itu bukan kuota terkini.** Runner memeriksa ulang kuota ketika dijalankan dengan `--run`. Saldo rupiah Gemini tetap diperiksa lewat AI Studio; file lokal hanya merekap token respons yang tersimpan.

### 1. Periksa hasil build dan tangani kandidat yang tertahan

Gunakan `data/processed/articles_main_01/dataset.csv` dan `data/processed/articles_main_02/dataset.csv`. Filter `ready_for_model=False`, lalu baca `not_ready_reason`:

- `article_not_eligible`: tinjau `articles.csv`, HTML/teks, bahasa dan jenis halaman melalui Notebook 06. Masukkan keputusan yang benar ke `data/manual/article_review.csv`; jangan menerima halaman non-artikel, teks terpotong, atau bahasa yang tidak sesuai hanya demi jumlah.
- `semantic_not_computed`: jika artikel sudah eligible, lakukan build dengan `--with-embeddings`.
- `url_matching_uncertain`: perlu pemeriksaan resolusi dan kecocokan URL terhadap sitasi asli. CSV review artikel tidak menyelesaikan label ini. Jangan mengisi label kosong sebagai 0 atau 1 tanpa bukti dan pembaruan sumber yang konsisten.
- `url_alias_needs_review`: tinjau URL final/canonical yang beririsan. Menerima artikel pada CSV review tidak otomatis menyelesaikan konflik alias.
- Gagal unduh sementara: scraper mendukung `--retry-failed`, tetapi retry juga mencakup beberapa status yang mungkin tetap gagal; periksa preview dan batasi jumlah. Halaman terlarang robots/challenge tidak diatasi dengan bypass.

Setelah review, jalankan ulang build. Kedua perintah ini lokal, **tanpa token Gemini atau kredit pencarian SerpApi**:

```powershell
python src/build_article_dataset.py --config configs/article_features.json --with-embeddings
python src/build_article_dataset.py --config configs/article_features_02.json --with-embeddings
```

Scraper berikutnya otomatis memakai ekstraktor tanggal yang diperbaiki. Build juga mengekstrak ulang HTML lama, tanpa mengunduh ulang artikel. `publication_age_days` adalah umur saat scraping, bukan saat training atau saat query dikirim ke Gemini. Parser mendukung tanggal ISO, timestamp bertitik, serta nama bulan Indonesia/Inggris yang lengkap dengan hari dan tahun. Tanggal parsial/ambigu tidak ditebak. Tanggal tanpa timezone diasumsikan UTC dan ditandai; nilai yang melampaui waktu scraping tetap kosong.

Kolom audit baru pada ekspor lengkap:

| Kolom/file | Kegunaan |
| --- | --- |
| `published_at_source` | Sumber tanggal: JSON-LD, metadata atau selector HTML |
| `published_at_normalized` | Tanggal yang berhasil dibaca, dalam ISO |
| `publication_age_status` | `available`, `missing_publication_date`, `unparseable_publication_date`, `future_publication_date`, atau `invalid_retrieval_date` |
| `publication_timezone_assumed` | Apakah timezone harus diasumsikan UTC |
| `missing_model_features` / `model_features_complete` | Daftar fitur kosong per pasangan / apakah semua terisi |
| `missing_features_report.json` | Jumlah nilai hilang per fitur pada dataset utama dan model_ready |

Hasil build ulang 20 September: umur publikasi kosong pada dataset utama turun dari 176 ke 174 baris (batch 01) dan 132 ke 127 (batch 02). Pada model_ready turun dari 13 ke 11 dan 4 ke 3. Dari 109 baris layak, **95 lengkap seluruh fitur dan 14 masih tanpa umur publikasi**; semua fitur model lainnya terisi. Seluruh tanggal publikasi yang sudah diperoleh berhasil dihitung. Sisa kosong berarti tanggal belum ditemukan oleh ekstraktor, bukan bukti pasti bahwa halaman tidak menampilkan tanggal.

Tanggal modifikasi, copyright dan tanggal dari URL tidak digunakan sebagai pengganti tanggal terbit. Kosong bukan berarti nol. `model_ready.csv` tetap berarti lolos kriteria kelayakan dan label, **bukan jaminan seluruh fitur tersedia**. Untuk XGBoost, nilai fitur hilang dapat dipertahankan sebagai NaN. Jika model/pipeline membutuhkan imputasi, fit median/strategi imputasi hanya pada data latih di masing-masing fold, lalu pakai transformasi yang sama untuk validasi, test dan prediksi. Jangan menghitung median dari semua data sebelum split. Jangan melakukan imputasi label. Training dan preprocessing final belum dijalankan oleh build ini.

### 2. Lanjutkan pengumpulan dari query accepted yang sudah ada

Belum perlu membayar pencarian PAA baru untuk tahap berikutnya: masih ada **237 query yang belum dimulai** pada `main_02`.

```powershell
# Preview lokal
python src/continue_main_dataset.py

# Pengumpulan berbayar bertahap
python src/continue_main_dataset.py --run --unstarted-only --max-queries 30 --check-every 5
```

Setiap query baru membutuhkan anggaran sekitar satu pencarian SerpApi untuk Google organik dan tiga panggilan Gemini, bukan tiga token. Biaya Gemini bergantung jumlah token dan grounding; gunakan batas billing pribadi. Parameter tetap tiga percobaan, minimal dua valid, dan label proporsi sitasi >=0,5.

**Catatan satu query terputus:** checkpoint 17 September memiliki satu trial selesai dan satu error; slot ketiga belum dipanggil. Melanjutkannya sekarang melewati jendela pengumpulan 6 jam, sehingga tidak menghasilkan query eligible walaupun slot terakhir berhasil. Flag baru `--unstarted-only` di atas melewati seluruh query yang sudah memiliki checkpoint, termasuk query terputus tersebut, agar fokus pada 237 query baru. Arsip lama tidak diubah. Tanpa flag ini, runner biasa masih mencoba melanjutkan query terputus. Jangan mengubah timestamp untuk membuatnya valid. Pengumpulan ulang yang ingin dipakai memerlukan batch baru berisi Google dan ketiga percobaan Gemini yang berdekatan waktunya. `--recover-gemini` bukan cara memulihkan jendela yang sudah kedaluwarsa dan tidak boleh digabung dengan `--unstarted-only`. Jika eksekusi baru terputus lagi, mode ini juga melewati query itu; tinjau pemulihannya secara terpisah.

### 3. Perluas manifest scraping setelah URL bertambah

Pembaruan 21 September: selesaikan satu tahap pengumpulan/ekspor URL, lalu gunakan `--extend-manifest` seperti bagian awal panduan untuk memperluas `articles_main_02`. Tetap gunakan config scraping dan config fitur `_02`. Checkpoint lama digunakan kembali dan build memisahkan pasangan Top-10/Gemini-only secara otomatis. Sumber yang bertambah juga dapat menambahkan pasangan Top-10 baru; keterangan 84 URL Gemini-only pada snapshot 20 September hanya berlaku untuk sisa manifest lamanya.

Jika konfigurasi, daftar batch sumber, atau nilai pasangan lama memang berubah, perluasan akan ditolak. Tinjau penyebabnya; untuk perubahan yang disengaja, buat config scraping dengan `dataset_id` baru dan config fitur yang menunjuk ke sana. Checkpoint lintas ID dataset artikel belum digunakan ulang otomatis, sehingga snapshot baru dapat mengunduh ulang URL lama. Jangan menghitung pasangan yang sama pada snapshot lama dan baru sebagai sampel berbeda.

### 4. Ukur hasil per query sebelum menentukan tambahan PAA

Secara teoritis, 306 query memberi **maksimal 3.060 kandidat pasangan Top-10**, sebelum hasil Google kurang dari 10, query tidak valid, kegagalan scraping, halaman non-artikel, ketidakpastian label dan duplikasi. Maka 306 query **tidak menjamin** 2.000–3.000 baris siap model.

Pada snapshot sekarang, 109/65 sekitar **1,68 baris siap-model per query eligible**. Nilai ini belum final karena review dan resolusi label masih tertahan. Ukur ulang setelah menuntaskan review dan satu tahap pengumpulan baru.

| Rata-rata baris siap-model per query | Perkiraan total query untuk 2.000 baris | Untuk 3.000 baris |
| --- | ---: | ---: |
| Sekitar 1,68 (hasil sementara sekarang) | sekitar 1.200 | sekitar 1.800 |
| 2 | 1.000 | 1.500 |
| 4 | 500 | 750 |
| 6 | 334 | 500 |
| 8 | 250 | 375 |

Tabel adalah skenario, bukan janji hasil; query gagal akan menambah kebutuhan pengumpulan. Hitung kebutuhan query tambahan sebagai `ceil((target - baris_layak_unik_saat_ini) / rata_rata_hasil_query_baru)`. Pantau juga label 0/1 dan jumlah tiap domain, bukan total saja. Jangan melonggarkan kriteria atau memilih query berdasarkan label yang diharapkan untuk memenuhi target.

Jika stok query tidak cukup, gunakan **bagian 3–6** di bawah untuk menambah PAA, mempertahankan jejak keyword Trends, meninjau kandidat dan membekukan batch query baru. PAA dari respons Google yang sudah disimpan bisa diekstrak lokal tanpa pencarian baru: tambahkan `main_02` ke `main_batches` pada `configs/query_expansion_01.json`, lalu jalankan:

```powershell
python src/prepare_query_expansion.py --config configs/query_expansion_01.json
```

Review kandidat baru di Notebook 05/CSV keputusan, lalu siapkan snapshot query baru (`main_03`, dst.). Pertahankan keputusan lama dan singkirkan query yang sudah berada di manifest utama mana pun. Skrip persiapan membaca keputusan yang tersimpan; tidak memanggil LLM otomatis. Meminta PAA baru lewat SerpApi memakai kredit pencarian; mengambil pertanyaannya dari respons tersimpan tidak. Query baru yang diproses ke Google dan Gemini tetap memakai kedua layanan.

### 5. Bekukan dataset akhir sebelum training

Gunakan kebijakan penggabungan pada bagian 10: satu korpus BM25 yang konsisten, deduplikasi pasangan, audit alias, dan jejak sumber. Jangan langsung concat beberapa `model_ready.csv` dengan statistik BM25 berbeda dan melatih model. Snapshot scraping yang baru menggantikan cakupan lama tidak boleh ditambahkan sebagai sampel baru.

Target selesai saat terdapat 2.000–3.000 **pasangan utama layak, label pasti, tanpa penghitungan ulang pasangan**, dengan kualitas teks diperiksa dan strategi missing value sudah ditetapkan. Bagi train/validasi/test berdasarkan query serta audit artikel sama lintas split; fit preprocessing hanya pada train. Target tersebut adalah total sebelum pembagian: jika membutuhkan 2.000–3.000 khusus subset train, kumpulkan lebih banyak sesuai proporsi test/validasi. Jumlah ini adalah target operasional; kecukupan pemodelan tetap diperiksa lewat distribusi kelas, learning curve dan evaluasi, bukan angka saja. Artikel baru untuk inferensi harus melalui ekstraksi/preprocessing yang sama; label boleh belum tersedia pada data prediksi, tetapi wajib pasti untuk training/evaluasi.

## Lanjutan siap jalan: main_02 (17 September 2026)

### Recovery Gemini timeout/jaringan

Timeout request Gemini sekarang 120 detik (sebelumnya 55 detik). Error baru dibedakan menjadi `timeout` dan `network_error`; error historis `network_or_timeout` tetap dikenali. Recovery harus dipilih dengan flag/perintah berikut, dan maksimal satu retry per slot percobaan sepanjang riwayat checkpoint.

Untuk memulihkan maksimal dua slot gagal dahulu, kemudian melanjutkan maksimal 30 query yang belum selesai:

```powershell
python src/continue_main_dataset.py --run --recover-gemini --max-recovery-calls 2 --max-queries 30 --check-every 5
```

Untuk preview atau recovery saja, tanpa melanjutkan query baru:

```powershell
python src/recover_main_gemini.py
python src/recover_main_gemini.py --run --max-new-calls 2
```

Preview tidak memakai API. Recovery saja memakai Gemini dan tidak melakukan pencarian SerpApi. Flag pada runner juga memeriksa Account API SerpApi serta rekap token sebelum/sesudah recovery. Timeout sebelumnya mungkin sudah diproses/ditagihkan di server meskipun respons tidak diterima; total token lokal hanya menghitung respons yang tersimpan.

**Pembaruan 8 Oktober 2026 — Gemini 503:** recovery sekarang juga menerima HTTP 503, maksimal satu retry per slot. Untuk sekaligus mengisi slot yang belum dijalankan tanpa memulai query baru, gunakan `python src/recover_main_gemini.py --config configs/main_dataset_03.json --finish-incomplete` sebagai preview. Setelah jeda saat layanan bermasalah, tambahkan `--run --max-new-calls 1` untuk mencoba satu panggilan Gemini; jika berhasil, lanjutkan dengan batas 3. Semua panggilan, baik retry maupun slot baru, masuk batas yang sama. **Tidak memakai pencarian SerpApi.** Opsi ini melewati Google yang belum selesai serta memeriksa jendela enam jam sebelum setiap panggilan. Jika 503 berulang, hentikan percobaan; jangan terus menjalankan `--unstarted-only`, karena setiap query baru bisa menghabiskan pencarian Google sebelum Gemini gagal. Petunjuk lengkap ada di [MULAI_BATCH_03.md](MULAI_BATCH_03.md).

Recovery mempertahankan respons sukses, Google lama, ID/repetition, dan arsip kegagalan di `recovery_history` pada JSON query. Waktu retry dicatat sebagai waktu percobaan aktif, sehingga validasi jendela waktu tidak memakai timestamp lama secara keliru. Jumlah slot penelitian tetap tiga; riwayat retry bukan ulangan tambahan untuk menghitung proporsi sitasi. Retry tidak dijalankan untuk respons selesai yang tidak memenuhi valid grounding, error billing/429, atau `started` dengan hasil tidak pasti. File `.tmp` dan lock mencegah recovery sampai diperiksa.

`collection_window_expired` berarti waktu recovery akan melewati jendela 6 jam sejak pengumpulan terkait; skrip melewatinya. Query itu perlu pengumpulan ulang terencana dengan Google dan Gemini pada batch baru bila ingin dipakai, bukan mengubah timestamp atau memperpanjang jendela batch lama. `retry_limit_reached` berarti jatah satu retry slot tersebut sudah dipakai. Jika retry gagal lagi, proses berhenti dan riwayat tetap tersedia. Command tanpa `--recover-gemini` hanya melanjutkan slot/query yang belum dijalankan, tidak mengulang slot berstatus error.

Snapshot `data/manual/main_02_queries.csv` berisi 265 query accepted yang belum ada pada manifest lama: 115 kesehatan, 92 keuangan, dan 58 teknologi. Konfigurasi `configs/main_dataset_02.json` mempertahankan model, prompt, tiga percobaan, minimal dua valid, serta parameter pencarian batch awal; ambang label ditetapkan 0,5.

```powershell
python src/continue_main_dataset.py
python src/continue_main_dataset.py --run --max-queries 10 --check-every 5
```

Perintah pertama menyiapkan/memeriksa snapshot lokal. Perintah kedua melanjutkan maksimal 10 query yang belum selesai, dengan pemeriksaan SerpApi dan rekap token Gemini tiap 5 query. Jalankan satu proses saja. Query selesai dilewati; checkpoint gagal/tidak pasti memerlukan pemeriksaan sebelum retry. Batas `--max-queries` adalah per eksekusi, bukan target total batch.

Pemantauan tersimpan di `data/raw/main/main_02/usage_latest.json` dan `usage_history/`. Token berasal dari `usageMetadata` respons Gemini dan hanya mencakup batch ini; bukan sisa saldo rupiah, bukan total seluruh akun, dan tidak memastikan biaya grounding. Saldo/billing tetap diperiksa di AI Studio. Kuota SerpApi dibaca dari Account API, dengan cadangan 10 pencarian. Proses berhenti saat kuota tidak cukup atau API gagal. Pengumpulan memakai kuota SerpApi serta token/biaya Gemini; belum melakukan scraping isi artikel. Hasil URL berada di `data/interim/main/main_02/`.

Manifest scraping lama tetap untuk `main_01`. Setelah pengumpulan baru selesai, buat konfigurasi scraping dengan ID baru untuk mengonsumsi `main_02`; jangan mengubah manifest scraping lama yang sudah berjalan.

Panduan ini mengikuti skrip proyek, diperbarui **14 September 2026**. Semua perintah dijalankan dari direktori utama proyek. Contoh nama batch baru di bawah adalah nama yang perlu kamu buat sendiri, bukan batch yang otomatis sudah tersedia. Menulis panduan ini tidak menjalankan pengumpulan berbayar.

**Pemisahan aktif:** dataset utama adalah artikel Google Top-10 dengan label sitasi Gemini pada ambang >=0,5. Sitasi Gemini di luar Top-10 menjadi dataset tambahan. Skrip scraping tetap memakai daftar URL gabungan untuk mengumpulkan keduanya; builder memisahkan ekspornya secara otomatis. Tidak perlu menjalankan scraper dua kali untuk masing-masing kelompok.

## 1. Tentukan mulai dari tahap mana

Alur penelitian:

**Keyword Google Trends → pertanyaan PAA → review query → Google Top-10 + tiga jawaban Gemini → gabungan URL → scraping → review artikel + otoritas domain biner → fitur dan label → dataset utama Top-10 + dataset tambahan Gemini-only.**

| Kebutuhanmu | Mulai dari |
| --- | --- |
| Menambah artikel dari 41 query yang URL-nya sudah dikumpulkan | Bagian 8: lanjutkan scraping yang ada |
| Memproses query accepted yang belum dikirim ke Gemini | Bagian 6: buat batch pengumpulan utama baru |
| Menambah jumlah/keragaman query di luar accepted sekarang | Bagian 3: ambil PAA tambahan, lalu review |
| Memperbaiki label, review, atau fitur dari HTML yang sudah ada | Bagian 9: bangun ulang dataset lokal |

Snapshot terakhir: **302 query accepted**, terdiri dari 41 query pada `main_01` dan **261 query tambahan belum diproses dalam pengumpulan utama**. Dari kandidat artikel yang memenuhi syarat pada `main_01`, 20 dari 870 URL sudah dicoba. Jadi kamu masih bisa menambah dataset tanpa mencari PAA baru terlebih dahulu. Angka ini adalah catatan progres, bukan jumlah yang selalu tetap setelah kamu melanjutkan.

## 2. Kuota apa yang dipakai?

Istilah SerpApi yang tepat adalah **kredit/kuota pencarian**, sedangkan Gemini memakai **token input/output dan ketentuan biaya tool grounding**. Satu panggilan Gemini bukan satu token.

| Kegiatan pada alur ini | Kuota pencarian SerpApi | Token/biaya Gemini | Keterangan |
| --- | --- | --- | --- |
| Mengunduh CSV lewat antarmuka Google Trends | Tidak | Tidak | Dilakukan di browser |
| Preview skrip tanpa `--run` | Tidak | Tidak | Memeriksa rencana lokal |
| Mengambil PAA baru dengan `collect_paa.py --run` | Ya, anggarkan 1 pencarian per keyword baru | Tidak | Satu respons dapat menghasilkan beberapa PAA atau tidak ada PAA |
| Mengambil teks PAA dari respons JSON tersimpan | Tidak | Tidak | `prepare_query_expansion.py` |
| Review query sendiri di Notebook 05 | Tidak | Tidak | Notebook tidak memanggil LLM untuk menilai otomatis |
| Mengambil Google Top-10 untuk query baru | Ya, anggarkan 1 pencarian per query | Tidak untuk langkah Google organiknya | Bukan 10 pencarian untuk 10 URL |
| Mengambil tiga jawaban Gemini per query | Tidak | Ya | Grounding Google internal Gemini tidak menggunakan key SerpApi |
| Menjalankan `collect_main_dataset.py --run` | Ya untuk Google yang belum dikumpulkan | Ya untuk slot Gemini yang belum dikumpulkan | Satu perintah menjalankan kedua langkah di atas |
| `collect_main_dataset.py --export-only` | Tidak | Tidak | Ekspor respons tersimpan |
| Mengunduh halaman URL melalui scraper | Tidak | Tidak | Akses langsung website; memakai internet dan penyimpanan |
| Ekstraksi teks, fitur, BM25, dan embedding lokal | Tidak | Tidak | Model embedding diunduh jika belum ada; komputasi CPU lokal |
| Penetapan otoritas domain biner | Tidak | Tidak | Suffix dan daftar host dibaca dari konfigurasi lokal; host lain otomatis Level 1 |
| Retry scraping URL gagal | Tidak | Tidak | Tetap mengikuti aturan akses website |
| Mengulang pencarian Google atau panggilan Gemini | Bisa memakai lagi | Bisa memakai lagi | Bergantung layanan yang benar-benar dipanggil |

Gemini dapat memiliki biaya grounding selain token, bergantung model dan paket. Jumlah pencarian internal juga tidak harus sama dengan jumlah jawaban. Periksa [harga resmi Gemini](https://ai.google.dev/gemini-api/docs/pricing) dan [ketentuan Google Search grounding](https://ai.google.dev/gemini-api/docs/generate-content/google-search) sebelum menjalankan batch; panduan ini tidak menetapkan tarif rupiah tetap. Sisa kredit SerpApi dapat diperiksa melalui dashboard atau [Account API](https://serpapi.com/account-api), yang juga dipakai kolektor proyek untuk pemeriksaan kuota.

Contoh anggaran: mencari PAA dari **10 keyword**, kemudian memproses **30 query accepted baru**, berarti rencanakan **40 pencarian SerpApi** dan **90 panggilan Gemini**. Jumlah token Gemini baru diketahui dari respons/penggunaan aktual. Jumlah artikel yang nantinya diunduh tidak menambah pencarian SerpApi. Sisakan cadangan sesuai konfigurasi; jangan menganggap respons error pasti tidak menggunakan kuota.

Aktifkan environment terlebih dahulu:

```powershell
cd D:\Kuliah\TA\final-assignment
.\venv\Scripts\Activate.ps1
```

Untuk scraping/fitur, jika dependensi belum terpasang:

```powershell
python -m pip install -r requirements-articles.txt
```

Kunci berada di `.env`: `SERPAPI_API_KEY` dan `GEMINI_API_KEY`. Jika key yang sama juga disetel sebagai environment variable, nilainya mengalahkan `.env`; mengganti `.env` saja tidak mengganti nilai environment yang masih aktif. Jangan menulis key di notebook atau file yang dikirim ke GitHub.

## 3. Mengambil PAA tambahan dari keyword Trends

**Biaya: SerpApi saat `--run`; tidak memakai Gemini.**

### 3.1. Pilih keyword sumber yang sah

Buka `data/interim/review/needs_paa.csv`. Pilih `source_text` dengan `research_domain` yang sesuai. Kolektor hanya menerima keyword yang tercatat di sana dengan status `needs_paa`; teks harus sesuai sumber, bukan keyword karangan baru.

Periksa daftar pencarian lama pada `data/interim/paa/<batch_id>/searches.csv`. Utamakan keyword yang belum diambil. Kolektor menyimpan checkpoint berdasarkan query dan parameter, sehingga membuat `batch_id` baru dengan keyword/parameter identik **tidak memaksa pencarian ulang**. Reset kuota bulanan juga tidak menghapus checkpoint lokal.

Jika semua keyword Trends sudah dicoba, kamu masih bisa mengambil PAA dari respons Google pengumpulan utama yang tersimpan pada bagian 4. Ini memperluas pertanyaan dari turunan keyword Trends sambil mempertahankan hubungan sumber. Skrip sekarang belum melakukan klik/ekspansi PAA rekursif secara langsung melalui endpoint lanjutan.

Jika ingin menambah unduhan Trends dengan periode baru, simpan sebagai sumber periode baru beserta wilayah, kategori, tanggal, dan filter. Jangan menimpa enam CSV lama atau mengubah urutan barisnya: ID sumber lama bergantung urutan. Alur penggabungan Trends saat ini membaca enam nama file tetap; penambahan periode baru perlu penyesuaian ingest, bukan sekadar menaruh CSV tambahan di folder `data`.

### 3.2. Buat konfigurasi PAA baru

Salin `configs/paa_expansion_04.json` menjadi `configs/paa_expansion_05.json`. Ubah:

| Kolom | Cara mengisi |
| --- | --- |
| `batch_id` | `paa_expansion_05`, gunakan ID baru yang belum dipakai |
| `purpose` | Alasan dan waktu penambahan data |
| `topics` | Daftar keyword yang dipilih, dikelompokkan menurut kesehatan/keuangan/teknologi |
| `max_searches` | Minimal sebanyak total keyword yang tercantum; untuk 6 keyword, isi 6 |
| `quota_reserve` | Kredit yang harus tersisa, misalnya 10 |
| `parameters` | Pertahankan parameter lokasi/bahasa/perangkat agar konsisten |

Contoh bentuk `topics` berikut adalah **placeholder**, ganti dengan teks yang benar-benar ada di `needs_paa.csv`:

```json
{
  "kesehatan": ["TEKS_KEYWORD_KESEHATAN"],
  "keuangan": ["TEKS_KEYWORD_KEUANGAN"],
  "teknologi": ["TEKS_KEYWORD_TEKNOLOGI"]
}
```

Jangan hanya menaikkan `max_searches`: jumlah keyword ditentukan oleh `topics`. Kolektor ini tidak memiliki opsi `--max-new-searches`; pembatasan dilakukan melalui daftar keyword pada config.

### 3.3. Preview, kemudian ambil

```powershell
python src/collect_paa.py --config configs/paa_expansion_05.json
python src/collect_paa.py --config configs/paa_expansion_05.json --run
```

Jalankan baris pertama dahulu dan periksa daftar/jumlah keyword. Baris kedua memanggil API. Untuk melanjutkan batch yang terputus, jalankan kembali baris kedua; checkpoint yang sudah ada dilewati.

Hasil:

- `data/interim/paa/paa_expansion_05/searches.csv`: status pencarian per keyword.
- `data/interim/paa/paa_expansion_05/questions.csv`: teks pertanyaan PAA beserta jejak sumber.
- `data/raw/paa/batches/paa_expansion_05/manifest.json`: konfigurasi dan sumber yang dibekukan.
- `data/raw/paa/requests/`: respons/checkpoint pencarian.

`no_paa` berarti respons tidak menyediakan PAA, bukan query otomatis tidak valid. `error` atau `started` tetap dilewati pada resume; jangan menghapus checkpoint untuk memaksa retry karena request sebelumnya mungkin sudah memakai kredit.

## 4. Mengambil query dari PAA yang sudah tersimpan

**Biaya: tidak memakai SerpApi maupun Gemini.**

Edit `configs/query_expansion_01.json`: tambahkan `paa_expansion_05` di daftar `paa_batches`, **pertahankan seluruh batch lama**. Jika kelak `main_02` sudah berisi hasil Google, tambahkan juga `main_02` ke `main_batches` untuk mengekstrak PAA dari respons Google tersebut tanpa pencarian baru.

Jalankan:

```powershell
python src/prepare_query_expansion.py --config configs/query_expansion_01.json
```

Skrip mengekstrak `related_questions`, mempertahankan teks asli dan hubungan ke Trends/query induk, menggabungkan kemunculan, serta membaca keputusan review yang sudah ada. Tidak ada sintesis query dengan LLM.

Buka folder `data/interim/query_expansion/query_expansion_01/`:

| File | Yang kamu periksa |
| --- | --- |
| `source_pool.csv` | Seluruh kemunculan dan provenance PAA |
| `candidates.csv` | Kandidat unik beserta bahasa dan status seleksi |
| `pending.csv` | Kandidat yang belum diputuskan |
| `needs_review.csv` | Kandidat yang masih memerlukan pertimbangan |
| `accepted_new.csv` | Query yang telah diterima pada pool ekspansi |
| `excluded.csv` | Query yang dikeluarkan beserta alasan |

Nama **`accepted_new.csv` berarti tambahan terhadap pool awal**, bukan otomatis “belum pernah dikirim pada semua batch utama”. Setelah membuat `main_02`, sebagian isinya bisa sudah diproses. Karena itu bagian 6 memfilter berdasarkan seluruh manifest batch utama sebelum membuat daftar berikutnya.

## 5. Review query di Notebook 05

**Biaya: tidak memakai kedua API.**

1. Buka `notebooks/05_review_query_expansion.ipynb` dengan kernel environment proyek.
2. Jalankan sel import/pemuatan dan sel yang menjalankan `prepare(config)`.
3. Pada sel filter, isi `STATUS = 'pending'` untuk kandidat baru, atau `STATUS = 'needs_review'`. Isi `DOMAIN = ''` untuk semua domain.
4. Baca `query_text`, domain, dan sumbernya. Terima jika kebutuhan informasinya dapat dipahami dari teks, sesuai domain, berbahasa Indonesia, dapat dijawab melalui artikel, dan tidak mengulang intent yang sudah dipilih.
5. Tambahkan keputusan pada dictionary **`decisions_by_text`** di bagian **Koreksi keputusan oleh peneliti**. Pertahankan entri lama. Teks key harus persis dari tabel.
6. Jalankan sel keputusan tersebut, lalu sel akhir yang menampilkan `accepted_new.csv`.

Contoh satu entri yang ditambahkan **hanya jika teks tersebut ada pada kandidatmu**:

```python
'Kenapa harga saham anjlok?': {
    'language': 'id',
    'status': 'accepted',
    'reason': 'Meminta penjelasan umum penyebab penurunan harga saham; tidak harus menunjuk satu emiten.',
},
```

Gunakan `excluded` jika maksudnya memerlukan tebakan konteks, di luar domain, navigasional semata, atau duplikat intent. Jangan menerima/menolak berdasarkan dugaan apakah Gemini akan berhasil mensitasi. Premis pertanyaan boleh dikoreksi oleh jawaban; pertanyaan yang jelas tidak berarti premisnya benar.

Alasan review adalah metadata, tidak ditambahkan ke prompt Gemini. Jangan memperjelas teks sumber dengan parafrasa diam-diam. Keputusan tersimpan di `data/manual/query_expansion_01_decisions.csv`; hasil `accepted_new.csv` dibentuk ulang dari keputusan itu.

Blok penilaian asisten dalam notebook berisi keputusan historis untuk ID tertentu, **bukan layanan LLM yang otomatis menilai semua kandidat baru**. Query baru tetap perlu kamu review. Jika teks identik muncul di beberapa domain, periksa `cross_domain_duplicate`; skrip dapat mempertahankannya sebagai `needs_review` meski keputusan menyatakan accepted.

## 6. Buat daftar tetap untuk batch query utama berikutnya

**Biaya: persiapan lokal ini tidak memakai API.**

Jangan mengganti daftar query pada `main_01`. Untuk contoh berikut gunakan `main_02`, dengan **30 query baru** agar anggaran mudah dikendalikan. Angka 30 boleh diganti sebelum batch dimulai. Untuk batch berikutnya gunakan `main_03`, dan seterusnya.

Buat satu sel baru di Notebook 05, setelah review, untuk membuat snapshot query. Cuplikan ini hanya menyalin data lokal, menyaring query yang sudah tercatat pada manifest utama, dan memilih secara bergantian antar domain:

```python
import csv
import json
from pathlib import Path

BATCH_ID = 'main_02'  # ganti menjadi main_03, dst. untuk batch lain
MAX_QUERIES = 30
assert MAX_QUERIES > 0
root = next(p for p in [Path.cwd(), *Path.cwd().parents]
            if (p / 'src/collect_main_dataset.py').exists())
source = root / 'data/interim/query_expansion/query_expansion_01/accepted_new.csv'
target = root / 'data/manual' / f'{BATCH_ID}_queries.csv'

if target.exists():
    raise FileExistsError(f'Snapshot sudah ada: {target}. Jangan timpa daftar batch berjalan.')

used_ids, used_texts = set(), set()
for path in (root / 'data/raw/main').glob('*/manifest.json'):
    manifest = json.loads(path.read_text(encoding='utf-8-sig'))
    for row in manifest['queries']:
        used_ids.add(row['query_id'])
        used_texts.add(' '.join(row['query_text'].casefold().split()))

with source.open(encoding='utf-8-sig', newline='') as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    available = [r for r in reader
                 if r['selection_status'] == 'accepted' and r['language'] == 'id'
                 and r['query_id'] not in used_ids
                 and ' '.join(r['query_text'].casefold().split()) not in used_texts]

buckets = {d: [r for r in available if r['domain'] == d]
           for d in sorted({r['domain'] for r in available})}
selected, selected_ids, selected_texts = [], set(), set()
for i in range(max((len(v) for v in buckets.values()), default=0)):
    for bucket in buckets.values():
        if i >= len(bucket) or len(selected) >= MAX_QUERIES:
            continue
        row = bucket[i]
        key = ' '.join(row['query_text'].casefold().split())
        if row['query_id'] in selected_ids or key in selected_texts:
            continue
        selected.append(row)
        selected_ids.add(row['query_id'])
        selected_texts.add(key)

if not selected:
    raise ValueError('Tidak ada query accepted yang belum dijadwalkan.')
target.parent.mkdir(parents=True, exist_ok=True)
with target.open('x', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(selected)
print('Snapshot:', target, '| query:', len(selected))
```

Filter menganggap seluruh query pada manifest lama sudah dijadwalkan, termasuk yang gagal atau belum selesai. Query tersebut dilanjutkan pada batch lamanya, tidak dijadikan query baru. Buat batch satu per satu; snapshot yang baru dibuat tetapi belum punya manifest belum terbaca oleh filter ini. Pemilihan bergantian adalah aturan operasional yang perlu dicatat, bukan pengambilan sampel acak.

Salin `configs/main_dataset.json` menjadi `configs/main_dataset_02.json`. Pada salinan ubah:

```json
"dataset_id": "main_02",
"query_csv": "data/manual/main_02_queries.csv",
"max_serp_searches": 30
```

Ini cuplikan tiga kolom yang diubah, bukan isi file JSON lengkap. `max_serp_searches` harus minimal sebanyak query pada snapshot; bukan perintah untuk memilih 30 baris dari CSV yang lebih besar.

Pertahankan `repetitions: 3`, `min_valid_trials: 2`, model, prompt, parameter Google, dan aturan waktu jika protokol penelitian tetap sama. `citation_threshold` kolektor boleh tetap `null`: proporsi disimpan dan builder memberi label 0,5 sesuai konfigurasi contoh yang telah disetujui. Sebelum pemodelan final, dokumentasikan ambang yang dipakai secara konsisten. Perubahan model/prompt/batas output karena kendala perlu dicatat sebagai perubahan protokol pada batch baru.

## 7. Kumpulkan Google Top-10 dan sitasi Gemini

**Biaya: memakai SerpApi dan Gemini saat `--run`.**

```powershell
# Preview, tanpa API
python src/collect_main_dataset.py --config configs/main_dataset_02.json

# Kerjakan maksimal 3 query yang belum selesai pada eksekusi ini
python src/collect_main_dataset.py --config configs/main_dataset_02.json --run --max-queries 3
```

Ulangi perintah kedua untuk melanjutkan. Untuk satu eksekusi pada tiga query baru, anggarkan sampai **3 pencarian SerpApi dan 9 panggilan Gemini**. `--max-queries` membatasi eksekusi, tidak mengubah daftar tetap batch. Hilangkan opsi itu hanya jika ingin memproses seluruh sisa batch dengan anggaran memadai.

Setiap query mengambil satu respons Google organik dan tiga slot Gemini. Jumlah hasil Google boleh kurang dari 10. Gemini menyimpan semua sumber yang terhubung dengan sitasi pada respons; tidak dibatasi satu URL. Kegagalan satu slot tidak otomatis memicu percobaan keempat. Minimal dua percobaan valid diperlukan, bersama syarat pengumpulan lengkap dan jeda Google–Gemini maksimal enam jam untuk kelayakan scraping pada implementasi sekarang. Selesaikan satu query dalam rentang ini; jangan sengaja mengambil Googlenya sekarang lalu Gemininya bulan depan.

Hasil berada di `data/interim/main/main_02/`:

| File | Isi |
| --- | --- |
| `queries.csv` | Status Google/Gemini, jumlah valid, dan waktu |
| `trials.csv` | Respons per percobaan, status valid, penggunaan token, dan error |
| `google_results.csv` | Hasil organik Google |
| `sources.csv` | Semua sumber Gemini dan status resolusi URL |
| `query_article_pairs_union.csv` | Gabungan Top-10 dan seluruh URL sitasi dari percobaan valid |

Ekspor ulang tanpa API:

```powershell
python src/collect_main_dataset.py --config configs/main_dataset_02.json --export-only
```

Di Notebook 04, ganti referensi batch `main_01` pada sel pemuatan menjadi `main_02` untuk melihat batch baru. `google_status=not_requested` berarti kolektor belum meminta Google organik lewat SerpApi; itu bukan status grounding internal Gemini.

Selesaikan satu tahap pengumpulan/ekspor sebelum scraping. Scraper membekukan fingerprint file pasangan sumber; penambahan berikutnya dapat diterima dengan `--extend-manifest` sesuai bagian awal panduan, sedangkan perubahan nilai pasangan lama tetap ditolak.

## 8. Scraping URL artikel

**Biaya: tidak memakai SerpApi maupun Gemini.**

### 8.1. Melanjutkan URL dari main_01 yang sudah ada

Ini jalur paling langsung jika ingin menambah artikel sekarang:

```powershell
# Preview URL berikutnya
python src/scrape_articles.py --max-new-urls 20

# Ambil maksimal 20 URL baru
python src/scrape_articles.py --run --max-new-urls 20

# Ekstrak ulang HTML lokal dan perbarui seluruh dataset batch ini
python src/build_article_dataset.py --with-embeddings
```

Jika sebelumnya sudah mencoba 20 URL, batas 20 berikutnya berarti total menjadi sampai 40 URL dicoba, bukan tetap 20. URL gagal tetap dihitung sebagai upaya dan tidak diganti diam-diam. Menjalankan ulang melewati semua checkpoint lama; skrip tidak mengulang otomatis kegagalan.

**Jalankan juga perintah builder setelah scraping**: scraper menyimpan HTML/checkpoint dan status pengambilan, sedangkan builder memperbarui file dataset final. Setiap pembangunan ulang mengikutsertakan seluruh checkpoint lama dan baru pada batch itu, lalu otomatis menempatkan pasangan Google Top-10 ke `dataset.csv` dan Gemini-only ke `dataset_gemini_only.csv`. Tidak perlu memindahkan baris CSV sendiri. Artikel yang muncul pada kedua sumber untuk query yang sama masuk utama. URL gagal tetap tercatat dalam kelompok yang sesuai. `model_ready.csv` hanya mengambil pasangan utama yang lolos pemeriksaan.

Jika lewat Notebook 06, aktifkan `RUN_SCRAPING=True` pada sel terakhir: scraping diikuti builder secara otomatis. Setelah berhasil, jumlah utama/tambahan dimuat ulang dan folder hasil ditampilkan. Kembalikan sakelar ke False setelah menjalankannya.

### 8.2. Scraping URL dari main_02

Konfigurasi `configs/article_dataset_02.json` dan `configs/article_features_02.json` **sudah tersedia dan digunakan**. Jangan menimpanya. Snapshot yang ada menggunakan:

```json
"dataset_id": "articles_main_02",
"source_batches": ["main_02"]
```

Config fitur `_02` sudah mengarah ke config scraping `_02`. CSV review manual dipakai bersama karena memakai ID artikel dan hostname. Perintah berikut berlaku selama file sumber `main_02` masih sama dengan manifest scraping. Jika sudah bertambah, tambahkan `--extend-manifest` pada perintah scraper sesuai bagian awal panduan.

```powershell
python src/scrape_articles.py --config configs/article_dataset_02.json --max-new-urls 20
python src/scrape_articles.py --config configs/article_dataset_02.json --run --max-new-urls 20
python src/build_article_dataset.py --config configs/article_features_02.json --with-embeddings
```

Lanjutkan dengan perintah sama; ubah angka menjadi 50, misalnya, untuk maksimal 50 URL baru per eksekusi. Memperbesar batch scraping memerlukan waktu/internet/ruang disk, bukan kuota pencarian.

Hasil baru berada di `data/processed/articles_main_02/`; raw HTML dan checkpoint ada di `data/raw/articles/articles_main_02/`. Dataset baru memiliki checkpoint terpisah: jika URL pernah diambil pada `articles_main_01`, scraper **belum otomatis memakai ulang HTML lintas dataset_id**.

### 8.3. URL gagal dan retry

Status seperti `robots_unavailable`, `robots_disallowed`, `http_error`, `network_error`, atau `blocked_or_challenge` tetap dicatat. Halaman yang bisa dibuka secara manual belum tentu memberi respons sama untuk crawler.

Untuk mencoba kembali hanya URL berstatus gagal pada checkpoint:

```powershell
python src/scrape_articles.py --config configs/article_dataset_02.json --run --retry-failed --max-new-urls 3
python src/build_article_dataset.py --config configs/article_features_02.json --with-embeddings
```

Di mode retry, angka 3 membatasi percobaan ulang, bukan mengambil tiga URL baru. Riwayat lama dipertahankan, aturan robots tetap diperiksa. Periksa `original_crawl_status` juga: error ekstraksi awal yang sudah pulih di hasil processed masih dapat dipilih retry berdasarkan checkpoint mentah. Untuk HTML yang sudah tersedia, cukup jalankan builder lebih dahulu agar tidak mengunduh ulang tanpa perlu.

## 9. Review artikel, otoritas domain, fitur, dan label

**Biaya: tidak memakai kedua API dengan alat lokal yang tersedia.**

Buka `notebooks/06_inspect_article_dataset.ipynb`. Untuk batch baru, ubah **hanya `FEATURE_CONFIG`** pada sel pemuatan, misalnya menjadi `ROOT / 'configs/article_features_02.json'`, lalu jalankan ulang sel pemuatan. Config scraping, folder hasil, config otoritas domain, serta perintah scraping/build otomatis mengikuti config fitur tersebut. Jangan mengganti `OUTPUT` secara terpisah. Contoh artikel memilih Alodokter jika tersedia, atau artikel pertama pada batch; `ARTICLE_ID` tetap boleh kamu ganti untuk inspeksi. Untuk batch yang belum memiliki ekspor artikel sama sekali, jalankan terminal bagian 8 terlebih dahulu sebelum membaca tabel di notebook.

Periksa teks, judul, bahasa, dan jenis halaman. Pastikan isi bukan menu, ringkasan terpotong, halaman tantangan, listing aplikasi, atau halaman non-artikel. Website baru mungkin memerlukan penyesuaian ekstraktor jika template umumnya tidak cukup; skrip reusable tidak menjamin setiap situs berhasil tanpa penyesuaian.

Edit CSV review dengan mempertahankan header dan baris lama:

| File | Kolom yang kamu isi |
| --- | --- |
| `data/manual/article_review.csv` | `article_id,status,language,reason,reviewer,reviewed_at` |

Untuk artikel, gunakan `accepted`/`excluded` dan `language=id` jika isi Indonesia. Satu keputusan per `article_id`. Gunakan editor CSV yang mempertahankan UTF-8 dan tanda kutip pada nilai yang mengandung koma.

Otoritas domain tidak memerlukan review satu per satu. Aturannya:

| Level | Kriteria |
| --- | --- |
| 2 | Rumah sakit/klinik jelas; afiliasi lembaga OJK; perusahaan/platform teknologi PSE; `.ac.id`/`.go.id`; media besar yang jelas kredibel |
| 1 | Semua lainnya, termasuk status tidak jelas atau ambigu |

Suffix `.ac.id`/`.go.id` diproses otomatis. Untuk menambah host jelas Level 2 dari kategori lain, edit `configs/domain_authority.json` pada `level_2_hosts` dan berikan basis yang sesuai. Semua host yang tidak tercantum otomatis Level 1; tidak ada status provisional dan file `data/manual/source_credibility.csv` hanya menjadi arsip historis rubrik lama.

Builder juga menyalin `evidence_urls` dan `reason` dari arsip tersebut menjadi `credibility_evidence` dan `credibility_reason` untuk hostname yang cocok. Kolom ini hanya untuk audit dan tidak menjadi fitur model. Jika menambah bukti manual, gunakan satu baris per hostname, pisahkan beberapa URL dengan titik koma, dan pertahankan alasan serta tanggal pemeriksaan. Penilaian biner tetap ditentukan oleh `configs/domain_authority.json`, bukan angka historis `credibility_level` pada CSV audit.

Setelah mengubah review, bangun ulang:

```powershell
python src/build_article_dataset.py --config configs/article_features_02.json --with-embeddings
```

Selalu gunakan `--with-embeddings` jika ingin ekspor lengkap untuk model. Builder tanpa flag ini tetap mengekspor ulang tetapi tidak mengisi kemiripan semantik pada ekspor tersebut. Embedding lokal yang sudah cocok dengan teks/pengaturan akan memakai cache; tidak memanggil Gemini.

| Hasil pada `data/processed/<dataset_id>/` | Kegunaan |
| --- | --- |
| `articles.csv` | Teks/metadata/fitur dan status setiap URL yang dicoba |
| `dataset.csv` | Dataset utama: pasangan Google Top-10, termasuk yang juga disitasi Gemini dan yang belum layak |
| `dataset_gemini_only.csv` | Dataset tambahan: pasangan sitasi Gemini di luar Top-10 untuk query yang sama |
| `dataset_union.csv` | Arsip audit gabungan kedua kelompok |
| `model_ready.csv` | Hanya pasangan dataset utama yang lolos pemeriksaan |
| `feature_columns.json` | Daftar fitur yang boleh digunakan dan target |
| `summary.json` | Jumlah URL, artikel layak, pasangan, label, dan konfigurasi |

Ambang pada konfigurasi fitur contoh adalah **proporsi sitasi >=0,5**. Artikel disitasi sekali dari tiga percobaan valid mendapat label 0 menurut ambang ini. Pencocokan sitasi yang belum pasti tetap kosong, bukan dipaksakan 0. URL gagal tetap ada pada dataset audit walau tidak masuk model_ready. Kolom `not_ready_reason` menjelaskan kendalanya.

Pemisahan berdasarkan pasangan query-artikel: URL yang sama boleh menjadi Top-10 untuk query A dan tambahan Gemini-only untuk query B. `ready_for_analysis=True` pada tambahan berarti pemeriksaan lengkap, tetapi `ready_for_model=False` karena tambahan tidak termasuk model utama. Label tambahan tidak otomatis 1: keanggotaan berarti pernah disitasi, sedangkan label tetap mengikuti ambang. BM25 kedua kelompok memakai korpus referensi artikel eligible Google Top-10; tambahan yang tidak pernah menjadi Top-10 tidak memengaruhi statistik korpus utama.

## 10. Menggabungkan hasil beberapa batch

Simpan `main_01`, `main_02`, dan batch lain sebagai arsip terpisah. Untuk **satu snapshot artikel gabungan dengan BM25 pada korpus yang sama**, fitur scraper sekarang mendukung beberapa `source_batches`:

1. Tuntaskan dahulu pengumpulan utama semua batch sumber yang akan disertakan.
2. Salin config scraping ke `configs/article_dataset_combined_01.json`.
3. Isi `dataset_id` dengan `articles_combined_01` dan `source_batches` dengan `["main_01", "main_02"]`.
4. Salin config fitur ke `configs/article_features_combined_01.json`, arahkan `scrape_config` ke config gabungan tersebut.
5. Preview lalu jalankan bertahap:

```powershell
python src/scrape_articles.py --config configs/article_dataset_combined_01.json --max-new-urls 20
python src/scrape_articles.py --config configs/article_dataset_combined_01.json --run --max-new-urls 20
python src/build_article_dataset.py --config configs/article_features_combined_01.json --with-embeddings
```

Manifest gabungan menyatukan URL identik antarbatch dan mempertahankan pasangan query serta `source_batch`. Namun **ini snapshot scraping baru**: checkpoint/HTML dari dataset artikel terpisah belum dipakai ulang otomatis, sehingga website dapat diunduh kembali. Tidak ada panggilan SerpApi/Gemini, tetapi waktu snapshot HTML berubah. Jika ingin menghindari pengambilan ulang, simpan hasil batch terpisah dahulu; pemakaian ulang arsip lintas dataset memerlukan pengembangan tambahan dan belum tersedia sebagai opsi CLI.

Jangan sekadar menumpuk `model_ready.csv` lalu menganggap fitur BM25 sudah sebanding: korpus BM25 tiap batch bisa berbeda. Sebelum analisis, tetapkan snapshot korpus, kebijakan deduplikasi dan alias, serta pemisahan train/test per query dan kemungkinan topik induk. Informasi sitasi, asal kandidat, dan posisi Google adalah kolom audit yang tidak boleh tanpa pertimbangan dijadikan fitur prediksi.

## 11. Melanjutkan bulan depan tanpa mengulang dari awal

- **Batch sama, daftar sama, belum selesai:** jalankan kembali config dan ID yang sama. Data tersimpan dilewati; hanya pekerjaan yang belum diminta dilanjutkan sesuai aturan kolektor.
- **Query baru:** buat snapshot CSV dan `dataset_id` utama baru. Jangan menunjuk batch berjalan langsung ke `accepted_new.csv` yang terus berubah.
- **Keyword PAA tambahan:** gunakan `batch_id` PAA baru dan tambahkan ke config pool; perubahan ID tidak menonaktifkan cache/checkpoint request identik.
- **URL baru dalam manifest scraping yang sama:** ulangi scraper dengan `--max-new-urls`. Tidak perlu menulis source code baru.
- **Ekspor sumber bertambah dalam batch yang sama:** gunakan `--extend-manifest` untuk preview, lalu tambahkan `--run` untuk menyimpan perluasan dan mengambil URL; checkpoint lama dipertahankan.
- **Sumber main batch baru:** buat config/ID scraping baru; jangan mengedit `source_batches` manifest yang sudah berjalan.
- **Koreksi review/fitur:** edit CSV manual dan bangun ulang lokal, tanpa API.
- **Error API, status started, atau lock tertinggal:** periksa checkpoint dan proses lama dahulu. Jangan menghapus raw/checkpoint untuk mengejar status selesai. Resume bukan retry semua kegagalan.

Catat setiap penambahan pada `docs/PROGRESS.md`: tanggal, ID batch, sumber keyword/query, jumlah pencarian, jumlah respons valid, kuota sebelum/sesudah jika tersedia, jumlah URL dicoba/layak/gagal, perubahan protokol, penilai, serta versi konfigurasi. Dengan begitu data yang bertambah tetap dapat ditelusuri sampai sumber Trends/PAA dan respons Gemini yang membentuk labelnya.
