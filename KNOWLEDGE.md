# KNOWLEDGE PATTERN — Project MagangHub (untuk Hermes)

Dokumen ini adalah pola pengetahuan (knowledge pattern) agar agen Hermes milik Salman
("dodon") dapat menemukan, membaca, dan memakai project-project yang dibuat Luna
(Muse) seputar data lowongan MagangHub Kemnaker. Ditulis 31 Oktober 2026.
Bahasa data: Bahasa Indonesia. Semua tanggal dalam WIB (Asia/Jakarta).

## 0. Ringkasan konteks

- Pemilik data: Salman Alfarizi Taha, fresh graduate Informatika Universitas
  Gunadarma (2022–2026), domisili Cibinong, Kab. Bogor. Target karier: DevOps
  entry-level; skill: Python, REST API, SQL, n8n, Selenium, otomasi & integrasi
  API, server/infrastruktur, backend, ML/pengolahan data, Golang intermediate.
- Sumber data: situs MagangHub Kemnaker — Magang Nasional
  (https://maganghub.kemnaker.go.id/magang-nasional/lowongan).
- Ada 4 project data + 1 dashboard. Pola aksesnya sama: file Excel (.xlsx) untuk
  dibaca manusia, file JSON mentah untuk diproses mesin, script Python (.py)
  adalah penghasil datanya (sumber kebenaran metode).

## 1. Peta lokasi (WAJIB dibaca dulu)

Project yang sama ada di dua tempat. Hermes berjalan di PC Salman, jadi pakai
jalur PC sebagai utama:

| Project | Di PC Salman (utama) | Di workspace Luna (mirror) |
|---|---|---|
| Scrape 1 (2 jurusan, perusahaan) | `C:\1project\maganghub-scraper\` | `~/workspace/maganghub-scraper/` |
| Scrape 2 (3 jurusan, semua penyelenggara) | `C:\1project\maganghub-scraper-2\` | `~/workspace/maganghub-scraper-2/` |
| Scrape total (tanpa filter) + rekomendasi gabungan | `C:\1project\maganghub-semua\` | `~/workspace/maganghub-semua/` |
| Script rekomendasi & sheet rekomendasi awal | (di dalam `maganghub-scraper-2\` di PC) | `~/workspace/maganghub-rekomendasi/` |
| Inventaris semua project Salman | `C:\1project\DAFTAR_SEMUA_PROJECT_DODON.md` | `~/workspace/projects-inventory/` |
| Dashboard interaktif | Artifact Muse: slug `dashboard-lowongan-maganghub` (nama "Dashboard Lowongan MagangHub") | — |

Aturan: file di PC dan di workspace Luna isinya sama (hasil salinan terverifikasi).
Jika ragu mana yang terbaru, bandingkan tanggal file; data scrape bertanggal
2026-10-31.

## 2. Isi tiap project

### 2.1 maganghub-scraper (Scrape 1 — 31 Okt 2026)
Filter: jurusan Informatika + Ilmu Informatika, penyelenggara Perusahaan saja.
Hasil: 678 slot / 38 halaman → 647 lowongan unik.
File penting:
- `Lowongan_MagangHub_Informatika_Perusahaan_2026-10-31.xlsx` — sheet utama.
- `maganghub_scraper.py` — scraper (lihat pola teknis di bagian 4).
- `all_vacancies_raw.json` — data mentah gabungan (format di bagian 3).
- `html_pages\` — 38 file HTML mentah per halaman (bukti sumber).

### 2.2 maganghub-scraper-2 (Scrape 2 — 31 Okt 2026)
Filter: jurusan Ilmu Informatika + Informatika + Manajemen Informatika,
SEMUA tipe penyelenggara. Hasil: 1.289 slot / 72 halaman → 1.245 lowongan unik
(840 perusahaan, 405 instansi pemerintah).
File penting: pola nama sama seperti 2.1, sheet-nya
`Lowongan_MagangHub_3Jurusan_SemuaPenyelenggara_2026-10-31.xlsx`.
Di folder PC ini juga ada sheet rekomendasi pertama:
`Rekomendasi_Lowongan_MagangHub_Untuk_Salman_2026-10-31.xlsx` (215 baris).

### 2.3 maganghub-semua (Scrape total — 31 Okt 2026)
TANPA filter: semua jurusan, semua penyelenggara, semua daerah.
Hasil: 27.667 slot / 1.538 halaman → 21.372 lowongan unik, 4.840 penyelenggara,
total kuota 46.522.
File penting:
- `Semua_Lowongan_MagangHub_TanpaFilter_2026-10-31.xlsx` — sheet master
  21.372 baris (25 kolom, sama seperti sheet lain) + sheet "Info".
- `Rekomendasi_Dari_Semua_Lowongan_Untuk_Salman_2026-10-31.xlsx` — rekomendasi
  final & terlengkap: 515 lowongan (lihat bagian 5). Gunakan file INI untuk
  pertanyaan rekomendasi, bukan sheet rekomendasi lama.
- `all_vacancies_raw.json` — 21.372 lowongan mentah hasil dedupe.
- `html_pages.zip` — seluruh 1.538 halaman HTML sumber.
- `scraper_semua.py` — scraper paralel (16 worker).
Catatan integritas: listing situs berubah selama hari pendaftaran; 310 lowongan
dari Scrape 2 tidak tertangkap ulang di scrape total, jadi dataset gabungan
(dedupe per ID) = 21.682 lowongan unik. Angka "total menurut situs" adalah
potret saat scrape, bukan konstanta.

### 2.4 Dashboard Lowongan MagangHub (artifact Muse)
- Slug: `dashboard-lowongan-maganghub`. Berisi 515+ rekomendasi yang sama
  dengan sheet 2.3, dengan fitur cari/filter (klaster skill, kota, tipe
  penyelenggara, menerima jurusan, belum ada pelamar, peluang, prioritas),
  Top 10, grafik, detail lowongan, dan penanda Simpan/Dilamar/Lewati.
- Update otomatis tiap 6 jam (cron `dashboard-maganghub-refresh-6h`) dari
  listing MagangHub terfilter 3 jurusan Salman + tombol Perbarui manual.
  Refresh bisa parsial bila server situs lambat; statusnya tertulis jujur
  di dashboard ("diperbarui sebagian").

## 3. Skema data

### 3.1 JSON mentah (`all_vacancies_raw.json` / `wrapped_*.json`)
Struktur: objek `{"vacancies": [ ... ], "meta_pages": [...]}` pada file
`wrapped_*.json`; pada `all_vacancies_raw.json` bisa berupa list langsung.
Satu lowongan = satu objek dengan kunci utama:
- `id` (UUID, kunci dedupe), `positionName`, `taskDescription`
- `quantityNeeded` (kuota dibutuhkan), `approvedQuantity` (kuota disetujui),
  `totalApplications` (jumlah pelamar saat scrape)
- `competitiveScore`, `opportunityScore` (skor bawaan situs)
- `studyProgram` {id, name} (jurusan utama) dan `studyPrograms` [{id, name}]
  (SEMUA jurusan yang diterima lowongan itu)
- `organizer` {name, organizableType: "company"|"government", email, phone,
  address, city{name}}
- `city` {name} — kota lokasi magang; `address`, `publishedAt`
- `educationLevels`, `workingDaysPerWeek`, `daysOff`, `interviewTypes`,
  `isDisabilityFriendly`
- `_detailUrl` (link detail lowongan), `_page` (halaman sumber)
Duplikat: ID yang sama bisa muncul beberapa kali di listing (slot > unik);
selalu dedupe berdasarkan `id`, ambil kemunculan dengan `totalApplications`
terbaru/terbesar sebagai yang paling segar.

### 3.2 Sheet Excel (.xlsx)
Sheet "Lowongan Magang": 25 kolom — No, Posisi, Perusahaan/Penyelenggara,
Tipe Penyelenggara, Kota/Kabupaten, Alamat, Kuota Dibutuhkan, Kuota Disetujui,
Total Pelamar, Skor Kompetitif, Skor Peluang, Jenjang Pendidikan, Program Studi
(utama), Semua Program Studi yang Diterima, Hari Kerja/Minggu, Hari Libur,
Tipe Interview, Ramah Disabilitas, Email, Telepon, Tanggal Publish, Halaman
Sumber, Link Detail Lowongan, ID Lowongan, Deskripsi Tugas. Sheet "Info"
berisi asal data & catatan. Baca dengan pandas/openpyxl:
`pd.read_excel(path, sheet_name='Lowongan Magang')`.

## 4. Pola teknis scraping (jika Hermes perlu men-scrape ulang)

- Halaman listing adalah Next.js SSR: data lowongan tertanam sebagai JSON
  `initialVacancies` di dalam payload RSC (`self.__next_f.push`). Parse dengan
  `json.JSONDecoder().raw_decode`, bukan unescape manual.
- API internal `api.kemnaker.go.id/v2/vacancies/published` TIDAK bisa diakses
  langsung dari luar (404/301) — scraping HTML adalah satu-satunya jalur.
- Pola URL: `https://maganghub.kemnaker.go.id/magang-nasional/lowongan?page=N`
  (18 lowongan/halaman). Filter jurusan memakai query
  `study_program[i][id]` + `study_program[i][label]`.
- ID jurusan Salman: Ilmu Informatika `b65a25f2-988f-40f8-9dfd-c1c097560e41`,
  Informatika `0b074455-5cb4-45c4-8111-1a9e3b6de1c0`,
  Manajemen Informatika `d5d70731-4169-42b2-90ba-028f85f4798e`.
- Server sering lambat/502 saat ramai: pakai timeout connect 20 dtk / read
  180 dtk, header `Accept-Encoding: identity`, retry dengan backoff, dan
  perlakukan halaman kosong kecil (~33 KB, tanpa `initialVacancies`) sebagai
  "coba lagi", BUKAN akhir data. Akhir data = meta `lastPage` terlampaui /
  halaman terkonfirmasi kosong.

## 5. Metode rekomendasi (skoring CV)

Dipakai untuk sheet rekomendasi & dashboard. Implementasi:
`matching*.py` + `build_rekomendasi*.py` di `maganghub-rekomendasi\`
(versi final: `matching_merged.py` + `build_rekomendasi_merged.py`).
- Relevansi skill: pencocokan kata kunci 5 klaster (DevOps & Infrastruktur IT;
  Automation & Integrasi API; Backend & Software Development; Data & Machine
  Learning; IT Support & Operasional IT). Nama posisi bobot 3x, deskripsi 1x.
  Ambang relevan: skor relevansi >= 5. Posisi non-IT (sales, akuntansi, admin
  umum, dst.) disisihkan.
- Skor Akhir (0–100) = relevansi skill (maks 55) + probabilitas dari rasio
  pelamar/kuota (maks 25) + kedekatan lokasi dari Cibinong (maks 10:
  Bogor 10, Depok 9, Jakarta 8, Bekasi/Tangerang 7, Jabar lain 4, luar 2)
  + nilai pengembangan skill (maks 10).
- Label peluang dari rasio pelamar per kuota: 0 pelamar atau <=0,5 "Sangat
  tinggi"; <=1 "Tinggi"; <=2 "Sedang-tinggi"; <=4 "Sedang"; <=8 "Rendah";
  >8 "Sangat rendah". Ini estimasi kasar dari data publik, BUKAN jaminan.
- Hasil final (dataset gabungan 21.682): 515 rekomendasi — klaster Backend
  199, IT Support 183, DevOps 77, Data/ML 45, Automation 11; 257 di
  Jabodetabek+Bogor; 115 belum ada pelamar; 219 menerima salah satu dari
  3 jurusan Salman (138 menerima Informatika persis). Kolom "Menerima Jurusan"
  di sheet menandai eligibilitas ini per baris.
- Konteks waktu: pendaftaran Batch 3 dilaporkan dibuka 31 Okt – 4 Nov 2026.

## 6. Pola tanya-jawab (contoh penggunaan knowledge ini)

- "Lowongan DevOps terbaik untuk Salman?" → buka sheet rekomendasi final
  (2.3), filter Klaster = "DevOps & Infrastruktur IT", urutkan Skor Akhir
  desc, utamakan "Menerima Jurusan" berisi Informatika.
- "Ada lowongan baru dekat rumah?" → filter Kota mengandung Bogor/Depok/
  Bekasi/Jakarta/Tangerang pada sheet master (2.3) atau cek dashboard
  (paling segar, update 6 jam).
- "Perusahaan X punya lowongan apa saja?" → cari nama di kolom
  Perusahaan/Penyelenggara pada sheet master 21.372 baris.
- Angka total (kuota, pelamar) selalu sebutkan sebagai potret tanggal scrape.

## 7. Batasan

- Data adalah potret (snapshot) saat scrape; jumlah pelamar & kuota di situs
  berubah terus. Untuk angka paling segar gunakan dashboard / scrape ulang.
- Jangan mengarang lowongan, perusahaan, atau angka di luar file-file ini.
- File HTML mentah adalah bukti sumber bila ada angka yang dipertanyakan.
