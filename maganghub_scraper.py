#!/usr/bin/env python3
"""
Webscraper MagangHub Kemnaker - lowongan Magang Nasional
Filter: Program Studi Informatika + Ilmu Informatika, Penyelenggara = Perusahaan

Cara kerja:
- Mengambil BODY HTML tiap halaman listing (Next.js SSR): page=1,2,3,...
  HTML tiap page disimpan ke folder html_pages/.
- Di dalam HTML ada data JSON `initialVacancies` (lowongan + meta pagination)
  yang di-parse jadi baris lowongan.
- Situs sedang RAMAI: kadang server mengembalikan halaman "kosong" (HTML kecil
  tanpa data) secara acak. Itu dianggap gangguan sesaat -> page di-retry dengan
  jeda panjang, BUKAN dianggap akhir data.
- Berhenti HANYA saat: server mengembalikan 404, atau page melewati lastPage
  dari meta DAN page berikutnya terkonfirmasi kosong/404, atau page terkonfirmasi
  kosong berulang kali setelah melewati lastPage.
- Timeout longgar: connect 20s, read 180s. Jeda antar halaman 4-8 detik.
"""
import json, re, time, random
from pathlib import Path
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
import requests

START_URL = ("https://maganghub.kemnaker.go.id/magang-nasional/lowongan"
    "?study_program%5B0%5D%5Bid%5D=0b074455-5cb4-45c4-8111-1a9e3b6de1c0"
    "&study_program%5B0%5D%5Blabel%5D=Informatika"
    "&study_program%5B1%5D%5Bid%5D=b65a25f2-988f-40f8-9dfd-c1c097560e41"
    "&study_program%5B1%5D%5Blabel%5D=Ilmu%20Informatika"
    "&organizer_type%5Bid%5D=company&organizer_type%5Blabel%5D=Perusahaan&page=1")

OUT = Path(__file__).parent
HTML_DIR = OUT / "html_pages"; HTML_DIR.mkdir(exist_ok=True)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
    "Referer": "https://maganghub.kemnaker.go.id/magang-nasional/lowongan",
    "Accept-Encoding": "identity",
}
CONNECT_TIMEOUT = 20
READ_TIMEOUT = 180
FETCH_RETRIES = 6        # untuk error jaringan / 5xx / 429
EMPTY_RETRIES = 8        # untuk halaman kosong sesaat (server sibuk)
PAGE_DELAY = (4, 8)
MAX_PAGES = 300

def build_url(page: int) -> str:
    u = urlparse(START_URL)
    q = dict(parse_qsl(u.query)); q["page"] = str(page)
    return urlunparse(u._replace(query=urlencode(q)))

def fetch_html(session, url):
    last_err = None
    for attempt in range(1, FETCH_RETRIES + 1):
        try:
            r = session.get(url, headers=HEADERS, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))
            if r.status_code == 404:
                return 404, ""
            if r.status_code >= 500 or r.status_code == 429:
                raise requests.HTTPError(f"HTTP {r.status_code}")
            r.raise_for_status()
            return r.status_code, r.text
        except Exception as e:
            last_err = e
            wait = min(15 * attempt, 90) + random.uniform(0, 5)
            print(f"    jaringan: percobaan {attempt}/{FETCH_RETRIES} gagal ({type(e).__name__}); tunggu {wait:.0f}s...", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"Gagal jaringan setelah {FETCH_RETRIES}x: {last_err}")

def parse_initial_vacancies(html: str):
    """Decode payload RSC Next.js (self.__next_f.push) lalu parse JSON initialVacancies."""
    dec = json.JSONDecoder()
    parts = []; idx = 0
    while True:
        i = html.find('self.__next_f.push([1,', idx)
        if i == -1: break
        j = html.find('"', i)
        if j == -1: break
        try:
            s, end = dec.raw_decode(html[j:])
            parts.append(s); idx = j + end
        except Exception:
            idx = j + 1
    full = ''.join(parts) if parts else html
    i = full.find('"initialVacancies":')
    if i == -1: return None
    start = full.find('{', i)
    depth = 0; in_str = False; esc = False
    for j in range(start, len(full)):
        c = full[j]
        if in_str:
            if esc: esc = False
            elif c == chr(92): esc = True
            elif c == '"': in_str = False
        else:
            if c == '"': in_str = True
            elif c == '{': depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    try: return json.loads(full[start:j+1])
                    except Exception: return None
    return None

def detail_links(html: str):
    links = {}
    for href in re.findall(r'href="(/magang-nasional/lowongan/[^"]+)"', html):
        href = href.replace('&amp;', '&')
        m = re.search(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$', href)
        if m: links[m.group(1)] = "https://maganghub.kemnaker.go.id" + href
    return links

def main():
    session = requests.Session()
    all_rows = {}; metas = []
    known_last_page = None
    page = 1
    while page <= MAX_PAGES:
        url = build_url(page)
        print(f"[page {page}] GET ...&page={page}", flush=True)
        parsed = None; status = None
        for attempt in range(1, EMPTY_RETRIES + 1):
            try:
                status, html = fetch_html(session, url)
            except RuntimeError as e:
                print(f"STOP di page {page}: {e}", flush=True); status = -1; break
            if status == 404:
                break
            candidate = parse_initial_vacancies(html)
            if candidate and candidate.get("data"):
                parsed = candidate
                (HTML_DIR / f"page_{page:03d}.html").write_text(html, encoding="utf-8")
                break
            # halaman kosong sesaat (server sibuk) -> tunggu lama lalu coba lagi
            beyond = known_last_page is not None and page > known_last_page
            if beyond and attempt >= 2:
                break  # sudah melewati lastPage dan 2x kosong: memang habis
            wait = min(20 * attempt, 120) + random.uniform(0, 5)
            print(f"    halaman kosong (percobaan {attempt}/{EMPTY_RETRIES}, ukuran HTML {len(html)}B) - server sibuk? tunggu {wait:.0f}s lalu retry...", flush=True)
            time.sleep(wait)
        if status == 404:
            print(f"STOP: page {page} -> 404 (resource tidak ditemukan)", flush=True); break
        if status == -1:
            break
        if not parsed or not parsed.get("data"):
            print(f"STOP: page {page} terkonfirmasi kosong (lastPage diketahui: {known_last_page})", flush=True); break
        meta = parsed.get("meta", {}); metas.append(meta)
        if meta.get("lastPage"): known_last_page = int(meta["lastPage"])
        links = detail_links(html)
        new_count = 0
        for v in parsed["data"]:
            if v["id"] not in all_rows: new_count += 1
            v["_detailUrl"] = links.get(v.get("id", ""), "")
            v["_page"] = page
            all_rows[v["id"]] = v
        print(f"    OK: {len(parsed['data'])} lowongan ({new_count} baru) | terkumpul {len(all_rows)} unik | meta {meta.get('currentPage')}/{meta.get('lastPage')} total {meta.get('total')}", flush=True)
        if new_count == 0 and known_last_page and page >= known_last_page:
            print("STOP: tidak ada lowongan baru dan sudah di lastPage", flush=True); break
        page += 1
        time.sleep(random.uniform(*PAGE_DELAY))
    rows = list(all_rows.values())
    (OUT / "all_vacancies_raw.json").write_text(json.dumps({"meta_pages": metas, "vacancies": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nSELESAI. Total lowongan unik: {len(rows)}; page terakhir dicoba: {page}; lastPage(meta): {known_last_page}")
    return rows

if __name__ == "__main__":
    main()
