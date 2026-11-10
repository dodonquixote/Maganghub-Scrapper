# MagangHub Scraper & Rekomendasi Lowongan

Kumpulan script Python untuk mengambil (scraping) seluruh lowongan dari
MagangHub Kemnaker (Magang Nasional), menyusunnya menjadi sheet Excel, dan
memeringkat lowongan berdasarkan kecocokan dengan profil/CV (skoring relevansi
skill, probabilitas pelamar vs kuota, lokasi, dan nilai pengembangan skill).

## Isi
- `maganghub_scraper.py` — scraper listing MagangHub terfilter (mengambil data
  JSON `initialVacancies` yang tertanam di payload halaman Next.js).
- `scraper_semua_lowongan.py` — scraper paralel (16 worker) untuk SEMUA
  lowongan tanpa filter (1.607 halaman, 28.925 slot per 2 Nov 2026).
- `build_sheet.py` — membangun sheet Excel dari data mentah hasil scrape.
- `matching_cv.py` + `build_rekomendasi.py` — pencocokan lowongan dengan
  profil CV (5 klaster skill) dan pembuatan sheet rekomendasi teranking.
- `KNOWLEDGE.md` — dokumentasi lengkap: peta data, skema JSON/Excel, metode.

## Catatan
Data lowongan adalah milik MagangHub Kemnaker; script ini hanya alat
pengambilan & analisis data publik untuk keperluan pribadi.
