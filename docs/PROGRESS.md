# Progres penelitian

Terakhir diperbarui: **9 Oktober 2026**.

## 9 Oktober 2026: review seluruh sisa kandidat query PAA

Seluruh **850 kandidat pending** pada pool ekspansi dinilai menggunakan rubrik query yang sama: bahasa Indonesia, relevansi domain, intent yang berdiri sendiri, kebutuhan informasi yang dapat dibahas artikel, dan duplikasi kebutuhan informasi. Penilaian dilakukan oleh asisten Codex sebagai **LLM-as-a-judge untuk seleksi query**, dengan reviewer `asisten_rubrik_v1_20261009`. Teks PAA tidak ditulis ulang dan keberhasilan sitasi Gemini tidak digunakan sebagai kriteria.

| Domain | Accepted baru | Excluded baru |
| --- | ---: | ---: |
| Kesehatan | 272 | 103 |
| Keuangan | 198 | 99 |
| Teknologi | 112 | 66 |
| **Total** | **582** | **268** |

Penolakan terdiri dari 198 duplikasi kebutuhan informasi, 43 pertanyaan ambigu/tidak lengkap, dan 27 di luar domain atau cakupan artikel. Seluruh 582 query diterima belum masuk manifest `main_01`–`main_03`. Keputusan lama sebanyak 403 ID dipertahankan identik; file keputusan aktif sekarang berisi 1.253 ID. Ekspor pool menjadi **918 accepted dan 335 excluded**, tanpa pending/needs_review. Angka 918 mencakup 336 query ekspansi yang sudah dipakai; snapshot khusus kandidat belum terjadwal berisi 582 baris. Bersama 381 query yang sudah terjadwal pada batch 1–3, terdapat 963 query terjadwal atau tersedia, bukan 963 query selesai maupun artikel model-ready.

Teks, status, alasan per baris, reviewer, provenance, serta `duplicate_of` dan teks wakil duplikat tersimpan pada [review lengkap](../data/manual/query_expansion_20261009_review.csv). Kandidat siap dipilih untuk batch selanjutnya terdapat pada [accepted_unused_20261009.csv](../data/interim/query_expansion/query_expansion_01/accepted_unused_20261009.csv). Rincian rubrik, contoh, batas pelaporan, serta penggunaan berkas dicatat pada [laporan review query](REVIEW_QUERY_20261009.md). Keputusan pipeline sudah diterapkan ke `data/manual/query_expansion_01_decisions.csv`; belum dibuat snapshot pengumpulan `main_04`.

Validasi lokal memastikan cakupan seluruh kandidat, alasan terisi, rujukan duplikat valid, keputusan lama dan teks PAA tetap identik, serta integritas ketiga manifest pengumpulan. Tidak ada penggunaan kuota SerpApi/Gemini atau perubahan dataset artikel. Review hanya memakai sumber ekspansi yang sudah aktif, termasuk PAA tersimpan dari `main_01` dan `main_02`; PAA tambahan dari `main_03` berada di luar cakupan snapshot ini. Hasil merupakan penilaian asisten yang dapat dikoreksi manusia, bukan validasi independen antarpenilai. Backup, anotasi, skrip penerapan, dan hitungan terdapat pada `outputs/query_review_20261009`.

## 8 Oktober 2026: verifikasi artikel batch 3

Sebanyak 222 dari 1.217 URL pada manifest batch `articles_main_03` sudah memiliki checkpoint scraping; audit ini hanya mencakup 222 URL tersebut. Menurut [rubrik kelayakan artikel](RUBRIK_SELEKSI_ARTIKEL.md), 114 halaman berhasil diekstraksi dengan minimal 100 kata; 12 sudah memiliki keputusan manual dari batch lama, sedangkan 102 baru dinilai berdasarkan judul dan bagian awal/tengah/akhir teks, dengan pemeriksaan teks/HTML lebih panjang untuk kasus meragukan. Hasil baru: **87 accepted, 8 excluded, 7 needs_extraction_review**. Sebanyak 108 URL lain tertahan oleh kegagalan crawl atau teks di bawah ambang; tidak dinilai sebagai artikel tanpa bukti isi. Keputusan lama 893 ID tetap identik, dan file review aktif kini memuat 995 ID unik.

Builder batch 3 dijalankan ulang dari HTML dan cache embedding lokal. Pasangan utama tetap 222 dan tambahan Gemini-only tetap 1; jumlah label dasar tidak berubah. Artikel eligible naik dari 78 menjadi 99, dan **model_ready naik dari 75 menjadi 96 pasangan**, dengan 30 kesehatan, 32 keuangan, 34 teknologi, serta 62 label 0 dan 34 label 1. Sebanyak 20 baris model-ready belum memiliki usia publikasi; nilai itu dipertahankan kosong untuk penanganan saat pelatihan. Tiga artikel yang diterima masih tertahan akibat `url_matching_uncertain`; satu artikel berstatus accepted sebelumnya gagal diunduh pada batch ini. Tidak ada penggunaan kuota SerpApi atau Gemini. Keputusan, alasan, bukti teks, hambatan teknis, serta ringkasan validasi tercatat pada [audit batch 3](../outputs/article_verification_20261008_main03/REVIEW.md).

## 8 Oktober 2026: pemulihan Gemini 503 tanpa pencarian Google baru

Checkpoint `main_03` diperiksa setelah tiga penghentian akibat Gemini `503 / UNAVAILABLE`. Terdapat 13 query yang sudah dimulai: 9 selesai, 3 memiliki hasil Google selesai tetapi Gemini terputus, dan 1 gagal pada Google. Sebanyak 62 query belum dimulai. Tersimpan 32 slot Gemini: 29 respons selesai dan 3 error 503. Saldo SerpApi terakhir dalam log pengguna adalah 119 pencarian; angka ini tidak diperiksa ulang melalui jaringan. Mengecilkan `--max-queries` tidak memperbaiki gangguan layanan, sedangkan `--unstarted-only` terus memakai pencarian Google untuk query berikutnya.

`src/recover_main_gemini.py` kini menerima HTTP 503 sebagai kegagalan yang boleh dipulihkan satu kali per slot, selain timeout/jaringan. Flag `--finish-incomplete` juga mengisi slot yang belum dimulai pada query yang hasil Googlenya sudah selesai. Jumlah panggilan recovery dan slot baru bersama-sama dibatasi `--max-new-calls`. Query baru tidak dimulai dan tidak ada panggilan SerpApi. Respons tersimpan digunakan kembali; kegagalan lama masuk `recovery_history`. Respons selesai yang tidak memenuhi grounding tidak diulang untuk mengejar hasil positif. Model, prompt, tiga slot penelitian, minimal dua valid, dan ambang label tetap sama.

Sebelum setiap panggilan baru, jendela enam jam diperiksa terhadap waktu Google dan slot tersimpan. Query kedaluwarsa, Google belum selesai, atau trial `started` yang hasilnya tidak pasti dilewati. Jika layanan kembali gagal, proses berhenti dan checkpoint tetap tersimpan. Pesan error 503 sekarang mengarahkan pengguna ke recovery, bukan memulai query baru. Preview lokal menemukan tujuh panggilan potensial untuk tiga query Gemini terputus (tiga retry dan empat slot belum dimulai); kelayakan waktu harus dicek lagi saat eksekusi.

Contoh preview dan eksekusi terbatas:

```powershell
python src/recover_main_gemini.py --config configs/main_dataset_03.json --finish-incomplete
python src/recover_main_gemini.py --config configs/main_dataset_03.json --finish-incomplete --run --max-new-calls 1
```

Validasi: **41 tes lulus** pada modul recovery, klien Gemini, pengumpulan utama, dan runner. Pengujian menggunakan respons simulasi, termasuk batas panggilan, arsip error 503, penghentian jika retry gagal, kelanjutan slot tersisa, idempotensi, dan penolakan jendela kedaluwarsa/checkpoint tidak pasti. Tidak ada panggilan Gemini/SerpApi berbayar atau perubahan checkpoint pengumpulan riil pada pengerjaan ini. Perbaikan mengatasi kelanjutan proses; ketersediaan layanan Gemini tetap bergantung pada penyedia.

## 7 Oktober 2026: persiapan batch utama `main_03`

Seluruh 261 respons Google `main_02` yang berstatus selesai diperiksa sebagai sumber PAA lokal tanpa pencarian baru. Ekspansi sekarang membaca `main_01` dan `main_02`; pembacaan `paa_depth` kosong dari empat kueri lama diperbaiki dengan fallback ke kedalaman PAA pertama. Empat tes ekspansi dan enam tes runner lulus. Dari 925 kandidat PAA baru yang sebelumnya pending, LLM memilih **75 kueri** yang jelas maksudnya dan tidak mengulang ID/teks kueri batch 1–2: **25 kesehatan, 25 keuangan, 25 teknologi**. Sisa **850 kandidat** tetap pending untuk seleksi lanjutan, bukan excluded.

Snapshot terkunci di `data/manual/main_03_queries.csv`. Keputusan dan alasan berada di `data/manual/query_expansion_01_decisions.csv`; daftar teks terpilih ada di `configs/main_03_query_selection.json`. Konfigurasi `configs/main_dataset_03.json` mempertahankan model, prompt, tiga percobaan, minimal dua valid, jendela enam jam, dan ambang label 0,5; `max_serp_searches` diset 75 dengan cadangan 10. Konfigurasi scraping dan fitur terpisah tersedia sebagai `configs/article_dataset_03.json` dan `configs/article_features_03.json`.

Runner `continue_main_dataset.py` kini menerima `--config` agar batch baru tidak tanpa sengaja menjalankan `main_02`; tanpa opsi itu perilaku lama tetap berlaku. Preview lokal untuk `main_03` berhasil menunjukkan 75 kueri seimbang. **Belum ada permintaan SerpApi, Gemini, ataupun scraping artikel untuk batch 3.** Maksimum terjadwal adalah 75 pencarian dan 225 percobaan Gemini, yang dapat dikerjakan bertahap. Perintah lengkap tercatat di [MULAI_BATCH_03.md](MULAI_BATCH_03.md). Kegagalan HTTP 503 pada empat checkpoint `main_02` tidak menghalangi snapshot `main_03`, tetapi perlu tetap dilaporkan sebagai sisa batch 2.

## 7 Oktober 2026: empat checkpoint Google `main_02` yang belum selesai

Setelah perintah `continue_main_dataset.py --run --max-queries 8 --check-every 5` dijalankan, **261 dari 265 kueri** berstatus `completed`. Empat kueri lain berstatus `started`: tiga pencarian Google mencatat **HTTP 503** tanpa respons tersimpan (`query_169786ad40e908636b010d5b`, `query_214008bd53b6e4ede63170d9`, `query_6cf188a6d39cc7102864d813`), sedangkan satu checkpoint (`query_6ee1458a9e019f676561dbf6`) masih `google.status=started` tanpa respons. Keempatnya belum memulai percobaan Gemini. Runner menghentikan proses pada checkpoint pertama karena tidak mengulang permintaan Google yang hasilnya gagal atau belum pasti secara otomatis.

Skrip `src/recover_main_google.py` yang sudah ada dicoba dua kali untuk `query_169786ad40e908636b010d5b` (sekali oleh asisten, sekali oleh pengguna) dan sekali untuk kueri berbeda, `query_214008bd53b6e4ede63170d9`. Ketiganya kembali menerima **HTTP 503**. Tidak ada respons Google baru atau panggilan Gemini; kegagalan lama tersimpan dalam `google_recovery_history`, sedangkan checkpoint aktif tetap berstatus error. Pemeriksaan akun setelah percobaan pertama dan sebelum percobaan kueri kedua sama-sama mencatat **131 pencarian tersisa** (119/250 terpakai), sehingga percobaan gagal yang teramati tidak mengurangi kredit. Dua checkpoint lain tidak dicoba ulang pada pemeriksaan ini.

Sesudah layanan pencarian kembali berhasil, jalankan pemulihan eksplisit **per ID** dengan `python src/recover_main_google.py --config configs/main_dataset_02.json --query-id QUERY_ID --run`, lalu lanjutkan `continue_main_dataset.py` tanpa `--unstarted-only`. Bila sumber pasangan bertambah, perluas manifest scraping `articles_main_02` dengan `--extend-manifest`, ambil URL Top 10 baru, lalu build ulang. Kuota dapat berubah setelah snapshot ini.

## 7 Oktober 2026: verifikasi artikel hasil crawling lanjutan

Sebanyak **561 artikel unik** pada cakupan Google Top 10 diperiksa menggunakan rubrik bahasa, jenis halaman, kecukupan isi, serta keutuhan/kebersihan ekstraksi. Kandidat berasal dari artikel baru dan antrean review yang belum diputuskan, termasuk 310 artikel yang sebelumnya lolos otomatis. Judul dan cuplikan awal/tengah/akhir dibaca oleh LLM; kasus meragukan ditelusuri pada teks lebih panjang serta HTML lokal. Label sitasi tidak menjadi dasar keputusan, dan tidak dilakukan pemeriksaan kebenaran setiap klaim atau pengukuran Cohen's kappa.

Hasilnya **419 accepted, 91 excluded, dan 51 needs_extraction_review**. Katalog, alat/kalkulator, forum, agregasi posting, abstrak tanpa badan makalah, dan narasi utama non-Indonesia dikecualikan. Artikel bersambung yang terpotong, isi tercampur berita lain/spam, atau kehilangan bagian utama ditahan. Keputusan lama sebanyak **332 tetap identik**; total aktif menjadi **893 ID unik** pada `data/manual/article_review.csv`.

Kedua batch dibangun ulang dengan HTML dan embedding lokal. Sebelum audit ini, crawling lanjutan telah menambah dataset utama `main_02` menjadi 2.165 pasangan, sehingga baseline berikut berbeda dari laporan audit 6 Oktober sebelumnya.

| Batch | Pasangan utama | Model-ready sebelum | Masuk | Ditarik | Model-ready sesudah |
| --- | ---: | ---: | ---: | ---: | ---: |
| main_01 | 325 | 186 | 0 | 0 | 186 |
| main_02 | 2.165 | 775 | 172 | 62 | 885 |
| **Total** | **2.490** | **961** | **172** | **62** | **1.071** |

Pertambahan bersih **110 pasangan**. Sebanyak 62 pasangan yang ditarik berasal dari 61 artikel yang sebelumnya lolos otomatis, tetapi hasil review menunjukkan masalah jenis halaman atau ekstraksi. Lima pasangan dari artikel accepted dalam audit ini masih tertahan: empat karena `url_matching_uncertain`, satu karena duplikasi pasangan. Semua penarikan dapat ditelusuri ke keputusan review; label, proporsi, dan hitungan sitasi seluruh pasangan tetap sama.

Model-ready berisi **826 label 0 / 245 label 1**, dengan kesehatan 504, keuangan 396, teknologi 171. Jumlahnya setara 993 ID artikel, 986 URL identitas artikel, dan 260 query; 1.071 pasangan query-identitas artikel berbeda. Hasil tetap tersimpan pada dua berkas `articles_main_01/model_ready.csv` dan `articles_main_02/model_ready.csv`, belum satu berkas training gabungan. Sebanyak 284 baris memiliki fitur kosong (usia publikasi 278, rerata panjang paragraf 11, beririsan lima), sehingga penanganan nilai hilang tetap diperlukan dalam pipeline pemodelan.

