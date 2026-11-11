# Simulasi G-value Radiolisis Air pada Iradiasi Proton Berpulsa (TOPAS-nBio)

Repositori ini berisi file parameter simulasi, data hasil, dan kode analisis untuk tesis
tentang pengaruh struktur pulsa (lebar pulsa, interval/frekuensi pulsa, dan jumlah pulsa)
terhadap G-value spesies radiolisis air. Simulasi dijalankan dengan
[TOPAS](https://www.topasmc.org/) + TOPAS-nBio (Geant4-DNA). Scorer yang dipakai adalah `TsIRTInterPulse`.

## Struktur folder

```
Tesis/
├── Parameter/          # file input TOPAS per kondisi (+ skrip run100.sh untuk 100 seed)
│   ├── lebarpulsa/     # variasi lebar pulsa
│   ├── Interval Pulse/ # variasi interval (frekuensi) pulsa
│   └── jumlahpulsa/    # variasi jumlah pulsa (Flash vs konvensional)
├── Result/             # output TOPAS: <nama>_seedN.phsp + .header (100 seed per kondisi)
├── Analisis_Gvalue/    # kode Python analisis G-value + output grafik & tabel
├── requirements.txt
└── README.md
```

Setiap folder kondisi di `Parameter/` berisi:
- `*_1seed.txt` – file input dasar TOPAS
- `run_seed_N.txt` – input per seed (N = 1–100), dibuat oleh `run100.sh`
- `TOPASChemistry.txt`, `TOPASDNAReactions.txt`, `TOPASDefaultReactions.txt` – parameter kimia
- `TopasParameterDump_Run_0000.html` – dump parameter lengkap dari TOPAS

## Kondisi simulasi

Parameter yang sama untuk semua kondisi: proton dalam bola air berjari-jari 1 µm,
dosis preskripsi 10 Gy per kondisi, distribusi pulsa `Uniform`, dan 100 seed (1–100).
Molekul yang dicatat: •OH, e⁻aq, H₃O⁺, H₂O₂, H•, H₂, OH⁻, O₂•⁻, HO₂•, O₂.

| Grup | Kondisi | Energi | Jumlah pulsa | Frekuensi | Lebar pulsa (FWHM) | Waktu akhir observasi |
|---|---|---|---|---|---|---|
| lebarpulsa | lebar10ps | 100 MeV | 10 | 100 Hz | 10 ps | 1,2×10⁵ µs |
| lebarpulsa | lebar10ns | 100 MeV | 10 | 100 Hz | 10 ns | 1,2×10⁵ µs |
| lebarpulsa | lebar10us | 100 MeV | 10 | 100 Hz | 10 µs | 1,2×10⁵ µs |
| lebarpulsa | lebar10ms | 100 MeV | 10 | 100 Hz | 10 ms | 1,2×10⁵ µs |
| Interval Pulse | interval1us | 100 MeV | 10 | 1 MHz | 10 µs | 25 µs |
| Interval Pulse | interval100us | 100 MeV | 10 | 10 kHz | 10 µs | 1,2×10³ µs |
| Interval Pulse | interval10ms | 100 MeV | 10 | 100 Hz | 10 µs | 1,2×10⁵ µs |
| Interval Pulse | interval100ms | 100 MeV | 10 | 10 Hz | 10 µs | 1,2×10⁶ µs |
| Interval Pulse | interval1s | 100 MeV | 10 | 1 Hz | 10 µs | 1,2×10⁷ µs |
| jumlahpulsa | Flash | 100 MeV | 10 | 100 Hz | 10 µs | 1,2×10⁵ µs |
| jumlahpulsa | konvensional | 30 MeV* | 1000 | 100 Hz | 10 µs | 0,09 s |

\* Nilai dari `run_seed_N.txt` (input yang benar-benar dijalankan). File dasar
`lebarpulsa_10ms_1seed.txt` di folder konvensional masih tertulis 100 MeV.

## Menjalankan simulasi

Butuh TOPAS dengan ekstensi TOPAS-nBio (scorer `TsIRTInterPulse`). Dari folder kondisi di `Parameter/`, jalankan:

```bash
bash run100.sh
```

Skrip ini membuat `run_seed_1.txt` … `run_seed_100.txt` dari file input dasar (variabel
`INPUT` di skrip), lalu menjalankan `topas` untuk tiap seed. Output (`.phsp` + `.header`)
kemudian dipindahkan ke folder yang sesuai di `Result/`.

## Analisis G-value

```bash
pip install -r requirements.txt
cd Analisis_Gvalue
python 1_grafik_gvalue_vs_waktu.py   # grafik G-value vs waktu
python 2_rata_rata_gvalue.py         # nilai rata-rata G-value
python 3_gvalue_maksimal.py          # nilai G-value maksimal
```

G-value dihitung sebagai G(t) = N(t) / (E(t)/100) [molekul/100 eV], lalu dirata-rata
antar 100 seed. Detail metode dan output ada di [Analisis_Gvalue/README.md](Analisis_Gvalue/README.md).

## Format data hasil (`Result/*.phsp`)

File ASCII dengan 4 kolom (lihat `.header`):

| Kolom | Isi | Satuan |
|---|---|---|
| 1 | TotalNumberOfSpeciesAtTime (jumlah molekul) | – |
| 2 | Time | ps |
| 3 | MoleculeName | – |
| 4 | EnergyDeposit (kumulatif) | eV |

## Catatan

- File hasil folder `Result/jumlahpulsa/Flash` diganti namanya dari `lebarpulsa_10us_seedN`
  menjadi `flash_seedN`, dan folder konvensional dari `konv_30mev_seedN` menjadi
  `konvensional_seedN`. `run_seed_N.txt` masih memakai nama output lama.

## Penulis

<!-- Lengkapi: nama, program studi, universitas, pembimbing, tahun -->
Dewi Riskiana – Tesis, [Program Studi], [Universitas], [Tahun].

## Lisensi

<!-- Pilih lisensi lalu tambahkan file LICENSE (mis. MIT untuk kode, CC BY 4.0 untuk data). -->
Belum ditentukan.
