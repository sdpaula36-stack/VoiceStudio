# Audiolivros pessoais com leitura guiada

Projeto pessoal, não comercial, separado dos audiolivros infantis (`D:\Projetos\Audio\Audiolivros`).
Proposta completa: https://claude.ai/artifact/XH9TDPjEGpiCR8HCyPtVgX

## Regras

- Só obras em domínio público, e traduções também em domínio público ou feitas por nós.
- Duas vozes fixas: **leitor** (só frases do autor) e **comentarista** (contexto, ligações dentro da obra e com outras obras).
- Todo corte é anunciado pelo leitor, `(Corte: ...)`, e listado no campo `cortes` do roteiro.
- Comentário diz o que é fato e o que é interpretação. Fatos conferidos antes de narrar.
- Cada capítulo sai em duas versões: `guiada` (com comentários) e `limpa` (só o texto).

## Pastas

- `livros/<livro>/original/`: texto original usado como fonte.
- `livros/<livro>/roteiros/`: um JSON por capítulo, trechos `[leitor|comentarista, texto, velocidade, pausa]`.
- `ferramentas/make_audiolivro_pessoal.py`: confere os roteiros e gera o notebook do Colab.
- `colab/`: notebooks prontos.

## Livros

| Livro | Situação |
| --- | --- |
| Memórias do Subsolo (Dostoiévski, 1864), tradução nossa do russo | Parte I (caps 1-11) narrada; Parte II (caps 12-21, *A propósito da neve molhada*) roteirizada; livro completo |

## Narrar no Colab

Abra `colab/Subsolo_Colab.ipynb` no Colab (GPU T4) e rode as células de cima para baixo.
A célula 4.5 aceita as licenças dos modelos; sem ela a geração falha.
Os MP3 vão para `MyDrive/Audiolivros-pessoais/<livro>/capNN/`.

Para gerar de novo o notebook depois de editar um roteiro:

```
python -I ferramentas/make_audiolivro_pessoal.py colab/Subsolo_Colab.ipynb livros/subsolo/roteiros/subsolo_cap*.json
```
