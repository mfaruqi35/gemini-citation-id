# Pengumpulan dataset utama

Batch `main_01` melanjutkan sumber Trends/PAA yang sudah tersedia tanpa sintesis LLM. Keputusan peneliti pada 10 September 2026: **3 percobaan Gemini per query, minimal 2 percobaan valid**. Ini pengumpulan utama; tidak ada pilot tambahan.

## Cakupan dan anggaran

Seleksi awal oleh asisten menghasilkan 41 query asli berbahasa Indonesia: 15 kesehatan, 14 keuangan, dan 12 teknologi. Tujuh kandidat ditunda untuk review dan satu dikeluarkan; alasan tersimpan di `data/manual/original_query_decisions.csv`. Teks query serta hubungan ke sumber tetap dipertahankan. Sembilan query yang pernah dipakai pada pilot boleh ada dalam batch, tetapi respons pilot tidak digabungkan ke percobaan utama.

Rencana maksimal 41 pencarian SerpApi dan 123 panggilan Gemini. Kuota akun yang terpasang telah diperiksa melalui Account API pada 10 September 2026 pukul 12:26 UTC: 250 pencarian tersisa. Setiap eksekusi memeriksa ulang kuota dan menyisakan 10 pencarian. Anggaran SerpApi terpisah dari penggunaan Gemini; penggunaan token Gemini dicatat per respons.

Setiap query mengambil hasil organik posisi 1–10 dari satu respons Google, lalu tiga respons Gemini dengan Google Search dan instruksi B. Jika Google hanya mengembalikan lebih sedikit hasil organik, jumlah itu dicatat apa adanya tanpa pencarian halaman tambahan. Maksimal 410 kemunculan hasil kandidat untuk batch ini; jumlah artikel layak dapat lebih sedikit setelah deduplikasi dan seleksi halaman.

## Definisi valid dan aturan perhitungan

Satu percobaan valid jika respons selesai dengan `finishReason=STOP`, memiliki teks jawaban, serta metadata `groundingSupports` menghubungkan sitasi dengan setidaknya satu sumber web. URL yang sekadar tertulis di jawaban tidak cukup. Validitas ini mengukur adanya grounding yang dapat diamati, bukan membuktikan kebenaran semua klaim atau meniadakan pengetahuan bawaan model.

- Tetap lakukan tiga slot percobaan, termasuk jika dua pertama sudah valid.
- Dua atau tiga valid: query memenuhi syarat jumlah percobaan untuk perhitungan keterkutipan.
- Nol atau satu valid: simpan seluruh respons dan tandai belum layak; jangan menghasilkan label negatif dari kegagalan grounding.
- Tidak ada pengulangan keempat otomatis untuk mengejar jumlah valid. Error API memakai satu slot dan menghentikan eksekusi agar penyebabnya dapat diperiksa; melanjutkan perintah mengerjakan slot berikutnya.
- Proporsi keterkutipan artikel = jumlah percobaan valid yang mensitasi artikel / jumlah percobaan valid. Contoh: satu kali disitasi dari dua valid berarti 0,5; dua kali dari tiga valid berarti 0,667.

`citation_threshold` sementara `null`: proporsi disimpan, label biner masih kosong. Ambang label perlu ditetapkan sebagai keputusan metodologi tersendiri sebelum melihat hasil pemodelan. Pengumpulan tidak perlu diulang ketika pelabelan offline ditambahkan.

## Pencocokan artikel dan keterbatasannya

