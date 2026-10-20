# Verifikasi artikel utama lintas batch — 11 Oktober 2026

## Cakupan dan metode

Sebanyak **833 ID artikel baru** dinilai menggunakan [rubrik kelayakan artikel](RUBRIK_SELEKSI_ARTIKEL.md), versi `article_eligibility_20261006_v1`. Cakupan meliputi artikel Google Top 10, termasuk irisan Google–Gemini, yang sudah memiliki hasil unduh sukses dan teks minimal 100 kata tetapi belum memiliki keputusan di tabel manual. Sebanyak 815 kandidat berasal dari snapshot batch 1–5; 18 kandidat dari batch 6 ditambahkan ketika hasil build batch tersebut tersedia. Batch 4 tidak memiliki kandidat baru pada snapshot ini. Artikel Gemini-only tidak dicari sebagai kandidat tersendiri, tetapi keputusan ikut diterapkan jika artikel yang sama digunakan di dataset tambahan.

Audit juga mencakup artikel lama berstatus `eligible_auto`, sehingga bukan hanya mengosongkan antrean bahasa/jenis halaman. Status awal 833 kandidat terdiri dari 582 eligible_auto, 105 needs_language_review, 83 needs_page_type_review, 38 not_article, dan 25 non_indonesian otomatis.

Asisten LLM memeriksa judul dan cuplikan awal, tengah, akhir setiap kandidat. Sebanyak **85 kasus** diperiksa lebih dalam menggunakan teks panjang dan HTML lokal. Materi penilaian tidak menampilkan label sitasi. Bahasa, jenis halaman, kecukupan isi, serta keutuhan/kebersihan ekstraksi menjadi dasar keputusan; popularitas, tingkat otoritas, dan jumlah sitasi tidak menjadi kriteria diterima.

Lima versi teks yang berbeda lintas batch diperiksa tersendiri. Salinan beranda/alat tetap dikecualikan; salinan artikel dengan kontaminasi testimoni tetap ditahan; salinan gagal HTTP tanpa teks tetap tidak layak secara teknis. Penerapan keputusan memeriksa hash **868 salinan** dan mempertahankan **1.280 keputusan sebelumnya secara identik**.

## Hasil keputusan

**655 accepted, 111 excluded, dan 67 needs_extraction_review.**

| Asal kandidat | Accepted | Excluded | Needs extraction review |
| --- | ---: | ---: | ---: |
| main_01 | 86 | 10 | 4 |
| main_02 | 184 | 39 | 23 |
| main_03 | 50 | 9 | 6 |
| main_05 | 319 | 53 | 32 |
| main_06 | 16 | 0 | 2 |

Tabel [article_review.csv](../data/manual/article_review.csv) kini berisi **2.113 ID unik**: 1.640 accepted, 309 excluded, dan 164 needs_extraction_review. Angka keputusan artikel berbeda dari jumlah pasangan kueri–artikel dalam model-ready.

Contoh penerapan:

| Contoh | Keputusan | Alasan |
| --- | --- | --- |
| Panduan Google Form pada Scribd | accepted | Teks langkah kuis, identitas, pilihan ganda, dan esai tersedia sampai akhir; dokumen dinilai dari isi. |
| Artikel Alodokter dengan istilah medis | accepted | Narasi utama Indonesia; istilah medis/referensi Inggris diperbolehkan. |
| Katalog produk Lazada | excluded | Antarmuka belanja/produk tanpa artikel mandiri. |
| Agregasi banyak posting Lemon8 | excluded | Berisi kumpulan unggahan, bukan satu badan artikel. |
| Artikel KUR/HP yang berhenti pada halaman pertama | needs_extraction_review | Daftar atau kelanjutan pembahasan belum terambil. |
| Penjelasan herpes RS Royal Progress | needs_extraction_review | Badan artikel terduplikasi dua kali dan dapat membiaskan fitur panjang. |
| Artikel pinjol Dolpheen dan perhitungan pajak Pegadaian pada batch 6 | needs_extraction_review | Daftar/tabel inti hilang; pada Dolpheen juga tercampur testimoni layanan. |

Keputusan accepted tidak memvalidasi kebenaran setiap klaim. Penahanan ekstraksi bersifat sementara dan dapat diperbarui setelah teks diperbaiki serta ditinjau ulang.

## Hasil pembangunan ulang

Batch 1, 2, 3, 5, dan 6 dibangun ulang; batch 4 tidak berubah karena tidak menggunakan artikel dengan keputusan baru. Build menggunakan ekstraksi tersimpan yang cocok dengan teks, metadata, fitur, dan hash HTML lokal. Embedding tersedia dipakai kembali; embedding yang belum tersedia dihitung lokal. BM25 dihitung ulang karena himpunan artikel eligible berubah. Memoisasi tokenisasi diuji menghasilkan skor BM25 yang sama dengan implementasi awal. Tidak ada kode ekstraktor produksi yang diubah.

