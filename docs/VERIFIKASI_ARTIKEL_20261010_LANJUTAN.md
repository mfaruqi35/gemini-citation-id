# Verifikasi lanjutan artikel batch 4 — 10 Oktober 2026

## Cakupan dan metode

Audit ini melanjutkan [review sebelumnya](VERIFIKASI_ARTIKEL_20261010.md) setelah scraping dan build terbaru. Batch `articles_main_04` sudah mencoba seluruh **390 URL Google Top 10** yang tersedia untuk 45 kuerinya, termasuk irisan dengan sitasi Gemini. Percobaan scraping tidak selalu berhasil menghasilkan artikel yang dapat dinilai.

Dari 390 URL tersebut, **212 memiliki teks yang melewati penyaringan isi**. Sebanyak 66 sudah memiliki keputusan sebelumnya dan **146 ID artikel baru** dinilai dalam audit ini. Sebanyak 178 URL lainnya belum memiliki hasil yang memadai untuk penilaian isi: 100 `not_extracted`, 58 `too_short`, 16 `extraction_empty`, dan empat `not_article` otomatis dengan teks di bawah ambang. Status teknis tersebut tetap disimpan; ketiadaan teks tidak dianggap bukti untuk menolak isi halaman aslinya.

Penilaian memakai [rubrik kelayakan artikel](RUBRIK_SELEKSI_ARTIKEL.md) versi `article_eligibility_20261006_v1`: bahasa, jenis halaman, kecukupan isi, dan keutuhan/kebersihan ekstraksi. Asisten LLM membaca judul serta cuplikan awal, tengah, dan akhir setiap kandidat. Kasus meragukan diperiksa melalui teks lebih panjang dan HTML lokal. Label sitasi serta tingkat otoritas sumber tidak digunakan untuk menentukan keputusan.

## Hasil keputusan artikel

| Keputusan baru | Artikel unik |
| --- | ---: |
| `accepted` | 103 |
| `excluded` | 27 |
| `needs_extraction_review` | 16 |
| **Total** | **146** |

Keputusan dan alasan per artikel sudah diterapkan pada [article_review.csv](../data/manual/article_review.csv). Semua **1.134 keputusan lama dipertahankan identik**. Tabel aktif kini berisi **1.280 ID unik**: 985 accepted, 198 excluded, dan 97 needs_extraction_review. Angka ini merupakan akumulasi keputusan artikel lintas batch, bukan jumlah baris model-ready.

Contoh penerapan rubrik:

| Contoh | Keputusan | Dasar |
| --- | --- | --- |
| Daftar harga laptop ASUS RAM 8 GB pada Kana Komputer | accepted | Memiliki penjelasan pilihan perangkat dan pertimbangan pembelian dalam bahasa Indonesia; nama spesifikasi Inggris bukan narasi asing dominan. |
| Tulisan GERD dan serangan jantung pada komunitas Alomedika | accepted | Satu tulisan penjelasan yang berdiri sendiri dengan 0 balasan; fungsi dan isi diperiksa, bukan hanya kategori URL komunitas. |
| Panduan pinjaman Pegadaian | accepted | Jawaban inti FAQ dan langkah perpanjangan terambil sampai penutup. Pengantar umum singkat yang tidak ikut terambil tidak menghilangkan pembahasan inti. |
| Halaman Cetirgi 10 mg di Halodoc | excluded | Halaman satu produk dengan harga per strip dan rekomendasi barang lain, bukan artikel mandiri. |
| Panduan menghapus Chrome dengan bahasa Melayu | excluded | Narasi memakai nyahpasang, peranti, tetapan, dan penyemak imbas; bahasa utama bukan Indonesia. |
| Persyaratan rekening BNI pada IDXChannel | needs_extraction_review | Teks berhenti sebelum daftar persyaratan; HTML memiliki tiga halaman dan ekstraksi turut menyerap banyak kartu berita. |
| Profil Bank Mandiri pada Flip | needs_extraction_review | Nama jenis kredit, daftar layanan digital, dan sebagian cara pengaduan tersedia di HTML tetapi hilang dari teks. |
| Posting panduan Chrome pada Lemon8 | needs_extraction_review | Badan posting ada pada HTML, tetapi ekstraksi justru memuat komentar dan banyak posting rekomendasi lintas topik. |

