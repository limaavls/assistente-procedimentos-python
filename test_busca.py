import unittest
from pathlib import Path

from busca import buscar_por_pergunta, extrair_palavras


class TestBuscaPorPergunta(unittest.TestCase):

    def test_extrai_palavras_sem_acento_e_sem_repeticao(self):
        resultado = extrair_palavras(
            "Como é a SOLICITAÇÃO de material material?"
        )
        self.assertEqual(resultado, {"solicitacao", "material"})

    def test_prioriza_documento_com_mais_palavras_em_comum(self):
        documentos = [
            (Path("a.txt"), "Material disponível."),
            (Path("b.txt"), "Para solicitar material, informe o setor."),
        ]

        resultado = buscar_por_pergunta(
            documentos, "Como solicitar material?"
        )

        self.assertEqual(
            [item[0].name for item in resultado],
            ["b.txt", "a.txt"],
        )

    def test_nao_encontra_parte_de_palavra(self):
        documentos = [
            (Path("exemplo.txt"), "Material disponível.")
        ]
        self.assertEqual(
            buscar_por_pergunta(documentos, "mat"), []
        )

    def test_buscas_sem_palavras_uteis(self):
        documentos = [
            (Path("exemplo.txt"), "Material disponível.")
        ]

        for pergunta in ["", "???", "como de para"]:
            with self.subTest(pergunta=pergunta):
                self.assertEqual(
                    buscar_por_pergunta(documentos, pergunta), []
                )

    def test_preserva_paragrafo_completo_sem_duplicar(self):
        trecho = (
            "Para solicitar material:\n"
            "- Informe o setor.\n"
            "- Informe a quantidade."
        )

        texto = f"Título.\n\n{trecho}\n\nContato: RH."
        documentos = [(Path("exemplo.txt"), texto)]

        resultado = buscar_por_pergunta(
            documentos, "Como solicitar material?"
        )

        self.assertEqual(resultado[0][2], [trecho])

    def test_pergunta_sem_correspondencia(self):
        documentos = [
            (Path("exemplo.txt"), "Solicitação de material.")
        ]

        self.assertEqual(
            buscar_por_pergunta(
                documentos, "Qual prazo de reembolso?"
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()