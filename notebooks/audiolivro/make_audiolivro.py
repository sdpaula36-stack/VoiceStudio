"""Gera notebooks/audiolivro/Audiolivro_Piloto_Colab.ipynb a partir dos roteiros JSON.

Uso: python -I notebooks/audiolivro/make_audiolivro.py notebooks/audiolivro/Audiolivro_Piloto_Colab.ipynb \
        notebooks/audiolivro/narizinho_cap01.json notebooks/audiolivro/narizinho_cap02.json ...
"""
import json
import pprint
import sys

OUT = sys.argv[1]
caps = sorted((json.load(open(p, encoding="utf-8")) for p in sys.argv[2:]), key=lambda c: c["capitulo"])
rot = caps[0]
vozes = {}
for c in caps:
    vozes.update(c["vozes"])
VOZES = pprint.pformat(vozes, width=100, sort_dicts=False)
CAPITULOS = "{\n" + "".join(
    f"    {c['capitulo']}: {{\"titulo\": {json.dumps(c['titulo'], ensure_ascii=False)}, \"trechos\": [\n"
    + "".join(f"        {json.dumps(t, ensure_ascii=False)},\n" for t in c["trechos"]) + "    ]},\n"
    for c in caps) + "}"
ULTIMO = caps[-1]["capitulo"]
# Pasta do livro no Drive: campo "pasta" do JSON ou o título sem acentos.
import re, unicodedata
PASTA = rot.get("pasta") or re.sub(r"[^a-z0-9]+", "_", unicodedata.normalize("NFKD", rot["livro"])
                                   .encode("ascii", "ignore").decode().lower()).strip("_")
cells = []


def md(s):
    cells.append({"cell_type": "markdown", "metadata": {}, "source": s.strip("\n").splitlines(keepends=True)})


def code(s):
    cells.append({"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
                  "source": s.strip("\n").splitlines(keepends=True)})


md(f'''
# Piloto de audiolivro adaptado: {rot["livro"]}

Narra, numa GPU grátis do Google Colab, os capítulos 1 a {ULTIMO} de *{rot["livro"]}*, numa adaptação para crianças e adolescentes com deficiência visual, síndrome de Down, autismo e TDAH. O guia de adaptação e de narração está em `notebooks/audiolivro/GUIA.md`.

**Antes de começar:** menu `Ambiente de execução → Alterar o tipo de ambiente de execução → GPU T4`. Depois rode as células de cima para baixo. Rodar de novo qualquer célula é seguro.

**Saída** (no seu Google Drive, em `MyDrive/Audiolivros/{PASTA}/capNN/`), para cada capítulo:
- `capNN_A_so_voz.mp3`: só a narração, para quem é sensível a sons;
- `capNN_B_com_ambiente.mp3`: narração com vinheta suave e som de riacho bem baixinho.

Escolha os capítulos na célula 2 (`CAPITULOS_PARA_GERAR`). As vozes ficam em `{PASTA}/vozes/` e são as mesmas em todos os capítulos.

**Licença:** a voz padrão (OmniVoice) é de uso **não comercial** (CC-BY-NC). Serve para um piloto gratuito. As vozes são sintéticas e originais, sem clonar ninguém.

**Sotaque:** o modelo fala português, mas às vezes puxa para o sotaque de Portugal. Se acontecer, troque a `semente` da voz na célula 5. Outra saída é usar uma gravação de 5 a 10 segundos de alguém que **autorizou por escrito** o uso da própria voz (campo `amostra`).
''')

code(r'''
# ── 1. Conferir a GPU ───────────────────────────────────────────────────────
import shutil, subprocess
if shutil.which("nvidia-smi"):
    print(subprocess.run(["nvidia-smi"], capture_output=True, text=True).stdout)
else:
    print("ATENÇÃO: sem GPU. Vá em Ambiente de execução -> Alterar o tipo de ambiente "
          "de execução -> GPU T4, e rode o notebook de novo do início.")
''')

code(r'''
# ── 2. Google Drive e pastas ────────────────────────────────────────────────
import os
from google.colab import drive
drive.mount("/content/drive")

CAPITULOS_PARA_GERAR = @@CAPS@@   # quais capítulos narrar (ex.: [2, 3])

LIVRO = "/content/drive/MyDrive/Audiolivros/@@PASTA@@"
PASTA_VOZES = os.path.join(LIVRO, "vozes")   # uma fala de referência por personagem
os.makedirs(PASTA_VOZES, exist_ok=True)
print("Os arquivos vão para:", LIVRO)
''')

