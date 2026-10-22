"""Valida data/deliberacoes.csv e gera site/data/deliberacoes.json.

Uso: python scripts/gerar_dados.py

Sai com código 1 e lista os problemas encontrados quando o CSV é inválido,
para que o GitHub Action barre PRs com dados quebrados.
"""

import csv
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ENTRADA = RAIZ / "data" / "deliberacoes.csv"
SAIDA = RAIZ / "site" / "data" / "deliberacoes.json"
COLUNAS = ["id", "evento", "ano", "descricao"]


def validar(linhas):
    """Retorna (registros, erros). Linhas contadas como no editor (cabeçalho = 1)."""
    registros, erros = [], []
    ids, descricoes = {}, {}

    for linha in linhas:
        n = linha.pop("__linha__")
        id_txt = (linha["id"] or "").strip()
        evento = (linha["evento"] or "").strip()
        ano_txt = (linha["ano"] or "").strip()
        descricao = (linha["descricao"] or "").strip()

        if not id_txt.isdigit():
            erros.append(f"linha {n}: id inválido ({id_txt!r})")
        elif id_txt in ids:
            erros.append(f"linha {n}: id {id_txt} repetido (já usado na linha {ids[id_txt]})")
        else:
            ids[id_txt] = n

        if not evento:
            erros.append(f"linha {n}: evento vazio")

        if not re.fullmatch(r"(19|20)\d{2}", ano_txt):
            erros.append(f"linha {n}: ano inválido ({ano_txt!r})")
        elif evento and ano_txt not in evento:
            erros.append(f"linha {n}: ano {ano_txt} não aparece no nome do evento ({evento!r})")

        if not descricao:
            erros.append(f"linha {n}: descrição vazia")
        elif descricao in descricoes:
            erros.append(f"linha {n}: descrição repetida (igual à da linha {descricoes[descricao]})")
        else:
            descricoes[descricao] = n

        if id_txt.isdigit() and ano_txt.isdigit():
            registros.append(
                {"id": int(id_txt), "evento": evento, "ano": int(ano_txt), "descricao": descricao}
            )

    return registros, erros


def ler_csv(caminho):
    with open(caminho, encoding="utf-8", newline="") as f:
        leitor = csv.DictReader(f)
        if leitor.fieldnames != COLUNAS:
            sys.exit(f"Cabeçalho deve ser {','.join(COLUNAS)}; encontrado: {leitor.fieldnames}")
        linhas = []
        for linha in leitor:
            if None in linha:
                sys.exit(f"linha {leitor.line_num}: colunas a mais (vírgula fora de aspas?)")
            linha["__linha__"] = leitor.line_num
            linhas.append(linha)
        return linhas


def main():
    registros, erros = validar(ler_csv(ENTRADA))
    if erros:
        print(f"{ENTRADA.relative_to(RAIZ)} tem {len(erros)} problema(s):", file=sys.stderr)
        for erro in erros:
            print(f"  - {erro}", file=sys.stderr)
        sys.exit(1)

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(SAIDA, "w", encoding="utf-8") as f:
        json.dump(registros, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(registros)} deliberações -> {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
