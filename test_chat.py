import os
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx
from google.genai import errors
from streamlit.testing.v1 import AppTest

from citacoes import (
    ApresentacaoResposta,
    FonteApresentada,
)


BASE = Path(__file__).resolve().parent


DOCUMENTOS = [
    (
        Path("material.txt"),
        (
            "Para solicitar material, "
            "informe o setor e a quantidade."
        ),
    ),
    (
        Path("ponto.txt"),
        (
            "Para ajustar ponto, "
            "informe a data ao RH."
        ),
    ),
]


RESPOSTA_VALIDADA = (
    ApresentacaoResposta(
        status="respondida",
        mensagem_principal="",
        linhas_itens=[
            (
                "Informe o setor e "
                "a quantidade. [F1]"
            )
        ],
        fontes_citadas=[
            FonteApresentada(
                identificador="F1",
                documento="material.txt",
                localizacao=(
                    "Sem paginação neste formato."
                ),
                trecho=(
                    "Para solicitar material, "
                    "informe o setor e a quantidade."
                ),
                citacoes=[
                    (
                        "informe o setor "
                        "e a quantidade."
                    )
                ],
                texto_extraido=False,
            )
        ],
        nao_citados=[],
    )
)


class TestChat(unittest.TestCase):

    def aplicar_patch(
        self,
        substituicao,
    ):
        objeto = (
            substituicao.start()
        )

        self.addCleanup(
            substituicao.stop
        )

        return objeto

    def setUp(self):
        self.aplicar_patch(
            patch(
                "app.carregar_documentos",
                return_value=DOCUMENTOS,
            )
        )

        self.aplicar_patch(
            patch(
                "painel_documentos.mostrar_importacao",
                return_value=False,
            )
        )

        self.aplicar_patch(
            patch(
                "dotenv.dotenv_values",
                return_value={},
            )
        )

        self.aplicar_patch(
            patch.dict(
                os.environ,
                {
                    "GEMINI_API_KEY": (
                        "chave-ficticia"
                    ),
                    "GEMINI_MODEL": (
                        "modelo-simulado"
                    ),
                },
            )
        )

        self.gerar_ia = (
            self.aplicar_patch(
                patch(
                    "consulta_ia.gerar_resposta",
                    return_value=(
                        RESPOSTA_VALIDADA
                    ),
                )
            )
        )

        cliente = self.aplicar_patch(
            patch(
                "consulta_ia.genai.Client",
                side_effect=(
                    AssertionError(
                        "O teste não deve acessar "
                        "o Gemini real."
                    )
                ),
            )
        )

        self.addCleanup(
            cliente.assert_not_called
        )

        self.tela = (
            AppTest.from_file(
                str(
                    BASE
                    / "chat.py"
                ),
                default_timeout=15,
            )
        )

        self.executar()

    def executar(self):
        self.tela.run()

        erros = [
            str(item.value)
            for item
            in self.tela.exception
        ]

        self.assertEqual(
            erros,
            [],
            (
                "Erro na interface do chat: "
                f"{erros}"
            ),
        )

    def botao(
        self,
        rotulo,
    ):
        for item in self.tela.button:
            if item.label == rotulo:
                return item

        self.fail(
            "Botão não encontrado: "
            f"{rotulo}"
        )

    def enviar_pergunta(
        self,
        texto=(
            "Como solicitar material?"
        ),
    ):
        self.tela.chat_input[
            0
        ].set_value(
            texto
        )

        self.executar()

    def autorizar(self):
        self.tela.checkbox(
            key="chat_autoriza_widget"
        ).check()

        self.executar()

    def gerar(self):
        self.botao(
            "Gerar resposta com IA"
        ).click()

        self.executar()

    def concluir_primeiro_turno(self):
        self.enviar_pergunta()
        self.autorizar()
        self.gerar()

    def textos(self):
        return [
            item.value
            for item
            in self.tela.text
        ]

    def captions(self):
        return [
            item.value
            for item
            in self.tela.caption
        ]

    def test_pergunta_nao_consulta_ia_antes_da_autorizacao(self):
        self.enviar_pergunta()

        self.gerar_ia.assert_not_called()

        pendente = (
            self.tela.session_state[
                "chat_pendente"
            ]
        )

        self.assertIsNotNone(
            pendente
        )

        self.assertEqual(
            pendente["pergunta"],
            "Como solicitar material?",
        )

        self.assertIn(
            "[F1]",
            pendente[
                "pacote"
            ].contexto,
        )

    def test_pergunta_pendente_preserva_registro_de_fontes(self):
        self.enviar_pergunta()

        pacote = (
            self.tela.session_state[
                "chat_pendente"
            ]["pacote"]
        )

        self.assertTrue(
            pacote.registro
        )

        self.assertEqual(
            pacote.registro[
                0
            ].identificador,
            "F1",
        )

        self.assertEqual(
            pacote.registro[
                0
            ].documento,
            "material.txt",
        )

    def test_marcar_checkbox_nao_envia_automaticamente(self):
        self.enviar_pergunta()

        self.autorizar()

        self.gerar_ia.assert_not_called()

        self.assertTrue(
            self.tela.session_state[
                "chat_autoriza"
            ]
        )

        self.assertFalse(
            self.botao(
                "Gerar resposta com IA"
            ).disabled
        )

    def test_gerar_usa_pacote_e_nao_contexto_solto(self):
        self.concluir_primeiro_turno()

        self.gerar_ia.assert_called_once()

        (
            pedido,
            pacote,
            chave,
            modelo,
        ) = self.gerar_ia.call_args.args

        self.assertIn(
            "pergunta_atual",
            pedido,
        )

        self.assertTrue(
            pacote.registro
        )

        self.assertIn(
            "[F1]",
            pacote.contexto,
        )

        self.assertEqual(
            chave,
            "chave-ficticia",
        )

        self.assertEqual(
            modelo,
            "modelo-simulado",
        )

    def test_resposta_validada_e_salva_no_historico(self):
        self.concluir_primeiro_turno()

        historico = (
            self.tela.session_state[
                "chat_historico"
            ]
        )

        self.assertEqual(
            len(historico),
            1,
        )

        turno = historico[0]

        self.assertEqual(
            turno["pergunta"],
            "Como solicitar material?",
        )

        self.assertIn(
            "resposta_validada",
            turno,
        )

        resposta = turno[
            "resposta_validada"
        ]

        self.assertEqual(
            resposta["status"],
            "respondida",
        )

        self.assertEqual(
            resposta[
                "fontes_citadas"
            ][0]["identificador"],
            "F1",
        )

    def test_historico_preserva_trecho_da_consulta(self):
        self.concluir_primeiro_turno()

        historico = (
            self.tela.session_state[
                "chat_historico"
            ]
        )

        fonte = (
            historico[0]
            ["resposta_validada"]
            ["fontes_citadas"][0]
        )

        self.assertEqual(
            fonte["trecho"],
            (
                "Para solicitar material, "
                "informe o setor e a quantidade."
            ),
        )

    def test_resposta_e_reexibida_sem_nova_consulta(self):
        self.concluir_primeiro_turno()

        self.executar()

        self.gerar_ia.assert_called_once()

        self.assertIn(
            (
                "Informe o setor e "
                "a quantidade. [F1]"
            ),
            self.textos(),
        )

    def test_fontes_sao_reexibidas_do_historico(self):
        self.concluir_primeiro_turno()

        textos = (
            self.textos()
        )

        self.assertTrue(
            any(
                (
                    "F1"
                    in texto
                    and "material.txt"
                    in texto
                )
                for texto
                in textos
            )
        )

    def test_contexto_enviado_tambem_fica_no_turno(self):
        self.concluir_primeiro_turno()

        turno = (
            self.tela.session_state[
                "chat_historico"
            ][0]
        )

        self.assertIn(
            "[F1]",
            turno["contexto"],
        )

        self.assertIn(
            "material.txt",
            turno["contexto"],
        )

    def test_resposta_invalida_nao_entra_no_historico(self):
        self.gerar_ia.side_effect = (
            ValueError(
                "A resposta da IA não passou "
                "na conferência das referências. "
                "Nenhum texto gerado foi apresentado."
            )
        )

        self.enviar_pergunta()
        self.autorizar()
        self.gerar()

        historico = (
            self.tela.session_state[
                "chat_historico"
            ]
        )

        self.assertEqual(
            historico,
            [],
        )

        self.assertIsNotNone(
            self.tela.session_state[
                "chat_pendente"
            ]
        )

        self.assertTrue(
            any(
                (
                    "não passou"
                    in item.value
                )
                for item
                in self.tela.error
            )
        )

    def test_erro_de_conexao_nao_registra_turno(self):
        self.gerar_ia.side_effect = (
            httpx.ConnectError(
                "Erro simulado."
            )
        )

        self.enviar_pergunta()
        self.autorizar()
        self.gerar()

        self.assertEqual(
            self.tela.session_state[
                "chat_historico"
            ],
            [],
        )

        self.assertTrue(
            any(
                (
                    "Falha de conexão"
                    in item.value
                )
                for item
                in self.tela.error
            )
        )

    def test_erro_de_cota_nao_registra_turno(self):
        self.gerar_ia.side_effect = (
            errors.ClientError(
                code=429,
                response_json={
                    "error": {
                        "code": 429,
                        "status": (
                            "RESOURCE_EXHAUSTED"
                        ),
                        "message": (
                            "Cota simulada."
                        ),
                    }
                },
            )
        )

        self.enviar_pergunta()
        self.autorizar()
        self.gerar()

        self.assertEqual(
            self.tela.session_state[
                "chat_historico"
            ],
            [],
        )

        self.assertTrue(
            any(
                (
                    "Cota atingida"
                    in item.value
                )
                for item
                in self.tela.error
            )
        )

    def test_cancelar_remove_pendente_sem_chamar_ia(self):
        self.enviar_pergunta()

        self.botao(
            "Cancelar pergunta"
        ).click()

        self.executar()

        self.assertIsNone(
            self.tela.session_state[
                "chat_pendente"
            ]
        )

        self.assertFalse(
            self.tela.session_state[
                "chat_autoriza"
            ]
        )

        self.assertFalse(
            self.tela.session_state[
                "chat_autoriza_widget"
            ]
        )

        self.gerar_ia.assert_not_called()

    def test_nova_conversa_limpa_historico(self):
        self.concluir_primeiro_turno()

        self.botao(
            "Nova conversa"
        ).click()

        self.executar()

        self.assertEqual(
            self.tela.session_state[
                "chat_historico"
            ],
            [],
        )

        self.assertIsNone(
            self.tela.session_state[
                "chat_pendente"
            ]
        )

        self.assertFalse(
            self.tela.session_state[
                "chat_autoriza"
            ]
        )

    def test_segunda_pergunta_usa_assunto_anterior_sem_reutilizar_resposta(self):
        self.concluir_primeiro_turno()

        self.enviar_pergunta(
            "E quais dados preciso informar?"
        )

        pendente = (
            self.tela.session_state[
                "chat_pendente"
            ]
        )

        pedido = (
            pendente["pedido"]
        )

        self.assertIn(
            "Como solicitar material?",
            pedido,
        )

        self.assertIn(
            "E quais dados preciso informar?",
            pedido,
        )

        self.assertNotIn(
            (
                "Informe o setor e "
                "a quantidade. [F1]"
            ),
            pedido,
        )

    def test_aviso_final_informa_limite_da_validacao(self):
        captions_normalizados = [
            item.casefold()
            for item
            in self.captions()
        ]

        self.assertTrue(
            any(
                (
                    "referências"
                    in item
                    and "interpretação"
                    in item
                )
                for item
                in captions_normalizados
            )
        )


if __name__ == "__main__":
    unittest.main()