import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import httpx
from google.genai import errors

import avaliar_gemini as ag
from avaliacao import CasoAvaliacao
from citacoes import (
    ApresentacaoResposta,
    FonteApresentada,
    TrechoCandidato,
)


class TestAvaliarGemini(
    unittest.TestCase
):

    def setUp(self):
        self.caso = CasoAvaliacao(
            identificador="teste_001",
            pergunta="Como solicitar material?",
            documentos_esperados=(
                "material.txt",
            ),
            termos_obrigatorios=(
                "setor",
                "quantidade",
            ),
            termos_proibidos=(
                "10 dias",
            ),
            status_esperado="respondida",
        )

        self.texto = (
            "Para solicitar material, "
            "informe o setor e a quantidade."
        )

        self.documentos = [
            (
                Path("material.txt"),
                self.texto,
            )
        ]

        self.resultados_busca = [
            (
                Path("material.txt"),
                self.texto,
                [
                    TrechoCandidato(
                        texto=self.texto,
                        inicio=0,
                        fim=len(
                            self.texto
                        ),
                    )
                ],
            )
        ]

        self.apresentacao = (
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
                        documento=(
                            "material.txt"
                        ),
                        localizacao=(
                            "Sem paginação neste formato."
                        ),
                        trecho=self.texto,
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

    def busca_ok(
        self,
        documentos,
        pergunta,
    ):
        return (
            self.resultados_busca
        )

    def test_nomes_documentos_preserva_ordem(self):
        nomes = ag.nomes_documentos(
            self.resultados_busca
        )

        self.assertEqual(
            nomes,
            (
                "material.txt",
            ),
        )

    def test_texto_da_apresentacao_usa_itens(self):
        texto = (
            ag.texto_da_apresentacao(
                self.apresentacao
            )
        )

        self.assertIn(
            "setor",
            texto,
        )

        self.assertIn(
            "[F1]",
            texto,
        )

    def test_documentos_citados(self):
        resultado = (
            ag.documentos_citados(
                self.apresentacao
            )
        )

        self.assertEqual(
            resultado,
            (
                "material.txt",
            ),
        )

    def test_executar_caso_aprovado(self):
        with patch.object(
            ag,
            "gerar_resposta",
            return_value=(
                self.apresentacao
            ),
        ) as gerar:
            resultado, registro = (
                ag.executar_caso(
                    self.caso,
                    modo="teste",
                    funcao_busca=(
                        self.busca_ok
                    ),
                    chave="chave-ficticia",
                    modelo="modelo-ficticio",
                    documentos=(
                        self.documentos
                    ),
                )
            )

        gerar.assert_called_once()

        self.assertIsNotNone(
            resultado
        )

        self.assertTrue(
            resultado.aprovado
        )

        self.assertTrue(
            registro.aprovado
        )

        self.assertEqual(
            registro.tipo_resultado,
            "qualidade",
        )

        self.assertIsNone(
            registro.erro
        )

    def test_sem_resultado_e_falha_de_qualidade(self):
        with patch.object(
            ag,
            "gerar_resposta",
        ) as gerar:
            resultado, registro = (
                ag.executar_caso(
                    self.caso,
                    modo="teste",
                    funcao_busca=(
                        lambda documentos, pergunta: []
                    ),
                    chave="chave",
                    modelo="modelo",
                    documentos=(
                        self.documentos
                    ),
                )
            )

        gerar.assert_not_called()

        self.assertIsNotNone(
            resultado
        )

        self.assertFalse(
            resultado.aprovado
        )

        self.assertFalse(
            registro.aprovado
        )

        self.assertEqual(
            registro.tipo_resultado,
            "qualidade",
        )

    def test_resposta_invalida_e_falha_de_qualidade(self):
        with patch.object(
            ag,
            "gerar_resposta",
            side_effect=ValueError(
                "Resposta inválida."
            ),
        ):
            resultado, registro = (
                ag.executar_caso(
                    self.caso,
                    modo="teste",
                    funcao_busca=(
                        self.busca_ok
                    ),
                    chave="chave",
                    modelo="modelo",
                    documentos=(
                        self.documentos
                    ),
                )
            )

        self.assertIsNotNone(
            resultado
        )

        self.assertFalse(
            resultado.aprovado
        )

        self.assertEqual(
            registro.tipo_resultado,
            "qualidade",
        )

        self.assertIn(
            "Resposta reprovada",
            registro.erro,
        )

    def test_erro_429_e_falha_operacional(self):
        erro_api = errors.ClientError(
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

        with patch.object(
            ag,
            "gerar_resposta",
            side_effect=erro_api,
        ):
            resultado, registro = (
                ag.executar_caso(
                    self.caso,
                    modo="teste",
                    funcao_busca=(
                        self.busca_ok
                    ),
                    chave="chave",
                    modelo="modelo",
                    documentos=(
                        self.documentos
                    ),
                )
            )

        self.assertIsNone(
            resultado
        )

        self.assertIsNone(
            registro.aprovado
        )

        self.assertEqual(
            registro.tipo_resultado,
            "operacional",
        )

        self.assertIn(
            "429",
            registro.erro,
        )

    def test_erro_de_conexao_e_falha_operacional(self):
        with patch.object(
            ag,
            "gerar_resposta",
            side_effect=httpx.ConnectError(
                "Falha simulada."
            ),
        ):
            resultado, registro = (
                ag.executar_caso(
                    self.caso,
                    modo="teste",
                    funcao_busca=(
                        self.busca_ok
                    ),
                    chave="chave",
                    modelo="modelo",
                    documentos=(
                        self.documentos
                    ),
                )
            )

        self.assertIsNone(
            resultado
        )

        self.assertEqual(
            registro.tipo_resultado,
            "operacional",
        )

        self.assertIn(
            "Falha de conexão",
            registro.erro,
        )

    def test_erro_na_busca_e_falha_operacional(self):
        def busca_com_erro(
            documentos,
            pergunta,
        ):
            raise RuntimeError(
                "Falha simulada."
            )

        resultado, registro = (
            ag.executar_caso(
                self.caso,
                modo="teste",
                funcao_busca=(
                    busca_com_erro
                ),
                chave="chave",
                modelo="modelo",
                documentos=(
                    self.documentos
                ),
            )
        )

        self.assertIsNone(
            resultado
        )

        self.assertEqual(
            registro.tipo_resultado,
            "operacional",
        )

    def test_executar_modo_resume_casos_avaliados(self):
        with patch.object(
            ag,
            "gerar_resposta",
            return_value=(
                self.apresentacao
            ),
        ):
            resultado = ag.executar_modo(
                "teste",
                self.busca_ok,
                chave="chave",
                modelo="modelo",
                casos=[
                    self.caso
                ],
                documentos=(
                    self.documentos
                ),
            )

        self.assertEqual(
            resultado.modo,
            "teste",
        )

        self.assertEqual(
            resultado.total_planejado,
            1,
        )

        self.assertEqual(
            resultado.avaliados,
            1,
        )

        self.assertEqual(
            resultado.falhas_operacionais,
            0,
        )

        self.assertIsNotNone(
            resultado.resumo
        )

        self.assertEqual(
            resultado.resumo.total,
            1,
        )

        self.assertEqual(
            resultado.resumo.aprovados,
            1,
        )

    def test_falha_operacional_nao_reduz_taxa_qualidade(self):
        casos = [
            self.caso,
            CasoAvaliacao(
                identificador="teste_002",
                pergunta="Outra pergunta.",
                documentos_esperados=(
                    "material.txt",
                ),
                termos_obrigatorios=(
                    "setor",
                ),
                status_esperado="respondida",
            ),
        ]

        chamadas = {
            "numero": 0
        }

        def gerar(
            *args,
            **kwargs,
        ):
            chamadas[
                "numero"
            ] += 1

            if (
                chamadas[
                    "numero"
                ]
                == 2
            ):
                raise errors.ClientError(
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

            return (
                self.apresentacao
            )

        with patch.object(
            ag,
            "gerar_resposta",
            side_effect=gerar,
        ):
            resultado = ag.executar_modo(
                "teste",
                self.busca_ok,
                chave="chave",
                modelo="modelo",
                casos=casos,
                documentos=(
                    self.documentos
                ),
            )

        self.assertEqual(
            resultado.total_planejado,
            2,
        )

        self.assertEqual(
            resultado.avaliados,
            1,
        )

        self.assertEqual(
            resultado.falhas_operacionais,
            1,
        )

        self.assertIsNotNone(
            resultado.resumo
        )

        self.assertEqual(
            resultado.resumo.total,
            1,
        )

        self.assertEqual(
            resultado.resumo.aprovados,
            1,
        )

        self.assertEqual(
            resultado.resumo.taxa_aprovacao,
            1.0,
        )

    def test_todos_operacionais_deixam_resumo_none(self):
        erro_api = errors.ClientError(
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

        with patch.object(
            ag,
            "gerar_resposta",
            side_effect=erro_api,
        ):
            resultado = ag.executar_modo(
                "teste",
                self.busca_ok,
                chave="chave",
                modelo="modelo",
                casos=[
                    self.caso
                ],
                documentos=(
                    self.documentos
                ),
            )

        self.assertEqual(
            resultado.avaliados,
            0,
        )

        self.assertEqual(
            resultado.falhas_operacionais,
            1,
        )

        self.assertIsNone(
            resultado.resumo
        )

    def test_selecionar_modo_individual(self):
        modos = ag.selecionar_modos(
            "palavras"
        )

        self.assertEqual(
            list(
                modos.keys()
            ),
            [
                "palavras"
            ],
        )

    def test_selecionar_todos(self):
        modos = ag.selecionar_modos(
            "todos"
        )

        self.assertEqual(
            set(
                modos.keys()
            ),
            {
                "palavras",
                "semantica",
                "hibrida",
            },
        )

    def test_limitar_casos(self):
        casos = ag.limitar_casos(
            2
        )

        self.assertEqual(
            len(
                casos
            ),
            2,
        )

    def test_limite_invalido(self):
        with self.assertRaises(
            ValueError
        ):
            ag.limitar_casos(
                0
            )

    def test_valor_ou_na(self):
        self.assertEqual(
            ag.valor_ou_na(
                None
            ),
            "N/A",
        )

        self.assertEqual(
            ag.valor_ou_na(
                0.5
            ),
            "0.500",
        )

        self.assertEqual(
            ag.valor_ou_na(
                0.5,
                percentual_valor=True,
            ),
            "50.0%",
        )

    def test_salvar_resultados_nao_grava_chave(self):
        with patch.object(
            ag,
            "gerar_resposta",
            return_value=(
                self.apresentacao
            ),
        ):
            resultado = ag.executar_modo(
                "teste",
                self.busca_ok,
                chave="SEGREDO_NAO_GRAVAR",
                modelo="modelo-ficticio",
                casos=[
                    self.caso
                ],
                documentos=(
                    self.documentos
                ),
            )

        with TemporaryDirectory() as pasta:
            with patch.object(
                ag,
                "PASTA_RESULTADOS",
                Path(
                    pasta
                ),
            ):
                caminho = (
                    ag.salvar_resultados(
                        (
                            resultado,
                        ),
                        modelo=(
                            "modelo-ficticio"
                        ),
                    )
                )

                conteudo = (
                    caminho.read_text(
                        encoding="utf-8"
                    )
                )

        self.assertNotIn(
            "SEGREDO_NAO_GRAVAR",
            conteudo,
        )

        self.assertIn(
            "modelo-ficticio",
            conteudo,
        )

    def test_percentual(self):
        self.assertEqual(
            ag.percentual(
                0.875
            ),
            "87.5%",
        )


if __name__ == "__main__":
    unittest.main()