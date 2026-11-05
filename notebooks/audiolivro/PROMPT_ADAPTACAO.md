# Modelo de pedido para adaptar um capítulo

Copie o bloco abaixo numa conversa com o Claude (ou outro assistente). Troque o que está entre `<< >>` e cole o texto do capítulo, tirado do arquivo `capNN.txt` que o `extrair_livro.py` gerou.

Use só com obras em domínio público ou com autorização por escrito do titular dos direitos.

---

```text
Você vai adaptar um capítulo de livro para um audiolivro destinado a crianças e
adolescentes com deficiência visual, síndrome de Down, autismo e TDAH.

Livro: <<título>>, de <<autor>> (<<domínio público desde ANO / licença de QUEM>>).
Capítulo de saída: <<N>>. Título curto e atraente para ele: você escolhe.

Regras de adaptação:
1. Entre 500 e 1.000 palavras (de 4 a 8 minutos de áudio).
2. Frases curtas, com uma ideia por frase e vocabulário concreto. Nada de orações encaixadas.
3. Estrutura fixa:
   - abertura "<<título do livro>>. Capítulo <<N por extenso>>: <<título>>.";
   - a partir do capítulo 2, uma recapitulação de 2 ou 3 frases ("No capítulo passado...");
   - ação logo no começo;
   - final com gancho e "Até lá!".
4. Repita o nome dos personagens quando puder haver dúvida de quem está falando.
5. Descreva o que seria ilustração (cores, tamanho, roupa).
6. Dê nome às emoções quando não forem óbvias.
7. Explique ou troque linguagem figurada e ironia por linguagem literal.
8. Tire passagens racistas ou preconceituosas. Trate todos os personagens com respeito.
9. Mantenha os personagens, os lugares e os acontecimentos principais do original.
   Não invente fatos importantes.
10. Narração animada: perguntas para quem ouve ("Sabe por quê?"), onomatopeias,
    pausas antes de revelações.

Formato da resposta: SÓ um JSON válido, assim:
{
  "livro": "<<título>>",
  "capitulo": <<N>>,
  "titulo": "...",
  "nota": "Adaptação de <<título>>, capítulo original <<X>>.",
  "vozes": { "<<personagem novo>>": {"voz": "...", "semente": <<número>>} },
  "trechos": [
    ["narrador", "texto do trecho", 1.0, 0.5],
    ...
  ]
}

- "vozes": coloque SÓ personagens que ainda não têm voz. Já existem: <<lista, ex.: narrador,
  narizinho, principe>>. Para cada voz nova, use só estes termos, separados por vírgula:
  male/female; child, teenager, young adult, middle-aged, elderly; very low pitch, low pitch,
  moderate pitch, high pitch, very high pitch; whisper. Semente: um número que ainda não foi
  usado (<<sementes já usadas>>).
- Cada trecho: [personagem, texto, velocidade, pausa em segundos depois].
  Velocidade de 0.85 (suspense, sono) a 1.1 (ação). Pausa de 0.4 a 1.8.
- No máximo 2 frases por trecho. Falas de personagens em trechos separados, sem aspas.

Texto original do capítulo:
<<cole aqui o conteúdo de capNN.txt>>
```

---

**Depois de receber o JSON:** salve-o como `<<livro>>_capNN.json` e leia o texto inteiro, comparando com o original. Corrija o que estiver errado e rode o `validar_roteiro.py`, como explica o [PASSO_A_PASSO.md](PASSO_A_PASSO.md).
