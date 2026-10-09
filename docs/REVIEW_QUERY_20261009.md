# Review kandidat query PAA — 9 Oktober 2026

Sebanyak **850 kandidat yang sebelumnya pending** telah dinilai menggunakan rubrik query yang sudah dipakai. Hasilnya **582 accepted dan 268 excluded**. Seluruh 582 query yang diterima belum terdapat pada manifest `main_01`, `main_02`, atau `main_03`, sehingga tersedia untuk pemilihan batch berikutnya.

| Domain | Ditinjau | Accepted | Excluded |
| --- | ---: | ---: | ---: |
| Kesehatan | 375 | 272 | 103 |
| Keuangan | 297 | 198 | 99 |
| Teknologi | 178 | 112 | 66 |
| **Total** | **850** | **582** | **268** |

## Berkas untuk melihat keputusan

- [Review lengkap 850 kandidat](../data/manual/query_expansion_20261009_review.csv): memuat teks pertanyaan, domain, `status`, `reason_code`, `reason`, reviewer, waktu review, serta asal PAA. Untuk duplikat tersedia `duplicate_of` dan `duplicate_query_text`.
- [582 query diterima dan belum terjadwal](../data/interim/query_expansion/query_expansion_01/accepted_unused_20261009.csv): snapshot kandidat yang dapat dipilih untuk batch berikutnya; mempertahankan kolom sumber yang digunakan pipeline.
- [Keputusan aktif seluruh ekspansi](../data/manual/query_expansion_01_decisions.csv): keputusan yang dibaca pipeline dan Notebook 05. Sebanyak 403 keputusan lama dipertahankan persis, termasuk alasan, reviewer, dan timestamp; total sekarang 1.253 keputusan.
- [Ringkasan audit](../outputs/query_review_20261009/summary.json): hitungan dan pemeriksaan integritas. Direktori audit juga menyimpan backup sebelum review, anotasi per domain, dan skrip penerapan lokal.

Buka berkas review lengkap di spreadsheet, lalu filter `domain` dan `status`. Kolom `reason` menjelaskan keputusan setiap baris. `Excluded` tetap disimpan untuk audit; pertanyaannya tidak dihapus dari sumber.

## Rubrik dan cara penilaian

Penilaian ini merupakan **seleksi query berbantuan LLM / LLM-as-a-judge**, menggunakan asisten Codex pada sesi ini dengan identitas reviewer `asisten_rubrik_v1_20261009`. Rubrik yang digunakan adalah rubrik query yang tercatat pada bagian “LLM-as-a-judge untuk seleksi query” di [PROGRESS.md](PROGRESS.md):

1. Teks asli PAA berbahasa Indonesia dan dapat dipahami.
2. Kebutuhan informasi relevan dengan domain kesehatan, keuangan, atau komputer dan elektronik yang ditetapkan.
3. Maksud pertanyaan dapat dipahami dari teksnya sendiri, tanpa menambahkan objek atau makna dari keyword asal.
4. Kebutuhan informasi dapat dibahas melalui artikel. Permintaan navigasi murni, seperti hanya menemukan alamat situs resmi, dikeluarkan dari cakupan ini.
5. Kebutuhan informasi belum terwakili oleh query yang telah dipakai atau kandidat lain yang dipertahankan.

Teks, domain, serta daftar query lama menjadi dasar penilaian. Hubungan dengan keyword Trends dan parent PAA tetap disimpan sebagai asal data; konteks itu tidak dipakai untuk melengkapi teks yang ambigu. Seluruh 850 baris memperoleh anotasi eksplisit oleh asisten, bukan keputusan otomatis berdasarkan kemiripan kata. Pemeriksaan kemiripan teks lokal digunakan sebagai bantuan audit tambahan; keputusan duplikasi tetap berdasarkan objek, kebutuhan informasi, dan batas yang disebutkan.

Pertanyaan umum, harga atau cicilan yang bergantung pada skenario, rekomendasi, serta premis yang mungkin keliru tidak otomatis ditolak. Artikel dapat menjelaskan variasi atau meluruskan premisnya. Perbedaan bermakna seperti jenis obat, populasi, perangkat, lembaga, anggaran, dan tanggal dapat menjadi kebutuhan tersendiri; perubahan redaksi atau panjang daftar saja tidak cukup. Keputusan tidak didasarkan pada perkiraan keberhasilan sitasi Gemini atau label artikel.

