import os
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx
from google.genai import errors
from streamlit.testing.v1 import AppTest

BASE = Path(__file__).resolve().parent
PERGUNTA = "Como solicitar material?"
RESPOSTA = "Informe o setor e a quantidade. [material.txt]"

DOCUMENTOS = [
    (
        Path("material.txt"),
        "Para solicitar material, informe o setor e a quantidade.",
    ),
    (
        Path("ponto.txt"),
        "Para ajustar ponto, informe a data ao RH.",
    ),
]


class TestInterface(unittest.TestCase):
    def aplicar_patch(self, substituicao):
        objeto = substituicao.start()
        self.addCleanup(substituicao.stop)
        return objeto

    def setUp(self):
        # Usa textos fictícios, sem ler os documentos reais.
        self.aplicar_patch(
            patch("app.carregar_documentos", return_value=DOCUMENTOS)
        )

        # Não lê seu .env nem utiliza sua chave verdadeira.
        self.aplicar_patch(patch("dotenv.dotenv_values", return_value={}))
        self.aplicar_patch(
            patch.dict(
                os.environ,
                {
                    "GEMINI_API_KEY": "chave-ficticia",
                    "GEMINI_MODEL": "modelo-simulado",
                },
            )
        )

        # A resposta vem do teste, não do Google.
        self.gerar_ia = self.aplicar_patch(
            patch("consulta_ia.gerar_resposta", return_value=RESPOSTA)
        )

        # Proteção adicional: bloqueia o cliente real se for acionado.
        cliente_real = self.aplicar_patch(
            patch(
                "consulta_ia.genai.Client",
                side_effect=AssertionError(
                    "O teste não deve criar um cliente real do Gemini."
                ),
            )
        )
        self.addCleanup(cliente_real.assert_not_called)

        self.tela = AppTest.from_file(
            str(BASE / "interface.py"), default_timeout=15
        )
        self.executar()

    def executar(self):
        self.tela.run()
        erros = [str(item.value) for item in self.tela.exception]
        self.assertEqual(erros, [], f"Erro na interface: {erros}")

    def botao(self, rotulo):
        for item in self.tela.button:
            if item.label == rotulo:
                return item
        self.fail(f"Botão não encontrado: {rotulo}")

    def pesquisar(self, pergunta=PERGUNTA):
        self.tela.text_input[0].set_value(pergunta)
        self.botao("Pesquisar").click()
        self.executar()

    def autorizar(self):
        self.tela.checkbox(key="autorizar_envio").check()
        self.executar()

    def gerar_resposta_na_tela(self):
        self.pesquisar()
        self.autorizar()
        self.botao("Gerar resposta com IA").click()
        self.executar()

    def textos_exibidos(self):
        return [item.value for item in self.tela.text]

    def test_pesquisar_nao_envia_e_exige_autorizacao(self):
        self.pesquisar()

        self.gerar_ia.assert_not_called()
        self.assertTrue(self.botao("Gerar resposta com IA").disabled)
        self.assertIn(
            "Fonte: material.txt",
            [item.value for item in self.tela.subheader],
        )

    def test_marcar_autorizacao_nao_envia_sozinho(self):
        self.pesquisar()
        self.autorizar()

        self.gerar_ia.assert_not_called()
        self.assertFalse(self.botao("Gerar resposta com IA").disabled)

    def test_gerar_envia_pergunta_e_mostra_resposta(self):
        self.gerar_resposta_na_tela()

        self.gerar_ia.assert_called_once()
        pergunta, contexto, chave, modelo = self.gerar_ia.call_args.args
        self.assertEqual(pergunta, PERGUNTA)
        self.assertIn("FONTE: material.txt", contexto)
        self.assertEqual(chave, "chave-ficticia")
        self.assertEqual(modelo, "modelo-simulado")
        self.assertIn(RESPOSTA, self.textos_exibidos())

    def test_reexecucao_preserva_resposta_sem_novo_envio(self):
        self.gerar_resposta_na_tela()
        self.executar()

        self.gerar_ia.assert_called_once()
        self.assertIn(RESPOSTA, self.textos_exibidos())
        self.assertTrue(self.botao("Gerar resposta com IA").disabled)

    def test_nova_pesquisa_limpa_resposta_e_autorizacao(self):
        self.gerar_resposta_na_tela()
        self.pesquisar("Como ajustar ponto?")

        self.assertEqual(self.tela.session_state["resposta_ia"], "")
        self.assertNotIn(RESPOSTA, self.textos_exibidos())
        self.assertFalse(self.tela.checkbox(key="autorizar_envio").value)
        self.assertTrue(self.botao("Gerar resposta com IA").disabled)
        self.gerar_ia.assert_called_once()

    def test_sem_correspondencia_nao_oferece_geracao(self):
        self.pesquisar("astronomia")

        self.gerar_ia.assert_not_called()
        self.assertNotIn(
            "Gerar resposta com IA",
            [item.label for item in self.tela.button],
        )
        self.assertTrue(
            any("Não encontrei documentos" in item.value for item in self.tela.info)
        )

    def test_pergunta_vazia_mostra_aviso(self):
        self.pesquisar("")

        self.gerar_ia.assert_not_called()
        self.assertTrue(
            any("Digite uma pergunta" in item.value for item in self.tela.warning)
        )

    def test_sem_chave_mantem_busca_mas_impede_ia(self):
        os.environ["GEMINI_API_KEY"] = ""
        self.pesquisar()

        self.gerar_ia.assert_not_called()
        self.assertIn(
            "Fonte: material.txt",
            [item.value for item in self.tela.subheader],
        )
        self.assertTrue(
            any("GEMINI_API_KEY" in item.value for item in self.tela.warning)
        )
        self.assertNotIn(
            "Gerar resposta com IA",
            [item.label for item in self.tela.button],
        )

    def test_falha_de_conexao_mostra_erro_sem_resposta(self):
        self.gerar_ia.side_effect = httpx.ConnectError("Falha simulada.")
        self.gerar_resposta_na_tela()

        self.gerar_ia.assert_called_once()
        self.assertEqual(self.tela.session_state["resposta_ia"], "")
        self.assertTrue(
            any("Falha de conexão" in item.value for item in self.tela.error)
        )

    def test_cota_esgotada_mostra_erro_sem_resposta(self):
        self.gerar_ia.side_effect = errors.ClientError(
            code=429,
            response_json={
                "error": {
                    "code": 429,
                    "status": "RESOURCE_EXHAUSTED",
                    "message": "Cota simulada atingida.",
                }
            },
        )
        self.gerar_resposta_na_tela()

        self.gerar_ia.assert_called_once()
        self.assertEqual(self.tela.session_state["resposta_ia"], "")
        self.assertTrue(
            any("Cota atingida" in item.value for item in self.tela.error)
        )


if __name__ == "__main__":
    unittest.main()