Rancangan kandidat telah diperluas atas permintaan peneliti: `query_article_pairs_union.csv` berisi gabungan Google Top-10 dan semua sumber web yang disitasi pada percobaan Gemini valid serta mempunyai URL tujuan. `query_article_pairs.csv` tetap memuat kandidat Google untuk pembanding. Semua kemunculan sumber Gemini, termasuk yang masih belum teresolusi atau dari percobaan tidak valid, tetap disimpan di `sources.csv`. Aturan deduplikasi, implikasi pemilihan kandidat berdasarkan sitasi, dan kolom audit yang tidak boleh dijadikan fitur dibahas di [CANDIDATE_UNION.md](MAIN_DATASET.md#gabungan-kandidat).

Skrip segera mencoba resolusi URL setelah respons tersimpan. URL tujuan untuk dibaca ada di `source_url`; redirect mentah tetap ada di `raw_url` untuk audit. Normalisasi konservatif hanya merapikan hostname/port standar, membuang fragmen, dan parameter pelacakan eksplisit. HTTP/HTTPS, www, perbedaan path, AMP, dan canonical tidak diasumsikan sama. Pemeriksaan alias/canonical artikel dilakukan setelah crawling.

Tujuan yang sudah diketahui meski mendapat HTTP 403/503 masih dapat dibandingkan; status akses tetap dicatat. Jika sumber sitasi belum memiliki URL tujuan, ketidakcocokan tidak langsung dianggap nol. `n_unknown_matches`, `citation_lower`, dan `citation_upper` mencatat ketidakpastian; proporsi pasti dan label ditunda. Keberhasilan resolusi bukan bukti bahwa halaman dapat diekstrak atau merupakan artikel.

Waktu mulai Google dan percobaan Gemini untuk setiap query dicatat. Batas operasional awal maksimal enam jam; jeda lebih panjang akibat resume ditandai `within_time_window=False`, sehingga belum layak dilabeli. Batas ini asumsi operasional batch, bukan ketetapan ilmiah universal. Timestamp asli dalam respons Google tetap diarsipkan untuk memeriksa umur cache. Google organik dan pencarian internal Gemini tidak diasumsikan menghasilkan SERP identik.

## Menjalankan dan melanjutkan

Dari root proyek dengan virtualenv aktif:

```powershell
# Pratinjau, tanpa jaringan
python ./src/collect_main_dataset.py

# Kumpulkan/lanjutkan seluruh batch
python ./src/collect_main_dataset.py --run

# Batasi satu eksekusi ke tiga query yang belum selesai; tetap bagian batch utama
python ./src/collect_main_dataset.py --run --max-queries 3

# Ekspor ulang respons tersimpan, tanpa API
python ./src/collect_main_dataset.py --export-only
```

Library standar Python cukup; tidak perlu dependensi baru. `SERPAPI_API_KEY` dan `GEMINI_API_KEY` dibaca dari environment atau `.env`. Nilai environment memiliki prioritas; jangan kirim key ke chat atau simpan di notebook.

Manifest membekukan konfigurasi dan daftar sumber saat pengumpulan mulai. Jangan mengubah keputusan sumber/konfigurasi di tengah batch; ekspansi menggunakan batch dengan `dataset_id` baru dan file query tersendiri. Respons tersimpan sebelum resolusi URL. Kelanjutan tidak memanggil ulang respons yang sudah tersimpan. Checkpoint `started` tanpa respons menunjukkan hasil permintaan tidak pasti dan memerlukan pemeriksaan; tidak ada retry otomatis yang berpotensi menggandakan pemakaian API. Jika ada `.tmp` lebih baru akibat file terkunci, periksa/pulihkan dahulu. Lock `running.lock` mencegah dua proses mengerjakan batch sama; hapus lock usang hanya setelah memastikan proses pengumpulan benar-benar berhenti.

## Berkas hasil dan tahap berikutnya

Data mentah dan manifest: `data/raw/main/main_01/`. CSV hasil: `data/interim/main/main_01/`.

| Berkas | Isi |
|---|---|
| `queries.csv` | Progres, jumlah valid, jumlah Google organik, dan jeda pengumpulan |
| `trials.csv` | Tiga slot per query, status valid, versi model, token, dan error |
| `google_results.csv` | Posisi, judul, snippet, dan URL hasil organik |
| `sources.csv` | Sumber Gemini, hubungan sitasi, URL mentah dan tujuan |
| `query_article_pairs.csv` | Kandidat query–artikel, hitungan/proporsi sitasi, dan ketidakpastian |
| `query_article_pairs_union.csv` | Gabungan kandidat Google dan semua URL sitasi valid Gemini, satu baris per pasangan unik |
| `candidate_pool_protocol.json` | Versi aturan gabungan dan catatan sampling |

[Notebook 04](../notebooks/04_inspect_main_dataset.ipynb) membaca hasil lokal tanpa menjalankan API. Data belum siap pemodelan: `article_status=pending_crawl_and_article_review` dan `ready_for_model=False` sampai artikel diambil, bahasa/jenis halaman diperiksa, fitur diekstrak, dan label ditetapkan. Setelah itu lakukan pemisahan data per query untuk mencegah kebocoran antar pasangan satu query.

Target historis 300 query memerlukan perluasan sumber dan anggaran pengumpulan lebih lanjut; 250 pencarian saja tidak mencukupi 300 pencarian organik baru sekaligus pengambilan PAA. Simpan juga query yang tidak lolos grounding agar tingkat keberhasilan dan bias seleksi dapat dilaporkan.

## Catatan hasil awal

Pengumpulan batch utama sudah dimulai. Pada pemeriksaan setelah tiga query pertama selesai terdapat sembilan percobaan dan 24 pasangan kandidat. Query batuk dan kegunaan VPN masing-masing mempunyai tiga valid; query gaji enam juta mempunyai nol valid karena ketiga respons `MAX_TOKENS`. Sumber sitasi pada respons terpotong tetap disimpan. Batas 4096 token mengikuti konfigurasi pilot; efek pemotongan perlu dilaporkan sebagai kegagalan teknis, terpisah dari respons selesai tanpa grounding. Jangan menyimpulkan query tersebut secara intrinsik tidak dapat menghasilkan sitasi. Jika batas token hendak diperbaiki, tetapkan protokol/batch baru dan dokumentasikan perubahan, jangan mengubah manifest yang sedang berjalan. Angka progres aktual dibaca dari CSV/notebook dan dapat bertambah setelah catatan ini.

## Kegagalan jaringan SerpApi dan pemulihan

`Jaringan SerpApi gagal` pada versi lama mencakup timeout, DNS, dan masalah koneksi lain; pesan tersebut tidak menyatakan kuota habis. Mulai 11 September 2026 batas tunggu respons dinaikkan dari 45 ke 120 detik dan error dibedakan menjadi `timeout`, `dns_error`, `tls_certificate_error`, `tls_error`, `connection_reset`, atau `connection_error`. Rincian numerik error disimpan tanpa API key atau URL permintaan berautentikasi. Verifikasi HTTPS tetap aktif dan tidak ada retry pencarian otomatis.

Jika checkpoint Google gagal tanpa respons dan Gemini belum dimulai, pemulihan satu query dapat dilakukan dengan:

```powershell
# Ganti QUERY_ID dengan ID query gagal yang telah diperiksa
python ./src/recover_main_google.py --query-id QUERY_ID --run
```

Pemulihan memeriksa lock/kuota, mengarsipkan status lama di `google_recovery_history`, lalu mengirim maksimal satu permintaan dengan parameter pencarian identik. Cache bawaan tetap diizinkan; jika cache tersedia, hasil dapat diperoleh tanpa pemakaian kredit baru. Ini tidak menjamin setiap pemulihan gratis. Waktu pencarian dari metadata dipertahankan agar pemulihan hasil cache tidak membuat data lama tampak baru. Tidak ada panggilan Gemini dari skrip pemulihan. Setelah berhasil, gunakan perintah kolektor biasa untuk melanjutkan resolusi URL dan Gemini.

Kasus `vitamin C untuk apa fungsinya?` berhasil dipulihkan pada 11 September 2026: respons `Success` dengan delapan hasil organik, waktu pemrosesan server 52,49 detik, sedangkan batas lama 45 detik. Ini mendukung diagnosis timeout; exception asli tidak mencatat jenis koneksi secara spesifik. Kuota sebelum dan setelah pemulihan tetap 55 terpakai/195 tersisa. Checkpoint kini `response_saved`, siap dilanjutkan dengan `python ./src/collect_main_dataset.py --run`.


---

<a id="query-asli"></a>

## Protokol kerja query asli — versi 1

Tanggal: 10 September 2026. Pekerjaan berikutnya menggunakan sumber Google Trends dan People Also Ask tanpa sintesis query LLM. Data serta pilot sebelumnya tetap dipertahankan.

### Aturan operasional

1. Trends menyediakan topik awal. Topik luas ditelusuri melalui PAA; teks Trends dengan kebutuhan informasi cukup jelas dapat dipertimbangkan langsung.
2. Query dipertahankan persis seperti sumber: tidak diparafrasakan, ditambahi tahun/entitas, atau diterjemahkan otomatis.
3. Batch kerja awal menggunakan teks yang sudah berbahasa Indonesia. Sumber Inggris ditunda dan tetap diarsipkan; jika ingin menerjemahkannya nanti, prosedur harus dicatat secara eksplisit.
4. Bahasa, cakupan domain, kejelasan kebutuhan informasi, konteks tambahan, duplikasi, dan alasan seleksi tetap diperiksa. Penandaan bahasa bukan penerimaan kualitas final.
5. PAA merupakan pertanyaan yang ditampilkan Google, bukan bukti rekaman verbatim query individual pengguna. Sampel ini tidak diklaim mewakili seluruh pengguna Indonesia.
6. Sintesis dan Judgment pertama untuk prompt sintesis tidak diperlukan pada jalur ini. Judgment kedua untuk query sintetis diganti dengan seleksi kualitas sumber yang terdokumentasi. Penilai LLM dapat dipertimbangkan sebagai alat bantu, tetapi belum dijalankan.
7. Keberhasilan grounding pilot tidak dipakai sebagai alasan tunggal menerima query. Konfigurasi B merupakan pilihan berdasarkan pilot; protokol pengumpulan utama tetap perlu dibekukan.

### Hasil persiapan

Masukan: 52 pertanyaan PAA dan 26 sumber Trends dengan status historis `ready_for_synthesis`. Nama status lama hanya dipakai untuk mengambil sumber yang sebelumnya dianggap cukup spesifik, bukan untuk menjalankan sintesis.

| Kelompok | Jumlah |
|---|---:|
| Seluruh sumber | 78 |
| PAA berbahasa Indonesia | 48 |
| Trends berbahasa Indonesia | 1 |
| Kandidat Indonesia | 49 |
| Sumber Inggris ditunda | 29 |

Kandidat Indonesia mencakup 17 kesehatan, 20 keuangan, dan 12 teknologi. Satu sumber Trends Indonesia adalah `hakikat senam aerobik menurut jackie sorensens`; kesesuaian cakupannya masih perlu ditinjau. Empat PAA ICD-10 dan 25 sumber Trends berbahasa Inggris tidak diterjemahkan. Sembilan query pilot ditandai sebagai pernah digunakan tanpa otomatis diterima berdasarkan hasil sitasinya.

Seleksi awal oleh asisten telah dicatat: **41 accepted** (15 kesehatan, 14 keuangan, 12 teknologi), **7 needs_review**, dan **1 excluded**. Seleksi memakai bahasa, domain, dan kejelasan kebutuhan informasi; hasil grounding tidak digunakan sebagai kriteria. Ini bukan penilaian manusia independen. Alasan setiap keputusan tersedia di CSV manual dan notebook 03. Query dengan asumsi efek sunscreen cepat, konteks keuangan yang kurang, serta topik akademik senam ditunda. Pertanyaan nama website NPWP dikeluarkan karena bersifat navigasional. Pemeriksaan duplikasi intent masih dapat diperlukan.

### Menjalankan

```powershell
python ./src/prepare_original_queries.py
```

Gunakan [notebook 03](../notebooks/03_review_original_queries.ipynb) untuk melihat sumber dan mengisi keputusan berdasarkan teks query. Keputusan tersimpan dibaca kembali pada sesi berikutnya. [Konfigurasi sumber](../configs/original_query_sources.json) mencatat pemeriksaan bahasa PAA oleh asisten untuk 52 ID saat ini; ID baru tanpa pemeriksaan menjadi `unknown`.

Hasil di `data/interim/original_queries/`:

- `source_pool.csv`: seluruh sumber, termasuk yang ditunda.
- `candidates_id.csv`: kandidat bahasa Indonesia, dengan status kualitas masing-masing.
- `deferred_language.csv`: sumber non-Indonesia/unknown tanpa penerjemahan.
- `accepted.csv`: kemunculan sumber yang diterima.
- `accepted_unique.csv`: query unik yang diterima.

Keputusan disimpan terpisah di `data/manual/original_query_decisions.csv`. `query_id` berdasarkan domain serta normalisasi huruf/spasi; `query_text` tidak diubah. Hubungan ke sumber tetap ada dan kemiripan semantik belum digabungkan.

### Berikutnya

Batch utama pertama memakai 41 query diterima. Peneliti menetapkan **3 percobaan Gemini per query, minimal 2 valid**. Prosedur, definisi valid, dan kelanjutan pengumpulan ada di [MAIN_DATASET.md](MAIN_DATASET.md). Ambang label biner belum ditetapkan. Setelah pengumpulan Google dan Gemini, cocokkan URL, ambil artikel, dan ekstrak fitur. Perluas sumber jika jumlah/keragaman kurang; batch ini belum memenuhi target historis 300 query.


---

<a id="penambahan-query"></a>

## Penambahan query asli untuk dataset utama

Pada 10 September 2026 peneliti meminta penambahan query menggunakan kuota tersedia. Pengumpulan `paa_expansion_01` memakai 30 topik Trends yang belum dicoba pada pengambilan PAA awal, masing-masing 10 kesehatan, keuangan, dan teknologi. Pemilihan dilakukan asisten secara purposif untuk memperluas topik. Teks sumber dipertahankan tanpa sintesis atau penerjemahan.

### Hasil penambahan

Seluruh 30 permintaan selesai: 24 menghasilkan PAA dan enam tanpa PAA, total **96 kemunculan pertanyaan**. Topik tanpa PAA: `coretax`, `kurs dollar`, `spreadsheet`, `chatgpt`, `canva`, dan `outlook`. Hasil kosong tetap diarsipkan.

Selain itu, 96 kemunculan PAA diekstrak dari 24 respons Google batch utama yang telah tersimpan. Ekstraksi lokal ini tidak memanggil API. Snapshot gabungan berisi:

| Ukuran | Jumlah |
|---|---:|
| Kemunculan sumber PAA | 192 |
| Query unik berdasarkan domain dan normalisasi huruf/spasi | 188 |
| Sudah ada pada pool awal | 5 |
| Kandidat tambahan | 183 |
| Diterima setelah seleksi awal asisten | 123 |
| Perlu review | 29 |
| Dikeluarkan | 31 |

Sebanyak 123 query diterima ditambahkan sebagai daftar tersendiri; jika digabung secara konseptual dengan 41 query batch pertama, ada **164 query diterima**. Pengumpulan Google/Gemini untuk 123 query baru belum dijalankan. Jumlah tersebut bukan jumlah query lolos grounding atau artikel siap pakai.

Semua 183 kandidat dalam snapshot ini diperiksa sebagai teks Indonesia. Seleksi mencatat kejelasan intent, cakupan domain, navigasi/gambar, dan pengulangan makna. Query dengan konteks pinjaman kurang, makna `driver` ambigu, atau premis yang perlu diperiksa masuk `needs_review`. Variasi daftar rumus Excel dan beberapa pertanyaan pajak/VPN dikeluarkan untuk mengurangi pengulangan. Hasil grounding tidak menjadi dasar penerimaan. Ini seleksi asisten, bukan penilaian manusia independen atau evaluasi faktual atas jawaban medis/keuangan.

### Kuota

Sebelum pengumpulan tambahan, Account API menunjukkan 226 pencarian tersisa. Konfigurasi membatasi batch ke 30 pencarian dan memeriksa cadangan 180 sebelum mulai. Snapshot akun setelah batch PAA selesai pada 13:12 UTC menunjukkan **197 pencarian tersisa**. Selisih snapshot akun tidak harus sama dengan jumlah permintaan batch karena cache dan proses lain; catatan 30 permintaan disimpan per request. Cadangan ini menampung sisa pengumpulan utama dan query baru, bukan alokasi untuk menghabiskan seluruh kuota pada PAA.

### Menjalankan

```powershell
# Ekstraksi/gabung PAA dari berkas tersimpan, tanpa API
python ./src/prepare_query_expansion.py

# Pratinjau daftar 30 topik perluasan
python ./src/collect_paa.py --config configs/paa_expansion_01.json

# Melanjutkan pengambilan perluasan jika belum lengkap; permintaan tersimpan dilewati
python ./src/collect_paa.py --config configs/paa_expansion_01.json --run
```

Gunakan [notebook 05](../notebooks/05_review_query_expansion.ipynb) untuk melihat dan mengoreksi seleksi. Notebook membaca ulang keputusan tersimpan dan tidak menjalankan API. Jalankan kembali setelah respons utama bertambah untuk menemukan PAA tambahan; pertanyaan baru otomatis `pending`, tidak langsung diterima.

### Berkas dan keterlacakan

- `configs/paa_expansion_01.json`: topik, parameter pencarian, dan anggaran.
- `configs/query_expansion_01.json`: batch sumber untuk ekstraksi lokal.
- `data/interim/paa/paa_expansion_01/`: hasil 30 pencarian dan 96 PAA langsung.
- `data/interim/query_expansion/query_expansion_01/source_pool.csv`: semua kemunculan dan jejak sumber.
- `data/interim/query_expansion/query_expansion_01/candidates.csv`: kandidat baru unik beserta keputusan.
- `data/interim/query_expansion/query_expansion_01/accepted_new.csv`: 123 query diterima untuk pengumpulan berikutnya.
- `data/manual/query_expansion_01_decisions.csv`: bahasa, keputusan, alasan, identitas penilai, dan waktu review.

PAA dari topik Trends langsung diberi kedalaman satu. PAA dari respons query utama mempertahankan `parent_query_id`, `topic_id` Trends, dan kedalaman berikutnya. Semua kemunculan sumber disimpan walau teks sama; kandidat digabung berdasarkan ID query. Pencocokan teks dengan pool lama mencegah pengajuan ulang pertanyaan lama termasuk yang pernah ditunda/dikeluarkan. Perbandingan makna tetap memerlukan review.

Daftar 41 query dan manifest `main_01` tidak diubah. Snapshot saat penambahan selesai menunjukkan batch Gemini lama berhenti pada HTTP 429 untuk percobaan kedua query `Fungsi Excel apa saja?`; respons sebelumnya tersimpan. Penyebab pembatasan Gemini perlu diperiksa sebelum melanjutkan, dan penambahan PAA ini tidak memanggil Gemini atau mengulang percobaan gagal.


---

<a id="gabungan-kandidat"></a>

## Kandidat Google Top-10 dan semua sitasi Gemini

Pada 10 September 2026 peneliti meminta kandidat artikel mencakup hasil organik Google dan seluruh sumber yang disitasi Gemini. Aturan ekspor `google_top10_plus_valid_citations_v1` menambahkan tabel gabungan tanpa mengubah permintaan API atau manifest pengumpulan. Daftar sumber sebenarnya sudah menyimpan banyak sumber per percobaan; tabel pasangan sebelumnya hanya mencakup kandidat Google.

### Pembentukan kandidat

Untuk setiap query, himpunan kandidat adalah gabungan:

1. Hasil organik Google posisi 1–10 yang tersedia dalam respons tersimpan.
2. Semua sumber web dengan hubungan sitasi dalam `groundingSupports`, dari setiap percobaan Gemini valid yang sudah tersimpan, dan mempunyai URL tujuan yang dapat dinormalisasi.

Satu URL hasil normalisasi menjadi satu pasangan per query. Sitasi berulang ke URL yang sama dalam satu jawaban dihitung satu kali pada `n_cited`. URL yang sama pada query lain tetap merupakan pasangan berbeda. Seluruh tiga percobaan digunakan sesuai protokol; kriteria minimal dua valid tetap berlaku untuk kelayakan query. Snapshot query yang belum selesai atau belum memenuhi minimal valid tetap diekspor dengan tanda belum layak.

Metadata API menyediakan referensi dalam `groundingChunks` serta hubungan dukungan dalam `groundingSupports`; implementasi mengambil sumber web yang benar-benar ditunjuk hubungan dukungan. [Referensi GenerateContent](https://ai.google.dev/api/generate-content#GroundingMetadata).

Semua kemunculan sumber, termasuk dari respons tidak valid dan URL belum teresolusi, tetap tersedia dalam `sources.csv` dan JSON mentah. Sumber hanya dari respons terpotong tidak dijadikan kandidat tambahan untuk analisis utama. Sumber dengan URL tujuan belum diketahui menunggu resolusi; tidak dibuat URL tebakan. Ketidakpastian pencocokan tidak otomatis menjadi label nol.

### Hasil ekspor

Di `data/interim/main/main_01/`:

- `query_article_pairs_union.csv`: tabel gabungan untuk peninjauan dan persiapan crawling.
- `query_article_pairs.csv`: tabel kandidat Google Top-10 untuk pembanding.
- `sources.csv`: seluruh kemunculan sumber Gemini dengan informasi apakah disitasi dan URL tujuan.
- `candidate_pool_protocol.json`: versi aturan kandidat, hash manifest pengumpulan, normalisasi, dan catatan sampling.

Kolom tambahan tabel gabungan:

| Kolom | Arti |
|---|---|
| `article_title` | Judul dari Google organik atau metadata sumber Gemini |
| `candidate_origin` | `google_only`, `google_and_gemini`, atau `gemini_only` |
| `in_google_top10` | URL teramati pada hasil organik Google tersimpan |
| `in_gemini_citations` | URL teramati disitasi pada setidaknya satu percobaan valid |

Untuk `gemini_only`, `google_positions=[]` dan judul/snippet Google kosong. Tidak ditemukannya URL pada Top-10 tidak menentukan apakah peringkatnya 11, lebih rendah, atau tidak terindeks. `google_only` berarti belum ditemukan kecocokan dengan sitasi valid yang URL-nya diketahui; jika ada URL belum teresolusi, periksa kolom ketidakpastian sebelum menafsirkannya.

Proporsi keterkutipan tetap `n_cited / n_valid`. Kandidat tambahan tidak otomatis diberi label positif untuk setiap ambang: misalnya satu sitasi dari tiga valid menghasilkan 1/3, yang akan di bawah ambang 0,5 apabila ambang tersebut dipilih. Ambang aktual masih `null` dan label biner belum ditetapkan.

### Implikasi rancangan penelitian

Populasi kandidat berubah menjadi gabungan hasil Google dan sumber yang teramati disitasi; sebagian kandidat dipilih berdasarkan hasil yang hendak diprediksi. Distribusi label gabungan tidak mewakili tingkat sitasi seluruh artikel web atau seluruh hasil Google.

`candidate_origin`, `in_gemini_citations`, jumlah/proporsi sitasi, dan metadata hasil percobaan adalah kolom audit atau target, bukan fitur prediksi. Dalam tabel gabungan, keberadaan/peringkat Google dan kekosongan judul/snippet Google juga dapat mengungkap cara kandidat dipilih. Jangan memasukkannya sebagai fitur gabungan tanpa mengubah dan memvalidasi rancangan sampling. Judul/isi artikel untuk fitur perlu diperoleh dengan prosedur ekstraksi yang sama bagi kedua asal kandidat. Tabel Google Top-10 tetap tersedia untuk evaluasi pembanding pada himpunan yang dibentuk sebelum melihat sitasi. Pemisahan data harus menjaga pasangan dari query yang sama berada pada bagian yang sama; hubungan topik induk juga perlu dipertimbangkan.

### Snapshot hasil

Pada ekspor pertama terdapat 41 query terjadwal, 23 query selesai, dan 71 catatan percobaan. Tabel Google memiliki 202 pasangan; tabel gabungan memiliki **554 pasangan dengan 515 URL kandidat unik**: 132 `google_only`, 70 `google_and_gemini`, dan 352 `gemini_only`. Sebanyak 513 pasangan berasal dari query selesai yang memenuhi minimal valid dan batas waktu; ini belum berarti semua pasangan telah pasti dicocokkan atau artikelnya layak. Ada 13 kemunculan sumber disitasi tanpa URL tujuan dalam tabel audit.

Contoh `Minum apa agar batuk cepat sembuh?`: sembilan kandidat Google dan 15 URL sitasi valid unik, tiga di antaranya sama, sehingga gabungannya 21 pasangan. Semua kandidat masih menunggu pengambilan isi, seleksi artikel/bahasa, pemeriksaan alias/canonical, fitur, serta pelabelan.

### Memperbarui

```powershell
python ./src/collect_main_dataset.py --export-only
```

Perintah ini memakai data lokal tanpa API. Pengumpulan berikutnya juga mengekspor kedua tabel secara otomatis. Notebook 04 sekarang membaca tabel gabungan dan menampilkan `n_candidate_union` per query. Jalankan sel pemuatan dan sel periksa query untuk melihat semua pasangan serta semua kemunculan sitasi query tersebut.

Pembaruan 11 September 2026: percobaan terakhir query Excel kembali mendapat 429 `RESOURCE_EXHAUSTED`. Ada 24 query selesai diproses dan 72 catatan percobaan; jumlah kandidat tetap sama karena respons error tidak menambahkan sumber. Pengumpulan 17 query berikutnya belum dilanjutkan akibat batas Gemini. Lihat catatan terbaru di PROGRESS.md.


---

<a id="penggabungan-trends"></a>

## Penggabungan sumber Google Trends

Jalankan dari direktori utama proyek:

```powershell
.\venv\Scripts\python.exe .\src\merge_trends.py
```

Skrip menggunakan library standar Python (`csv` dan `pathlib`), tanpa instalasi tambahan.
Lokasi masukan dihitung dari lokasi skrip sehingga tidak bergantung pada direktori kerja.

Masukan adalah enam file `data/top_{domain}.csv` dan
`data/rising_{domain}.csv` untuk kesehatan, keuangan, dan teknologi.
Folder `data/before` tidak dibaca. Hasil ditulis ke
`data/interim/trends_sources.csv`; menjalankan ulang akan mengganti hasil tersebut.

Semua baris dipertahankan, termasuk duplikasi dan sumber yang belum diseleksi.
Nilai minat pencarian dan persentase kenaikan disalin sebagai teks tanpa konversi.
Skrip memvalidasi kolom, kelengkapan baris, dan query kosong sebelum menulis hasil.

| Kolom | Keterangan |
|---|---|
| `source_id` | ID berdasarkan domain, jenis daftar, dan urutan baris data |
| `source_type` | `google_trends` |
| `domain` | Pemetaan berdasarkan nama file, bukan hasil penilaian relevansi |
| `source_list` | `top` atau `rising` |
| `source_file` | Path relatif file masukan |
| `source_row` | Urutan baris data, dimulai dari 1 setelah header |
| `source_text` | Isi asli kolom `query` |
| `search_interest` | Isi asli kolom `search interest` |
| `increase_percent` | Isi asli kolom `increase percent` |

ID dapat berubah jika urutan atau isi baris sumber diubah. Bekukan file masukan
sebelum ID digunakan oleh tabel penilaian atau sintesis. Metadata kategori asli,
periode, wilayah, dan tautan pengambilan belum ditambahkan karena belum tersedia
di CSV masukan. File hasil dapat dibaca dari Jupyter dengan `pandas.read_csv`.


## Ketentuan awal kredibilitas sumber

Ketentuan awal tingkat kredibilitas sumber berdasarkan keputusan peneliti pada 11 September 2026:

| Tingkat | Ketentuan |
| ------- | --------- |
| 1 | Domain resmi pemerintah (.go.id), atau institusi dengan status verifikasi tertinggi sesuai kriteria domainnya (rumah sakit terakreditasi KARS paripurna, lembaga jasa keuangan berizin penuh OJK). |
| 2 | Terverifikasi resmi sesuai kriteria per domain tapi bukan kategori tertinggi (PSE terdaftar, Dewan Pers terverifikasi administratif dan faktual, rumah sakit terakreditasi non-paripurna). |
| 3 | Portal dengan proses editorial/tinjauan ahli yang terlihat, tapi bukan institusi berstatus resmi sesuai kriteria di atas (contoh: portal kesehatan konsumer besar dengan tinjauan dokter). |
| 4 | Situs dengan identitas jelas tapi tidak ditemukan status verifikasi resmi apa pun (blog bermerek, situs bisnis/UMKM). |
| 5 | Tidak dapat diverifikasi sama sekali, atau UGC/forum tanpa identitas jelas. |

Angka 1 menunjukkan tingkat tertinggi dan angka 5 tingkat terendah dalam rubrik penelitian ini. Rubrik merupakan ketentuan operasional peneliti, bukan klasifikasi resmi bersama dari lembaga-lembaga tersebut atau jaminan kebenaran isi artikel. Penerapannya harus disertai sumber bukti, tanggal pemeriksaan, dan alasan penetapan tingkat. Sumber yang belum diperiksa tetap berstatus belum ditinjau, bukan otomatis tingkat 5.
