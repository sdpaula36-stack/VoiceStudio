# Como fizemos o audiolivro de *Reinações de Narizinho* (piloto)

Registro completo do piloto feito em 05/11/2026, para repetir o processo com outro livro sem perder nenhum detalhe. O roteiro genérico está no [PASSO_A_PASSO.md](PASSO_A_PASSO.md). Este arquivo conta o que de fato aconteceu.

## Resumo

| Item | Valor |
|---|---|
| Livro | *Reinações de Narizinho*, Monteiro Lobato (domínio público no Brasil desde 2019) |
| Capítulos prontos | 3 (cerca de 10 min de áudio no total) |
| Público | crianças e adolescentes com deficiência visual, síndrome de Down, autismo e TDAH |
| Uso | gratuito, sem fins lucrativos (teste) |
| Modelo de voz | OmniVoice (`k2-fsa/OmniVoice`), licença CC-BY-NC: **só uso não comercial** |
| Onde rodou | Google Colab grátis, GPU Tesla T4 |
| Custo | **R$ 0,00** (Colab grátis, Drive grátis, sem API paga) |
| Tempo de GPU | cerca de 5 min no cap. 1 e cerca de 4 min nos caps. 2 e 3 juntos, mais 5 a 8 min de instalação |
| Resultado | aprovado pelo usuário ("ficou muito bom") nos três capítulos |

## Os capítulos

| Cap. | Título | Trechos | Palavras | Só voz (A) | Com ambiente (B) |
|---|---|---|---|---|---|
| 1 | Um peixinho no nariz | 45 | 553 | 3 min 54 s | 3 min 58 s |
| 2 | O palácio de conchas | 34 | 486 | 3 min 16 s | 3 min 21 s |
| 3 | Emília fala! | 29 | 369 | 2 min 30 s | 2 min 34 s |

Roteiros: `livros/narizinho/roteiros/narizinho_cap01.json` a `cap03.json`.

## As vozes

Nenhuma voz foi clonada de uma pessoa. Cada voz nasce de uma descrição e de uma semente (número) no OmniVoice. A primeira fala gerada vira a referência, e todas as outras falas do personagem são clonadas dela, para a voz ficar igual em todos os capítulos.

| Personagem | Chave | Descrição | Semente | Estreia |
|---|---|---|---|---|
| Narrador | `narrador` | male, young adult, moderate pitch | 201 | cap. 1 |
| Narizinho | `narizinho` | female, child, high pitch | 211 | cap. 1 |
| Príncipe Escamado | `principe` | male, teenager, high pitch | 221 | cap. 1 |
| Major Agarra | `major` | male, middle-aged, very low pitch | 231 | cap. 1 |
| Dona Aranha | `aranha` | female, middle-aged, high pitch | 241 | cap. 2 |
| Doutor Caramujo | `caramujo` | male, elderly, low pitch | 251 | cap. 2 |
| Emília | `emilia` | female, young adult, very high pitch | 261 | cap. 3 |
| Tia Nastácia | `nastacia` | female, middle-aged, low pitch | 271 | cap. 3 |

Para um personagem novo, use a próxima semente livre (281, 291…). Termos aceitos na descrição: `male`/`female`; `child`, `teenager`, `young adult`, `middle-aged`, `elderly`; `very low pitch` a `very high pitch`; `whisper`.

## Como foi gerado, etapa por etapa

1. **Direitos.** Lobato morreu em 1948; a obra está livre desde 1º/1/2019. Foi o motivo da escolha.
2. **Texto.** Os sites com o original (Wikisource, Domínio Público) estavam bloqueados para o assistente, então a adaptação foi escrita a partir da história conhecida. **Pendência:** comparar os três roteiros com uma edição do livro antes de levar aos jovens.
3. **Adaptação.** O Claude escreveu cada capítulo seguindo as regras do [GUIA.md](GUIA.md): 370 a 560 palavras, frases curtas, abertura fixa, recapitulação, gancho e "Até lá!". O modelo de pedido é o [PROMPT_ADAPTACAO.md](PROMPT_ADAPTACAO.md). A saída é um JSON por capítulo.
4. **Checagem.** `python -I ferramentas/validar_roteiro.py livros/narizinho/roteiros/*.json` respondeu "Tudo certo para narrar."
5. **Notebook.** `python -I ferramentas/make_audiolivro.py colab/Audiolivro_Piloto_Colab.ipynb livros/narizinho/roteiros/*.json` gera o notebook com os roteiros dentro.
6. **Colab.** Upload do `.ipynb`, *Ambiente de execução → GPU T4*, *Executar tudo*. Estes passos são do usuário:
   - "Executar mesmo assim", no aviso de notebook que não é do Google;
   - permitir o acesso ao Google Drive (célula 2);
   - aceitar as licenças de `k2-fsa/OmniVoice` e `eustlb/higgs-audio-v2-tokenizer`. No piloto isso era uma troca de `False` para `True` e foi o passo que mais travou. Agora a célula **4.5** aceita as duas sozinha; sem ela a geração dá erro (detalhes no fim do [PASSO_A_PASSO.md](PASSO_A_PASSO.md)).