Penerimaan menunjukkan kelayakan sebagai **query penelitian**, bukan pembenaran klaim kesehatan/keuangan dalam pertanyaan, jaminan tersedianya artikel yang dapat di-scrape, atau keberhasilan pengumpulan respons. Teks PAA tidak disintesis, diterjemahkan, atau diperbaiki. ID model/snapshot dan parameter sampling penilai tidak diarsipkan, sehingga tidak dicantumkan sebagai informasi yang diketahui. Belum dilakukan penilaian independen atau pengukuran kesepakatan antarpenilai untuk review ini.

## Alasan penolakan

| Kategori | Jumlah |
| --- | ---: |
| Duplikasi kebutuhan informasi | 198 |
| Maksud ambigu atau objek tidak lengkap | 43 |
| Di luar domain atau cakupan pembahasan artikel | 27 |
| **Total** | **268** |

Contoh keputusan:

| Query asli | Status | Alasan ringkas |
| --- | --- | --- |
| Apa saja 3 fase penyakit campak? | accepted | Meminta penjelasan tahapan penyakit yang jelas. |
| Pinjam 10 juta di BRI angsuran berapa? | accepted | Lembaga dan nominal jelas; variasi tenor serta produk dapat dijelaskan dalam artikel. |
| Ctrl + T Excel untuk apa? | accepted | Tombol dan aplikasi disebutkan secara eksplisit. |
| Berapa lama campak akan sembuh? | excluded | Kebutuhan sama dengan “Berapa lama campak sembuh?” yang sudah terjadwal. |
| Ctrl + F11 untuk apa? | excluded | Aplikasi tidak disebutkan; fungsi tombol berbeda antar-aplikasi. |
| Bank Mandiri apa saja? | excluded | Tidak jelas apakah produk, cabang, atau entitas grup yang diminta. |
| Apa saja hotel Aman di Indonesia? | excluded | Tidak menyebut kebutuhan kesehatan maupun aspek keuangan; kemunculannya pada kedua domain tidak membuatnya relevan. |

## Status pool dan kelanjutan

Ekspor `accepted_new.csv` sekarang berisi **918 accepted**: 336 keputusan lama yang sudah digunakan dalam batch terdahulu dan 582 tambahan dari review ini. Karena itu, gunakan snapshot **`accepted_unused_20261009.csv`** untuk memilih query baru, bukan menganggap seluruh `accepted_new.csv` belum pernah dipakai.

Pool ekspansi kini memiliki 918 accepted dan 335 excluded, tanpa pending atau needs_review. Angka tersebut hanya mencakup sumber pada konfigurasi ekspansi yang aktif: PAA tersimpan serta respons Google `main_01` dan `main_02`. PAA dari respons `main_03` belum dimasukkan ke review ini.

Jika menghitung 381 query yang sudah terjadwal pada batch 1–3 bersama 582 cadangan ini, tersedia **963 query terjadwal atau diterima untuk penggunaan berikutnya**. Ini bukan jumlah query yang telah selesai dikumpulkan ataupun jumlah artikel model-ready.

582 query merupakan pool cadangan, belum snapshot atau konfigurasi pengumpulan `main_04`. Batch berikutnya dapat memilih sebagian sesuai kebutuhan domain dan kuota; jumlah yang diterima tidak sengaja disamakan antar-domain. Tidak perlu melakukan pencarian PAA tambahan untuk mulai memilih dari cadangan ini. Tujuh query batch 3 yang belum selesai menurut log terakhir tetap merupakan urusan recovery terpisah; seleksi ini tidak mengulangnya.

Tidak ada pemanggilan SerpApi, Gemini, atau scraping halaman pada review ini. Pemeriksaan lokal memastikan cakupan 850 keputusan, alasan tidak kosong, rujukan duplikat menuju query yang dipertahankan, teks asli dan 403 keputusan terdahulu tidak berubah, serta hash ketiga manifest pengumpulan tetap identik. Tidak ada perubahan pada dataset artikel atau label sitasinya.
