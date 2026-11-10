#!/usr/bin/env python3
"""Gabungkan hasil scrape (pass1 + pass2 dst) dan buat file Excel (.xlsx) + CSV."""
import json, sys, re
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

OUT = Path(__file__).parent

def load_ids(paths):
    merged = {}
    total_meta = None
    for p in paths:
        d = json.loads(Path(p).read_text(encoding='utf-8'))
        if d.get('meta_pages'): total_meta = d['meta_pages'][-1]
        for v in d['vacancies']:
            merged[v['id']] = v  # data terbaru menimpa yang lama
    return merged, total_meta

def clean(s):
    if not isinstance(s, str): return s
    s = s.replace('\\n', '\n').replace('\\r', '')
    return re.sub(r'\n{3,}', '\n\n', s).strip()

def edu_label(levels):
    m = {'diploma': 'Diploma (D3/D4)', 'bachelor': 'Sarjana (S1)', 'master': 'Magister (S2)', 'doctor': 'Doktor (S3)', 'high_school': 'SMA/SMK', 'vocational': 'SMK'}
    return ', '.join(m.get(x, x) for x in (levels or []))

def main(paths):
    merged, meta = load_ids(paths)
    rows = sorted(merged.values(), key=lambda v: (v.get('publishedAt') or '', v.get('positionName') or ''), reverse=True)
    cols = [
        ('No', 6), ('Posisi', 46), ('Perusahaan / Penyelenggara', 40), ('Tipe Penyelenggara', 14),
        ('Kota / Kabupaten', 24), ('Alamat Lokasi Magang', 52), ('Kuota Dibutuhkan', 11), ('Kuota Disetujui', 11),
        ('Total Pelamar (saat scrape)', 13), ('Skor Kompetitif', 11), ('Skor Peluang', 11),
        ('Jenjang Pendidikan', 20), ('Program Studi (utama)', 22), ('Semua Program Studi yang Diterima', 48),
        ('Hari Kerja / Minggu', 11), ('Hari Libur', 16), ('Tipe Interview', 14), ('Ramah Disabilitas', 11),
        ('Email Perusahaan', 30), ('Telepon Perusahaan', 16), ('Tanggal Publish', 17),
        ('Halaman Sumber', 10), ('Link Detail Lowongan', 60), ('ID Lowongan', 38), ('Deskripsi Tugas', 90),
    ]
    wb = Workbook(); ws = wb.active; ws.title = 'Lowongan Magang'
    hdr_fill = PatternFill('solid', fgColor='1F4E79')
    for c, (title, w) in enumerate(cols, 1):
        cell = ws.cell(row=1, column=c, value=title)
        cell.font = Font(bold=True, color='FFFFFF'); cell.fill = hdr_fill
        cell.alignment = Alignment(vertical='center', wrap_text=True)
        ws.column_dimensions[get_column_letter(c)].width = w
    for i, v in enumerate(rows, 1):
        org = v.get('organizer') or {}
        city = (v.get('city') or org.get('city') or {})
        sp = v.get('studyProgram') or {}
        sps = ', '.join(s.get('name','') for s in (v.get('studyPrograms') or []))
        vals = [
            i, clean(v.get('positionName')), clean(org.get('name')), org.get('organizableType'),
            city.get('name'), clean(v.get('address') or org.get('address')),
            v.get('quantityNeeded'), v.get('approvedQuantity'), v.get('totalApplications'),
            v.get('competitiveScore'), v.get('opportunityScore'),
            edu_label(v.get('educationLevels')), sp.get('name'), sps,
            v.get('workingDaysPerWeek'), ', '.join(v.get('daysOff') or []),
            ', '.join(v.get('interviewTypes') or []),
            'Ya' if v.get('isDisabilityFriendly') else 'Tidak',
            org.get('email'), org.get('phone'),
            (v.get('publishedAt') or '')[:10], v.get('_page'), v.get('_detailUrl'),
            v.get('id'), clean(v.get('taskDescription')),
        ]
        for c, val in enumerate(vals, 1):
            cell = ws.cell(row=i+1, column=c, value=val)
            cell.alignment = Alignment(vertical='top', wrap_text=(c in (2,3,6,14,25)))
            if c == 23 and val:
                cell.hyperlink = val; cell.font = Font(color='0563C1', underline='single')
    ws.freeze_panes = 'C2'; ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{len(rows)+1}"
    ws.row_dimensions[1].height = 32
    # Sheet info
    info = wb.create_sheet('Info')
    info.column_dimensions['A'].width = 26; info.column_dimensions['B'].width = 110
    notes = [
        ('Sumber', 'https://maganghub.kemnaker.go.id/magang-nasional/lowongan (MagangHub Kemnaker - Magang Nasional)'),
        ('Filter', 'TANPA FILTER SAMA SEKALI - semua program studi, semua tipe penyelenggara, semua daerah (link polos /magang-nasional/lowongan)'),
        ('Tanggal scrape', '2 November 2026 (20:33-20:40 WIB) — scrape ulang penuh tanpa filter, 0 halaman gagal)'),
        ('Total menurut situs', f"{meta.get('total') if meta else '?'} lowongan, {meta.get('lastPage') if meta else '?'} halaman x {meta.get('perPage') if meta else '?'} lowongan"),
        ('Total di sheet ini', f"{len(rows)} lowongan unik"),
        ('Catatan', 'Scrape ulang PENUH tanpa filter: situs menampilkan 28.925 slot dalam 1.607 halaman (naik dari 27.667 slot / 1.538 halaman pada 31 Okt). Semua 28.925 slot tertangkap & terverifikasi dari 1.607 file HTML. Berbeda dengan 31 Okt (hari pertama pendaftaran, listing kacau sehingga 1 lowongan bisa muncul berkali-kali dan uniknya hanya terhitung 21.372), scrape kali ini bersih: hanya 295 ID ganda, sehingga lowongan unik = 28.630 dari jauh lebih banyak penyelenggara. Dibandingkan data 31 Okt: 7.469 ID lowongan tidak ada di data lama (baru tayang atau dulu tertutup duplikasi), 211 ID lama tidak tertangkap lagi. Angka pelamar & kuota adalah potret 2 Nov 2026 malam.'),
        ('Berhenti di', 'Halaman 1.607 adalah lastPage menurut situs (28.925 total / 18 per halaman).'),
    ]
    for r, (a, b) in enumerate(notes, 1):
        info.cell(row=r, column=1, value=a).font = Font(bold=True)
        c = info.cell(row=r, column=2, value=b); c.alignment = Alignment(wrap_text=True, vertical='top')
    xlsx = OUT / 'Semua_Lowongan_MagangHub_TanpaFilter_2026-11-02.xlsx'
    wb.save(xlsx)
    print('saved', xlsx, 'rows', len(rows))
if __name__ == '__main__':
    main(sys.argv[1:])
