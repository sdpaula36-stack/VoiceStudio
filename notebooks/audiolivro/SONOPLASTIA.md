# Sonoplastia leve: o que cabe sem carregar

Avaliação feita em 06/11/2026, depois que os caps. 1 a 3 de *Narizinho* saíram só com vinheta e riacho. Pergunta: que efeitos sonoros dá para pôr sem cansar nem incomodar quem ouve? A resposta segue a [BASE_CIENTIFICA.md](BASE_CIENTIFICA.md).

## O que a pesquisa permite (e o que proíbe)

| Achado | Consequência para os efeitos |
|---|---|
| No autismo, a hipersensibilidade a sons é o traço sensorial mais consistente; cerca de 60% têm hoje [11][12] | A versão **A (só voz) continua a padrão** e nunca recebe efeito. Efeitos só na **B**, que é opcional |
| Detalhes interessantes mas fora do assunto atrapalham o aprendizado (metanálise de 58 estudos) [13] | Efeito só onde **ajuda a seguir a história**: troca de cena, mágica, um som que a história nomeia. Nada de enfeite |
| Na síndrome de Down, a memória do que se ouve é curta [3] | **Nunca por cima da fala.** O som entra na pausa, depois da frase, para não disputar atenção com a palavra |
| Guia de audiodescrição: não falar por cima de um som importante [6] | Mesmo princípio ao contrário: a pausa cresce para o som caber inteiro |
| Previsibilidade ajuda no autismo (regra 3 do GUIA) | **Mesmo som = mesmo sentido**, em todos os capítulos. Um catálogo pequeno e fixo, como uma "trilha de avisos" |

Nada disso foi testado com audiolivros e esses públicos (ver o limite da pesquisa na BASE_CIENTIFICA). Por isso a ficha de observação já pergunta sobre incômodo com os sons da B.

## As regras

1. **Só na versão B.** A versão A fica igual: só voz.
2. **Só nas pausas**, nunca junto da fala. O notebook alonga a pausa quando o som não cabe nela.
3. **Baixo e macio:** 15 dB abaixo da voz (RMS) e pico de no máximo um terço do pico da voz; ataque suave (nada de estalo), duração de 0,9 a 1,5 s.
4. **No máximo 6 por capítulo** (cerca de 1 por minuto). O `validar_roteiro.py` avisa quando passa.
5. **Catálogo fixo de 7 sons**, sempre com o mesmo sentido (tabela abaixo). Não inventar som novo para um capítulo só.
6. **Sem sons de susto:** nada de trovão, grito, explosão, latido, buzina, porta batendo forte. Momentos de medo ficam só na voz.
7. **Onomatopeias continuam na voz** ("tchibum", "tloc, pluf, nhoc", "coin, coin"). O som da B, quando houver, vem depois e baixinho, reforçando.
8. **Ambiente de fundo só quando a cena pede:** o riacho fica nos capítulos passados na beira da água (`"ambiente": "riacho"`); nos outros, `"nenhum"`. Sem música por baixo da fala.
9. **Sons sintetizados no próprio notebook**, sem baixar arquivo nem usar outro modelo: soam iguais toda vez e não dependem de licença.

## O catálogo

| Nome no roteiro | Som | Quando usar |
|---|---|---|
| `transicao` | duas notas suaves que descem (sol, dó) | troca de cena ou de tempo ("No dia seguinte...") |
| `magia` | quatro notinhas agudas subindo, bem baixas | encanto, sonho começando ou acabando, algo impossível acontecendo |
| `agua` | "chuá" abafado e duas bolhas | mergulho, queda na água |
| `galope` | quatro batidinhas de madeira (pac, pac) | cavalinho chegando ou partindo |
| `porta` | três batidas graves e abafadas (toc, toc, toc) | alguém bate na porta |
| `zumbido` | zum-zum baixinho que entra e sai devagar | abelhas, colmeia |
| `festa` | acorde curto e alegre (dó, mi, sol juntos) | final feliz, festa, um "sim" importante |

A vinheta de abertura e fechamento continua como era (três notas, dó, mi, sol).

Para ouvir os sete sons em sequência: [amostra_sonoplastia.mp3](amostra_sonoplastia.mp3) (volume reduzido, como ficam por baixo da narração).

## Como marcar no roteiro

O efeito é um quinto item, opcional, no trecho depois do qual ele toca:

```json
["narrador", "Narizinho foi ajudar Tia Nastácia com a roupa. Mas, de repente... tchibum!", 1.05, 1.0, "agua"],
```

E cada capítulo diz o ambiente:

```json
"ambiente": "nenhum",
```

Capítulos sem o campo (os caps. 1 a 3) continuam com o riacho, como foram aprovados.

## O que ficou de fora, e por quê

- **Música de fundo:** disputa atenção com a fala [13] e pesa para quem tem hipersensibilidade [12].
- **Efeitos gerados por IA (Stable Audio Open):** usados nos jogos, mas aqui cada geração sai diferente, quebrando a regra do "mesmo som = mesmo sentido", e o modelo tem licença restrita.
- **Sons de bicho (porco, galinha, abelha zangada):** a voz já faz ("coin, coin"), e sons realistas de bicho podem assustar.
- **Efeito na voz (eco, reverb, voz de robô):** a voz fica limpa nas duas versões; muda-se o personagem pela escolha da voz, não por filtro.

## Onde isso mora no código

- `ferramentas/make_audiolivro.py`: funções `ef_*`, dicionário `EFEITOS` e a mixagem em `montar` (célula 7 do notebook).
- `ferramentas/validar_roteiro.py`: confere o nome do efeito, o `"ambiente"` e o limite de 6 por capítulo.

As referências numeradas ([3], [6], [11], [12], [13]) são as da [BASE_CIENTIFICA.md](BASE_CIENTIFICA.md).
