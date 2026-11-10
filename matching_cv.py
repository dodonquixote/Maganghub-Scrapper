import json, re
from collections import Counter, defaultdict

DATA = 'all_vacancies_raw.json'
d = json.load(open(DATA))
rows = d['vacancies']

# Klaster skill berdasarkan CV Salman:
# target utama DevOps; kuat di automation (n8n/Selenium/API), backend (Python/REST/SQL),
# ML/data, plus infra/lab ops (server, network, hardware). Golang intermediate juga ada.
CLUSTERS = {
 'DevOps & Infrastruktur IT': ['devops','infrastruktur','infrastructure','server','linux','docker','cloud','sysadmin','system administrator','administrator sistem','network engineer','jaringan','network','it infrastructure','infrastruktur it','deployment','ci/cd','virtualisasi','mikrotik','cisco'],
 'Automation & Integrasi API': ['otomasi','automation','n8n','workflow','rpa','selenium','integrasi api','integrasi sistem','chatbot','otomatisasi'],
 'Backend & Software Development': ['backend','back-end','back end','software developer','software engineer','web developer','fullstack','full-stack','full stack','programmer','pengembang perangkat lunak','pengembang aplikasi','developer','python','django','golang','laravel','rest api','api developer','software development','web development','frontend','front-end','mobile developer','android developer'],
 'Data & Machine Learning': ['machine learning','data scientist','data analyst','data engineer','analisis data','pengolahan data','data processing','artificial intelligence','kecerdasan buatan',' ai ','deep learning','data mining','big data','business intelligence','data science','analis data','pengolah data'],
 'IT Support & Operasional IT': ['it support','technical support','helpdesk','help desk','teknisi','it staff','staff it','staf it','it officer','sistem informasi','information technology','teknologi informasi','database','sql','data entry','pengelola data','administrator database','it admin','admin it','sistem komputer','teknik komputer','pemeliharaan sistem','pengelolaan sistem','operator komputer','aplikasi'],
}
NEGATIVE = ['sales','marketing','akuntansi','accounting','keuangan','finance','customer service','call center','desain grafis','graphic design','content creator','video editor','human resource','hrd','legal','hukum','sekretaris','resepsionis','kasir','gudang','warehouse','produksi','operator produksi','kurir','driver','satpam','kebersihan','arsiparis','kearsipan','perpustakaan','tata usaha','administrasi umum','administrasi perkantoran','administrasi keuangan','pajak','perbankan','teller','administrasi kepatuhan','administrasi bisnis','administrasi publik']

def norm(s): return ' ' + re.sub(r'\s+',' ', (s or '').lower()) + ' '

def cluster_scores(v):
    name = norm(v.get('positionName'))
    desc = norm(v.get('taskDescription'))
    out = {}
    for cl, kws in CLUSTERS.items():
        s = 0.0; hits=[]
        for kw in kws:
            kn = ' ' + kw + ' ' if len(kw)<=3 else kw
            if kw in name: s += 3; hits.append(kw+'(posisi)')
            elif kn in name: s += 3; hits.append(kw+'(posisi)')
            if kw in desc: s += 1
        out[cl] = (s, hits)
    return out

results = []
for v in rows:
    cs = cluster_scores(v)
    best_cl = max(cs, key=lambda k: cs[k][0])
    best = cs[best_cl][0]
    second = sorted([cs[k][0] for k in cs], reverse=True)[1]
    relevance = best + 0.4*second
    name_l = norm(v.get('positionName'))
    neg = any(n in name_l for n in NEGATIVE)
    quota = v.get('approvedQuantity') or v.get('quantityNeeded') or 0
    apps = v.get('totalApplications') or 0
    ratio = (apps/quota) if quota else 99
    results.append({'v': v, 'cluster': best_cl, 'relevance': relevance, 'best': best, 'neg': neg, 'ratio': ratio, 'hits': cs[best_cl][1]})

for th in [3,4,5,6,7,8]:
    sel=[r for r in results if r['relevance']>=th and not r['neg']]
    seln=[r for r in results if r['relevance']>=th]
    print(f'threshold {th}: relevan {len(seln)} (tanpa negatif {len(sel)})')
sel=[r for r in results if r['relevance']>=5 and not r['neg']]
print('\ndistribusi klaster (relevansi>=5, non-negatif):', Counter(r['cluster'] for r in sel))
print('rasio pelamar/kuota pada yang relevan: 0 pelamar:', sum(1 for r in sel if (r['v'].get('totalApplications') or 0)==0), '| rasio<0.5:', sum(1 for r in sel if r['ratio']<0.5), '| rasio<1:', sum(1 for r in sel if r['ratio']<1))
print('\ncontoh top 25:')
for r in sorted(sel, key=lambda x:-x['relevance'])[:25]:
    v=r['v']; print(f"{r['relevance']:.0f} [{r['cluster'][:22]}] {v.get('positionName')} @ {(v.get('organizer') or {}).get('name')} - {(v.get('city') or {}).get('name')} kuota {v.get('approvedQuantity')} pelamar {v.get('totalApplications')}")
print('\ncek negatif yang lolos klaster tinggi (sampel):')
for r in sorted([r for r in results if r['relevance']>=6 and r['neg']], key=lambda x:-x['relevance'])[:10]:
    print(' NEG', r['v'].get('positionName'))
print('\nsampel relevansi 4-5.9 non-negatif:')
for r in sorted([r for r in results if 4<=r['relevance']<6 and not r['neg']], key=lambda x:-x['relevance'])[:15]:
    v=r['v']; print(f" {r['relevance']:.1f} {v.get('positionName')} @ {(v.get('organizer') or {}).get('name')}")
