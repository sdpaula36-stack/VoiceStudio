# Audiolivros adaptados

Projeto de audiolivros adaptados para crianças e adolescentes com deficiência visual, síndrome de Down, autismo e TDAH. A narração é gerada por IA no Google Colab (grátis), com o modelo OmniVoice do VoiceStudio.

Esta pasta só tem o projeto de audiolivros. Os sons e falas dos jogos ficam na pasta de cada jogo (`D:\Projetos\Jogos\...\docs\estudio-de-voz`).

## Comece por aqui

1. [COMO_FIZEMOS_NARIZINHO.md](COMO_FIZEMOS_NARIZINHO.md): o que foi feito no piloto, com tempos, custo, vozes e onde ficou cada arquivo.
2. [COMO_A_NARRACAO_E_GERADA.md](COMO_A_NARRACAO_E_GERADA.md): como as vozes são criadas e como saem as versões A (sem efeitos) e B (com vinheta e riacho).
3. [PASSO_A_PASSO.md](PASSO_A_PASSO.md): as 8 etapas para fazer um livro novo.
4. [GUIA.md](GUIA.md): regras de adaptação, estilo de narração e ficha de observação dos ouvintes.
5. [PROMPT_ADAPTACAO.md](PROMPT_ADAPTACAO.md): o pedido pronto para o Claude adaptar um capítulo.

## Pastas

| Pasta | Conteúdo |
|---|---|
| `ferramentas/` | `extrair_livro.py` (EPUB/PDF em capítulos), `validar_roteiro.py` (confere o roteiro), `make_audiolivro.py` (gera o notebook do Colab) |
| `colab/` | Notebooks prontos para subir no Colab. `Audiolivro_Piloto_Colab.ipynb` narra Narizinho, caps. 1 a 3 |
| `livros/<livro>/roteiros/` | Os roteiros JSON de cada capítulo. Exemplo: `livros/narizinho/` |
| `livros/<livro>/texto/` | (opcional) Texto extraído do original, só de obras em domínio público |

Os áudios não ficam aqui: ficam no Google Drive, em `Meu Drive/Audiolivros/<livro>/`.

## Livro novo em 5 linhas

```bash
python -I ferramentas/extrair_livro.py livro.epub livros/meu_livro/texto
# adapte cada capítulo com o PROMPT_ADAPTACAO.md e salve em livros/meu_livro/roteiros/
python -I ferramentas/validar_roteiro.py livros/meu_livro/roteiros/*.json
python -I ferramentas/make_audiolivro.py colab/meu_livro_Colab.ipynb livros/meu_livro/roteiros/*.json
# suba o .ipynb no Colab, GPU T4, Executar tudo; os MP3 vão para o Drive
```

No JSON, o campo `"pasta"` define o nome da pasta no Drive (ex.: `"narizinho"`).

## Livros

| Livro | Situação | Áudios |
|---|---|---|
| *Reinações de Narizinho* (Lobato) | Caps. 1 a 3 narrados e aprovados em 05/11/2026; falta conferir com o original e testar com ouvintes | `Meu Drive/Audiolivros/narizinho/` |