Tidak ada lagi antrean `needs_language_review`/`needs_page_type_review` pada dataset utama. **1.419 pasangan belum model-ready**, termasuk 57 pasangan yang memerlukan perbaikan ekstraksi, kegagalan teknis, teks terlalu pendek, halaman di luar cakupan, dan masalah pasangan lainnya. Di luar 561 kandidat, 675 ID baru masih memiliki hambatan teknis dan tidak dinilai isinya tanpa teks yang cukup. Audit tidak menyatakan seluruh korpus lama telah dinilai LLM: 345 baris model-ready masih menggunakan artikel `eligible_auto` di luar cakupan ini.

Rubrik: `docs/RUBRIK_SELEKSI_ARTIKEL.md`. Laporan lengkap: `docs/VERIFIKASI_ARTIKEL_LANJUTAN_20261007.md`. Keputusan per artikel, bukti, snapshot sebelum perubahan, log build, dan hasil dua validasi tersimpan di `outputs/article_verification_20261006_followup/`. Hash seluruh 561 teks sumber cocok setelah build; empat variasi teks lintas batch diperiksa terpisah dan tidak mengubah keputusan. Definisi 37 fitur tetap sama. **Tidak ada penggunaan kuota SerpApi/Gemini API atau crawling baru pada proses ini.**

## 6 Oktober 2026: verifikasi antrean artikel Google Top 10

Atas permintaan untuk memverifikasi artikel yang sudah di-crawl, antrean dataset utama ditinjau berdasarkan bahasa, jenis halaman, dan kelengkapan teks. Cakupan **218 artikel unik / 237 pasangan query-artikel** dari dua batch mencakup Google Top 10 serta irisan Top 10 dengan sitasi Gemini. Artikel yang hanya muncul pada dataset tambahan Gemini-only tidak termasuk antrean review ini.

Pemeriksaan berbantuan LLM menghasilkan **163 artikel accepted, 50 excluded, dan 5 needs_extraction_review**. Keputusan didasarkan pada teks dan HTML lokal, bukan label sitasi. Artikel/panduan Indonesia yang substantif diterima; katalog, listing, dan halaman non-artikel dikecualikan. Penilaian ini bukan verifikasi manusia independen atau pemeriksaan kebenaran setiap klaim dalam artikel.

Keputusan aktif disimpan di `data/manual/article_review.csv`. Dari 118 keputusan lama, 116 dipertahankan identik; dua status ekstraksi Hello Sehat diperbarui setelah badan artikelnya berhasil dipulihkan. Sebanyak 214 keputusan baru ditambahkan sehingga terdapat 332 keputusan aktif. Audit per artikel, alasan, cuplikan bukti, backup, hash sumber, dan validasi build tersedia di `outputs/article_verification_20261006/`. Laporan lengkap: `docs/VERIFIKASI_ARTIKEL_20261006.md`.

Empat artikel dipulihkan tanpa crawling ulang: dua Hello Sehat yang sebelumnya mengambil daftar referensi Inggris (1.762 dan 632 kata Indonesia), Rumah Ginjal yang tercampur daftar kata kunci (817 kata), dan AXA Mandiri yang tercampur kartu artikel/footer (1.582 kata). Selector badan artikel ditambahkan pada ekstraktor agar berlaku juga pada proses selanjutnya. Dua paragraf promosi yang melekat pada penutup artikel AXA tetap disimpan.

Kedua batch dibangun ulang dengan embedding lokal. Hasilnya:

| Batch | Pasangan utama | Model-ready sebelum | Model-ready sesudah | Pertambahan |
| --- | ---: | ---: | ---: | ---: |
| main_01 | 325 | 153 | 186 | 33 |
| main_02 | 900 | 308 | 453 | 145 |
| **Total** | **1.225** | **461** | **639** | **178** |

Dari 179 pasangan dengan artikel yang diterima dalam review ini, 178 masuk model-ready; satu pasangan masih memiliki `url_matching_uncertain`. Kelima artikel `needs_extraction_review` belum dapat diterima karena panduan terpotong, ekstraksi melewatkan bagian isi, teks spam, atau hanya pratinjau dokumen. Tidak ada lagi `needs_language_review` atau `needs_page_type_review` pada dataset utama. Secara keseluruhan, **586 pasangan utama belum model-ready**; angka ini juga mencakup kegagalan crawling/ekstraksi, teks terlalu pendek, halaman non-artikel, pengecualian, dan masalah pencocokan URL, sehingga tidak semuanya dapat diselesaikan dengan persetujuan review.

Sebanyak 639 pasangan model-ready terdiri atas **413 label 0 dan 226 label 1**; domain kesehatan 277, keuangan 232, teknologi 130. Terdapat 583 ID artikel unik (579 URL identitas artikel) dan 224 query. Hasil masih berada pada dua berkas `data/processed/articles_main_01/model_ready.csv` dan `data/processed/articles_main_02/model_ready.csv`, belum satu berkas training gabungan. Usia publikasi masih tidak tersedia pada 191 pasangan model-ready; tidak diisi dengan nilai rekaan, dan penanganan nilai hilang tetap bagian pipeline pemodelan.

Validasi offline: **13 tes ekstraktor lulus**. Audit kedua ekspor membuktikan jumlah/ID pasangan serta label, `n_cited`, dan `n_valid` seluruh 1.225 pasangan tetap sama. Seluruh 308 ID pasangan model-ready lama main_02 tetap tersedia; main_01 memiliki 153 pasangan model-ready di luar antrean review dan 33 tambahan dari antrean. Keempat hasil pemulihan berbahasa Indonesia, berstatus accepted, dan memakai selector yang diperiksa. BM25 serta fitur tekstual dihitung ulang sesuai korpus eligible yang diperbarui. Tidak ada penggunaan SerpApi atau Gemini pada verifikasi/build ini.

## 5 Oktober 2026: opsi menggunakan cadangan SerpApi tanpa mengubah manifest

Pemantauan terakhir `main_02` pada 4 Oktober mencatat kuota akun aktif **10 dari 250 pencarian tersisa** (240 terpakai) dan preview lokal menemukan **81 query belum dimulai**. Cadangan 10 dalam manifest menghentikan runner biasa. Opsi `--quota-reserve 0` ditambahkan untuk satu eksekusi `continue_main_dataset.py`; pemeriksaan kuota pada runner dan kolektor menggunakan nilai runtime yang sama, sedangkan konfigurasi/manifest batch tetap menyimpan cadangan 10. `--unstarted-only` tetap melewati checkpoint lama yang gagal atau terputus. Petunjuk penggunaan ada di `docs/PANDUAN_MENAMBAH_DATASET.md`.

Pengujian offline untuk batas kuota dan mode lanjut lulus. Preview lokal dengan opsi baru berhasil; **belum ada panggilan SerpApi atau Gemini berbayar** dari perubahan kode ini. Pemakaian kuota aktual setelah tanggal snapshot harus diperiksa kembali saat `--run`.

## 22 September 2026: penerapan review manual jenis halaman

Peneliti mengirim hasil pemeriksaan **50 artikel / 53 pasangan utama** melalui `articel_review.txt`. Semua ID cocok dengan 50 artikel yang diteruskan dari review bahasa 21 September, tanpa duplikasi atau ID tidak dikenal. Catatan `accepted`, `page informasi`, dan `page panduan` dipetakan ke penerimaan jenis halaman berdasarkan rubrik yang sudah disepakati. Halaman daftar harga emas dan halaman formulir dengan informasi terbatas dipetakan ke `excluded`. Sebanyak 18 keputusan ditulis eksplisit sebagai accepted; 32 catatan deskriptif dipetakan oleh asisten. Ini merupakan **review halaman oleh peneliti**, bukan penilaian jenis halaman baru oleh LLM; keputusan bahasa terdahulu tetap memiliki provenance review asisten.

Hasil review jenis halaman adalah **48 diterima dan 2 dikecualikan**. Ada satu hambatan teknis pada `article_3412cae508eb697d3d877a65` (JDIH Sukoharjo): meskipun jenis artikelnya diterima peneliti, salinan HTML hasil unduh dan teks ekstraksi berhenti pada langkah pertama JMO di tengah kalimat. Artikel ini ditahan dengan `needs_extraction_review` sampai salinan lengkap tersedia. Keputusan aktif dari 50 artikel menjadi **47 accepted / 50 pasangan**, **2 excluded / 2 pasangan**, dan **1 needs_extraction_review / 1 pasangan**. Salinan saat pengumpulan dapat berbeda dari halaman yang dilihat peneliti saat review; penerimaan jenis halaman tidak memperbaiki isi salinan secara otomatis.

Keputusan diperbarui di `data/manual/article_review.csv`, dengan `reviewer=manual_user_review` dan tanggal penerapan/review yang dilaporkan **2026-09-22**. Tanggal pemeriksaan per artikel tidak dicantumkan dalam berkas masukan. Sebanyak **68 keputusan lainnya dipertahankan** dan total tetap 118 ID unik. Alasan teknis untuk artikel yang ditahan dibedakan dari keputusan jenis halaman peneliti dalam audit.

Bukti dan riwayat:

- `data/manual/article_page_type_review_20260922_source.txt`: salinan persis berkas masukan peneliti, SHA-256 `5f8e29643db3a757ad48536e807061e10a0f1736c7b1c37c8970245349ec24d2`.
- `data/manual/article_page_type_review_20260922.csv`: nomor baris sumber, catatan asli, aturan pemetaan, keputusan jenis halaman peneliti, status aktif, penahanan teknis, dan keputusan sebelumnya untuk seluruh 50 ID.
- `data/manual/article_language_review_20260921.csv`: audit bahasa sebelumnya tetap dipertahankan sebagai riwayat.
- `outputs/review_backups/page_type_review_20260922/`: cadangan CSV keputusan dan keluaran dua batch sebelum perubahan, serta log build.

Pembaruan menggunakan hasil scraping, respons Google/Gemini, dan model embedding yang sudah tersimpan. Tidak ada pencarian, pemanggilan Gemini, atau scraping baru untuk penerapan review ini. Halaman excluded tetap disimpan dalam dataset audit dengan penanda kelayakan; tidak dihapus dari data sumber.

Daftar 50 artikel dari peneliti sudah ditangani seluruhnya. Di luar daftar tersebut masih ada **79 ID artikel lain / 87 pasangan utama** dengan `needs_page_type_review` (39 pasangan batch pertama dan 48 batch kedua). Antrean ini sudah ada sebelum review bahasa dan bukan kegagalan baru. Empat ID artikel / empat pasangan utama masih ditahan untuk kelengkapan/kebersihan teks: dua Hello Sehat, satu Cobisnis, dan satu JDIH Sukoharjo.

Kedua build dengan `--with-embeddings` selesai (exit code 0), menggunakan `configs/article_features.json` dan `configs/article_features_02.json`:

| Batch | Pasangan utama | Model-ready sebelum | Model-ready sesudah | Tambahan |
| --- | ---: | ---: | ---: | ---: |
| `articles_main_01` | 325 | 133 | 153 | 20 |
| `articles_main_02` | 362 | 116 | 146 | 30 |
| **Total** | **687** | **249** | **299** | **50** |

Tambahan 50 pasangan berasal dari 47 ID artikel yang diterima; satu artikel dapat berpasangan dengan beberapa query. Sebanyak **388 pasangan utama belum siap** karena berbagai hambatan yang tetap dicatat pada dataset. Dari 299 baris model-ready, **244 lengkap seluruh fitur dan 55 masih memiliki nilai kosong**: usia publikasi kosong pada 53 baris, rerata panjang paragraf pada tiga baris, dengan satu baris beririsan. Nilai kosong tetap memerlukan prapemrosesan sesuai kebijakan model; tidak diisi dengan angka rekaan. Distribusi model-ready: label 0 sebanyak 155 dan label 1 sebanyak 144; kesehatan 116, keuangan 115, teknologi 68.

Validasi membandingkan seluruh pasangan gabungan sebelum/sesudah: ID pasangan, asal sumber, label dan hitungan sitasi, bukti kredibilitas serta kecocokan URL tetap sama. Seluruh 249 pasangan siap sebelumnya dipertahankan, dan tepat 50 pasangan dari artikel accepted ditambahkan. Teks ekstraksi serta status artikel di luar 50 ID review tidak berubah. Model-ready tetap hanya Google Top-10, sedangkan Gemini-only tersedia terpisah. Definisi 37 fitur tetap sama; BM25 dihitung ulang karena korpus eligible bertambah. Laporan validasi tersimpan di `outputs/review_backups/page_type_review_20260922/review_report.json`. Angka 299 merupakan penjumlahan dua berkas model-ready, belum berkas training gabungan.

## 21 September 2026: review bahasa oleh asisten LLM pada kandidat Top-10

Atas permintaan peneliti, asisten meninjau **101 artikel unik yang mewakili 106 pasangan utama** berstatus `needs_language_review`. Pemilihan dibatasi pada Google Top-10, mencakup Google-only serta irisan Google/Gemini. Review berdasarkan judul dan teks awal, tengah, akhir setiap artikel; kasus tidak wajar ditinjau lebih lanjut, termasuk HTML lokal dua halaman Hello Sehat. Ini merupakan **penilaian berbantuan LLM (LLM-as-a-judge)**, bukan verifikasi manusia independen atau pembacaan setiap kata seluruh artikel. Identitas reviewer dicatat sebagai `llm_assistant_language_review`.

Hasil bahasa: **96 artikel berbahasa Indonesia dan 5 didominasi Inggris**. Istilah teknis, nama produk serta referensi Inggris diperbolehkan bila narasi utama Indonesia. Penilaian tidak semata-mata mengikuti metadata `lang` atau keluaran detektor. Persentase 70–80% yang pernah disarankan dalam percakapan tidak dijadikan hasil pengukuran atau ambang baru; rubrik yang dipakai bersifat kualitatif dan didokumentasikan.

| Keputusan aktif dari review ini | Artikel unik | Pasangan utama |
| --- | ---: | ---: |
| `accepted`: bahasa Indonesia dan syarat jenis halaman sebelumnya sudah terpenuhi | 43 | 45 |
| `needs_page_type_review`: bahasa Indonesia sudah jelas, jenis/kelengkapan halaman belum diputuskan | 50 | 53 |
| `needs_extraction_review`: bahasa Indonesia terverifikasi, tetapi teks ekstraksi bermasalah | 3 | 3 |
| `excluded`: badan halaman didominasi Inggris | 5 | 5 |

