import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx
from google.genai import errors, types

import consulta_ia as ia


class TestPrepararContexto(unittest.TestCase):
    def test_inclui_fontes_e_apenas_trechos(self):
        documentos = [
            (
                Path("material.txt"),
                "Texto integral não selecionado.",
                ["Informe o setor.", "Informe a quantidade."],
            ),
            (
                Path("ponto.txt"),
                "Outro texto integral.",
                ["Encaminhe ao RH."],
            ),
        ]

        contexto = ia.preparar_contexto(documentos)

        self.assertIn("FONTE: material.txt", contexto)
        self.assertIn("FONTE: ponto.txt", contexto)
        self.assertIn("Informe a quantidade.", contexto)
        self.assertNotIn("Texto integral não selecionado.", contexto)

    def test_respeita_limite_de_documentos(self):
        documentos = [
            (
                Path(f"doc_{numero}.txt"),
                "Texto.",
                [f"Trecho {numero}."],
            )
            for numero in range(ia.MAX_DOCUMENTOS + 1)
        ]

        contexto = ia.preparar_contexto(documentos)

        self.assertEqual(
            contexto.count("FONTE:"),
            ia.MAX_DOCUMENTOS,
        )
        self.assertNotIn(
            f"doc_{ia.MAX_DOCUMENTOS}.txt",
            contexto,
        )

    def test_rejeita_contexto_vazio(self):
        casos = [
            [],
            [(Path("vazio.txt"), "Texto sem trechos.", [])],
        ]

        for documentos in casos:
            with self.subTest(documentos=documentos):
                with self.assertRaises(ValueError):
                    ia.preparar_contexto(documentos)

    def test_rejeita_contexto_muito_grande(self):
        documentos = [
            (
                Path("grande.txt"),
                "",
                ["x" * (ia.MAX_CARACTERES + 1)],
            )
        ]

        with self.assertRaises(ValueError):
            ia.preparar_contexto(documentos)


class TestGerarResposta(unittest.TestCase):
    def setUp(self):
        # Substitui o cliente real antes de cada teste desta classe.
        substituicao = patch("consulta_ia.genai.Client")
        self.criar_cliente = substituicao.start()
        self.addCleanup(substituicao.stop)

        cliente = (
            self.criar_cliente.return_value.__enter__.return_value
        )
        self.chamada = cliente.models.generate_content

        self.chamada.return_value = SimpleNamespace(
            candidates=[
                SimpleNamespace(
                    finish_reason=types.FinishReason.STOP
                )
            ],
            text="Resposta simulada.",
        )

        self.pergunta = "Como solicitar material?"
        self.contexto = "FONTE: material.txt\nInforme o setor."

    def consultar(self):
        # Estes valores são fictícios.
        # Não coloque uma chave real aqui.
        return ia.gerar_resposta(
            self.pergunta,
            self.contexto,
            "chave-ficticia-para-testes",
            "modelo-simulado",
        )

    def test_devolve_resposta_sem_espacos_extras(self):
        self.chamada.return_value.text = "  Informe o setor.  \n"

        self.assertEqual(
            self.consultar(),
            "Informe o setor.",
        )
        self.chamada.assert_called_once()

    def test_prepara_pergunta_contexto_e_instrucoes(self):
        self.consultar()

        argumentos = self.chamada.call_args.kwargs
        dados = json.loads(argumentos["contents"])

        self.assertEqual(
            dados,
            {
                "pergunta": self.pergunta,
                "trechos": self.contexto,
            },
        )
        self.assertEqual(
            argumentos["model"],
            "modelo-simulado",
        )
        self.assertEqual(
            argumentos["config"].system_instruction,
            ia.INSTRUCOES,
        )

    def test_rejeita_entrada_vazia_sem_criar_cliente(self):
        casos = [
            ("", self.contexto),
            (self.pergunta, "   "),
        ]

        for pergunta, contexto in casos:
            with self.subTest(
                pergunta=pergunta,
                contexto=contexto,
            ):
                with self.assertRaises(ValueError):
                    ia.gerar_resposta(
                        pergunta,
                        contexto,
                        "chave-ficticia",
                        "modelo-simulado",
                    )

        self.criar_cliente.assert_not_called()

    def test_rejeita_resposta_sem_candidatos(self):
        self.chamada.return_value.candidates = []

        with self.assertRaises(ValueError):
            self.consultar()

    def test_rejeita_resposta_sem_texto(self):
        for texto in ("", "   ", None):
            with self.subTest(texto=texto):
                self.chamada.return_value.text = texto

                with self.assertRaises(ValueError):
                    self.consultar()

    def test_rejeita_resposta_interrompida(self):
        self.chamada.return_value.candidates[0].finish_reason = (
            types.FinishReason.MAX_TOKENS
        )

        with self.assertRaises(ValueError):
            self.consultar()

    def test_repassa_erro_de_conexao(self):
        self.chamada.side_effect = httpx.ConnectError(
            "Falha simulada."
        )

        with self.assertRaises(httpx.ConnectError):
            self.consultar()

    def test_repassa_erro_de_cota(self):
        self.chamada.side_effect = errors.ClientError(
            code=429,
            response_json={
                "error": {
                    "code": 429,
                    "status": "RESOURCE_EXHAUSTED",
                    "message": "Cota simulada atingida.",
                }
            },
        )

        with self.assertRaises(errors.APIError) as capturado:
            self.consultar()

        self.assertEqual(
            capturado.exception.code,
            429,
        )


if __name__ == "__main__":
    unittest.main()