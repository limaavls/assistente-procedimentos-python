from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from metricas_dashboard import (
    ErroMetricas,
    carregar_metricas,
    decimal,
    percentual,
    resumir_metricas,
    ultima_metrica_por_modo,
)


BASE = Path(__file__).resolve().parent


def filtrar_metricas(
    metricas,
    *,
    modo: str | None = None,
    modelo: str | None = None,
):
    """
    Filtra as métricas sem alterar a coleção original.

    None representa ausência de filtro.
    """
    resultado = []

    for metrica in metricas:
        if (
            modo is not None
            and metrica.modo != modo
        ):
            continue

        if (
            modelo is not None
            and metrica.modelo != modelo
        ):
            continue

        resultado.append(
            metrica
        )

    return tuple(
        resultado
    )


def formatar_data(
    valor: str,
) -> str:
    """
    Converte ISO para uma apresentação curta.

    Mantém UTC porque os arquivos de avaliação
    são gravados com horário UTC.
    """
    data = datetime.fromisoformat(
        valor.replace(
            "Z",
            "+00:00",
        )
    )

    return data.strftime(
        "%d/%m/%Y %H:%M UTC"
    )


def tabela_metricas(
    metricas,
) -> pd.DataFrame:
    """
    Converte as execuções em DataFrame para exibição.
    """
    linhas = []

    for metrica in metricas:
        linhas.append(
            {
                "Data": formatar_data(
                    metrica.executado_em_utc
                ),
                "Modo": metrica.modo,
                "Modelo": metrica.modelo,
                "Planejados": (
                    metrica.total_planejado
                ),
                "Avaliados": (
                    metrica.avaliados
                ),
                "Falhas operacionais": (
                    metrica.falhas_operacionais
                ),
                "Aprovados": (
                    metrica.aprovados
                ),
                "Reprovados": (
                    metrica.reprovados
                ),
                "Aprovação": (
                    percentual(
                        metrica.taxa_aprovacao
                    )
                ),
                "Precision": (
                    decimal(
                        metrica.precision_media
                    )
                ),
                "Recall": (
                    decimal(
                        metrica.recall_media
                    )
                ),
                "MRR": (
                    decimal(
                        metrica.mrr
                    )
                ),
                "Citações válidas": (
                    percentual(
                        metrica.taxa_citacoes_validas
                    )
                ),
                "Conteúdo válido": (
                    percentual(
                        metrica.taxa_conteudo_valido
                    )
                ),
                "Status válido": (
                    percentual(
                        metrica.taxa_status_valido
                    )
                ),
                "Arquivo": metrica.arquivo,
            }
        )

    return pd.DataFrame(
        linhas
    )


def tabela_comparacao(
    metricas,
) -> pd.DataFrame:
    """
    Gera comparação da execução mais recente de cada modo.
    """
    ultimas = ultima_metrica_por_modo(
        metricas
    )

    linhas = []

    for modo in sorted(
        ultimas
    ):
        metrica = ultimas[
            modo
        ]

        linhas.append(
            {
                "Modo": modo,
                "Aprovação": (
                    metrica.taxa_aprovacao
                ),
                "Precision": (
                    metrica.precision_media
                ),
                "Recall": (
                    metrica.recall_media
                ),
                "MRR": (
                    metrica.mrr
                ),
                "Citações": (
                    metrica.taxa_citacoes_validas
                ),
                "Conteúdo": (
                    metrica.taxa_conteudo_valido
                ),
                "Operacionais": (
                    metrica.falhas_operacionais
                ),
            }
        )

    return pd.DataFrame(
        linhas
    )


def tabela_operacionais(
    metricas,
) -> pd.DataFrame:
    """
    Mostra somente execuções que tiveram falhas operacionais.
    """
    linhas = []

    for metrica in metricas:
        if (
            metrica.falhas_operacionais
            <= 0
        ):
            continue

        linhas.append(
            {
                "Data": formatar_data(
                    metrica.executado_em_utc
                ),
                "Modo": metrica.modo,
                "Modelo": metrica.modelo,
                "Planejados": (
                    metrica.total_planejado
                ),
                "Avaliados": (
                    metrica.avaliados
                ),
                "Falhas operacionais": (
                    metrica.falhas_operacionais
                ),
                "Arquivo": metrica.arquivo,
            }
        )

    return pd.DataFrame(
        linhas
    )


# -------------------------------------------------------------------
# Página
# -------------------------------------------------------------------

st.set_page_config(
    page_title="Dashboard de Métricas",
    page_icon="📊",
    layout="wide",
)

st.title(
    "📊 Dashboard de Métricas"
)

st.caption(
    "Resultados locais das avaliações do assistente. "
    "Abrir esta página não chama Gemini nem Google Drive."
)


# -------------------------------------------------------------------
# Leitura local
# -------------------------------------------------------------------

try:
    metricas = carregar_metricas()

except ErroMetricas as erro:
    st.error(
        f"Não consegui carregar as avaliações: {erro}"
    )

    st.stop()


if not metricas:
    st.info(
        "Ainda não existem avaliações locais em .avaliacoes/. "
        "Execute avaliar_gemini.py para gerar resultados."
    )

    st.stop()


# -------------------------------------------------------------------
# Filtros
# -------------------------------------------------------------------

modelos = sorted(
    {
        metrica.modelo
        for metrica in metricas
    }
)

modos = sorted(
    {
        metrica.modo
        for metrica in metricas
    }
)