Lima keputusan excluded adalah halaman katalog ASUS berisi deskripsi Inggris. Dua artikel Hello Sehat memiliki paragraf Indonesia pada HTML, tetapi ekstraksi hanya mengambil daftar pustaka Inggris. Satu artikel Cobisnis memiliki narasi Indonesia disertai teks tautan promosi unduhan yang tidak terkait. Ketiganya ditandai `needs_extraction_review`; status ini tidak memenuhi syarat accepted/eligible_auto sehingga tetap tertahan dari model. Bahasa pada halaman tabel harga emas juga dikonfirmasi sebagai Indonesia, tetapi cakupan jenis halamannya tetap perlu diperiksa. Kandidat `article_candidate`/`unknown` tidak otomatis diterima hanya karena bahasanya sudah diketahui.

Keputusan aktif ditambahkan ke `data/manual/article_review.csv`; **17 keputusan sebelumnya dipertahankan**, dan ID artikel tidak diduplikasi. Audit khusus tersimpan pada `data/manual/article_language_review_20260921.csv`, berisi alasan, cuplikan bukti, lokasi HTML, hash teks, jenis tindak lanjut dan tanggal review. Keyakinan `high_qualitative` bukan probabilitas terkalibrasi. Cadangan keputusan dan kedua dataset sebelum review ada di `outputs/review_backups/language_review_20260921/`.

Peneliti dapat meninjau ulang melalui [REVIEW_BAHASA_ARTIKEL.md](REVIEW_BAHASA_ARTIKEL.md), yang memuat tautan semua artikel, kasus prioritas serta petunjuk mengubah keputusan aktif. Review ini tidak memeriksa kebenaran informasi, kredibilitas, atau relevansi setiap pasangan query-artikel; label sitasi tidak menjadi dasar penilaian bahasa. Tidak ada panggilan Gemini atau SerpApi untuk review ini. Pembangunan ulang memakai HTML tersimpan dan embedding lokal.

Kedua build selesai. `model_ready` batch pertama bertambah **110 -> 133**, sedangkan batch kedua **94 -> 116**: total **249 pasangan utama**, bertambah 45 dari 204. Seluruh pasangan siap sebelumnya tetap tersedia. Terdapat 236 ID artikel/URL unik, dengan label 0 sebanyak 129 dan label 1 sebanyak 120; domain kesehatan 81, keuangan 103, teknologi 65. Ini hitungan dua batch, belum satu berkas training gabungan. BM25 dihitung ulang karena korpus artikel eligible bertambah.

Tidak ada lagi `needs_language_review` pada dataset utama. Masih ada **438 pasangan utama belum siap**, termasuk 140 pasangan yang perlu review jenis halaman (87 sebelumnya + 53 dari review bahasa) dan 3 pasangan yang perlu pemeriksaan ekstraksi. Status belum siap lainnya tetap dicatat. Sebanyak **210 dari 249 baris model-ready** lengkap seluruh fiturnya; 37 baris kehilangan umur publikasi dan 3 kehilangan rerata panjang paragraf, dengan satu baris beririsan, sehingga **39 baris** membutuhkan penanganan nilai kosong dalam pipeline pemodelan. Tidak ada imputasi menggunakan seluruh dataset.

Validasi data akhir memastikan cakupan 101 ID tepat sesuai antrean awal, tidak ada duplikasi ID review, 17 keputusan lama utuh, teks yang dinilai cocok dengan hash bukti, dan status artikel di luar cakupan tidak berubah. Label serta hitungan sitasi seluruh 687 pasangan utama dan hash respons API mentah juga tetap sama. Hanya 45 pasangan dari artikel yang baru diterima bertambah ke model-ready; status review halaman/ekstraksi dan excluded tidak masuk model. Rekap pemeriksaan dan hash CSV akhir ada di `outputs/review_backups/language_review_20260921/review_report.json`.

## 21 September 2026: pemulihan teknis dataset tanpa keputusan review manual

Perbaikan difokuskan pada data yang sudah terkumpul, tanpa panggilan Gemini atau pencarian SerpApi baru. Salinan keluaran sebelum perbaikan dan CSV review disimpan di `outputs/review_backups/dataset_repair_20260921/`. Respons Gemini, snapshot Google, manifest scraping dan keputusan review manual dipertahankan; hasil pencocokan ulang menjadi lapisan turunan yang dapat diaudit.

### Perbaikan yang diterapkan

- **Resolusi sumber sitasi:** `src/recover_article_sources.py` memulihkan tujuan URL dari hasil yang sudah tersimpan, dengan batas permintaan dan cache terpisah. Sebanyak **79 dari 93 URL** yang dahulu belum diketahui tujuannya berhasil dikenali. Header redirect Google cukup sebagai bukti tujuan, meskipun halaman penerbit gagal diakses; status tersebut tidak menyatakan artikel berhasil diunduh. TLS tetap diverifikasi. Empat belas URL yang masih gagal tetap ditandai.
- **Pencocokan sitasi dan alias:** `src/article_source_matching.py` menghitung kembali frekuensi sitasi dari sumber yang benar-benar dirujuk pada `groundingSupports` setiap percobaan valid. Link awal Google yang berbeda dari URL tujuan yang sudah diketahui tetap dikenali. Alias hanya disatukan dengan bukti redirect scraping sukses, atau canonical sama dan judul serta teks lengkap identik. Duplikasi alias dalam satu jawaban dihitung sekali. Ketidakpastian tidak diubah menjadi label negatif.
- **Ekstraksi isi:** selector Elementor dan beberapa struktur situs diperbaiki agar isi utama tidak tertukar dengan cuplikan atau kartu artikel terkait. Extractor version menjadi **3**, konfigurasi fitur menjadi `article_features_v5_source_matching`. Fitur semantik dihitung lokal; jumlah prediktor tetap **37**.
- **Retry terbatas:** scraper menerima `--retry-transient-only --primary-only`. Sebanyak **57 URL Top-10** dicoba ulang dan **7 berhasil diunduh** pada putaran ini. Dibanding CSV sebelum perbaikan, total artikel berstatus sukses bertambah 10 karena build juga memasukkan tiga keberhasilan scraping yang sebelumnya sudah tersimpan pada checkpoint tetapi belum tercermin dalam CSV batch pertama. Robots disallowed, HTTP 403/404 dan non-HTML tidak dipilih dalam retry sementara.
- **Keputusan manusia:** `preserve_pending_manual_reviews` menjaga status `needs_language_review`/`needs_page_type_review` lama sampai ada keputusan eksplisit. CSV `data/manual/article_review.csv` tidak berubah. Halaman yang kini berhasil diekstrak tetapi belum memenuhi kelayakan otomatis tetap ditahan untuk review.

### Hasil setelah pembangunan ulang

Unit hitungan berikut adalah **pasangan query-artikel Google Top-10**. Jumlah kandidat utama tetap 687; perbaikan meningkatkan kelayakan data yang sudah ada.

| Ukuran | articles_main_01 | articles_main_02 | Total |
| --- | ---: | ---: | ---: |
| Kandidat utama | 325 | 362 | 687 |
| Model-ready sebelum perbaikan | 72 | 59 | 131 |
| Model-ready setelah perbaikan | 110 | 94 | **204** |
| Pencocokan sitasi belum pasti setelah perbaikan | 2 | 7 | **9** |
| Alias masih perlu pemeriksaan pada dataset utama | 2 | 1 | **3** |

Jumlah model-ready bertambah **73 baris**; seluruh 131 pasangan yang sebelumnya siap tetap tersedia. Pencocokan tidak pasti turun dari 186 menjadi 9 pasangan, dan penanda alias yang belum terselesaikan turun dari 51 menjadi 3. Label dapat berubah ketika bukti sitasi baru berhasil dicocokkan; nilai sumber sebelumnya disimpan di kolom `original_*`. Ambang label tetap proporsi sitasi **>=0,5**, dengan protokol tiga slot percobaan dan minimal dua valid.

Sebanyak 204 baris tersebut berasal dari **74 query**, mewakili **193 ID artikel/URL**, dengan 192 identitas artikel setelah penyatuan alias. Distribusi label: **106 negatif dan 98 positif**. Distribusi domain: kesehatan 60, keuangan 91, teknologi 53. Dataset tambahan Gemini-only tetap terpisah; 452 pasangannya memenuhi kelayakan analisis, tidak dihitung sebagai data model utama. Sebanyak 45 pasangan alias duplikat pada ekspor gabungan dipertahankan untuk audit tetapi tidak masuk pemodelan/analisis.

Masih ada **483 pasangan utama yang belum siap**. Sebanyak 193 pasangan (180 URL unik) memiliki status review bahasa/jenis halaman; sisanya mencakup kegagalan unduh, teks kosong/terlalu pendek, halaman bukan artikel, bahasa bukan Indonesia, keputusan excluded sebelumnya, atau alias belum pasti. Sebagian penanda dapat tumpang tindih, sehingga jumlah per kategori hambatan tidak boleh dijumlahkan sembarangan. Perbaikan teknis tidak menjadikan semua hasil scraping layak.

Pada model-ready, **180 baris lengkap seluruh prediktor**. Sebanyak 23 baris tidak memiliki `publication_age_days` karena tanggal publikasi tidak ditemukan; dua baris memiliki `mean_paragraph_word_count` kosong karena badan HTML tidak memiliki elemen paragraf `<p>`, sehingga rerata berbasis elemen tersebut tidak terdefinisi. Satu baris memiliki kedua kekosongan itu, jadi totalnya **24 baris dengan fitur belum lengkap**. Fitur model lainnya tersedia. Definisi paragraf tidak diubah hanya pada dua situs demi mengisi nilai, dan tanggal tidak dikarang. Imputasi, jika diperlukan, harus di-fit pada fold train. Model-ready menyatakan kelayakan artikel dan label, bukan jaminan seluruh fitur bebas NaN.

File yang digunakan tetap `data/processed/articles_main_01/model_ready.csv` dan `data/processed/articles_main_02/model_ready.csv`. Angka 204 merupakan hitungan kedua batch, **belum berkas pelatihan gabungan**. Sebelum training lintas batch, gabungkan dengan pemeriksaan duplikasi/identitas artikel, hitung fitur korpus secara konsisten, dan atur pemisahan train/test yang mencegah artikel sama bocor ke kedua sisi.

### Audit dan penggunaan berikutnya

Setiap batch menyimpan `source_matching_audit.json`: bukti penyatuan URL, hash respons sumber mentah/cache pemulihan, serta salinan bukti pemulihan yang dipakai. `article_identity_url`, `original_*`, alasan kredibilitas dan metadata matching bukan prediktor. Waktu pemulihan URL dicatat terpisah dari waktu eksperimen; jawaban Gemini tidak diminta ulang. Lapisan ini memperbaiki pencocokan kandidat dalam manifest yang ada, bukan otomatis menambah seluruh URL sitasi yang baru berhasil diresolusi ke manifest scraping.

Validasi: **74 tes offline lulus**, mencakup pencocokan per percobaan, canonical dengan isi berbeda, pemulihan redirect, URL Google awal/akhir yang berbeda, perlindungan review manual, retry selektif, pemisahan dataset, dan protokol kolektor. Pemeriksaan CSV akhir memastikan label sesuai percobaan valid/ambang, tidak ada pasangan duplikat siap-model, metadata audit bukan fitur, seluruh pasangan siap sebelumnya tetap tersedia, dan hash review serta respons sumber tidak berubah. Rekap beserta hash CSV tersimpan di `outputs/review_backups/dataset_repair_20260921/repair_report.json`. Kedua build menggunakan HTML/cache lokal dan mempertahankan data gagal dalam ekspor audit. Panduan lengkap dan perintah lanjutan diperbarui di `docs/PANDUAN_MENAMBAH_DATASET.md` pada bagian pemulihan teknis. **Tidak ada token Gemini atau kredit pencarian SerpApi yang digunakan dalam perbaikan ini.**

## 21 September 2026: perluasan manifest untuk melanjutkan scraping main_02

Error `Manifest berbeda` terjadi karena ekspor `main_02` bertambah setelah snapshot scraping dibuat pada 18 September. Konfigurasi scraping tetap identik. Manifest lama memuat 584 URL/610 pasangan; kandidat terbaru memuat 917 URL/986 pasangan dari 43 query eligible. Seluruh 610 pasangan lama identik, tanpa penghapusan; tambahan berjumlah 333 URL dan 376 pasangan.

`src/scrape_articles.py` kini menerima `--extend-manifest`. Preview menghitung tambahan secara lokal tanpa menulis data. Dengan `--run`, scraper mengunci proses, membaca ulang manifest aktif, memvalidasi bahwa konfigurasi dan pasangan lama tetap sama, lalu mengarsipkan manifest sebelumnya ke `manifest_history/manifest_<sha256>.json` sebelum menyimpan perluasan. Perubahan label, URL, kelayakan pasangan lama, konfigurasi, identitas duplikat atau penghapusan pasangan ditolak. Fingerprint yang berubah hanya karena baris belum eligible boleh diperbarui dengan persetujuan flag yang sama, meskipun tambahannya nol.

Checkpoint, HTML, ekstraksi dan riwayat percobaan lama tetap digunakan. URL berhasil tidak diunduh ulang; pasangan baru pada URL yang sudah diambil memakai checkpoint tersebut. Mode biasa hanya mengambil URL belum dicoba, sedangkan `--retry-failed` hanya mengulang status gagal yang diizinkan. Setelah perluasan tersimpan, perintah tanpa flag perluasan kembali dapat digunakan selama sumber tidak berubah lagi. Builder tetap membaca manifest aktif dan memisahkan Top-10/Gemini-only per pasangan query-artikel.

Validasi: **33 tes offline lulus** (22 scraper dan 11 builder). Enam tes scraper baru mencakup perluasan dengan URL bersama, penggunaan ulang hasil unduhan tanpa perubahan byte, arsip manifest, resume idempoten, retry terpisah dari URL baru, penolakan perubahan/penghapusan/duplikasi, kegagalan penyimpanan arsip, preview tanpa penulisan, dan perubahan fingerprint tanpa kandidat baru. Preview data aktual berhasil untuk pengambilan baru dan retry: 417 URL belum dicoba (84 lama + 333 tambahan), serta 67 URL memenuhi status retry. Manifest lama masih mencatat 500 URL dicoba, termasuk 429 sukses.

Panduan `docs/PANDUAN_MENAMBAH_DATASET.md` diperbarui: penambahan dalam batch yang sama dapat diperluas tanpa membuat `dataset_id` baru. Pada pekerjaan perbaikan ini belum ada perluasan manifest riil, scraping website, build dataset riil, atau panggilan Gemini/SerpApi. Untuk menerapkan perluasan sambil retry maksimal 10 URL, jalankan:

```powershell
python src/scrape_articles.py --config configs/article_dataset_02.json --extend-manifest --retry-failed --run --max-new-urls 10
```

Untuk mengambil URL belum dicoba, hilangkan `--retry-failed`. Setelah pengambilan/retry, jalankan `python src/build_article_dataset.py --config configs/article_features_02.json --with-embeddings` untuk memperbarui CSV final. Ini tidak memakai token Gemini atau kredit pencarian SerpApi.

## 20 September 2026: perbaikan tanggal publikasi dan rute penambahan dataset

