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
    TrechoCandidato,
)


BASE = Path(__file__).resolve().parent

PERGUNTA = "Como solicitar material?"

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

TRECHO_MATERIAL = (
    "Para solicitar material, "
    "informe o setor e a quantidade."
)

RESULTADO_ALTERNATIVO = [
    (
        Path("material.txt"),
        TRECHO_MATERIAL,
        [
            TrechoCandidato(
                texto=TRECHO_MATERIAL,
                inicio=0,
                fim=len(TRECHO_MATERIAL),
                indice_recorte=1,
            )
        ],
    )
]

RESPOSTA_VALIDADA = ApresentacaoResposta(
    status="respondida",
    mensagem_principal="",
    linhas_itens=[
        "Informe o setor e a quantidade. [F1]"
    ],
    fontes_citadas=[
        FonteApresentada(
            identificador="F1",
            documento="material.txt",
            localizacao="Sem paginação neste formato.",
            trecho=TRECHO_MATERIAL,
            citacoes=[
                "informe o setor e a quantidade."
            ],
            texto_extraido=False,
        )
    ],
    nao_citados=[],
)


class TestInterface(unittest.TestCase):

    def aplicar_patch(self, substituicao):
        objeto = substituicao.start()
        self.addCleanup(substituicao.stop)
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
                "dotenv.dotenv_values",
                return_value={},
            )
        )

        self.aplicar_patch(
            patch.dict(
                os.environ,
                {
                    "GEMINI_API_KEY": "chave-ficticia",
                    "GEMINI_MODEL": "modelo-simulado",
                },
            )
        )

        self.gerar_ia = self.aplicar_patch(
            patch(
                "consulta_ia.gerar_resposta",
                return_value=RESPOSTA_VALIDADA,
            )
        )

        cliente_real = self.aplicar_patch(
            patch(
                "consulta_ia.genai.Client",
                side_effect=AssertionError(
                    "O teste não deve criar um cliente real do Gemini."
                ),
            )
        )

        self.addCleanup(
            cliente_real.assert_not_called
        )

        self.tela = AppTest.from_file(
            str(BASE / "interface.py"),
            default_timeout=15,
        )

        self.executar()

    def executar(self):
        self.tela.run()

        erros = [
            str(item.value)
            for item in self.tela.exception
        ]

        self.assertEqual(
            erros,
            [],
            f"Erro na interface: {erros}",
        )

    def botao(self, rotulo):
        for item in self.tela.button:
            if item.label == rotulo:
                return item

        self.fail(
            f"Botão não encontrado: {rotulo}"
        )

    def selecionar_modo(self, modo):
        self.tela.selectbox(
            key="modo_busca_individual"
        ).set_value(modo)

        self.executar()

    def pesquisar(
        self,
        pergunta=PERGUNTA,
        modo=None,
    ):
        if modo is not None:
            self.selecionar_modo(modo)

        self.tela.text_input[0].set_value(
            pergunta
        )

        self.botao(
            "Pesquisar"
        ).click()

        self.executar()

    def autorizar(self):
        self.tela.checkbox(
            key="autorizar_envio"
        ).check()

        self.executar()

    def gerar_resposta_na_tela(
        self,
        modo=None,
    ):
        self.pesquisar(
            modo=modo
        )

        self.autorizar()

        self.botao(
            "Gerar resposta com IA"
        ).click()

        self.executar()

    def textos_exibidos(self):
        return [
            item.value
            for item in self.tela.text
        ]

    def captions_exibidos(self):
        return [
            item.value
            for item in self.tela.caption
        ]

    def test_oferece_tres_modos_de_busca(self):
        opcoes = self.tela.selectbox(
            key="modo_busca_individual"
        ).options

        self.assertEqual(
            list(opcoes),
            [
                "Por palavras",
                "Por significado (local)",
                "Híbrida (palavras + significado)",
            ],
        )

    def test_modo_padrao_e_busca_por_palavras(self):
        self.assertEqual(
            self.tela.selectbox(
                key="modo_busca_individual"
            ).value,
            "Por palavras",
        )

    def test_busca_por_palavras_funciona(self):
        self.pesquisar()

        consulta = self.tela.session_state[
            "pesquisa_salva"
        ]

        self.assertEqual(
            consulta["modo_busca"],
            "Por palavras",
        )

        self.assertTrue(
            consulta["resultados"]
        )

    def test_busca_semantica_funciona_com_resultado_simulado(self):
        with patch(
            "busca_semantica.buscar_semantico",
            return_value=RESULTADO_ALTERNATIVO,
        ):
            self.pesquisar(
                modo="Por significado (local)"
            )

        consulta = self.tela.session_state[
            "pesquisa_salva"
        ]

        self.assertEqual(
            consulta["modo_busca"],
            "Por significado (local)",
        )

        self.assertTrue(
            consulta["resultados"]
        )

    def test_busca_hibrida_funciona_com_resultado_simulado(self):
        with patch(
            "busca_hibrida.buscar_hibrido",
            return_value=RESULTADO_ALTERNATIVO,
        ):
            self.pesquisar(
                modo="Híbrida (palavras + significado)"
            )

        consulta = self.tela.session_state[
            "pesquisa_salva"
        ]

        self.assertEqual(
            consulta["modo_busca"],
            "Híbrida (palavras + significado)",
        )

        self.assertTrue(
            consulta["resultados"]
        )

    def test_busca_hibrida_exibe_aviso(self):
        self.selecionar_modo(
            "Híbrida (palavras + significado)"
        )

        self.assertTrue(
            any(
                "busca híbrida"
                in item.value.casefold()
                for item in self.tela.info
            )
        )

        self.assertTrue(
            any(
                "probabilidade de acerto"
                in item.value.casefold()
                for item in self.tela.caption
            )
        )

    def test_pesquisar_nao_envia_e_exige_autorizacao(self):
        self.pesquisar()

        self.gerar_ia.assert_not_called()

        self.assertTrue(
            self.botao(
                "Gerar resposta com IA"
            ).disabled
        )

        self.assertIn(
            "Fonte: material.txt",
            [
                item.value
                for item in self.tela.subheader
            ],
        )

    def test_busca_exibe_texto_do_trecho(self):
        self.pesquisar()

        self.assertTrue(
            any(
                "Para solicitar material"
                in texto
                for texto in self.textos_exibidos()
            )
        )

    def test_pesquisa_salva_modo_utilizado(self):
        self.pesquisar()

        consulta = self.tela.session_state[
            "pesquisa_salva"
        ]

        self.assertEqual(
            consulta["modo_busca"],
            "Por palavras",
        )

    def test_marcar_autorizacao_nao_envia_sozinho(self):
        self.pesquisar()
        self.autorizar()

        self.gerar_ia.assert_not_called()

        self.assertFalse(
            self.botao(
                "Gerar resposta com IA"
            ).disabled
        )

    def test_gerar_envia_pergunta_e_pacote(self):
        self.gerar_resposta_na_tela()

        self.gerar_ia.assert_called_once()

        pergunta, pacote, chave, modelo = (
            self.gerar_ia.call_args.args
        )

        self.assertEqual(
            pergunta,
            PERGUNTA,
        )

        self.assertIn(
            "[F1]",
            pacote.contexto,
        )

        self.assertTrue(
            pacote.registro
        )

        self.assertEqual(
            pacote.registro[0].documento,
            "material.txt",
        )

        self.assertEqual(
            chave,
            "chave-ficticia",
        )

        self.assertEqual(
            modelo,
            "modelo-simulado",
        )

    def test_gerar_com_busca_hibrida_preserva_validacao(self):
        with patch(
            "busca_hibrida.buscar_hibrido",
            return_value=RESULTADO_ALTERNATIVO,
        ):
            self.gerar_resposta_na_tela(
                modo="Híbrida (palavras + significado)"
            )

        self.gerar_ia.assert_called_once()

        pacote = self.gerar_ia.call_args.args[1]

        self.assertTrue(
            pacote.registro
        )

        self.assertEqual(
            pacote.registro[0].identificador,
            "F1",
        )

    def test_gerar_mostra_resposta_validada(self):
        self.gerar_resposta_na_tela()

        self.assertIn(
            "Informe o setor e a quantidade. [F1]",
            self.textos_exibidos(),
        )

    def test_interface_exibe_fonte_citada(self):
        self.gerar_resposta_na_tela()

        textos = self.textos_exibidos()

        self.assertTrue(
            any(
                "F1" in texto
                and "material.txt" in texto
                for texto in textos
            )
        )

    def test_interface_exibe_trecho_e_passagem_citada(self):
        self.gerar_resposta_na_tela()

        textos = self.textos_exibidos()

        self.assertTrue(
            any(
                "Para solicitar material"
                in texto
                for texto in textos
            )
        )

        self.assertTrue(
            any(
                "informe o setor e a quantidade."
                in texto
                for texto in textos
            )
        )

    def test_interface_exibe_aviso_de_conferencia(self):
        self.gerar_resposta_na_tela()

        self.assertTrue(
            any(
                "Referências conferidas"
                in item
                for item in self.captions_exibidos()
            )
        )

    def test_resposta_e_salva_com_fontes_no_historico_da_sessao(self):
        self.gerar_resposta_na_tela()

        salvo = self.tela.session_state[
            "resposta_ia"
        ]

        self.assertIsInstance(
            salvo,
            dict,
        )

        self.assertEqual(
            salvo["status"],
            "respondida",
        )

        self.assertEqual(
            salvo["fontes_citadas"][0]["identificador"],
            "F1",
        )

        self.assertEqual(
            salvo["fontes_citadas"][0]["trecho"],
            TRECHO_MATERIAL,
        )

    def test_reexecucao_preserva_resposta_sem_novo_envio(self):
        self.gerar_resposta_na_tela()

        self.executar()

        self.gerar_ia.assert_called_once()

        self.assertIn(
            "Informe o setor e a quantidade. [F1]",
            self.textos_exibidos(),
        )

        self.assertTrue(
            self.botao(
                "Gerar resposta com IA"
            ).disabled
        )

    def test_nova_pesquisa_limpa_resposta_e_autorizacao(self):
        self.gerar_resposta_na_tela()

        self.pesquisar(
            "Como ajustar ponto?"
        )

        self.assertIsNone(
            self.tela.session_state[
                "resposta_ia"
            ]
        )

        self.assertNotIn(
            "Informe o setor e a quantidade. [F1]",
            self.textos_exibidos(),
        )

        self.assertFalse(
            self.tela.checkbox(
                key="autorizar_envio"
            ).value
        )

        self.assertTrue(
            self.botao(
                "Gerar resposta com IA"
            ).disabled
        )

        self.gerar_ia.assert_called_once()

    def test_sem_correspondencia_nao_oferece_geracao(self):
        self.pesquisar(
            "astronomia"
        )

        self.gerar_ia.assert_not_called()

        self.assertNotIn(
            "Gerar resposta com IA",
            [
                item.label
                for item in self.tela.button
            ],
        )

        self.assertTrue(
            any(
                "Não encontrei documentos"
                in item.value
                for item in self.tela.info
            )
        )

    def test_pergunta_vazia_mostra_aviso(self):
        self.pesquisar(
            ""
        )

        self.gerar_ia.assert_not_called()

        self.assertTrue(
            any(
                "Digite uma pergunta"
                in item.value
                for item in self.tela.warning
            )
        )

    def test_sem_chave_mantem_busca_mas_impede_ia(self):
        os.environ[
            "GEMINI_API_KEY"
        ] = ""

        self.pesquisar()

        self.gerar_ia.assert_not_called()

        self.assertIn(
            "Fonte: material.txt",
            [
                item.value
                for item in self.tela.subheader
            ],
        )

        self.assertTrue(
            any(
                "GEMINI_API_KEY"
                in item.value
                for item in self.tela.warning
            )
        )

        self.assertNotIn(
            "Gerar resposta com IA",
            [
                item.label
                for item in self.tela.button
            ],
        )

    def test_falha_de_conexao_mostra_erro_sem_resposta(self):
        self.gerar_ia.side_effect = (
            httpx.ConnectError(
                "Falha simulada."
            )
        )

        self.gerar_resposta_na_tela()

        self.assertIsNone(
            self.tela.session_state[
                "resposta_ia"
            ]
        )

        self.assertTrue(
            any(
                "Falha de conexão"
                in item.value
                for item in self.tela.error
            )
        )

    def test_cota_esgotada_mostra_erro_sem_resposta(self):
        self.gerar_ia.side_effect = (
            errors.ClientError(
                code=429,
                response_json={
                    "error": {
                        "code": 429,
                        "status": "RESOURCE_EXHAUSTED",
                        "message": "Cota simulada atingida.",
                    }
                },
            )
        )

        self.gerar_resposta_na_tela()

        self.assertIsNone(
            self.tela.session_state[
                "resposta_ia"
            ]
        )

        self.assertTrue(
            any(
                "Cota atingida"
                in item.value
                for item in self.tela.error
            )
        )

    def test_resposta_invalida_nao_e_salva(self):
        self.gerar_ia.side_effect = (
            ValueError(
                "A resposta da IA não passou "
                "na conferência das referências. "
                "Nenhum texto gerado foi apresentado."
            )
        )

        self.gerar_resposta_na_tela()

        self.assertIsNone(
            self.tela.session_state[
                "resposta_ia"
            ]
        )

        self.assertTrue(
            any(
                "não passou na conferência"
                in item.value
                for item in self.tela.error
            )
        )

    def test_aviso_final_limita_busca_hibrida(self):
        with patch(
            "busca_hibrida.buscar_hibrido",
            return_value=RESULTADO_ALTERNATIVO,
        ):
            self.pesquisar(
                modo="Híbrida (palavras + significado)"
            )

        captions = [
            item.casefold()
            for item in self.captions_exibidos()
        ]

        self.assertTrue(
            any(
                "busca híbrida" in item
                and "probabilidade de acerto" in item
                for item in captions
            )
        )


if __name__ == "__main__":
    unittest.main()