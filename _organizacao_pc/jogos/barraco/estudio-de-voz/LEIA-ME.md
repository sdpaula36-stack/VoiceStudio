# Estúdio de voz do Barraco do Bairro

Como foram geradas as falas e os efeitos de 05/11/2026, e como gerar de novo. A integração no jogo está no
`docs/jogo-combate-77-etapa30-vozes.md` (branch `etapa-30-vozes`).

## Resumo

| Item | Valor |
|---|---|
| Gerado em | 05/11/2026, no Google Colab grátis (GPU Tesla T4) |
| Notebook | `Estudio_Jogos_Colab.ipynb` (esta pasta), com `JOGO = "barraco"` na célula 2 |
| Vozes | 88 falas (lutadores, locutor em português, Dark Cida) com o OmniVoice do VoiceStudio |
| Efeitos | 25 efeitos em duas versões (`_v1` e `_v2`) com o Stable Audio Open 1.0; o jogo usa a `_v1` |
| Total | 138 MP3 (mais os WAV originais) |
| Custo | R$ 0,00 (Colab grátis, Drive grátis, conta grátis do Hugging Face) |
| Licenças | OmniVoice CC-BY-NC (só uso não comercial); Stable Audio Open: Stability AI Community License. O jogo não é comercial. |

## Onde está cada coisa

| O quê | Onde |
|---|---|
| Originais (WAV e MP3) | Google Drive: `Meu Drive/EstudioJogos/barraco/wav/` e `.../mp3/` |
| Cópia no PC | `mp3/estudio-2026-11-05/` (fora do git) e `barraco.zip`, o pacote baixado do Colab |
| Arquivos do jogo | `src/assets/audio/`, gerados por `python -I tools/preparar-sons.py mp3`; procedência em `src/assets/audio/CREDITOS.md` |
| Notebook e gerador | esta pasta; original no fork `sdpaula36-stack/VoiceStudio`, branch `colab-estudio-jogos` (PR #1) |

## Como gerar de novo

1. Edite as falas (célula 5, `ROTEIROS["barraco"]`) ou os efeitos (célula 8, `EFEITOS_POR_JOGO["barraco"]`) direto no
   notebook. Para mudar o gerador, edite `make_estudio_jogos.py` e rode
   `python -I docs/estudio-de-voz/make_estudio_jogos.py docs/estudio-de-voz/Estudio_Jogos_Colab.ipynb "../Top Gear/src/story/dialogos.json"`
   (o gerador monta os três jogos de uma vez e precisa das falas do Pé na Tábua). Depois troque `JOGO` para `"barraco"`.
2. No [Colab](https://colab.research.google.com): *Arquivo → Fazer upload de notebook*, *Ambiente de execução → GPU T4*.
3. Para os efeitos: aceite os termos em https://huggingface.co/stabilityai/stable-audio-open-1.0, crie um token de
   leitura e salve como segredo `HF_TOKEN` no Colab (ícone 🔑).
4. *Executar tudo*. Cliques que só você pode dar: "Executar mesmo assim" e o acesso ao Drive. A célula **4.5**
   aceita as licenças das vozes sozinha; sem ela as vozes dão erro (veja abaixo).
5. Tempo: instalação de 5 a 8 min; cada fala leva de 5 a 20 s e cada efeito de 10 a 30 s. Arquivos que já existem no
   Drive são pulados (`SO_NOVAS = True`).
6. Copie a pasta `mp3/` do Drive para `mp3/estudio-AAAA-MM-DD/` e rode `python -I tools/preparar-sons.py mp3`.

Problemas já resolvidos no notebook: o ambiente dos efeitos usa `diffusers==0.35.2` e `transformers<5` e aproveita o
`torch` do Colab; o Colab esconde a saída dos subprocessos, por isso o notebook a mostra linha a linha.

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