Ditambahkan `src/article_dates.py` untuk membaca tanggal publikasi lengkap dengan format ISO (termasuk bentuk padat), timestamp ISO dengan pemisah jam bertitik, serta nama bulan Indonesia/Inggris dan timezone WIB/WITA/WIT. Parser tidak melengkapi tahun/hari yang hilang atau menebak urutan tanggal numerik ambigu. Tanggal modifikasi, copyright dan URL tidak menggantikan tanggal terbit. Tanggal tanpa timezone memakai asumsi UTC yang dicatat; tanggal setelah waktu scraping tetap tidak menghasilkan umur negatif.

Ekstraktor artikel sekarang juga memeriksa metadata publikasi tambahan dan elemen publikasi eksplisit, dengan perlindungan terhadap elemen terkait/footer serta lebih dari satu tanggal berbeda pada selector yang sama. Tanggal mentah tetap disimpan; sumber ekstraksi dicatat pada `published_at_source`. Extractor version menjadi 2, konfigurasi fitur kedua batch menjadi `article_features_v4_publication_dates`. Perbaikan otomatis berlaku pada scraping berikutnya dan build ulang HTML lokal. Dependensi `python-dateutil==2.9.0.post0` sudah tersedia di venv dan dicatat eksplisit pada requirements.

Builder menambahkan `published_at_normalized`, `publication_age_status`, `publication_timezone_assumed`, `missing_model_features` dan `model_features_complete` sebagai audit. File `missing_features_report.json` merangkum kelengkapan masing-masing fitur pada dataset utama dan model_ready. Daftar 37 prediktor dan aturan label tetap sama. Metadata audit tidak menjadi prediktor. Missing value yang tidak dapat dipulihkan tetap kosong; build tidak melakukan imputasi menggunakan keseluruhan dataset. Model_ready menyatakan kelayakan artikel/label, bukan jaminan semua nilai fitur tersedia. Penanganan NaN atau imputasi yang di-fit hanya pada fold train tetap bagian pipeline pemodelan berikutnya.

Pemeriksaan progres menemukan 306 query terjadwal (41 + 265); `main_02` memiliki 27 query selesai, 1 terputus dan 237 belum dimulai. Dari 584 URL pada manifest `articles_main_02`, 500 sudah dicoba. **Seluruh 84 URL tersisa adalah Gemini-only**, sehingga melengkapinya tidak menambah pasangan model utama. Dua snapshot artikel memiliki 557 pasangan utama dari 65 query eligible, dengan 109 pasangan model_ready saat pemeriksaan.

Untuk melanjutkan query baru tanpa membayar slot tambahan pada query lama yang melewati jendela 6 jam, runner mendapat opsi `--unstarted-only`. Mode ini melewati setiap query yang sudah mempunyai checkpoint, tidak mengubah arsipnya, dan tidak dapat digabung dengan recovery. Kolektor juga memfilter pekerjaan sebelum menerapkan batas jumlah query, sehingga query lama tidak menghabiskan slot eksekusi. Pengumpulan lama dapat dipulihkan melalui alur terpisah jika masih memenuhi protokol; mode ini tidak menyatakan query terputus sebagai selesai/valid. Preview lokal mengonfirmasi 237 query tersedia.

`docs/PANDUAN_MENAMBAH_DATASET.md` diperbarui dengan rute menuju 2.000–3.000 pasangan utama: review hambatan, pengumpulan query accepted tersisa, snapshot scraping baru setelah sumber bertambah, pembacaan laporan missing value, proyeksi kebutuhan query berdasarkan hasil aktual, penambahan PAA, penggabungan korpus dan persiapan train/test. Target tidak menghitung Gemini-only atau pasangan duplikat dari snapshot tumpang tindih. Angka kuota yang tersimpan diberi tanggal dan tidak diklaim sebagai saldo terkini.

Validasi offline: 60 tes lulus pada parser tanggal (5), ekstraksi fitur (10), builder (11), scraper (16), kolektor utama (14), dan runner (4). Tidak ada panggilan API berbayar atau pengunduhan artikel baru pada pekerjaan ini; pembangunan ulang menggunakan HTML tersimpan dan cache embedding lokal.

Kedua build selesai dengan sukses. `articles_main_01` tetap 325 pasangan utama/72 model_ready; umur publikasi kosong turun dari 176 ke 174 pada dataset utama dan 13 ke 11 pada model_ready. `articles_main_02` tetap 232 pasangan utama/37 model_ready; umur publikasi kosong turun dari 132 ke 127 pada dataset utama dan 4 ke 3 pada model_ready. Total tujuh baris utama dipulihkan (enam format tanggal dan satu ekstraksi elemen HTML). Seluruh nilai umur yang masih kosong pada dataset utama berstatus `missing_publication_date`; tanggal yang berhasil diperoleh semuanya sudah dapat dihitung. Pada gabungan 109 baris model_ready, 95 lengkap seluruh fitur dan 14 masih tidak memiliki umur publikasi; tidak ada fitur model lain yang kosong. Jumlah baris/label tidak berubah. Ketiadaan tanggal tidak diatasi dengan mengarang tanggal atau mengisi nol.

## 18 September 2026: bukti kredibilitas dipertahankan sebagai metadata audit

Atas keputusan peneliti, fitur model tetap biner melalui `domain_authority_level`, sedangkan `credibility_evidence` dan `credibility_reason` ditambahkan kembali ke ekspor lengkap. Builder membaca `data/manual/source_credibility.csv`: `evidence_urls` dan `reason` lama disalin sebagai catatan mentah apabila hostname cocok. Untuk Level 2 tanpa audit lama, URL final yang diamati menjadi bukti awal dan alasan mengikuti basis aturan biner. Level 1 yang belum pernah diperiksa menyimpan bukti kosong dan alasan default.

Kolom tersebut tersedia pada `articles.csv`, `dataset.csv`, `dataset_gemini_only.csv`, dan `dataset_union.csv`. Keduanya dikeluarkan secara eksplisit dari daftar prediktor dan tidak tersedia di `model_ready.csv`; label, kelayakan artikel, serta level biner tidak berubah karena isi metadata audit. `domain_authority_basis` tetap menjadi alasan aturan aktif. Alasan dari CSV lama adalah bukti historis rubrik 1–5 dan dapat berbeda dari keputusan biner aktif. Konfigurasi fitur mencatat lokasi sumber audit melalui `credibility_audit_csv`. Sebelas tes builder lulus sebelum pembangunan ulang dataset lokal.

Dataset `articles_main_01` kemudian selesai dibangun ulang dari 870 checkpoint lokal tanpa panggilan SerpApi/Gemini: 330 artikel eligible, 942 pasangan gabungan, dan 72 pasangan utama siap-model. Sebanyak 432 artikel memiliki bukti audit tidak kosong dan seluruh 870 memiliki alasan. Jumlah baris/fitur model tidak berubah.

Konfigurasi `configs/article_dataset_02.json` dan `configs/article_features_02.json` disiapkan untuk scraping terpisah dari `main_02`. Preview pada 18 September menemukan **610 pasangan eligible dan 584 URL unik** dari 27 query selesai/eligible; 571 URL belum pernah dicoba pada `articles_main_01`, sedangkan 13 beririsan dengan checkpoint lama. Belum ada permintaan halaman dari konfigurasi baru. Eksekusi pertama dengan `--run` akan membekukan snapshot ini; perubahan ekspor `main_02` sesudahnya harus memakai dataset_id artikel baru.

## 17 September 2026: recovery Gemini untuk kegagalan transport

Pengumpulan `main_02` sempat berhenti pada query kedua, "Bagaimana cara cek pajak NPWP?": satu respons berhasil dan dua slot berstatus `network_or_timeout`. Kuota terakhir tersimpan 150 SerpApi, token respons tersimpan 14.420. Status query `completed` berarti tiga slot sudah memiliki hasil/error, bukan otomatis memenuhi minimal dua valid.

Ditambahkan `src/recover_main_gemini.py` dan flag `--recover-gemini --max-recovery-calls` pada runner. Recovery eksplisit, maksimal satu retry per slot sepanjang checkpoint, tanpa mengulang Google atau respons berhasil. Kegagalan lama diarsipkan di `recovery_history`; jadwal tetap tiga slot dan denominator proporsi sitasi adalah jumlah slot valid, bukan jumlah request HTTP. Slot retry memakai waktu baru; recovery melewati slot yang akan melanggar jendela 6 jam. Error billing/429, respons invalid yang sudah selesai, dan status `started` tidak diulang otomatis.

Timeout Gemini dinaikkan dari 55 menjadi 120 detik dan error transport dipisahkan menjadi `timeout`/`network_error` tanpa mencetak detail rahasia. Rekap penggunaan menambahkan jumlah kegagalan yang diarsipkan. Timeout yang tidak mengembalikan respons mungkin sudah ditagihkan; token lokal bukan total billing. Perubahan ini hanya mengubah transport/recovery, tidak mengubah model/prompt/manifest batch. Implementasi dan preview diuji lokal; **30 tes terkait lulus, belum ada retry API berbayar yang dijalankan pada tahap perbaikan ini**. Preview menemukan slot 2 dan 3 query kedua masih siap dipulihkan saat diperiksa.

## 17 September 2026: pengumpulan query tersisa dan pemantauan penggunaan

Atas instruksi peneliti, pengumpulan URL batch `main_02` dimulai dari snapshot **265 query accepted baru**: 115 kesehatan, 92 keuangan, 58 teknologi. Daftar menggabungkan 4 query awal yang belum dikumpulkan dan 261 query ekspansi; ID dan teks dibandingkan dengan manifest batch sebelumnya agar 41 query lama tidak diulang. Total accepted saat persiapan adalah 306. Snapshot ada di `data/manual/main_02_queries.csv`, config di `configs/main_dataset_02.json`.

`src/continue_main_dataset.py` menyiapkan snapshot dan melanjutkan kolektor yang sudah ada. Model/prompt/parameter pencarian tetap mengikuti batch awal; tiga percobaan, minimal dua valid, ambang sitasi >=0,5. Urutan bergantian antar domain. Kuota SerpApi awal **152 dari 250 tersisa** (98 terpakai), diperiksa melalui Account API. Eksekusi dimulai dengan batas **142 query**, pemeriksaan tiap **5 query**, cadangan **10 kredit**. Ini adalah batas eksekusi, bukan klaim bahwa 142 query telah selesai.

Token Gemini direkap dari respons tersimpan, termasuk respons yang belum selesai resolusi URL. Laporan `data/raw/main/main_02/usage_latest.json` serta `usage_history/` menyimpan kuota dan penggunaan batch. Laporan ini tidak mengetahui saldo rupiah Gemini maupun penggunaan di luar batch; billing perlu dilihat di AI Studio. API error menghentikan proses dan mempertahankan checkpoint, tanpa retry panggilan berbayar otomatis. Respons yang berakhir karena batas token tetap disimpan untuk audit.

Saat catatan ini dibuat, **query pertama selesai dengan tiga percobaan valid**, 7 pasangan Google dan 23 pasangan gabungan; penggunaan yang dilaporkan 10.469 token total. Query kedua sedang diproses. Angka live tersedia dalam `data/interim/main/main_02/queries.csv`, `trials.csv`, dan checkpoint mentah. Pengumpulan ini belum melakukan scraping artikel baru. Manifest/dataset scraping lama tetap terpisah. **13 tes kolektor dan 2 tes pemantauan lulus**, seluruhnya menggunakan simulasi tanpa API.

Build artikel terakhir sebelum ekspansi (19.18 WIB) mencakup 870 URL dicoba, 330 artikel eligible, 72 pasangan utama siap-model dari 68 URL unik, serta 194 pasangan tambahan siap analisis. Status baru pengumpulan URL tidak otomatis menambah baris model-ready sebelum scraping dan build berikutnya.

## Pembaruan terbaru: jalur query asli tanpa sintesis

