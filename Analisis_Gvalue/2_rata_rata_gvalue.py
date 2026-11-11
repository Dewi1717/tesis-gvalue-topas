"""
2. Nilai rata-rata G-value.

Untuk setiap kondisi dan molekul, dihitung dua jenis "rata-rata":

  a) G_rata2_waktu : rata-rata G(t) terhadap seluruh titik waktu observasi pada
                     tiap seed, lalu dirata-rata antar seed (mean ± SD, SEM).
                     Catatan: titik waktu TOPAS berskala logaritmik, sehingga ini
                     setara dengan rata-rata pada skala log(waktu).
  b) G_akhir       : G pada waktu observasi terakhir (akhir simulasi), rata-rata
                     antar seed (mean ± SD, SEM). Ini yang biasa dilaporkan sebagai
                     G-value "akhir" / steady state.

Opsional: --tmin / --tmax untuk membatasi jendela waktu rata-rata (a), dalam satuan
SATUAN_WAKTU di gvalue_utils.py (default µs).

Jalankan:
    python 2_rata_rata_gvalue.py
    python 2_rata_rata_gvalue.py --grup lebarpulsa
    python 2_rata_rata_gvalue.py --tmin 1 --tmax 1000
"""

import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import gvalue_utils as gu


def argumen():
    p = argparse.ArgumentParser(description="Rata-rata G-value")
    p.add_argument("--grup", nargs="*", default=None)
    p.add_argument("--molekul", nargs="*", default=None)
    p.add_argument("--tmin", type=float, default=None, help="batas bawah waktu (satuan SATUAN_WAKTU)")
    p.add_argument("--tmax", type=float, default=None, help="batas atas waktu (satuan SATUAN_WAKTU)")
    return p.parse_args()


def ringkas(x: np.ndarray):
    x = x[~np.isnan(x)]
    n = len(x)
    sd = x.std(ddof=1) if n > 1 else np.nan
    return x.mean() if n else np.nan, sd, sd / np.sqrt(n) if n > 1 else np.nan, n


def main():
    arg = argumen()
    print("Membaca data ...")
    semua = gu.muat_semua(arg.grup)
    satuan = gu.SATUAN_WAKTU

    baris = []
    for d in semua:
        t = d.waktu
        jendela = np.ones_like(t, dtype=bool)
        if arg.tmin is not None:
            jendela &= t >= arg.tmin
        if arg.tmax is not None:
            jendela &= t <= arg.tmax
        mols = arg.molekul or d.molekul
        for mol in mols:
            g = d.G[:, d.idx(mol), :]                      # (seed, waktu)
            rata_waktu_per_seed = np.nanmean(g[:, jendela], axis=1)
            akhir_per_seed = g[:, -1]
            m1, sd1, se1, n = ringkas(rata_waktu_per_seed)
            m2, sd2, se2, _ = ringkas(akhir_per_seed)
            baris.append({
                "grup": d.kondisi.grup, "kondisi": d.kondisi.nama, "molekul": mol,
                "n_seed": n,
                f"t_awal_{satuan}": t[jendela][0], f"t_akhir_{satuan}": t[jendela][-1],
                "G_rata2_waktu_mean": m1, "G_rata2_waktu_SD": sd1, "G_rata2_waktu_SEM": se1,
                "G_akhir_mean": m2, "G_akhir_SD": sd2, "G_akhir_SEM": se2,
            })

    df = pd.DataFrame(baris)
    gu.TABEL_DIR.mkdir(parents=True, exist_ok=True)
    out = gu.TABEL_DIR / "Gvalue_rata_rata.csv"
    df.to_csv(out, index=False)
    print(f"\nTabel disimpan: {out.relative_to(gu.ANALISIS_DIR)}")

    # tabel ringkas di layar (format mean ± SD)
    tampil = df.assign(
        **{"G rata2 waktu": df.G_rata2_waktu_mean.map("{:.3f}".format) + " ± " + df.G_rata2_waktu_SD.map("{:.3f}".format),
           "G akhir": df.G_akhir_mean.map("{:.3f}".format) + " ± " + df.G_akhir_SD.map("{:.3f}".format)}
    )[["grup", "kondisi", "molekul", "G rata2 waktu", "G akhir"]]
    tampil = tampil[(df.G_rata2_waktu_mean.fillna(0) != 0) | (df.G_akhir_mean.fillna(0) != 0)]
    with pd.option_context("display.max_rows", None, "display.width", 200):
        print(tampil.to_string(index=False))

    # grafik batang per grup: G rata-rata (waktu) dan G akhir, ± SD
    for grup, dg in df.groupby("grup", sort=False):
        dg = dg[(dg.G_rata2_waktu_mean.fillna(0) != 0) | (dg.G_akhir_mean.fillna(0) != 0)]
        mols = list(dict.fromkeys(dg.molekul))
        kondisi = list(dict.fromkeys(dg.kondisi))
        fig, axes = plt.subplots(1, 2, figsize=(max(8, 1.2 * len(mols) * len(kondisi) / 2), 4.2))
        lebar = 0.8 / len(kondisi)
        x = np.arange(len(mols))
        for ax, kol, judul in [(axes[0], "G_rata2_waktu", "Rata-rata terhadap waktu"),
                               (axes[1], "G_akhir", "G pada akhir observasi")]:
            for i, k in enumerate(kondisi):
                sub = dg[dg.kondisi == k].set_index("molekul").reindex(mols)
                ax.bar(x + (i - (len(kondisi) - 1) / 2) * lebar, sub[f"{kol}_mean"],
                       lebar, yerr=sub[f"{kol}_SD"], capsize=2, label=k, color=f"C{i % 10}")
            ax.set_xticks(x, [gu.LABEL_MOLEKUL.get(m, m) for m in mols])
            ax.set_ylabel("G-value (molekul/100 eV)")
            ax.set_title(judul)
            ax.grid(True, axis="y", alpha=0.3)
        axes[0].legend(fontsize=8)
        fig.suptitle(f"Rata-rata G-value — {grup} (error bar = ± 1 SD antar seed)")
        fig.tight_layout()
        outg = gu.GRAFIK_DIR / "rata_rata" / f"Gvalue_rata_rata_{grup.replace(' ', '')}.png"
        outg.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(outg, dpi=200)
        plt.close(fig)
        print(f"Grafik disimpan: {outg.relative_to(gu.ANALISIS_DIR)}")


if __name__ == "__main__":
    main()
