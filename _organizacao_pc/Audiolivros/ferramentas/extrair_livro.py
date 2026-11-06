"""Extrai o texto de um livro (EPUB ou PDF) em um arquivo por capítulo.

Uso:
    python -I ferramentas/extrair_livro.py livro.epub pasta_saida
    python -I ferramentas/extrair_livro.py livro.pdf  pasta_saida   (precisa de: pip install pypdf)

Gera em pasta_saida/:
    cap01.txt, cap02.txt, ...   texto limpo de cada capítulo (na ordem de leitura)
    indice.txt                  título, autor, direitos e número de palavras de cada capítulo

Antes de adaptar, confira em indice.txt a linha "direitos": só use obras em domínio
público ou com autorização por escrito do titular dos direitos.
"""
import html
import os
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

MIN_PALAVRAS = 150   # trechos menores (capa, sumário, créditos) não viram capítulo


def limpar(texto):
    texto = html.unescape(texto)
    texto = re.sub(r"[ \t\r\f\v]+", " ", texto)
    texto = re.sub(r" *\n *", "\n", texto)
    return re.sub(r"\n{3,}", "\n\n", texto).strip()


def html_para_texto(conteudo):
    conteudo = re.sub(r"(?is)<(script|style|head)\b.*?</\1>", " ", conteudo)
    conteudo = re.sub(r"(?i)<br\s*/?>|</(p|div|h[1-6]|li|blockquote)>", "\n", conteudo)
    return limpar(re.sub(r"<[^>]+>", " ", conteudo))


def ler_epub(caminho):
    z = zipfile.ZipFile(caminho)
    container = ET.fromstring(z.read("META-INF/container.xml"))
    opf_path = next(e.get("full-path") for e in container.iter() if e.tag.endswith("rootfile"))
    opf = ET.fromstring(z.read(opf_path))
    base = os.path.dirname(opf_path)

    meta = {}
    for e in opf.iter():
        nome = e.tag.rsplit("}", 1)[-1]
        if nome in ("title", "creator", "publisher", "rights", "language") and e.text:
            meta.setdefault(nome, e.text.strip())

    itens = {e.get("id"): e.get("href") for e in opf.iter() if e.tag.endswith("item")}
    ordem = [e.get("idref") for e in opf.iter() if e.tag.endswith("itemref")]
    partes = []
    for idref in ordem:
        href = itens.get(idref)
        if not href or not href.lower().endswith((".xhtml", ".html", ".htm")):
            continue
        nome = os.path.normpath(os.path.join(base, href)).replace(os.sep, "/")
        partes.append(html_para_texto(z.read(nome).decode("utf-8", "ignore")))
    return meta, partes


def ler_pdf(caminho):
    try:
        from pypdf import PdfReader
    except ImportError:
        raise SystemExit("Para PDF, instale antes: pip install pypdf")
    pdf = PdfReader(caminho)
    info = pdf.metadata or {}
    meta = {"title": info.get("/Title", ""), "creator": info.get("/Author", "")}
    texto = "\n".join(limpar(p.extract_text() or "") for p in pdf.pages)
    if not texto.strip():
        raise SystemExit("O PDF não tem texto (é imagem escaneada). Passe por um OCR antes.")
    # Divide onde aparece "Capítulo N" ou "CAPÍTULO N" no começo de uma linha.
    partes = re.split(r"\n(?=(?:cap[ií]tulo|CAP[IÍ]TULO)\s+\w+)", texto)
    return meta, [p.strip() for p in partes]


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    livro, saida = sys.argv[1], sys.argv[2]
    meta, partes = (ler_pdf if livro.lower().endswith(".pdf") else ler_epub)(livro)
    capitulos = [p for p in partes if len(p.split()) >= MIN_PALAVRAS]
    if not capitulos:
        raise SystemExit("Nenhum capítulo encontrado. Confira se o arquivo tem texto.")

    os.makedirs(saida, exist_ok=True)
    linhas = [f"título: {meta.get('title', '?')}", f"autor: {meta.get('creator', '?')}",
              f"editora: {meta.get('publisher', '?')}", f"direitos: {meta.get('rights', 'não informado')}",
              ""]
    for i, cap in enumerate(capitulos, 1):
        with open(os.path.join(saida, f"cap{i:02d}.txt"), "w", encoding="utf-8") as f:
            f.write(cap + "\n")
        palavras = len(cap.split())
        linhas.append(f"cap{i:02d}.txt  {palavras:6d} palavras  ~{palavras / 130:4.1f} min lidos sem adaptar")
    total = sum(len(c.split()) for c in capitulos)
    linhas += ["", f"total: {len(capitulos)} capítulos, {total} palavras"]
    with open(os.path.join(saida, "indice.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")
    print("\n".join(linhas))
    print(f"\nTexto salvo em {saida}/. Confira a linha 'direitos' antes de adaptar.")


if __name__ == "__main__":
    main()
