# Estúdio de voz do Clank

Como foram gerados os efeitos e o som de fundo de 05/11/2026, e como gerar de novo. Como o áudio entra na mesa está
em `docs/AUDIO-IA.md`.

## Resumo

| Item | Valor |
|---|---|
| Gerado em | 05/11/2026, no Google Colab grátis (GPU Tesla T4) |
| Notebook | `Estudio_Jogos_Colab.ipynb` (esta pasta), com `JOGO = "clank"`. Só efeitos: rode as células 1, 2, 8, 9 e 10 |
| Efeitos | 19 efeitos e 2 fundos (`fundo_misterio`, `fundo_tensao`), em duas versões, com o Stable Audio Open 1.0 |
| Falas | nenhuma (o Clank não tem falas) |
| Custo | R$ 0,00 (Colab grátis, Drive grátis, conta grátis do Hugging Face) |
| Licença | Stability AI Community License (o jogo não é comercial) |

## Onde está cada coisa

| O quê | Onde |
|---|---|
| Originais | Google Drive: `Meu Drive/EstudioJogos/clank/wav/` (e `mp3/`) |
| Cópia no PC | `clank_sons.zip` e `clank_musica.zip`, os pacotes baixados do Colab |
| Arquivos do jogo | `assets/audio/ia-<som>-v1.ogg` e `-v2.ogg`, mais o manifesto `assets/audio/ia.json` (commit 3abee96, publicado) |
| Notebook e ferramentas | esta pasta; original no fork `sdpaula36-stack/VoiceStudio`, branch `colab-estudio-jogos` (PR #1) |

## Como gerar de novo

1. Edite a lista `EFEITOS_POR_JOGO["clank"]` (célula 8): id, descrição em inglês e duração.
2. No [Colab](https://colab.research.google.com): *Arquivo → Fazer upload de notebook*, *Ambiente de execução → GPU T4*.
3. Aceite os termos em https://huggingface.co/stabilityai/stable-audio-open-1.0, crie um token de leitura e salve
   como segredo `HF_TOKEN` no Colab (ícone 🔑).
4. Rode as células 1, 2, 8, 9 e 10 (cada efeito leva de 10 a 30 s).
5. Converta para OGG (o servidor do Clank só serve `.ogg` em `assets/audio`):
   - efeitos: `sh docs/estudio-de-voz/converter.sh <pasta com os *_v1.mp3 e *_v2.mp3> assets/audio` (grava `ia.json`);
   - fundos em laço sem emenda: `python3 docs/estudio-de-voz/laco.py fundo_misterio_v1.wav assets/audio/ia-fundo_misterio-v1.ogg`.
6. Escolha as versões em `escuta.html` e atualize `ESCOLHIDAS` em `src/ui/amostras.js`.

Publicar: push na `main` publica o site (15 créditos do Netlify). Só com a ordem do usuário.

O Clank só usa efeitos, então pula a célula 4.5. Se um dia o Clank ganhar falas, rode as células 3, 4 e 4.5 antes das vozes.

## Aviso que sempre volta: aceitar as licenças (célula 4.5)

Sem aceitar as licenças do `k2-fsa/OmniVoice` e do `eustlb/higgs-audio-v2-tokenizer`, o `/generate` do VoiceStudio
dá erro. Todos os notebooks têm a célula **4.5**, que aceita as duas sozinha (rode depois da célula 4, com o servidor
ligado). Se você montar um notebook novo, copie esta célula:

```python
# ── 4.5. Aceitar as licenças dos modelos (obrigatório antes de gerar) ───────
import requests

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
```

`BASE` é `http://127.0.0.1:3900`. A cada sessão nova do Colab, o servidor começa do zero, então a célula tem de rodar
de novo. Lembre: OmniVoice é CC-BY-NC, uso só não comercial.

## De onde vem o VoiceStudio (Colab x PC)

O Colab **não usa nada do seu PC**. A cada sessão, na nuvem do Google:

1. a célula 3 clona o código do fork `https://github.com/sdpaula36-stack/VoiceStudio` (branch `main`) em `/content/VoiceStudio` e instala tudo com `uv`;
2. na primeira geração, o VoiceStudio baixa os modelos do Hugging Face (`k2-fsa/OmniVoice` e `eustlb/higgs-audio-v2-tokenizer`; nos efeitos dos jogos, `stabilityai/stable-audio-open-1.0`) para o disco do Colab;
3. só o resultado vai para o seu Google Drive. Quando a sessão fecha, a instalação e os modelos somem, e por isso a instalação se repete a cada vez (5 a 8 min).

No PC ficam só:

- `D:\Projetos\Ferramentas\VoiceStudio`: o código do Estúdio de voz (clone do fork). Serve para ler ou mudar o código e não é necessário para o Colab;
- os projetos (`D:\Projetos\Audiolivros` e `docs\estudio-de-voz` de cada jogo).

Em 06/11/2026 foi apagada a pasta `D:\Projetos\VoiceStudio` (28 GB), com os dados do app VoiceStudio para Windows: Python, pacotes, modelos e o banco `data\omnivoice.db`. Este PC não consegue gerar voz (GT 730 de 2 GB e i3-530 sem AVX). Na tentativa de 05/11, o capítulo passou do tempo limite na CPU e nenhum foi gerado.

**Para reinstalar o app no PC um dia** (num computador com GPU NVIDIA ou CPU moderna): baixe o instalador do Windows em https://github.com/debpalash/VoiceStudio/releases/latest e abra o app. Ele monta tudo de novo, baixando uns 28 GB. O app guarda o local dos dados em `%APPDATA%\VoiceStudio\runtime-location.json`; se ele reclamar da pasta antiga, apague esse arquivo e abra o app de novo.
