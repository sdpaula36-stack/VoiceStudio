"""Gera notebooks/Estudio_Jogos_Colab.ipynb (vozes + efeitos: Barraco, Pé na Tábua e Clank).

Uso: python make_nb.py notebooks/Estudio_Jogos_Colab.ipynb <pe-na-tabua>/src/story/dialogos.json
"""
import json
import sys

OUT = sys.argv[1]
DIALOGOS = sys.argv[2]   # src/story/dialogos.json do pe-na-tabua
cells = []

import re, unicodedata, pprint

def _slug(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", t).strip("_")

def _frase(t):
    """MAIÚSCULAS do jogo -> frase normal (o TTS lê melhor)."""
    t = t.lower()
    return re.sub(r"(^|[.!?]\s+|\.\.\.\s*)([a-zà-ú])", lambda m: m.group(1) + m.group(2).upper(), t)

def _pe_falas():
    d = json.load(open(DIALOGOS, encoding="utf-8"))
    out = []
    def walk(x, path):
        if isinstance(x, dict):
            if "texto" in x and "quem" in x:
                out.append((path, x["quem"], x["texto"])); return
            for k, v in x.items():
                if k in ("nota", "versao"): continue
                walk(v, path + [k])
        elif isinstance(x, list):
            for i, v in enumerate(x): walk(v, path + [str(i)])
        elif isinstance(x, str):
            quem = None
            if path[0] == "podio" or path[:2] in (["turne", "depois"],):
                quem = path[-2] if path[0] == "podio" else path[-1]
            if path[:2] == ["turne", "novidades"]:
                quem = "NARRADOR"
            out.append((path, quem, x))
    walk(d, [])
    return out

_VOZES_PE = {
    "NARRADOR":    ("narrador", "male, middle-aged, low pitch", 101, "radio"),
    "O BARÃO":     ("barao",    "male, elderly, very low pitch", 111, None),
    "DONA ZÉLIA":  ("zelia",    "female, elderly, moderate pitch", 121, None),
    "RUSTY KANE":  ("rusty",    "male, middle-aged, low pitch, american accent", 131, None),
    "LA SOMBRA":   ("sombra",   "female, young adult, whisper", 141, None),
    "KLAUS FERRO": ("klaus",    "male, middle-aged, low pitch", 151, None),
    "INGRID NORD": ("ingrid",   "female, young adult, low pitch", 161, None),
    "O ESCORPIÃO": ("escorpiao","male, elderly, low pitch", 171, None),
    "KAZE":        ("kaze",     "male, teenager, moderate pitch, japanese accent", 181, None),
}
# Falas curtas novas (não estão no dialogos.json): avisos de corrida.
_EXTRAS_PE = {
    "narrador": {
        "corrida_3": "Três!", "corrida_2": "Dois!", "corrida_1": "Um!", "corrida_ja": "Já!",
        "corrida_ultima_volta": "Última volta!", "corrida_nitro": "Nitro!",
        "corrida_1o_lugar": "Primeiro lugar!", "corrida_2o_lugar": "Segundo lugar!",
        "corrida_3o_lugar": "Terceiro lugar!",
        "clima_tempestade_areia": "Tempestade de areia à frente!",
        "clima_chuva": "Chuva forte na pista!", "clima_gelo": "Cuidado, gelo na pista!",
    },
    "barao": {
        "barao_ultrapassa_1": "Sai da frente, novato!",
        "barao_ultrapassa_2": "Vinte anos, e você ainda vê a minha traseira.",
        "barao_ultrapassa_3": "Até logo. Muito logo.",
    },
}

def pe_roteiro():
    rot = {}
    for path, quem, texto in _pe_falas():
        if quem not in _VOZES_PE or "{" in texto:
            continue  # falas com marcadores ({RIVAL}, {NO_PAIS}...) ficam em texto
        nome, voz, semente, fx = _VOZES_PE[quem]
        p = rot.setdefault(nome, {"voz": voz, "semente": semente, "falas": {}})
        if fx: p["fx"] = fx
        fid = "_".join(_slug(x) for x in path if x != "turne")
        p["falas"][fid] = _frase(texto)
    for nome, extras in _EXTRAS_PE.items():
        rot[nome]["falas"].update(extras)
    # A fala mais longa vira a referência da voz (primeira da lista).
    for p in rot.values():
        itens = sorted(p["falas"].items(), key=lambda kv: -len(kv[1]))
        p["falas"] = dict([itens[0]] + [kv for kv in p["falas"].items() if kv != itens[0]])
    return rot

PE_ROTEIRO = pprint.pformat(pe_roteiro(), width=110, sort_dicts=False)


def md(s):
    cells.append({"cell_type": "markdown", "metadata": {}, "source": s.strip("\n").splitlines(keepends=True)})


def code(s):
    cells.append({"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
                  "source": s.strip("\n").splitlines(keepends=True)})


md(r'''
# Estúdio de jogos no Colab: vozes e efeitos sonoros

Gera, numa GPU grátis do Google Colab, as **vozes** (VoiceStudio) e os **efeitos sonoros** (Stable Audio Open) dos jogos **Barraco do Bairro**, **Pé na Tábua** e **Clank** (no Clank, só efeitos: rode 1, 2, 8, 9 e 10). Escolha o jogo na célula 2. Tudo é salvo no seu Google Drive, em `MyDrive/EstudioJogos/<jogo>/`.

**Antes de começar**

1. Menu `Ambiente de execução → Alterar o tipo de ambiente de execução → GPU T4`.
2. Para os efeitos sonoros, o modelo `stabilityai/stable-audio-open-1.0` exige aceitar os termos e um token:
   - entre em https://huggingface.co/stabilityai/stable-audio-open-1.0 e aceite os termos (conta grátis);
   - crie um token de leitura em https://huggingface.co/settings/tokens;
   - no Colab, clique na chave 🔑 (barra lateral esquerda), crie o segredo `HF_TOKEN` com o token e ative "Acesso ao notebook".
3. Rode as células de cima para baixo. Pode rodar de novo qualquer célula sem problema.

**Partes**

- **1 a 4b:** preparar (GPU, Drive, instalar e ligar o VoiceStudio, aceitar as licenças do modelo de voz).
- **5 a 7:** vozes dos lutadores e do locutor (edite as listas na célula 5).
- **8 a 9:** efeitos sonoros (edite a lista na célula 8).
- **10:** baixar tudo num `.zip`.

**Licenças:** o modelo de voz padrão (OmniVoice) tem pesos de uso **não comercial** (CC-BY-NC). A célula 4b mostra as licenças e só segue depois que você as aceita. Para um jogo vendido ou com anúncios, use outro motor de voz com licença comercial. O Stable Audio Open 1.0 usa a *Stability AI Community License*: uso comercial grátis enquanto a receita anual for menor que US$ 1 milhão. Confira os termos atuais na página do modelo antes de publicar o jogo.

**Depois de gerar:** copie a pasta `mp3/` do Drive para a pasta do jogo e rode `python -I tools/preparar-sons.py mp3` como de costume.
''')

code(r'''
# ── 1. Conferir a GPU ───────────────────────────────────────────────────────
import shutil, subprocess

if shutil.which("nvidia-smi"):
    print(subprocess.run(["nvidia-smi"], capture_output=True, text=True).stdout)
    print("GPU encontrada.")
else:
    print("=" * 70)
    print("ATENÇÃO: sem GPU. Vá em Ambiente de execução -> Alterar o tipo de")
    print("ambiente de execução -> GPU T4, e rode o notebook de novo do início.")
    print("=" * 70)
''')

code(r'''
# ── 2. Google Drive e pastas de saída ───────────────────────────────────────
import os
from google.colab import drive

drive.mount("/content/drive")

JOGO = "clank"   # escolha o jogo: "barraco", "pe-na-tabua" ou "clank" (só efeitos)
SAIDA = f"/content/drive/MyDrive/EstudioJogos/{JOGO}"
PASTA_WAV = os.path.join(SAIDA, "wav")   # originais, qualidade máxima
PASTA_MP3 = os.path.join(SAIDA, "mp3")   # pronto para tools/preparar-sons.py
for p in (PASTA_WAV, PASTA_MP3):
    os.makedirs(p, exist_ok=True)
print("Os arquivos vão para:", SAIDA)

# Token do Hugging Face (necessário só para os efeitos sonoros, parte 8).
try:
    from google.colab import userdata
    os.environ["HF_TOKEN"] = userdata.get("HF_TOKEN")
    print("HF_TOKEN carregado dos segredos do Colab.")
except Exception:
    print("Sem o segredo HF_TOKEN: as vozes funcionam, os efeitos (parte 8) não.")
''')

code(r'''
# ── 3. Instalar o VoiceStudio (primeira vez: ~5-8 min) ──────────────────────
# Mesma instalação do notebook oficial (notebooks/OmniVoice_Studio_Colab.ipynb),
# sem a interface web: aqui usamos só a API.
import os, shutil, subprocess, sys

REPO_URL = "https://github.com/sdpaula36-stack/VoiceStudio"
REPO_DIR = "/content/VoiceStudio"
os.environ.setdefault("UV_HTTP_TIMEOUT", "300")

def run(cmd, *, cwd=None, what=""):
    shown = cmd if isinstance(cmd, str) else " ".join(cmd)
    print(f"\n$ {shown}")
    rc = subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str)).returncode
    if rc != 0:
        raise SystemExit(f"\nFALHOU: {what or shown} (código {rc}). Veja o erro acima; "
                         "rodar a célula de novo é seguro.")

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

run([sys.executable, "-c",
     "import torch, transformers; "
     "print(f'torch {torch.__version__}, transformers {transformers.__version__}, "
     "CUDA: {torch.cuda.is_available()}'); "
     "from omnivoice.models.omnivoice import OmniVoice; print('Instalação OK')"],
    cwd=REPO_DIR, what="teste de importação")

from huggingface_hub import snapshot_download
print("Baixando o modelo de voz (alguns GB, só na primeira vez)...")
snapshot_download("k2-fsa/OmniVoice")
print("Modelo de voz pronto.")
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
if info:
    print("Servidor já estava ligado:", info)
else:
    subprocess.run(f"kill -9 $(lsof -t -i:{PORT}) 2>/dev/null || true", shell=True)
    env = os.environ.copy()
    env["OMNIVOICE_SERVER_MODE"] = "1"
    env.setdefault("OMNIVOICE_DATA_DIR", "/content/omnivoice_data")
    env["PYTHONUNBUFFERED"] = "1"
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
        tail = open(LOG_PATH, errors="replace").readlines()[-40:]
        raise SystemExit("O servidor não ligou em 5 min. Final do log:\n" + "".join(tail))
    print("Servidor ligado:", info)
''')

code(r'''
# ── 4b. Licenças do modelo de voz ───────────────────────────────────────────
# O VoiceStudio só gera voz depois que você aceita a licença de cada modelo.
# Leia o que aparece abaixo. Se concordar, troque para True e rode de novo.
ACEITO_AS_LICENCAS = False

import requests
BASE = "http://127.0.0.1:3900"
MODELOS_DE_VOZ = ["k2-fsa/OmniVoice", "eustlb/higgs-audio-v2-tokenizer"]

pendentes = []
for repo in MODELOS_DE_VOZ:
    st = requests.get(f"{BASE}/models/licenses/acceptance/{repo}", timeout=30).json()
    print(f"{repo}\n  licença: {st.get('license')}\n  categoria: {st.get('category')}"
          f"\n  situação: {st.get('state')}")
    print(f"  detalhes: https://huggingface.co/{repo}\n")
    if not st.get("accepted"):
        pendentes.append(st)

if not pendentes:
    print("Licenças já aceitas. Pode seguir para as vozes.")
elif not ACEITO_AS_LICENCAS:
    raise SystemExit("Leia as licenças acima. Se concordar, mude ACEITO_AS_LICENCAS para True "
                     "nesta célula e rode de novo. Atenção: 'noncommercial' quer dizer que o "
                     "áudio não pode ser usado em produto comercial.")
else:
    for st in pendentes:
        r = requests.post(f"{BASE}/models/licenses/accept", timeout=30,
                          json={"repo_id": st["repo_id"], "fingerprint": st["fingerprint"],
                                "accepted": True})
        r.raise_for_status()
        print("Aceita:", st["repo_id"])
    print("Pronto. Pode seguir para as vozes.")
''')

md(r'''
## Vozes

A célula 5 tem o **roteiro**: cada personagem tem uma descrição de voz e uma lista de falas. Edite à vontade e rode as células 5 a 7.

- `voz` aceita só estes termos, separados por vírgula: `male`/`female`; `child`, `teenager`, `young adult`, `middle-aged`, `elderly`; `very low pitch`, `low pitch`, `moderate pitch`, `high pitch`, `very high pitch`; `whisper`.
- A primeira fala de cada personagem vira a **voz de referência**, e as outras são clonadas dela. Assim o personagem soa igual em todas as falas. Se a primeira não ficar boa, troque o `semente` e rode de novo.
- **Sotaque brasileiro:** o modelo fala português, mas pode puxar para o de Portugal. O jeito mais garantido é clonar de uma gravação sua (ou de alguém que autorize) com sotaque brasileiro: veja `amostra` na célula 5.
- Os nomes dos arquivos seguem os ids do jogo com o lutador no fim (ex.: `grunt_atk_bira_1`).
''')

code(r'''
# ── 5. Roteiro de vozes (EDITE AQUI) ────────────────────────────────────────
# id do arquivo -> texto. "amostra" (opcional): caminho de um .wav de 5-10 s
# com a voz que você quer clonar (envie pela pasta 📁 à esquerda ou pelo Drive).
ROTEIROS = {}
ROTEIROS["barraco"] = {
    "bira": {
        "voz": "male, middle-aged, low pitch", "semente": 11,
        "falas": {
            "victory_bira": "Sai do balcão que a chapa tá quente!",
            "grunt_atk_bira_1": "Toma!",
            "grunt_atk_bira_2": "Rá!",
            "grunt_hurt_bira_1": "Ai!",
            "grunt_hurt_bira_2": "Ugh!",
            "grunt_hurt_bira_3": "Aaai!",
            "ko_scream_bira_1": "Nããão!",
            "ko_scream_bira_2": "Aaaaah!",
            "special_bira_ovo": "OVO FRITO!",
            "special_bira_toalha": "TOALHADA!",
            "special_bira_espatula": "ESPATULADA!",
        },
    },
    "naldo": {
        "voz": "male, middle-aged, moderate pitch", "semente": 21,
        "falas": {
            "victory_naldo": "Volta aqui que o chapéu volta sozinho.",
            "grunt_atk_naldo_1": "Ê!",
            "grunt_atk_naldo_2": "Opa!",
            "grunt_hurt_naldo_1": "Ai!",
            "grunt_hurt_naldo_2": "Ui!",
            "grunt_hurt_naldo_3": "Aaai!",
            "ko_scream_naldo_1": "Nããão!",
            "ko_scream_naldo_2": "Aaaaah!",
            "special_naldo_chinelo": "CHINELO VOADOR!",
            "special_naldo_arraia": "RABO DE ARRAIA!",
        },
    },
    "zegas": {
        "voz": "male, middle-aged, very low pitch", "semente": 31,
        "falas": {
            "victory_zegas": "Olha o gááás!",
            "grunt_atk_zegas_1": "Hmpf!",
            "grunt_atk_zegas_2": "Rááá!",
            "grunt_hurt_zegas_1": "Ugh!",
            "grunt_hurt_zegas_2": "Ai!",
            "grunt_hurt_zegas_3": "Ooof!",
            "ko_scream_zegas_1": "Nããão!",
            "ko_scream_zegas_2": "Aaaaah!",
            "special_zegas_botijao": "BOTIJÃO ROLANDO!",
            "special_zegas_abraco": "ABRAÇO DO BOTIJÃO!",
        },
    },
    "kaique": {
        "voz": "male, teenager, high pitch", "semente": 41,
        "falas": {
            "victory_kaique": "Foi no grau, mano.",
            "grunt_atk_kaique_1": "Vai!",
            "grunt_atk_kaique_2": "Toma!",
            "grunt_hurt_kaique_1": "Ai!",
            "grunt_hurt_kaique_2": "Ui!",
            "grunt_hurt_kaique_3": "Aaai!",
            "ko_scream_kaique_1": "Nããão!",
            "ko_scream_kaique_2": "Aaaaah!",
            "special_kaique_fumaceira": "FUMACEIRA!",
            "special_kaique_arrancada": "ARRANCADA!",
            "special_kaique_cavalo": "CAVALO DE PAU!",
        },
    },
    "passinho": {
        "voz": "male, young adult, moderate pitch", "semente": 51,
        "falas": {
            "victory_passinho": "Dançou!",
            "grunt_atk_passinho_1": "Ê!",
            "grunt_atk_passinho_2": "Vai!",
            "grunt_hurt_passinho_1": "Ai!",
            "grunt_hurt_passinho_2": "Ui!",
            "grunt_hurt_passinho_3": "Aaai!",
            "ko_scream_passinho_1": "Nããão!",
            "ko_scream_passinho_2": "Aaaaah!",
            "special_passinho_grave": "ONDA DO GRAVE!",
            "special_passinho_quadradinho": "QUADRADINHO!",
        },
    },
    "cida": {
        "voz": "female, middle-aged, moderate pitch", "semente": 61,
        "falas": {
            "victory_cida": "No meu salão quem manda sou eu.",
            "grunt_atk_cida_1": "Toma!",
            "grunt_atk_cida_2": "Rá!",
            "grunt_hurt_cida_1": "Ai!",
            "grunt_hurt_cida_2": "Ui!",
            "grunt_hurt_cida_3": "Aaai!",
            "ko_scream_cida_1": "Nããão!",
            "ko_scream_cida_2": "Aaaaah!",
            "special_cida_laque": "SPRAY DE LAQUÊ!",
            "special_cida_secador": "SECADOR TURBO!",
            "special_cida_bobs": "BOBS VOADORES!",
            "victory_darkcida_base": "A escova agora é definitiva.",
        },
    },
    "locutor": {
        "voz": "male, middle-aged, low pitch", "semente": 71,
        "falas": {
            "announcer_intro": "Bem-vindos ao Barraco do Bairro!",
            "announcer_round1": "Round um!",
            "announcer_round2": "Round dois!",
            "announcer_final_round": "Último round!",
            "announcer_fight": "Porrada!",
            "announcer_ko": "Nocaute!",
            "announcer_you_win": "Você venceu!",
            "announcer_you_lose": "Você perdeu!",
            "announcer_espetinho": "Espetinho!",
            "announcer_gatonet": "Gatonet!",
            "announcer_defendeu": "Defendeu!",
            "announcer_agarrou": "Agarrou!",
            "announcer_contra": "Contra-ataque!",
        },
    },
}

# Pé na Tábua: falas do src/story/dialogos.json (as com {RIVAL}, {NO_PAIS} etc.
# ficam de fora) mais avisos curtos de corrida. O id é o caminho da fala no JSON.
# "fx": "radio" passa a voz por um filtro de rádio no MP3 (célula 7).
ROTEIROS["pe-na-tabua"] = ''' + PE_ROTEIRO + r'''

# Clank: só efeitos sonoros, sem falas (pule as células 3 a 7).
ROTEIROS["clank"] = {}

PERSONAGENS = ROTEIROS[JOGO]

# Barraco: a Dark Cida usa a voz da Dona Cida com efeitos (célula 7): estes
# ids da Dona Cida ganham uma cópia "darkcida" processada.
DARK_CIDA = JOGO == "barraco"

total = sum(len(p["falas"]) for p in PERSONAGENS.values())
print(f"{len(PERSONAGENS)} personagens, {total} falas no roteiro.")
''')

code(r'''
# ── 6. Gerar as vozes (~5-20 s por fala) ────────────────────────────────────
import os, subprocess, requests
from IPython.display import Audio, display

BASE = "http://127.0.0.1:3900"
SO_NOVAS = True   # True: pula arquivos que já existem no Drive. False: refaz tudo.

def gerar(texto, destino, **campos):
    arquivos = campos.pop("files", None)
    dados = {"text": texto, "language": "pt", "effect_preset": "raw", **campos}
    r = requests.post(f"{BASE}/generate", data=dados, files=arquivos, timeout=1800)
    if r.status_code != 200:
        raise SystemExit(f"Erro {r.status_code} em /generate: {r.text[:500]}\n"
                         "Log do servidor: /content/voicestudio_backend.log")
    with open(destino, "wb") as f:
        f.write(r.content)
    return destino

def para_mp3(wav):
    mp3 = os.path.join(PASTA_MP3, os.path.basename(wav)[:-4] + ".mp3")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav,
                    "-codec:a", "libmp3lame", "-q:a", "2", mp3], check=True)
    return mp3

for nome, p in PERSONAGENS.items():
    print(f"\n=== {nome} ({p['voz']}) ===")
    falas = list(p["falas"].items())
    ref_id, ref_texto = falas[0]
    ref_wav = os.path.join(PASTA_WAV, ref_id + ".wav")

    # Fala de referência: clonada da amostra, se houver, ou criada pela descrição.
    if not (SO_NOVAS and os.path.exists(ref_wav)):
        if p.get("amostra"):
            with open(p["amostra"], "rb") as a:
                gerar(ref_texto, ref_wav, seed=p["semente"],
                      files={"ref_audio": (os.path.basename(p["amostra"]), a)})
        else:
            gerar(ref_texto, ref_wav, instruct=p["voz"], seed=p["semente"])
        para_mp3(ref_wav)
    print(f"{ref_id}: {ref_texto}")
    display(Audio(ref_wav))

    # As outras falas são clonadas da referência, para a voz não mudar.
    for fid, texto in falas[1:]:
        wav = os.path.join(PASTA_WAV, fid + ".wav")
        if SO_NOVAS and os.path.exists(wav):
            continue
        with open(ref_wav, "rb") as ref:
            gerar(texto, wav, seed=p["semente"], ref_text=ref_texto,
                  files={"ref_audio": ("ref.wav", ref, "audio/wav")})
        para_mp3(wav)
        print(f"{fid}: {texto}")
        display(Audio(wav))

print("\nVozes prontas em", PASTA_WAV)
''')

code(r'''
# ── 7. Efeitos de voz: Dark Cida (Barraco) e rádio do narrador (Pé na Tábua)
# Ajuste os números para mudar o efeito.
import glob, os
import numpy as np
import soundfile as sf
from pedalboard import Pedalboard, PitchShift, Distortion, Reverb, Gain, Limiter
from IPython.display import Audio, display

efeito = Pedalboard([
    PitchShift(semitones=-4),        # mais grave
    Distortion(drive_db=8),          # rouquidão
    Reverb(room_size=0.6, wet_level=0.25, dry_level=0.8),  # eco
    Gain(gain_db=-2),
    Limiter(threshold_db=-1.0),
])

if DARK_CIDA:
    def aplicar(origem, destino):
        audio, sr = sf.read(origem, dtype="float32", always_2d=True)
        sf.write(destino, efeito(audio.T, sr).T, sr)
        para_mp3(destino)
        print(os.path.basename(destino))
        return destino

    # Gritos e especiais da Dona Cida viram versões "darkcida".
    for wav in sorted(glob.glob(os.path.join(PASTA_WAV, "*_cida*.wav"))):
        if os.path.basename(wav).startswith("victory_"):
            continue  # a Dark Cida tem frase de vitória própria
        aplicar(wav, wav.replace("_cida", "_darkcida"))

    # Frase de vitória da Dark Cida: gravada com a voz da Dona Cida, depois o efeito.
    base = os.path.join(PASTA_WAV, "victory_darkcida_base.wav")
    if os.path.exists(base):
        display(Audio(aplicar(base, os.path.join(PASTA_WAV, "victory_darkcida.wav"))))

# Filtro de rádio: o WAV fica limpo e o MP3 sai com som de rádio de estrada.
from pedalboard import HighpassFilter, LowpassFilter, Compressor
radio = Pedalboard([
    HighpassFilter(cutoff_frequency_hz=400),
    LowpassFilter(cutoff_frequency_hz=3200),
    Compressor(threshold_db=-20, ratio=4),
    Distortion(drive_db=6),
    Gain(gain_db=-3),
    Limiter(threshold_db=-1.0),
])
os.makedirs("/content/fx", exist_ok=True)
for nome, p in PERSONAGENS.items():
    if p.get("fx") != "radio":
        continue
    for fid in p["falas"]:
        wav = os.path.join(PASTA_WAV, fid + ".wav")
        if not os.path.exists(wav):
            continue
        audio, sr = sf.read(wav, dtype="float32", always_2d=True)
        tmp = os.path.join("/content/fx", fid + ".wav")
        sf.write(tmp, radio(audio.T, sr).T, sr)
        para_mp3(tmp)   # substitui o MP3 limpo pelo MP3 com rádio
    print(f"{nome}: MP3 com filtro de rádio")
    display(Audio(tmp))
''')

md(r'''
## Efeitos sonoros

Os efeitos usam o **Stable Audio Open 1.0**, que transforma uma descrição em inglês num som de até 47 s. Ele roda num ambiente Python separado para não mexer na instalação do VoiceStudio.

- Na célula 8, cada efeito tem um `id` (nome do arquivo), a descrição (`prompt`) e a duração em segundos.
- Cada efeito sai em **2 versões** (`_v1`, `_v2`) para você escolher a melhor.
- Descrições curtas e concretas funcionam melhor ("egg sizzling on a hot griddle" rende mais que "som de ovo").
- Se a GPU ficar sem memória, desligue o servidor de vozes antes: `!kill -9 $(lsof -t -i:3900)`.
''')

code(r'''
# ── 8. Lista de efeitos (EDITE AQUI) ────────────────────────────────────────
# (id, prompt em inglês, duração em segundos)
EFEITOS_POR_JOGO = {}
EFEITOS_POR_JOGO["barraco"] = [
    # Projéteis (hoje todos usam "slipper") e impactos ("slipper_hit")
    ("proj_ovo",        "egg sizzling on a hot griddle, short burst", 1.5),
    ("proj_botijao",    "heavy metal gas cylinder rolling on a concrete floor", 2.0),
    ("proj_grave",      "deep bass boom wave from a huge speaker, sub drop", 1.5),
    ("proj_spray",      "aerosol spray can hiss", 1.2),
    ("proj_fumaceira",  "small motorcycle exhaust backfire and smoky rev", 1.5),
    ("hit_ovo",         "raw egg cracking and splatting", 0.8),
    ("hit_lata",        "metal can hit, sharp clang", 0.8),
    ("hit_grave",       "deep low punchy thump", 0.8),
    # Golpes com som próprio
    ("chapeu_bumerangue", "spinning boomerang whoosh flying away and coming back", 2.0),
    ("moto_arrancada",  "125cc motorcycle revving and accelerating fast", 2.5),
    ("moto_derrapada",  "tire screeching skid on asphalt", 1.5),
    ("secador_turbo",   "hair dryer turning on, high pitched whirr", 2.0),
    ("bobs_caindo",     "plastic hair curlers falling and bouncing on a floor", 1.2),
    ("super_fogo",      "fire igniting with a big whoosh", 1.5),
    # Fatalities
    ("fatal_gatonet",   "electric shock with sparks crackling from power lines", 1.5),
    ("fatal_botijao",   "gas cylinder explosion with a long echo", 3.0),
    ("fatal_espetinho", "meat sizzling on a charcoal barbecue grill", 2.5),
    # Ambientes, um por palco (laços)
    ("ambience_baile",    "muffled brazilian funk party heard from outside, crowd chatter, night", 10.0),
    ("ambience_laje",     "rooftop in a city neighborhood, wind, distant dogs barking, kites", 10.0),
    ("ambience_deposito", "empty warehouse room tone, distant metal clanks", 10.0),
    ("ambience_ladeira",  "steep street in a favela, motorcycles passing, people talking", 10.0),
    ("ambience_salao",    "small hair salon, hair dryer in background, radio playing softly", 10.0),
    # Torcida do bairro
    ("crowd_ooh",       "small crowd of neighbors going oooh in surprise", 2.0),
    ("crowd_laugh",     "small crowd laughing", 2.5),
    ("crowd_cheer",     "small crowd clapping and cheering", 3.0),
]
EFEITOS_POR_JOGO["pe-na-tabua"] = [
    # Criaturas e naves (hoje sintetizados em src/audio/music.ts)
    ("dino_rugido",       "giant dinosaur roar, deep and raspy, retro arcade feel", 1.5),
    ("nave_raio",         "UFO tractor beam rising sci-fi zap", 1.0),
    ("nave_porco",        "cartoon pig oink oink", 0.8),
    # Armas (tocarArma)
    ("arma_escudo",       "magic shield activating, bright glassy shimmer", 0.8),
    ("arma_oleo",         "thick oil glugging and splashing on asphalt", 0.8),
    ("arma_pedrada",      "rock thrown and bouncing twice on a road", 1.6),
    ("arma_tachinhas",    "handful of metal tacks scattering on asphalt", 0.6),
    ("arma_marimbondos",  "angry wasp swarm buzzing close", 1.5),
    ("arma_lama",         "mud splash with dripping drops", 0.8),
    ("arma_ima",          "powerful electromagnet humming and clunking metal", 1.2),
    ("pneu_furado",       "tire puncture pop and air hissing out", 1.0),
    # Clima (clima.ts)
    ("clima_trovao",      "distant thunder rumble", 3.0),
    ("clima_vendaval",    "strong gust of wind howling", 2.5),
    ("clima_arvore",      "tree trunk snapping and crashing down", 1.5),
    ("ambiente_chuva",    "steady rain on a car roof, seamless loop", 6.0),
    # Pista
    ("pista_lama",        "car tires driving through thick mud", 1.5),
    ("pista_viaduto",     "car wheels hitting a bridge expansion joint, two thumps", 0.8),
    ("pista_pouso",       "car landing hard after a jump, suspension thud", 0.8),
    ("ambiente_mare",     "waves washing over a coastal road, loop", 6.0),
    ("podio_fogos",       "fireworks popping and crackling", 3.0),
    # Ambientes por país (laços)
    ("ambiente_vesuvio",  "volcano rumbling with bubbling lava", 8.0),
    ("ambiente_areia",    "desert sandstorm wind with sand hissing", 8.0),
    ("ambiente_toquio",   "busy city at night, distant traffic and neon buzz", 8.0),
    ("ambiente_gelo",     "ice cracking and creaking on a frozen fjord, cold wind", 8.0),
]
EFEITOS_POR_JOGO["clank"] = [
    # Hoje tudo é sintetizado em src/ui/sintese.js. O id é o nome do som lá;
    # cada versão vira uma variante nova em escuta.html para comparar.
    # Momentos
    ("dragao",     "huge dragon roar echoing in a stone cavern, deep and menacing", 3.0),
    ("asas",       "giant leathery dragon wings flapping in a cave", 2.0),
    ("fantasma",   "ghostly wail echoing in a crypt, eerie and hollow", 2.5),
    ("dano",       "heavy blunt impact on leather armor, painful thud", 0.6),
    ("tesouro",    "treasure chest lid opening with sparkling magical chimes", 2.0),
    # Mesa
    ("clank",      "metal armor and iron gear clanking loudly as someone stumbles", 1.0),
    ("bolsa",      "small wooden cubes shaken inside a leather pouch", 1.0),
    ("moeda",      "a few gold coins clinking on a wooden table", 0.8),
    ("carta",      "playing card flicked onto a wooden table", 0.5),
    ("compra",     "drawing a single card from a deck, paper slide", 0.4),
    ("embaralhar", "shuffling a deck of playing cards", 1.0),
    ("passo",      "footsteps on a stone dungeon floor, two steps, echo", 0.8),
    ("peca",       "heavy stone slab dragged and set down with a thud", 1.5),
    # Eventos do ambiente
    ("goteira",    "single water drop falling into a puddle in a cave, echo", 0.8),
    ("ossos",      "old bones rattling and rolling on stone", 1.2),
    ("correntes",  "iron chains rattling in a dungeon", 1.5),
    ("batida",     "slow heavy heartbeat, two deep beats", 1.0),
    # Camadas contínuas (laços)
    ("vento",      "cold wind blowing through underground catacombs, seamless loop", 8.0),
    ("respiracao", "sleeping dragon slow deep breathing and low rumble in a cave, seamless loop", 8.0),
]
EFEITOS = EFEITOS_POR_JOGO[JOGO]
VERSOES = 2
PASSOS = 100      # mais passos = mais qualidade e mais tempo (50 já é razoável)
print(f"{len(EFEITOS)} efeitos x {VERSOES} versões.")
''')

code(r'''
# ── 9. Gerar os efeitos (instalação ~2 min; ~10-30 s por efeito) ────────────
import json, os, subprocess, sys

if not os.environ.get("HF_TOKEN"):
    raise SystemExit("Falta o segredo HF_TOKEN (veja o início do notebook) e rode a célula 2 de novo.")

def mostrar(cmd):
    """Roda um comando e mostra a saída na célula (o Colab esconde a saída de subprocessos)."""
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for linha in proc.stdout:
        print(linha, end="", flush=True)
    return proc.wait()

VENV = "/content/sfx-venv"
PY = f"{VENV}/bin/python"
import shutil
if not shutil.which("uv"):
    mostrar([sys.executable, "-m", "pip", "install", "-q", "uv"])
if not os.path.exists(PY):
    # Ambiente separado que reaproveita o torch do Colab e não altera o VoiceStudio.
    mostrar(["uv", "venv", "--python", sys.executable, "--system-site-packages", VENV])
    mostrar(["uv", "pip", "install", "--python", PY,
             "diffusers==0.35.2", "transformers>=4.45,<5", "accelerate", "protobuf",
             "torchsde", "sentencepiece", "soundfile"])
    # O torchsde puxa outro torch para o venv; sem ele, vale o torch do Colab,
    # que combina com o torchvision do sistema ("torchvision::nms does not exist").
    mostrar(["uv", "pip", "uninstall", "--python", PY, "torch"])

roteiro = "/content/sfx_lista.json"
json.dump({"efeitos": EFEITOS, "versoes": VERSOES, "passos": PASSOS,
           "pasta_wav": PASTA_WAV}, open(roteiro, "w"))

script = r"""
import json, os, sys
import torch, soundfile as sf
from diffusers import StableAudioPipeline

cfg = json.load(open(sys.argv[1]))
pipe = StableAudioPipeline.from_pretrained(
    "stabilityai/stable-audio-open-1.0", torch_dtype=torch.float16,
    token=os.environ["HF_TOKEN"]).to("cuda")
sr = pipe.vae.sampling_rate
for i, (fid, prompt, seg) in enumerate(cfg["efeitos"]):
    saidas = [os.path.join(cfg["pasta_wav"], f"{fid}_v{n+1}.wav") for n in range(cfg["versoes"])]
    if all(os.path.exists(s) for s in saidas):
        print("já existe:", fid, flush=True); continue
    g = torch.Generator("cuda").manual_seed(1000 + i)
    audios = pipe(prompt, negative_prompt="low quality, music, speech",
                  num_inference_steps=cfg["passos"], audio_end_in_s=float(seg),
                  num_waveforms_per_prompt=cfg["versoes"], generator=g).audios
    for a, s in zip(audios, saidas):
        sf.write(s, a.T.float().cpu().numpy(), sr)
    print("gerado:", fid, flush=True)
"""
open("/content/sfx_gerar.py", "w").write(script)
rc = mostrar([PY, "/content/sfx_gerar.py", roteiro])
if rc != 0:
    raise SystemExit("A geração de efeitos falhou; veja o erro acima. Se for falta de memória, "
                     "desligue o servidor de vozes (!kill -9 $(lsof -t -i:3900)) e rode de novo.")

from IPython.display import Audio, display
for fid, prompt, _ in EFEITOS:
    for n in range(VERSOES):
        wav = os.path.join(PASTA_WAV, f"{fid}_v{n+1}.wav")
        mp3 = os.path.join(PASTA_MP3, f"{fid}_v{n+1}.mp3")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav,
                        "-codec:a", "libmp3lame", "-q:a", "2", mp3], check=True)
        print(f"{fid}_v{n+1}: {prompt}")
        display(Audio(wav))
''')

code(r'''
# ── 10. Baixar tudo num .zip ────────────────────────────────────────────────
# Os arquivos já estão no seu Drive; isto é só para baixar direto no PC.
import shutil
from google.colab import files

zip_path = shutil.make_archive(f"/content/{JOGO}_sons", "zip", SAIDA)
files.download(zip_path)
''')

md(r'''
## Problemas comuns

- **"Erro 4xx/5xx em /generate":** veja o final de `/content/voicestudio_backend.log` (`!tail -50 /content/voicestudio_backend.log`).
- **Erro 401/403 nos efeitos:** aceite os termos em https://huggingface.co/stabilityai/stable-audio-open-1.0 com a mesma conta do token.
- **O Colab desconectou:** rode de novo da célula 1. Com `SO_NOVAS = True`, o que já está no Drive não é refeito.
- **Voz com sotaque de Portugal:** use `amostra` com uma gravação brasileira na célula 5.
''')

nb = {
    "cells": cells,
    "metadata": {
        "accelerator": "GPU",
        "colab": {"gpuType": "T4", "provenance": [], "toc_visible": True},
        "kernelspec": {"display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 0,
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
    f.write("\n")
print("ok", len(cells), "células")
