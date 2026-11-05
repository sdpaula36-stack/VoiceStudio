# Passo a passo: do livro ao audiolivro adaptado

Este é o caminho que usamos no piloto de *Reinações de Narizinho* (capítulos 1 a 3). Os arquivos citados estão em `notebooks/audiolivro/`.

| Etapa | O que fazer | Ferramenta | Resultado |
|---|---|---|---|
| 0 | Conferir os direitos | Você | Sim ou não para seguir |
| 1 | Extrair o texto | `extrair_livro.py` | `cap01.txt`, `cap02.txt`… e `indice.txt` |
| 2 | Planejar os capítulos | Você | Lista de capítulos do audiolivro |
| 3 | Adaptar cada capítulo | `PROMPT_ADAPTACAO.md` + Claude | `livro_capNN.json` |
| 4 | Revisar | Você (e, se possível, um educador) | JSON corrigido |
| 5 | Validar | `validar_roteiro.py` | "Tudo certo para narrar." |
| 6 | Narrar | Notebook no Colab | MP3 A (só voz) e B (com ambiente) no Drive |
| 7 | Ouvir e ajustar | Você | Sementes ou trechos refeitos |
| 8 | Testar com ouvintes | Ficha do `GUIA.md` | Observações para o próximo ciclo |

## 0. Conferir os direitos (obrigatório)

Só siga se a obra estiver **em domínio público** ou se você tiver **autorização por escrito** do titular dos direitos.

- No Brasil, a obra entra em domínio público 70 anos após a morte do autor, contados a partir de 1º de janeiro do ano seguinte. Exemplo: Monteiro Lobato morreu em 1948, então a obra dele está livre desde 2019.
- Uma tradução tem direitos próprios. Um conto dos Grimm é livre, mas a tradução moderna pode não ser.
- Use um arquivo de fonte legítima: Domínio Público (gov.br), Wikisource, Projeto Gutenberg ou uma edição que você comprou. Não use arquivos de sites piratas (Z-Library, Library Genesis e semelhantes).
- A exceção para pessoas com deficiência visual (Lei 9.610, art. 46, e o Tratado de Marrakesh) cobre **cópias acessíveis** da obra, não **adaptações**. Para adaptar uma obra protegida, peça licença à editora.

## 1. Extrair o texto

```bash
python -I notebooks/audiolivro/extrair_livro.py meu_livro.epub textos/meu_livro
# PDF: primeiro "pip install pypdf"; PDF escaneado (imagem) precisa de OCR antes
```

Abra o `indice.txt`. Confira a linha **direitos** e o número de palavras de cada capítulo.

## 2. Planejar os capítulos

Meta: 500 a 1.000 palavras por capítulo do audiolivro, de 4 a 8 minutos.

- Um capítulo original longo pode virar dois, cada um com o próprio gancho.
- Capítulos originais curtos podem ser juntados num só.
- Escolha nomes simples para os personagens (`narrador`, `emilia`, `principe`). Esses nomes ficam iguais em todos os capítulos.

## 3. Adaptar cada capítulo

Use o [PROMPT_ADAPTACAO.md](PROMPT_ADAPTACAO.md): cole o texto do `capNN.txt` e preencha a lista das vozes que já existem. Salve a resposta como `meu_livro_capNN.json`. Os arquivos `narizinho_cap01.json` a `narizinho_cap03.json` servem de exemplo.

Regras de voz:
- Defina cada personagem uma única vez, no primeiro capítulo em que ele aparece. Daí em diante, a voz dele é a mesma em todos os capítulos.
- Cada personagem tem uma `semente` diferente.

## 4. Revisar (não pule)

Leia o JSON inteiro e compare com o original:
- Algum fato foi inventado ou mudado?
- Falta algo essencial para entender a história?
- Ficou algum trecho preconceituoso, assustador demais ou confuso?
- O gancho final dá vontade de ouvir o próximo?

Se puder, peça para um professor de AEE, um fonoaudiólogo ou um terapeuta ler um capítulo.

## 5. Validar

```bash
python -I notebooks/audiolivro/validar_roteiro.py meu_livro_cap01.json meu_livro_cap02.json ...
```

Passe **todos** os capítulos do livro juntos. Corrija cada `ERRO`. Os `AVISO`s são sugestões.

## 6. Narrar no Colab

1. Gere o notebook com os seus capítulos:
   ```bash
   python -I notebooks/audiolivro/make_audiolivro.py notebooks/audiolivro/Audiolivro_Piloto_Colab.ipynb meu_livro_cap*.json
   ```
   A pasta no Drive vem do campo `"pasta"` do JSON (ex.: `"narizinho"`). Sem esse campo, o notebook usa o título do livro sem acentos.
2. Abra o notebook no Colab: *Arquivo → Fazer upload de notebook*, ou pelo GitHub.
3. Escolha *Ambiente de execução → Alterar o tipo → GPU T4* e clique em *Executar tudo*. Se aparecer o aviso "não é de autoria do Google", clique em *Executar assim mesmo*.
4. Na primeira vez, a célula 4b para e mostra a licença do modelo de voz (OmniVoice, uso **não comercial**). Se concordar, troque `False` por `True` e rode de novo a partir dela.
5. Tempo: a instalação leva cerca de 3 minutos. Cada capítulo de 4 minutos leva cerca de 2 minutos de GPU.

Os arquivos vão para o Drive, em `MyDrive/Audiolivros/<livro>/capNN/`:
- `capNN_A_so_voz.mp3`: só a narração;
- `capNN_B_com_ambiente.mp3`: narração com vinheta e riacho baixinho;
- `trechos/`: um arquivo por trecho;
- `<livro>/vozes/`: a amostra de cada personagem.

## 7. Ouvir e ajustar

- **Voz ruim ou com sotaque de Portugal:** troque a `semente` do personagem no JSON. Depois apague os arquivos dele em `vozes/` e em `capNN/trechos/` e narre de novo.
- **Um trecho ruim:** apague só o `.wav` dele em `trechos/` e rode a célula 7 com `REFAZER = True`.
- **Capítulo inteiro de novo:** coloque o número dele em `CAPITULOS_PARA_GERAR` e use `REFAZER = True`.

## 8. Testar com ouvintes

Use a ficha de observação do [GUIA.md](GUIA.md). Peça o consentimento por escrito dos responsáveis e a concordância de cada jovem. Não grave os jovens. Leve as duas versões, A e B, e anote qual cada um prefere.
