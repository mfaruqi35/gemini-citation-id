# Rubrik verifikasi kelayakan artikel oleh LLM

Versi: `article_eligibility_20261006_v1`. Dokumen ini merangkum kriteria yang telah dibahas dan digunakan dalam verifikasi artikel; tidak menggantikan rubrik seleksi kueri atau aturan pelabelan sitasi.

## Cakupan dan unit penilaian

Unit penilaian adalah artikel yang tersimpan, dikenali melalui `article_id` dan hash teks. Penilaian yang sama berlaku pada pasangan kueri yang menggunakan salinan artikel yang sama. Dataset model utama mencakup Google Top 10, termasuk irisan dengan sitasi Gemini. Gemini-only menjadi dataset tambahan.

Penyaringan teknis memeriksa keberhasilan unduh, ketersediaan teks, dan panjang minimal 100 kata menurut tokenisasi ekstraktor. Halaman gagal diunduh, teks kosong, dan teks di bawah ambang tetap memiliki status teknisnya; ketiadaan teks tidak dianggap keputusan substantif LLM atas halaman asli.

## Rubrik

| Aspek | Kriteria diterima | Dasar pengecualian atau penahanan |
| --- | --- | --- |
| Bahasa | Narasi utama Indonesia; nama produk, istilah teknis/medis, kode, dan referensi Inggris diperbolehkan. | Narasi utama berbahasa lain dikecualikan. Jika yang terambil hanya referensi/antarmuka, periksa ekstraksi sebelum menyimpulkan bahasa halaman asli. |
| Jenis halaman | Artikel, berita, penjelasan, panduan, atau dokumen informasional dengan pembahasan mandiri. | Katalog/kategori produk, halaman transaksi/produk, direktori profil, daftar unduhan, kalkulator/alat, percakapan forum, serta agregasi beberapa posting tanpa satu badan artikel dikecualikan. |
| Kecukupan isi | Teks melewati penyaringan minimal 100 kata dan memiliki penjelasan substantif. Daftar/tabel dapat menjadi bagian pendukung artikel. | Jumlah kata dari menu, spesifikasi produk, daftar tautan, referensi, atau kartu artikel lain tidak cukup untuk menyatakan halaman sebagai artikel. Abstrak dan metadata makalah saja tidak mewakili badan makalah lengkap. |
| Keutuhan dan kebersihan ekstraksi | Salinan memuat badan utama secara cukup utuh; cuplikan yang diperiksa berkesinambungan. | Hanya satu bagian dari artikel bersambung, kehilangan bagian utama/daftar/tabel teks, paragraf terputus, referensi saja, atau campuran signifikan isi halaman lain/spam ditahan untuk perbaikan. |

Penilaian jenis halaman mempertimbangkan fungsi halaman serta isi, bukan hostname saja. Artikel rekomendasi produk dapat diterima karena memiliki penjelasan mandiri. Keberadaan promosi penutup tidak otomatis menggugurkan artikel. Halaman katalog atau pemasaran produk tetap dibedakan dari artikel meskipun memiliki deskripsi atau FAQ. Kiriman pengguna yang berupa tulisan mandiri dapat diterima; halaman agregasi dan percakapan tidak otomatis dianggap artikel.

Tidak digunakan persentase numerik baru untuk menentukan dominasi bahasa. `domain_authority_level`, jumlah sitasi Gemini, label 0/1, dan kesesuaian hasil terhadap hipotesis tidak menjadi dasar penerimaan artikel. Pemeriksaan ini tidak memvalidasi kebenaran medis/keuangan/teknis setiap klaim, dan tidak menilai relevansi setiap pasangan kueri-artikel.

## Keputusan

