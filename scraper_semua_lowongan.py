#!/usr/bin/env python3
"""
Scraper SEMUA lowongan MagangHub (TANPA filter apapun).
1.538 halaman x 18 = 27.667 slot (meta per 31 Okt 2026 10:07).
Dijalankan paralel 8 worker; tiap page disimpan HTML-nya ke html_pages/.
Page yang gagal dicatat ke failed_pages.txt untuk disapu ulang (pass berikutnya).
"""
import json, re, time, random, sys, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests

BASE = "https://maganghub.kemnaker.go.id/magang-nasional/lowongan?page={}"
OUT = Path(__file__).parent
HTML_DIR = OUT / "html_pages"; HTML_DIR.mkdir(exist_ok=True)
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
           "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
           "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
           "Accept-Encoding": "identity",
           "Referer": "https://maganghub.kemnaker.go.id/magang-nasional/lowongan"}
WORKERS = 16
print_lock = threading.Lock()
done_count = 0

def parse_initial_vacancies(html):
    dec = json.JSONDecoder(); parts=[]; idx=0
    while True:
        i = html.find('self.__next_f.push([1,', idx)
        if i == -1: break
        j = html.find('"', i)
        if j == -1: break
        try:
            s, end = dec.raw_decode(html[j:]); parts.append(s); idx = j+end
        except Exception: idx = j+1
    full = ''.join(parts) if parts else html
    i = full.find('"initialVacancies":')
    if i == -1: return None
    start = full.find('{', i); depth=0; in_str=False; esc=False
    for j in range(start, len(full)):
        c = full[j]
        if in_str:
            if esc: esc=False
            elif c == chr(92): esc=True
            elif c == '"': in_str=False
        else:
            if c == '"': in_str=True
            elif c == '{': depth+=1
            elif c == '}':
                depth-=1
                if depth==0:
                    try: return json.loads(full[start:j+1])
                    except Exception: return None
    return None

def detail_links(html):
    links={}
    for href in re.findall(r'href="(/magang-nasional/lowongan/[^"]+)"', html):
        href=href.replace('&amp;','&')
        m=re.search(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$', href)
        if m: links[m.group(1)]="https://maganghub.kemnaker.go.id"+href
    return links

def fetch_page(page):
    """Return dict page->parsed rows or None if failed after retries."""
    sess = requests.Session()
    url = BASE.format(page)
    for attempt in range(1, 5):  # 4 percobaan di pass utama; sisa disapu pass berikutnya
        try:
            r = sess.get(url, headers=HEADERS, timeout=(20, 180))
            if r.status_code == 404:
                return {'page': page, 'status': '404', 'data': []}
            if r.status_code >= 500 or r.status_code == 429:
                raise requests.HTTPError(f"HTTP {r.status_code}")
            r.raise_for_status()
            parsed = parse_initial_vacancies(r.text)
            if parsed and parsed.get('data'):
                (HTML_DIR / f"page_{page:04d}.html").write_text(r.text, encoding='utf-8')
                links = detail_links(r.text)
                for v in parsed['data']:
                    v['_detailUrl'] = links.get(v.get('id',''), ''); v['_page'] = page
                return {'page': page, 'status': 'ok', 'data': parsed['data'], 'meta': parsed.get('meta', {})}
        except Exception:
            pass
        time.sleep(min(6*attempt, 25) + random.uniform(0, 3))
    return None

def main():
    start_page = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    end_page = int(sys.argv[2]) if len(sys.argv) > 2 else 1538
    # lewati page yang HTML-nya sudah tersimpan (resume)
    todo = [p for p in range(start_page, end_page+1) if not (HTML_DIR / f"page_{p:04d}.html").exists()]
    print(f"range {start_page}-{end_page}; sudah ada {end_page-start_page+1-len(todo)}; akan diambil {len(todo)} page; workers {WORKERS}", flush=True)
    results = {}; failed = []
    global done_count
    def run(page):
        global done_count
        res = fetch_page(page)
        with print_lock:
            done_count += 1
            if res and res['status'] in ('ok','404'): results[page] = res
            else: failed.append(page)
            if done_count % 50 == 0 or res is None:
                print(f"progress {done_count}/{len(todo)} | sukses {len(results)} gagal {len(failed)} (page {page}: {'OK' if res else 'GAGAL'})", flush=True)
        time.sleep(random.uniform(0.3, 1.2))
        return res
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        list(ex.map(run, todo))
    (OUT / 'failed_pages.txt').write_text('\n'.join(map(str, sorted(failed))), encoding='utf-8')
    rows = []
    for p in sorted(results):
        if results[p]['status'] == 'ok': rows.extend(results[p]['data'])
    (OUT / f'raw_{start_page}_{end_page}.json').write_text(json.dumps(rows, ensure_ascii=False), encoding='utf-8')
    print(f"SELESAI range {start_page}-{end_page}: {len(results)} page sukses, {len(failed)} gagal, {len(rows)} slot terkumpul", flush=True)

if __name__ == '__main__':
    main()
