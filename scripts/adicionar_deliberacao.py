"""Adiciona ao CSV as deliberações de uma issue "Sugerir deliberação".

Uso (no GitHub Action): ISSUE_BODY="..." python scripts/adicionar_deliberacao.py --resumo resumo.md

Lê o corpo da issue gerado pelo formulário .github/ISSUE_TEMPLATE/nova-deliberacao.yml,
acrescenta uma linha por deliberação em data/deliberacoes.csv e valida o arquivo inteiro
com as mesmas regras de scripts/gerar_dados.py. Se algo estiver errado, nada é gravado,
os problemas vão para a saída de erro e o código de saída é 1.
"""

import argparse
import csv
import io
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gerar_dados import COLUNAS, ENTRADA, validar  # noqa: E402

# Títulos dos campos no formulário -> chaves usadas aqui.
CAMPOS = {
    "Encontro": "encontro",
    "Nome do encontro (se escolheu Outro)": "outro_encontro",
    "Ano": "ano",
    "Grupo de discussão ou espaço": "grupo",
    "Deliberações": "deliberacoes",
    "Fonte (opcional)": "fonte",
    "Confirmação": "confirmacao",
}
SEM_RESPOSTA = "_No response_"


class SugestaoInvalida(Exception):
    pass


def ler_formulario(corpo):
    """Separa o corpo da issue em {chave: valor} pelos títulos '### ...' conhecidos."""
    titulos = "|".join(re.escape(t) for t in CAMPOS)
    partes = re.split(rf"^###\s+({titulos})\s*$", corpo.replace("\r\n", "\n"), flags=re.MULTILINE)
    campos = {}
    for titulo, valor in zip(partes[1::2], partes[2::2]):
        valor = valor.strip()
        campos[CAMPOS[titulo]] = "" if valor == SEM_RESPOSTA else valor
    return campos


def montar_registros(campos):
    """Converte os campos do formulário em [(evento, ano, descricao)]."""
    erros = []

    encontro = campos.get("encontro", "")
    if encontro == "Outro":
        encontro = campos.get("outro_encontro", "")
        if not encontro:
            erros.append('Escolheu "Outro" mas não informou o nome do encontro.')
    elif not encontro:
        erros.append("Encontro não informado.")

    ano = campos.get("ano", "").strip()
    if not re.fullmatch(r"(19|20)\d{2}", ano):
        erros.append(f"Ano inválido: {ano!r} (use 4 dígitos, ex.: 2024).")

    grupo = " ".join(campos.get("grupo", "").split())
    if not grupo:
        erros.append("Grupo de discussão ou espaço não informado.")

    textos = [t.strip() for t in re.split(r"^\s*---\s*$", campos.get("deliberacoes", ""), flags=re.MULTILINE)]
    textos = [t for t in textos if t]
    if not textos:
        erros.append("Nenhuma deliberação informada.")

    if erros:
        raise SugestaoInvalida(erros)

    evento = f"{grupo} - {encontro} {ano}"
    return [(evento, ano, texto) for texto in textos]


def adicionar(caminho_csv, corpo):
    """Acrescenta as deliberações da issue ao CSV. Retorna as linhas adicionadas."""
    registros = montar_registros(ler_formulario(corpo))

    with open(caminho_csv, encoding="utf-8", newline="") as f:
        conteudo = f.read()
        f.seek(0)
        leitor = csv.DictReader(f)
        if leitor.fieldnames != COLUNAS:
            raise SugestaoInvalida([f"Cabeçalho inesperado em {caminho_csv}: {leitor.fieldnames}"])
        existentes = []
        for linha in leitor:
            linha["__linha__"] = leitor.line_num
            existentes.append(linha)

    proximo_id = max((int(l["id"]) for l in existentes if l["id"].isdigit()), default=0) + 1
    novas = [
        {"id": str(proximo_id + i), "evento": evento, "ano": ano, "descricao": texto}
        for i, (evento, ano, texto) in enumerate(registros)
    ]

    # Valida a base inteira com as novas linhas antes de gravar qualquer coisa.
    _, erros = validar(existentes + [dict(l, __linha__=f"nova {i + 1}") for i, l in enumerate(novas)])
    if erros:
        raise SugestaoInvalida(erros)

    saida = io.StringIO()
    escritor = csv.DictWriter(saida, fieldnames=COLUNAS, lineterminator="\n")
    escritor.writerows(novas)
    if conteudo and not conteudo.endswith("\n"):
        conteudo += "\n"
    with open(caminho_csv, "w", encoding="utf-8", newline="") as f:
        f.write(conteudo + saida.getvalue())
    return novas


def resumo_markdown(novas):
    linhas = [f"Adiciona {len(novas)} deliberação(ões) em `data/deliberacoes.csv`:", ""]
    for l in novas:
        texto = " ".join(l["descricao"].split())
        linhas.append(f"- **#{l['id']}** {l['evento']}: {texto[:150]}{'…' if len(texto) > 150 else ''}")
    return "\n".join(linhas)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--csv", default=ENTRADA, type=Path)
    parser.add_argument("--resumo", type=Path, help="arquivo onde gravar o resumo em Markdown")
    args = parser.parse_args()

    corpo = os.environ.get("ISSUE_BODY") or sys.stdin.read()
    try:
        novas = adicionar(args.csv, corpo)
    except SugestaoInvalida as e:
        for erro in e.args[0]:
            print(f"- {erro}", file=sys.stderr)
        sys.exit(1)

    resumo = resumo_markdown(novas)
    if args.resumo:
        args.resumo.write_text(resumo + "\n", encoding="utf-8")
    print(resumo)


if __name__ == "__main__":
    main()
