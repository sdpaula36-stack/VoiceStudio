# Como a narração é gerada: versão A (sem efeitos) e versão B (com efeitos)

Este arquivo explica, passo a passo, como o notebook `colab/Audiolivro_Piloto_Colab.ipynb` transforma o roteiro em
áudio. Foi assim que os capítulos 1 a 3 de *Reinações de Narizinho* foram feitos em 05/11/2026. O resumo do piloto
está em [COMO_FIZEMOS_NARIZINHO.md](COMO_FIZEMOS_NARIZINHO.md), e o caminho do livro ao roteiro está no
[PASSO_A_PASSO.md](PASSO_A_PASSO.md).

## Visão geral

```
roteiro JSON ──► 1 voz de referência por personagem ──► 1 WAV por trecho ──► trechos + pausas = narração
                     (célula 6, pasta vozes/)            (célula 7, trechos/)        │
                                                                                     ├─► A: só voz       → capNN_A_so_voz.mp3
                                                                                     └─► B: voz + efeitos → capNN_B_com_ambiente.mp3
```

As duas versões usam **exatamente a mesma narração**. A diferença está só na mixagem final: a B acrescenta uma vinheta
e um som de riacho bem baixo. A voz em si não recebe efeito nenhum (sem eco, reverb ou distorção) nas duas versões.

## Etapa 1: preparar o servidor de voz (células 1 a 4.5)

| Célula | O que faz |
|---|---|
| 1 | Confere se a GPU T4 está ligada |
| 2 | Monta o Google Drive e define a pasta do livro: `Meu Drive/Audiolivros/<pasta>/` (`<pasta>` vem do campo `"pasta"` do JSON, ex.: `narizinho`) e a lista `CAPITULOS_PARA_GERAR` |
| 3 | Clona o fork `sdpaula36-stack/VoiceStudio` e instala com `uv` (5 a 8 min) |
| 4 | Liga o servidor do VoiceStudio em `http://127.0.0.1:3900` |
| 4.5 | Aceita as licenças do `k2-fsa/OmniVoice` e do `eustlb/higgs-audio-v2-tokenizer`. **Sem isso a geração dá erro.** Roda em toda sessão nova |

O motor de voz é o **OmniVoice** (padrão do VoiceStudio), licença CC-BY-NC: uso só não comercial.

## Etapa 2: criar a voz de cada personagem (célula 6)

Para cada personagem listado em `VOZES` (célula 5):

1. O notebook pega a **fala mais longa** desse personagem no primeiro capítulo em que ele aparece.
2. Gera essa fala com o OmniVoice a partir de uma **descrição** e de uma **semente**, sem clonar ninguém:
   `POST /generate` com `text` (a fala), `language = "pt"`, `instruct` (a descrição, ex.: `female, child, high pitch`),
   `seed` (ex.: `211`) e `effect_preset = "raw"` (sem efeito de áudio).
3. Salva o resultado em `Meu Drive/Audiolivros/<pasta>/vozes/<personagem>_<código>.wav`. Esse arquivo é a
   **voz de referência** do personagem e vale para todos os capítulos.
4. Mostra um player para ouvir. Se a voz não agradar, troque a `semente` na célula 5, apague o arquivo dele em `vozes/`
   e rode de novo.

O `<código>` é um resumo da descrição e do texto. Se você mudar a descrição, a semente ou a fala, o nome muda e a voz é
gerada de novo. Se nada mudou, o arquivo existente é reaproveitado.

Opcional: `"amostra"` em uma voz aponta para um WAV de 5 a 10 s de alguém que **autorizou por escrito** o uso da voz.
No piloto não foi usado.

## Etapa 3: narrar cada trecho (célula 7, função `narrar`)

O roteiro é uma lista de trechos `[personagem, texto, velocidade, pausa]`. Para cada trecho, em ordem:

1. Chama `POST /generate` **clonando a voz de referência** do personagem: `ref_audio` (o WAV de `vozes/`),
   `ref_text` (o texto dessa referência), `text` (o trecho), `speed` (a velocidade do roteiro), `seed`, `language = "pt"`
   e `effect_preset = "raw"`.
2. Salva em `Meu Drive/Audiolivros/<pasta>/capNN/trechos/NNN_<personagem>_<código>.wav`
   (ex.: `012_narizinho_3fa9c1d2.wav`).
3. Se o arquivo já existe, pula. Por isso dá para refazer **um trecho só**: apague o WAV dele e rode a célula 7 de novo.

