import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx
from google.genai import errors, types

import consulta_ia as ia
from citacoes import (
    ApresentacaoResposta,
    PacoteEnvio,
    TrechoCandidato,
)


class TestPrepararPacote(unittest.TestCase):

    def test_inclui_fontes_e_apenas_trechos(self):
        documentos = [
            (
                Path("material.txt"),
                "Texto integral não selecionado.",
                [
                    TrechoCandidato(
                        texto="Informe o setor.",
                        inicio=0,
                        fim=17,
                    ),
                    TrechoCandidato(
                        texto="Informe a quantidade.",
                        inicio=18,
                        fim=39,
                    ),
                ],
            ),
            (
                Path("ponto.txt"),
                "Outro texto integral.",
                [
                    TrechoCandidato(
                        texto="Encaminhe ao RH.",
                        inicio=0,
                        fim=16,
                    )
                ],
            ),
        ]

        pacote = ia.preparar_pacote(
            documentos
        )

        self.assertIsInstance(
            pacote,
            PacoteEnvio,
        )

        self.assertIn(
            "[F1]",
            pacote.contexto,
        )

        self.assertIn(
            "[F2]",
            pacote.contexto,
        )

        self.assertIn(
            "[F3]",
            pacote.contexto,
        )

        self.assertIn(
            "Documento: material.txt",
            pacote.contexto,
        )

        self.assertIn(
            "Documento: ponto.txt",
            pacote.contexto,
        )

        self.assertIn(
            "Informe a quantidade.",
            pacote.contexto,
        )

        self.assertNotIn(
            "Texto integral não selecionado.",
            pacote.contexto,
        )

        self.assertEqual(
            len(pacote.registro),
            3,
        )

    def test_preparar_contexto_mantem_compatibilidade(self):
        documentos = [
            (
                Path("material.txt"),
                "Informe o setor.",
                [
                    TrechoCandidato(
                        texto="Informe o setor.",
                        inicio=0,
                        fim=17,
                    )
                ],
            )
        ]

        contexto = ia.preparar_contexto(
            documentos
        )

        self.assertIsInstance(
            contexto,
            str,
        )

        self.assertIn(
            "[F1]",
            contexto,
        )

        self.assertIn(
            "Informe o setor.",
            contexto,
        )

    def test_respeita_limite_de_documentos(self):
        documentos = [
            (
                Path(
                    f"doc_{numero}.txt"
                ),
                f"Trecho {numero}.",
                [
                    TrechoCandidato(
                        texto=f"Trecho {numero}.",
                        inicio=0,
                        fim=len(
                            f"Trecho {numero}."
                        ),
                    )
                ],
            )
            for numero in range(
                ia.MAX_DOCUMENTOS + 1
            )
        ]

        pacote = ia.preparar_pacote(
            documentos
        )

        self.assertEqual(
            len(
                pacote.documentos_recuperados
            ),
            ia.MAX_DOCUMENTOS,
        )

        self.assertNotIn(
            f"doc_{ia.MAX_DOCUMENTOS}.txt",
            pacote.documentos_recuperados,
        )

    def test_rejeita_contexto_vazio(self):
        casos = [
            [],
            [
                (
                    Path("vazio.txt"),
                    "Texto sem trechos.",
                    [],
                )
            ],
        ]

        for documentos in casos:
            with self.subTest(
                documentos=documentos
            ):
                with self.assertRaises(
                    ValueError
                ):
                    ia.preparar_pacote(
                        documentos
                    )

    def test_rejeita_contexto_muito_grande(self):
        texto = (
            "x"
            * (
                ia.MAX_CARACTERES
                + 1
            )
        )

        documentos = [
            (
                Path("grande.txt"),
                texto,
                [
                    TrechoCandidato(
                        texto=texto,
                        inicio=0,
                        fim=len(texto),
                    )
                ],
            )
        ]

        with self.assertRaises(
            ValueError
        ):
            ia.preparar_pacote(
                documentos
            )


