"""
3. Nilai G-value maksimal.

Untuk setiap kondisi dan molekul:
  a) G_maks_kurva_rata2 : puncak dari kurva G(t) rata-rata 100 seed, beserta waktu
                          terjadinya puncak dan SD antar seed pada waktu tersebut.
  b) G_maks_per_seed    : puncak G(t) dicari pada tiap seed, lalu nilai puncak dan
                          waktunya dirata-rata antar seed (mean ± SD, SEM).

Hasil: output/tabel/Gvalue_maksimal.csv dan grafik batang per grup.

Jalankan:
    python 3_gvalue_maksimal.py
    python 3_gvalue_maksimal.py --grup "Interval Pulse"
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import gvalue_utils as gu


def main():
    arg = gu.parse_argumen("G-value maksimal")
    print("Membaca data ...")
    semua = gu.muat_semua(arg.grup)
    satuan = gu.SATUAN_WAKTU

    baris = []
    for d in semua:
        t = d.waktu
        for mol in arg.molekul or d.molekul:
            g = d.G[:, d.idx(mol), :]                      # (seed, waktu)
            mean = np.nanmean(g, axis=0)
            if np.all(np.isnan(mean)) or np.nanmax(mean) == 0:
                i_puncak = None
            else:
                i_puncak = int(np.nanargmax(mean))

            # per seed
            valid = ~np.all(np.isnan(g), axis=1)
            maks_seed = np.full(len(g), np.nan)
            t_maks_seed = np.full(len(g), np.nan)
            maks_seed[valid] = np.nanmax(g[valid], axis=1)
            t_maks_seed[valid] = t[np.nanargmax(g[valid], axis=1)]
            n = int(valid.sum())

            baris.append({
                "grup": d.kondisi.grup, "kondisi": d.kondisi.nama, "molekul": mol, "n_seed": n,
                "G_maks_kurva_rata2": mean[i_puncak] if i_puncak is not None else 0.0,
                "G_maks_kurva_rata2_SD": np.nanstd(g[:, i_puncak], ddof=1) if i_puncak is not None else np.nan,
                f"t_maks_kurva_rata2_{satuan}": t[i_puncak] if i_puncak is not None else np.nan,
                "G_maks_per_seed_mean": np.nanmean(maks_seed),
                "G_maks_per_seed_SD": np.nanstd(maks_seed, ddof=1),
                "G_maks_per_seed_SEM": np.nanstd(maks_seed, ddof=1) / np.sqrt(n),
                f"t_maks_per_seed_mean_{satuan}": np.nanmean(t_maks_seed),
                f"t_maks_per_seed_SD_{satuan}": np.nanstd(t_maks_seed, ddof=1),
            })

    df = pd.DataFrame(baris)
    gu.TABEL_DIR.mkdir(parents=True, exist_ok=True)
    out = gu.TABEL_DIR / "Gvalue_maksimal.csv"
    df.to_csv(out, index=False)
    print(f"\nTabel disimpan: {out.relative_to(gu.ANALISIS_DIR)}")

    aktif = df[df.G_maks_kurva_rata2 > 0]
    tampil = pd.DataFrame({
        "grup": aktif.grup, "kondisi": aktif.kondisi, "molekul": aktif.molekul,
        "G maks (kurva rata2)": aktif.G_maks_kurva_rata2.map("{:.3f}".format)
            + " ± " + aktif.G_maks_kurva_rata2_SD.map("{:.3f}".format),
        f"t puncak ({gu.LABEL_SATUAN[satuan]})": aktif[f"t_maks_kurva_rata2_{satuan}"].map("{:.3g}".format),
        "G maks per seed": aktif.G_maks_per_seed_mean.map("{:.3f}".format)
            + " ± " + aktif.G_maks_per_seed_SD.map("{:.3f}".format),
    })
    with pd.option_context("display.max_rows", None, "display.width", 200):
        print(tampil.to_string(index=False))

    for grup, dg in aktif.groupby("grup", sort=False):
        mols = list(dict.fromkeys(dg.molekul))
        kondisi = list(dict.fromkeys(dg.kondisi))
        fig, ax = plt.subplots(figsize=(max(7, 0.6 * len(mols) * len(kondisi) / 2), 4.2))
        lebar = 0.8 / len(kondisi)
        x = np.arange(len(mols))
        for i, k in enumerate(kondisi):
            sub = dg[dg.kondisi == k].set_index("molekul").reindex(mols)
            ax.bar(x + (i - (len(kondisi) - 1) / 2) * lebar, sub.G_maks_kurva_rata2, lebar,
                   yerr=sub.G_maks_kurva_rata2_SD, capsize=2, label=k, color=f"C{i % 10}")
        ax.set_xticks(x, [gu.LABEL_MOLEKUL.get(m, m) for m in mols])
        ax.set_ylabel("G-value maksimal (molekul/100 eV)")
        ax.set_title(f"G-value maksimal — {grup} (puncak kurva rata-rata, error bar = ± 1 SD)")
        ax.grid(True, axis="y", alpha=0.3)
        ax.legend(fontsize=8)
        fig.tight_layout()
        outg = gu.GRAFIK_DIR / "maksimal" / f"Gvalue_maksimal_{grup.replace(' ', '')}.png"
        outg.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(outg, dpi=200)
        plt.close(fig)
        print(f"Grafik disimpan: {outg.relative_to(gu.ANALISIS_DIR)}")


if __name__ == "__main__":
    main()
