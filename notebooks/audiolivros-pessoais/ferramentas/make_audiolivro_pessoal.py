"""Gera o notebook Colab de um audiolivro pessoal com leitura guiada.

Uso: python -I ferramentas/make_audiolivro_pessoal.py colab/Subsolo_Colab.ipynb \
        livros/subsolo/roteiros/subsolo_cap01.json livros/subsolo/roteiros/subsolo_cap02.json

Cada trecho do roteiro é [voz, texto, velocidade, pausa], com duas vozes:
  leitor        só o texto do autor (avisos de corte entre parênteses)
  comentarista  comentários de leitura guiada
Saída por capítulo: capNN_guiada.mp3 (tudo) e capNN_limpa.mp3 (só o leitor).
Antes de gerar, confere o roteiro; sai com erro se algo impedir a narração.
"""
import json
import pprint
import sys

OUT = sys.argv[1]
caps = sorted((json.load(open(p, encoding="utf-8")) for p in sys.argv[2:]), key=lambda c: c["capitulo"])

# ── Conferência do roteiro ───────────────────────────────────────────────────
TERMOS = {"male", "female", "child", "teenager", "young adult", "middle-aged", "elderly",
          "very low pitch", "low pitch", "moderate pitch", "high pitch", "very high pitch", "whisper"}
erros = []
vozes = {}
for c in caps:
    vozes.update(c["vozes"])
for nome, v in vozes.items():
    if {t.strip() for t in v["voz"].split(",")} - TERMOS:
        erros.append(f"voz '{nome}' com termos inválidos")
if set(vozes) != {"leitor", "comentarista"}:
    erros.append("as vozes devem ser exatamente 'leitor' e 'comentarista'")
for c in caps:
    pal = {"leitor": 0, "comentarista": 0}
    for i, t in enumerate(c["trechos"], 1):
        onde = f"cap {c['capitulo']}, trecho {i}"
        if len(t) != 4 or t[0] not in vozes:
            erros.append(f"{onde}: precisa ser [leitor|comentarista, texto, velocidade, pausa]")
            continue
        if len(t[1]) > 300:
            erros.append(f"{onde}: trecho com {len(t[1])} caracteres (máx. 300)")
        if not 0.8 <= t[2] <= 1.2 or not 0 <= t[3] <= 3:
            erros.append(f"{onde}: velocidade ou pausa fora da faixa")
        pal[t[0]] += len(t[1].split())
    cortes_falados = sum(1 for t in c["trechos"] if t[0] == "leitor" and t[1].startswith("(Corte:"))
    if cortes_falados != len(c.get("cortes", [])):
        erros.append(f"cap {c['capitulo']}: {len(c.get('cortes', []))} cortes listados, {cortes_falados} anunciados")
    print(f"cap {c['capitulo']}: texto {pal['leitor'] / 140:.1f} min, comentários {pal['comentarista'] / 140:.1f} min")
if erros:
    raise SystemExit("ERROS:\n" + "\n".join(erros))

rot = caps[0]
VOZES = pprint.pformat(vozes, width=100, sort_dicts=False)
CAPITULOS = "{\n" + "".join(
    f"    {c['capitulo']}: {{\"titulo\": {json.dumps(c['titulo'], ensure_ascii=False)}, \"trechos\": [\n"
    + "".join(f"        {json.dumps(t, ensure_ascii=False)},\n" for t in c["trechos"]) + "    ]},\n"
    for c in caps) + "}"
PASTA = rot["pasta"]
CORTES = "\n".join(f"- {x}" for c in caps for x in c.get("cortes", []))
cells = []


def md(s):
    cells.append({"cell_type": "markdown", "metadata": {}, "source": s.strip("\n").splitlines(keepends=True)})


def code(s):
    cells.append({"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
                  "source": s.strip("\n").splitlines(keepends=True)})


