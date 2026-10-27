import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

import metricas_dashboard as md


BASE = Path(__file__).resolve().parent


METRICAS = (
    md.MetricaModo(
        arquivo="avaliacao_1.json",
        executado_em_utc=(
            "2026-10-27T20:00:00+00:00"
        ),
        modelo="gemini-ficticio",
        modo="palavras",
        total_planejado=12,
        avaliados=12,
        falhas_operacionais=0,
        aprovados=9,
        reprovados=3,
        taxa_aprovacao=0.75,
        precision_media=0.681,
        recall_media=0.917,
        mrr=0.819,
        taxa_citacoes_validas=0.917,
        taxa_conteudo_valido=0.75,
        taxa_status_valido=0.917,
    ),
    md.MetricaModo(
        arquivo="avaliacao_1.json",
        executado_em_utc=(
            "2026-10-27T20:00:00+00:00"
        ),
        modelo="gemini-ficticio",
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
    md.MetricaModo(
        arquivo="avaliacao_1.json",
        executado_em_utc=(
            "2026-10-27T20:00:00+00:00"
        ),
        modelo="gemini-ficticio",
        modo="hibrida",
        total_planejado=12,
        avaliados=8,
        falhas_operacionais=4,
        aprovados=8,
        reprovados=0,
        taxa_aprovacao=1.0,
        precision_media=0.333,
        recall_media=1.0,
        mrr=0.903,
        taxa_citacoes_validas=1.0,
        taxa_conteudo_valido=1.0,
        taxa_status_valido=1.0,
    ),
)


class TestDashboardMetricas(
    unittest.TestCase
):

    def criar_tela(
        self,
        metricas=METRICAS,
    ):
        substituicao = patch(
            "metricas_dashboard.carregar_metricas",
            return_value=metricas,
        )

        substituicao.start()

        self.addCleanup(
            substituicao.stop
        )

        tela = AppTest.from_file(
            str(
                BASE
                / "dashboard_metricas.py"
            ),
            default_timeout=15,
        )

        tela.run()

        erros = [
            str(
                item.value
            )
            for item
            in tela.exception
        ]

        self.assertEqual(
            erros,
            [],
            (
                "Erro no dashboard: "
                f"{erros}"
            ),
        )

        return tela

    def test_dashboard_carrega_sem_rede(self):
        tela = self.criar_tela()

        self.assertEqual(
            tela.title[
                0
            ].value,
            "📊 Dashboard de Métricas",
        )

    def test_exibe_metricas_principais(self):
        tela = self.criar_tela()

        rotulos = {
            item.label
            for item
            in tela.metric
        }

        self.assertIn(
            "Execuções",
            rotulos,
        )

        self.assertIn(
            "Casos avaliados",
            rotulos,
        )

        self.assertIn(
            "Falhas operacionais",
            rotulos,
        )

        self.assertIn(
            "Taxa média de aprovação",
            rotulos,
        )

        self.assertIn(
            "MRR médio",
            rotulos,
        )

    def test_filtros_incluem_modos(self):
        tela = self.criar_tela()

        seletor = tela.selectbox(
            key="dashboard_modo"
        )

        self.assertEqual(
            set(
                seletor.options
            ),
            {
                "Todos",
                "palavras",
                "semantica",
                "hibrida",
            },
        )

    def test_filtro_por_modo_atualiza_kpis(self):
        tela = self.criar_tela()

        tela.selectbox(
            key="dashboard_modo"
        ).set_value(
            "semantica"
        )

        tela.run()

        erros = [
            str(
                item.value
            )
            for item
            in tela.exception
        ]

        self.assertEqual(
            erros,
            [],
        )

        metricas_tela = {
            item.label: item.value
            for item
            in tela.metric
        }

        self.assertEqual(
            metricas_tela[
                "Execuções"
            ],
            "1",
        )

        self.assertEqual(
            metricas_tela[
                "Taxa média de aprovação"
            ],
            "100.0%",
        )

        self.assertEqual(
            metricas_tela[
                "MRR médio"
            ],
            "1.000",
        )

    def test_exibe_falha_operacional_separada(self):
        tela = self.criar_tela()

        self.assertTrue(
            any(
                (
                    "Falhas operacionais "
                    "são exibidas separadamente"
                )
                in item.value
                for item
                in tela.warning
            )
        )

    def test_sem_metricas_exibe_aviso(self):
        tela = self.criar_tela(
            metricas=(),
        )

        self.assertTrue(
            any(
                (
                    "Ainda não existem avaliações"
                    in item.value
                )
                for item
                in tela.info
            )
        )

    def test_modelo_aparece_no_filtro(self):
        tela = self.criar_tela()

        seletor = tela.selectbox(
            key="dashboard_modelo"
        )

        self.assertIn(
            "gemini-ficticio",
            seletor.options,
        )


if __name__ == "__main__":
    unittest.main()