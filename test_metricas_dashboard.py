import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import metricas_dashboard as md


def dados_avaliacao(
    *,
    modo="hibrida",
    avaliados=12,
    operacionais=0,
    aprovados=12,
    reprovados=0,
    taxa=1.0,
    precision=0.3333333333333333,
    recall=1.0,
    mrr=0.9,
):
    return {
        "executado_em_utc": (
            "2026-10-27T20:00:00+00:00"
        ),
        "modelo": (
            "gemini-ficticio"
        ),
        "resultados": [
            {
                "modo": modo,
                "total_planejado": (
                    avaliados
                    + operacionais
                ),
                "avaliados": avaliados,
                "falhas_operacionais": (
                    operacionais
                ),
                "resumo": (
                    None
                    if avaliados == 0
                    else {
                        "total": avaliados,
                        "aprovados": aprovados,
                        "reprovados": reprovados,
                        "taxa_aprovacao": taxa,
                        "precision_media": (
                            precision
                        ),
                        "recall_media": (
                            recall
                        ),
                        "mrr": mrr,
                        "taxa_citacoes_validas": (
                            1.0
                        ),
                        "taxa_conteudo_valido": (
                            taxa
                        ),
                        "taxa_status_valido": (
                            1.0
                        ),
                        "resultados": [],
                    }
                ),
                "execucoes": [],
            }
        ],
    }


def resultado_caso(
    identificador,
    *,
    aprovado=True,
    precision=1.0,
    recall=1.0,
    reciprocal_rank=1.0,
):
    return {
        "identificador": identificador,
        "documentos_encontrados": [
            "documento.txt"
        ],
        "documentos_esperados": [
            "documento.txt"
        ],
        "citacoes_encontradas": [
            "documento.txt"
        ],
        "termos_obrigatorios_encontrados": [],
        "termos_obrigatorios_ausentes": [],
        "termos_proibidos_encontrados": [],
        "status_obtido": (
            "respondida"
            if aprovado
            else None
        ),
        "status_esperado": (
            "respondida"
        ),
        "precision_documentos": (
            precision
        ),
        "recall_documentos": (
            recall
        ),
        "reciprocal_rank": (
            reciprocal_rank
        ),
        "citacoes_validas": aprovado,
        "conteudo_valido": aprovado,
        "status_valido": aprovado,
        "aprovado": aprovado,
    }


def dados_legados(
    *,
    com_erro_429=False,
):
    resultados = [
        resultado_caso(
            "caso_001"
        ),
        resultado_caso(
            "caso_002"
        ),
    ]

    execucoes = [
        {
            "caso_id": "caso_001",
            "modo": "hibrida",
            "pergunta": "Pergunta 1",
            "documentos_encontrados": [
                "documento.txt"
            ],
            "documentos_citados": [
                "documento.txt"
            ],
            "status": "respondida",
            "texto_resposta": "Resposta",
            "aprovado": True,
            "erro": None,
        },
        {
            "caso_id": "caso_002",
            "modo": "hibrida",
            "pergunta": "Pergunta 2",
            "documentos_encontrados": [
                "documento.txt"
            ],
            "documentos_citados": (
                []
                if com_erro_429
                else [
                    "documento.txt"
                ]
            ),
            "status": (
                None
                if com_erro_429
                else "respondida"
            ),
            "texto_resposta": (
                ""
                if com_erro_429
                else "Resposta"
            ),
            "aprovado": (
                False
                if com_erro_429
                else True
            ),
            "erro": (
                "Erro da API (429)."
                if com_erro_429
                else None
            ),
        },
    ]

    if com_erro_429:
        resultados[
            1
        ] = resultado_caso(
            "caso_002",
            aprovado=False,
            precision=1.0,
            recall=1.0,
            reciprocal_rank=1.0,
        )

    aprovados = (
        1
        if com_erro_429
        else 2
    )

    return {
        "executado_em_utc": (
            "2026-10-27T20:00:00+00:00"
        ),
        "modelo": (
            "gemini-legado"
        ),
        "resultados": [
            {
                "modo": "hibrida",
                "resumo": {
                    "total": 2,
                    "aprovados": aprovados,
                    "reprovados": (
                        2
                        - aprovados
                    ),
                    "taxa_aprovacao": (
                        aprovados
                        / 2
                    ),
                    "precision_media": 1.0,
                    "recall_media": 1.0,
                    "mrr": 1.0,
                    "taxa_citacoes_validas": (
                        aprovados
                        / 2
                    ),
                    "taxa_conteudo_valido": (
                        aprovados
                        / 2
                    ),
                    "taxa_status_valido": (
                        aprovados
                        / 2
                    ),
                    "resultados": resultados,
                },
                "execucoes": execucoes,
            }
        ],
    }


