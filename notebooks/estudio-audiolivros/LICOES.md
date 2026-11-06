# Lições aprendidas

O que aprendemos fazendo Narizinho, Sherlock e Memórias do Subsolo. Cada lição diz **onde ela já está automatizada**. Quando uma lição nova virar regra, coloque-a em `estudio.py` (validação ou narração) e marque aqui; assim ela não depende de alguém lembrar.

Para acrescentar uma lição: data, o que aconteceu, o que fazer, e onde ficou automatizado (ou "manual").

## Colab e instalação

| Data | Lição | Onde está |
|---|---|---|
| 2026-11-05 | Sem aceitar as licenças do `k2-fsa/OmniVoice` e do `eustlb/higgs-audio-v2-tokenizer`, o `/generate` falha. A versão antiga (trocar `False` por `True`) travou o piloto. | Célula 4.5 automática em todo notebook; `gerar()` sugere rodar a 4.5 se o erro falar de licença |
| 2026-11-06 | A célula 4.5 precisa rodar em **toda sessão nova** do Colab: o servidor começa do zero. | "Executar tudo" sempre passa por ela |
| 2026-11-06 | A janela de autorização do Google Drive abre fora do alcance do Claude; só a pessoa consegue autorizar. É o único passo manual. | Manual (célula 2) |
| 2026-11-06 | O Colab pede o Secret `HF_TOKEN`: pode cancelar, os modelos são públicos. | Manual |
| 2026-11-06 | Narrar outro livro na mesma sessão não precisa reinstalar. | Célula 3 pula a instalação se já foi feita; troque o livro e "Executar tudo" de novo |
| 2026-11-06 | T4 narra cerca de 1,5 min por capítulo de 3 a 4 min de áudio; a instalação leva de 5 a 8 min. | Célula 7 mostra o tempo de cada capítulo |

## Roteiro

| Data | Lição | Onde está |
|---|---|---|
| 2026-11-05 | A voz aceita só os termos fixos (`male`, `female`, `child` ... `whisper`); qualquer outro faz a voz sair errada. | `validar()`: erro |
| 2026-11-05 | Cada personagem tem semente própria e é definido uma vez; redefinir muda a voz no meio do livro. | `validar()`: aviso de semente repetida e de voz redefinida |
| 2026-11-06 | Trechos com mais de 300 caracteres saem pior; divida. No pessoal é erro, no PCD é aviso. | `validar()` |
| 2026-11-06 | Sonoplastia leve: só os 7 sons de `SONOPLASTIA.md`, no máximo 6 por capítulo, só nas pausas e só na versão B. | `validar()` e `montar_pcd()` |
| 2026-11-06 | Leitura guiada: todo corte é anunciado pelo leitor `(Corte: ...)` e listado em `cortes`; as vozes são só `leitor` e `comentarista`. | `validar()`: erro |
| 2026-11-06 | Os scripts que geram roteiros no rascunho do Claude não sobrevivem à sessão. **A fonte é sempre o JSON** na branch do fork. | `livros.json` aponta para a branch de cada livro |
| 2026-11-06 | Voz com sotaque de Portugal: troque a `semente`. | Manual (instrução na célula 6) |

## Cache e Drive

| Data | Lição | Onde está |
|---|---|---|
| 2026-11-06 | Os nomes dos `.wav` (vozes e trechos) são um código da voz, do texto e da velocidade. Mudar a forma de calcular faz o Colab narrar tudo de novo. | `juntar()` e `chave()` iguais aos notebooks antigos; conferido em 06/11 (2.218 arquivos de Narizinho, Sherlock e Subsolo com o mesmo nome) |
| 2026-11-06 | Primeiro teste real no Colab: Narizinho (40 caps prontos) não narrou nada, reaproveitou as vozes e organizou o Drive. | Conferido pelo usuário |
| 2026-11-06 | Um capítulo está pronto quando as duas versões em MP3 existem; o resto é pulado. | `escolher()` e `pronto()` |
| 2026-11-06 | Se a sessão cai no meio de uma gravação, ficava um arquivo pela metade que depois era reaproveitado. | `gerar()` e `exportar()` gravam em `.parcial` e só renomeiam no fim |
| 2026-11-06 | O notebook PCD antigo deixava um `.wav` grande de cada versão no Drive. | `exportar()` usa uma pasta temporária fora do Drive |
| 2026-11-06 | Ouvir no celular é mais fácil com nomes legíveis e em ordem. | `organizar()`: `ouvir/<versão>/NN - Título.mp3`, playlists `.m3u`, `situacao.md` |

## Texto original e direitos

| Data | Lição | Onde está |
|---|---|---|
| 2026-11-05 | Só domínio público ou autorização por escrito; a tradução também precisa estar livre. *O mistério da escola* foi apagado por direitos. | Manual (etapa 0 do `PASSO_A_PASSO.md`) |
| 2026-11-06 | Na nuvem do Claude, Wikisource e gutenberg.org são bloqueados. GitHub (GITenberg) funciona; o Wikisource funciona pelo Chrome do PC ou no Colab. | `baixar_gutenberg()` cai no GITenberg sozinho; `baixar_wikisource()` é para rodar no Colab ou no PC |
| 2026-11-06 | O Gutenberg divide alguns livros por algarismo romano dentro de cada aventura; a divisão automática é só um ponto de partida para planejar os capítulos. | Manual |
| 2026-11-06 | Escrever de memória gera erros; o piloto de Narizinho teve de ser conferido depois com a 1ª edição. Sempre adaptar a partir do texto baixado. | Manual |
