"""Estúdio de audiolivros: um motor só para narrar qualquer livro do catálogo.

O notebook `Estudio_Audiolivros_Colab.ipynb` usa este arquivo no Colab: você escolhe o
livro, clica em "Executar tudo" e ele narra só os capítulos que ainda faltam.

Também roda no PC, para preparar um livro (precisa só de Python 3.10+):

    python -I estudio.py validar narizinho                 # roteiros do livro (lidos do git)
    python -I estudio.py validar roteiros/*.json --tipo pcd # arquivos soltos
    python -I estudio.py baixar gutenberg 1661 pasta_saida
    python -I estudio.py baixar wikisource pt "As Reinações de Narizinho" pasta_saida
    python -I estudio.py notebook Estudio_Audiolivros_Colab.ipynb

Tipos de livro (campo "tipo" em livros.json):
    pcd      audiolivros adaptados: capNN_A_so_voz.mp3 e capNN_B_com_ambiente.mp3
    pessoal  leitura guiada: capNN_guiada.mp3 e capNN_limpa.mp3

As lições aprendidas ficam em LICOES.md. Quando uma lição vira regra, ela entra aqui
(na validação ou na narração) para não depender de memória.
"""
import glob
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
CATALOGO = os.path.join(AQUI, "livros.json")
BRANCH_DO_ESTUDIO = "main"   # onde este arquivo mora no fork

LICENCAS = ("k2-fsa/OmniVoice", "eustlb/higgs-audio-v2-tokenizer")
TERMOS_DE_VOZ = {"male", "female", "child", "teenager", "young adult", "middle-aged", "elderly",
                 "very low pitch", "low pitch", "moderate pitch", "high pitch", "very high pitch",
                 "whisper"}
EFEITOS_VALIDOS = {"transicao", "magia", "agua", "galope", "porta", "zumbido", "festa"}  # SONOPLASTIA.md
MAX_EFEITOS = 6
VERSOES = {"pcd": ("A_so_voz", "B_com_ambiente"), "pessoal": ("guiada", "limpa")}
RAIZ_DRIVE = {"pcd": "Audiolivros", "pessoal": "Audiolivros-pessoais"}
AGENTE = "EstudioAudiolivros/1.0 (projeto pessoal, nao comercial)"


# ════════════════════════════════════════════════════════════════════════════
# Catálogo e roteiros
# ════════════════════════════════════════════════════════════════════════════

def catalogo():
    with open(CATALOGO, encoding="utf-8") as f:
        return {k: v for k, v in json.load(f).items() if not k.startswith("_")}


def livro(nome):
    cat = catalogo()
    if nome not in cat:
        raise SystemExit(f"Livro '{nome}' não está no catálogo (livros.json). Livros: {', '.join(cat)}")
    return cat[nome]


def pasta_drive(cfg, drive="/content/drive/MyDrive"):
    return os.path.join(drive, RAIZ_DRIVE[cfg["tipo"]], cfg["pasta"])


def _git(repo_dir, *args):
    r = subprocess.run(["git", "-C", repo_dir, *args], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} falhou:\n{r.stderr}")
    return r.stdout


def roteiros_do_git(repo_dir, onde):
    """Lê os roteiros direto da branch do fork, sem trocar a branch do clone."""
    b, d, pref = onde["branch"], onde["dir"].rstrip("/"), onde["prefixo"]
    ref = f"refs/remotes/origin/{b}"
    _git(repo_dir, "fetch", "-q", "--depth", "1", "origin", f"+refs/heads/{b}:{ref}")
    nomes = [n for n in _git(repo_dir, "ls-tree", "--name-only", ref, d + "/").split()
             if os.path.basename(n).startswith(pref) and n.endswith(".json")]
    return [(f"{b}:{n}", json.loads(_git(repo_dir, "show", f"{ref}:{n}"))) for n in nomes]


def roteiros_da_pasta(pasta):
    caps = []
    for p in sorted(glob.glob(os.path.join(pasta, "*.json"))):
        with open(p, encoding="utf-8") as f:
            caps.append((p, json.load(f)))
    return caps


def carregar_roteiros(nome, repo_dir, livro_dir=None):
    """Roteiros de um livro. Se o Drive tiver <livro>/roteiros/*.json, eles têm prioridade
    (assim dá para editar um roteiro no Drive e narrar de novo sem mexer no git)."""
    cfg = livro(nome)
    no_drive = os.path.join(livro_dir, "roteiros") if livro_dir else None
    if no_drive and glob.glob(os.path.join(no_drive, "*.json")):
        print(f"Usando os roteiros do Drive: {no_drive}")
        return roteiros_da_pasta(no_drive)
    print(f"Lendo os roteiros do fork: branch {cfg['roteiros']['branch']}, {cfg['roteiros']['dir']}")
    return roteiros_do_git(repo_dir, cfg["roteiros"])


# ════════════════════════════════════════════════════════════════════════════
# Validação (junta validar_roteiro.py e a conferência de make_audiolivro_pessoal.py)
# ════════════════════════════════════════════════════════════════════════════