class TestGerarResposta(unittest.TestCase):

    def setUp(self):
        substituicao = patch(
            "consulta_ia.genai.Client"
        )

        self.criar_cliente = (
            substituicao.start()
        )

        self.addCleanup(
            substituicao.stop
        )

        cliente = (
            self.criar_cliente
            .return_value
            .__enter__
            .return_value
        )

        self.chamada = (
            cliente.models.generate_content
        )

        self.pergunta = (
            "Como solicitar material?"
        )

        self.texto_documento = (
            "Para solicitar material, "
            "informe o setor."
        )

        self.pacote = ia.preparar_pacote(
            [
                (
                    Path("material.txt"),
                    self.texto_documento,
                    [
                        TrechoCandidato(
                            texto=self.texto_documento,
                            inicio=0,
                            fim=len(
                                self.texto_documento
                            ),
                        )
                    ],
                )
            ]
        )

        self.resposta_json = json.dumps(
            {
                "status": "respondida",
                "itens": [
                    {
                        "texto": (
                            "Informe o setor."
                        ),
                        "evidencias": [
                            {
                                "fonte_id": "F1",
                                "citacao": (
                                    "informe o setor."
                                ),
                            }
                        ],
                    }
                ],
            },
            ensure_ascii=False,
        )

        self.chamada.return_value = (
            SimpleNamespace(
                candidates=[
                    SimpleNamespace(
                        finish_reason=(
                            types.FinishReason.STOP
                        )
                    )
                ],
                text=self.resposta_json,
            )
        )

    def consultar(self):
        return ia.gerar_resposta(
            self.pergunta,
            self.pacote,
            "chave-ficticia-para-testes",
            "modelo-simulado",
        )

    def test_devolve_apresentacao_validada(self):
        resultado = self.consultar()

        self.assertIsInstance(
            resultado,
            ApresentacaoResposta,
        )

        self.assertEqual(
            resultado.status,
            "respondida",
        )

        self.assertEqual(
            len(
                resultado.fontes_citadas
            ),
            1,
        )

        self.assertEqual(
            resultado.fontes_citadas[
                0
            ].identificador,
            "F1",
        )

        self.assertIn(
            "[F1]",
            resultado.linhas_itens[0],
        )

    def test_prepara_pergunta_contexto_e_instrucoes(self):
        self.consultar()

        argumentos = (
            self.chamada.call_args.kwargs
        )

        dados = json.loads(
            argumentos["contents"]
        )

        self.assertEqual(
            dados,
            {
                "pergunta": (
                    self.pergunta
                ),
                "trechos": (
                    self.pacote.contexto
                ),
            },
        )

        self.assertEqual(
            argumentos["model"],
            "modelo-simulado",
        )

        config = argumentos[
            "config"
        ]

        self.assertEqual(
            config.system_instruction,
            ia.INSTRUCOES,
        )

        self.assertEqual(
            config.response_mime_type,
            "application/json",
        )

        self.assertIsNotNone(
            config.response_json_schema
        )

    def test_rejeita_contexto_sem_pacote(self):
        with self.assertRaises(
            ValueError
        ):
            ia.gerar_resposta(
                self.pergunta,
                self.pacote.contexto,
                "chave-ficticia",
                "modelo-simulado",
            )

        self.criar_cliente.assert_not_called()

    def test_rejeita_pergunta_vazia_sem_criar_cliente(self):
        with self.assertRaises(
            ValueError
        ):
            ia.gerar_resposta(
                "",
                self.pacote,
                "chave-ficticia",
                "modelo-simulado",
            )

        self.criar_cliente.assert_not_called()

    def test_rejeita_pacote_sem_registro(self):
        pacote_vazio = PacoteEnvio(
            contexto="Trecho fictício.",
            registro=(),
            documentos_recuperados=(
                "arquivo.txt",
            ),
        )

        with self.assertRaises(
            ValueError
        ):
            ia.gerar_resposta(
                self.pergunta,
                pacote_vazio,
                "chave-ficticia",
                "modelo-simulado",
            )

        self.criar_cliente.assert_not_called()

    def test_rejeita_resposta_sem_candidatos(self):
        self.chamada.return_value.candidates = []

        with self.assertRaises(
            ValueError
        ):
            self.consultar()

    def test_rejeita_resposta_sem_texto(self):
        for texto in (
            "",
            "   ",
            None,
        ):
            with self.subTest(
                texto=texto
            ):
                self.chamada.return_value = (
                    SimpleNamespace(
                        candidates=[
                            SimpleNamespace(
                                finish_reason=(
                                    types
                                    .FinishReason
                                    .STOP
                                )
                            )
                        ],
                        text=texto,
                    )
                )

                with self.assertRaises(
                    ValueError
                ):
                    self.consultar()

    def test_rejeita_resposta_interrompida(self):
        self.chamada.return_value = (
            SimpleNamespace(
                candidates=[
                    SimpleNamespace(
                        finish_reason=(
                            types
                            .FinishReason
                            .MAX_TOKENS
                        )
                    )
                ],
                text=(
                    self.resposta_json
                ),
            )
        )

        with self.assertRaises(
            ValueError
        ):
            self.consultar()

    def test_rejeita_json_invalido(self):
        self.chamada.return_value.text = (
            '{"status":"respondida"'
        )

        with self.assertRaises(
            ValueError
        ):
            self.consultar()

    def test_rejeita_fonte_inexistente(self):
        self.chamada.return_value.text = (
            json.dumps(
                {
                    "status": (
                        "respondida"
                    ),
                    "itens": [
                        {
                            "texto": (
                                "Informe o setor."
                            ),
                            "evidencias": [
                                {
                                    "fonte_id": (
                                        "F99"
                                    ),
                                    "citacao": (
                                        "informe o setor."
                                    ),
                                }
                            ],
                        }
                    ],
                },
                ensure_ascii=False,
            )
        )

        with self.assertRaises(
            ValueError
        ):
            self.consultar()

    def test_rejeita_citacao_inventada(self):
        self.chamada.return_value.text = (
            json.dumps(
                {
                    "status": (
                        "respondida"
                    ),
                    "itens": [
                        {
                            "texto": (
                                "O prazo é de 10 dias."
                            ),
                            "evidencias": [
                                {
                                    "fonte_id": "F1",
                                    "citacao": (
                                        "O prazo é de "
                                        "10 dias."
                                    ),
                                }
                            ],
                        }
                    ],
                },
                ensure_ascii=False,
            )
        )

        with self.assertRaises(
            ValueError
        ):
            self.consultar()

    def test_sem_evidencia_nao_apresenta_texto_do_modelo(self):
        self.chamada.return_value.text = (
            json.dumps(
                {
                    "status": (
                        "sem_evidencia"
                    ),
                    "itens": [],
                },
                ensure_ascii=False,
            )
        )

        resultado = self.consultar()

        self.assertEqual(
            resultado.status,
            "sem_evidencia",
        )

        self.assertEqual(
            resultado.fontes_citadas,
            [],
        )

        self.assertEqual(
            resultado.linhas_itens,
            [],
        )

        self.assertEqual(
            resultado.mensagem_principal,
            (
                "Não encontrei essa informação "
                "nos trechos consultados."
            ),
        )

    def test_repassa_erro_de_conexao(self):
        self.chamada.side_effect = (
            httpx.ConnectError(
                "Falha simulada."
            )
        )

        with self.assertRaises(
            httpx.ConnectError
        ):
            self.consultar()

    def test_repassa_erro_de_cota(self):
        self.chamada.side_effect = (
            errors.ClientError(
                code=429,
                response_json={
                    "error": {
                        "code": 429,
                        "status": (
                            "RESOURCE_EXHAUSTED"
                        ),
                        "message": (
                            "Cota simulada "
                            "atingida."
                        ),
                    }
                },
            )
        )

        with self.assertRaises(
            errors.APIError
        ) as capturado:
            self.consultar()

        self.assertEqual(
            capturado.exception.code,
            429,
        )


if __name__ == "__main__":
    unittest.main()