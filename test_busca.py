import unittest
from pathlib import Path

from busca import buscar_por_pergunta, extrair_palavras
from citacoes import TrechoCandidato


class TestBuscaPorPergunta(unittest.TestCase):

    def test_extrai_palavras_sem_acento_e_sem_repeticao(self):
        resultado = extrair_palavras(
            "Como é a SOLICITAÇÃO de material material?"
        )

        self.assertEqual(
            resultado,
            {"solicitacao", "material"},
        )

    def test_prioriza_documento_com_mais_palavras_em_comum(self):
        documentos = [
            (
                Path("a.txt"),
                "Material disponível.",
            ),
            (
                Path("b.txt"),
                "Para solicitar material, informe o setor.",
            ),
        ]

        resultado = buscar_por_pergunta(
            documentos,
            "Como solicitar material?",
        )

        self.assertEqual(
            [
                item[0].name
                for item in resultado
            ],
            [
                "b.txt",
                "a.txt",
            ],
        )

    def test_nao_encontra_parte_de_palavra(self):
        documentos = [
            (
                Path("exemplo.txt"),
                "Material disponível.",
            )
        ]

        self.assertEqual(
            buscar_por_pergunta(
                documentos,
                "mat",
            ),
            [],
        )

    def test_buscas_sem_palavras_uteis(self):
        documentos = [
            (
                Path("exemplo.txt"),
                "Material disponível.",
            )
        ]

        for pergunta in [
            "",
            "???",
            "como de para",
        ]:
            with self.subTest(
                pergunta=pergunta
            ):
                self.assertEqual(
                    buscar_por_pergunta(
                        documentos,
                        pergunta,
                    ),
                    [],
                )

    def test_preserva_paragrafo_completo_sem_duplicar(self):
        trecho = (
            "Para solicitar material:\n"
            "- Informe o setor.\n"
            "- Informe a quantidade."
        )

        texto = (
            f"Título.\n\n"
            f"{trecho}\n\n"
            "Contato: RH."
        )

        documentos = [
            (
                Path("exemplo.txt"),
                texto,
            )
        ]

        resultado = buscar_por_pergunta(
            documentos,
            "Como solicitar material?",
        )

        self.assertEqual(
            len(resultado),
            1,
        )

        self.assertEqual(
            len(resultado[0][2]),
            1,
        )

        trecho_encontrado = (
            resultado[0][2][0]
        )

        self.assertIsInstance(
            trecho_encontrado,
            TrechoCandidato,
        )

        self.assertEqual(
            trecho_encontrado.texto,
            trecho,
        )

        inicio_esperado = (
            texto.index(trecho)
        )

        fim_esperado = (
            inicio_esperado
            + len(trecho)
        )

        self.assertEqual(
            trecho_encontrado.inicio,
            inicio_esperado,
        )

        self.assertEqual(
            trecho_encontrado.fim,
            fim_esperado,
        )

        self.assertEqual(
            texto[
                trecho_encontrado.inicio:
                trecho_encontrado.fim
            ],
            trecho,
        )

        self.assertIsNone(
            trecho_encontrado.indice_recorte
        )

    def test_pergunta_sem_correspondencia(self):
        documentos = [
            (
                Path("exemplo.txt"),
                "Solicitação de material.",
            )
        ]

        self.assertEqual(
            buscar_por_pergunta(
                documentos,
                "Qual prazo de reembolso?",
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()