def validar(caps, tipo):
    """caps: lista de (origem, roteiro). Devolve (erros, avisos)."""
    erros, avisos, vozes, sementes, numeros = [], [], {}, {}, {}
    caps = sorted(caps, key=lambda pc: pc[1].get("capitulo", 0))
    for p, c in caps:
        for campo in ("livro", "capitulo", "titulo", "vozes", "trechos"):
            if campo not in c:
                erros.append(f"{p}: falta o campo '{campo}'")
        n = c.get("capitulo")
        if n in numeros:
            erros.append(f"{p}: capítulo {n} repetido (também em {numeros[n]})")
        numeros[n] = p
        for nome, v in c.get("vozes", {}).items():
            termos = {t.strip() for t in v.get("voz", "").split(",")}
            if termos - TERMOS_DE_VOZ:
                erros.append(f"{p}: voz de '{nome}' tem termos inválidos: {sorted(termos - TERMOS_DE_VOZ)}")
            if not isinstance(v.get("semente"), int):
                erros.append(f"{p}: voz de '{nome}' sem 'semente' inteira")
            if v.get("semente") in sementes and sementes[v["semente"]] != nome:
                avisos.append(f"{p}: '{nome}' usa a mesma semente de '{sementes[v['semente']]}'")
            if nome in vozes and vozes[nome] != v:
                avisos.append(f"{p}: voz de '{nome}' redefinida; vale a última, e a voz muda daqui em diante")
            sementes[v.get("semente")] = nome
            vozes[nome] = v
        if tipo == "pcd" and c.get("ambiente", "riacho") not in ("riacho", "nenhum"):
            erros.append(f"{p}: 'ambiente' deve ser \"riacho\" ou \"nenhum\"")

        palavras, n_efeitos, cortes_falados = {}, 0, 0
        for i, t in enumerate(c.get("trechos", []), 1):
            onde = f"{p}, trecho {i}"
            tamanhos = (4, 5) if tipo == "pcd" else (4,)
            if not (isinstance(t, list) and len(t) in tamanhos):
                erros.append(f"{onde}: precisa ser [voz, texto, velocidade, pausa]"
                             + (" ou com um efeito no fim" if tipo == "pcd" else ""))
                continue
            quem, texto, vel, pausa = t[:4]
            if len(t) == 5:
                n_efeitos += 1
                if t[4] not in EFEITOS_VALIDOS:
                    erros.append(f"{onde}: efeito '{t[4]}' não existe; use um destes: {sorted(EFEITOS_VALIDOS)}")
            if quem not in vozes:
                erros.append(f"{onde}: voz '{quem}' sem definição (aqui ou num capítulo anterior)")
            if not isinstance(texto, str) or not texto.strip():
                erros.append(f"{onde}: texto vazio")
                continue
            if not (isinstance(vel, (int, float)) and 0.8 <= vel <= 1.2):
                erros.append(f"{onde}: velocidade {vel} fora de 0.8 a 1.2")
            if not (isinstance(pausa, (int, float)) and 0 <= pausa <= 3):
                erros.append(f"{onde}: pausa {pausa} fora de 0 a 3 segundos")
            if len(texto) > 300:
                (erros if tipo == "pessoal" else avisos).append(
                    f"{onde}: trecho longo ({len(texto)} caracteres, máx. 300); divida em dois")
            if tipo == "pcd" and any(len(f.split()) > 25 for f in re.split(r"[.!?]", texto)):
                avisos.append(f"{onde}: frase com mais de 25 palavras; o guia pede frases curtas")
            if tipo == "pessoal" and quem == "leitor" and texto.startswith("(Corte:"):
                cortes_falados += 1
            palavras[quem] = palavras.get(quem, 0) + len(texto.split())

        total = sum(palavras.values())
        if tipo == "pcd":
            if n_efeitos > MAX_EFEITOS:
                avisos.append(f"{p}: {n_efeitos} efeitos; o limite leve é {MAX_EFEITOS} por capítulo")
            if total and not 300 <= total <= 1100:
                avisos.append(f"{p}: {total} palavras; o guia pede de 500 a 1.000 (4 a 8 min)")
        else:
            if cortes_falados != len(c.get("cortes", [])):
                erros.append(f"{p}: {len(c.get('cortes', []))} cortes listados, {cortes_falados} anunciados")
    if tipo == "pessoal" and vozes and set(vozes) != {"leitor", "comentarista"}:
        erros.append(f"as vozes devem ser exatamente 'leitor' e 'comentarista' (achei {sorted(vozes)})")
    pastas = {c.get("pasta") for _, c in caps}
    if len(pastas) > 1:
        avisos.append(f"campo 'pasta' diferente entre capítulos: {sorted(map(str, pastas))}")
    nums = sorted(n for n in numeros if isinstance(n, int))
    if nums and nums != list(range(nums[0], nums[-1] + 1)):
        avisos.append(f"faltam capítulos na sequência: {sorted(set(range(nums[0], nums[-1] + 1)) - set(nums))}")
    return erros, avisos


def relatorio(caps, tipo):
    erros, avisos = validar(caps, tipo)
    for _, c in sorted(caps, key=lambda pc: pc[1].get("capitulo", 0)):
        pal = sum(len(t[1].split()) for t in c.get("trechos", []) if isinstance(t, list) and len(t) > 1)
        print(f"  cap {c.get('capitulo')}: {c.get('titulo')} ({len(c.get('trechos', []))} trechos, "
              f"~{pal / 135:.1f} min)")
    for a in avisos:
        print("AVISO:", a)
    for e in erros:
        print("ERRO:", e)
    print("Tudo certo para narrar." if not erros else f"{len(erros)} erro(s): corrija antes de narrar.")
    return erros


def juntar(caps):
    """VOZES e CAPITULOS no mesmo formato dos notebooks antigos (as chaves dos arquivos
    em cache dependem disso: mudar aqui faria o Colab narrar tudo de novo)."""
    caps = sorted((c for _, c in caps), key=lambda c: c["capitulo"])
    vozes = {}
    for c in caps:
        vozes.update(c["vozes"])
    capitulos = {c["capitulo"]: {"titulo": c["titulo"], "ambiente": c.get("ambiente", "riacho"),
                                 "trechos": c["trechos"]} for c in caps}
    return vozes, capitulos


# ════════════════════════════════════════════════════════════════════════════
# Situação no Drive e escolha dos capítulos
# ════════════════════════════════════════════════════════════════════════════

def mp3s(livro_dir, tipo, n):
    return [os.path.join(livro_dir, f"cap{n:02d}", f"cap{n:02d}_{v}.mp3") for v in VERSOES[tipo]]


def pronto(livro_dir, tipo, n):
    return all(map(os.path.exists, mp3s(livro_dir, tipo, n)))


