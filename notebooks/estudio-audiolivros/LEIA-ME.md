# Estúdio de audiolivros

Um notebook e um script para todos os livros, PCD e pessoais. A parte criativa (adaptar, cortar, comentar) continua com o Claude e com você; a receita de bolo fica aqui.

| Arquivo | Para quê |
|---|---|
| `Estudio_Audiolivros_Colab.ipynb` | Escolha o livro, clique em *Executar tudo*. Narra só o que falta e organiza o Drive |
| `estudio.py` | O motor: lê e confere os roteiros, narra, monta as versões, organiza o Drive e baixa textos |
| `livros.json` | O catálogo: tipo de cada livro, pasta no Drive e onde estão os roteiros no fork |
| `LICOES.md` | O que aprendemos e onde cada lição já está automatizada |

## Narrar

Abra no Colab:
https://colab.research.google.com/github/sdpaula36-stack/VoiceStudio/blob/main/notebooks/estudio-audiolivros/Estudio_Audiolivros_Colab.ipynb

1. `Ambiente de execução → Alterar o tipo → GPU T4`.
2. Na célula 0, escolha o livro. Deixe `CAPITULOS` vazio para narrar só o que falta.
3. `Ambiente de execução → Executar tudo` e autorize o Drive quando a janela abrir.

O que sai no Drive:

- `capNN/` com os MP3 de cada capítulo (mesmos nomes dos notebooks antigos; nada do que já foi narrado é refeito);
- `ouvir/<versão>/NN - Título.mp3` e uma playlist por versão, para ouvir em sequência;
- `situacao.md`: quais capítulos estão prontos e a duração de cada um.

## Livro novo

1. **Texto:** `python -I estudio.py baixar gutenberg <id> pasta` ou `baixar wikisource <língua> "<página>" pasta`. EPUB/PDF: `audiolivros/ferramentas/extrair_livro.py`.
2. **Roteiros:** o Claude adapta cada capítulo (PCD: `PROMPT_ADAPTACAO.md`; pessoal: regras do `LEIA-ME` dos audiolivros pessoais) e salva os JSON numa pasta do fork.
3. **Conferir:** `python -I estudio.py validar roteiros/*.json`.
4. **Catálogo:** acrescente o livro em `livros.json` (tipo, pasta, branch e pasta dos roteiros) e rode `python -I estudio.py notebook Estudio_Audiolivros_Colab.ipynb` para o livro aparecer na lista.
5. Narre no Colab.

Para testar um roteiro sem mexer no git, ponha os JSON em `<livro>/roteiros/` no Drive: o notebook usa essa pasta quando ela existe.
