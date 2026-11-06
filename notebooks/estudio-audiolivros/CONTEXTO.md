# Contexto do projeto de audiolivros

Leia este arquivo primeiro numa conversa nova. Ele resume o que existe, como funciona e onde está cada coisa. Atualizado em 06/11/2026.

## Em uma frase

Um notebook do Google Colab narra qualquer livro do catálogo com vozes sintéticas (OmniVoice, pelo VoiceStudio). O Claude prepara os roteiros, e você escolhe o livro e clica em *Executar tudo*. **O script não muda de um livro para outro:** um livro novo é só um conjunto de roteiros JSON e uma linha no catálogo.

## O notebook único

- Link fixo: https://colab.research.google.com/github/sdpaula36-stack/VoiceStudio/blob/main/notebooks/estudio-audiolivros/Estudio_Audiolivros_Colab.ipynb
- Mora no fork `sdpaula36-stack/VoiceStudio`, branch `main`, pasta `notebooks/estudio-audiolivros/`.
- Como usar:
  1. `Ambiente de execução → Alterar o tipo → GPU T4`.
  2. Célula 0: escolha o livro. `CAPITULOS` vazio = só os que faltam; `"todos"`; ou `"4-10, 12"`. `REFAZER = True` narra de novo os escolhidos.
  3. `Ambiente de execução → Executar tudo`. Autorize o Google Drive quando a janela abrir (o único passo manual).
- Para narrar outro livro na mesma sessão: troque o livro na célula 0 e *Executar tudo* de novo. A instalação, o servidor e as licenças são pulados.
- Para testar um roteiro sem mexer no git: ponha os JSON em `<livro>/roteiros/` no Drive. Se essa pasta existir, o notebook usa ela.

### O que cada célula faz

| Célula | O que faz |
|---|---|
| 0 | Escolha do livro, dos capítulos e do REFAZER |
| 1 | Confere a GPU |
| 2 | Monta o Google Drive |
| 3 | Clona o fork e instala o VoiceStudio (5 a 8 min só na primeira vez da sessão). Baixa o modelo sem pedir a chave `HF_TOKEN` |
| 4 | Liga o servidor do VoiceStudio em `http://127.0.0.1:3900` |
| 4.5 | **Aceita as licenças** do `k2-fsa/OmniVoice` e do `eustlb/higgs-audio-v2-tokenizer`. Sem ela a geração falha. Roda em toda sessão |
| 5 | Lê os roteiros do livro, confere (erros param tudo) e mostra quais capítulos faltam |
| 6 | Cria ou reaproveita a voz de referência de cada personagem |
| 7 | Narra só os capítulos da fila e monta as duas versões em MP3 |
| 8 | Organiza o Drive: `ouvir/<versão>/NN - Título.mp3`, playlists `.m3u` e `situacao.md` |

### Arquivos da pasta

| Arquivo | Para quê |
|---|---|
| `estudio.py` | O motor. Lê e confere os roteiros, narra, mixa, organiza o Drive, baixa textos e gera o notebook. Também roda no PC: `validar`, `baixar`, `notebook` |
| `livros.json` | O catálogo: para cada livro, o tipo (`pcd` ou `pessoal`), a pasta no Drive e onde estão os roteiros no fork (branch, pasta, prefixo do nome) |
| `Estudio_Audiolivros_Colab.ipynb` | Gerado por `python -I estudio.py notebook Estudio_Audiolivros_Colab.ipynb`. Não edite à mão |
| `LICOES.md` | Lições aprendidas e onde cada uma já está automatizada |
| `LEIA-ME.md` | Resumo de uso |
| `CONTEXTO.md` | Este arquivo |

### Cuidado que não pode ser esquecido

Os nomes dos `.wav` no Drive (vozes e trechos) são um código calculado a partir da voz, do texto e da velocidade (`chave()` e `juntar()` em `estudio.py`). Eles são **iguais** aos dos notebooks antigos: foram conferidos 2.218 arquivos. Se a forma de calcular mudar, o Colab narra tudo de novo. Um trecho só é refeito quando o texto, a voz ou a velocidade dele mudam.

## Livro novo: o fluxo

1. **Você escolhe o livro.** Só domínio público ou autorização por escrito, e a tradução também precisa estar livre. Ideias em `audiolivros/SUGESTOES_DE_LIVROS.md`.
2. **O Claude baixa o texto original:** `python -I estudio.py baixar gutenberg <id> pasta` ou `baixar wikisource <língua> "<página>" pasta`. Na nuvem do Claude, o gutenberg.org e o Wikisource são bloqueados. O Gutenberg cai sozinho no espelho GITenberg do GitHub; o Wikisource vai pelo Chrome do PC ou no Colab.
3. **O Claude adapta ou roteiriza** cada capítulo num JSON, seguindo as regras do tipo (abaixo), e confere com `python -I estudio.py validar roteiros/*.json`.
4. **O Claude publica** os JSON numa branch do fork e acrescenta o livro em `livros.json`. Depois regera o notebook, para o livro aparecer na lista da célula 0, e faz o merge na `main`.
5. **Você roda o Colab** e ouve. Ajustes: trocar a `semente` de uma voz, apagar o `.wav` de um trecho ruim e rodar de novo.
6. **Lições novas** entram em `LICOES.md`. Se uma lição virar regra, ela vai para `estudio.py` (validação ou narração).