code(r'''
# ── 3. Instalar o VoiceStudio (primeira vez: ~5-8 min) ──────────────────────
import os, shutil, subprocess, sys

REPO_URL = "https://github.com/sdpaula36-stack/VoiceStudio"
REPO_DIR = "/content/VoiceStudio"
os.environ.setdefault("UV_HTTP_TIMEOUT", "300")

def run(cmd, *, cwd=None, what=""):
    shown = cmd if isinstance(cmd, str) else " ".join(cmd)
    print(f"\n$ {shown}")
    if subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str)).returncode != 0:
        raise SystemExit(f"\nFALHOU: {what or shown}. Veja o erro acima; rodar de novo é seguro.")

if os.path.isdir(os.path.join(REPO_DIR, ".git")):
    run(["git", "-C", REPO_DIR, "pull", "--ff-only"], what="git pull")
else:
    run(["git", "clone", "--depth", "1", REPO_URL, REPO_DIR], what="git clone")

run("apt-get -qq update && apt-get -qq install -y ffmpeg libsndfile1", what="apt-get install")
if not shutil.which("uv"):
    run([sys.executable, "-m", "pip", "install", "-q", "uv"], what="pip install uv")
run(["uv", "pip", "install", "--system", "--no-cache",
     "--constraint", "deploy/torch-constraints.txt",
     "--override", "deploy/uv-overrides.txt", "."],
    cwd=REPO_DIR, what="instalação do backend")

from huggingface_hub import snapshot_download
print("Baixando o modelo de voz (alguns GB, só na primeira vez)...")
snapshot_download("k2-fsa/OmniVoice")
print("Pronto.")
''')

code(r'''
# ── 4. Ligar o servidor do VoiceStudio ──────────────────────────────────────
import json, os, subprocess, sys, time, urllib.request

PORT = 3900
BASE = f"http://127.0.0.1:{PORT}"
LOG_PATH = "/content/voicestudio_backend.log"

def health():
    try:
        with urllib.request.urlopen(f"{BASE}/health", timeout=5) as r:
            return json.load(r)
    except Exception:
        return None

info = health()
if not info:
    subprocess.run(f"kill -9 $(lsof -t -i:{PORT}) 2>/dev/null || true", shell=True)
    env = os.environ.copy()
    env.update(OMNIVOICE_SERVER_MODE="1", PYTHONUNBUFFERED="1")
    env.setdefault("OMNIVOICE_DATA_DIR", "/content/omnivoice_data")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--app-dir", "backend",
         "--host", "127.0.0.1", "--port", str(PORT)],
        cwd="/content/VoiceStudio", env=env,
        stdout=open(LOG_PATH, "ab"), stderr=subprocess.STDOUT)
    deadline = time.time() + 300
    while time.time() < deadline and proc.poll() is None and not info:
        print(".", end="", flush=True)
        time.sleep(3)
        info = health()
    print()
    if not info:
        raise SystemExit("O servidor não ligou em 5 min. Final do log:\n"
                         + "".join(open(LOG_PATH, errors="replace").readlines()[-40:]))
print("Servidor ligado:", info)
''')

code(r'''
# ── 4b. Licenças do modelo de voz ───────────────────────────────────────────
# Leia o que aparece abaixo. Se concordar, troque para True e rode de novo.
ACEITO_AS_LICENCAS = False

import requests
pendentes = []
for repo in ["k2-fsa/OmniVoice", "eustlb/higgs-audio-v2-tokenizer"]:
    st = requests.get(f"{BASE}/models/licenses/acceptance/{repo}", timeout=30).json()
    print(f"{repo}\n  licença: {st.get('license')} ({st.get('category')})\n"
          f"  detalhes: https://huggingface.co/{repo}\n")
    if not st.get("accepted"):
        pendentes.append(st)

if not pendentes:
    print("Licenças já aceitas.")
elif not ACEITO_AS_LICENCAS:
    raise SystemExit("Leia as licenças acima. Se concordar, mude ACEITO_AS_LICENCAS para True "
                     "e rode de novo. 'noncommercial' = o áudio não pode ser vendido.")
else:
    for st in pendentes:
        requests.post(f"{BASE}/models/licenses/accept", timeout=30,
                      json={"repo_id": st["repo_id"], "fingerprint": st["fingerprint"],
                            "accepted": True}).raise_for_status()
        print("Aceita:", st["repo_id"])
''')

