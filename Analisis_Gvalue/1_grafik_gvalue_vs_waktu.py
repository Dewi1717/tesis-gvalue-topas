"""
1. Grafik G-value vs waktu.

Untuk setiap kondisi di folder Result/:
  - grafik per kondisi: satu panel per molekul, garis = rata-rata 100 seed,
    pita = ± 1 SD antar seed.
Untuk setiap grup (jumlahpulsa, lebarpulsa, Interval Pulse):
  - grafik perbandingan: satu panel per molekul, tiap kondisi satu garis.
Data rata-rata G(t) juga disimpan sebagai CSV agar bisa diolah di Excel/Origin.

Jalankan:
    python 1_grafik_gvalue_vs_waktu.py
    python 1_grafik_gvalue_vs_waktu.py --grup jumlahpulsa
    python 1_grafik_gvalue_vs_waktu.py --molekul OH^0 e_aq^-1 H2O2^0
"""

import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import gvalue_utils as gu


def grid(n):
    kol = min(n, 3)
    return math.ceil(n / kol), kol


def plot_per_kondisi(d: gu.DataGvalue, mols: list[str]):
    baris, kol = grid(len(mols))
    fig, axes = plt.subplots(baris, kol, figsize=(4.6 * kol, 3.4 * baris), squeeze=False)
    t = d.waktu
    for ax, mol in zip(axes.flat, mols):
        m, s = d.mean(mol), d.sd(mol)
        ax.plot(t, m, color="C0", lw=1.5, label="rata-rata")
        ax.fill_between(t, m - s, m + s, color="C0", alpha=0.25, lw=0, label="± 1 SD")
        ax.set_xscale("log")
        ax.set_title(gu.LABEL_MOLEKUL.get(mol, mol))
        ax.set_xlabel(f"Waktu ({gu.LABEL_SATUAN[gu.SATUAN_WAKTU]})")
        ax.set_ylabel("G-value (molekul/100 eV)")
        ax.grid(True, which="both", alpha=0.3)
    for ax in list(axes.flat)[len(mols):]:
        ax.set_visible(False)
    axes.flat[0].legend(fontsize=8)
    fig.suptitle(f"G-value vs waktu — {d.kondisi.id}  (n = {len(d.seeds)} seed)")
    fig.tight_layout()
    out = gu.GRAFIK_DIR / "per_kondisi" / f"Gvalue_vs_waktu_{d.kondisi.id_file}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200)
    plt.close(fig)
    return out


def plot_per_grup(grup: str, data: list[gu.DataGvalue], mols: list[str]):
    baris, kol = grid(len(mols))
    fig, axes = plt.subplots(baris, kol, figsize=(4.6 * kol, 3.4 * baris), squeeze=False)
    for ax, mol in zip(axes.flat, mols):
        for i, d in enumerate(data):
            if mol in d.molekul:
                ax.plot(d.waktu, d.mean(mol), lw=1.4, color=f"C{i % 10}", label=d.kondisi.nama)
        ax.set_xscale("log")
        ax.set_title(gu.LABEL_MOLEKUL.get(mol, mol))
        ax.set_xlabel(f"Waktu ({gu.LABEL_SATUAN[gu.SATUAN_WAKTU]})")
        ax.set_ylabel("G-value (molekul/100 eV)")
        ax.grid(True, which="both", alpha=0.3)
    for ax in list(axes.flat)[len(mols):]:
        ax.set_visible(False)
    axes.flat[0].legend(fontsize=8)
    fig.suptitle(f"Perbandingan G-value vs waktu — {grup} (rata-rata seed)")
    fig.tight_layout()
    out = gu.GRAFIK_DIR / "perbandingan_grup" / f"Gvalue_vs_waktu_{grup.replace(' ', '')}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200)
    plt.close(fig)
    return out


def simpan_csv(d: gu.DataGvalue):
    kolom = {f"waktu_{gu.SATUAN_WAKTU}": d.waktu,
             "E_rata2_eV": d.E.mean(axis=0)}
    for mol in d.molekul:
        kolom[f"G_mean_{mol}"] = d.mean(mol)
        kolom[f"G_SD_{mol}"] = d.sd(mol)
        kolom[f"G_SEM_{mol}"] = d.sem(mol)
    out = gu.TABEL_DIR / "Gvalue_vs_waktu" / f"Gvalue_vs_waktu_{d.kondisi.id_file}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(kolom).to_csv(out, index=False)


def main():
    arg = gu.parse_argumen("Grafik G-value vs waktu")
    print("Membaca data ...")
    semua = gu.muat_semua(arg.grup)
    if not semua:
        print("Tidak ada data ditemukan.")
        return

    print("Membuat grafik per kondisi ...")
    for d in semua:
        mols = arg.molekul or gu.molekul_aktif(d)
        print("  ->", plot_per_kondisi(d, mols).relative_to(gu.ANALISIS_DIR))
        simpan_csv(d)

    print("Membuat grafik perbandingan per grup ...")
    for grup in dict.fromkeys(d.kondisi.grup for d in semua):
        data = [d for d in semua if d.kondisi.grup == grup]
        mols = arg.molekul or list(dict.fromkeys(m for d in data for m in gu.molekul_aktif(d)))
        print("  ->", plot_per_grup(grup, data, mols).relative_to(gu.ANALISIS_DIR))
    print("Selesai.")


if __name__ == "__main__":
    main()
