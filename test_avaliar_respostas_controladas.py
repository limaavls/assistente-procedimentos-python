import unittest

import avaliar_respostas_controladas as arc
from avaliacao import CasoAvaliacao


class TestAvaliarRespostasControladas(
    unittest.TestCase
):

    def test_base_controlada_aprova_todos_os_casos(self):
        resumo = arc.avaliar_respostas()

        self.assertEqual(
            resumo.total,
            12,
        )

        self.assertEqual(
            resumo.aprovados,
            12,
        )

        self.assertEqual(
            resumo.reprovados,
            0,
        )

        self.assertEqual(
            resumo.taxa_aprovacao,
            1.0,
        )

        self.assertEqual(
            resumo.taxa_citacoes_validas,
            1.0,
        )

        self.assertEqual(
            resumo.taxa_conteudo_valido,
            1.0,
        )

        self.assertEqual(
            resumo.taxa_status_valido,
            1.0,
        )

    def test_detecta_termo_obrigatorio_ausente(self):
        caso = CasoAvaliacao(
            identificador="teste",
            pergunta="Pergunta.",
            documentos_esperados=(
                "teste.txt",
            ),
            termos_obrigatorios=(
                "quantidade",
            ),
            status_esperado="respondida",
        )

        respostas = {
            "teste": arc.RespostaControlada(
                texto="Informe o setor.",
                documentos_encontrados=(
                    "teste.txt",
                ),
                documentos_citados=(
                    "teste.txt",
                ),
                citacoes_validas=True,
                status="respondida",
            )
        }

        resumo = arc.avaliar_respostas(
            respostas=respostas,
            casos=[
                caso
            ],
        )

        self.assertEqual(
            resumo.aprovados,
            0,
        )

        resultado = resumo.resultados[
            0
        ]

        self.assertEqual(
            resultado.termos_obrigatorios_ausentes,
            (
                "quantidade",
            ),
        )

    def test_detecta_termo_proibido(self):
        caso = CasoAvaliacao(
            identificador="teste",
            pergunta="Pergunta.",
            documentos_esperados=(
                "teste.txt",
            ),
            termos_proibidos=(
                "10 dias",
            ),
            status_esperado="respondida",
        )

        respostas = {
            "teste": arc.RespostaControlada(
                texto=(
                    "O prazo é de 10 dias."
                ),
                documentos_encontrados=(
                    "teste.txt",
                ),
                documentos_citados=(
                    "teste.txt",
                ),
                citacoes_validas=True,
                status="respondida",
            )
        }

        resumo = arc.avaliar_respostas(
            respostas=respostas,
            casos=[
                caso
            ],
        )

        self.assertFalse(
            resumo.resultados[
                0
            ].conteudo_valido
        )

    def test_detecta_citacao_invalida(self):
        caso = CasoAvaliacao(
            identificador="teste",
            pergunta="Pergunta.",
            documentos_esperados=(
                "teste.txt",
            ),
            status_esperado="respondida",
        )

        respostas = {
            "teste": arc.RespostaControlada(
                texto="Resposta.",
                documentos_encontrados=(
                    "teste.txt",
                ),
                documentos_citados=(
                    "teste.txt",
                ),
                citacoes_validas=False,
                status="respondida",
            )
        }

        resumo = arc.avaliar_respostas(
            respostas=respostas,
            casos=[
                caso
            ],
        )

        self.assertFalse(
            resumo.resultados[
                0
            ].citacoes_validas
        )

        self.assertFalse(
            resumo.resultados[
                0
            ].aprovado
        )

    def test_detecta_documento_citado_errado(self):
        caso = CasoAvaliacao(
            identificador="teste",
            pergunta="Pergunta.",
            documentos_esperados=(
                "correto.txt",
            ),
            status_esperado="respondida",
        )

        respostas = {
            "teste": arc.RespostaControlada(
                texto="Resposta.",
                documentos_encontrados=(
                    "correto.txt",
                ),
                documentos_citados=(
                    "errado.txt",
                ),
                citacoes_validas=True,
                status="respondida",
            )
        }

        resumo = arc.avaliar_respostas(
            respostas=respostas,
            casos=[
                caso
            ],
        )

        self.assertFalse(
            resumo.resultados[
                0
            ].citacoes_validas
        )

    def test_detecta_status_errado(self):
        caso = CasoAvaliacao(
            identificador="teste",
            pergunta="Pergunta.",
            documentos_esperados=(
                "teste.txt",
            ),
            status_esperado=(
                "sem_evidencia"
            ),
        )

        respostas = {
            "teste": arc.RespostaControlada(
                texto="Resposta.",
                documentos_encontrados=(
                    "teste.txt",
                ),
                documentos_citados=(
                    "teste.txt",
                ),
                citacoes_validas=True,
                status="respondida",
            )
        }

        resumo = arc.avaliar_respostas(
            respostas=respostas,
            casos=[
                caso
            ],
        )

        self.assertFalse(
            resumo.resultados[
                0
            ].status_valido
        )

    def test_rejeita_resposta_ausente(self):
        caso = CasoAvaliacao(
            identificador="sem_resposta",
            pergunta="Pergunta.",
        )

        with self.assertRaisesRegex(
            ValueError,
            "Não existe resposta controlada",
        ):
            arc.avaliar_respostas(
                respostas={},
                casos=[
                    caso
                ],
            )

    def test_rejeita_formato_invalido(self):
        caso = CasoAvaliacao(
            identificador="teste",
            pergunta="Pergunta.",
        )

        with self.assertRaisesRegex(
            ValueError,
            "formato inválido",
        ):
            arc.avaliar_respostas(
                respostas={
                    "teste": {
                        "texto": "Resposta."
                    }
                },
                casos=[
                    caso
                ],
            )

    def test_percentual(self):
        self.assertEqual(
            arc.percentual(
                0.875
            ),
            "87.5%",
        )


if __name__ == "__main__":
    unittest.main()