7. **O que o notebook faz** (explicação completa das vozes e das versões A e B em [COMO_A_NARRACAO_E_GERADA.md](COMO_A_NARRACAO_E_GERADA.md)):
   - célula 3: clona o fork `sdpaula36-stack/VoiceStudio` e instala com `uv` (5 a 8 min);
   - célula 4: liga o servidor do VoiceStudio na porta 3900;
   - célula 6: cria uma referência por personagem (`POST /generate` com `instruct` e `seed`, idioma `pt`);
   - célula 7: narra cada trecho clonando a referência (`ref_audio` + `ref_text` + `speed`), junta com as pausas do roteiro e exporta dois MP3 com `ffmpeg` (`loudnorm` em -16 LUFS e pico de -1,5 dBTP, 44,1 kHz, LAME qualidade 2).
   - Mixagem B: vinheta de três notas suaves (dó, mi, sol) no início e no fim e ruído filtrado de "riacho" bem baixo (volume 0,01), com entrada e saída lentas. Nada alto ou repentino.
8. **Capítulos 2 e 3.** Depois do cap. 1 aprovado, os dois roteiros foram adicionados e o notebook regerado. `CAPITULOS_PARA_GERAR` (célula 2) escolhe os capítulos; capítulos com os dois MP3 prontos são pulados, a não ser que `REFAZER = True` (célula 7). As vozes do cap. 1 foram reaproveitadas da pasta `vozes/`.
9. **Escuta.** O usuário ouviu e aprovou. O assistente não consegue ouvir áudio, então essa etapa é sempre humana.

## Onde está cada coisa

| O quê | Onde |
|---|---|
| MP3 finais | Google Drive: `Meu Drive/Audiolivros/narizinho/cap01/`, `cap02/`, `cap03/` (`capNN_A_so_voz.mp3` e `capNN_B_com_ambiente.mp3`) |
| Trechos soltos (WAV) | `Meu Drive/Audiolivros/narizinho/capNN/trechos/` (um arquivo por trecho; apagar um e rodar de novo refaz só ele) |
| Vozes de referência | `Meu Drive/Audiolivros/narizinho/vozes/` (compartilhadas entre os capítulos) |
| Roteiros, ferramentas, notebook e guias | `D:\Projetos\Audiolivros` (esta pasta) e a pasta `audiolivros` do projeto no Claude |
| Cópia no GitHub | fork `sdpaula36-stack/VoiceStudio`, PR #2, pasta `notebooks/audiolivro/` |
| Plano do projeto | [Audiolivros adaptados para jovens PCD](https://claude.ai/artifact/D8o83QqqCwPiLswAYsi89k) |

## Custo em detalhe

- **Colab grátis:** R$ 0. A cota de GPU grátis varia e não é garantida; num dia ruim pode faltar T4. Se faltar, espere algumas horas ou use o Colab Pro (pago, por mês). Um capítulo de 4 min gasta só alguns minutos de GPU, então a cota grátis sobra.
- **Google Drive:** os três capítulos com trechos e vozes ocupam poucas dezenas de MB, dentro dos 15 GB grátis.
- **Claude:** a adaptação e a montagem foram feitas dentro do plano do usuário, sem API paga.
- **PC do usuário:** não serve para gerar (GT 730 de 2 GB e i3 sem AVX). Por isso tudo roda no Colab.

## Cuidados que valem para os próximos livros

- Só obras em domínio público ou com autorização por escrito. A tradução também precisa estar livre.
- Não usar arquivos de sites piratas. Em 05/11/2026 recusamos *O mistério da escola* (Martin Widmark, protegido, cópia da Z-Library); o arquivo foi apagado.
- Não clonar a voz de nenhum dublador ou artista (o estilo do Mauro Santos serve só de inspiração de ritmo e energia).
- OmniVoice só para uso não comercial. Para vender ou cobrar, trocar por um modelo de licença livre (VoxCPM2 ou CosyVoice3, Apache-2.0; suporte a português não testado).
- Teste com jovens só com consentimento escrito dos responsáveis, sem gravar os jovens e sem guardar dados que os identifiquem (ficha no [GUIA.md](GUIA.md)).

## Próximos passos do piloto

1. Conferir os três roteiros com uma edição do livro.
2. Testar com 5 a 10 ouvintes, levando as versões A e B, e anotar na ficha do GUIA.md.
3. Com o retorno, ajustar as regras e seguir para os próximos capítulos.
