import unittest
from pathlib import Path

import executar_avaliacao as ea
from avaliacao import CasoAvaliacao
from citacoes import TrechoCandidato


class TestExecutarAvaliacao(
    unittest.TestCase
):

    def setUp(self):
        self.documentos = [
            (
                Path("a.txt"),
                "Conteúdo A.",
            ),
            (
                Path("b.txt"),
                "Conteúdo B.",
            ),
        ]

        self.casos = [
            CasoAvaliacao(
                identificador="caso_a",
                pergunta="Pergunta A",
                documentos_esperados=(
                    "a.txt",
                ),
            ),
            CasoAvaliacao(
                identificador="caso_b",
                pergunta="Pergunta B",
                documentos_esperados=(
                    "b.txt",
                ),
            ),
        ]

    def resultado(
        self,
        arquivo,
        texto,
    ):
        return (
            arquivo,
            texto,
            [
                TrechoCandidato(
                    texto=texto,
                    inicio=0,
                    fim=len(
                        texto
                    ),
                )
            ],
        )

    def test_nomes_documentos_preserva_ordem(self):
        resultados = [
            self.resultado(
                Path("b.txt"),
                "B",
            ),
            self.resultado(
                Path("a.txt"),
                "A",
            ),
        ]

        self.assertEqual(
            ea.nomes_documentos(
                resultados
            ),
            (
                "b.txt",
                "a.txt",
            ),
        )

    def test_nomes_documentos_remove_repeticao(self):
        resultados = [
            self.resultado(
                Path("a.txt"),
                "A",
            ),
            self.resultado(
                Path("a.txt"),
                "A",
            ),
        ]

        self.assertEqual(
            ea.nomes_documentos(
                resultados
            ),
            (
                "a.txt",
            ),
        )

    def test_rejeita_resultado_invalido(self):
        with self.assertRaises(
            ValueError
        ):
            ea.nomes_documentos(
                [
                    (
                        "arquivo.txt",
                        "Texto",
                        [],
                    )
                ]
            )

    def test_avaliar_modo_perfeito(self):
        def busca(
            documentos,
            pergunta,
        ):
            if pergunta == "Pergunta A":
                return [
                    self.resultado(
                        Path("a.txt"),
                        "Conteúdo A.",
                    )
                ]

            return [
                self.resultado(
                    Path("b.txt"),
                    "Conteúdo B.",
                )
            ]

        resumo = ea.avaliar_modo(
            "teste",
            busca,
            documentos=self.documentos,
            casos=self.casos,
        )

        self.assertEqual(
            resumo.total,
            2,
        )

        self.assertEqual(
            resumo.aprovados,
            2,
        )

        self.assertEqual(
            resumo.taxa_aprovacao,
            1.0,
        )

        self.assertEqual(
            resumo.recall_media,
            1.0,
        )

        self.assertEqual(
            resumo.mrr,
            1.0,
        )

    def test_avaliar_modo_detecta_falha(self):
        def busca(
            documentos,
            pergunta,
        ):
            return [
                self.resultado(
                    Path("a.txt"),
                    "Conteúdo A.",
                )
            ]

        resumo = ea.avaliar_modo(
            "teste",
            busca,
            documentos=self.documentos,
            casos=self.casos,
        )

        self.assertEqual(
            resumo.aprovados,
            1,
        )

        self.assertEqual(
            resumo.taxa_aprovacao,
            0.5,
        )

        falha = resumo.resultados[
            1
        ]

        self.assertFalse(
            falha.aprovado
        )

        self.assertEqual(
            falha.recall,
            0.0,
        )

    def test_precision_penaliza_resultados_extras(self):
        def busca(
            documentos,
            pergunta,
        ):
            if pergunta == "Pergunta A":
                return [
                    self.resultado(
                        Path("a.txt"),
                        "Conteúdo A.",
                    ),
                    self.resultado(
                        Path("b.txt"),
                        "Conteúdo B.",
                    ),
                ]

            return [
                self.resultado(
                    Path("b.txt"),
                    "Conteúdo B.",
                )
            ]

        resumo = ea.avaliar_modo(
            "teste",
            busca,
            documentos=self.documentos,
            casos=self.casos,
        )

        self.assertEqual(
            resumo.resultados[
                0
            ].precision,
            0.5,
        )

        self.assertEqual(
            resumo.resultados[
                0
            ].recall,
            1.0,
        )

    def test_mrr_considera_posicao(self):
        def busca(
            documentos,
            pergunta,
        ):
            if pergunta == "Pergunta A":
                return [
                    self.resultado(
                        Path("b.txt"),
                        "Conteúdo B.",
                    ),
                    self.resultado(
                        Path("a.txt"),
                        "Conteúdo A.",
                    ),
                ]

            return [
                self.resultado(
                    Path("b.txt"),
                    "Conteúdo B.",
                )
            ]

        resumo = ea.avaliar_modo(
            "teste",
            busca,
            documentos=self.documentos,
            casos=self.casos,
        )

        self.assertEqual(
            resumo.resultados[
                0
            ].reciprocal_rank,
            0.5,
        )

    def test_executar_comparacao_usa_todos_os_modos(self):
        chamadas = []

        def busca_a(
            documentos,
            pergunta,
        ):
            chamadas.append(
                (
                    "a",
                    pergunta,
                )
            )

            return []

        def busca_b(
            documentos,
            pergunta,
        ):
            chamadas.append(
                (
                    "b",
                    pergunta,
                )
            )

            return []

        modos = {
            "modo_a": busca_a,
            "modo_b": busca_b,
        }

        resumos = ea.executar_comparacao(
            modos
        )

        self.assertEqual(
            [
                resumo.modo
                for resumo
                in resumos
            ],
            [
                "modo_a",
                "modo_b",
            ],
        )

        self.assertTrue(
            chamadas
        )

    def test_avaliacao_nao_exige_gemini(self):
        self.assertNotIn(
            "gemini",
            " ".join(
                ea.MODOS.keys()
            ).casefold(),
        )

    def test_percentual(self):
        self.assertEqual(
            ea.percentual(
                0.875
            ),
            "87.5%",
        )

    def test_avaliar_modo_rejeita_sem_casos(self):
        with self.assertRaises(
            ValueError
        ):
            ea.avaliar_modo(
                "teste",
                lambda documentos, pergunta: [],
                documentos=self.documentos,
                casos=[],
            )


if __name__ == "__main__":
    unittest.main()