## Os dois tipos de livro

### `pcd`: audiolivros adaptados (crianças e adolescentes)

- Público: crianças e adolescentes com deficiência visual, síndrome de Down, autismo e TDAH. Projeto gratuito, não comercial.
- **Desenho universal:** um texto só para todos. Os capítulos têm de 500 a 1.000 palavras (4 a 8 min), frases curtas e um gancho no fim.
- Saída: `capNN_A_so_voz.mp3` (só a narração) e `capNN_B_com_ambiente.mp3`, com vinheta, **sonoplastia leve** e, quando a cena pede, riacho baixinho.
- Sonoplastia leve: só 7 sons (`transicao`, `magia`, `agua`, `galope`, `porta`, `zumbido`, `festa`), no máximo 6 por capítulo, só nas pausas e só na versão B. Regras em `audiolivros/SONOPLASTIA.md`.
- **Folhinha do adulto:** 3 perguntas por capítulo para depois da escuta, em `livros/<livro>/folhinhas/`.
- Regras e fontes: `audiolivros/GUIA.md`, `PROMPT_ADAPTACAO.md`, `BASE_CIENTIFICA.md`.
- Drive: `MyDrive/Audiolivros/<pasta>/`.

### `pessoal`: leitura guiada (projeto do próprio usuário)

- Duas vozes fixas: **leitor**, que lê só frases do autor, e **comentarista**, que traz contexto, ligações dentro da obra e com outras obras. O comentarista separa fato de interpretação.
- Todo corte é anunciado pelo leitor como `(Corte: ...)` e listado no campo `cortes` do JSON. O notebook confere isso.
- Saída: `capNN_guiada.mp3` (texto e comentários, com um sinal curto antes e depois de cada comentário) e `capNN_limpa.mp3` (só o texto).
- Traduções: só em domínio público ou feitas por nós.
- Drive: `MyDrive/Audiolivros-pessoais/<pasta>/`.

### Formato do roteiro (JSON, um por capítulo)

```json
{"livro": "...", "pasta": "narizinho", "capitulo": 4, "titulo": "...",
 "ambiente": "riacho",
 "vozes": {"narrador": {"voz": "male, young adult, moderate pitch", "semente": 201}},
 "trechos": [["narrador", "Texto do trecho.", 1.0, 0.6, "magia"]]}
```

- Cada trecho é `[voz, texto, velocidade 0.8 a 1.2, pausa 0 a 3 s]` e, só no PCD, um efeito opcional no fim.
- A voz aceita só estes termos: `male`, `female`, `child`, `teenager`, `young adult`, `middle-aged`, `elderly`, `very low pitch` … `very high pitch`, `whisper`.
- Cada personagem é definido uma vez, com uma semente própria. A voz dele nasce da fala mais longa no primeiro capítulo em que aparece.
- Trechos de no máximo 300 caracteres.
- No pessoal, há também os campos `autor`, `fonte`, `original` e `cortes`.

## Livros prontos (06/11/2026)

| Livro | Tipo | Capítulos | Situação | Roteiros no fork |
|---|---|---|---|---|
| *Reinações de Narizinho* (Lobato) | pcd | 1 a 40 (livro inteiro) | Narrado. Caps 1 a 3 ouvidos e aprovados; **4 a 40 falta ouvir** e testar com ouvintes | `claude/project-thread-wm77ja`, `notebooks/audiolivro/narizinho_capNN.json` |
| Sherlock Holmes (Conan Doyle): *A Liga dos Cabeças Vermelhas* (1 a 3) e *O Carbúnculo Azul* (4 a 6) | pcd | 1 a 6 | Narrado; **falta ouvir** | mesma branch, `sherlock_capNN.json` |
| *Memórias do Subsolo* (Dostoiévski), tradução nossa do russo | pessoal | 1 a 21 (Parte I: 1 a 11; Parte II: 12 a 21) | Narrado: guiada 3,6 h, limpa 3,2 h. Caps 1 e 2 aprovados; **3 a 21 falta ouvir** | `claude/project-thread-xlgms3`, `notebooks/audiolivros-pessoais/livros/subsolo/roteiros/` |