Enam belas kasus penahanan terdiri dari delapan artikel bersambung yang belum lengkap, tiga kasus kehilangan butir penting atau judul yang benar, serta lima kasus konten bercampur/berulang. Status ini bukan pengecualian permanen; teks perlu dipulihkan lalu ditinjau kembali. Audit ini tidak mengubah ekstraktor atau memaksakan artikel yang rusak masuk model.

## Penyelarasan dataset

Keputusan berlaku pada artikel yang sama di berbagai pasangan kueri. Enam kandidat juga ditemukan pada batch sebelumnya: dua pada batch 1 dan empat pada batch 2. Karena itu batch 1, 2, dan 4 dibangun ulang; batch 3 tidak memiliki kandidat yang terdampak.

Terdapat **152 kemunculan artikel lintas batch** untuk 146 ID baru. Sebanyak 151 memakai versi teks yang sama dengan kandidat batch 4. Satu salinan artikel scan barcode pada batch 2 memiliki teks rekomendasi berbeda; salinan itu diperiksa tersendiri dan menunjukkan masalah kontaminasi yang sama. Kedua versi ditahan, dengan hash serta cuplikan masing-masing disimpan dalam audit.

Pembangunan ulang menggunakan ekstraksi tersimpan yang diperiksa terhadap teks, metadata, fitur, dan hash HTML lokal. BM25 dihitung ulang sesuai korpus eligible; memoization tokenisasi hanya menghindari pekerjaan berulang tanpa mengganti rumus. Embedding menggunakan model/cache lokal. Tidak ada perubahan kode produksi, pengumpulan URL baru, maupun panggilan Gemini API atau SerpApi.

Ambang label tetap proporsi sitasi **≥0,5**, dengan minimal dua percobaan valid dan ketentuan pasangan sebelumnya. Artikel yang dikecualikan atau ditahan tetap ada di `articles.csv` dan dataset utama untuk audit. `model_ready.csv` adalah subset `dataset.csv`, bukan dataset terpisah yang jumlahnya dijumlahkan.

## Hasil dataset setelah build dan validasi

Baseline berikut diambil setelah scraping terbaru, sehingga berbeda dari angka dalam audit sebelumnya pada tanggal yang sama.

| Batch | Pasangan utama | Model-ready sebelum | Masuk | Ditarik | Model-ready akhir |
| --- | ---: | ---: | ---: | ---: | ---: |
| main_01 | 325 | 186 | 0 | 0 | 186 |
| main_02 | 2.165 | 883 | 0 | 1 | 882 |
| main_03 | 379 | 165 | 0 | 0 | 165 |
| main_04 | 390 | 111 | 31 | 11 | 131 |
| **Total** | **3.259** | **1.345** | **31** | **12** | **1.364** |

Jumlah akhir adalah **1.364 pasangan kueri–artikel siap model**, mencakup **1.253 ID artikel** dan **353 ID kueri**. Pertambahan bersih audit adalah **19 pasangan**. Dua belas pasangan yang ditarik terdiri dari tiga yang artikelnya dikecualikan dan sembilan yang perlu perbaikan ekstraksi. Satu penarikan pada batch 2 menggunakan artikel scan barcode Liputan6 yang tercampur konten rekomendasi. Catatan sumber tetap tersedia.

| Domain | Pasangan model-ready |
| --- | ---: |
| Kesehatan | 611 |
| Keuangan | 499 |
| Teknologi | 254 |
| **Total** | **1.364** |

Distribusi labelnya 1.043 negatif dan 321 positif. Seluruh **3.259 ID pasangan utama unik**; **1.895 pasangan belum model-ready**. Dataset tambahan Gemini-only tetap berisi 1.429 pasangan dan tidak dimasukkan ke model utama. Dalam batch 4, seluruh 212 halaman yang lolos penyaringan isi telah memiliki keputusan: 152 accepted, 34 excluded, dan 26 needs_extraction_review. Dari 152 accepted tersebut, 21 pasangannya masih tertahan oleh `url_matching_uncertain`, termasuk 13 dari review baru ini.

