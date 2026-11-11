# Analisis G-value

Kode Python untuk mengolah output TOPAS-nBio (scorer `TsIRTInterPulse`) di folder `../Result`.

## Cara kerja

Tiap file `*_seedN.phsp` berisi kolom: jumlah molekul `N`, waktu `t` [ps], nama molekul,
dan energi terdeposit kumulatif `E` [eV]. G-value dihitung sebagai

    G(t) = N(t) / (E(t) / 100)      [molekul / 100 eV]

lalu dirata-rata antar 100 seed per kondisi. Folder kondisi dicari otomatis
(semua folder di `Result/` yang berisi `*_seedN.phsp`), jadi kondisi baru langsung ikut terolah.

## File

| File | Isi |
|---|---|
| `gvalue_utils.py` | Fungsi bersama: cari file, baca .phsp, hitung G, cache. Satuan waktu diatur di `SATUAN_WAKTU` (default µs). |
| `1_grafik_gvalue_vs_waktu.py` | Grafik G-value vs waktu per kondisi (rata-rata ± 1 SD) dan perbandingan antar kondisi per grup. CSV kurva rata-rata juga disimpan. |
| `2_rata_rata_gvalue.py` | Rata-rata G-value: (a) rata-rata terhadap waktu, (b) G pada akhir observasi. Masing-masing mean ± SD/SEM antar seed. |
| `3_gvalue_maksimal.py` | G-value maksimal: (a) puncak kurva rata-rata + waktu puncak, (b) puncak per seed lalu dirata-rata. |

## Menjalankan

```bash
pip install numpy pandas matplotlib
python 1_grafik_gvalue_vs_waktu.py
python 2_rata_rata_gvalue.py
python 3_gvalue_maksimal.py
```

Opsi (semua skrip): `--grup jumlahpulsa lebarpulsa "Interval Pulse"`, `--molekul OH^0 e_aq^-1 H2O2^0`.
Skrip 2 juga punya `--tmin` dan `--tmax` (satuan `SATUAN_WAKTU`) untuk membatasi jendela rata-rata.

## Output

- `output/grafik/per_kondisi/` – G vs waktu tiap kondisi
- `output/grafik/perbandingan_grup/` – G vs waktu, semua kondisi dalam satu grup
- `output/grafik/rata_rata/`, `output/grafik/maksimal/` – grafik batang
- `output/tabel/Gvalue_vs_waktu/*.csv` – kurva rata-rata, SD, SEM per molekul
- `output/tabel/Gvalue_rata_rata.csv`, `output/tabel/Gvalue_maksimal.csv`

`cache/` menyimpan data yang sudah dibaca (.npz) agar run berikutnya cepat. Cache diperbarui
otomatis jika file di `Result/` berubah; folder ini boleh dihapus kapan saja.

## Catatan interpretasi

- Pada waktu awal (~1 ps) energi terdeposit per seed masih kecil, sehingga G antar seed sangat
  bervariasi (SD besar, pita ± SD bisa turun di bawah nol). Untuk nilai maksimal, **puncak kurva
  rata-rata** lebih representatif daripada rata-rata puncak per seed, yang ikut membesar karena noise.
- Titik waktu TOPAS berskala logaritmik, jadi "rata-rata terhadap waktu" setara dengan rata-rata
  pada skala log(waktu). Untuk G-value akhir/steady state, pakai kolom `G_akhir`.
- Urutan baris dalam file .phsp tidak selalu urut waktu; kode mengurutkannya per molekul.
- Molekul yang selalu nol (HO₂•, O₂•⁻, O₂) tidak ditampilkan di grafik, tetapi tetap ada di tabel CSV.
