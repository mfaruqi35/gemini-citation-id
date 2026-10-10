# Verifikasi artikel terbaru — 10 Oktober 2026

## Cakupan

Audit menggunakan [rubrik kelayakan artikel](RUBRIK_SELEKSI_ARTIKEL.md), versi `article_eligibility_20261006_v1`, pada artikel Google Top 10 yang sudah diambil dalam batch 3 dan 4. Irisan Top 10 dengan sitasi Gemini termasuk cakupan ini. Artikel yang hanya berasal dari sitasi Gemini tetap menjadi dataset tambahan.

| Batch | URL utama yang sudah dicoba | Lolos penyaringan teks untuk inspeksi | Sudah memiliki keputusan | Artikel baru dinilai |
| --- | ---: | ---: | ---: | ---: |
| articles_main_03 | 372 | 202 | 116 | 86 |
| articles_main_04 | 92 | 58 | 5 | 53 |
| **Total kemunculan per batch** | **464** | **260** | **121** | **139** |

Kandidat baru berjumlah **139 ID artikel unik**. Sebanyak 204 kemunculan URL lainnya belum melewati penyaringan teknis: gagal diambil, bukan HTML, kosong, atau teks kurang dari 100 kata. URL tersebut tetap tercatat dengan status teknisnya; ketiadaan teks tidak dianggap bukti untuk menolak isi halaman aslinya. Angka 464 bukan seluruh URL dalam manifest, melainkan URL utama yang sudah memiliki hasil percobaan scraping saat audit dimulai.

## Metode dan keputusan

Asisten LLM dalam sesi Codex membaca judul serta bagian awal, tengah, dan akhir setiap kandidat. Teks lebih panjang dan HTML lokal diperiksa untuk kasus yang diragukan, termasuk navigasi artikel bersambung, abstrak jurnal, isi yang hilang, dan kontaminasi halaman lain. Tidak ada panggilan Gemini API, SerpApi, atau scraping jaringan baru.

| Batch sumber kandidat | Accepted | Excluded | Needs extraction review |
| --- | ---: | ---: | ---: |
| articles_main_03 | 69 | 8 | 9 |
| articles_main_04 | 39 | 5 | 9 |
| **Total artikel baru** | **108** | **13** | **18** |

Keputusan diterapkan ke `data/manual/article_review.csv`. Semua **995 keputusan sebelumnya dipertahankan identik**. File aktif kini berisi **1.134 ID unik**: 882 accepted, 171 excluded, dan 81 needs_extraction_review. Hitungan ini adalah akumulasi keputusan artikel lintas batch, bukan jumlah baris model-ready.

Dasar keputusan mencakup bahasa, jenis halaman, kecukupan isi, serta keutuhan/kebersihan ekstraksi. Status sitasi, label target, dan tingkat otoritas sumber tidak ditampilkan sebagai bahan penilaian. Artikel promosi/rekomendasi produk dan tulisan pengguna diterima jika memiliki pembahasan mandiri. Nama produk, istilah teknis, kode, serta referensi Inggris diperbolehkan jika narasi utamanya Indonesia.

Contoh keputusan:

| Contoh halaman | Keputusan | Bukti/alasan |
| --- | --- | --- |
| Entri Inbox by Gmail pada Wikipedia Indonesia | accepted | Narasi layanan dan riwayatnya berbahasa Indonesia; nama fitur dan referensi Inggris diperbolehkan. |
| Tutorial kuis Google Forms pada Kumparan | accepted | Kiriman pengguna berupa panduan mandiri dengan langkah-langkah, bukan percakapan forum. |
| Makalah perbandingan MYOB/Accurate pada landing jurnal | excluded | Salinan hanya memuat abstrak, metadata, referensi, atau akses PDF; tidak memuat badan makalah. |
| Entri BNI pada Wikipedia Melayu | excluded | Narasi utamanya Melayu, terlihat dari kata seperti syarikat, perkhidmatan, dan ditubuhkan. |
| Produk cetirizine K24Klik | excluded | Fungsi halaman berupa transaksi produk dengan harga, stok, dan keranjang. |
| Panduan RAM Lampungpro | needs_extraction_review | Teks berhenti sebelum langkah yang dijanjikan; HTML memiliki tiga halaman yang belum tergabung. |
| Daftar bunga Pegadaian | needs_extraction_review | Bagian daftar bunga dan beberapa jenis gadai terdapat di HTML tetapi hilang dari teks ekstraksi. |
| Berita Liputan6 yang diperiksa | needs_extraction_review | Ekstraksi juga memuat blok Sixtainability/daftar berita lintas topik di luar badan artikel. |