Tempos do Subsolo (guiada / limpa): 1 8:51/7:02 · 2 8:17/6:15 · 3 10:11/8:30 · 4 4:17/3:30 · 5 6:06/5:24 · 6 3:28/2:35 · 7 11:34/10:13 · 8 9:07/8:18 · 9 7:26/6:31 · 10 4:47/3:43 · 11 7:48/6:40 · 12 15:16/13:51 · 13 7:31/6:30 · 14 12:02/11:02 · 15 15:19/14:22 · 16 10:34/9:37 · 17 14:32/13:41 · 18 14:16/13:08 · 19 14:23/13:26 · 20 15:07/14:18 · 21 12:09/10:54.

Para ver a situação de qualquer livro, abra `situacao.md` na pasta dele no Drive. O notebook atualiza o arquivo a cada execução.

Vozes já usadas (sementes), para não repetir:
- Narizinho: 201 a 591 (lista em `audiolivros/COMO_FIZEMOS_NARIZINHO.md`).
- Sherlock: narrador 201 (o mesmo de Narizinho), 301 a 411.
- Subsolo: leitor 601, comentarista 611.
- Próxima semente livre: 621.

## Regras fixas

- **Direitos:** só domínio público (no Brasil, 70 anos após a morte do autor) ou autorização por escrito. *O mistério da escola* foi apagado por direitos. Não use sites piratas.
- **Licença do modelo:** OmniVoice é CC-BY-NC, uso só **não comercial**. Para vender, troque o modelo (VoxCPM2 ou CosyVoice3, Apache-2.0; o português não foi testado).
- **Nunca clonar voz** de dublador ou artista. Uma `amostra` real só com autorização por escrito.
- **Célula 4.5** em todo notebook novo (licenças). Este é o erro que mais se repete.
- **Chave HF:** o notebook baixa o modelo com `token=False`. Se o Colab ainda pedir o Secret `HF_TOKEN`, pode cancelar.
- **A fonte é o JSON** na branch do fork. Os scripts temporários do Claude não sobrevivem à conversa.
- **Escrever a partir do texto original**, nunca de memória.

## Onde fica cada coisa

| Lugar | O que tem |
|---|---|
| Fork `sdpaula36-stack/VoiceStudio`, `main`, `notebooks/estudio-audiolivros/` | Notebook único, motor, catálogo, LICOES, este arquivo |
| Fork, branch `claude/project-thread-wm77ja`, `notebooks/audiolivro/` | Roteiros de Narizinho e Sherlock, e os notebooks antigos (só histórico) |
| Fork, branch `claude/project-thread-xlgms3`, `notebooks/audiolivros-pessoais/` | Roteiros do Subsolo, texto original russo, notebook antigo (só histórico) |
| Google Drive `MyDrive/Audiolivros/<livro>/` | Áudios PCD: `capNN/`, `vozes/`, `ouvir/`, `situacao.md` |
| Google Drive `MyDrive/Audiolivros-pessoais/<livro>/` | Áudios da leitura guiada, na mesma organização |
| PC `D:\Projetos\Audio\Audiolivros` | Cópia do projeto PCD: guias, roteiros, folhinhas, ferramentas |
| PC `D:\Projetos\Audio\Audiolivros-pessoais` | Cópia do projeto pessoal (pendente: mover os arquivos que estão no OneDrive) |
| Pasta do projeto do Claude `/mnt/project-files/` | `audiolivros/`, `audiolivros-pessoais/` e `estudio-audiolivros/` (cópia desta pasta) |

Documentos de apoio:
- `audiolivros/LEIA-ME.md`, `PASSO_A_PASSO.md`, `GUIA.md`, `PROMPT_ADAPTACAO.md`, `BASE_CIENTIFICA.md`, `SONOPLASTIA.md`, `COMO_A_NARRACAO_E_GERADA.md`, `COMO_FIZEMOS_NARIZINHO.md`, `SUGESTOES_DE_LIVROS.md`
- `audiolivros-pessoais/LEIA-ME.md`; proposta da leitura guiada: https://claude.ai/artifact/XH9TDPjEGpiCR8HCyPtVgX
- Plano dos audiolivros PCD: https://claude.ai/artifact/D8o83QqqCwPiLswAYsi89k
- Lições: `LICOES.md` (nesta pasta)

## Custos e tempos

- Colab grátis (T4) serve. O usuário tem Colab Pro.
- Instalação: de 5 a 8 min por sessão nova.
- Narração: cerca de 1 min de GPU por minuto de áudio. A Parte II do Subsolo (131 min de áudio guiado) levou no máximo 2h10, numa sessão só.
- Custo: zero.

## Pendências

- Ouvir Narizinho 4 a 40, Sherlock 1 a 6 e Subsolo 3 a 21.
- Testar Narizinho com os ouvintes, usando a ficha do `GUIA.md`, com consentimento por escrito.
- Testar `baixar wikisource` (ainda não foi rodado).
- Mover os arquivos de `audiolivros-pessoais` do OneDrive para `D:\Projetos\Audio\Audiolivros-pessoais`.
- Próximos livros sugeridos (PCD): *O Saci* (Lobato), *Just So Stories* (Kipling), *O patinho feio* (Andersen).