Velocidades usadas: 1,0 normal; até 1,1 na ação; 0,85 a 0,9 no suspense e no sono. Pausas: 0,4 a 1,8 s, maiores antes
das revelações.

## Etapa 4: montar a narração (célula 7, função `montar`)

1. Lê todos os WAV do capítulo, na ordem do roteiro, e converte para mono.
2. Depois de cada trecho, coloca um silêncio do tamanho da `pausa` do roteiro.
3. O resultado é uma faixa só, a **narração**. Ela é a base das duas versões.

## Versão A: narração sem efeitos (`capNN_A_so_voz.mp3`)

Para quem tem sensibilidade a sons.

- Montagem: **1 s de silêncio + narração + 1 s de silêncio**. Nada mais.
- Exportação (função `exportar`): `ffmpeg` com `loudnorm=I=-16:TP=-1.5:LRA=11` (volume padronizado em -16 LUFS, pico
  máximo de -1,5 dBTP), 44,1 kHz, MP3 LAME qualidade 2 (`-q:a 2`).
- Arquivo: `Meu Drive/Audiolivros/<pasta>/capNN/capNN_A_so_voz.mp3`.

## Versão B: narração com efeitos (`capNN_B_com_ambiente.mp3`)

Voz com vinheta e ambiente de riacho, sem sons altos ou repentinos. Os dois efeitos são **sintetizados no próprio
notebook** (não vêm de arquivo nem de outro modelo de IA).

- Montagem: **vinheta + 1 s de silêncio + (narração + riacho) + 1 s de silêncio + vinheta**.
- **Vinheta** (função `vinheta`, 2,2 s): três notas suaves, dó (523 Hz), mi (659 Hz) e sol (784 Hz), entrando a cada
  0,35 s. Cada nota dura 1,4 s, tem volume 0,12 e vai sumindo devagar, sem ataque forte.
- **Riacho** (função `riacho`): ruído aleatório suavizado (média de 40 amostras), que soa como água correndo. Volume
  0,01 (bem baixo, embaixo da voz), com uma ondulação lenta de 0,15 Hz e entrada e saída de até 4 s. É somado à
  narração durante todo o capítulo e usa uma semente fixa (7), então soa igual toda vez.
- Exportação: a mesma da versão A (-16 LUFS, pico -1,5 dBTP, 44,1 kHz, MP3 qualidade 2).
- Arquivo: `Meu Drive/Audiolivros/<pasta>/capNN/capNN_B_com_ambiente.mp3`.
- A B fica cerca de 4 s mais longa que a A por causa das duas vinhetas (ex.: cap. 1 com 3 min 54 s na A e 3 min 58 s na B).

## O que fica no Drive

```
Meu Drive/Audiolivros/narizinho/
├── vozes/                       voz de referência de cada personagem (vale para todos os capítulos)
├── cap01/
│   ├── cap01_A_so_voz.mp3       versão A, sem efeitos
│   ├── cap01_B_com_ambiente.mp3 versão B, com vinheta e riacho
│   └── trechos/                 um WAV por trecho do roteiro (001_narrador_....wav, 002_...)
├── cap02/  (igual)
└── cap03/  (igual)
```

A célula 7 também grava, ao lado de cada MP3, o WAV usado para exportá-lo (`capNN_A_so_voz.wav` e
`capNN_B_com_ambiente.wav`), sem normalização. Ele pode ser apagado se faltar espaço.

## Como mudar os efeitos

Os números ficam na célula 7 do notebook e na função correspondente em `ferramentas/make_audiolivro.py`. Mude nos
dois, ou só no gerador e depois regere o notebook.

| Quero… | Onde mexer |
|---|---|
| Riacho mais alto ou mais baixo | `0.01` em `riacho` (dobrar = mais ou menos +6 dB) |
| Outras notas na vinheta | a lista `[523.25, 659.25, 783.99]` em `vinheta` |
| Tirar a vinheta só da B | trocar `vinheta(sr)` por `um_seg` em `montar` |
| Volume final diferente | `I=-16` no `loudnorm` de `exportar` |
| Um efeito na voz | não use: as duas versões deixam a voz limpa de propósito (`effect_preset = "raw"`) |

Depois de mudar um efeito, só a mixagem muda: rode a célula 7 com `REFAZER = True`. Os trechos já narrados são
reaproveitados, então leva poucos segundos por capítulo.

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