- `accepted`: memenuhi aspek kelayakan dan tidak ditemukan masalah ekstraksi yang material pada bagian yang ditinjau.
- `excluded`: tersedia bukti bahwa bahasa atau jenis/kecukupan halaman tidak memenuhi cakupan artikel. Catatan sumber tetap disimpan.
- `needs_extraction_review`: artikel berpotensi layak, tetapi salinan teks belum memadai. Artikel belum masuk model sampai pemulihan ekstraksi dibuktikan dan keputusan diperbarui.

Penahanan ekstraksi bukan pengecualian permanen. Artikel yang diterima juga belum otomatis menjadi pasangan model-ready: kepastian pencocokan URL, kelayakan percobaan, label, duplikasi, serta fitur pasangan tetap diperiksa builder.

## Cara penilaian dan bukti

LLM membaca judul dan cuplikan awal, tengah, serta akhir teks setiap kandidat. Kasus meragukan diperiksa melalui bagian teks yang lebih panjang atau HTML lokal. Pemeriksaan berbasis cuplikan tidak diklaim sebagai pembacaan setiap kata atau jaminan tidak ada kesalahan tersisa. Tautan pagination dan perbedaan antara HTML dengan teks ekstraksi dicatat jika ditemukan.

Catatan audit menyimpan ID, URL, judul, status sebelum/sesudah, bahasa, jumlah kata, hash teks, lokasi HTML, alasan keputusan, cuplikan bukti, reviewer, tanggal, serta versi rubrik. Revisi selama audit disimpan terpisah dari keputusan sebelumnya. Label sitasi tidak ditampilkan pada materi penilaian; label hanya dibaca untuk validasi sebelum/sesudah build.

Keputusan aktif ada di `data/manual/article_review.csv`. Audit lanjutan crawling 6 Oktober tersimpan di `outputs/article_verification_20261006_followup/`; penerapan selesai pada 7 Oktober 2026. Penilaian dilakukan oleh asisten LLM dalam sesi Codex; tidak ada pengujian kesepakatan antarpenilai atau verifikasi manusia independen pada audit ini. Jangan menganggap seluruh korpus historis telah diperiksa LLM hanya karena audit ini selesai: cakupan setiap audit dicatat pada `scope.json`/`merge_report.json`.

## Contoh dari audit lanjutan

| Halaman | Keputusan | Alasan |
| --- | --- | --- |
| Tutorial penggunaan Psiphon pada Steemit | accepted | Pengantar Inggris singkat diikuti penjelasan dan langkah Indonesia hingga koneksi aktif; tulisan mandiri. |
| Halaman kategori laptop ASUS | excluded | Daftar perangkat dan spesifikasi; bukan artikel mandiri. |
| Halaman jurnal perbandingan sunscreen spray dan cream | excluded | HTML memuat abstrak, metadata, dan daftar pustaka; badan makalah tidak tersedia pada salinan. |
| Simulasi perhitungan gadai Pegadaian | needs_extraction_review | Teks berhenti sebelum tabel; HTML masih memuat simulasi lain yang hilang dari ekstraksi. |
| Artikel manfaat WhatsApp pada halaman kedua JPNN | needs_extraction_review | Salinan hanya berisi sebagian poin dan memiliki tautan halaman lanjutan. |

## Redaksi untuk prosedur penelitian

Kelayakan artikel diperiksa menggunakan rubrik yang mencakup bahasa, jenis halaman, kecukupan isi, dan keutuhan hasil ekstraksi. Setelah penyaringan teknis, LLM menilai judul serta bagian awal, tengah, dan akhir teks artikel. Hasil ekstraksi yang diragukan diperiksa lebih lanjut melalui salinan HTML. Keputusan disimpan bersama alasan dan cuplikan bukti, dengan status diterima, dikecualikan, atau ditahan untuk perbaikan ekstraksi. Status sitasi Gemini tidak digunakan dalam menentukan kelayakan artikel. Pemeriksaan ini merupakan seleksi berbantuan LLM dan tidak mencakup pengujian kesepakatan antarpenilai maupun pemeriksaan kebenaran setiap klaim dalam artikel.
