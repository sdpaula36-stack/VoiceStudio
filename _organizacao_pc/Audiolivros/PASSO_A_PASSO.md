# Passo a passo: do livro ao audiolivro adaptado

Este é o caminho que usamos no piloto de *Reinações de Narizinho* (capítulos 1 a 3). Os caminhos abaixo partem da pasta `Audiolivros` (no PC: `D:\Projetos\Audiolivros`). O registro completo do que foi feito com Narizinho, com tempos, custo e locais, está em [COMO_FIZEMOS_NARIZINHO.md](COMO_FIZEMOS_NARIZINHO.md).

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
python -I ferramentas/extrair_livro.py meu_livro.epub livros/meu_livro/texto
# PDF: primeiro "pip install pypdf"; PDF escaneado (imagem) precisa de OCR antes
```

Abra o `indice.txt`. Confira a linha **direitos** e o número de palavras de cada capítulo.

## 2. Planejar os capítulos

Meta: 500 a 1.000 palavras por capítulo do audiolivro, de 4 a 8 minutos.

- Um capítulo original longo pode virar dois, cada um com o próprio gancho.
- Capítulos originais curtos podem ser juntados num só.
- Escolha nomes simples para os personagens (`narrador`, `emilia`, `principe`). Esses nomes ficam iguais em todos os capítulos.

## 3. Adaptar cada capítulo

Use o [PROMPT_ADAPTACAO.md](PROMPT_ADAPTACAO.md): cole o texto do `capNN.txt` e preencha a lista das vozes que já existem. Salve a resposta como `livros/meu_livro/roteiros/meu_livro_capNN.json`. Os arquivos de `livros/narizinho/roteiros/` servem de exemplo.

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
python -I ferramentas/validar_roteiro.py livros/meu_livro/roteiros/*.json
```

Passe **todos** os capítulos do livro juntos. Corrija cada `ERRO`. Os `AVISO`s são sugestões.

## 6. Narrar no Colab

1. Gere o notebook com os seus capítulos:
   ```bash
   python -I ferramentas/make_audiolivro.py colab/meu_livro_Colab.ipynb livros/meu_livro/roteiros/*.json
   ```
   A pasta no Drive vem do campo `"pasta"` do JSON (ex.: `"narizinho"`). Sem esse campo, o notebook usa o título do livro sem acentos.
2. Abra o [Colab](https://colab.research.google.com), vá em *Arquivo → Fazer upload de notebook* e escolha o `.ipynb` gerado.
3. Escolha *Ambiente de execução → Alterar o tipo → GPU T4* e clique em *Executar tudo*. Se aparecer o aviso "não é de autoria do Google", clique em *Executar assim mesmo*.
4. A célula **4.5** aceita sozinha as licenças do OmniVoice e do tokenizador (uso **não comercial**). Sem ela, a geração de voz dá erro. Ela precisa rodar em toda sessão nova do Colab (veja o aviso no fim deste arquivo).
5. Tempo: a instalação leva de 5 a 8 minutos na primeira vez. Cada capítulo de 3 a 4 minutos de áudio leva de 2 a 5 minutos de GPU. Custo: zero no Colab grátis (detalhes em COMO_FIZEMOS_NARIZINHO.md).

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