def escolher(pedido, capitulos, livro_dir, tipo, refazer=False):
    """pedido: "" = só os que faltam; "todos"; ou "4-10, 12"."""
    pedido = str(pedido).strip().lower()
    if pedido in ("", "faltam", "faltantes"):
        return [n for n in sorted(capitulos) if refazer or not pronto(livro_dir, tipo, n)]
    if pedido == "todos":
        lista = sorted(capitulos)
    else:
        lista = []
        for parte in re.split(r"[,\s]+", pedido):
            if not parte:
                continue
            a, _, b = parte.partition("-")
            lista += range(int(a), int(b or a) + 1)
    fora = [n for n in lista if n not in capitulos]
    if fora:
        raise SystemExit(f"Capítulos sem roteiro: {fora}. Este livro tem: {sorted(capitulos)}")
    return [n for n in lista if refazer or not pronto(livro_dir, tipo, n)]


# ════════════════════════════════════════════════════════════════════════════
# Narração (o mesmo código dos notebooks que já narraram Narizinho, Sherlock e Subsolo)
# ════════════════════════════════════════════════════════════════════════════

def _mostrar(caminho):
    try:
        from IPython.display import Audio, display
        display(Audio(caminho))
    except Exception:
        pass


def chave(*partes):
    return hashlib.sha1(repr(partes).encode()).hexdigest()[:8]


class Narrador:
    def __init__(self, base, livro_dir, tipo, vozes, capitulos, log_path="/content/voicestudio_backend.log"):
        self.base, self.livro_dir, self.tipo = base, livro_dir, tipo
        self.vozes, self.capitulos, self.log_path = vozes, capitulos, log_path
        self.pasta_vozes = os.path.join(livro_dir, "vozes")
        os.makedirs(self.pasta_vozes, exist_ok=True)
        self.ref = {}

    def gerar(self, texto, destino, **campos):
        import requests
        arquivos = campos.pop("files", None)
        dados = {"text": texto, "language": "pt", "effect_preset": "raw", **campos}
        r = requests.post(f"{self.base}/generate", data=dados, files=arquivos, timeout=1800)
        if r.status_code != 200:
            dica = ""
            if "licen" in r.text.lower():
                dica = "\nDICA: rode a célula 4.5 (aceitar as licenças) e tente de novo."
            raise SystemExit(f"Erro {r.status_code} em /generate: {r.text[:500]}{dica}\nLog: {self.log_path}")
        tmp = destino + ".parcial"
        with open(tmp, "wb") as f:
            f.write(r.content)
        os.replace(tmp, destino)   # nunca fica um .wav pela metade se a sessão cair

    def criar_vozes(self, ouvir=True):
        """Uma fala de referência por voz: a fala mais longa no primeiro capítulo em que ela aparece."""
        for nome, v in self.vozes.items():
            falas_por_cap = ([t[1] for t in c["trechos"] if t[0] == nome]
                             for _, c in sorted(self.capitulos.items()))
            texto = next((max(f, key=len) for f in falas_por_cap if f), None)
            if texto is None:
                print(f"{nome}: definida, mas sem falas; pulei.")
                continue
            arq = f"{nome}_{chave(v, texto)}.wav"
            wav = os.path.join(self.pasta_vozes, arq)
            antigo = os.path.join(self.livro_dir, "cap01", "vozes", arq)   # versão do primeiro piloto
            if not os.path.exists(wav) and os.path.exists(antigo):
                shutil.copy(antigo, wav)
            novo = not os.path.exists(wav)
            if novo:
                if v.get("amostra"):
                    with open(v["amostra"], "rb") as a:
                        self.gerar(texto, wav, seed=v["semente"], files={"ref_audio": ("amostra.wav", a)})
                else:
                    self.gerar(texto, wav, instruct=v["voz"], seed=v["semente"])
            self.ref[nome] = (wav, texto)
            print(f"{nome} ({v['voz']}, semente {v['semente']}){' [nova]' if novo else ''}: {texto[:90]}")
            if ouvir and novo:
                _mostrar(wav)

    def narrar(self, n):
        pasta = os.path.join(self.livro_dir, f"cap{n:02d}", "trechos")
        os.makedirs(pasta, exist_ok=True)
        saida, novos = [], 0
        for i, t in enumerate(self.capitulos[n]["trechos"], 1):
            quem, texto, vel, pausa = t[:4]
            efeito = t[4] if len(t) > 4 else None
            ref_wav, ref_texto = self.ref[quem]
            wav = os.path.join(pasta, f"{i:03d}_{quem}_{chave(os.path.basename(ref_wav), texto, vel)}.wav")
            if not os.path.exists(wav):
                with open(ref_wav, "rb") as ref:
                    self.gerar(texto, wav, seed=self.vozes[quem]["semente"], ref_text=ref_texto, speed=vel,
                               files={"ref_audio": ("ref.wav", ref, "audio/wav")})
                novos += 1
                print(f"  {n}.{i:03d} {quem}: {texto[:80]}")
            saida.append((quem, wav, pausa, efeito))
        print(f"  {len(saida)} trechos ({novos} novos, {len(saida) - novos} reaproveitados)")
        return saida

    def montar(self, n, trechos):
        if self.tipo == "pcd":
            return montar_pcd(n, trechos, self.livro_dir, self.capitulos[n].get("ambiente", "riacho"))
        return montar_pessoal(n, trechos, self.livro_dir)

    def capitulo(self, n):
        print(f"\n=== Capítulo {n}: {self.capitulos[n]['titulo']} ===")
        self.montar(n, self.narrar(n))


def exportar(audio, sr, pasta, nome, ouvir=True):
    import soundfile as sf
    with tempfile.TemporaryDirectory() as tmpdir:   # o .wav temporário não vai para o Drive
        tmp = os.path.join(tmpdir, nome + ".wav")
        sf.write(tmp, audio, sr)
        mp3 = os.path.join(pasta, nome + ".mp3")
        # Volume normalizado para fone e caixinha: -16 LUFS, pico máximo -1.5 dBTP.
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp,
                        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "44100",
                        "-codec:a", "libmp3lame", "-q:a", "2", mp3 + ".parcial.mp3"], check=True)
        os.replace(mp3 + ".parcial.mp3", mp3)
    print(f"  {nome}.mp3: {len(audio) / sr / 60:.1f} min")
    if ouvir:
        _mostrar(mp3)