Rancangan dilanjutkan menggunakan query asli Trends/PAA, tanpa sintesis LLM. Untuk batch awal, teks berbahasa Inggris dipisahkan tanpa diterjemahkan. [Protokol terbaru](MAIN_DATASET.md#query-asli) dan catatan di awal CONTEXT.md menggantikan tahapan sintesis yang masih muncul sebagai riwayat dalam dokumen ini.

[prepare_original_queries.py](../src/prepare_original_queries.py) dan [notebook 03](../notebooks/03_review_original_queries.ipynb) telah dijalankan secara lokal. Dari 52 pertanyaan PAA dan 26 sumber Trends yang sebelumnya dianggap cukup spesifik, tersedia **49 kandidat berbahasa Indonesia**: 17 kesehatan, 20 keuangan, 12 teknologi. Sumber tersebut terdiri dari 48 PAA dan satu Trends. **29 sumber Inggris** diarsipkan sebagai ditunda, tanpa parafrasa atau terjemahan. Seluruh teks hasil telah diperiksa identik dengan sumbernya.

CSV kandidat berada di `data/interim/original_queries/candidates_id.csv`. Semua kandidat masih `pending` untuk penilaian kualitas; ini belum 49 query final atau pasangan query–artikel. Notebook menerima keputusan memakai teks query, menyimpan progres ke `data/manual/original_query_decisions.csv`, dan mengekspor query yang diterima. Tidak ada API atau kuota tambahan yang digunakan.

**Pekerjaan terdekat:** seleksi kualitas 49 kandidat, periksa duplikasi intent dan cakupan, lalu pilih batch untuk pengumpulan Google Top-10 dan Gemini. Sintesis dan Judgment prompt sintesis tidak lagi menjadi prasyarat jalur ini; rencana lama di bawah dibaca sebagai riwayat.

## Tujuan dan posisi saat ini

Penelitian mengikuti [CONTEXT.md](../CONTEXT.md): memprediksi keterkutipan artikel web berbahasa Indonesia oleh Gemini dengan Google Search Grounding menggunakan XGBoost, membandingkannya dengan Logistic Regression dan Random Forest, serta menganalisis kontribusi fitur melalui SHAP dan ablation study.

Unit analisis dataset utama nantinya adalah **pasangan query–artikel**. Target awal sekitar 300 query final dan maksimal 3.000 pasangan sebelum pembersihan. Target terdekat adalah memperoleh dataset awal yang dapat dibawa ke bimbingan dan dilanjutkan menjadi dataset pemodelan.

**Progres implementasi saat ini baru sampai pengumpulan dan seleksi sumber query Google Trends.** Data yang sudah tersedia belum merupakan query final, label keterkutipan, atau dataset pasangan query–artikel. Pengambilan PAA dan sintesis belum dijalankan dalam rangkaian pekerjaan ini. CONTEXT.md mencatat pilot terdahulu 40 query; pilot tersebut belum diintegrasikan atau diaudit ulang dalam pekerjaan ini.

## Pekerjaan yang telah selesai

1. Meninjau rancangan penelitian dan menyusun alur kerja bertahap dengan Python untuk proses berulang serta Jupyter Notebook untuk peninjauan dan analisis.
2. Mengumpulkan CSV Google Trends secara manual oleh peneliti, tanpa kata kunci awal, menggunakan periode setahun terakhir dan kategori Kesehatan, Keuangan, serta Komputer & elektronik. Nama ekspor mencantumkan wilayah ID dan rentang 10 September 2025–10 September 2026. Tautan Explore, jenis pencarian, dan metadata kategori terperinci masih perlu dicatat dalam manifest sumber.
3. Memisahkan enam ekspor sumber di `data/before/` dan enam CSV hasil seleksi di `data/`. Ekspor asli tidak diubah oleh skrip penggabungan/review.
4. Membuat dan menjalankan [src/merge_trends.py](../src/merge_trends.py). Skrip menggabungkan enam CSV terpilih, mempertahankan teks serta nilai Trends asli, dan menambahkan ID, domain, jenis daftar, file asal, serta nomor baris data.
5. Membuat [notebook peninjauan](../notebooks/01_review_trends_sources.ipynb) dan [modul review](../src/review_trends.py). Notebook mengelompokkan teks identik, menampilkan filter, menerima keputusan manual, menyimpan progres, dan mengekspor daftar per status.
6. Memasang `ipykernel` pada virtual environment proyek. Dependensi notebook dicatat dalam [requirements-notebooks.txt](../requirements-notebooks.txt). Penggabungan dan penyimpanan CSV menggunakan library standar Python.
7. Melengkapi keputusan review berdasarkan arahan peneliti, termasuk alasan serta intent untuk sumber siap sintesis. Keputusan yang sudah ditulis peneliti dan sesuai aturan terbaru dipertahankan.
8. Mengeluarkan enam sumber GTK, memperbarui penggabungan, menyelaraskan kembali asal sumber, dan memperbarui dictionary keputusan serta ekspor notebook.

## Pilot People Also Ask selesai

Pengambil [src/collect_paa.py](../src/collect_paa.py) telah dijalankan dengan [konfigurasi pilot](../configs/paa_pilot.json), maksimal 15 pencarian. Konfigurasi: Google Indonesia, negara ID, bahasa ID, lokasi Indonesia, desktop, hanya PAA pada respons awal. Topik dipilih secara purposif (lima per domain) dari daftar `needs_paa`, bukan sampel acak. Respons disimpan per request dan pengambilan dapat dilanjutkan tanpa mengirim ulang request tersimpan.

| Domain | Pencarian | Menghasilkan PAA | Tanpa PAA | Pertanyaan |
|---|---:|---:|---:|---:|
| Kesehatan | 5 | 5 | 0 | 20 |
| Keuangan | 5 | 5 | 0 | 20 |
| Teknologi | 5 | 3 | 2 | 12 |
| **Total** | **15** | **13** | **2** | **52** |

Seluruh 52 pertanyaan memiliki teks unik setelah normalisasi huruf dan spasi. `github` dan `lacak hp gmail` berhasil dicari tetapi tidak menghasilkan PAA. Tidak ada pencarian pengganti atau ekspansi otomatis.

Kuota akun yang diperiksa: sebelum batch **213 terpakai, 37 tersisa** dari 250; sesudah batch **228 terpakai, 22 tersisa**. Penggunaan batch adalah 15 pencarian. Tidak ada pengambilan tambahan setelah batch ini.

Hasil berada di `data/interim/paa/paa_pilot_01/questions.csv` dan `searches.csv`; respons mentah dengan redaksi kredensial serta manifest berada di `data/raw/paa/`. Semua pertanyaan berstatus `unreviewed`. Pengaturan bahasa Indonesia tidak menjamin bahasa hasil; sebagai contoh PAA `icd 10` berbahasa Inggris dan perlu ditinjau sebelum diterjemahkan/sintesis. Review sumber Trends tidak diubah menjadi status selesai PAA; status pengambilan dicatat terpisah pada `searches.csv`.

Gunakan [notebook inspeksi PAA](../notebooks/02_inspect_paa_pilot.ipynb) untuk bahan bimbingan tanpa memanggil API. [Panduan pengambilan dan resume](PAA_COLLECTION.md) menjelaskan struktur hasil, pengamanan kuota, dan penambahan batch menuju dataset utama. Empat tes lokal tanpa jaringan mencakup penggunaan kembali hasil, kuota tidak cukup, kegagalan tanpa retry, dan redaksi rahasia.

## Dataset sumber terkini

| Domain | Top | Rising | Total baris sumber | Teks unik aktif |
|---|---:|---:|---:|---:|
| Kesehatan | 29 | 29 | 58 | 57 |
| Keuangan | 46 | 41 | 87 | 76 |
| Teknologi | 47 | 41 | 88 | 76 |
| **Total** | **122** | **111** | **233** | **209** |

Penggabungan mempertahankan seluruh 233 kemunculan sumber. Review memiliki satu baris per teks yang persis sama, sehingga berisi 209 baris. Pengelompokan ini belum menghapus duplikasi semantik atau kesamaan intent.

## Keputusan review yang berlaku

Keputusan berikut merupakan arahan peneliti, **bukan hasil LLM Judgment**. Top/Rising menunjukkan asal daftar, bukan ukuran kualitas query.

- Kesehatan Top: `needs_paa`.
- Kesehatan Rising: `ready_for_synthesis`, dengan pengecualian di bawah.
- `icd 10`: diperbarui dari `needs_review` menjadi `needs_paa` setelah penjelasan klasifikasi penyakit dan masalah kesehatan diverifikasi melalui [WHO](https://icd.who.int/browse10/2019/en) dan disetujui peneliti. Intent tetap kosong karena kebutuhan informasi belum spesifik.
- Sumber setelah `icd 10` sampai `abu vulkanik` dalam urutan review: `needs_paa`.
- `best sunscreen for face`: `needs_paa`, untuk menelusuri kebutuhan yang lebih spesifik melalui PAA tanpa mengarang jenis kulit dalam query.
- `campak`, yang muncul pada Top dan Rising: `needs_paa`; keputusan rentang/Top didahulukan.
- Keuangan dan teknologi: seluruh sumber aktif menjadi `needs_paa`.
- Keputusan `best pillow for side sleepers` tetap `ready_for_synthesis`, dengan intent mencari rekomendasi bantal untuk orang yang tidur menyamping.

| Domain | `needs_paa` | `ready_for_synthesis` | `needs_review` | Total |
|---|---:|---:|---:|---:|
| Kesehatan | 31 | 26 | 0 | 57 |
| Keuangan | 76 | 0 | 0 | 76 |
| Teknologi | 76 | 0 | 0 | 76 |
| **Total** | **183** | **26** | **0** | **209** |

Tidak ada sumber aktif berstatus `unreviewed` atau `needs_review`. Bahasa yang belum dapat ditetapkan dengan yakin ditandai `unknown`. Intent untuk `needs_paa` dikosongkan agar tidak menciptakan kebutuhan informasi sebelum pertanyaan sumber diperoleh.

## Pengeluaran GTK dan jejak perubahan

Alasan peneliti: GTK lebih berkaitan dengan pendidikan dan tidak sesuai cakupan teknologi penelitian ini.

Enam teks yang dikeluarkan:

- `gtk`
- `info gtk`
- `info gtk kemendikdasmen`
- `info gtk 2026`
- `emis gtk`
- `ruang gtk`

Peneliti telah menghapus empat kueri pada Rising. Saat pemeriksaan, dua kueri pada Top masih tersedia dan kemudian dikeluarkan dengan alasan yang sama.

Sebelum perubahan ini, dataset gabungan memuat 239 baris dan review memuat 215 teks unik. Setelah perubahan: 233 baris dan 209 teks unik. Jumlah `needs_paa` saat pengeluaran GTK turun dari 188 menjadi 182; keputusan sumber lainnya dipertahankan. Setelah keputusan lanjutan untuk `icd 10`, jumlah terkini menjadi 183.

Jejak pengeluaran tersimpan terpisah di [data/manual/gtk_exclusions.csv](../data/manual/gtk_exclusions.csv), termasuk ID dan referensi sumber sebelumnya, alasan, serta waktu pengeluaran. Karena keenam sumber telah dihapus dari masukan aktif, mereka tidak muncul dalam `data/interim/review/excluded.csv`; daftar pengeluaran GTK harus dibaca bersama ekspor status aktif saat melaporkan seleksi.

Cadangan sebelum penyelarasan tersedia di `outputs/review_backups/20260910T041943791901Z/`. Cadangan ini menyimpan notebook, review, gabungan lama, serta CSV terpilih pada saat pemeriksaan; empat penghapusan Rising oleh peneliti sudah terjadi sebelum cadangan tersebut. Ekspor asli tetap berada di `data/before/`.

`source_id` berasal dari nomor baris dan dapat berubah setelah penghapusan. Pada penyelarasan ini, keputusan lama dipertahankan melalui `topic_id` berbasis hash teks, setelah kecocokan teks dan domain diperiksa; referensi ke baris masukan dibentuk ulang. Validasi perubahan sumber pada `load_review` tetap aktif agar perubahan berikutnya tidak diterima diam-diam.

## Berkas kerja dan cara melanjutkan

| Berkas | Fungsi |
|---|---|
| `data/top_*.csv`, `data/rising_*.csv` | Enam CSV sumber terpilih |
| `data/before/` | Ekspor asli Google Trends |
| `data/interim/trends_sources.csv` | Seluruh kemunculan sumber hasil penggabungan |
| `data/manual/trends_review.csv` | Progres keputusan untuk teks unik aktif |
| `data/manual/gtk_exclusions.csv` | Catatan sumber GTK yang dikeluarkan |
| `data/interim/review/needs_paa.csv` | 183 topik untuk penelusuran PAA |
| `data/interim/review/ready_for_synthesis.csv` | 26 sumber untuk persiapan sintesis |
| `data/interim/review/needs_review.csv` | Kosong; seluruh sumber aktif telah diputuskan |

Jalankan penggabungan dari direktori utama proyek:

```powershell
.\venv\Scripts\python.exe .\src\merge_trends.py
```

Buka notebook dan pilih interpreter `venv/Scripts/python.exe`. Jalankan sel dari atas ke bawah. Untuk koreksi keputusan, cari komentar teks sumber di blok **Isi keputusan manual**, edit dictionary, lalu jalankan sel keputusan dan sel simpan. Dictionary menerapkan keputusan yang tertulis di dalamnya; jangan mengedit CSV keputusan secara terpisah tanpa menyelaraskannya dengan notebook.

Jika sumber CSV berubah lagi, arsipkan dan selaraskan review sebelum menjalankan notebook; menjalankan penggabungan saja tidak memigrasikan keputusan lama. Folder data dan outputs saat ini diabaikan Git sesuai `.gitignore`, sehingga arsip data perlu disimpan secara terpisah dari kode.

## Pemeriksaan yang dilakukan

- Penggabungan enam file dengan pemeriksaan struktur dan query kosong.
- Eksekusi seluruh sel kode notebook secara berurutan menggunakan Python virtual environment.
- Pemeriksaan keunikan ID topik dan jumlah kemunculan sumber.
- Pemeriksaan bahwa kueri GTK tidak berada pada sumber, review, atau dictionary keputusan aktif.
- Pemeriksaan bahwa keputusan sumber yang dipertahankan tidak berubah akibat pembaruan nomor baris.
- Pemeriksaan pemuatan ulang review, konsistensi ekspor per status, dan kestabilan penerapan ulang keputusan.

## Skrip pilot Gemini disiapkan

[src/pilot_gemini_grounding.py](../src/pilot_gemini_grounding.py) dan [konfigurasi pilot](../configs/gemini_grounding_pilot.json) telah dibuat untuk sembilan pertanyaan PAA asli berbahasa Indonesia, tiga per domain. Dua kondisi (A: Google Search aktif; B: sama dengan tambahan instruksi pencarian) diuji dua kali, sehingga rencana maksimal 36 pemanggilan. Kedua kondisi memiliki instruksi bahasa Indonesia yang sama. Model mengikuti pilihan peneliti, `gemini-3.5-flash`, tanpa pergantian otomatis.

Mode bawaan adalah pratinjau lokal; `--run --max-new-calls 2` memulai dua pemanggilan baru dan `--run` melanjutkan sisa rencana. Implementasi memakai REST generateContent dan library standar Python. Respons mentah, metadata sitasi, token, serta hasil resolusi URL segera per respons disimpan untuk dapat dilanjutkan tanpa pengulangan API yang tidak disengaja.

Pada tahap pembuatan skrip, pratinjau menunjukkan 36 percobaan belum dikirim dan tidak ada pemanggilan Gemini atau penggunaan kuota SerpApi. Lima tes awal tanpa jaringan untuk pilot Gemini lulus. Peneliti kemudian menjalankan seluruh pilot; hasil terkini dijelaskan di bawah.

Panduan eksekusi, batas biaya, interpretasi metrik, dan penanganan error ada di [GEMINI_GROUNDING_PILOT.md](GEMINI_GROUNDING_PILOT.md). Pilot teknis ini memakai PAA asli tanpa sintesis; tidak menggantikan sintesis dan penilaian query untuk dataset utama. Sebelum menjalankan, periksa anggaran Gemini, lalu mulai dari pasangan A/B pertama.

## Hasil pilot Gemini lengkap dan ekspor URL tujuan

Seluruh **36 percobaan selesai**, dengan finish reason `STOP`, tanpa error API pada hasil akhir. Model yang dilaporkan respons adalah `gemini-3.5-flash`.

| Kondisi | Respons dengan sitasi / selesai | Proporsi |
|---|---:|---:|
| A: Google Search aktif | 8/18 | 44,4% |
| B: ditambah instruksi pencarian | 18/18 | 100% |

Per domain, kondisi A memiliki sitasi pada 2/6 respons kesehatan, 4/6 keuangan, dan 2/6 teknologi. Kondisi B memiliki sitasi pada 6/6 respons di setiap domain. Ini hasil eksploratif sembilan query dan dua pengulangan, bukan jaminan seluruh query akan menghasilkan sitasi.

Ada 292 kemunculan sumber dengan hubungan sitasi di metadata. Setelah mencoba ulang lima kegagalan resolusi tanpa pemanggilan Gemini atau SerpApi, 290 kemunculan sumber memiliki URL tujuan (159 URL tujuan unik), dan dua kemunculan dari `lombokbaratkab.go.id` masih belum memiliki URL tujuan. Sebanyak 236 kemunculan berstatus `resolved`, 54 `destination_http_error` (45 HTTP 403 dan 9 HTTP 503), serta dua `network_or_url_error`. Angka kemunculan bukan jumlah artikel layak; seleksi video, toko, dan jenis halaman lainnya belum dilakukan.

Gunakan [source_links.csv](../data/interim/gemini_pilot/gemini_grounding_pilot_01/source_links.csv) untuk tautan tujuan tanpa kolom redirect Google, atau [report.md](../data/interim/gemini_pilot/gemini_grounding_pilot_01/report.md) untuk ringkasan dan tautan yang bisa diklik. `sources.csv` tetap menyimpan `raw_url` sebagai jejak data dan kini menambahkan `source_url` sebagai kolom tujuan untuk digunakan. URL yang belum diketahui tidak diganti dengan tebakan atau tautan redirect. JSON respons asli tetap dipertahankan.

Mode `--resolve-missing-only` ditambahkan untuk mencoba ulang resolusi sumber tanpa URL tujuan, dengan riwayat hasil sebelumnya. Ekspor ulang dengan `--export-only` tidak memerlukan jaringan. Tiga belas tes lokal lulus, termasuk pengujian bahwa ekspor pembaca tidak memakai fallback redirect dan resolusi ulang tidak memanggil model. Pemeriksaan hasil aktual memastikan ekspor tautan dan laporan tidak memuat URL redirect Google.

## Pekerjaan berikutnya

### Catatan eksekusi dan perbaikan penyimpanan

Peneliti mulai menjalankan pilot Gemini pada 10 September 2026. Pasangan pertama untuk pertanyaan penyebab campak berhasil: kondisi A tanpa metadata grounding, kondisi B memiliki enam sumber yang terhubung ke sitasi dan berhasil diresolusi. Ini hasil satu pasangan, belum kesimpulan keseluruhan.

Eksekusi berikutnya mengalami Windows `PermissionError` saat mengganti JSON checkpoint `trial_28ddb36b5b4fc613c5db0ba7`. Respons Gemini sudah tersimpan; file sementara memiliki progres dua URL dibanding satu URL pada JSON lama. Progres sementara telah dipulihkan setelah kecocokan respons dan identitas trial diperiksa, dengan cadangan di `outputs/checkpoint_recovery/20260910T080615523953Z/`. Perbaikan penyimpanan menambahkan retry terbatas hanya untuk operasi penggantian file. Dua belas tes lokal lulus, termasuk simulasi lock sementara dan permanen. Ekspor lokal diperbarui tanpa pemanggilan Gemini tambahan; resume akan melanjutkan resolusi respons tersimpan.

1. Lengkapi manifest pengumpulan Trends dan pemetaan ekspor asli ke file terpilih; jangan mengasumsikan metadata yang tidak tersedia di CSV.
2. Tinjau metadata bahasa yang masih `unknown` bila diperlukan untuk tahap berikutnya; pemeriksaan makna `icd 10` telah selesai.
3. Tinjau hasil pilot PAA dan evaluasi konfigurasi sebelum membekukan prosedur pengumpulan utama; konfigurasi batch pilot sudah disimpan.
4. Seleksi 52 pertanyaan PAA yang telah dikumpulkan berdasarkan bahasa, cakupan, kejelasan intent, dan duplikasi. Pertahankan hubungan ke `topic_id` Trends. Tambahkan batch hanya setelah mempertimbangkan sisa kuota; 15 dari 183 topik sudah dicoba.
5. Susun rubrik dan prompt penilai Judgment pertama, lalu susun, nilai, dan revisi prompt sintesis sebelum dipakai.
6. Uji sintesis pada batch kecil dari sumber siap sintesis dan PAA yang telah diterima. Pertahankan makna sumber, terjemahkan sesuai aturan, dan hindari tambahan fakta atau batasan.
7. Lanjutkan pemeriksaan deterministik, Judgment kedua, dan audit manual.
8. Setelah instrumen siap, lanjutkan pilot/pengumpulan Google dan Gemini, resolusi URL langsung, crawling artikel, label, dan fitur untuk dataset awal bimbingan.

Catatan rencana lama di atas telah diperbarui oleh protokol query asli dan pengumpulan utama di bawah. Status `ready_for_synthesis` tetap merupakan nama historis, bukan proses sintesis yang dijalankan saat ini.

## Dataset utama: tiga percobaan, minimal dua valid

Peneliti memilih melanjutkan langsung dataset utama tanpa sintesis LLM dan menetapkan tiga percobaan Gemini per query dengan minimal dua valid. [MAIN_DATASET.md](MAIN_DATASET.md) menjadi pedoman terbaru; langkah sintesis/pilot tambahan dalam catatan historis tidak lagi berlaku.

Seleksi awal asisten pada 49 kandidat Indonesia menghasilkan 41 accepted, tujuh needs_review, dan satu excluded. Batch `main_01` berisi 15 kesehatan, 14 keuangan, dan 12 teknologi dengan maksimal 41 pencarian Google organik dan 123 panggilan Gemini. Akun SerpApi aktif terverifikasi memiliki kuota 250 sebelum pengumpulan dimulai. Respons pilot tidak digunakan ulang sebagai respons utama.

Skrip `src/collect_main_dataset.py` menggunakan checkpoint, pembekuan manifest, batas kuota, serta ekspor query, percobaan, sumber, hasil Google, dan pasangan kandidat. Minimum valid mengacu pada respons STOP dengan teks dan sitasi web pada metadata. Resolusi gagal menjadi ketidakpastian pencocokan, bukan label negatif. Ambang biner belum ditetapkan; crawling artikel dan ekstraksi fitur merupakan tahap selanjutnya. Sebanyak 21 tes lokal lulus tanpa API, termasuk tiga percobaan/dua valid, resume, error, kuota, dan penanganan URL.

Pengumpulan nyata sudah dimulai. Snapshot awal setelah tiga query selesai: sembilan percobaan, 24 pasangan kandidat, dua query memenuhi minimal dua valid. Satu query keuangan mengalami `MAX_TOKENS` pada ketiga percobaan dan belum layak dilabeli; ini kegagalan penyelesaian respons, bukan bukti tidak adanya sitasi. Progres berikutnya dapat dilihat di notebook 04, yang seluruh selnya telah diperiksa dengan hasil lokal tanpa API. Data pasangan masih memerlukan crawling, seleksi artikel, fitur, dan pelabelan.

## Penambahan query dari kuota tersedia

Batch `paa_expansion_01` menyelesaikan 30 pencarian dari 30 topik Trends baru (10 per domain), menghasilkan 96 PAA dan enam hasil tanpa PAA. Ditambah 96 kemunculan PAA dari respons utama tersimpan, snapshot berisi 192 kemunculan, 188 query unik berdasarkan domain/teks, dan 183 kandidat tambahan setelah lima query lama dipisahkan. Seleksi awal asisten menerima 123, menunda 29, dan mengeluarkan 31. Daftar diterima tambahan tersimpan terpisah; 41 query utama pertama tetap dipertahankan. Total daftar diterima awal + tambahan adalah 164, belum seluruhnya dikumpulkan Google/Gemini.

Sisa kuota SerpApi pada snapshot setelah pengumpulan PAA adalah 197. Pipeline lokal `prepare_query_expansion.py` dan notebook 05 dapat mengekstrak PAA berikutnya tanpa API sambil mempertahankan keputusan lama, teks asli, hubungan induk, kedalaman PAA, dan asal topik Trends. Sebanyak 24 tes lokal lulus. Panduan serta alasan seleksi ada di [QUERY_EXPANSION.md](MAIN_DATASET.md#penambahan-query).

Saat pemeriksaan ini, proses pengumpulan Gemini utama telah berhenti akibat HTTP 429 pada percobaan kedua query `Fungsi Excel apa saja?`. Checkpoint tersimpan dan penambahan query tidak menggunakan Gemini. Status ini memperbarui laporan sebelumnya bahwa pengumpulan masih berjalan.

## Gabungan Google Top-10 dan semua sitasi Gemini

Sesuai permintaan peneliti, ekspor pasangan kini juga menghasilkan `query_article_pairs_union.csv`, gabungan hasil organik Google dan seluruh URL tujuan yang disitasi pada percobaan Gemini valid. Metadata sitasi lengkap sebenarnya sudah disimpan; pembatasan sebelumnya terletak pada himpunan kandidat pasangan Google. URL berulang per query digabung dan sitasi dihitung sekali per percobaan, sementara sumber tidak valid/belum teresolusi tetap diarsipkan.

Ekspor lokal tanpa API menghasilkan 554 pasangan gabungan (515 URL kandidat unik), dibanding 202 pasangan Google. Asalnya: 132 Google saja, 70 keduanya, 352 Gemini saja. Contoh query batuk memiliki 21 kandidat gabungan dari sembilan Google dan 15 URL sitasi, dengan tiga URL beririsan. Ini kandidat sebelum crawling dan seleksi halaman. Notebook 04 kini menampilkan tabel gabungan. Dua puluh delapan tes lokal lulus, termasuk semua sumber sitasi, deduplikasi per percobaan, respons tidak valid, dan URL belum diketahui. Protokol serta implikasi sampling tercatat di [CANDIDATE_UNION.md](MAIN_DATASET.md#gabungan-kandidat).

## Pemeriksaan dan kelanjutan 11 September 2026

Implementasi gabungan kandidat, notebook 04, dan dokumentasi telah selesai. Sesuai permintaan untuk melanjutkan, satu panggilan Gemini baru dikirim pada slot ketiga query `Fungsi Excel apa saja?`; API kembali mengembalikan HTTP 429 dengan status `RESOURCE_EXHAUSTED`. Tidak ada pencarian organik Google baru pada percobaan melanjutkan ini. API tidak memberikan rincian quota metric atau retry delay pada respons yang diterima, sehingga jenis batas (per menit/per hari/batas lain) belum dapat dipastikan.

Ketiga slot query Excel sudah tercatat (satu respons valid, dua error 429); tidak ada percobaan keempat. Checkpoint dituntaskan secara lokal tanpa API. Jeda Google dan percobaan terakhir juga telah melampaui enam jam, sehingga query ini belum layak. Snapshot terbaru: 24 dari 41 query selesai diproses, 21 memenuhi minimal dua valid, 17 belum dimulai, dan 72 catatan percobaan. Tabel gabungan tetap 554 pasangan/515 URL kandidat unik. Selesai diproses tidak berarti semuanya berhasil atau siap pemodelan.

Penyimpanan error ditambah dengan rincian kuota yang diizinkan bila tersedia (status, quota metric/ID/value, retry delay), tanpa URL permintaan, API key, pesan provider bebas, atau identitas akun/proyek. Error pada slot terakhir kini langsung menuntaskan status query agar resume tidak menganggapnya masih memerlukan percobaan. Sebanyak 31 tes lokal lulus. Pengumpulan berhenti setelah 429; periksa batas akun Gemini sebelum mencoba 17 query berikutnya. [Dokumentasi batas Gemini](https://ai.google.dev/gemini-api/docs/rate-limits) membedakan batas per menit, token, dan per hari; pergantian tanggal WIB tidak cukup untuk menyimpulkan kuota sudah reset.

## Pemulihan pencarian SerpApi yang terputus

Setelah peneliti melanjutkan, pencarian `vitamin C untuk apa fungsinya?` tercatat gagal koneksi tanpa respons lokal, sementara akun SerpApi menunjukkan 55/250 terpakai. Account API berhasil diakses dan menunjukkan 195 tersisa. Pemulihan satu permintaan identik berhasil mendapatkan respons Google tersimpan, dengan delapan hasil organik. Metadata mencatat waktu pemrosesan 52,49 detik, melampaui batas tunggu lama 45 detik; ini mendukung diagnosis timeout, meski jenis exception asli tidak tersimpan. Kuota sebelum/sesudah pemulihan tetap 55 terpakai dan 195 tersisa.

`collect_paa.fetch` kini menunggu hingga 120 detik, mengklasifikasikan error jaringan, dan tetap memverifikasi TLS tanpa retry otomatis. `recover_main_google.py` memungkinkan pemulihan eksplisit satu query Google gagal yang belum memiliki respons/percobaan Gemini, dengan riwayat checkpoint, pemeriksaan kuota, cache default, dan waktu pencarian asli. Respons yang sudah tersimpan tidak dikirim ulang. Sebanyak 36 tes lokal lulus. Checkpoint vitamin C sudah `response_saved` dengan nol panggilan Gemini selama pemulihan; perintah kolektor biasa dapat melanjutkannya. Ekspor setelah pemulihan berisi 210 pasangan Google dan 562 pasangan gabungan; 24 query selesai diproses, satu menunggu resolusi/Gemini, dan 16 belum dimulai.

## Pengumpulan main_01 selesai — 11 September 2026

Peneliti melanjutkan skrip dan seluruh 41 query kini selesai diproses. Seluruh pengambilan Google berstatus completed dan tidak ada lock proses aktif. Terdapat 123 catatan percobaan Gemini: 114 valid (STOP dengan sitasi), tujuh selesai dengan MAX_TOKENS, dan dua error 429 yang tetap dipertahankan. Sebanyak 38 query memenuhi minimal dua valid dan jendela waktu pengumpulan.

Hasil Google berisi 348 kemunculan organik. Gabungan Google dan sitasi valid menghasilkan **983 pasangan query–artikel dengan 903 URL kandidat unik**: 216 Google saja, 132 keduanya, dan 635 Gemini saja. Tabel sumber memiliki 1.360 kemunculan; 21 kemunculan sitasi belum memiliki URL tujuan. Angka URL unik berdasarkan normalisasi konservatif, belum membuktikan jumlah artikel unik/layak setelah crawling dan canonical.

Dari tabel gabungan, 942 pasangan berasal dari 38 query yang memenuhi syarat. Di dalamnya, 757 pasangan mempunyai proporsi pasti tetapi ambang label belum ditetapkan, dan 185 masih memiliki ketidakpastian pencocokan URL. Sebanyak 41 pasangan lain berasal dari tiga query belum layak: `Gaji 6 juta pajak berapa?` (nol valid), `Rumus apa saja di Excel?` (satu valid), dan `Fungsi Excel apa saja?` (satu valid serta jeda melebihi enam jam). Tiga query tersebut tetap diarsipkan.

Lihat notebook 04 dan `data/interim/main/main_01/queries.csv`, `query_article_pairs_union.csv`, serta `sources.csv`. Pengumpulan batch pertama selesai, sedangkan pengambilan isi artikel, seleksi halaman/bahasa, pencocokan URL lanjutan, keputusan ambang label, dan ekstraksi fitur masih diperlukan. Daftar 123 query tambahan tetap merupakan kandidat untuk batch berikutnya dan tidak tercakup dalam 41 query main_01 ini.


## 11 September 2026 ? perapian proyek dan rencana pengolahan artikel

- Menghapus sembilan cache `.pyc` dan empat panduan yang isinya telah digabungkan ke `docs/MAIN_DATASET.md` (protokol query asli, ekspansi query, gabungan kandidat, dan petunjuk penggabungan Trends dari `src/README.md`). Total 13 file dihapus; isi panduan dipertahankan dan tautannya diperbarui.
- Mengisi README utama sebagai pintu masuk proyek. Data penelitian, konfigurasi, notebook, checkpoint, serta cadangan pemulihan dipertahankan. Modul pilot tetap diperlukan oleh kolektor utama.
- Verifikasi: 36 pengujian unit lulus; tidak menjalankan pengumpulan API nyata atau menulis kode pipeline baru.
- Prioritas berikut: unduh isi URL unik dengan checkpoint, tinjau kelayakan artikel, periksa alias/canonical dan pencocokan sitasi yang belum pasti, tetapkan ambang label sebelum pemodelan, lalu ekstrak fitur dan bentuk dataset siap pakai. Halaman gagal diakses tidak otomatis menjadi label negatif.
- Pemisahan peran: Python untuk crawling, ekstraksi, pencocokan, serta ekspor yang dapat dilanjutkan; Jupyter untuk review artikel, distribusi domain/label, dan pemeriksaan kualitas.
- Anggaran yang dilaporkan pengguna: Gemini Rp82.000; SerpApi 71/250 (diasumsikan 71 terpakai, sehingga tersisa 179). Pengambilan halaman langsung tidak memakai panggilan Gemini/SerpApi. Setelah jumlah artikel layak diketahui, pertimbangkan batch baru 15?30 query dari kandidat tambahan yang tersedia: maksimal 15?30 pencarian Google dan 45?90 percobaan Gemini. Periksa biaya aktual per blok kecil sebelum melanjutkan; belum ada pengeluaran baru yang dilakukan.


### Ketentuan awal kredibilitas sumber

Peneliti menetapkan rubrik lima tingkat: (1) pemerintah atau institusi berstatus tertinggi sesuai kriteria; (2) verifikasi resmi kategori lain; (3) proses editorial/tinjauan ahli terlihat; (4) identitas jelas tanpa status verifikasi resmi yang ditemukan; (5) tidak dapat diverifikasi atau UGC/forum tanpa identitas jelas. Tabel lengkap dicatat di CONTEXT.md dan panduan dataset utama. Belum dilakukan penilaian situs atau perubahan kode/data. Sumber yang belum ditinjau dibedakan dari tingkat 5.


### PAA ekspansi 02 ? pemakaian sisa kuota akun pertama

Pada 11 September 2026 dijalankan 22 pencarian baru dari topik Trends needs_paa (7 kesehatan, 7 keuangan, 8 teknologi), tanpa mengulang request lama dan tanpa Gemini. Sebanyak 16 pencarian menghasilkan PAA dan 6 tidak memiliki PAA; tidak ada request gagal. Tersimpan 64 kemunculan pertanyaan. Kuota akun sebelum pengumpulan 22 (228/250 terpakai); setelahnya masih 1 (249/250 terpakai); jumlah request tidak selalu sama dengan pengurangan kuota.

Batch `paa_expansion_02` ditambahkan ke konfigurasi query ekspansi yang digunakan Notebook 05. Hasil ekspor menambah 64 kandidat unik berdasarkan query_id; kandidat baru belum ditinjau. Seluruh keputusan manual sebelumnya dipertahankan identik. Respons mentah, manifest, catatan kuota, dan CSV hasil tersimpan; batch utama main_01 tidak diubah.


Pemeriksaan kuota terakhir pada 11 September 2026 07:24 UTC mengonfirmasi 0 tersisa (250/250 terpakai), tersimpan di `data/raw/paa/batches/paa_expansion_02/quota_final.json`. Rencana satu pencarian tambahan `compress pdf` dibatalkan otomatis oleh pemeriksaan kuota sebelum request pencarian dikirim; konfigurasi sementara dihapus. Hasil akhir tetap 22 pencarian, 64 kandidat tambahan: 28 kesehatan, 24 keuangan, 12 teknologi. Pool ekspansi kini 309 kandidat: 123 accepted, 29 needs_review, 31 excluded, 126 pending.


## LLM-as-a-judge untuk seleksi query di Notebook 05

Atas permintaan peneliti, asisten LLM dalam sesi Codex menilai kelayakan query PAA menggunakan rubrik yang dirumuskan melalui diskusi dengan peneliti. Kegiatan ini termasuk **LLM-as-a-judge untuk penyaringan query**, atau seleksi berbantuan LLM dengan koreksi manusia. Ini bukan sintesis query: teks pertanyaan PAA asli tidak ditulis ulang. Ini juga bukan penilaian kebenaran jawaban Gemini, penilaian kredibilitas artikel, atau pembentukan label keterkutipan.

### Masukan, rubrik, dan prosedur

Masukan penilaian adalah teks kandidat, domain, status serta alasan review terdahulu, konteks sumber yang tersedia, dan daftar query yang sudah diterima untuk pemeriksaan duplikasi. Penilaian kejelasan intent didasarkan pada kemampuan teks berdiri sendiri; keyword asal tidak digunakan untuk menambahkan makna yang hilang. Asisten melihat seluruh konteks diskusi, sehingga proses ini bukan evaluasi buta dengan prompt terisolasi.

Rubrik mencakup relevansi domain, kejelasan intent, kelengkapan bahasa Indonesia, kebutuhan informasi yang dapat dibahas artikel, dan duplikasi kebutuhan informasi. Pertanyaan umum, angka yang bergantung pada skenario, rekomendasi/perbandingan, dan premis yang mungkin keliru tidak otomatis ditolak. Penilaian tidak menggunakan jawaban atau keberhasilan sitasi Gemini sebagai dasar penerimaan.

Duplikasi dinilai secara semantik oleh asisten dengan membandingkan objek, kebutuhan informasi, dan batas eksplisit. Query utama atau query yang sudah diterima diutamakan sebagai wakil. Entri yang dikeluarkan karena duplikasi mencantumkan alasan dan `duplicate_of` di notebook. Ini bukan hasil algoritme deduplikasi otomatis yang telah divalidasi.

### Cakupan dan hasil penilaian

Snapshot yang ditinjau berisi **149 query: 23 needs_review dan 126 pending**. Sebelum langkah ini terdapat 127 accepted dan 33 excluded, termasuk enam keputusan yang telah diisi peneliti. Keputusan final tersebut dipertahankan.

| Domain | Accepted oleh asisten | Excluded oleh asisten |
| --- | ---: | ---: |
| Kesehatan | 48 | 6 |
| Keuangan | 49 | 13 |
| Teknologi | 22 | 11 |
| Total | 119 | 30 |

Seluruh keputusan dan alasan disimpan sebagai `assistant_decisions` dalam [Notebook 05](../notebooks/05_review_query_expansion.ipynb), bagian Review asisten berdasarkan rubrik. Sel penerapan menggunakan `reviewer=asisten_rubrik_v1`; koreksi peneliti menggunakan `reviewer=peneliti` dan tetap diutamakan. Reviewer asisten tidak dicatat sebagai penilai manusia.

Pada saat penyusunan keputusan, notebook diuji menggunakan salinan data sementara: cakupan 149 keputusan, perlindungan keputusan final lama, pengulangan tanpa perubahan, dan prioritas koreksi peneliti telah diperiksa. CSV penelitian asli tidak diubah pada langkah penyusunan tersebut. Menjalankan sel penerapan menyimpan keputusan ke `data/manual/query_expansion_01_decisions.csv` dan memperbarui ekspor lokal. Jika seluruh keputusan diterapkan tanpa koreksi tambahan, total pool menjadi **246 accepted dan 63 excluded**. Tidak ada panggilan SerpApi atau Gemini untuk langkah review ini; penilaian dilakukan oleh asisten LLM dalam percakapan, bukan tanpa penggunaan LLM.

### Batas pelaporan dan tindak lanjut

Belum dilakukan penilaian independen oleh beberapa penilai, pengulangan penilaian LLM, atau pengukuran kesepakatan manusia-LLM. Keputusan ini tidak boleh dilaporkan sebagai ground truth manusia atau sebagai validasi objektif kelayakan query. Enam keputusan manusia yang sudah ada juga tidak merupakan pengujian kesepakatan independen untuk 149 keputusan baru.

Prompt penilaian berasal dari instruksi dan rubrik dalam riwayat percakapan, bukan satu template prompt terpisah. Identitas layanan penilai adalah asisten Codex; ID model/snapshot yang dapat direproduksi dan parameter sampling tidak diarsipkan pada tahap ini, sehingga tidak boleh direka untuk pelaporan. Notebook menyimpan keputusan dan alasan, tetapi bukan rekaman lengkap input-output API penilai. Riwayat percakapan perlu dipertahankan sebagai jejak instruksi bila tersedia.

Tindak lanjut metodologis: peneliti meninjau keputusan asisten, terutama penolakan karena ambiguitas dan duplikasi, mencatat koreksi beserta alasan, serta mengaudit konsistensi query yang sudah accepted/excluded sebelum langkah ini. Jika mengklaim reliabilitas penilaian, diperlukan evaluasi manusia independen yang direncanakan dan dilaporkan tersendiri. Keputusan akhir seleksi query tetap menjadi tanggung jawab peneliti.


## 11 September 2026 - target sekitar 300 query accepted tercapai

Peneliti meminta pengumpulan PAA tambahan dan keputusan langsung accepted/excluded menggunakan rubrik yang sama. Titik awal 287 accepted (41 main_01 dan 246 tambahan). Akun aktif diperiksa melalui Account API: 179 pencarian tersisa, bukan perkiraan 120-an.

Batch paa_expansion_03 dan paa_expansion_04 mengirim sembilan pencarian dari keyword Trends needs_paa yang belum dicari: cetirizine, rupiah, subsidi tepat, blackbox ai, duckduckgo, gform, uang, maxstream, ibox. Lima pencarian menghasilkan PAA, dua no_paa (blackbox ai dan duckduckgo), dan dua error SerpApiError tanpa respons tersimpan (subsidi tepat dan maxstream). Rincian sebab jaringan/HTTP tidak tersedia pada checkpoint kolektor ini, sehingga penyebab pasti tidak disimpulkan. Resume hanya mengerjakan request yang belum memiliki checkpoint; error lama tidak dikirim ulang. Kuota akhir 170 (80/250 terpakai); sembilan pencarian terpakai, tanpa panggilan Gemini.

Hasil: 20 kemunculan PAA, satu kemunculan query yang sudah ada (Tukar uang di BCA apakah bisa?), 19 kandidat baru. Penilaian LLM-as-a-judge dalam sesi Codex dengan rubrik yang sama menerima 15 dan mengeluarkan 4. Identitas reviewer: asisten_rubrik_target300_v1. Penolakan berkaitan dengan intent tidak lengkap atau konteks teknologi tidak jelas; penerimaan tidak memvalidasi premis medis/keuangan atau menjamin grounding. Tidak ada kandidat baru yang dibiarkan pending/needs_review. Semua keputusan dan alasan tercantum dalam blok tambahan Notebook 05 dan telah diterapkan ke CSV. Keputusan manual/asisten lama dipertahankan identik, termasuk timestamp.

Total sekarang **302 accepted: 129 kesehatan, 103 keuangan, 70 teknologi**. Sebanyak 41 sudah masuk main_01, sedangkan **261 accepted tambahan belum menjalani pengumpulan utama**. Pool ekspansi berisi 328 kandidat (261 accepted, 67 excluded). Tujuh needs_review dan 29 deferred_language pada pool awal berada di luar lingkup review tambahan ini dan tidak diubah. main_01 tetap dibekukan; belum ada scraping artikel atau pengumpulan Gemini baru. Pengumpulan PAA dihentikan karena target tercapai.

Berkas hasil: data/interim/paa/paa_expansion_03, data/interim/paa/paa_expansion_04, dan data/interim/query_expansion/query_expansion_01/accepted_new.csv. Backup sebelum penerapan: outputs/review_backups/20260911T094305962144Z. Verifikasi mencakup cakupan 19 keputusan, identitas reviewer, tidak ada overlap query_id accepted dengan main_01, jumlah total per domain, sintaks sel notebook, dan integritas manifest main_01.

## 12 September 2026 - uji scraping 20 URL dan dataset fitur artikel

Peneliti memilih cakupan **gabungan Google Top-10 dan seluruh sitasi Gemini**, lalu meminta uji 20 URL sebelum pengambilan lebih besar. Peneliti juga menyetujui **label positif jika proporsi sitasi >=0,5 untuk dataset contoh**: 1 dari 2 atau 2 dari 3 percobaan valid. Persetujuan ini diterapkan pada configs/article_features.json; konfigurasi dan respons pengumpulan main_01 yang dibekukan tidak diubah. Pengambilan langsung dari situs dan penghitungan embedding lokal tidak memakai kuota SerpApi atau Gemini.

Manifest scraping memuat **870 URL unik dari 942 pasangan query-artikel** pada query main_01 yang memenuhi syarat pengumpulan, bukan seluruh 903 URL dari 983 pasangan sebelum penyaringan kelayakan query. Pemilihan awal diselingi berdasarkan domain, asal kandidat, dan query; ini contoh teknis, bukan sampel acak representatif. Tepat **20 URL dicoba**, sehingga 850 kandidat belum dicoba. Sebuah URL bisa berhubungan dengan beberapa query: 20 URL tersebut menghasilkan **24 pasangan** dalam dataset contoh.

Hasil akhirnya **17 halaman berhasil diekstrak**, terdiri dari **15 artikel/halaman informasi berbahasa Indonesia yang diterima** dan 2 halaman dikeluarkan (listing aplikasi Google Play dan artikel Yahoo berbahasa Inggris). Tiga URL belum diambil: Bio Farma dan account.pajak.go.id berstatus robots_unavailable, sedangkan Facebook berstatus robots_disallowed. Status ini tidak menyatakan situs hilang atau sumber tidak kredibel. Semua URL tetap ada dalam articles.csv dan pasangan terkait tetap ada dalam dataset.csv; fitur yang tidak tersedia dikosongkan. Tiga error ekstraksi awal dipulihkan dari HTML tersimpan setelah dependensi dan ekstraktor diperbaiki, tanpa mengunduh ulang halaman; original_crawl_status mempertahankan status awal.

Struktur HTML dan hasil ekstraksi diperiksa untuk menyesuaikan selector isi, antara lain Pegadaian, Kapz, DQLab, Android Help, Eka Hospital, DJP, dan Ayo Sehat Kemenkes. Pada Kemenkes, isi lengkap sudah tersedia di HTML pada #isi-lengkap sehingga ekstraksi tidak berhenti pada ringkasan. Pada DJP, keseluruhan elemen article dipertahankan agar berbagai kategori persyaratan NPWP tidak terpotong. Menu, footer, artikel terkait, dan label antarmuka dibersihkan. Judul H1 digunakan ketika metadata judul terlalu umum. Konflik bahasa metadata dengan isi dan kelayakan halaman bantuan dicatat dalam data/manual/article_review.csv. Review ini dilakukan asisten dari HTML/teks, bukan penilaian manusia independen atau validasi kebenaran isi.

Dataset menyediakan **37 fitur numerik** untuk lima kelompok rancangan: struktur, keterbacaan (WPS/CPW), kekayaan informasi, kredibilitas/metadata, dan relevansi query-artikel. Definisi dan batas pengukuran ada di MAIN_DATASET.md bagian scraping-dan-fitur. BM25 memakai judul dan isi dari 15 artikel yang diterima; korpus dan hash dicatat sehingga skor harus dihitung ulang ketika korpus bertambah. Kemiripan semantik sudah dihitung menggunakan sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 melalui FastEmbed/ONNX lokal, dengan potongan 112 token, overlap 16, dan agregasi rerata vektor ternormalisasi untuk mencakup seluruh teks. Model dan vektor disimpan dalam cache; sidik artefak model dicatat. Fitur turunan sitasi, posisi Google, dan identitas baris tidak dimasukkan sebagai prediktor dalam feature_columns.json. Metadata yang tidak ditemukan tidak direka.

Rubrik kredibilitas 1-5 mengikuti ketentuan peneliti. Tabel data/manual/source_credibility.csv menyimpan bukti, alasan, tanggal, dan penilai. Dari 20 hostname, **9 terverifikasi, 6 provisional, 3 perlu verifikasi, dan 2 perlu pemetaan rubrik** untuk institusi pendidikan. Peringkat kosong tidak otomatis menjadi tingkat 5. Pemeriksaan memakai domain pemerintah, pengumuman izin Pegadaian pada situs OJK, serta pencarian registrasi PSE publik dengan kecocokan domain, operator, dan status; respons PSE disimpan di data/raw/credibility. Registrasi platform tidak membuktikan kualitas setiap halaman atau pembuat kontennya. Eka Hospital tetap provisional karena kategori KARS tertinggi yang berlaku untuk unit terkait belum dipastikan. Semua peringkat provisional/kosong dikeluarkan dari model_ready sampai ditinjau lebih lanjut.

Dari 24 pasangan, **20 mempunyai label pasti (9 positif, 11 negatif)** dan 4 tetap kosong karena pencocokan URL sitasi belum pasti. Ketidakpastian tidak diubah menjadi label negatif. Setelah kelayakan artikel, label, kredibilitas, embedding, dan kemungkinan alias URL diperiksa, **7 pasangan masuk model_ready.csv (3 positif, 4 negatif)**. Ini contoh alur dataset dan belum memadai untuk pelatihan/evaluasi penelitian. Waktu scraping berbeda dari waktu pengumpulan jawaban Gemini, sehingga perubahan isi halaman setelah jawaban dikumpulkan merupakan keterbatasan yang perlu dilaporkan.

Kode yang dapat dilanjutkan: src/scrape_articles.py (preview, pengambilan terbatas, checkpoint/resume, retry khusus kegagalan, pemeriksaan robots dan batas respons), src/article_features.py, src/article_embeddings.py, src/build_article_dataset.py, serta src/check_source_credibility.py. Dependensi terpasang dan dicatat dalam requirements-articles.txt. HTML/respons mentah, ekstraksi turunan, tabel artikel, dan tabel pasangan disimpan terpisah untuk audit. Hasil berada di data/processed/articles_main_01: articles.csv, dataset.csv, model_ready.csv, feature_columns.json, summary.json, dan embedding_model_manifest.json.

Notebook **06_inspect_article_dataset.ipynb** menampilkan hasil, teks artikel, fitur, label, bukti kredibilitas, serta alasan kegagalan. Semua sel bawaan hanya membaca hasil lokal. Untuk mengambil batch berikutnya, aktifkan RUN_SCRAPING dan tentukan MAX_NEW_URLS; untuk memperbarui fitur setelah koreksi CSV manual, cukup aktifkan RUN_BUILD. Padanan terminal: python src/scrape_articles.py --run --max-new-urls 20, kemudian python src/build_article_dataset.py --with-embeddings. Batas 20 berarti tambahan URL baru, bukan total kumulatif; checkpoint lama dilewati. Perintah --retry-failed dipakai secara eksplisit hanya untuk kegagalan dan tetap mengikuti robots. Panduan lengkap dan cara mengganti batch sumber/config ada di MAIN_DATASET.md.

Validasi: **67 unit test lulus**; validasi format dan sintaks Notebook 06 serta eksekusi seluruh sel bawaan berhasil tanpa subprocess/jaringan. Audit CSV memastikan tepat 20 checkpoint/URL unik, 24 pasangan unik, 15 artikel diterima, 7 pasangan model_ready, 37 fitur tanpa kolom label bocor, rentang cosine sah, dan label sesuai ambang yang disetujui. Pengumpulan dihentikan pada 20 URL sesuai lingkup uji; pengambilan 261 query accepted tambahan dari progres sebelumnya belum dijalankan.

## 14 September 2026 - dataset utama Google Top-10 dan tambahan Gemini-only

Peneliti meminta pemisahan sebelum scraping berikutnya: **dataset utama berisi artikel Google Top-10 dengan label biner keterkutipan Gemini**, sedangkan **dataset tambahan berisi sitasi Gemini yang berada di luar Top-10 untuk query yang sama**. Peneliti menegaskan kembali **ambang proporsi sitasi >=0,5**, bukan label positif hanya karena pernah muncul satu kali. Dengan demikian label 0 berarti di bawah ambang yang ditetapkan, dan tidak selalu berarti sama sekali tidak pernah disitasi. Label tetap kosong jika pencocokan sumber belum pasti.

Aturan keanggotaan diterapkan pada pasangan query-artikel: google_only dan google_and_gemini masuk utama; gemini_only masuk tambahan. Artikel yang berada di kedua sumber tetap masuk utama. URL yang sama boleh berada di kelompok berbeda untuk query berbeda, sehingga pemisahan tidak dilakukan secara global berdasarkan URL. Istilah di luar Top-10 hanya mengacu pada hasil Google yang tersimpan untuk query tersebut; tidak menyimpulkan peringkat pasti atau bahwa URL tidak terindeks.

src/build_article_dataset.py kini mengekspor secara otomatis:

| File pada data/processed/articles_main_01 | Isi dan jumlah saat pemisahan |
| --- | --- |
| dataset.csv | **13 pasangan utama**, terdiri dari 7 google_only dan 6 google_and_gemini; 13 URL unik |
| dataset_gemini_only.csv | **11 pasangan tambahan**; 9 URL unik |
| dataset_union.csv | **24 pasangan** gabungan untuk audit; 20 URL unik |
| model_ready.csv | **3 pasangan utama** lolos seluruh pemeriksaan: 2 positif dan 1 negatif |
| articles.csv | Tetap 20 URL yang pernah dicoba, dengan teks/fitur/status masing-masing |

Dua URL muncul pada kedua kelompok untuk query berbeda; karena itu jumlah URL unik masing-masing kelompok tidak boleh dijumlahkan sebagai total unik gabungan. Dataset utama memiliki **4 label positif, 6 negatif, dan 3 belum pasti**. Tambahan memiliki **5 positif, 5 negatif menurut ambang, dan 1 belum pasti**. Keanggotaan tambahan menunjukkan pernah disitasi, sedangkan satu kali dari tiga percobaan valid masih berlabel 0 pada ambang 0,5. Empat pasangan tambahan lolos pemeriksaan dengan ready_for_analysis=True, tetapi tidak masuk model utama. ready_for_model hanya True pada pasangan utama yang lolos; alasan supplement_not_primary menandai tambahan. Perubahan jumlah model_ready dari 7 menjadi 3 disebabkan pemisahan empat pasangan tambahan, bukan hilangnya hasil scraping atau penurunan kualitas artikel.

Statistik BM25 sekarang memakai **10 artikel eligible yang terdapat dalam Google Top-10**, bukan seluruh 15 artikel eligible gabungan. Dataset tambahan diberi skor memakai referensi yang sama; artikel yang tidak pernah menjadi kandidat Top-10 tidak mengubah IDF atau panjang rata-rata korpus utama. Istilah di luar kosakata referensi tidak berkontribusi; jika belum ada korpus referensi utama, skor dikosongkan. Hash korpus baru: bad333d4627cbd221a1f509757b63c434120a8fb27f074891d8b2eeb3dcf80bf. Versi fitur output diperbarui menjadi article_features_v2_google_top10 dan protokol pemisahan google_top10_primary_gemini_only_supplement_v1. Definisi 37 prediktor tetap; kolom kelompok, sumber kandidat, dan hasil sitasi tetap merupakan audit/target, bukan prediktor. Kebijakan korpus saat train/test masih perlu ditetapkan sebelum evaluasi final.

Hasil dibangun ulang **secara lokal** dari HTML dan cache embedding yang tersedia. Tidak ada scraping, panggilan SerpApi, panggilan Gemini, atau unduhan model baru. Sebanyak 52 berkas raw scraping diperiksa hash sebelum/sesudah dan identik. Raw respons utama, manifest pengumpulan, manifest scraping, keputusan review, dan label sebelumnya dipertahankan. Salinan ekspor sebelum pemisahan tersimpan di outputs/review_backups/dataset_split_20260914T020530Z. Jumlah pengambilan tetap 20 URL, dengan 17 berhasil diekstrak, 15 layak, 2 dikeluarkan, dan 3 belum berhasil diambil.

Notebook 06 diperbarui untuk menampilkan kedua kelompok secara terpisah serta arsip gabungan. README, MAIN_DATASET.md, dan PANDUAN_MENAMBAH_DATASET.md menjelaskan file keluaran dan alur aktif. Perintah scraping/build berikutnya tetap sama; satu pengambilan URL gabungan menyediakan kedua dataset. Sampel awal tetap berasal dari urutan manifest gabungan yang dibekukan, sehingga pemisahan ini tidak menjadikan 13 pasangan utama sebagai sampel acak atau Top-10 lengkap per query.

Validasi: **70 unit test lulus**, termasuk keanggotaan per query, artikel yang muncul pada kedua sumber, kegagalan/ketidakpastian tetap tersimpan, keluaran tambahan kosong dengan header, penolakan flag sumber tidak konsisten, tambahan tidak masuk ekspor model, dan kestabilan BM25 utama terhadap penambahan dokumen tambahan. Audit hasil memastikan kedua kelompok tidak tumpang tindih pada identitas pasangan, gabungannya tepat 24 pasangan awal, label/URL/hitungan sitasi/embedding tidak berubah, serta 3 baris model berasal dari utama. Semua sel bawaan Notebook 06 berhasil dijalankan tanpa proses pengumpulan.

### 14 September 2026 - memastikan scraping lanjutan mengikuti pemisahan

Peneliti meminta agar hasil scraping berikutnya juga masuk ke dataset yang benar. Alur builder otomatis yang sudah diterapkan dipertahankan: checkpoint lama dan baru diproses bersama, pasangan Top-10 masuk dataset.csv, Gemini-only masuk dataset_gemini_only.csv, dan hanya utama yang boleh masuk model_ready.csv. Scraper tetap mengambil URL unik satu kali per batch; keputusan kelompok berada pada pasangan query-artikel, bukan pada direktori HTML fisik.

Notebook 06 disesuaikan agar satu variabel FEATURE_CONFIG mengendalikan config scraping, folder hasil, sumber review kredibilitas, dan argumen kedua perintah. Mengganti batch tidak lagi memerlukan penggantian path OUTPUT dan perintah secara terpisah. RUN_SCRAPING=True menjalankan scraping lalu pembangunan ulang otomatis; kedua tabel kelompok dimuat ulang dan jumlah/folder hasil ditampilkan setelah selesai. Pilihan artikel contoh juga menyesuaikan jika Alodokter tidak ada dalam batch baru. Panduan penambahan dan MAIN_DATASET.md menegaskan bahwa pada terminal, builder dijalankan setelah scraper untuk memperbarui dataset final.

Ditambahkan satu tes integrasi dengan HTTP/embedding simulasi: mengambil satu URL, membangun dataset, melanjutkan dua URL berikutnya, lalu membangun ulang. Tes membuktikan checkpoint awal tidak berubah, URL bersama diunduh sekali, pasangan baru masuk ke kelompok yang tepat, URL gagal tetap berada di dataset tambahannya, dan model hanya memuat pasangan utama. **Sembilan tes pada test_build_article_dataset.py lulus**, termasuk tes integrasi baru. Sel notebook juga diperiksa dalam mode baca dan cabang scraping/build dengan subprocess yang disimulasikan. Tidak ada pengambilan website, panggilan SerpApi/Gemini, atau perubahan jumlah dataset riil; tetap 20 URL, 13 pasangan utama dan 11 tambahan.

## 17 September 2026 - otoritas domain disederhanakan menjadi dua level

Atas keputusan peneliti, rubrik kredibilitas 1–5 diganti oleh fitur **`domain_authority_level` biner**. Level 2 berarti otoritas tinggi: domain kesehatan yang jelas terafiliasi rumah sakit/klinik, domain keuangan yang terafiliasi lembaga berizin OJK, domain teknologi yang terafiliasi perusahaan/platform terdaftar PSE, suffix `.ac.id`/`.go.id`, atau media besar yang jelas kredibel. Level 1 menjadi default/rendah bagi semua lainnya, termasuk status tidak jelas atau ambigu. Tidak ada lagi level kosong, provisional, pemeriksaan KARS rinci, atau kebutuhan menyelesaikan edge case sebelum dataset dapat digunakan.

Aturan dibekukan dalam `configs/domain_authority.json` dengan versi `domain_authority_binary_v1`. Suffix pemerintah dan akademik diterapkan otomatis; rumah sakit/klinik, afiliasi OJK, perusahaan/platform PSE, dan media besar menggunakan daftar hostname eksplisit beserta basis kategori. Host baru yang tidak ditemukan otomatis Level 1. `domain_authority_basis` dan versi aturan disimpan sebagai kolom audit, tetapi hanya `domain_authority_level` menjadi fitur model. Level tidak menyatakan kebenaran isi artikel atau aturan internal Gemini.

`src/build_article_dataset.py` dan `configs/article_features.json` diperbarui. Fitur `credibility_level` diganti oleh `domain_authority_level`; jumlah prediktor tetap 37. Status `credibility_needs_verification` dihapus dari syarat kesiapan. `data/manual/source_credibility.csv`, respons PSE mentah, dan dokumentasi rubrik 1–5 dipertahankan sebagai arsip historis tetapi tidak lagi dibaca builder. Versi fitur menjadi `article_features_v3_binary_domain_authority`. Notebook 06 menampilkan level, basis, dan versi aturan baru; output lama notebook dibersihkan agar tidak menampilkan status kredibilitas yang sudah kedaluwarsa.

Dataset dibangun ulang secara lokal tanpa scraping, SerpApi, atau Gemini. Snapshot aktual berisi **90 URL dicoba, 112 pasangan gabungan, 68 pasangan utama, dan 44 pasangan tambahan**. Dari 90 domain artikel, **48 mendapat Level 2 dan 42 Level 1**. `model_ready.csv` sekarang berisi **23 pasangan utama: 7 positif dan 16 negatif**, naik dari 3 karena ketidakpastian rubrik lama tidak lagi memblokir baris. Perubahan ini tidak mengubah label, status crawling, keputusan artikel, BM25, atau embedding. Artikel gagal, halaman tidak eligible, label tidak pasti, dan alias yang perlu diperiksa tetap tidak masuk model-ready. Status `eligible_auto` masih mengikuti aturan kelayakan ekstraktor dan tetap dapat diverifikasi manusia melalui `article_review.csv` sebelum dataset final dibekukan.

Ekspor sebelum perubahan disalin ke `outputs/review_backups/domain_authority_binary_20260917`. Audit memastikan seluruh artikel memiliki tepat Level 1 atau 2, basis tidak kosong, kolom lama tidak menjadi fitur, tidak ada alasan kesiapan kredibilitas lama, dan seluruh 23 pasangan model-ready berasal dari dataset utama dengan label pasti. **72 unit test lulus**, termasuk pengujian suffix, daftar hostname, default Level 1, dan pipeline lanjutan. Notebook 06 tervalidasi dan seluruh sel default berjalan tanpa proses pengumpulan.