Akumulasi `needs_extraction_review` pada keempat dataset utama adalah **102 pasangan dari 97 ID artikel**. Tidak ada lagi status `needs_language_review` atau `needs_page_type_review` pada dataset utama; hambatan teknis, ekstraksi, dan kepastian pasangan tetap ada. Sebanyak 1.036 pasangan model-ready memakai keputusan accepted dan 328 memakai eligible_auto dari korpus lama di luar audit ini.

Validasi membuktikan seluruh 1.134 keputusan lama tetap identik, hash 152 salinan artikel sesuai versi yang diperiksa, dan semua ID pasangan, jumlah percobaan valid, jumlah sitasi, proporsi sitasi, serta label tetap sama. Semua perubahan keanggotaan model-ready dapat ditelusuri ke keputusan baru. Fitur yang memang belum tersedia tidak diisi dengan nilai rekaan: 358 baris model-ready masih memiliki fitur kosong, yaitu usia publikasi pada 349 baris dan rerata panjang paragraf pada 14 baris, beririsan lima. Penanganan nilai hilang tetap diperlukan dalam pipeline pelatihan.

Hasil tersedia pada [model_ready batch 1](../data/processed/articles_main_01/model_ready.csv), [batch 2](../data/processed/articles_main_02/model_ready.csv), [batch 3](../data/processed/articles_main_03/model_ready.csv), dan [batch 4](../data/processed/articles_main_04/model_ready.csv). Tidak dibuat salinan gabungan baru pada audit ini.

## Berkas keputusan dan bukti

- [Keputusan aktif seluruh artikel](../data/manual/article_review.csv): status, bahasa, alasan, reviewer, dan waktu review.
- [Audit 146 artikel baru](../outputs/article_verification_20261010_followup/review_audit.csv): ID, URL, judul, status sebelum/sesudah, alasan, cuplikan, hash teks, dan lokasi HTML.
- [Antrean 16 perbaikan ekstraksi baru](../outputs/article_verification_20261010_followup/needs_extraction_review.csv).
- `outputs/article_verification_20261010_followup/candidates.json`: snapshot teks kandidat tanpa label sitasi.
- `outputs/article_verification_20261010_followup/technical_blockers.json`: 178 URL yang belum melewati penyaringan isi.
- `outputs/article_verification_20261010_followup/article_review_before.csv`: backup 1.134 keputusan sebelumnya.
- `outputs/article_verification_20261010_followup/html_inspection.txt`: pemeriksaan HTML pada kasus meragukan.
- `outputs/article_verification_20261010_followup/variant_review.json`: bukti penilaian versi lama artikel scan barcode.
- `outputs/article_verification_20261010_followup/cached_build_report.json`: sumber dan hash ekstraksi yang dipakai saat build; log berada di direktori yang sama.
- [Validasi hasil akhir](../outputs/article_verification_20261010_followup/validation_report.json): hitungan per batch, domain, label, dan kesamaan observasi sebelum/sesudah.
- [Perubahan keanggotaan model-ready](../outputs/article_verification_20261010_followup/membership_changes.csv): 31 pasangan masuk dan 12 ditarik, dengan alasan masing-masing.
- `outputs/article_verification_20261010_followup/final_census.json`: keunikan pasangan, status review pada model-ready, dan fitur yang belum tersedia.

Hasil merupakan **seleksi kelayakan berbantuan LLM**, bukan verifikasi manusia independen. Pemeriksaan tidak mencakup kebenaran seluruh klaim medis/keuangan/teknis, relevansi setiap pasangan kueri–artikel, atau pengukuran kesepakatan antarpenilai. Audit berbasis cuplikan tidak menjamin setiap kata telah dibaca. Cakupannya adalah artikel baru yang tersedia pada snapshot ini, bukan pernyataan bahwa seluruh korpus historis sudah ditinjau LLM.
