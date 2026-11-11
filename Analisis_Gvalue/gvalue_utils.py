"""
Fungsi bersama untuk analisis G-value dari output TOPAS-nBio (scorer TsIRTInterPulse).

Format tiap file .phsp (lihat .header):
    1: TotalNumberOfSpeciesAtTime   -> N (jumlah molekul pada waktu t)
    2: Time [picosecond]            -> t
    3: MoleculeName                 -> nama spesies
    4: EnergyDeposit [eV]           -> energi terdeposit kumulatif sampai waktu t

G-value dihitung sebagai jumlah molekul per 100 eV energi terdeposit:
    G(t) = N(t) / (E(t) / 100)      [molekul / 100 eV]

Satu kondisi (mis. Result/jumlahpulsa/Flash/Flash) berisi 100 seed. Untuk tiap kondisi,
semua seed dibaca, G(t) dihitung per seed, lalu dirata-rata antar seed (mean, SD, SEM).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Pengaturan
# ---------------------------------------------------------------------------
ANALISIS_DIR = Path(__file__).resolve().parent
TESIS_DIR = ANALISIS_DIR.parent
RESULT_DIR = TESIS_DIR / "Result"
OUTPUT_DIR = ANALISIS_DIR / "output"
GRAFIK_DIR = OUTPUT_DIR / "grafik"
TABEL_DIR = OUTPUT_DIR / "tabel"
CACHE_DIR = ANALISIS_DIR / "cache"

# Satuan waktu untuk grafik & tabel: "ps", "ns", "us", "ms", atau "s"
SATUAN_WAKTU = "us"
FAKTOR_DARI_PS = {"ps": 1.0, "ns": 1e-3, "us": 1e-6, "ms": 1e-9, "s": 1e-12}
LABEL_SATUAN = {"ps": "ps", "ns": "ns", "us": "µs", "ms": "ms", "s": "s"}

# Urutan & label molekul untuk grafik
MOLEKUL = ["OH^0", "e_aq^-1", "H3O^1", "H2O2^0", "H^0", "H_2^0",
           "OH^-1", "O2^-1", "HO2^0", "O2^0"]
LABEL_MOLEKUL = {
    "OH^0": "•OH", "e_aq^-1": "e⁻aq", "H3O^1": "H₃O⁺", "H2O2^0": "H₂O₂",
    "H^0": "H•", "H_2^0": "H₂", "OH^-1": "OH⁻", "O2^-1": "O₂•⁻",
    "HO2^0": "HO₂•", "O2^0": "O₂",
}

POLA_FILE = re.compile(r"^(?P<prefix>.+)_seed(?P<seed>\d+)\.phsp$")


# ---------------------------------------------------------------------------
# Struktur data
# ---------------------------------------------------------------------------
@dataclass
class Kondisi:
    """Satu set simulasi (satu folder berisi file *_seedN.phsp)."""
    grup: str            # mis. "jumlahpulsa", "lebarpulsa", "Interval Pulse"
    nama: str            # mis. "Flash", "lebar10us"
    folder: Path
    prefix: str          # mis. "flash"
    files: dict[int, Path] = field(default_factory=dict)  # seed -> path

    @property
    def id(self) -> str:
        return f"{self.grup}/{self.nama}"

    @property
    def id_file(self) -> str:
        return f"{self.grup}_{self.nama}".replace(" ", "")


@dataclass
class DataGvalue:
    """Hasil G-value semua seed untuk satu kondisi."""
    kondisi: Kondisi
    waktu_ps: np.ndarray                 # (n_waktu,)
    seeds: np.ndarray                    # (n_seed,)
    molekul: list[str]
    G: np.ndarray                        # (n_seed, n_molekul, n_waktu)  molekul/100 eV
    N: np.ndarray                        # (n_seed, n_molekul, n_waktu)
    E: np.ndarray                        # (n_seed, n_waktu)  eV

    @property
    def waktu(self) -> np.ndarray:
        return self.waktu_ps * FAKTOR_DARI_PS[SATUAN_WAKTU]

    def idx(self, mol: str) -> int:
        return self.molekul.index(mol)

    def mean(self, mol: str) -> np.ndarray:
        return np.nanmean(self.G[:, self.idx(mol), :], axis=0)

    def sd(self, mol: str) -> np.ndarray:
        return np.nanstd(self.G[:, self.idx(mol), :], axis=0, ddof=1)

    def sem(self, mol: str) -> np.ndarray:
        g = self.G[:, self.idx(mol), :]
        n = np.sum(~np.isnan(g), axis=0)
        return np.nanstd(g, axis=0, ddof=1) / np.sqrt(n)


# ---------------------------------------------------------------------------
# Pencarian file
# ---------------------------------------------------------------------------
def cari_kondisi(result_dir: Path = RESULT_DIR) -> list[Kondisi]:
    """Cari semua folder di Result/ yang berisi file *_seedN.phsp."""
    hasil: dict[Path, Kondisi] = {}
    for f in sorted(result_dir.rglob("*.phsp")):
        m = POLA_FILE.match(f.name)
        if not m:
            continue
        folder = f.parent
        if folder not in hasil:
            rel = folder.relative_to(result_dir).parts
            grup = rel[0]
            nama = rel[-1]
            hasil[folder] = Kondisi(grup=grup, nama=nama, folder=folder,
                                    prefix=m["prefix"])
        k = hasil[folder]
        if m["prefix"] != k.prefix:
            print(f"  [peringatan] prefix berbeda di {folder}: {f.name} (diabaikan)")
            continue
        k.files[int(m["seed"])] = f
    return sorted(hasil.values(), key=lambda k: (k.grup, k.nama))


# ---------------------------------------------------------------------------
# Pembacaan & perhitungan
# ---------------------------------------------------------------------------
def baca_phsp(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=r"\s+", header=None,
                       names=["N", "t_ps", "mol", "E_eV"],
                       dtype={"N": float, "t_ps": float, "mol": str, "E_eV": float})


def hitung_G(N: np.ndarray, E: np.ndarray) -> np.ndarray:
    """G = N / (E/100). Jika E = 0, G dibuat NaN."""
    with np.errstate(divide="ignore", invalid="ignore"):
        G = N / (E / 100.0)
    G[~np.isfinite(G)] = np.nan
    return G


def muat_kondisi(k: Kondisi, pakai_cache: bool = True) -> DataGvalue:
    """Baca semua seed satu kondisi -> DataGvalue. Disimpan ke cache .npz."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache = CACHE_DIR / f"{k.id_file}.npz"
    seeds = np.array(sorted(k.files))
    mtime_terbaru = max(p.stat().st_mtime for p in k.files.values())

    if pakai_cache and cache.exists() and cache.stat().st_mtime >= mtime_terbaru:
        z = np.load(cache, allow_pickle=False)
        if np.array_equal(z["seeds"], seeds):
            return DataGvalue(k, z["waktu_ps"], seeds, list(z["molekul"]),
                              z["G"], z["N"], z["E"])

    waktu_ref = None
    molekul = None
    N_all, E_all = [], []
    for s in seeds:
        df = baca_phsp(k.files[s])
        mols = list(dict.fromkeys(df["mol"]))  # urutan sesuai file
        if molekul is None:
            molekul = [m for m in MOLEKUL if m in mols] + [m for m in mols if m not in MOLEKUL]
        N_seed = []
        E_seed = None
        for mol in molekul:
            # urutan baris di file tidak selalu urut waktu -> urutkan per molekul
            sub = df[df["mol"] == mol].sort_values("t_ps", kind="stable")
            t = sub["t_ps"].to_numpy()
            if E_seed is None:
                E_seed = sub["E_eV"].to_numpy()
            if waktu_ref is None:
                waktu_ref = t
            if len(t) != len(waktu_ref) or not np.allclose(t, waktu_ref, rtol=1e-4):
                raise ValueError(f"Grid waktu berbeda di {k.files[s]} ({mol})")
            N_seed.append(sub["N"].to_numpy())
        N_all.append(N_seed)
        E_all.append(E_seed)

    N = np.array(N_all, dtype=float)                 # (seed, mol, waktu)
    E = np.array(E_all, dtype=float)                 # (seed, waktu)
    G = hitung_G(N, E[:, None, :])
    np.savez_compressed(cache, waktu_ps=waktu_ref, seeds=seeds,
                        molekul=np.array(molekul), G=G, N=N, E=E)
    return DataGvalue(k, waktu_ref, seeds, molekul, G, N, E)


def muat_semua(filter_grup: list[str] | None = None) -> list[DataGvalue]:
    """Muat semua kondisi (opsional: hanya grup tertentu)."""
    data = []
    for k in cari_kondisi():
        if filter_grup and k.grup not in filter_grup:
            continue
        print(f"  membaca {k.id:40s} ({len(k.files)} seed)")
        data.append(muat_kondisi(k))
    return data


def molekul_aktif(d: DataGvalue) -> list[str]:
    """Molekul yang G-nya tidak selalu nol/NaN."""
    return [m for m in d.molekul if np.nanmax(np.abs(d.G[:, d.idx(m), :]), initial=0) > 0]


def parse_argumen(deskripsi: str):
    import argparse
    p = argparse.ArgumentParser(description=deskripsi)
    p.add_argument("--grup", nargs="*", default=None,
                   help='Hanya grup tertentu, mis. --grup jumlahpulsa lebarpulsa "Interval Pulse"')
    p.add_argument("--molekul", nargs="*", default=None,
                   help="Hanya molekul tertentu, mis. --molekul OH^0 e_aq^-1 H2O2^0")
    return p.parse_args()