def _ler(wav):
    import soundfile as sf
    a, s = sf.read(wav, dtype="float32", always_2d=True)
    return a.mean(axis=1), s


# ── PCD: versão A (só voz) e B (vinheta, sonoplastia leve, riacho) ───────────

def montar_pcd(n, trechos, livro_dir, ambiente="riacho", ouvir=True):
    import numpy as np
    partes, marcas, sr, pos = [], [], None, 0
    for _, wav, pausa, efeito in trechos:
        fala, s = _ler(wav)
        sr = sr or s
        assert s == sr, f"taxa de amostragem diferente em {wav}"
        pos += len(fala)
        if efeito:
            som = EFEITOS[efeito](sr)
            pausa = max(pausa, len(som) / sr + 0.4)   # o som cabe inteiro na pausa
            marcas.append((pos + int(0.15 * sr), som))
        partes += [fala, np.zeros(int(pausa * sr), dtype="float32")]
        pos += int(pausa * sr)
    voz = np.concatenate(partes)
    # Sons das pausas: 15 dB abaixo da fala (RMS) e pico até 1/3 do pico da fala.
    ativo = voz[np.abs(voz) > 0.01]
    rms_voz = float(np.sqrt((ativo ** 2).mean())) if len(ativo) else 0.1
    sons = np.zeros_like(voz)
    for ini, som in marcas:
        sa = som[np.abs(som) > 1e-4]
        g = rms_voz * 10 ** (-15 / 20) / float(np.sqrt((sa ** 2).mean()))
        g = min(g, np.abs(voz).max() / 3 / float(np.abs(som).max()))
        sons[ini:ini + len(som)] += (som * g)[:len(sons) - ini]
    fundo = riacho(len(voz), sr) if ambiente == "riacho" else 0
    um_seg = np.zeros(sr, dtype="float32")
    pasta = os.path.join(livro_dir, f"cap{n:02d}")
    exportar(np.concatenate([um_seg, voz, um_seg]), sr, pasta, f"cap{n:02d}_A_so_voz", ouvir)
    exportar(np.concatenate([vinheta(sr), um_seg, voz + sons + fundo, um_seg, vinheta(sr)]),
             sr, pasta, f"cap{n:02d}_B_com_ambiente", ouvir)


def tom(freq, dur, vol, sr):
    import numpy as np
    t = np.arange(int(dur * sr)) / sr
    return (vol * np.sin(2 * np.pi * freq * t) * np.exp(-3 * t)).astype("float32")


def vinheta(sr):
    import numpy as np
    # Três notas suaves (dó, mi, sol), sem ataque forte.
    v = np.zeros(int(2.2 * sr), dtype="float32")
    for k, f in enumerate([523.25, 659.25, 783.99]):
        nota = tom(f, 1.4, 0.12, sr)
        ini = int(k * 0.35 * sr)
        v[ini:ini + len(nota)] += nota
    return v


def riacho(n, sr):
    import numpy as np
    # Ruído suave filtrado, que lembra água correndo, bem baixo e com entrada lenta.
    rng = np.random.default_rng(7)
    r = np.convolve(rng.standard_normal(n + 400).astype("float32"),
                    np.ones(40, dtype="float32") / 40, mode="valid")[:n]
    r *= 0.01 * (1 + 0.3 * np.sin(2 * np.pi * 0.15 * np.arange(n) / sr))
    fade = min(n // 2, 4 * sr)
    r[:fade] *= np.linspace(0, 1, fade)
    r[-fade:] *= np.linspace(1, 0, fade)
    return r


# Sete sons curtos, sintetizados aqui mesmo, sempre iguais (mesmo som = mesmo sentido).
# Entram só nas pausas, nunca por cima da fala; ataque suave; pico baixo.

def _env(n, sr, ataque=0.03, queda=4.0):
    import numpy as np
    t = np.arange(n) / sr
    a = np.clip(t / ataque, 0, 1)
    return (a * np.exp(-queda * t)).astype("float32")


def _nota(f, dur, vol, sr, queda=3.0):
    import numpy as np
    t = np.arange(int(dur * sr)) / sr
    som = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t)
    return (vol * som * _env(len(t), sr, 0.02, queda)).astype("float32")


def _suave(x, k):
    import numpy as np
    return np.convolve(x, np.ones(k, dtype="float32") / k, mode="same").astype("float32")


def _junta(sr, dur, pecas):
    import numpy as np
    out = np.zeros(int(dur * sr), dtype="float32")
    for ini, p in pecas:
        i = int(ini * sr)
        p = p[:len(out) - i]
        out[i:i + len(p)] += p
    return out


def ef_transicao(sr):   # troca de cena: duas notas que descem (sol, dó)
    return _junta(sr, 1.3, [(0, _nota(783.99, 1.0, 0.07, sr)), (0.3, _nota(523.25, 1.0, 0.07, sr))])


def ef_magia(sr):       # encanto, sonho, feitiço: quatro notas agudas subindo
    fs = [1046.5, 1318.5, 1568.0, 2093.0]
    return _junta(sr, 1.5, [(k * 0.12, _nota(f, 0.9, 0.035, sr, 4.0)) for k, f in enumerate(fs)])


def ef_agua(sr):        # mergulho / água: ruído abafado + duas bolhas
    import numpy as np
    rng = np.random.default_rng(11)
    n = int(0.6 * sr)
    chua = _suave(rng.standard_normal(n).astype("float32"), 60) * _env(n, sr, 0.04, 6.0) * 0.6

    def bolha(f0):
        t = np.arange(int(0.12 * sr)) / sr
        return (0.04 * np.sin(2 * np.pi * (f0 + 900 * t) * t) * _env(len(t), sr, 0.01, 20)).astype("float32")
    return _junta(sr, 0.9, [(0, chua), (0.35, bolha(500)), (0.55, bolha(650))])


