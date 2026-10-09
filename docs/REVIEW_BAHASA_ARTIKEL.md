# Hasil review bahasa artikel

Tanggal review bahasa awal: 21 September 2026. Tindak lanjut manual: 22 September 2026.

## Pembaruan setelah review manual peneliti (22 September 2026)

Seluruh **50 artikel yang diteruskan dari review bahasa ke review jenis halaman** sudah diperiksa oleh peneliti melalui `articel_review.txt`. Sebanyak **48 dinilai sebagai artikel/panduan informasional**, sementara halaman daftar harga emas (`article_2a90fc20f81db6c645489e65`) dan formulir JHT dengan informasi terbatas (`article_3c0669fbd180c284a0b4ede7`) dikecualikan sesuai deskripsi peneliti dan rubrik.

Keputusan aktif menjadi **47 accepted, 2 excluded, dan 1 needs_extraction_review**. Satu artikel yang jenis halamannya diterima, `article_3412cae508eb697d3d877a65` ([panduan JDIH Sukoharjo](https://jdih.sukoharjokab.go.id/berita/detail/empat-cara-mencairkan-bpjs-ketenagakerjaan-online)), masih tertahan: salinan HTML dan teks yang tersimpan berhenti di tengah langkah pertama JMO. Diperlukan salinan lengkap sebelum teks ini dapat dipakai model. Ini hambatan kelengkapan salinan, bukan penolakan terhadap penilaian jenis halaman peneliti.

Keputusan aktif ada di [article_review.csv](../data/manual/article_review.csv). [Audit review manual](../data/manual/article_page_type_review_20260922.csv) menyimpan catatan asli, keputusan peneliti dan status yang diterapkan; [berkas masukan asli](../data/manual/article_page_type_review_20260922_source.txt) juga disimpan. Reviewer jenis halaman dicatat `manual_user_review`; tanggal 2026-09-22 adalah tanggal penerapan/review yang dilaporkan, bukan waktu pemeriksaan setiap halaman yang diketahui secara terpisah.

Masih ada **79 artikel lain / 87 pasangan utama** yang berstatus `needs_page_type_review` di luar daftar 50 artikel kiriman ini. Gunakan filter status tersebut pada dataset utama hasil build terbaru untuk melihat antrean aktif. Seluruh 50 ID kiriman peneliti sudah memiliki keputusan lanjutan; tidak perlu meninjau ulang daftar yang sama dari awal.

Build ulang selesai: batch pertama **133 -> 153** dan batch kedua **116 -> 146** pasangan model-ready. Total menjadi **299**, bertambah 50 pasangan dari 47 artikel. Semua label sitasi dan pasangan siap sebelumnya dipertahankan. Sebanyak 244 baris lengkap seluruh prediktor, sedangkan 55 baris tetap membutuhkan penanganan fitur kosong pada prapemrosesan. Hasil dan validasi terperinci ada di [PROGRESS.md](PROGRESS.md).

**Bagian review bahasa dan tabel 101 artikel di bawah merupakan riwayat keadaan 21 September.** Filter `page_type` pada audit bahasa lama menunjukkan antrean awal, bukan antrean aktif saat ini. Untuk status terkini gunakan keputusan aktif dan `articles.csv`/`dataset.csv` hasil build terbaru. Review 50 artikel ini tidak mencakup kandidat jenis halaman lain di dataset. Tiga masalah ekstraksi dari review bahasa sebelumnya tetap tertahan, ditambah satu kasus JDIH di atas.

## Riwayat review bahasa awal

Review ini dilakukan oleh **asisten LLM**, atas permintaan peneliti, pada **101 artikel unik / 106 pasangan query-artikel** yang berstatus `needs_language_review` dan muncul pada Google Top-10 di batch `articles_main_01` atau `articles_main_02`. Antrean mencakup Google-only dan irisan Google/Gemini. Artikel yang hanya berasal dari Gemini tidak dipilih untuk review ini. Keputusan pada tingkat artikel juga berlaku jika artikel yang sama muncul dalam pasangan tambahan.

## Hasil bahasa dan status artikel

| Hasil | Artikel unik | Pasangan utama |
| --- | ---: | ---: |
| Bahasa Indonesia; diterima setelah hambatan bahasa diselesaikan | 43 | 45 |
| Bahasa Indonesia; masih perlu review jenis/kelengkapan halaman | 50 | 53 |
| Bahasa Indonesia; masih perlu pemeriksaan ekstraksi | 3 | 3 |
| Didominasi Inggris; excluded | 5 | 5 |
| **Total** | **101** | **106** |

Sebanyak **96 artikel** memenuhi kriteria bahasa Indonesia dan **5 artikel** tidak memenuhinya. Bahasa yang sudah jelas tidak otomatis membuat artikel masuk model_ready: kelayakan halaman, kualitas ekstraksi, kepastian label, dan duplikasi tetap diperiksa oleh build.

Kedua dataset sudah dibangun ulang. Model-ready batch pertama menjadi **133 pasangan** (sebelumnya 110), dan batch kedua **116 pasangan** (sebelumnya 94). Totalnya **249 pasangan**, meningkat 45 baris. Seluruh label dan hitungan sitasi tetap sama; keputusan review hanya memengaruhi kelayakan artikel dan fitur yang dihitung dari korpus eligible. Sebanyak 210 baris lengkap seluruh fitur dan 39 masih memerlukan penanganan nilai kosong saat prapemrosesan. Tidak ada lagi status `needs_language_review` pada dataset utama setelah review ini.

## Rubrik dan cara peninjauan

Narasi utama dinilai dari kalimat penjelas, bukan dari kode bahasa HTML. Nama produk, singkatan, istilah teknis/medis, kode, dan judul referensi Inggris diperbolehkan bila penjelasan utamanya tetap Indonesia. Angka 70–80% yang pernah disebut dalam percakapan tidak digunakan sebagai hasil pengukuran atau ambang numerik pada review ini; keputusan memakai rubrik kualitatif yang sama untuk setiap artikel.

Peninjauan membaca judul serta cuplikan bagian awal, tengah, dan akhir dari **setiap** teks hasil ekstraksi. Kasus tidak wajar diperiksa lebih jauh; untuk dua artikel Hello Sehat, paragraf pada HTML lokal juga dibaca. Ini adalah peninjauan berbasis sampel bagian teks, bukan klaim telah membaca setiap kata seluruh artikel. Alasan dan cuplikan bukti disimpan agar peneliti dapat mengaudit keputusan. `confidence=high_qualitative` menyatakan keyakinan kualitatif asisten pada bahasa; bukan probabilitas terkalibrasi atau hasil validasi manusia.

Metadata `lang=en` atau `zxx` tidak mengalahkan narasi Indonesia yang terlihat. Banyak artikel masuk antrean karena konflik metadata tersebut. Lima halaman ASUS berisi deskripsi produk berbahasa Inggris yang dominan; label/tombol Indonesia tidak cukup untuk menyatakan badan halaman berbahasa Indonesia.

Status `accepted` hanya diberikan pada artikel yang bahasa Indonesianya telah ditinjau dan sebelumnya sudah memenuhi pemeriksaan jenis halaman otomatis (`page_type=article` dengan ekstraksi badan yang terkonfirmasi), tanpa masalah isi ekstraksi yang terlihat pada peninjauan. Kandidat dengan jenis halaman `article_candidate` atau `unknown` tetap memerlukan review jenis halaman. Halaman harga emas yang didominasi tabel juga ditahan untuk pemeriksaan cakupan.

Review bahasa tidak menilai kebenaran informasi kesehatan/keuangan, akurasi tanggal, reputasi penerbit, atau relevansi setiap pasangan query-artikel. Label sitasi tidak menjadi dasar keputusan bahasa. Review ini termasuk **penilaian berbantuan LLM / LLM-as-a-judge**, dengan peneliti sebagai pemeriksa ulang; bukan verifikasi manusia independen.

## Kasus yang perlu diprioritaskan untuk pemeriksaan ulang

- [Minum Paracetamol untuk Ibu Hamil, Ini Aturannya](<https://hellosehat.com/kehamilan/kandungan/prenatal/paracetamol-untuk-ibu-hamil/>) — `article_023391f0ff028742e0744894`: HTML memuat narasi Indonesia tentang paracetamol saat hamil; teks hasil ekstraksi justru seluruhnya daftar pustaka Inggris. Bahasa telah diverifikasi; ekstraksi harus diperiksa sebelum artikel dapat diterima.
- [Harga Emas ANTAM Harian \| Emas Antam Indonesia](<https://emasantam.id/harga-emas-antam-harian/>) — `article_2a90fc20f81db6c645489e65`: Keterangan dan narasi pendamping harga emas berbahasa Indonesia; halaman didominasi tabel harga sehingga jenis halamannya perlu diperiksa. Bahasa telah diverifikasi; keputusan jenis/kelengkapan halaman masih menunggu review.
- [Cara Cek NIK Sudah Terdaftar di NPWP, ini Langkahnya](<https://cobisnis.com/cara-cek-nik-sudah-terdaftar-di-npwp-ini-langkahnya/>) — `article_7645f726765d12492fc9fcf4`: Panduan NIK/NPWP jelas berbahasa Indonesia tetapi teks ekstraksi juga memuat tautan promosi unduhan berbahasa Inggris yang tidak terkait. Bahasa telah diverifikasi; ekstraksi harus diperiksa sebelum artikel dapat diterima.
- [Ragam Bahan Tradisional untuk Obat Alami Batuk Kering dan Berdahak](<https://hellosehat.com/pernapasan/pilek/obat-batuk-alami/>) — `article_f104caafcfb7d7340553bf74`: HTML memuat pembahasan obat batuk alami dalam bahasa Indonesia; ekstraksi saat ini hanya berisi daftar referensi Inggris. Bahasa telah diverifikasi; ekstraksi harus diperiksa sebelum artikel dapat diterima.

Dua halaman Hello Sehat tidak dinyatakan sebagai artikel Inggris hanya karena daftar pustakanya berbahasa Inggris. Paragraf Indonesia tersedia pada HTML asli, sedangkan kolom teks hasil ekstraksi saat ini hanya berisi referensi. Karena itu, bahasa dicatat `id`, tetapi statusnya `needs_extraction_review` agar teks tersebut belum masuk model.

## File yang digunakan

- [article_review.csv](../data/manual/article_review.csv): keputusan aktif yang dibaca builder. Sebanyak 101 keputusan ditambahkan; 17 keputusan sebelumnya dipertahankan.
- [article_language_review_20260921.csv](../data/manual/article_language_review_20260921.csv): catatan review asisten, URL, alasan, hasil bahasa, status lanjutan, cuplikan bukti, hash teks, dan lokasi HTML asal. Ini catatan audit; mengubah file ini saja tidak mengubah dataset hasil build.
- [Cadangan sebelum review](../outputs/review_backups/language_review_20260921/): CSV keputusan lama dan seluruh keluaran dua batch sebelum review bahasa.

Untuk memeriksa hasil, buka CSV audit dan filter `followup_type`: `page_type` untuk review jenis halaman dan `extraction` untuk perbaikan/pemeriksaan teks. Jika ingin mengaudit keputusan bahasa yang sudah diterima, filter `status=accepted`. Lima keputusan `excluded` juga tetap dapat ditinjau ulang.

Catat koreksi pada **article_review.csv** sesuai `article_id`; gunakan identitas penilai dan tanggal review milikmu. Jangan menambahkan baris kedua untuk ID yang sama. Status `needs_extraction_review` menahan kelayakan artikel sampai masalah ekstraksi diperiksa; menggantinya menjadi accepted tanpa memperbaiki teks tidak menyelesaikan masalah tersebut. Jika kelayakan jenis halaman masih belum diputuskan, pertahankan `needs_page_type_review` meskipun `language=id`.

Setelah keputusan berubah, bangun ulang batch terkait:

```powershell
python src/build_article_dataset.py --config configs/article_features.json --with-embeddings
python src/build_article_dataset.py --config configs/article_features_02.json --with-embeddings
```

Kedua perintah memakai HTML dan cache lokal; tidak memakai token Gemini atau kredit SerpApi. Keputusan review mengikuti ID artikel, sehingga satu artikel tidak perlu dinilai lagi untuk setiap query.

## Daftar keputusan bahasa pada 21 September 2026 (riwayat)

| No. | Artikel | Bahasa | Status pada 21 September | Tindak lanjut saat itu |
| --- | --- | --- | --- | --- |
| 1 | [Rekomendasi Sunscreen untuk Usia 50 Tahun ke Atas, Cegah Penuaan Dini](<https://www.zalora.co.id/blog/kecantikan/beauty-recommendation/rekomendasi-sunscreen-untuk-usia-50-tahun-ke-atas/>) | id | `accepted` | Tidak ada dari review bahasa |
| 2 | [Minum Paracetamol untuk Ibu Hamil, Ini Aturannya](<https://hellosehat.com/kehamilan/kandungan/prenatal/paracetamol-untuk-ibu-hamil/>) | id | `needs_extraction_review` | extraction |
| 3 | [9 Manfaat Kunyit untuk Kesehatan Tubuh](<https://www.alodokter.com/kebenaran-manfaat-kunyit-ditinjau-dari-segi-medis>) | id | `needs_page_type_review` | page_type |
| 4 | [7 Sunscreen untuk Ibu Hamil yang Aman dan Bagus](<https://www.alodokter.com/7-sunscreen-untuk-ibu-hamil-yang-aman-dan-bagus>) | id | `needs_page_type_review` | page_type |
| 5 | [6 Faktor Utama Penularan HIV yang Jarang Disadari](<https://dp3appkb.bantulkab.go.id/news/6-faktor-utama-penularan-hiv-yang-jarang-disadari>) | id | `needs_page_type_review` | page_type |
| 6 | [Obat Jantung Alami dari Tumbuhan yang Mudah Didapatkan](<https://primayahospital.com/jantung/obat-jantung-alami-dari-tumbuhan/>) | id | `accepted` | Tidak ada dari review bahasa |
| 7 | [Pengertian Campak](<https://www.alodokter.com/campak>) | id | `needs_page_type_review` | page_type |
| 8 | [Ms Office: Pengertian dan Jenis-jenisnya](<https://course-net.com/blog/ms-office-pengertian-dan-jenis-jenisnya/>) | id | `accepted` | Tidak ada dari review bahasa |
| 9 | [Penyebab Penyakit Kista pada Wanita yang Perlu Diketahui](<https://www.alodokter.com/penyebab-penyakit-kista-pada-wanita-yang-perlu-diketahui>) | id | `needs_page_type_review` | page_type |
| 10 | [13 Rekomendasi Merek Vitamin untuk Ibu Hamil yang Bagus](<https://www.farmaku.com/artikel/rekomendasi-merk-vitamin-untuk-ibu-hamil-yang-bagus/>) | id | `accepted` | Tidak ada dari review bahasa |
| 11 | [Batuk Kering, Inilah 6 Langkah Mudah untuk Mengatasinya](<https://www.alodokter.com/sekarang-juga-lenyapkan-batuk-kering-secepatnya>) | id | `needs_page_type_review` | page_type |
| 12 | [Bantuan Subsidi Upah Meluncur Lagi, Ini Cara Cek Penerimanya](<https://indonesiabaik.id/infografis/bantuan-subsidi-upah-meluncur-lagi-ini-cara-cek-penerimanya>) | id | `needs_page_type_review` | page_type |
| 13 | [Cara Cek Penerima BSU BPJS Ketenagakerjaan 2025](<https://empower.amartha.com/blog/cara-cek-penerima-bsu/>) | id | `accepted` | Tidak ada dari review bahasa |
| 14 | [Harga Emas ANTAM Harian \| Emas Antam Indonesia](<https://emasantam.id/harga-emas-antam-harian/>) | id | `needs_page_type_review` | page_type |
| 15 | [Memory (RAM) - 16GB RAM｜Laptop For Students｜ASUS Indonesia](<https://www.asus.com/id/laptops/for-students/all-series/filter?Spec=196>) | en | `excluded` | Tidak ada dari review bahasa |
| 16 | [JDIH Kabupaten Sukoharjo](<https://jdih.sukoharjokab.go.id/berita/detail/empat-cara-mencairkan-bpjs-ketenagakerjaan-online>) | id | `needs_page_type_review` | page_type |
| 17 | [Hati Hati, Ada Aplikasi VPN Gratis Palsu Yang Sebarkan Malware Klopatra!](<https://winpoin.com/hati-hati-ada-aplikasi-vpn-gratis-palsu-yang-sebarkan-malware-klopatra/>) | id | `accepted` | Tidak ada dari review bahasa |
| 18 | [Gejala HIV pada Wanita yang Tidak Boleh Diabaikan](<https://www.alodokter.com/gejala-hiv-pada-wanita-yang-umum-ditemui>) | id | `needs_page_type_review` | page_type |
| 19 | [Pengembangan Saldo JHT - Tetap Sejahtera di Hari Tua](<https://www.bpjsketenagakerjaan.go.id/tetap-sejahtera.html>) | id | `needs_page_type_review` | page_type |
| 20 | [Artikel](<https://papuapegunungan.kpu.go.id/blog/read/683_demokrasi-parlementer-pengertian-ciri-aspek-prinsip-dan-penerapannya-di-era-modern>) | id | `accepted` | Tidak ada dari review bahasa |
| 21 | [Daftar Makanan yang Mengandung Vitamin C Tinggi](<https://www.alodokter.com/daftar-makanan-yang-mengandung-vitamin-c-tinggi>) | id | `needs_page_type_review` | page_type |
| 22 | [Harga Laptop Asus RAM 16GB](<https://www.arenalaptop.com/list/harga-laptop-asus-ram-16gb/>) | id | `accepted` | Tidak ada dari review bahasa |
| 23 | [Rekomendasi Sunscreen yang Aman untuk Ibu Hamil](<https://www.zalora.co.id/blog/parenting/product-review/rekomendasi-sunscreen-yang-aman-untuk-ibu-hamil/>) | id | `accepted` | Tidak ada dari review bahasa |
| 24 | [Manfaat Vitamin C untuk Ibu Hamil, Bisa Mencegah Anemia Loh ! \| Klinik SehatQ](<https://www.kliniksehatq.com/articles/4>) | id | `needs_page_type_review` | page_type |
| 25 | [9 Obat Batuk Tablet yang Paling Ampuh di Apotek](<https://www.farmaku.com/artikel/obat-batuk-tablet-yang-paling-ampuh-di-apotek/>) | id | `accepted` | Tidak ada dari review bahasa |
| 26 | [Pengobatan Campak](<https://www.alodokter.com/campak/pengobatan>) | id | `needs_page_type_review` | page_type |
| 27 | [Pentingnya Menguasai Microsoft Office di Era Digital](<https://binus.ac.id/malang/2020/04/pentingnya-menguasai-microsoft-office/>) | id | `accepted` | Tidak ada dari review bahasa |
| 28 | [Berapa Gaji Minimal yang Tidak Kena Pajak?](<https://www.jstax.co.id/berapa-gaji-minimal-yang-tidak-kena-pajak>) | id | `accepted` | Tidak ada dari review bahasa |
| 29 | [Microsoft Excel: Pengertian, Sejarah, Fungsi, Manfaat, dan Kelebihan](<https://fikti.umsu.ac.id/microsoft-excel-pengertian-sejarah-fungsi-manfaat-dan-kelebihan/>) | id | `accepted` | Tidak ada dari review bahasa |
| 30 | [Kamu Harus Tahu! 5 Skill Microsoft Office yang Harus Dikuasai Dalam Dunia Kerja](<https://grahakarya.com/blog/kamu-harus-tahu-5-skill-microsoft-office-yang-harus-dikuasai-dalam-dunia-kerja>) | id | `needs_page_type_review` | page_type |
| 31 | [Price - Rp 18.000.000 - Rp 20.000.000｜Laptop For Home｜ASUS Indonesia](<https://www.asus.com/id/laptops/for-home/all-series/filter?Spec=16059>) | en | `excluded` | Tidak ada dari review bahasa |
| 32 | [KUR BRI 2026: Bunga 6%, Plafon Rp500 Juta, Cicilan Rp9,6 Juta](<https://skorlife.com/blog/pinjol-kta/tabel-kur-bri/>) | id | `accepted` | Tidak ada dari review bahasa |
| 33 | [Apakah Kista Berbahaya? Ketahui Jawabannya di Sini](<https://www.alodokter.com/apakah-kista-berbahaya-ketahui-jawabannya-di-sini>) | id | `needs_page_type_review` | page_type |
| 34 | [Inilah Syarat Membuat NPWP Pribadi](<https://ayopajak.com/inilah-syarat-membuat-npwp-pribadi/>) | id | `accepted` | Tidak ada dari review bahasa |
| 35 | [KUR BRI Pinjaman Rp50 Juta Agustus 2026, Segini Cicilannya](<https://www.metrotvnews.com/read/NgxCayaV-kur-bri-pinjaman-rp50-juta-agustus-2026-segini-cicilannya>) | id | `accepted` | Tidak ada dari review bahasa |
| 36 | [Bagaimana Cek NPWP Online? Berikut Informasinya!](<https://ayopajak.com/cek-npwp-online/>) | id | `accepted` | Tidak ada dari review bahasa |
| 37 | [Mengenal Aplikasi di Microsoft 365 dan Fungsinya untuk Bisnis](<https://indibiz.co.id/artikel/mengenal-aplikasi-di-microsoft-365-dan-fungsinya-untuk-bisnis>) | id | `accepted` | Tidak ada dari review bahasa |
| 38 | [Cara Pembayaran Iuran](<https://www.bpjsketenagakerjaan.go.id/jmo/pembayaran-iuran.html>) | id | `needs_page_type_review` | page_type |
| 39 | [Pengertian Dan 5 Fungsi VPN (Virtual Private Network)](<https://www.dinamika.ac.id/forums/pengertian-dan-fungsi-vpn/>) | id | `accepted` | Tidak ada dari review bahasa |
| 40 | [7 Ciri-ciri Jantung Bermasalah yang Tak Boleh Disepelekan](<https://www.aia-financial.co.id/id/health-and-wellness/aia-content-club/physical-wellness/7-Ciri-ciri-Jantung-Bermasalah-yang-Tak-Boleh-Disepelekan>) | id | `accepted` | Tidak ada dari review bahasa |
| 41 | [Memory (RAM) - 16GB RAM｜Laptop For Home｜ASUS Indonesia](<https://www.asus.com/id/laptops/for-home/all-series/filter?Spec=37>) | en | `excluded` | Tidak ada dari review bahasa |
| 42 | [20 Obat Batuk Kering Paling Ampuh di Apotek dan Harganya](<https://www.k24klik.com/blog/obat-batuk-kering/>) | id | `accepted` | Tidak ada dari review bahasa |
| 43 | [6 Vitamin C untuk Ibu Hamil agar Kehamilan Tetap Sehat](<https://www.alodokter.com/vitamin-c-untuk-ibu-hamil-agar-kehamilan-tetap-sehat>) | id | `needs_page_type_review` | page_type |
| 44 | [Price - Rp 12.000.000 - Rp 15.000.000｜Laptop For Home｜ASUS Indonesia](<https://www.asus.com/id/laptops/for-home/all-series/filter?Spec=16057>) | en | `excluded` | Tidak ada dari review bahasa |
| 45 | [Obat Batuk yang Aman Bagi Penderita Diabetes](<https://www.konimexstore.com/artikel/view/judul/Obat+Batuk+yang+Aman+Bagi+Penderita+Diabetes?srsltid=AfmBOooShaADyLRq0WVAxwyBqW9OzzLJ2Cg-fpxj07uVUrj-Cg0fucXA>) | id | `needs_page_type_review` | page_type |
| 46 | [Vitamin C](<https://www.alodokter.com/vitamin-c>) | id | `needs_page_type_review` | page_type |
| 47 | [Alternatif Microsoft Office Terbaik: Gratis dan Nyaman untuk Produktivitas Anda](<https://poltekbangplg.ac.id/alternatif-microsoft-office-terbaik-gratis-dan-nyaman-untuk-produktivitas-anda/>) | id | `needs_page_type_review` | page_type |
| 48 | [Cara Cek NIK Sudah Terdaftar di NPWP, ini Langkahnya](<https://cobisnis.com/cara-cek-nik-sudah-terdaftar-di-npwp-ini-langkahnya/>) | id | `needs_extraction_review` | extraction |
| 49 | [Cara Cek BSU BPJS Ketenagakerjaan Sudah Masuk atau Belum di JMO](<https://blog.itera.ac.id/cara-cek-bsu-bpjs-ketenagakerjaan/>) | id | `accepted` | Tidak ada dari review bahasa |
| 50 | [Tak Perlu Resign, Pekerja Aktif Bisa Klaim JHT 10%](<https://indonesiabaik.id/infografis/tak-perlu-resign-pekerja-aktif-bisa-klaim-jht-10>) | id | `needs_page_type_review` | page_type |
| 51 | [Wajib Pajak Badan Curup Simak Kiat Agar NPWP Valid](<https://pajak.go.id/en/node/73173>) | id | `needs_page_type_review` | page_type |
| 52 | [Diskon 50 persen Iuran BPJS Ketenagakerjaan Ini Dia Syaratnya](<https://www.bpjsketenagakerjaan.go.id/artikel/18931/artikel--diskon-50-persen-iuran-bpjs-ketenagakerjaan-ini-dia-syaratnya.bpjs>) | id | `needs_page_type_review` | page_type |
| 53 | [Pantangan Campak pada Dewasa, Ini Makanan dan Aktivitas yang Harus Dijauhi](<https://www.alodokter.com/pantangan-campak-pada-dewasa-ini-makanan-dan-aktivitas-yang-harus-dijauhi>) | id | `needs_page_type_review` | page_type |
| 54 | [Cara Cek BSU Sudah Cair atau Belum, Ini Langkah Mudahnya](<https://daftarsekolah.spmb.teknokrat.ac.id/2026/02/cara-cek-bsu-sudah-cair-atau-belum-ini-langkah-mudahnya/>) | id | `needs_page_type_review` | page_type |
| 55 | [Paracetamol untuk Ibu Menyusui, Ini Tips Aman Mengonsumsinya](<https://www.alodokter.com/paracetamol-untuk-ibu-menyusui-ini-tips-aman-mengonsumsinya>) | id | `needs_page_type_review` | page_type |
| 56 | [Mengapa IHSG Anjlok? Ini Penyebab Utama yang Membuat Investor Panik di Bursa Saham](<https://daftarsekolah.spmb.teknokrat.ac.id/2026/06/mengapa-ihsg-anjlok-ini-penyebab-utama-yang-membuat-investor-panik-di-bursa-saham/>) | id | `needs_page_type_review` | page_type |
| 57 | [13 Sunscreen Terbaik untuk Berbagai Jenis Kulit](<https://www.alodokter.com/5-rekomendasi-sunscreen-terbaik-untuk-melindungi-kulit>) | id | `needs_page_type_review` | page_type |
| 58 | [AIDS: Apa Gejala, Bagaiana Mencegah dan Mengobati?](<https://primayahospital.com/penyakit-dalam/aids/>) | id | `accepted` | Tidak ada dari review bahasa |
| 59 | [5 Fungsi VPN dan Cara Kerjanya](<https://herza.id/blog/5-fungsi-vpn-dan-cara-kerjanya/>) | id | `accepted` | Tidak ada dari review bahasa |
| 60 | [Ruam Campak, Kenali Ciri-Ciri dan Tips untuk Mengatasinya](<https://www.alodokter.com/ruam-campak-kenali-ciri-ciri-dan-tips-untuk-mengatasinya>) | id | `needs_page_type_review` | page_type |
| 61 | [Kenali Ciri-Ciri Hamil 16 Minggu yang Sehat](<https://www.alodokter.com/kenali-ciri-ciri-hamil-16-minggu-yang-sehat>) | id | `needs_page_type_review` | page_type |
| 62 | [Risiko ADHD dan Autisme pada Konsumsi Paracetamol saat Hamil](<https://www.alomedika.com/konsumsi-paracetamol-saat-hamil-dan-risiko-adhd-pada-anak>) | id | `accepted` | Tidak ada dari review bahasa |
| 63 | [Besaran Iuran BPJS Ketenagakerjaan untuk Peserta Bukan Penerima Upah BPU](<https://www.bpjsketenagakerjaan.go.id/artikel/18963/artikel-besaran-iuran-bpjs-ketenagakerjaan-untuk-peserta-bukan-penerima-upah-bpu.bpjs>) | id | `needs_page_type_review` | page_type |
| 64 | [Jasa Konsultan Pajak \| Tax Consultant - Enforce A](<https://enforcea.com/Blog/punya-npwp-belum-tentu-bayar-pajak>) | id | `needs_page_type_review` | page_type |
| 65 | [Campak pada Orang Dewasa. Gejala, Risiko Komplikasi, dan Kapan Harus ke Dokter](<https://rsroemani.com/artikel/campak-pada-orang-dewasa-gejala-risiko-komplikasi-dan-kapan-harus-ke-dokter>) | id | `needs_page_type_review` | page_type |
| 66 | [Bayar Iuran Rp16.800 per Bulan, Pekerja Informal Terlindungi BPJAMSOSTEK](<https://www.bpjsketenagakerjaan.go.id/berita/28039/Bayar-Iuran-Rp16.800-per-Bulan,-Pekerja-Informal-Terlindungi-BPJAMSOSTEK>) | id | `needs_page_type_review` | page_type |
| 67 | [8 Sunblock Wajah Terbaik dan Ampuh Menghalau Sinar UV](<https://www.alodokter.com/sunblock-wajah-terbaik-dan-ampuh-menghalau-sinar-uv>) | id | `needs_page_type_review` | page_type |
| 68 | [Waspadai Bahaya Penyakit Kista yang Merugikan Kesehatan Tubuh](<https://www.alodokter.com/mewaspadai-bahaya-penyakit-kista-yang-merugikan-kesehatan-tubuh>) | id | `needs_page_type_review` | page_type |
| 69 | [Penyakit Addison](<https://www.alodokter.com/penyakit-addison>) | id | `needs_page_type_review` | page_type |
| 70 | [Ini Dia Daftar Bank yang Masuk dalam Klaster Usaha BUMN](<https://suksescpns.id/ini-dia-daftar-bank-yang-masuk-dalam-klaster-usaha-bumn/>) | id | `accepted` | Tidak ada dari review bahasa |
| 71 | [Berapa Besaran Iuran JHT, JKK, JKM, JP dan JKP?](<https://www.bpjsketenagakerjaan.go.id/artikel/18913/artikel-berapa-besaran-iuran-jht,-jkk,-jkm,-jp-dan-jkp>) | id | `needs_page_type_review` | page_type |
| 72 | [15 Rekomendasi Sunscreen Terbaik, Nyaman untuk Semua Jenis Kulit](<https://www.farmaku.com/artikel/rekomendasi-sunscreen-terbaik-nyaman-untuk-semua-jenis-kulit/>) | id | `accepted` | Tidak ada dari review bahasa |
| 73 | [Pengertian HIV dan AIDS](<https://www.alodokter.com/hiv-aids>) | id | `needs_page_type_review` | page_type |
| 74 | [Harga Laptop Asus, September 2026](<https://bigrit.com/laptop-asus/?srsltid=AfmBOop8Qf6eXweq8BjY8672waHpYht33wWpIywvtKhYKYIXe5Ggp_pV&v=b80bb7740288>) | id | `accepted` | Tidak ada dari review bahasa |
| 75 | [8 Rekomendasi Sunscreen Terbaik Sesuai Jenis Kulit, Harga Mulai 30 Ribuan-100 Ribuan!](<https://www.beautyhaul.com/blog/8-rekomendasi-sunscreen-terbaik-sesuai-jenis-kulit-harga-mulai-30-ribuan-100-ribuan?srsltid=AfmBOop83GGZiB2AuuqYanwBy-um4crhXE3804tRJbellZooBOIZdc8V>) | id | `accepted` | Tidak ada dari review bahasa |
| 76 | [Harga Laptop Asus, September 2026](<https://bigrit.com/laptop-asus/?srsltid=AfmBOoqFoPHChy1eXtQ_qRYA4zMSa2N4d3GPd426UEjXmHAinEEpV5zh&v=b80bb7740288>) | id | `accepted` | Tidak ada dari review bahasa |
| 77 | [Harga Laptop Asus RAM 4GB](<https://www.arenalaptop.com/list/harga-laptop-asus-ram-4gb/>) | id | `accepted` | Tidak ada dari review bahasa |
| 78 | [Penggunaan pada Kehamilan dan Ibu Menyusui](<https://www.alomedika.com/obat/analgesik/analgesik-non-narkotik-antipiretik/paracetamol/kehamilan-menyusui>) | id | `accepted` | Tidak ada dari review bahasa |
| 79 | [Halo, Apa yang dapat kami bantu?](<https://support.online-pajak.com/en/hc/syarat-membuat-npwp/>) | id | `accepted` | Tidak ada dari review bahasa |
| 80 | [Memahami Ciri-Ciri Penyakit HIV Pada Pria](<https://primayahospital.com/penyakit/penyakit-hiv-pada-pria/>) | id | `accepted` | Tidak ada dari review bahasa |
| 81 | [10 Harga Laptop Asus Core i5 Terbaik Sesuai Kebutuhan Anda](<https://www.kanakomputer.com/harga-laptop-asus-core-i5/>) | id | `accepted` | Tidak ada dari review bahasa |
| 82 | [8 Rekomendasi Sunscreen Terbaik Sesuai Jenis Kulit, Harga Mulai 30 Ribuan-100 Ribuan!](<https://www.beautyhaul.com/blog/8-rekomendasi-sunscreen-terbaik-sesuai-jenis-kulit-harga-mulai-30-ribuan-100-ribuan?srsltid=AfmBOorzpEzKo0uY_s8QRKd8JmQDCaJZkBa8C-_avOBTUHHGub0fAsP3>) | id | `accepted` | Tidak ada dari review bahasa |
| 83 | [7 Obat Sakit Kepala untuk Ibu Menyusui di Apotek](<https://www.farmaku.com/artikel/obat-sakit-kepala-untuk-ibu-menyusui-di-apotek/>) | id | `accepted` | Tidak ada dari review bahasa |
| 84 | [Bolehkah Minum Paracetamol Saat Hamil? Ini Jawabannya](<https://www.alodokter.com/amankah-mengonsumsi-paracetamol-saat-hamil>) | id | `needs_page_type_review` | page_type |
| 85 | [Sunscreen untuk Flek Hitam Terbaik, Jangan Salah Pilih!](<https://www.wardahbeauty.com/id/news/sunscreen-untuk-flek-hitam>) | id | `accepted` | Tidak ada dari review bahasa |
| 86 | [KPU KAB-YALIMO - Apa Itu Republik? Pengertian, Ciri-Ciri dan Contoh Negaranya](<https://kab-yalimo.kpu.go.id/blog/read/8410_apa-itu-republik-pengertian-ciri-ciri-dan-contoh-negaranya>) | id | `accepted` | Tidak ada dari review bahasa |
| 87 | [Pinjaman KUR BRI 2026: Plafon Rp50 Juta, Bunga 6%, Syarat &#038; Cara Ajukan](<https://skorlife.com/blog/pinjol-kta/apa-itu-kur-dan-cara-mengajukannya/>) | id | `accepted` | Tidak ada dari review bahasa |
| 88 | [Ciri-Ciri Sakit Jantung yang Harus Diwaspadai](<https://www.alodokter.com/kenali-ciri-ciri-sakit-jantung>) | id | `needs_page_type_review` | page_type |
| 89 | [Cara Cek BLT Subsidi Gaji di bsu.bpjsketenagakerjaan.go.id, Diperluas ke 1,6 Juta Penerima](<https://www.bpjsketenagakerjaan.go.id/berita/27779/Cara-Cek-BLT-Subsidi-Gaji-di-bsu.bpjsketenagakerjaan.go.id,-Diperluas-ke-1,6-Juta-Penerima>) | id | `needs_page_type_review` | page_type |
| 90 | [Gejala Awal Penyakit Jantung dan Pencegahannya](<https://primayahospital.com/jantung/gejala-awal-penyakit-jantung/>) | id | `accepted` | Tidak ada dari review bahasa |
| 91 | [Microsoft Excel: Definisi, Fungsi, dan Rumus Penting](<https://pasartrainer.com/blog/microsoft-excel-definisi-fungsi-dan-rumus-penting>) | id | `needs_page_type_review` | page_type |
| 92 | [Saat Anak terkena Campak, Harus Apa?](<https://primayahospital.com/anak/campak/>) | id | `accepted` | Tidak ada dari review bahasa |
| 93 | [Penyebab HIV dan AIDS](<https://www.alodokter.com/hiv-aids/penyebab>) | id | `needs_page_type_review` | page_type |
| 94 | [Ragam Bahan Tradisional untuk Obat Alami Batuk Kering dan Berdahak](<https://hellosehat.com/pernapasan/pilek/obat-batuk-alami/>) | id | `needs_extraction_review` | extraction |
| 95 | [Kista](<https://www.alodokter.com/kista>) | id | `needs_page_type_review` | page_type |
| 96 | [10 Sunscreen Terbaik untuk Flek Hitam agar Wajah Cerah](<https://www.alodokter.com/10-sunscreen-terbaik-untuk-flek-hitam-agar-wajah-cerah>) | id | `needs_page_type_review` | page_type |
| 97 | [Cara Cek Penerima BSU 2025 Secara Online: Mudah Dan Cepat!](<https://www.dinamika.ac.id/forums/cek-bsu-2025-online/>) | id | `accepted` | Tidak ada dari review bahasa |
| 98 | [Pengertian Penyakit Jantung Koroner](<https://www.alodokter.com/penyakit-jantung-koroner>) | id | `needs_page_type_review` | page_type |
| 99 | [ASUS Store Indonesia Laptop Collection](<https://www.asus.com/id/store/laptops/>) | en | `excluded` | Tidak ada dari review bahasa |
| 100 | [7 Obat Batuk Dewasa Paling Ampuh](<https://www.alodokter.com/obat-batuk-dewasa-paling-ampuh>) | id | `needs_page_type_review` | page_type |
| 101 | [5 Gejala HIV pada Pria yang Perlu Diwaspadai](<https://www.alodokter.com/5-gejala-hiv-pada-pria-yang-perlu-diwaspadai>) | id | `needs_page_type_review` | page_type |
