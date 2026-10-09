# Verifikasi artikel hasil crawling lanjutan

Penerapan dan validasi selesai pada **7 Oktober 2026**. Penilaian dimulai pada 6 Oktober, sehingga direktori audit tetap bernama `outputs/article_verification_20261006_followup/`.

## Cakupan dan cara pemeriksaan

Verifikasi memakai [rubrik seleksi artikel](RUBRIK_SELEKSI_ARTIKEL.md): bahasa utama Indonesia, jenis halaman informasional, kecukupan isi, serta keutuhan dan kebersihan ekstraksi. Kandidat diambil dari artikel baru pada dataset utama Google Top 10 sejak audit sebelumnya, ditambah antrean review bahasa/jenis halaman yang belum memiliki keputusan. Artikel harus sudah berhasil diunduh dan memiliki minimal 100 kata menurut ekstraktor agar dapat dinilai melalui teks.

Sebanyak **561 ID artikel unik** diperiksa melalui judul dan cuplikan awal, tengah, serta akhir. Kasus meragukan diperiksa menggunakan teks lebih panjang, HTML lokal, dan tautan halaman lanjutan. Ini merupakan penilaian LLM berbasis bukti tersimpan, bukan pembacaan setiap kata seluruh korpus atau pemeriksaan kebenaran setiap klaim. Label sitasi tidak menjadi masukan keputusan kelayakan. Tidak dilakukan Cohen's kappa maupun verifikasi manusia independen dalam audit ini.

Seluruh kandidat berasal dari `main_02` dan mewakili **571 pasangan utama**. Lima pasangan utama `main_01` memakai ID artikel yang sama sehingga ikut menerima keputusan global. Artikel yang hanya berada di luar Google Top 10 tidak dipilih sebagai kandidat. Keputusan global per ID juga dapat tercermin pada dataset tambahan yang memakai artikel tersebut.

Sebanyak **675 ID baru lainnya** masih memiliki hambatan teknis: 372 `not_extracted`, 191 `too_short`, 97 `extraction_empty`, serta 15 `not_article` dengan teks kurang dari 100 kata. Status tersebut dipertahankan; tidak diberikan keputusan isi tanpa teks yang cukup. Artikel lama berstatus `eligible_auto` di luar cakupan tidak ditinjau ulang pada audit ini.

## Hasil keputusan

| Status sebelum review | Diterima | Dikecualikan | Ditahan untuk ekstraksi | Total artikel |
| --- | ---: | ---: | ---: | ---: |
| `eligible_auto` | 249 | 13 | 48 | 310 |
| `needs_language_review` | 115 | 6 | 3 | 124 |
| `needs_page_type_review` | 55 | 46 | 0 | 101 |
| `non_indonesian` | 0 | 8 | 0 | 8 |
| `not_article` dengan teks cukup | 0 | 18 | 0 | 18 |
| **Total** | **419** | **91** | **51** | **561** |

Pengecualian mencakup katalog/produk, kalkulator, forum, agregasi posting, profil, abstrak jurnal tanpa badan makalah, dan narasi utama berbahasa lain. Artikel rekomendasi produk tetap dapat diterima bila memiliki pembahasan mandiri; promosi penutup tidak otomatis menggugurkannya.

Penahanan mencakup artikel bersambung yang baru tersimpan sebagian, teks tercampur berita lain, daftar atau tabel utama yang hilang, fragmen berulang, serta spam tidak terkait. Contohnya, ekstraksi simulasi gadai Pegadaian berhenti sebelum tabel, artikel JPNN hanya memuat satu halaman dari beberapa halaman, dan teks Segari tercampur promosi kaus sepak bola berbahasa Spanyol. Keputusan `needs_extraction_review` dapat diperbarui setelah salinan lengkap dan bersih tersedia.

Sebanyak **332 keputusan lama dipertahankan identik**. Penambahan 561 keputusan menghasilkan **893 ID unik** pada `data/manual/article_review.csv`; tidak ada duplikasi ID review. Alasan, bukti, hash teks, dan revisi selama pemeriksaan tersimpan dalam audit terpisah.

## Dampak pada dataset

Kedua batch dibangun ulang menggunakan HTML dan embedding lokal yang sudah tersedia:

| Batch | Pasangan utama | Model-ready sebelum | Masuk setelah review | Ditarik dari model-ready | Model-ready sesudah |
| --- | ---: | ---: | ---: | ---: | ---: |
| `articles_main_01` | 325 | 186 | 0 | 0 | 186 |
| `articles_main_02` | 2.165 | 775 | 172 | 62 | 885 |
| **Total** | **2.490** | **961** | **172** | **62** | **1.071** |

