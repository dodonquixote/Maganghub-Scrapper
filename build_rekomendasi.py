#!/usr/bin/env python3
import json, re
from collections import Counter
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

exec(open('matching_cv.py').read().split('results = []')[0])  # ambil CLUSTERS, NEGATIVE, norm, cluster_scores, rows

def location_points(city_name):
    c = (city_name or '').lower()
    if 'bogor' in c: return 10, 'Domisili (Bogor)'
    if 'depok' in c: return 9, 'Dekat (Depok)'
    if 'jakarta' in c: return 8, 'Komuter (Jakarta)'
    if 'bekasi' in c: return 7, 'Komuter (Bekasi)'
    if 'tangerang' in c: return 7, 'Komuter (Tangerang)'
    if any(x in c for x in ['bandung','cimahi','sumedang','karawang','purwakarta','sukabumi','cianjur','garut','tasikmalaya','cirebon','indramayu','subang','majalengka','kuningan','ciamis','banjar','pangandaran']): return 4, 'Jawa Barat lain'
    return 2, 'Luar Jabodetabek/Jabar'

GROWTH = {'DevOps & Infrastruktur IT':10,'Automation & Integrasi API':10,'Backend & Software Development':9,'Data & Machine Learning':9,'IT Support & Operasional IT':6}

items = []
for v in rows:
    cs = cluster_scores(v)
    best_cl = max(cs, key=lambda k: cs[k][0])
    ranked = sorted([cs[k][0] for k in cs], reverse=True)
    relevance = ranked[0] + 0.4*ranked[1]
    name_l = norm(v.get('positionName'))
    if relevance < 5 or any(n in name_l for n in NEGATIVE): continue
    quota = v.get('approvedQuantity') or v.get('quantityNeeded') or 0
    apps = v.get('totalApplications') or 0
    ratio = (apps/quota) if quota else 99
    prob_idx = quota/(quota+apps) if (quota+apps) > 0 else 0
    if apps == 0: plabel = 'Sangat tinggi (belum ada pelamar)'
    elif ratio <= 0.5: plabel = 'Sangat tinggi'
    elif ratio <= 1: plabel = 'Tinggi'
    elif ratio <= 2: plabel = 'Sedang-tinggi'
    elif ratio <= 4: plabel = 'Sedang'
    elif ratio <= 8: plabel = 'Rendah'
    else: plabel = 'Sangat rendah'
    city = (v.get('city') or {}).get('name') or ((v.get('organizer') or {}).get('city') or {}).get('name')
    lpts, larea = location_points(city)
    skor = round(min(relevance/12,1)*55 + prob_idx*25 + lpts + GROWTH[best_cl]*0.0 + (GROWTH[best_cl]/10)*10, 1)
    # rumus final: relevansi 55 + probabilitas 25 + lokasi 10 + nilai pengembangan skill 10
    items.append({'v': v, 'cluster': best_cl, 'relevance': round(relevance,1), 'quota': quota, 'apps': apps,
                  'ratio': round(ratio,2), 'prob': plabel, 'prob_idx': round(prob_idx,2), 'city': city,
                  'larea': larea, 'growth': GROWTH[best_cl], 'skor': skor})
items.sort(key=lambda x: (-x['skor'], x['ratio']))
for i, it in enumerate(items, 1):
    it['rank'] = i
    it['prioritas'] = 'Prioritas Utama' if i <= 30 else ('Sangat Relevan' if it['skor'] >= 62 else 'Relevan')

wb = Workbook(); ws = wb.active; ws.title = 'Rekomendasi Lowongan'
cols = [('Rank',7),('Prioritas',16),('Skor Akhir (0-100)',11),('Klaster Skill',26),('Posisi',44),('Perusahaan / Penyelenggara',38),('Tipe',11),('Kota',22),('Area dari Cibinong',18),('Kuota',7),('Pelamar',8),('Pelamar per Kuota',11),('Peluang (estimasi)',24),('Skor Kompetitif Situs',11),('Skor Peluang Situs',11),('Tanggal Publish',13),('Link Detail',55),('Deskripsi Tugas',85)]
hfill = PatternFill('solid', fgColor='1F4E79'); pfill = PatternFill('solid', fgColor='FFF2CC')
for c,(t,w) in enumerate(cols,1):
    cell=ws.cell(row=1,column=c,value=t); cell.font=Font(bold=True,color='FFFFFF'); cell.fill=hfill
    cell.alignment=Alignment(vertical='center',wrap_text=True); ws.column_dimensions[get_column_letter(c)].width=w