def ef_galope(sr):      # cavalinho: pac, pac, pac (quatro batidinhas de madeira)
    import numpy as np

    def pac(f):
        t = np.arange(int(0.08 * sr)) / sr
        return (0.09 * np.sin(2 * np.pi * f * t) * _env(len(t), sr, 0.003, 45)).astype("float32")
    return _junta(sr, 1.2, [(k * 0.25, pac(700 if k % 2 else 600)) for k in range(4)])


def ef_porta(sr):       # batida na porta: toc, toc, toc (grave e abafado)
    import numpy as np

    def toc():
        t = np.arange(int(0.12 * sr)) / sr
        return (0.12 * np.sin(2 * np.pi * 160 * t) * _env(len(t), sr, 0.004, 30)).astype("float32")
    return _junta(sr, 1.0, [(k * 0.28, toc()) for k in range(3)])


def ef_zumbido(sr):     # abelhas: zum-zum baixinho, entra e sai devagar
    import numpy as np
    t = np.arange(int(1.2 * sr)) / sr
    z = sum(np.sin(2 * np.pi * h * 210 * t) / h for h in (1, 2, 3))
    z *= 0.5 + 0.5 * np.sin(2 * np.pi * 9 * t)
    janela = np.sin(np.pi * t / t[-1]) ** 2
    return (0.025 * z * janela).astype("float32")


def ef_festa(sr):       # alegria, festa, final feliz: acorde curto (dó, mi, sol juntos)
    return _junta(sr, 1.4, [(0, _nota(f, 1.3, 0.04, sr, 2.5)) for f in (523.25, 659.25, 783.99)])


EFEITOS = {"transicao": ef_transicao, "magia": ef_magia, "agua": ef_agua, "galope": ef_galope,
           "porta": ef_porta, "zumbido": ef_zumbido, "festa": ef_festa}


# ── Pessoal: versão guiada (com comentários) e limpa (só o leitor) ───────────

def _nota_sinal(f, dur, vol, sr):
    import numpy as np
    t = np.arange(int(dur * sr)) / sr
    env = np.clip(t / 0.02, 0, 1) * np.exp(-4 * t)
    return (vol * (np.sin(2 * np.pi * f * t) + 0.2 * np.sin(4 * np.pi * f * t)) * env).astype("float32")


def sinal(sr, entra):
    import numpy as np
    # Duas notas curtas e baixas: sobem quando o comentário começa, descem quando acaba.
    fs = (440.0, 659.25) if entra else (659.25, 440.0)
    out = np.zeros(int(1.0 * sr), dtype="float32")
    for k, f in enumerate(fs):
        nota = _nota_sinal(f, 0.6, 0.06, sr)
        i = int(k * 0.18 * sr)
        out[i:i + len(nota)] += nota[:len(out) - i]
    return out


def montar_pessoal(n, trechos, livro_dir, ouvir=True):
    import numpy as np
    sr = None
    guiada, limpa, anterior = [], [], "leitor"
    for quem, wav, pausa, _ in trechos:
        fala, s = _ler(wav)
        sr = sr or s
        assert s == sr, f"taxa de amostragem diferente em {wav}"
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
    pasta = os.path.join(livro_dir, f"cap{n:02d}")
    exportar(np.concatenate([um_seg, *guiada, um_seg]), sr, pasta, f"cap{n:02d}_guiada", ouvir)
    exportar(np.concatenate([um_seg, *limpa, um_seg]), sr, pasta, f"cap{n:02d}_limpa", ouvir)


# ════════════════════════════════════════════════════════════════════════════
# Organizar o Drive: pasta "ouvir" com nomes legíveis, playlists e situacao.md
# ════════════════════════════════════════════════════════════════════════════

def _nome_arquivo(s):
    return re.sub(r'[\\/:*?"<>|]+', "", s).strip().rstrip(".") or "sem titulo"


def duracao(mp3):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=nw=1:nk=1", mp3], capture_output=True, text=True, timeout=60)
        return float(r.stdout.strip())
    except Exception:
        return None