md(f'''
# Audiolivro com leitura guiada: {rot["livro"]}

{rot["autor"]}. Fonte: {rot["fonte"]}

Duas vozes, nunca trocadas: o **leitor** lê só o texto do autor, e o **comentarista** entra entre os trechos com contexto, ligações dentro da obra e com outras obras. Cada corte é anunciado pelo leitor entre parênteses.

**Antes de começar:** menu `Ambiente de execução → Alterar o tipo de ambiente de execução → GPU T4`. Depois rode as células de cima para baixo. Rodar de novo qualquer célula é seguro.

**Saída** (no seu Google Drive, em `MyDrive/Audiolivros-pessoais/{PASTA}/capNN/`), para cada capítulo:
- `capNN_guiada.mp3`: texto e comentários, com um sinal curto antes e depois de cada comentário;
- `capNN_limpa.mp3`: só o texto do autor, para reouvir sem comentários.

**Cortes deste lote:**
{CORTES}

**Licença:** a voz padrão (OmniVoice) é de uso **não comercial** (CC-BY-NC). As vozes são sintéticas, sem clonar ninguém.
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

CAPITULOS_PARA_GERAR = @@CAPS@@   # quais capítulos narrar (ex.: [2])

LIVRO = "/content/drive/MyDrive/Audiolivros-pessoais/@@PASTA@@"
PASTA_VOZES = os.path.join(LIVRO, "vozes")
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
# ── 4.5. Aceitar as licenças dos modelos (obrigatório antes de gerar) ───────
# Sem este passo o /generate falha. Rodar esta célula aceita as licenças em seu nome:
# OmniVoice é CC-BY-NC (uso NÃO comercial: o áudio não pode ser vendido).
import requests
BASE = "http://127.0.0.1:3900"

for repo in ("k2-fsa/OmniVoice", "eustlb/higgs-audio-v2-tokenizer"):
    st = requests.get(f"{BASE}/models/licenses/acceptance/{repo}", timeout=30).json()
    if st.get("accepted"):
        print(f"[ok] {repo} já aceito")
        continue
    r = requests.post(
        f"{BASE}/models/licenses/accept",
        json={"repo_id": repo, "fingerprint": st["fingerprint"], "accepted": True},
        timeout=30,
    )
    r.raise_for_status()
    print(f"[aceito] {repo} ({st.get('license')})")
''')

md('''
## Roteiro

Cada trecho é `[voz, texto, velocidade, pausa depois em segundos]`, com voz `leitor` ou `comentarista`.

- O **leitor** só lê frases do autor. Um corte aparece como `(Corte: ...)` e fica nas duas versões.
- O **comentarista** só entra entre trechos, nunca no meio de uma frase do autor.
- **voz** aceita só estes termos: `male`/`female`; `child`, `teenager`, `young adult`, `middle-aged`, `elderly`; `very low pitch` … `very high pitch`; `whisper`. Se não gostar de uma voz, troque a `semente`.

Edite à vontade. Os trechos que você mudar são gerados de novo na célula 7.
''')

code(f'''
# ── 5. Roteiro (EDITE AQUI) ─────────────────────────────────────────────────
VOZES = {VOZES}

CAPITULOS = {CAPITULOS}

for n, c in CAPITULOS.items():
    m = {{v: sum(len(t[1].split()) for t in c["trechos"] if t[0] == v) / 140 for v in VOZES}}
    print(f"Capítulo {{n}}, {{c['titulo']}}: texto {{m['leitor']:.1f}} min, comentários {{m['comentarista']:.1f}} min.")
''')

code(r'''
# ── 6. Criar as duas vozes e ouvir (troque a semente se não gostar) ─────────
import hashlib, os, requests
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

REF = {}   # voz -> (wav de referência, texto)
for nome, v in VOZES.items():
    texto = next(max(falas, key=len) for _, c in sorted(CAPITULOS.items())
                 if (falas := [t[1] for t in c["trechos"] if t[0] == nome]))
    wav = os.path.join(PASTA_VOZES, f"{nome}_{chave(v, texto)}.wav")
    if not os.path.exists(wav):
        gerar(texto, wav, instruct=v["voz"], seed=v["semente"])
    REF[nome] = (wav, texto)
    print(f"{nome} ({v['voz']}, semente {v['semente']}): {texto}")
    display(Audio(wav))
''')

