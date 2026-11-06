#!/bin/sh
# Uso: converter.sh <pasta com *_v1.mp3/*_v2.mp3> <saida assets/audio>
# Converte o lote de IA do Colab para OGG (o servidor do Clank só serve .ogg em assets/audio) e grava ia.json.
set -e
ENT="$1"; SAI="$2"; mkdir -p "$SAI"
python3 - "$ENT" "$SAI" <<'PY'
import json, os, re, subprocess, sys
ent, sai = sys.argv[1:]
man = {}
for f in sorted(os.listdir(ent)):
    m = re.fullmatch(r"(.+)_v([12])\.mp3", f)
    if not m: continue
    nome, n = m.groups(); arq = f"ia-{nome}-v{n}.ogg"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(ent, f), "-c:a", "libvorbis", "-q:a", "5", os.path.join(sai, arq)], check=True)
    man.setdefault(nome, {})["c" if n == "1" else "d"] = arq
json.dump(man, open(os.path.join(sai, "ia.json"), "w"), indent=1, ensure_ascii=False)
print(len(man), "sons")
PY
