"""Confere roteiros de capítulo (JSON) antes de narrar no Colab.

Uso: python -I notebooks/audiolivro/validar_roteiro.py narizinho_cap01.json narizinho_cap02.json ...

Passe todos os capítulos do livro juntos: um personagem pode ter a voz definida num
capítulo anterior. Sai com erro (código 1) se algo impedir a narração; avisos não bloqueiam.
"""
import json
import sys

TERMOS_DE_VOZ = {"male", "female", "child", "teenager", "young adult", "middle-aged", "elderly",
                 "very low pitch", "low pitch", "moderate pitch", "high pitch", "very high pitch",
                 "whisper"}


def main(caminhos):
    erros, avisos, vozes, sementes = [], [], {}, {}
    caps = []
    for p in caminhos:
        try:
            caps.append((p, json.load(open(p, encoding="utf-8"))))
        except (OSError, json.JSONDecodeError) as e:
            erros.append(f"{p}: não abre como JSON ({e})")
    caps.sort(key=lambda pc: pc[1].get("capitulo", 0))

    for p, c in caps:
        for campo in ("livro", "capitulo", "titulo", "vozes", "trechos"):
            if campo not in c:
                erros.append(f"{p}: falta o campo '{campo}'")
        for nome, v in c.get("vozes", {}).items():
            termos = {t.strip() for t in v.get("voz", "").split(",")}
            if termos - TERMOS_DE_VOZ:
                erros.append(f"{p}: voz de '{nome}' tem termos inválidos: {sorted(termos - TERMOS_DE_VOZ)}")
            if v.get("semente") in sementes and sementes[v["semente"]] != nome:
                avisos.append(f"{p}: '{nome}' usa a mesma semente de '{sementes[v['semente']]}'")
            sementes[v.get("semente")] = nome
            vozes[nome] = v

        palavras = 0
        for i, t in enumerate(c.get("trechos", []), 1):
            onde = f"{p}, trecho {i}"
            if not (isinstance(t, list) and len(t) == 4):
                erros.append(f"{onde}: precisa ser [personagem, texto, velocidade, pausa]")
                continue
            quem, texto, vel, pausa = t
            if quem not in vozes:
                erros.append(f"{onde}: personagem '{quem}' sem voz definida (aqui ou num capítulo anterior)")
            if not isinstance(texto, str) or not texto.strip():
                erros.append(f"{onde}: texto vazio")
                continue
            if not (isinstance(vel, (int, float)) and 0.8 <= vel <= 1.2):
                erros.append(f"{onde}: velocidade {vel} fora de 0.8 a 1.2")
            if not (isinstance(pausa, (int, float)) and 0 <= pausa <= 3):
                erros.append(f"{onde}: pausa {pausa} fora de 0 a 3 segundos")
            if len(texto) > 300:
                avisos.append(f"{onde}: trecho longo ({len(texto)} caracteres); divida em dois")
            if any(len(f.split()) > 25 for f in texto.replace("!", ".").replace("?", ".").split(".")):
                avisos.append(f"{onde}: frase com mais de 25 palavras; o guia pede frases curtas")
            palavras += len(texto.split())
        if palavras and not 300 <= palavras <= 1100:
            avisos.append(f"{p}: {palavras} palavras; o guia pede de 500 a 1.000 (4 a 8 min)")
        print(f"{p}: capítulo {c.get('capitulo')}, {len(c.get('trechos', []))} trechos, {palavras} palavras")

    for a in avisos:
        print("AVISO:", a)
    for e in erros:
        print("ERRO:", e)
    print("Tudo certo para narrar." if not erros else f"{len(erros)} erro(s): corrija antes de narrar.")
    return 1 if erros else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    sys.exit(main(sys.argv[1:]))
