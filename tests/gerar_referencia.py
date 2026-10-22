"""Gera tests/referencia.json com resultados do scikit-learn.

Implementação de referência da busca de site/js/similaridade.js. O teste
tests/similaridade.test.mjs compara as duas.

Uso: python tests/gerar_referencia.py   (requer scikit-learn)
"""

import json
import re
import unicodedata
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "site" / "data"
SAIDA = RAIZ / "tests" / "referencia.json"
LIMITE = 5

with open(DADOS / "stopwords-pt.json", encoding="utf-8") as f:
    STOPWORDS = set(json.load(f))


def tokenizar(texto):
    palavras = re.findall(r"[^\W_]+", unicodedata.normalize("NFC", texto).lower())
    return [p for p in palavras if len(p) >= 2 and p not in STOPWORDS]


def extrair_ano(texto):
    m = re.search(r"(?:19|20)\d{2}", texto)
    return int(m.group()) if m else None


def buscar(consultas, base, vetorizador, matriz_base):
    matriz_consultas = vetorizador.transform([c["descricao"] for c in consultas])
    sim_base = linear_kernel(matriz_consultas, matriz_base)
    sim_consultas = linear_kernel(matriz_consultas, matriz_consultas)
    anos = [extrair_ano(c["evento"]) for c in consultas]

    resultados = []
    for i, ano in enumerate(anos):
        candidatos = [
            {"origem": "base", "indice": j, "similaridade": float(sim_base[i, j])}
            for j, d in enumerate(base)
            if ano is None or d["ano"] != ano
        ] + [
            {"origem": "consulta", "indice": j, "similaridade": float(sim_consultas[i, j])}
            for j in range(len(consultas))
            if j != i and (ano is None or anos[j] != ano)
        ]
        candidatos = [c for c in candidatos if c["similaridade"] > 1e-12]
        candidatos.sort(key=lambda c: -c["similaridade"])
        resultados.append(candidatos[:LIMITE])
    return resultados


def main():
    with open(DADOS / "deliberacoes.json", encoding="utf-8") as f:
        base = json.load(f)

    vetorizador = TfidfVectorizer(tokenizer=tokenizar, lowercase=False, token_pattern=None)
    matriz_base = vetorizador.fit_transform([d["descricao"] for d in base])

    # Cada deliberação da base como consulta isolada.
    casos = [[{"evento": d["evento"], "descricao": d["descricao"]}] for d in base]
    # Casos de borda: várias consultas juntas, sem ano, sem palavras conhecidas, só stopwords.
    casos += [
        [
            {"evento": "Assembleia 2024", "descricao": "Que o custeio do PET seja pago no início do ano."},
            {"evento": "Reunião 2024", "descricao": "Pagamento do custeio dos grupos PET no começo do ano fiscal."},
            {"evento": "Sem ano", "descricao": "Saúde mental dos petianos e acompanhamento psicológico."},
        ],
        [{"evento": "Evento 2018", "descricao": "Divulgação do PET nas redes sociais e visibilidade do programa."}],
        [{"evento": "Teste", "descricao": "xyzzy plugh quux"}],
        [{"evento": "Teste 2020", "descricao": "que de a o e para com"}],
        [{"evento": "Acentos", "descricao": "AÇÕES AFIRMATIVAS, Permanência — evasão; 2º ano!"}],
    ]

    referencia = [
        {"consultas": consultas, "resultados": buscar(consultas, base, vetorizador, matriz_base)}
        for consultas in casos
    ]
    with open(SAIDA, "w", encoding="utf-8") as f:
        json.dump(referencia, f, ensure_ascii=False)
    print(f"{len(referencia)} casos -> {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
