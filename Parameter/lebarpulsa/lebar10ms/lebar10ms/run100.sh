#!/bin/bash
# Menjalankan TOPAS 100x, seed 1 sampai 100, output terpisah per seed.

INPUT="lebarpulsa_10ms_1seed.txt"   # nama file input dasar kamu

for seed in $(seq 1 100); do
    tmp="run_seed_${seed}.txt"

    # Salin file input, lalu ganti baris Seed dan OutputFile dengan versi per-seed
    sed -e "s|^i:Ts/Seed = .*|i:Ts/Seed = ${seed}|" \
        -e "s|^s:Sc/gvalue/OutputFile = .*|s:Sc/gvalue/OutputFile = \"lebarpulsa_10ms_seed${seed}\"|" \
        "$INPUT" > "$tmp"

    echo ">>> Run seed ${seed} ..."
    topas "$tmp"          # ganti 'topas' bila perintah TOPAS kamu berbeda
done

echo "Selesai. 100 run sudah dijalankan."