Penahanan ekstraksi bukan pengecualian permanen. Artikel dapat ditinjau kembali setelah badan teks dipulihkan dan fitur dibangun ulang. Pada audit ini ekstraktor tidak diubah; keputusan merujuk pada hash teks yang benar-benar diperiksa. Artikel accepted juga belum otomatis menjadikan semua pasangan kuerinya model-ready: pemeriksaan label, percobaan, pencocokan URL, duplikasi pasangan, dan fitur semantik tetap berlaku.

Dari 18 kasus ekstraksi baru, tiga berupa artikel bersambung yang belum lengkap, tujuh kehilangan isi utama atau salah memilih judul, dan delapan tercampur konten lain/spam. Pengelompokan ini untuk tindak lanjut perbaikan, bukan kriteria baru di luar rubrik.

## Pembangunan ulang

Batch 3 dan 4 dibangun ulang dari HTML lokal dengan embedding lokal. Tujuh artikel yang sama juga muncul pada batch lama: satu pada batch 1 dan enam pada batch 2. Kedua batch lama diselaraskan menggunakan hasil ekstraksi tersimpan yang diverifikasi terhadap teks, metadata, dan fitur pada `articles.csv`, serta hash HTML saat digunakan kembali. Ekstraktor produksi tidak diubah. BM25 dan keanggotaan dataset dihitung ulang mengikuti korpus eligible; embedding menggunakan cache lokal.

Label biner tetap memakai proporsi sitasi **≥0,5**, minimal dua percobaan valid, dan aturan kelayakan pasangan sebelumnya. Artikel yang dikecualikan atau ditahan tetap tercatat di `dataset.csv`/`articles.csv`; hanya penyertaannya dalam `model_ready.csv` yang disesuaikan.

Hasil akhir setelah keempat batch dibangun ulang dan divalidasi:

| Batch | Pasangan utama | Model-ready sebelum audit | Masuk | Ditarik | Model-ready akhir |
| --- | ---: | ---: | ---: | ---: | ---: |
| articles_main_01 | 325 | 186 | 0 | 0 | 186 |
| articles_main_02 | 2.165 | 885 | 0 | 2 | 883 |
| articles_main_03 | 379 | 134 | 32 | 1 | 165 |
| articles_main_04 | 92 | 26 | 14 | 5 | 35 |
| **Total** | **2.961** | **1.231** | **46** | **8** | **1.269** |

Pertambahan bersih dari awal audit adalah **38 pasangan**. Angka sementara 1.271 yang terlihat setelah batch 3–4 selesai berkurang dua ketika batch 2 diselaraskan. Kedua pasangan tersebut memakai artikel `article_94230be31d9e9444a83dedef` tentang daftar bunga Pegadaian, yang kehilangan bagian daftar/tabel utama pada ekstraksinya. Satu pasangan artikel yang sama pada batch 4 juga ditahan. Delapan pasangan yang ditarik secara keseluruhan berasal dari enam ID artikel dengan keputusan `needs_extraction_review`; catatannya tetap ada dalam dataset utama.

Model-ready adalah **subset dari 2.961 pasangan unik pada dataset utama**, sehingga jumlah kedua berkas tidak dijumlahkan. Sebanyak **1.692 pasangan** belum model-ready. Dataset tambahan Gemini-only tetap berjumlah 1.429 pasangan dan tidak dimasukkan ke model utama.

| Domain | Pasangan model-ready |
| --- | ---: |
| Kesehatan | 568 |
| Keuangan | 466 |
| Teknologi | 235 |
| **Total** | **1.269** |