class TestMetricasDashboard(
    unittest.TestCase
):

    def criar_json(
        self,
        pasta,
        nome,
        dados,
    ):
        caminho = (
            Path(pasta)
            / nome
        )

        caminho.write_text(
            json.dumps(
                dados,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        return caminho

    def test_carrega_arquivo_valido(self):
        with TemporaryDirectory() as pasta:
            caminho = self.criar_json(
                pasta,
                "avaliacao_gemini_20261027T200000Z.json",
                dados_avaliacao(),
            )

            metricas = (
                md.carregar_arquivo_avaliacao(
                    caminho
                )
            )

        self.assertEqual(
            len(
                metricas
            ),
            1,
        )

        metrica = metricas[
            0
        ]

        self.assertEqual(
            metrica.modo,
            "hibrida",
        )

        self.assertEqual(
            metrica.total_planejado,
            12,
        )

        self.assertEqual(
            metrica.avaliados,
            12,
        )

        self.assertEqual(
            metrica.falhas_operacionais,
            0,
        )

        self.assertEqual(
            metrica.taxa_aprovacao,
            1.0,
        )

    def test_carrega_formato_legado(self):
        with TemporaryDirectory() as pasta:
            caminho = self.criar_json(
                pasta,
                "avaliacao_gemini_20261027T190000Z.json",
                dados_legados(),
            )

            metrica = (
                md.carregar_arquivo_avaliacao(
                    caminho
                )[0]
            )

        self.assertEqual(
            metrica.total_planejado,
            2,
        )

        self.assertEqual(
            metrica.avaliados,
            2,
        )

        self.assertEqual(
            metrica.falhas_operacionais,
            0,
        )

        self.assertEqual(
            metrica.aprovados,
            2,
        )

        self.assertEqual(
            metrica.taxa_aprovacao,
            1.0,
        )

    def test_legado_429_nao_reduz_qualidade(self):
        with TemporaryDirectory() as pasta:
            caminho = self.criar_json(
                pasta,
                "avaliacao_gemini_20261027T190000Z.json",
                dados_legados(
                    com_erro_429=True
                ),
            )

            metrica = (
                md.carregar_arquivo_avaliacao(
                    caminho
                )[0]
            )

        self.assertEqual(
            metrica.total_planejado,
            2,
        )

        self.assertEqual(
            metrica.avaliados,
            1,
        )

        self.assertEqual(
            metrica.falhas_operacionais,
            1,
        )

        self.assertEqual(
            metrica.aprovados,
            1,
        )

        self.assertEqual(
            metrica.reprovados,
            0,
        )

        self.assertEqual(
            metrica.taxa_aprovacao,
            1.0,
        )

        self.assertEqual(
            metrica.taxa_citacoes_validas,
            1.0,
        )

    def test_carrega_varios_modos_do_mesmo_arquivo(self):
        dados = dados_avaliacao()

        dados[
            "resultados"
        ].append(
            dados_avaliacao(
                modo="semantica"
            )[
                "resultados"
            ][0]
        )

        with TemporaryDirectory() as pasta:
            caminho = self.criar_json(
                pasta,
                "avaliacao_gemini_20261027T200000Z.json",
                dados,
            )

            metricas = (
                md.carregar_arquivo_avaliacao(
                    caminho
                )
            )

        self.assertEqual(
            {
                item.modo
                for item in metricas
            },
            {
                "hibrida",
                "semantica",
            },
        )

    def test_falha_operacional_e_preservada(self):
        dados = dados_avaliacao(
            avaliados=8,
            operacionais=4,
            aprovados=8,
            reprovados=0,
            taxa=1.0,
        )

        with TemporaryDirectory() as pasta:
            caminho = self.criar_json(
                pasta,
                "avaliacao_gemini_20261027T200000Z.json",
                dados,
            )

            metrica = (
                md.carregar_arquivo_avaliacao(
                    caminho
                )[0]
            )

        self.assertEqual(
            metrica.total_planejado,
            12,
        )

        self.assertEqual(
            metrica.avaliados,
            8,
        )

        self.assertEqual(
            metrica.falhas_operacionais,
            4,
        )

        self.assertEqual(
            metrica.taxa_aprovacao,
            1.0,
        )

    def test_todos_operacionais_permite_resumo_none(self):
        dados = dados_avaliacao(
            avaliados=0,
            operacionais=12,
            aprovados=0,
            reprovados=0,
            taxa=0,
        )

        with TemporaryDirectory() as pasta:
            caminho = self.criar_json(
                pasta,
                "avaliacao_gemini_20261027T200000Z.json",
                dados,
            )

            metrica = (
                md.carregar_arquivo_avaliacao(
                    caminho
                )[0]
            )

        self.assertEqual(
            metrica.avaliados,
            0,
        )

        self.assertEqual(
            metrica.falhas_operacionais,
            12,
        )

        self.assertIsNone(
            metrica.taxa_aprovacao
        )

        self.assertIsNone(
            metrica.mrr
        )

    def test_rejeita_contagens_inconsistentes(self):
        dados = dados_avaliacao()

        dados[
            "resultados"
        ][0][
            "total_planejado"
        ] = 99

        with TemporaryDirectory() as pasta:
            caminho = self.criar_json(
                pasta,
                "avaliacao_gemini_20261027T200000Z.json",
                dados,
            )

            with self.assertRaisesRegex(
                md.ErroMetricas,
                "inconsistentes",
            ):
                md.carregar_arquivo_avaliacao(
                    caminho
                )

    def test_rejeita_taxa_fora_do_intervalo(self):
        dados = dados_avaliacao()

        dados[
            "resultados"
        ][0][
            "resumo"
        ][
            "recall_media"
        ] = 1.5

        with TemporaryDirectory() as pasta:
            caminho = self.criar_json(
                pasta,
                "avaliacao_gemini_20261027T200000Z.json",
                dados,
            )

            with self.assertRaisesRegex(
                md.ErroMetricas,
                "intervalo",
            ):
                md.carregar_arquivo_avaliacao(
                    caminho
                )

    def test_rejeita_json_invalido(self):
        with TemporaryDirectory() as pasta:
            caminho = (
                Path(pasta)
                / "avaliacao_gemini_invalida.json"
            )

            caminho.write_text(
                "{invalido",
                encoding="utf-8",
            )

            with self.assertRaises(
                md.ErroMetricas
            ):
                md.carregar_arquivo_avaliacao(
                    caminho
                )

    def test_pasta_ausente_retorna_vazio(self):
        with TemporaryDirectory() as pasta:
            inexistente = (
                Path(pasta)
                / "nao_existe"
            )

            self.assertEqual(
                md.listar_arquivos_avaliacao(
                    inexistente
                ),
                (),
            )

    def test_lista_somente_arquivos_de_avaliacao(self):
        with TemporaryDirectory() as pasta:
            base = Path(
                pasta
            )

            self.criar_json(
                pasta,
                "avaliacao_gemini_20261027T200000Z.json",
                dados_avaliacao(),
            )

            (
                base
                / "outro.json"
            ).write_text(
                "{}",
                encoding="utf-8",
            )

            arquivos = (
                md.listar_arquivos_avaliacao(
                    base
                )
            )

        self.assertEqual(
            len(
                arquivos
            ),
            1,
        )

    def test_carregar_metricas_agrega_arquivos(self):
        with TemporaryDirectory() as pasta:
            self.criar_json(
                pasta,
                "avaliacao_gemini_20261027T200000Z.json",
                dados_avaliacao(
                    modo="hibrida"
                ),
            )

            segundo = dados_avaliacao(
                modo="semantica"
            )

            segundo[
                "executado_em_utc"
            ] = (
                "2026-10-27T21:00:00+00:00"
            )

            self.criar_json(
                pasta,
                "avaliacao_gemini_20261027T210000Z.json",
                segundo,
            )

            metricas = md.carregar_metricas(
                Path(
                    pasta
                )
            )

        self.assertEqual(
            len(
                metricas
            ),
            2,
        )

    def test_resumo_vazio(self):
        resumo = (
            md.resumir_metricas(
                []
            )
        )

        self.assertEqual(
            resumo.execucoes,
            0,
        )

        self.assertEqual(
            resumo.total_planejado,
            0,
        )

        self.assertIsNone(
            resumo.taxa_aprovacao_media
        )

    def test_resumo_consolida_metricas(self):
        metricas = (
            md.MetricaModo(
                arquivo="a.json",
                executado_em_utc=(
                    "2026-10-27T20:00:00+00:00"
                ),
                modelo="modelo",
                modo="palavras",
                total_planejado=12,
                avaliados=12,
                falhas_operacionais=0,
                aprovados=9,
                reprovados=3,
                taxa_aprovacao=0.75,
                precision_media=0.68,
                recall_media=0.917,
                mrr=0.819,
                taxa_citacoes_validas=0.917,
                taxa_conteudo_valido=0.75,
                taxa_status_valido=0.917,
            ),
            md.MetricaModo(
                arquivo="b.json",
                executado_em_utc=(
                    "2026-10-27T21:00:00+00:00"
                ),
                modelo="modelo",
                modo="semantica",
                total_planejado=12,
                avaliados=12,
                falhas_operacionais=0,
                aprovados=12,
                reprovados=0,
                taxa_aprovacao=1.0,
                precision_media=0.333,
                recall_media=1.0,
                mrr=1.0,
                taxa_citacoes_validas=1.0,
                taxa_conteudo_valido=1.0,
                taxa_status_valido=1.0,
            ),
        )

        resumo = (
            md.resumir_metricas(
                metricas
            )
        )

        self.assertEqual(
            resumo.arquivos_lidos,
            2,
        )

        self.assertEqual(
            resumo.execucoes,
            2,
        )

        self.assertEqual(
            resumo.total_planejado,
            24,
        )

        self.assertEqual(
            resumo.total_avaliados,
            24,
        )

        self.assertAlmostEqual(
            resumo.taxa_aprovacao_media,
            0.875,
        )

    def test_agrupa_por_modo(self):
        metrica = md.MetricaModo(
            arquivo="a.json",
            executado_em_utc=(
                "2026-10-27T20:00:00+00:00"
            ),
            modelo="modelo",
            modo="hibrida",
            total_planejado=1,
            avaliados=1,
            falhas_operacionais=0,
            aprovados=1,
            reprovados=0,
            taxa_aprovacao=1.0,
            precision_media=1.0,
            recall_media=1.0,
            mrr=1.0,
            taxa_citacoes_validas=1.0,
            taxa_conteudo_valido=1.0,
            taxa_status_valido=1.0,
        )

        grupos = (
            md.metricas_por_modo(
                [
                    metrica
                ]
            )
        )

        self.assertIn(
            "hibrida",
            grupos,
        )

    def test_ultima_metrica_por_modo(self):
        antiga = md.MetricaModo(
            arquivo="a.json",
            executado_em_utc=(
                "2026-10-27T20:00:00+00:00"
            ),
            modelo="modelo",
            modo="hibrida",
            total_planejado=1,
            avaliados=1,
            falhas_operacionais=0,
            aprovados=1,
            reprovados=0,
            taxa_aprovacao=1.0,
            precision_media=1.0,
            recall_media=1.0,
            mrr=0.5,
            taxa_citacoes_validas=1.0,
            taxa_conteudo_valido=1.0,
            taxa_status_valido=1.0,
        )

        nova = md.MetricaModo(
            arquivo="b.json",
            executado_em_utc=(
                "2026-10-27T21:00:00+00:00"
            ),
            modelo="modelo",
            modo="hibrida",
            total_planejado=1,
            avaliados=1,
            falhas_operacionais=0,
            aprovados=1,
            reprovados=0,
            taxa_aprovacao=1.0,
            precision_media=1.0,
            recall_media=1.0,
            mrr=1.0,
            taxa_citacoes_validas=1.0,
            taxa_conteudo_valido=1.0,
            taxa_status_valido=1.0,
        )

        ultimas = (
            md.ultima_metrica_por_modo(
                [
                    antiga,
                    nova,
                ]
            )
        )

        self.assertEqual(
            ultimas[
                "hibrida"
            ].arquivo,
            "b.json",
        )

    def test_formatacao(self):
        self.assertEqual(
            md.percentual(
                0.91666
            ),
            "91.7%",
        )

        self.assertEqual(
            md.percentual(
                None
            ),
            "N/A",
        )

        self.assertEqual(
            md.decimal(
                0.903
            ),
            "0.903",
        )

        self.assertEqual(
            md.decimal(
                None
            ),
            "N/A",
        )


if __name__ == "__main__":
    unittest.main()