md('''
## Roteiro

Cada trecho é `[personagem, texto, velocidade, pausa depois em segundos]`.

- **velocidade:** 1.0 é normal; até 1.1 na ação; 0.85 a 0.9 no suspense e no sono.
- **pausa:** o silêncio depois do trecho. Pausas maiores antes das revelações prendem a atenção.
- **voz** aceita só estes termos: `male`/`female`; `child`, `teenager`, `young adult`, `middle-aged`, `elderly`; `very low pitch` … `very high pitch`; `whisper`.
- A voz de cada personagem nasce da fala mais longa dele no **primeiro** capítulo em que aparece, e é a mesma em todos os outros.

Edite à vontade. Os trechos que você mudar são gerados de novo na célula 7.
''')

code(f'''
# ── 5. Roteiro (EDITE AQUI) ─────────────────────────────────────────────────
# "amostra" (opcional, em cada voz): caminho de um .wav de 5-10 s de alguém que
# AUTORIZOU por escrito o uso da voz. Nunca use a voz de um dublador ou artista.
VOZES = {VOZES}

CAPITULOS = {CAPITULOS}

for n, c in CAPITULOS.items():
    palavras = sum(len(t[1].split()) for t in c["trechos"])
    print(f"Capítulo {{n}}, {{c['titulo']}}: {{len(c['trechos'])}} trechos, cerca de "
          f"{{palavras / 130 + sum(t[3] for t in c['trechos']) / 60:.1f}} min.")
''')

code(r'''
# ── 6. Criar as vozes e ouvir (troque a semente de quem não ficou bom) ──────
import hashlib, os, shutil, requests
from IPython.display import Audio, display

def gerar(texto, destino, **campos):
    arquivos = campos.pop("files", None)
    dados = {"text": texto, "language": "pt", "effect_preset": "raw", **campos}
    r = requests.post(f"{BASE}/generate", data=dados, files=arquivos, timeout=1800)
    if r.status_code != 200:
        raise SystemExit(f"Erro {r.status_code} em /generate: {r.text[:500]}\nLog: {LOG_PATH}")
    with open(destino, "wb") as f:
        f.write(r.content)

def chave(*partes):
    return hashlib.sha1(repr(partes).encode()).hexdigest()[:8]

REF = {}   # personagem -> (wav de referência, texto)
for nome, v in VOZES.items():
    # A fala mais longa do personagem no primeiro capítulo em que ele aparece.
    texto = next(max(falas, key=len) for _, c in sorted(CAPITULOS.items())
                 if (falas := [t[1] for t in c["trechos"] if t[0] == nome]))
    arq = f"{nome}_{chave(v, texto)}.wav"
    wav = os.path.join(PASTA_VOZES, arq)
    antigo = os.path.join(LIVRO, "cap01", "vozes", arq)   # versão do primeiro teste
    if not os.path.exists(wav) and os.path.exists(antigo):
        shutil.copy(antigo, wav)
    if not os.path.exists(wav):
        if v.get("amostra"):
            with open(v["amostra"], "rb") as a:
                gerar(texto, wav, seed=v["semente"], files={"ref_audio": ("amostra.wav", a)})
        else:
            gerar(texto, wav, instruct=v["voz"], seed=v["semente"])
    REF[nome] = (wav, texto)
    print(f"{nome} ({v['voz']}, semente {v['semente']}): {texto}")
    display(Audio(wav))
''')

