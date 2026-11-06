"""Narra outro livro (ou outros capítulos) na MESMA sessão do Colab.

Use depois que as células 1 a 4.5 de qualquer notebook de audiolivro já rodaram
(GPU, Drive, instalação, servidor e licenças). Assim não é preciso instalar nem
aceitar as licenças de novo.

Numa célula nova:

    import urllib.request
    exec(urllib.request.urlopen(URL_DESTE_ARQUIVO).read().decode())
    rodar(URL_DO_NOTEBOOK, [13, 14, 15])   # capítulos; None = os do notebook

O notebook indicado tem as suas células 2 (pastas), 5 (roteiro), 6 (vozes) e
7 (narrar e montar) executadas aqui, nessa ordem.
"""
import json
import urllib.request


def rodar(url_notebook, capitulos=None):
    nb = json.loads(urllib.request.urlopen(url_notebook).read().decode("utf-8"))
    ip = get_ipython()  # noqa: F821 (existe dentro do Colab/Jupyter)
    for cel in nb["cells"]:
        if cel["cell_type"] != "code":
            continue
        fonte = "".join(cel["source"])
        titulo = fonte.splitlines()[0] if fonte else ""
        if not any(titulo.startswith(f"# ── {k}. ") for k in ("2", "5", "6", "7")):
            continue
        print("▶", titulo.strip("# ─"))
        res = ip.run_cell(fonte)
        if titulo.startswith("# ── 2. ") and capitulos is not None:
            ip.user_ns["CAPITULOS_PARA_GERAR"] = list(capitulos)
            print("Capítulos desta rodada:", list(capitulos))
        if not res.success:
            raise SystemExit("Parei: a célula acima deu erro.")