Pertambahan bersih adalah **110 pasangan query-artikel**. Sebanyak 62 pasangan ditarik karena 61 artikel yang sebelumnya lolos otomatis ternyata tidak layak atau belum utuh; satu artikel dapat dipakai oleh beberapa query. Angka 419 artikel diterima tidak sama dengan 419 baris baru, karena sebagian telah masuk model-ready sebelum audit.

Dari pasangan yang artikelnya diterima dalam audit ini, lima masih tertahan: empat memiliki `url_matching_uncertain` dan satu merupakan `duplicate_query_article`. Menerima isi artikel tidak menghapus hambatan tersebut.

Jumlah 1.071 merupakan penjumlahan dua berkas berikut, belum berkas pelatihan gabungan:

- `data/processed/articles_main_01/model_ready.csv`: **186 pasangan**.
- `data/processed/articles_main_02/model_ready.csv`: **885 pasangan**.

Terdapat **1.071 pasangan query-identitas artikel berbeda**, **993 ID artikel**, **986 URL identitas artikel**, dan **260 query** pada gabungan model-ready. Distribusinya adalah 826 label 0 dan 245 label 1; kesehatan 504, keuangan 396, teknologi 171.

Sebanyak **787 baris** lengkap seluruh 37 fitur dan **284 baris** masih memerlukan penanganan nilai hilang dalam pipeline model. Usia publikasi kosong pada 278 baris dan rerata panjang paragraf pada 11 baris, dengan lima baris beririsan. Nilai hilang tidak diisi dengan nilai rekaan. Imputasi, bila digunakan, tetap dipelajari hanya dari bagian latih.

## Yang masih tertahan

Tidak ada lagi `needs_language_review` atau `needs_page_type_review` pada dataset utama saat validasi ini. Namun, **1.419 pasangan utama belum model-ready**. Status artikelnya mencakup kegagalan unduh/ekstraksi, teks terlalu pendek, pengecualian, dan **57 pasangan** yang berstatus `needs_extraction_review` termasuk keputusan lama. Delapan pasangan dengan artikel `accepted`/`eligible_auto` juga belum siap karena pemeriksaan pasangan lainnya. Jadi, sisa pekerjaan tidak seluruhnya dapat diselesaikan melalui persetujuan review.

Di antara baris model-ready, 726 menggunakan artikel berstatus `accepted` dan 345 masih `eligible_auto`. `Accepted` juga mencakup keputusan historis, termasuk review manusia terdahulu. Jangan menyatakan semua artikel di korpus historis telah diverifikasi LLM melalui audit ini.

## Pemeriksaan hasil dan lokasi audit

Validasi memastikan ID seluruh pasangan gabungan, identitas query/artikel, label sitasi, `n_cited`, `n_valid`, dan proporsi sitasi tetap sama. Seluruh penarikan dari model-ready dapat ditelusuri ke keputusan audit. Definisi fitur tidak berubah. BM25 dan keluaran fitur dibangun ulang sesuai korpus eligible.

Hash teks seluruh 561 kandidat cocok dengan hasil build `main_02`. Dari 19 ID bersama dalam tabel artikel `main_01`, 15 memiliki teks identik dan empat diperiksa terpisah. Perbedaannya hanya keterangan jenis artikel pada Hello Sehat atau jumlah tayangan pada Pajak; isi utama tetap sama. Cuplikan serta selisih teks disimpan di `evidence_validation.json`.

| Berkas | Isi |
| --- | --- |
| `data/manual/article_review.csv` | Keputusan aktif yang dibaca builder. |
| `outputs/article_verification_20261006_followup/review_decisions.csv` | Seluruh 561 keputusan, alasan, cuplikan, hash, dan provenance. |
| `outputs/article_verification_20261006_followup/accepted.csv` | 419 artikel diterima pada audit ini. |
| `outputs/article_verification_20261006_followup/excluded.csv` | 91 artikel dikecualikan pada audit ini. |
| `outputs/article_verification_20261006_followup/needs_extraction_review.csv` | 51 artikel yang perlu pemulihan ekstraksi. |
| `outputs/article_verification_20261006_followup/technical_blockers.json` | 675 ID baru dengan hambatan teknis di luar review isi. |
| `outputs/article_verification_20261006_followup/build_validation.json` | Perbandingan sebelum/sesudah, jumlah baris, label, dan distribusi domain. |
| `outputs/article_verification_20261006_followup/evidence_validation.json` | Pemeriksaan hash, variasi teks lintas batch, fitur kosong, dan pasangan accepted yang tertahan. |
| `outputs/article_verification_20261006_followup/main_02_withdrawn_model_ready.csv` | 62 pasangan yang ditarik, beserta alasan review. |

Backup sebelum perubahan, manifest cakupan, log kedua build, bukti HTML/pagination, dan skrip validasi juga berada di direktori audit tersebut. **Tidak ada penggunaan kuota SerpApi atau Gemini API, dan tidak ada crawling baru pada verifikasi/build ini.**