st.sidebar.header(
    "Filtros"
)


modo_selecionado = st.sidebar.selectbox(
    "Modo de busca",
    [
        "Todos",
        *modos,
    ],
    key="dashboard_modo",
)


modelo_selecionado = st.sidebar.selectbox(
    "Modelo",
    [
        "Todos",
        *modelos,
    ],
    key="dashboard_modelo",
)


modo_filtro = (
    None
    if modo_selecionado == "Todos"
    else modo_selecionado
)

modelo_filtro = (
    None
    if modelo_selecionado == "Todos"
    else modelo_selecionado
)


filtradas = filtrar_metricas(
    metricas,
    modo=modo_filtro,
    modelo=modelo_filtro,
)


if not filtradas:
    st.warning(
        "Nenhuma avaliação corresponde aos filtros selecionados."
    )

    st.stop()


resumo = resumir_metricas(
    filtradas
)


# -------------------------------------------------------------------
# KPIs
# -------------------------------------------------------------------

st.subheader(
    "Visão geral"
)


coluna_1, coluna_2, coluna_3, coluna_4 = st.columns(
    4
)


coluna_1.metric(
    "Execuções",
    resumo.execucoes,
)


coluna_2.metric(
    "Casos avaliados",
    resumo.total_avaliados,
)


coluna_3.metric(
    "Falhas operacionais",
    resumo.total_falhas_operacionais,
)


coluna_4.metric(
    "Taxa média de aprovação",
    percentual(
        resumo.taxa_aprovacao_media
    ),
)


coluna_5, coluna_6, coluna_7, coluna_8 = st.columns(
    4
)


coluna_5.metric(
    "Precision média",
    decimal(
        resumo.precision_media
    ),
)


coluna_6.metric(
    "Recall médio",
    decimal(
        resumo.recall_media
    ),
)


coluna_7.metric(
    "MRR médio",
    decimal(
        resumo.mrr_medio
    ),
)


coluna_8.metric(
    "Citações válidas",
    percentual(
        resumo.taxa_citacoes_validas_media
    ),
)


# -------------------------------------------------------------------
# Comparação
# -------------------------------------------------------------------

st.divider()

st.subheader(
    "Comparação mais recente por modo"
)


comparacao = tabela_comparacao(
    filtradas
)


if comparacao.empty:
    st.info(
        "Não há dados suficientes para comparação."
    )

else:
    tabela_visual = (
        comparacao.copy()
    )

    for coluna in (
        "Aprovação",
        "Precision",
        "Recall",
        "MRR",
        "Citações",
        "Conteúdo",
    ):
        tabela_visual[
            coluna
        ] = tabela_visual[
            coluna
        ].map(
            lambda valor: (
                "N/A"
                if pd.isna(
                    valor
                )
                else f"{valor:.3f}"
            )
        )

    st.dataframe(
        tabela_visual,
        use_container_width=True,
        hide_index=True,
    )


    grafico = (
        comparacao[
            [
                "Modo",
                "Aprovação",
                "Recall",
                "MRR",
                "Citações",
                "Conteúdo",
            ]
        ]
        .set_index(
            "Modo"
        )
    )

    st.bar_chart(
        grafico,
        use_container_width=True,
    )


# -------------------------------------------------------------------
# Qualidade
# -------------------------------------------------------------------

st.divider()

st.subheader(
    "Indicadores de qualidade"
)


qualidade_1, qualidade_2, qualidade_3 = st.columns(
    3
)


qualidade_1.metric(
    "Conteúdo válido",
    percentual(
        resumo.taxa_conteudo_valido_media
    ),
)


qualidade_2.metric(
    "Status válido",
    percentual(
        resumo.taxa_status_valido_media
    ),
)


qualidade_3.metric(
    "Arquivos de avaliação",
    resumo.arquivos_lidos,
)


# -------------------------------------------------------------------
# Falhas operacionais
# -------------------------------------------------------------------

st.divider()

st.subheader(
    "Falhas operacionais"
)


operacionais = tabela_operacionais(
    filtradas
)


if operacionais.empty:
    st.success(
        "Nenhuma falha operacional nas avaliações filtradas."
    )

else:
    st.warning(
        "Falhas operacionais são exibidas separadamente "
        "e não devem ser confundidas com reprovação de qualidade."
    )

    st.dataframe(
        operacionais,
        use_container_width=True,
        hide_index=True,
    )


# -------------------------------------------------------------------
# Histórico
# -------------------------------------------------------------------

st.divider()

st.subheader(
    "Histórico de avaliações"
)


historico = tabela_metricas(
    filtradas
)


if not historico.empty:
    st.dataframe(
        historico,
        use_container_width=True,
        hide_index=True,
    )


# -------------------------------------------------------------------
# Informações
# -------------------------------------------------------------------

st.divider()

st.subheader(
    "Sobre as métricas"
)


st.caption(
    "Precision mede a proporção de documentos recuperados "
    "que pertencem ao conjunto esperado."
)


st.caption(
    "Recall mede a proporção dos documentos esperados "
    "que foram recuperados."
)


st.caption(
    "MRR considera a posição do primeiro documento relevante "
    "no ranking."
)


st.caption(
    "As médias apresentadas são médias simples entre execuções "
    "filtradas e não constituem benchmark científico."
)


st.caption(
    "Os arquivos de avaliação permanecem locais em .avaliacoes/ "
    "e estão ignorados pelo Git."
)