def organizar(livro_dir, tipo, capitulos, titulo_livro=""):
    """Copia os MP3 prontos para <livro>/ouvir/<versão>/NN - Título.mp3 (bom para ouvir em
    sequência no celular), escreve uma playlist por versão e o resumo situacao.md."""
    linhas = [f"# {titulo_livro or os.path.basename(livro_dir)}", "",
              "| Cap. | Título | " + " | ".join(VERSOES[tipo]) + " |",
              "|---|---|" + "---|" * len(VERSOES[tipo])]
    listas = {v: [] for v in VERSOES[tipo]}
    total, prontos = {v: 0.0 for v in VERSOES[tipo]}, 0
    for n in sorted(capitulos):
        celulas = []
        for v, src in zip(VERSOES[tipo], mp3s(livro_dir, tipo, n)):
            if not os.path.exists(src):
                celulas.append("falta")
                continue
            nome = f"{n:02d} - {_nome_arquivo(capitulos[n]['titulo'])}.mp3"
            dst_dir = os.path.join(livro_dir, "ouvir", v)
            os.makedirs(dst_dir, exist_ok=True)
            dst = os.path.join(dst_dir, nome)
            if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src) \
                    or os.path.getsize(dst) != os.path.getsize(src):
                shutil.copy2(src, dst)
            listas[v].append(nome)
            d = duracao(src)
            total[v] += d or 0
            celulas.append(f"{int(d // 60)}:{int(d % 60):02d}" if d else "ok")
        prontos += all(c != "falta" for c in celulas)
        linhas.append(f"| {n} | {capitulos[n]['titulo']} | " + " | ".join(celulas) + " |")
    for v, nomes in listas.items():
        if nomes:
            with open(os.path.join(livro_dir, "ouvir", f"{v}.m3u"), "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n" + "".join(f"{v}/{x}\n" for x in nomes))
    linhas += ["", f"{prontos} de {len(capitulos)} capítulos prontos. Total: "
               + ", ".join(f"{v} {t / 3600:.1f} h" for v, t in total.items()), ""]
    with open(os.path.join(livro_dir, "situacao.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))
    print("\n".join(linhas))


# ════════════════════════════════════════════════════════════════════════════
# Baixar o texto original (Gutenberg e Wikisource)
# ════════════════════════════════════════════════════════════════════════════

def _baixar(url):
    req = urllib.request.Request(url, headers={"User-Agent": AGENTE})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def _html_para_texto(conteudo):
    conteudo = re.sub(r"(?is)<(script|style|head|sup)\b.*?</\1>", " ", conteudo)
    conteudo = re.sub(r'(?is)<(div|span|table)[^>]*class="[^"]*(noprint|ws-noexport|mw-editsection|reference)'
                      r'[^"]*"[^>]*>.*?</\1>', " ", conteudo)
    conteudo = re.sub(r"(?i)<br\s*/?>|</(p|div|h[1-6]|li|blockquote|tr)>", "\n", conteudo)
    texto = html.unescape(re.sub(r"<[^>]+>", " ", conteudo))
    texto = re.sub(r"[ \t\r\f\v]+", " ", texto)
    texto = re.sub(r" *\n *", "\n", texto)
    return re.sub(r"\n{3,}", "\n\n", texto).strip()


def _salvar(saida, partes, cabecalho):
    os.makedirs(saida, exist_ok=True)
    linhas = cabecalho + [""]
    for i, (titulo, texto) in enumerate(partes, 1):
        with open(os.path.join(saida, f"cap{i:02d}.txt"), "w", encoding="utf-8") as f:
            f.write(texto + "\n")
        linhas.append(f"cap{i:02d}.txt  {len(texto.split()):6d} palavras  {titulo}")
    linhas += ["", f"total: {len(partes)} partes, {sum(len(t.split()) for _, t in partes)} palavras"]
    with open(os.path.join(saida, "indice.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")
    print("\n".join(linhas))


def baixar_gutenberg(ebook_id, saida):
    """Texto puro do Projeto Gutenberg (sem o cabeçalho e a licença), dividido em capítulos
    quando o livro tem títulos como CHAPTER I / ADVENTURE I / Capítulo 1."""
    urls = [f"https://www.gutenberg.org/cache/epub/{ebook_id}/pg{ebook_id}.txt",
            f"https://www.gutenberg.org/files/{ebook_id}/{ebook_id}-0.txt"]
    texto, erros = None, []
    for u in urls:
        try:
            texto = _baixar(u)
            break
        except Exception as e:
            erros.append(f"{u}: {e}")
    if texto is None:   # gutenberg.org bloqueado: espelho GITenberg no GitHub
        try:
            busca = json.loads(_baixar("https://api.github.com/search/repositories?q="
                                       + urllib.parse.quote(f"org:GITenberg {ebook_id} in:name")))
            repo = next(i["name"] for i in busca["items"] if i["name"].endswith(f"_{ebook_id}"))
            for arq in (f"{ebook_id}.txt", f"{ebook_id}-8.txt", f"{ebook_id}-0.txt"):
                u = f"https://raw.githubusercontent.com/GITenberg/{repo}/master/{arq}"
                try:
                    texto = _baixar(u)
                    break
                except Exception as e:
                    erros.append(f"{u}: {e}")
        except Exception as e:
            erros.append(f"GITenberg: {e}")
    if texto is None:
        raise SystemExit("Não consegui baixar:\n" + "\n".join(erros))
    ini = re.search(r"\*\*\* ?START OF (THE|THIS) PROJECT GUTENBERG.*?\*\*\*", texto)
    fim = re.search(r"\*\*\* ?END OF (THE|THIS) PROJECT GUTENBERG", texto)
    corpo = texto[ini.end() if ini else 0: fim.start() if fim else len(texto)].replace("\r\n", "\n").strip()
    titulo = re.search(r"^Title: *(.+)$", texto, re.M)
    autor = re.search(r"^Author: *(.+)$", texto, re.M)
    marca = re.compile(r"\n\s*\n(?=(?:CHAPTER|Chapter|ADVENTURE|PART|Part|CAP[IÍ]TULO|Cap[ií]tulo|"
                       r"[IVXLC]+\.)\s*[IVXLC0-9]*[.\s])")
    pedacos = [p.strip() for p in marca.split(corpo) if p.strip()]
    partes = [(p.splitlines()[0][:70], p) for p in pedacos if len(p.split()) >= 150] or [("livro inteiro", corpo)]
    _salvar(saida, partes, [f"fonte: Projeto Gutenberg #{ebook_id}",
                            f"título: {titulo.group(1).strip() if titulo else '?'}",
                            f"autor: {autor.group(1).strip() if autor else '?'}",
                            "direitos: confira em https://www.gutenberg.org/ebooks/" + str(ebook_id)
                            + " (domínio público nos EUA; confira também no Brasil: 70 anos após a morte do autor)"])


def _ws_api(lingua, **params):
    q = urllib.parse.urlencode({"format": "json", "formatversion": 2, **params})
    return json.loads(_baixar(f"https://{lingua}.wikisource.org/w/api.php?{q}"))


def baixar_wikisource(lingua, pagina, saida):
    """Baixa uma obra do Wikisource. Se a página principal for um índice com subpáginas
    (Obra/Capítulo I...), baixa cada subpágina na ordem do índice."""
    p = _ws_api(lingua, action="parse", page=pagina, prop="text|links", redirects=1)
    if "error" in p:
        raise SystemExit(f"Wikisource: {p['error'].get('info')}")
    pagina = p["parse"]["title"]
    html_principal = p["parse"]["text"]
    # Subpáginas na ordem em que aparecem no índice.
    alvo = "/wiki/" + urllib.parse.quote(pagina.replace(" ", "_")) + "/"
    vistos, subs = set(), []
    for href in re.findall(r'href="([^"#]+)"', html_principal):
        if href.startswith(alvo) or urllib.parse.unquote(href).startswith("/wiki/" + pagina.replace(" ", "_") + "/"):
            nome = urllib.parse.unquote(href[len("/wiki/"):]).replace("_", " ")
            if nome not in vistos:
                vistos.add(nome)
                subs.append(nome)
    partes = []
    if subs:
        for s in subs:
            q = _ws_api(lingua, action="parse", page=s, prop="text", redirects=1)
            if "parse" in q:
                partes.append((s.split("/", 1)[-1], _html_para_texto(q["parse"]["text"])))
                print(f"  baixado: {s}")
    else:
        partes = [(pagina, _html_para_texto(html_principal))]
    _salvar(saida, partes, [f"fonte: https://{lingua}.wikisource.org/wiki/{urllib.parse.quote(pagina.replace(' ', '_'))}",
                            f"título: {pagina}",
                            "direitos: confira a licença na página (Wikisource só publica domínio público"
                            " ou licença livre, mas a tradução também precisa estar livre)"])


# ════════════════════════════════════════════════════════════════════════════
# Gerar o notebook genérico do Colab
# ════════════════════════════════════════════════════════════════════════════

CELULA_45 = r'''
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
'''


def gerar_notebook(saida):
    cat = catalogo()
    opcoes = json.dumps(list(cat), ensure_ascii=False)
    tabela = "\n".join(f"| `{k}` | {v['titulo']} | {v['tipo']} | `MyDrive/{RAIZ_DRIVE[v['tipo']]}/{v['pasta']}/` |"
                       for k, v in cat.items())
    cells = []

    def md(s):
        cells.append({"cell_type": "markdown", "metadata": {}, "source": s.strip("\n").splitlines(keepends=True)})

    def code(s, form=False):
        meta = {"cellView": "form"} if form else {}
        cells.append({"cell_type": "code", "metadata": meta, "execution_count": None, "outputs": [],
                      "source": s.strip("\n").splitlines(keepends=True)})

    md(f'''
# Estúdio de audiolivros

Um notebook só para todos os livros. **Escolha o livro na célula 0 e clique em `Ambiente de execução → Executar tudo`.** Ele narra só os capítulos que ainda não têm MP3 no seu Drive; os que já estão prontos são pulados.

**Antes:** `Ambiente de execução → Alterar o tipo de ambiente de execução → GPU T4`. A única coisa que você precisa fazer é autorizar o Google Drive quando aparecer a janela (célula 2).

| Livro | Obra | Tipo | Pasta no Drive |
|---|---|---|---|
{tabela}

- **pcd:** `capNN_A_so_voz.mp3` e `capNN_B_com_ambiente.mp3` (vinheta e sonoplastia leve).
- **pessoal:** `capNN_guiada.mp3` (com comentários) e `capNN_limpa.mp3` (só o texto).
- No fim, a célula 8 põe cópias com nome legível em `<livro>/ouvir/` (bom para o celular) e escreve `situacao.md` com o que está pronto.

**Outro livro na mesma sessão:** troque o livro na célula 0 e clique de novo em *Executar tudo*. A instalação, o servidor e as licenças já prontos são pulados em segundos.

**Editar um roteiro sem mexer no git:** ponha os JSON em `<livro>/roteiros/` no Drive. Se essa pasta existir, o notebook usa ela.

**Licença:** a voz (OmniVoice) é de uso **não comercial** (CC-BY-NC). As vozes são sintéticas, sem clonar ninguém. Lições aprendidas: `LICOES.md`.
''')

    code(f'''
# ── 0. Escolha o livro ──────────────────────────────────────────────────────
LIVRO = "{next(iter(cat))}"  #@param {opcoes} {{allow-input: true}}
CAPITULOS = ""  #@param {{type:"string"}}
REFAZER = False  #@param {{type:"boolean"}}
# CAPITULOS: vazio = só os que faltam; "todos"; ou uma lista como "4-10, 12".
# REFAZER: True narra de novo os escolhidos, mesmo que os MP3 já existam
# (trechos .wav que não mudaram são reaproveitados).
ESTUDIO_BRANCH = "{BRANCH_DO_ESTUDIO}"
''', form=True)

    code(r'''
# ── 1. Conferir a GPU ───────────────────────────────────────────────────────
import shutil, subprocess
if shutil.which("nvidia-smi"):
    print(subprocess.run(["nvidia-smi", "-L"], capture_output=True, text=True).stdout)
else:
    raise SystemExit("Sem GPU. Vá em Ambiente de execução -> Alterar o tipo de ambiente "
                     "de execução -> GPU T4, e rode o notebook de novo do início.")
''')

    code(r'''
# ── 2. Google Drive ─────────────────────────────────────────────────────────
# Autorize na janela que abrir (é o único passo manual).
import os
from google.colab import drive
if not os.path.isdir("/content/drive/MyDrive"):
    drive.mount("/content/drive")
print("Drive pronto.")
''')

    code(r'''
# ── 3. Instalar o VoiceStudio (primeira vez: ~5-8 min; depois, segundos) ────
import os, shutil, subprocess, sys

REPO_URL = "https://github.com/sdpaula36-stack/VoiceStudio"
REPO_DIR = "/content/VoiceStudio"
MARCA = "/content/.voicestudio_instalado"
os.environ.setdefault("UV_HTTP_TIMEOUT", "300")

def run(cmd, *, cwd=None, what=""):
    shown = cmd if isinstance(cmd, str) else " ".join(cmd)
    print(f"\n$ {shown}")
    if subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str)).returncode != 0:
        raise SystemExit(f"\nFALHOU: {what or shown}. Veja o erro acima; rodar de novo é seguro.")

if not os.path.isdir(os.path.join(REPO_DIR, ".git")):
    run(["git", "clone", "--depth", "1", "--branch", ESTUDIO_BRANCH, REPO_URL, REPO_DIR], what="git clone")
else:   # clone já existe (até de outro notebook): só traz a versão nova do estúdio
    run(["git", "-C", REPO_DIR, "fetch", "-q", "--depth", "1", "origin",
         f"+refs/heads/{ESTUDIO_BRANCH}:refs/remotes/origin/{ESTUDIO_BRANCH}"], what="git fetch")
    run(["git", "-C", REPO_DIR, "checkout", "-q", "-B", "estudio", f"origin/{ESTUDIO_BRANCH}"], what="git checkout")

if not os.path.exists(MARCA):
    run("apt-get -qq update && apt-get -qq install -y ffmpeg libsndfile1", what="apt-get install")
    if not shutil.which("uv"):
        run([sys.executable, "-m", "pip", "install", "-q", "uv"], what="pip install uv")
    run(["uv", "pip", "install", "--system", "--no-cache",
         "--constraint", "deploy/torch-constraints.txt",
         "--override", "deploy/uv-overrides.txt", "."],
        cwd=REPO_DIR, what="instalação do backend")
    from huggingface_hub import snapshot_download
    print("Baixando o modelo de voz (alguns GB, só na primeira vez)...")
    # token=False: o modelo é público; sem isso o Colab pede acesso ao Secret HF_TOKEN.
    snapshot_download("k2-fsa/OmniVoice", token=False)
    open(MARCA, "w").close()
print("Instalado.")

sys.path.insert(0, os.path.join(REPO_DIR, "notebooks", "estudio-audiolivros"))
import importlib, estudio as E
importlib.reload(E)
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

    code(CELULA_45)

    code(r'''
# ── 5. Carregar e conferir os roteiros do livro ─────────────────────────────
CFG = E.livro(LIVRO)
TIPO = CFG["tipo"]
PASTA_LIVRO = E.pasta_drive(CFG)
os.makedirs(PASTA_LIVRO, exist_ok=True)
print(f"{CFG['titulo']} ({TIPO}) -> {PASTA_LIVRO}")

ROTEIROS = E.carregar_roteiros(LIVRO, REPO_DIR, PASTA_LIVRO)
if E.relatorio(ROTEIROS, TIPO):
    raise SystemExit("O roteiro tem erros (acima). Nada foi narrado.")
VOZES, CAPITULOS_DO_LIVRO = E.juntar(ROTEIROS)
FILA = E.escolher(CAPITULOS, CAPITULOS_DO_LIVRO, PASTA_LIVRO, TIPO, REFAZER)
prontos = [n for n in CAPITULOS_DO_LIVRO if E.pronto(PASTA_LIVRO, TIPO, n)]
print(f"\nJá prontos: {len(prontos)} de {len(CAPITULOS_DO_LIVRO)}. Vou narrar agora: {FILA or 'nada'}")
''')

    code(r'''
# ── 6. Vozes (as que já existem no Drive são reaproveitadas) ────────────────
NARRADOR = E.Narrador(BASE, PASTA_LIVRO, TIPO, VOZES, CAPITULOS_DO_LIVRO, LOG_PATH)
NARRADOR.criar_vozes()
# Voz ruim ou com sotaque de Portugal: troque a "semente" no roteiro, apague o .wav
# dela em <livro>/vozes/ e rode de novo.
''')

    code(r'''
# ── 7. Narrar e montar os capítulos da fila ─────────────────────────────────
import time
for n in FILA:
    t0 = time.time()
    NARRADOR.capitulo(n)
    print(f"  ({(time.time() - t0) / 60:.1f} min de GPU)")
print("\nNarração concluída." if FILA else "Nada para narrar: todos os capítulos escolhidos já estão prontos.")
# Um trecho ruim: apague o .wav dele em <livro>/capNN/trechos/ e rode com CAPITULOS="NN" e REFAZER=True.
''')

    code(r'''
# ── 8. Organizar no Drive (pasta ouvir/, playlists e situacao.md) ───────────
E.organizar(PASTA_LIVRO, TIPO, CAPITULOS_DO_LIVRO, CFG["titulo"])
print("\nPronto! Tudo em", PASTA_LIVRO)
''')

    nb = {"cells": cells, "metadata": {"accelerator": "GPU", "colab": {"gpuType": "T4", "provenance": []},
          "kernelspec": {"display_name": "Python 3", "name": "python3"}, "language_info": {"name": "python"}},
          "nbformat": 4, "nbformat_minor": 0}
    with open(saida, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("Notebook gerado:", saida, f"({len(cells)} células)")


# ════════════════════════════════════════════════════════════════════════════
# Linha de comando
# ════════════════════════════════════════════════════════════════════════════

def main(args):
    if not args:
        raise SystemExit(__doc__)
    cmd, resto = args[0], args[1:]
    if cmd == "validar":
        tipo = None
        if "--tipo" in resto:
            i = resto.index("--tipo")
            tipo = resto[i + 1]
            resto = resto[:i] + resto[i + 2:]
        if len(resto) == 1 and not resto[0].endswith(".json"):
            cfg = livro(resto[0])
            repo = os.path.dirname(os.path.dirname(AQUI))
            caps, tipo = roteiros_do_git(repo, cfg["roteiros"]), tipo or cfg["tipo"]
        else:
            caps = []
            for p in resto:
                with open(p, encoding="utf-8") as f:
                    caps.append((p, json.load(f)))
            if not tipo:
                vozes = {v for _, c in caps for v in c.get("vozes", {})}
                tipo = "pessoal" if vozes == {"leitor", "comentarista"} else "pcd"
        print(f"Tipo: {tipo}")
        return 1 if relatorio(caps, tipo) else 0
    if cmd == "baixar" and resto and resto[0] == "gutenberg" and len(resto) == 3:
        return baixar_gutenberg(resto[1], resto[2]) or 0
    if cmd == "baixar" and resto and resto[0] == "wikisource" and len(resto) == 4:
        return baixar_wikisource(resto[1], resto[2], resto[3]) or 0
    if cmd == "notebook" and len(resto) == 1:
        return gerar_notebook(resto[0]) or 0
    raise SystemExit(__doc__)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