code(r'''
# ── 7. Narrar e montar cada capítulo (A: só voz; B: com vinheta e riacho) ───
import os, subprocess
import numpy as np
import soundfile as sf
from IPython.display import Audio, display

def narrar(n):
    pasta = os.path.join(LIVRO, f"cap{n:02d}", "trechos")
    os.makedirs(pasta, exist_ok=True)
    arquivos = []
    for i, (quem, texto, vel, pausa) in enumerate(CAPITULOS[n]["trechos"], 1):
        ref_wav, ref_texto = REF[quem]
        wav = os.path.join(pasta, f"{i:03d}_{quem}_{chave(os.path.basename(ref_wav), texto, vel)}.wav")
        if not os.path.exists(wav):
            with open(ref_wav, "rb") as ref:
                gerar(texto, wav, seed=VOZES[quem]["semente"], ref_text=ref_texto, speed=vel,
                      files={"ref_audio": ("ref.wav", ref, "audio/wav")})
            print(f"{n}.{i:03d} {quem}: {texto}")
        arquivos.append((wav, pausa))
    return arquivos

def tom(freq, dur, vol, sr):
    t = np.arange(int(dur * sr)) / sr
    return (vol * np.sin(2 * np.pi * freq * t) * np.exp(-3 * t)).astype("float32")

def vinheta(sr):
    # Três notas suaves (dó, mi, sol), sem ataque forte.
    v = np.zeros(int(2.2 * sr), dtype="float32")
    for k, f in enumerate([523.25, 659.25, 783.99]):
        nota = tom(f, 1.4, 0.12, sr)
        ini = int(k * 0.35 * sr)
        v[ini:ini + len(nota)] += nota
    return v

def riacho(n, sr):
    # Ruído suave filtrado, que lembra água correndo, bem baixo e com entrada lenta.
    rng = np.random.default_rng(7)
    r = np.convolve(rng.standard_normal(n + 400).astype("float32"),
                    np.ones(40, dtype="float32") / 40, mode="valid")[:n]
    r *= 0.01 * (1 + 0.3 * np.sin(2 * np.pi * 0.15 * np.arange(n) / sr))
    fade = min(n // 2, 4 * sr)
    r[:fade] *= np.linspace(0, 1, fade)
    r[-fade:] *= np.linspace(1, 0, fade)
    return r

def exportar(audio, sr, pasta, nome):
    tmp = os.path.join(pasta, nome + ".wav")
    sf.write(tmp, audio, sr)
    mp3 = os.path.join(pasta, nome + ".mp3")
    # Volume normalizado para fone e caixinha: -16 LUFS, pico máximo -1.5 dBTP.
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp,
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "44100",
                    "-codec:a", "libmp3lame", "-q:a", "2", mp3], check=True)
    print(f"{nome}.mp3: {len(audio) / sr / 60:.1f} min")
    display(Audio(mp3))

def montar(n, arquivos):
    partes, sr = [], None
    for wav, pausa in arquivos:
        a, s = sf.read(wav, dtype="float32", always_2d=True)
        sr = sr or s
        assert s == sr, f"taxa de amostragem diferente em {wav}"
        partes += [a.mean(axis=1), np.zeros(int(pausa * sr), dtype="float32")]
    voz = np.concatenate(partes)
    um_seg = np.zeros(sr, dtype="float32")
    pasta = os.path.join(LIVRO, f"cap{n:02d}")
    exportar(np.concatenate([um_seg, voz, um_seg]), sr, pasta, f"cap{n:02d}_A_so_voz")
    exportar(np.concatenate([vinheta(sr), um_seg, voz + riacho(len(voz), sr), um_seg, vinheta(sr)]),
             sr, pasta, f"cap{n:02d}_B_com_ambiente")

REFAZER = False   # True: narra de novo capítulos que já têm os dois MP3 prontos

for n in CAPITULOS_PARA_GERAR:
    print(f"\n=== Capítulo {n}: {CAPITULOS[n]['titulo']} ===")
    prontos = [os.path.join(LIVRO, f"cap{n:02d}", f"cap{n:02d}_{v}.mp3")
               for v in ("A_so_voz", "B_com_ambiente")]
    if not REFAZER and all(map(os.path.exists, prontos)):
        print("Já estava pronto (para refazer, use REFAZER = True).")
        continue
    montar(n, narrar(n))
print("\nPronto! Os arquivos estão no Drive, em", LIVRO)

# Se um trecho ficou ruim, apague o .wav dele na pasta capNN/trechos/ e rode esta célula de novo.
''')

for c in cells:
    c["source"] = [l.replace("@@PASTA@@", PASTA).replace("@@CAPS@@", "[" + ", ".join(str(c2["capitulo"]) for c2 in caps) + "]")
                   for l in c["source"]]
nb = {"cells": cells, "metadata": {"accelerator": "GPU", "colab": {"gpuType": "T4", "provenance": []},
      "kernelspec": {"display_name": "Python 3", "name": "python3"}, "language_info": {"name": "python"}},
      "nbformat": 4, "nbformat_minor": 0}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
    f.write("\n")
print("Notebook gerado:", OUT, f"({len(cells)} células)")