for it in items:
    v=it['v']; org=v.get('organizer') or {}
    vals=[it['rank'],it['prioritas'],it['skor'],it['cluster'],re.sub(r'\\n',' ',v.get('positionName') or ''),org.get('name'),org.get('organizableType'),it['city'],it['larea'],it['quota'],it['apps'],it['ratio'],it['prob'],v.get('competitiveScore'),v.get('opportunityScore'),(v.get('publishedAt') or '')[:10],v.get('_detailUrl'),re.sub(r'\s+',' ',(v.get('taskDescription') or '').replace('\\n',' '))]
    for c,val in enumerate(vals,1):
        cell=ws.cell(row=it['rank']+1,column=c,value=val)
        cell.alignment=Alignment(vertical='top',wrap_text=(c in (5,6,18)))
        if it['prioritas']=='Prioritas Utama': cell.fill=pfill
        if c==17 and val: cell.hyperlink=val; cell.font=Font(color='0563C1',underline='single')
ws.freeze_panes='A2'; ws.auto_filter.ref=f"A1:{get_column_letter(len(cols))}{len(items)+1}"; ws.row_dimensions[1].height=32

# sheet statistik
st = wb.create_sheet('Statistik & Metodologi')
st.column_dimensions['A'].width=34; st.column_dimensions['B'].width=105
def add(r,a,b,bold=False):
    st.cell(row=r,column=1,value=a).font=Font(bold=True)
    c=st.cell(row=r,column=2,value=b); c.alignment=Alignment(wrap_text=True,vertical='top'); 
    if bold: c.font=Font(bold=True)
lines=[
 ('Profil dari CV','Salman Alfarizi Taha - fresh graduate Informatika Gunadarma (2022-2026, IPK 3,35), domisili Cibinong, Bogor. Target di CV: posisi entry-level DevOps. Kekuatan: Python, REST API, SQL, n8n, Selenium, otomasi workflow & integrasi API pihak ketiga, manajemen server/infrastruktur, operasi PC & jaringan (asisten lab), backend (RESTful API + database), machine learning & pengolahan data, Golang intermediate.'),
 ('Sumber data','1.245 lowongan unik MagangHub (scrape 31 Okt 2026 pagi, filter Ilmu Informatika + Informatika + Manajemen Informatika, semua penyelenggara).'),
 ('Lowongan relevan lolos saringan', f"{len(items)} dari 1.245 ({len(items)/1245*100:.1f}%). Ambang: skor relevansi >= 5 dari pencocokan kata kunci nama posisi (bobot 3x) + deskripsi tugas (1x), dan bukan posisi non-IT (sales, akuntansi, admin umum, dll)."),
 ('Distribusi klaster (yang relevan)','; '.join(f"{k}: {n}" for k,n in Counter(i['cluster'] for i in items).most_common())),
 ('Distribusi peluang (yang relevan)','; '.join(f"{k}: {n}" for k,n in Counter(i['prob'] for i in items).most_common())),
 ('Yang relevan & belum ada pelamar', f"{sum(1 for i in items if i['apps']==0)} lowongan"),
 ('Yang relevan di Jabodetabek+Bogor', f"{sum(1 for i in items if i['larea'].startswith(('Domisili','Dekat','Komuter')))} dari {len(items)}"),
 ('Rumus Skor Akhir','Relevansi skill (maks 55) + Probabilitas diterima dari rasio pelamar/kuota (maks 25) + Kedekatan lokasi dari Cibinong (maks 10) + Nilai pengembangan skill sesuai target DevOps/automation/backend/ML di CV (maks 10).'),
 ('Arti estimasi peluang','Berdasarkan rasio pelamar per kuota saat data diambil: 0 pelamar atau <=0,5 = Sangat tinggi; <=1 = Tinggi; <=2 = Sedang-tinggi; <=4 = Sedang; <=8 = Rendah; >8 = Sangat rendah. Ini estimasi kasar dari data publik situs (jumlah pelamar & kuota), bukan jaminan - faktor seleksi berkas, tes, dan wawancara tidak terlihat dari data ini.'),
 ('Catatan waktu','Pelamaran MagangHub Batch 3 dilaporkan dibuka 31 Okt - 4 Nov 2026 (dari pemberitaan; cek situs untuk kepastian). Prioritaskan 30 baris teratas (highlight kuning, "Prioritas Utama").'),
]
for r,(a,b) in enumerate(lines,1): add(r,a,b)
out='Rekomendasi_Lowongan_MagangHub.xlsx'
wb.save(out)
print('saved', out, 'rows', len(items))
print('TOP15:')
for it in items[:15]:
    v=it['v']; print(f"{it['rank']}. [{it['skor']}] {v.get('positionName')} @ {(v.get('organizer') or {}).get('name')} - {it['city']} | kuota {it['quota']} pelamar {it['apps']} ({it['prob']}) | {it['cluster']}")
print('stats cluster', Counter(i['cluster'] for i in items))
print('stats prob', Counter(i['prob'] for i in items))
print('jabodetabek+bogor', sum(1 for i in items if i['larea'].startswith(('Domisili','Dekat','Komuter'))))
print('nol pelamar', sum(1 for i in items if i['apps']==0))
