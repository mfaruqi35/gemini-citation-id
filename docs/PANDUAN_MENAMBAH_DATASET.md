# Panduan menambah dataset: PAA sampai artikel dan fitur

Panduan ini mengikuti skrip proyek, diperbarui **14 September 2026**. Semua perintah dijalankan dari direktori utama proyek. Contoh nama batch baru di bawah adalah nama yang perlu kamu buat sendiri, bukan batch yang otomatis sudah tersedia. Menulis panduan ini tidak menjalankan pengumpulan berbayar.

**Pemisahan aktif:** dataset utama adalah artikel Google Top-10 dengan label sitasi Gemini pada ambang >=0,5. Sitasi Gemini di luar Top-10 menjadi dataset tambahan. Skrip scraping tetap memakai daftar URL gabungan untuk mengumpulkan keduanya; builder memisahkan ekspornya secara otomatis. Tidak perlu menjalankan scraper dua kali untuk masing-masing kelompok.

## 1. Tentukan mulai dari tahap mana

Alur penelitian:

**Keyword Google Trends → pertanyaan PAA → review query → Google Top-10 + tiga jawaban Gemini → gabungan URL → scraping → review artikel/kredibilitas → fitur dan label → dataset utama Top-10 + dataset tambahan Gemini-only.**

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
| Review kredibilitas lewat bukti publik/browser | Tidak | Tidak | Skrip PSE yang tersedia mengakses layanan publik langsung |
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

Tuntaskan pengumpulan/ekspor batch sebelum membuat manifest scraping. Scraper membekukan fingerprint file pasangan sumber; perubahan file sumber setelah scraping dimulai dapat ditolak untuk menjaga konsistensi.

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

Setelah bagian 7 selesai, salin `configs/article_dataset.json` menjadi `configs/article_dataset_02.json`, lalu ubah:

```json
"dataset_id": "articles_main_02",
"source_batches": ["main_02"]
```

Salin `configs/article_features.json` menjadi `configs/article_features_02.json`; ubah hanya `scrape_config` menjadi `configs/article_dataset_02.json` jika definisi fitur lainnya tetap sama. Dua CSV review manual boleh dipakai bersama karena memakai ID artikel dan hostname.

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

## 9. Review artikel, kredibilitas, fitur, dan label

**Biaya: tidak memakai kedua API dengan alat lokal yang tersedia.**

Buka `notebooks/06_inspect_article_dataset.ipynb`. Untuk batch baru, ubah **hanya `FEATURE_CONFIG`** pada sel pemuatan, misalnya menjadi `ROOT / 'configs/article_features_02.json'`, lalu jalankan ulang sel pemuatan. Config scraping, folder hasil, CSV kredibilitas, serta perintah scraping/build otomatis mengikuti config fitur tersebut. Jangan mengganti `OUTPUT` secara terpisah. Contoh artikel memilih Alodokter jika tersedia, atau artikel pertama pada batch; `ARTICLE_ID` tetap boleh kamu ganti untuk inspeksi. Untuk batch yang belum memiliki ekspor artikel sama sekali, jalankan terminal bagian 8 terlebih dahulu sebelum membaca tabel di notebook.

Periksa teks, judul, bahasa, dan jenis halaman. Pastikan isi bukan menu, ringkasan terpotong, halaman tantangan, listing aplikasi, atau halaman non-artikel. Website baru mungkin memerlukan penyesuaian ekstraktor jika template umumnya tidak cukup; skrip reusable tidak menjamin setiap situs berhasil tanpa penyesuaian.

Edit CSV review dengan mempertahankan header dan baris lama:

| File | Kolom yang kamu isi |
| --- | --- |
| `data/manual/article_review.csv` | `article_id,status,language,reason,reviewer,reviewed_at` |
| `data/manual/source_credibility.csv` | `hostname,credibility_level,review_status,source_category,evidence_urls,checked_at,reason,reviewer` |

Untuk artikel, gunakan `accepted`/`excluded` dan `language=id` jika isi Indonesia. Satu keputusan per `article_id`. Untuk sumber, satu baris per hostname; `www.example.com` dan `example.com` tidak otomatis sama dalam tabel review ini. Gunakan editor CSV yang mempertahankan UTF-8 dan tanda kutip pada nilai yang mengandung koma.

Rubrik kredibilitas:

| Tingkat | Kriteria |
| --- | --- |
| 1 | Pemerintah .go.id atau status tertinggi sesuai domain, misalnya KARS paripurna atau izin penuh OJK |
| 2 | Verifikasi resmi selain kategori tertinggi: PSE, Dewan Pers administratif dan faktual, KARS non-paripurna |
| 3 | Proses editorial/tinjauan ahli terlihat tanpa status resmi yang sesuai kategori di atas |
| 4 | Identitas situs jelas, tetapi status verifikasi resmi tidak ditemukan setelah pemeriksaan yang memadai |
| 5 | Tidak dapat diverifikasi sama sekali atau UGC/forum tanpa identitas jelas |

Catat bukti, tanggal, alasan, dan identitas penilai. Isi `review_status=verified` jika bukti mendukung pemetaan tingkat, `provisional` untuk sementara, `needs_verification` jika belum cukup bukti, atau `needs_rubric_mapping` jika jenis institusi belum tercakup. Belum diperiksa tidak otomatis tingkat 5. Jangan memakai status verified hanya supaya baris masuk dataset model.

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
- **Sumber main batch baru:** buat config/ID scraping baru; jangan mengedit `source_batches` manifest yang sudah berjalan.
- **Koreksi review/fitur:** edit CSV manual dan bangun ulang lokal, tanpa API.
- **Error API, status started, atau lock tertinggal:** periksa checkpoint dan proses lama dahulu. Jangan menghapus raw/checkpoint untuk mengejar status selesai. Resume bukan retry semua kegagalan.

Catat setiap penambahan pada `docs/PROGRESS.md`: tanggal, ID batch, sumber keyword/query, jumlah pencarian, jumlah respons valid, kuota sebelum/sesudah jika tersedia, jumlah URL dicoba/layak/gagal, perubahan protokol, penilai, serta versi konfigurasi. Dengan begitu data yang bertambah tetap dapat ditelusuri sampai sumber Trends/PAA dan respons Gemini yang membentuk labelnya.