code(r'''
# ── 7. Narrar e montar cada capítulo (guiada e limpa) ───────────────────────
import os, subprocess
import numpy as np
import soundfile as sf
from IPython.display import Audio, display

def narrar(n):
    pasta = os.path.join(LIVRO, f"cap{n:02d}", "trechos")
    os.makedirs(pasta, exist_ok=True)
    saida = []
    for i, (quem, texto, vel, pausa) in enumerate(CAPITULOS[n]["trechos"], 1):
        ref_wav, ref_texto = REF[quem]
        wav = os.path.join(pasta, f"{i:03d}_{quem}_{chave(os.path.basename(ref_wav), texto, vel)}.wav")
        if not os.path.exists(wav):
            with open(ref_wav, "rb") as ref:
                gerar(texto, wav, seed=VOZES[quem]["semente"], ref_text=ref_texto, speed=vel,
                      files={"ref_audio": ("ref.wav", ref, "audio/wav")})
            print(f"{n}.{i:03d} {quem}: {texto}")
        saida.append((quem, wav, pausa))
    return saida

def _nota(f, dur, vol, sr):
    t = np.arange(int(dur * sr)) / sr
    env = np.clip(t / 0.02, 0, 1) * np.exp(-4 * t)
    return (vol * (np.sin(2 * np.pi * f * t) + 0.2 * np.sin(4 * np.pi * f * t)) * env).astype("float32")

def sinal(sr, entra):
    # Duas notas curtas e baixas: sobem quando o comentário começa, descem quando acaba.
    fs = (440.0, 659.25) if entra else (659.25, 440.0)
    out = np.zeros(int(1.0 * sr), dtype="float32")
    for k, f in enumerate(fs):
        nota = _nota(f, 0.6, 0.06, sr)
        i = int(k * 0.18 * sr)
        out[i:i + len(nota)] += nota[:len(out) - i]
    return out

def exportar(audio, sr, pasta, nome):
    tmp = os.path.join(pasta, nome + ".wav")
    sf.write(tmp, audio, sr)
    mp3 = os.path.join(pasta, nome + ".mp3")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp,
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "44100",
                    "-codec:a", "libmp3lame", "-q:a", "2", mp3], check=True)
    os.remove(tmp)
    print(f"{nome}.mp3: {len(audio) / sr / 60:.1f} min")
    display(Audio(mp3))

def montar(n, trechos):
    sr = None
    guiada, limpa, anterior = [], [], "leitor"
    for quem, wav, pausa in trechos:
        a, s = sf.read(wav, dtype="float32", always_2d=True)
        sr = sr or s
        assert s == sr, f"taxa de amostragem diferente em {wav}"
        fala = a.mean(axis=1)
        silencio = np.zeros(int(pausa * sr), dtype="float32")
        if quem != anterior:
            guiada += [sinal(sr, entra=(quem == "comentarista")), np.zeros(int(0.3 * sr), dtype="float32")]
        guiada += [fala, silencio]
        if quem == "leitor":
            limpa += [fala, silencio]
        anterior = quem
    if anterior == "comentarista":
        guiada.append(sinal(sr, entra=False))
    um_seg = np.zeros(sr, dtype="float32")
    pasta = os.path.join(LIVRO, f"cap{n:02d}")
    exportar(np.concatenate([um_seg, *guiada, um_seg]), sr, pasta, f"cap{n:02d}_guiada")
    exportar(np.concatenate([um_seg, *limpa, um_seg]), sr, pasta, f"cap{n:02d}_limpa")

REFAZER = False   # True: narra de novo capítulos que já têm os dois MP3

for n in CAPITULOS_PARA_GERAR:
    print(f"\n=== Capítulo {n}: {CAPITULOS[n]['titulo']} ===")
    prontos = [os.path.join(LIVRO, f"cap{n:02d}", f"cap{n:02d}_{v}.mp3") for v in ("guiada", "limpa")]
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