| Batch | Pasangan utama | Model-ready sebelum | Masuk | Ditarik | Model-ready sesudah |
| --- | ---: | ---: | ---: | ---: | ---: |
| main_01 | 325 | 186 | 0 | 5 | 181 |
| main_02 | 2.165 | 882 | 3 | 37 | 848 |
| main_03 | 571 | 202 | 16 | 3 | 215 |
| main_04 | 390 | 131 | 0 | 0 | 131 |
| main_05 | 777 | 260 | 117 | 37 | 340 |
| main_06 | 44 | 7 | 8 | 1 | 14 |
| **Total** | **4.272** | **1.668** | **144** | **83** | **1.729** |

Jumlah akhir **1.729 pasangan siap model**, mencakup **1.591 ID artikel** dan **432 ID kueri**. Ada 144 pasangan masuk dan 83 ditarik, dengan perubahan bersih **+61 pasangan**. Penarikan berasal dari artikel yang setelah ditinjau ternyata nonartikel atau memerlukan perbaikan teks, bukan pengubahan label sitasi.

| Domain | Pasangan model-ready |
| --- | ---: |
| kesehatan | 763 |
| keuangan | 625 |
| teknologi | 341 |

Distribusi label adalah **1.378 label 0** dan **351 label 1**. Model-ready merupakan subset dari **4.272 pasangan utama**; masih ada **2.543 pasangan belum siap**. Dataset tambahan berisi 1.544 pasangan Gemini-only dan tetap terpisah.

## Yang masih perlu ditindaklanjuti

Pada snapshot batch 1–6, **tidak ada artikel utama dengan unduh sukses dan teks minimal 100 kata yang belum memiliki keputusan**. Status needs_language_review/needs_page_type_review pada pasangan utama tersisa **0**. Seluruh model-ready kini menggunakan status artikel `accepted`.

Masih ada **173 pasangan dari 164 ID artikel** yang berstatus needs_extraction_review, termasuk keputusan lama. Daftarnya tersedia dalam [antrean perbaikan ekstraksi](../outputs/article_verification_20261011/needs_extraction_review.csv). Kolom `is_new_decision` membedakan kasus audit ini dari kasus lama. Ini bukan antrean persetujuan kosong: salinan teksnya perlu diperbaiki sebelum diterima.

Kegagalan unduh, teks kosong/pendek, dan ketidakpastian pencocokan URL tetap disimpan. Sebanyak 14 pasangan dari artikel accepted baru masih tertahan oleh pemeriksaan pasangan. Status accepted pada artikel tidak otomatis meloloskan pasangan yang label/URL-nya belum pasti. `technical_blockers.json` memuat 1.945 kemunculan lintas batch yang tidak masuk penyaringan isi saat snapshot; angka ini bukan jumlah artikel unik dan tidak boleh dijumlahkan dengan hitungan pasangan.

Ada 446 baris model-ready dengan setidaknya satu fitur kosong. Rinciannya: mean_paragraph_word_count: 16, publication_age_days: 434. Angka per fitur dapat beririsan. Nilai yang tidak tersedia tidak direkayasa; penanganan nilai hilang tetap dilakukan dalam pipeline pelatihan.

## Validasi dan lokasi hasil

Validasi memeriksa keputusan lama tetap identik, teks sesuai hash yang ditinjau, keputusan baru tersalurkan ke setiap salinan, ID pasangan serta jumlah percobaan/sitasi/proporsi/label tetap sama, dan model-ready tepat sama dengan subset `ready_for_model=True` pada dataset utama. Semua perubahan keanggotaan dapat ditelusuri ke keputusan baru. Pemisahan Google Top 10 dan Gemini-only tetap konsisten.

- [Keputusan aktif dan alasan](../data/manual/article_review.csv).
- [Audit 833 artikel: URL, judul, alasan, cuplikan, hash, reviewer](../outputs/article_verification_20261011/review_audit.csv).
- [Perubahan keanggotaan model-ready](../outputs/article_verification_20261011/membership_changes.csv).
- [Validasi akhir](../outputs/article_verification_20261011/validation_report.json) dan [sensus akhir](../outputs/article_verification_20261011/final_census.json).
- `data/processed/articles_main_01/` sampai `articles_main_06/`: dataset.csv, model_ready.csv, articles.csv, dan ekspor tambahan terbaru. Tidak dibuat salinan gabungan baru.
- `outputs/article_verification_20261011/`: backup sebelum perubahan, snapshot kandidat, versi teks berbeda, log build, dan skrip audit lokal.

Proses menggunakan **0 panggilan Gemini dan 0 pencarian SerpApi**, tanpa scraping baru. Penilaian merupakan seleksi berbantuan LLM dalam sesi Codex, bukan verifikasi manusia independen atau pengukuran kesepakatan antarpenilai. Pemeriksaan cuplikan tidak menjamin setiap kata telah dibaca. Cakupan dibatasi snapshot ini; hasil crawling/build yang ditambahkan setelahnya perlu masuk putaran verifikasi berikutnya.