Model-ready mencakup 1.165 ID artikel dan 339 ID kueri, dengan 955 label 0 dan 314 label 1. Sebanyak 938 pasangan menggunakan artikel berstatus accepted, sedangkan 331 menggunakan artikel eligible_auto dari korpus lama di luar cakupan audit terbaru. Tidak ada lagi status `needs_language_review` atau `needs_page_type_review` pada dataset utama keempat batch. Status teknis gagal, pengecualian, penahanan ekstraksi, serta hambatan pada pasangan tetap dipertahankan.

Validasi memastikan semua 995 keputusan lama identik, 146 salinan lintas batch untuk 139 ID yang dinilai memiliki hash teks yang sesuai, semua label/proporsi/jumlah sitasi tetap sama, dan perubahan keanggotaan model-ready dapat ditelusuri ke keputusan baru. Sembilan pasangan dari artikel accepted baru masih tertahan oleh `url_matching_uncertain` (tiga pada batch 3 dan enam pada batch 4).

Dataset siap pakai tetap tersimpan per batch:

- [model_ready batch 1](../data/processed/articles_main_01/model_ready.csv)
- [model_ready batch 2](../data/processed/articles_main_02/model_ready.csv)
- [model_ready batch 3](../data/processed/articles_main_03/model_ready.csv)
- [model_ready batch 4](../data/processed/articles_main_04/model_ready.csv)

Satu baris merupakan pasangan kueri–artikel. Artikel yang muncul untuk kueri berbeda tidak dihapus hanya karena `article_id` sama. Status model-ready menunjukkan kelayakan pasangan; fitur yang memang tidak tersedia, seperti usia publikasi, tetap membutuhkan penanganan nilai hilang pada tahap pemodelan.

Pada hasil akhir, 334 baris model-ready memiliki fitur kosong: usia publikasi pada 328 baris dan rerata panjang paragraf pada 11 baris, beririsan lima baris. Nilai hilang tetap dipertahankan untuk penanganan dalam pipeline pelatihan; parameter imputasi dipelajari dari fold pelatihan.

## Berkas audit

- [Keputusan aktif](../data/manual/article_review.csv): status, bahasa, alasan, reviewer, dan waktu review yang dibaca builder.
- [Audit 139 artikel](../outputs/article_verification_20261010/review_audit.csv): URL, judul, status sebelum/sesudah, alasan, cuplikan awal/tengah/akhir, hash teks, lokasi HTML, reviewer, dan versi rubrik.
- `outputs/article_verification_20261010/candidates.json`: snapshot teks kandidat tanpa label sitasi.
- `outputs/article_verification_20261010/technical_blockers.json`: URL yang belum memiliki teks memadai untuk penilaian substantif.
- `outputs/article_verification_20261010/html_inspection.txt`: pemeriksaan elemen HTML lokal pada kasus meragukan.
- `outputs/article_verification_20261010/article_review_before.csv`: backup 995 keputusan lama.
- `outputs/article_verification_20261010/merge_report.json`: validasi cakupan dan penerapan keputusan.
- [Validasi hasil akhir](../outputs/article_verification_20261010/validation_report.json): hitungan per batch, domain, label, pemeriksaan keutuhan keputusan, dan kesamaan observasi sitasi.
- [Perubahan keanggotaan model-ready](../outputs/article_verification_20261010/membership_changes.csv): 46 pasangan masuk dan delapan pasangan ditarik, berikut alasan per baris.
- `outputs/article_verification_20261010/cached_build_report.json`: sumber/hash ekstraksi yang digunakan kembali pada batch 1–2; log finalnya `build_01_cached.log` dan `build_02_cached.log`. Log batch 3–4 adalah `build_03.log` dan `build_04.log`.

Keputusan merupakan **seleksi kelayakan berbantuan LLM**, dapat dikoreksi melalui review manusia. Audit ini tidak mengukur kesepakatan antarpenilai, tidak menjamin setiap kata telah dibaca, tidak memeriksa kebenaran semua klaim medis/keuangan/teknis, dan tidak menyatakan seluruh korpus historis telah diperiksa dalam sesi ini.
