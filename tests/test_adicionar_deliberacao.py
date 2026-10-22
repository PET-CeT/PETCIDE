"""Testes de scripts/adicionar_deliberacao.py. Uso: python -m unittest discover tests"""

import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from adicionar_deliberacao import SugestaoInvalida, adicionar, ler_formulario  # noqa: E402

CSV_INICIAL = (
    "id,evento,ano,descricao\n"
    "10,GDT 1 - ENAPET 2018,2018,Que o custeio seja pago no início do ano.\n"
    '11,GDT 2 - ENAPET 2018,2018,"Texto com vírgula, e\nquebra de linha."\n'
)


def corpo_issue(encontro="ENAPET", outro="_No response_", ano="2024", grupo="GDT 3",
                deliberacoes="Que os grupos PET divulguem suas ações.", fonte="_No response_"):
    """Corpo no formato que o GitHub gera para o formulário nova-deliberacao.yml."""
    return (
        f"### Encontro\n\n{encontro}\n\n"
        f"### Nome do encontro (se escolheu Outro)\n\n{outro}\n\n"
        f"### Ano\n\n{ano}\n\n"
        f"### Grupo de discussão ou espaço\n\n{grupo}\n\n"
        f"### Deliberações\n\n{deliberacoes}\n\n"
        f"### Fonte (opcional)\n\n{fonte}\n\n"
        "### Confirmação\n\n- [X] Os textos foram copiados da ata oficial do encontro, sem alterações de conteúdo."
    )


class AdicionarDeliberacaoTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.csv = Path(self.dir.name) / "deliberacoes.csv"
        self.csv.write_text(CSV_INICIAL, encoding="utf-8")

    def tearDown(self):
        self.dir.cleanup()

    def linhas(self):
        with open(self.csv, encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))

    def test_adiciona_uma_deliberacao_com_proximo_id(self):
        novas = adicionar(self.csv, corpo_issue())
        self.assertEqual(novas, [{"id": "12", "evento": "GDT 3 - ENAPET 2024", "ano": "2024",
                                  "descricao": "Que os grupos PET divulguem suas ações."}])
        linhas = self.linhas()
        self.assertEqual(len(linhas), 3)
        self.assertEqual(linhas[1]["descricao"], "Texto com vírgula, e\nquebra de linha.")
        self.assertEqual(linhas[2]["evento"], "GDT 3 - ENAPET 2024")

    def test_varias_deliberacoes_separadas_por_tracos(self):
        texto = "Primeira deliberação,\ncom duas linhas.\n---\nSegunda deliberação.\n  ---  \n\n---\nTerceira."
        novas = adicionar(self.csv, corpo_issue(deliberacoes=texto))
        self.assertEqual([n["id"] for n in novas], ["12", "13", "14"])
        self.assertEqual(novas[0]["descricao"], "Primeira deliberação,\ncom duas linhas.")
        self.assertEqual(novas[2]["descricao"], "Terceira.")

    def test_encontro_outro_usa_nome_informado(self):
        novas = adicionar(self.csv, corpo_issue(encontro="Outro", outro="SulPET", grupo="Encontro de Tutores"))
        self.assertEqual(novas[0]["evento"], "Encontro de Tutores - SulPET 2024")

    def test_quebra_de_linha_windows(self):
        novas = adicionar(self.csv, corpo_issue().replace("\n", "\r\n"))
        self.assertEqual(novas[0]["ano"], "2024")

    def test_titulo_markdown_dentro_do_texto_nao_quebra_campos(self):
        texto = "### Considerando\nQue os grupos PET registrem suas atas."
        novas = adicionar(self.csv, corpo_issue(deliberacoes=texto))
        self.assertEqual(novas[0]["descricao"], texto)

    def assertRecusa(self, corpo, trecho):
        antes = self.csv.read_text(encoding="utf-8")
        with self.assertRaises(SugestaoInvalida) as ctx:
            adicionar(self.csv, corpo)
        self.assertIn(trecho, " ".join(ctx.exception.args[0]))
        self.assertEqual(self.csv.read_text(encoding="utf-8"), antes, "CSV não pode mudar quando recusa")

    def test_recusa_ano_invalido(self):
        self.assertRecusa(corpo_issue(ano="24"), "Ano inválido")

    def test_recusa_outro_sem_nome(self):
        self.assertRecusa(corpo_issue(encontro="Outro"), "nome do encontro")

    def test_recusa_sem_grupo(self):
        self.assertRecusa(corpo_issue(grupo="_No response_"), "Grupo")

    def test_recusa_descricao_que_ja_existe(self):
        self.assertRecusa(corpo_issue(deliberacoes="Que o custeio seja pago no início do ano."), "repetida")

    def test_recusa_duplicada_dentro_da_issue(self):
        self.assertRecusa(corpo_issue(deliberacoes="Mesmo texto.\n---\nMesmo texto."), "repetida")

    def test_ler_formulario_trata_sem_resposta_como_vazio(self):
        campos = ler_formulario(corpo_issue())
        self.assertEqual(campos["outro_encontro"], "")
        self.assertEqual(campos["fonte"], "")


if __name__ == "__main__":
    unittest.main()
