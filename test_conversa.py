import unittest
from copy import deepcopy

from conversa import montar_consulta


class TestConversa(unittest.TestCase):
    def test_primeira_pergunta(self):
        busca, pedido = montar_consulta(
            "  Como solicitar material?  ",
            [],
        )

        self.assertEqual(busca, "Como solicitar material?")
        self.assertIn(
            '"pergunta_atual": "Como solicitar material?"',
            pedido,
        )

    def test_complemento_mantem_assunto(self):
        historico = [
            {
                "pergunta": "Como solicitar material?",
                "resposta": "Exemplo.",
            }
        ]

        busca, pedido = montar_consulta(
            "E quais dados preciso informar?",
            historico,
        )

        self.assertIn("Como solicitar material?", busca)
        self.assertIn("E quais dados preciso informar?", pedido)
        self.assertEqual(
            busca.count("Como solicitar material?"),
            1,
        )

    def test_usa_primeira_e_ultima_pergunta(self):
        historico = [
            {
                "pergunta": "Assunto inicial",
                "resposta": "A",
            },
            {
                "pergunta": "Pergunta intermediária",
                "resposta": "B",
            },
            {
                "pergunta": "Pergunta mais recente",
                "resposta": "C",
            },
        ]

        busca, _ = montar_consulta("Qual o prazo?", historico)

        self.assertIn("Assunto inicial", busca)
        self.assertIn("Pergunta mais recente", busca)
        self.assertNotIn("Pergunta intermediária", busca)

    def test_nao_reenvia_resposta_anterior_como_fonte(self):
        historico = [
            {
                "pergunta": "Como solicitar material?",
                "resposta": "ERRO INVENTADO",
            }
        ]

        busca, pedido = montar_consulta("E o prazo?", historico)

        self.assertNotIn("ERRO INVENTADO", busca + pedido)

    def test_rejeita_entrada_invalida(self):
        for pergunta in ("", "   ", "???", "x" * 501):
            with self.subTest(pergunta=pergunta):
                with self.assertRaises(ValueError):
                    montar_consulta(pergunta, [])

    def test_nao_altera_historico(self):
        historico = [
            {
                "pergunta": "Como solicitar material?",
                "resposta": "Exemplo.",
            }
        ]
        antes = deepcopy(historico)

        montar_consulta("E o prazo?", historico)

        self.assertEqual(historico, antes)


if __name__ == "__main__":
    unittest.main()