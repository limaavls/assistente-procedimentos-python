import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean


BASE = Path(__file__).resolve().parent

PASTA_AVALIACOES = (
    BASE
    / ".avaliacoes"
)


class ErroMetricas(ValueError):
    """Erro controlado ao carregar métricas locais."""


@dataclass(frozen=True)
class MetricaModo:
    arquivo: str
    executado_em_utc: str
    modelo: str

    modo: str

    total_planejado: int
    avaliados: int
    falhas_operacionais: int

    aprovados: int
    reprovados: int

    taxa_aprovacao: float | None
    precision_media: float | None
    recall_media: float | None
    mrr: float | None

    taxa_citacoes_validas: float | None
    taxa_conteudo_valido: float | None
    taxa_status_valido: float | None


@dataclass(frozen=True)
class ResumoDashboard:
    arquivos_lidos: int
    execucoes: int
    modelos: tuple[str, ...]
    modos: tuple[str, ...]

    total_planejado: int
    total_avaliados: int
    total_falhas_operacionais: int

    taxa_aprovacao_media: float | None
    precision_media: float | None
    recall_media: float | None
    mrr_medio: float | None

    taxa_citacoes_validas_media: float | None
    taxa_conteudo_valido_media: float | None
    taxa_status_valido_media: float | None

    metricas: tuple[
        MetricaModo,
        ...
    ]


def _numero(
    valor,
    *,
    campo: str,
) -> float | None:
    if valor is None:
        return None

    if isinstance(
        valor,
        bool,
    ):
        raise ErroMetricas(
            f"Campo numérico inválido: {campo}."
        )

    if not isinstance(
        valor,
        (int, float),
    ):
        raise ErroMetricas(
            f"Campo numérico inválido: {campo}."
        )

    return float(
        valor
    )


def _inteiro(
    valor,
    *,
    campo: str,
) -> int:
    if (
        isinstance(
            valor,
            bool,
        )
        or not isinstance(
            valor,
            int,
        )
        or valor < 0
    ):
        raise ErroMetricas(
            f"Campo inteiro inválido: {campo}."
        )

    return valor


def _texto(
    valor,
    *,
    campo: str,
) -> str:
    if (
        not isinstance(
            valor,
            str,
        )
        or not valor.strip()
    ):
        raise ErroMetricas(
            f"Campo de texto inválido: {campo}."
        )

    return valor.strip()


def _validar_taxa(
    valor: float | None,
    *,
    campo: str,
) -> float | None:
    if valor is None:
        return None

    if not (
        0.0
        <= valor
        <= 1.0
    ):
        raise ErroMetricas(
            f"Taxa fora do intervalo esperado: {campo}."
        )

    return valor


def _media_opcional(
    valores,
) -> float | None:
    validos = [
        valor
        for valor in valores
        if valor is not None
    ]

    if not validos:
        return None

    return mean(
        validos
    )


def _validar_data_iso(
    valor: str,
) -> str:
    valor = _texto(
        valor,
        campo="executado_em_utc",
    )

    try:
        datetime.fromisoformat(
            valor.replace(
                "Z",
                "+00:00",
            )
        )

    except ValueError as erro:
        raise ErroMetricas(
            "Data de execução inválida."
        ) from erro

    return valor


def _erro_operacional_legado(
    erro,
) -> bool:
    """
    Reconhece falhas operacionais em arquivos gerados
    antes da separação entre qualidade e operação.
    """
    if not isinstance(
        erro,
        str,
    ):
        return False

    texto = (
        erro.strip()
        .casefold()
    )

    if not texto:
        return False

    indicadores = (
        "erro da api",
        "429",
        "resource_exhausted",
        "falha de conexão",
        "falha de conexao",
        "falha operacional",
        "timeout",
        "timed out",
        "connection",
    )

    return any(
        indicador in texto
        for indicador in indicadores
    )


def _ids_operacionais_legados(
    execucoes,
) -> set[str]:
    """
    Localiza casos que não chegaram a ser avaliados
    por falha operacional em arquivos antigos.
    """
    if not isinstance(
        execucoes,
        list,
    ):
        return set()

    ids = set()

    for item in execucoes:
        if not isinstance(
            item,
            dict,
        ):
            continue

        if not _erro_operacional_legado(
            item.get(
                "erro"
            )
        ):
            continue

        caso_id = item.get(
            "caso_id"
        )

        if isinstance(
            caso_id,
            str,
        ) and caso_id.strip():
            ids.add(
                caso_id.strip()
            )

    return ids


def _resultado_ids_operacionais(
    resumo,
    ids_operacionais,
):
    """
    Remove dos resultados de qualidade os casos que,
    em arquivos antigos, representam falhas operacionais.
    """
    if not isinstance(
        resumo,
        dict,
    ):
        return []

    resultados = resumo.get(
        "resultados"
    )

    if not isinstance(
        resultados,
        list,
    ):
        return []

    filtrados = []

    for resultado in resultados:
        if not isinstance(
            resultado,
            dict,
        ):
            continue

        identificador = resultado.get(
            "identificador"
        )

        if identificador in ids_operacionais:
            continue

        filtrados.append(
            resultado
        )

    return filtrados


def _resumo_recalculado_legado(
    item,
):
    """
    Converte o formato antigo de avaliar_gemini.py para
    o contrato atual do dashboard.

    Arquivos antigos tinham:
        modo
        resumo
        execucoes

    mas ainda não possuíam:
        total_planejado
        avaliados
        falhas_operacionais

    Quando uma execução antiga contém erro operacional,
    as métricas são recalculadas sem penalizar a qualidade.
    """
    resumo = item.get(
        "resumo"
    )

    execucoes = item.get(
        "execucoes"
    )

    if not isinstance(
        resumo,
        dict,
    ):
        raise ErroMetricas(
            "Resumo legado da avaliação inválido."
        )

    ids_operacionais = (
        _ids_operacionais_legados(
            execucoes
        )
    )

    if isinstance(
        execucoes,
        list,
    ):
        total_planejado = len(
            execucoes
        )
    else:
        total_planejado = _inteiro(
            resumo.get(
                "total"
            ),
            campo="resumo.total",
        )

    falhas_operacionais = len(
        ids_operacionais
    )

    resultados_validos = (
        _resultado_ids_operacionais(
            resumo,
            ids_operacionais,
        )
    )

    if resultados_validos:
        avaliados = len(
            resultados_validos
        )

        aprovados = sum(
            1
            for resultado in resultados_validos
            if resultado.get(
                "aprovado"
            ) is True
        )

        reprovados = (
            avaliados
            - aprovados
        )

        taxa_aprovacao = (
            aprovados
            / avaliados
        )

        precision_media = _media_opcional(
            _numero(
                resultado.get(
                    "precision_documentos"
                ),
                campo=(
                    "precision_documentos"
                ),
            )
            for resultado in resultados_validos
        )

        recall_media = _media_opcional(
            _numero(
                resultado.get(
                    "recall_documentos"
                ),
                campo=(
                    "recall_documentos"
                ),
            )
            for resultado in resultados_validos
        )

        mrr = _media_opcional(
            _numero(
                resultado.get(
                    "reciprocal_rank"
                ),
                campo=(
                    "reciprocal_rank"
                ),
            )
            for resultado in resultados_validos
        )

        taxa_citacoes = mean(
            1.0
            if resultado.get(
                "citacoes_validas"
            ) is True
            else 0.0
            for resultado in resultados_validos
        )

        taxa_conteudo = mean(
            1.0
            if resultado.get(
                "conteudo_valido"
            ) is True
            else 0.0
            for resultado in resultados_validos
        )

        taxa_status = mean(
            1.0
            if resultado.get(
                "status_valido"
            ) is True
            else 0.0
            for resultado in resultados_validos
        )

    else:
        total_resumo = _inteiro(
            resumo.get(
                "total"
            ),
            campo="resumo.total",
        )

        avaliados = (
            total_resumo
            - falhas_operacionais
        )

        if avaliados < 0:
            raise ErroMetricas(
                "Contagens legadas da avaliação são inconsistentes."
            )

        aprovados_originais = _inteiro(
            resumo.get(
                "aprovados"
            ),
            campo="resumo.aprovados",
        )

        aprovados = min(
            aprovados_originais,
            avaliados,
        )

        reprovados = (
            avaliados
            - aprovados
        )

        if avaliados == 0:
            taxa_aprovacao = None
            precision_media = None
            recall_media = None
            mrr = None
            taxa_citacoes = None
            taxa_conteudo = None
            taxa_status = None

        else:
            taxa_aprovacao = (
                aprovados
                / avaliados
            )

            precision_media = _validar_taxa(
                _numero(
                    resumo.get(
                        "precision_media"
                    ),
                    campo="precision_media",
                ),
                campo="precision_media",
            )

            recall_media = _validar_taxa(
                _numero(
                    resumo.get(
                        "recall_media"
                    ),
                    campo="recall_media",
                ),
                campo="recall_media",
            )

            mrr = _validar_taxa(
                _numero(
                    resumo.get(
                        "mrr"
                    ),
                    campo="mrr",
                ),
                campo="mrr",
            )

            taxa_citacoes = _validar_taxa(
                _numero(
                    resumo.get(
                        "taxa_citacoes_validas"
                    ),
                    campo=(
                        "taxa_citacoes_validas"
                    ),
                ),
                campo=(
                    "taxa_citacoes_validas"
                ),
            )

            taxa_conteudo = _validar_taxa(
                _numero(
                    resumo.get(
                        "taxa_conteudo_valido"
                    ),
                    campo=(
                        "taxa_conteudo_valido"
                    ),
                ),
                campo=(
                    "taxa_conteudo_valido"
                ),
            )

            taxa_status = _validar_taxa(
                _numero(
                    resumo.get(
                        "taxa_status_valido"
                    ),
                    campo=(
                        "taxa_status_valido"
                    ),
                ),
                campo=(
                    "taxa_status_valido"
                ),
            )

    if (
        avaliados
        + falhas_operacionais
        != total_planejado
    ):
        raise ErroMetricas(
            "Contagens legadas da avaliação são inconsistentes."
        )

    return {
        "total_planejado": (
            total_planejado
        ),
        "avaliados": avaliados,
        "falhas_operacionais": (
            falhas_operacionais
        ),
        "aprovados": aprovados,
        "reprovados": reprovados,
        "taxa_aprovacao": (
            taxa_aprovacao
        ),
        "precision_media": (
            precision_media
        ),
        "recall_media": (
            recall_media
        ),
        "mrr": mrr,
        "taxa_citacoes_validas": (
            taxa_citacoes
        ),
        "taxa_conteudo_valido": (
            taxa_conteudo
        ),
        "taxa_status_valido": (
            taxa_status
        ),
    }


def _extrair_metrica_atual(
    item,
):
    """
    Lê o formato atual gerado por avaliar_gemini.py.
    """
    total_planejado = _inteiro(
        item.get(
            "total_planejado"
        ),
        campo="total_planejado",
    )

    avaliados = _inteiro(
        item.get(
            "avaliados"
        ),
        campo="avaliados",
    )

    falhas_operacionais = _inteiro(
        item.get(
            "falhas_operacionais"
        ),
        campo="falhas_operacionais",
    )

    if (
        avaliados
        + falhas_operacionais
        != total_planejado
    ):
        raise ErroMetricas(
            "Contagens da avaliação são inconsistentes."
        )

    resumo = item.get(
        "resumo"
    )

    if resumo is None:
        if avaliados != 0:
            raise ErroMetricas(
                "Avaliação possui casos avaliados sem resumo."
            )

        return {
            "total_planejado": (
                total_planejado
            ),
            "avaliados": avaliados,
            "falhas_operacionais": (
                falhas_operacionais
            ),
            "aprovados": 0,
            "reprovados": 0,
            "taxa_aprovacao": None,
            "precision_media": None,
            "recall_media": None,
            "mrr": None,
            "taxa_citacoes_validas": None,
            "taxa_conteudo_valido": None,
            "taxa_status_valido": None,
        }

    if not isinstance(
        resumo,
        dict,
    ):
        raise ErroMetricas(
            "Resumo da avaliação inválido."
        )

    total_resumo = _inteiro(
        resumo.get(
            "total"
        ),
        campo="resumo.total",
    )

    if total_resumo != avaliados:
        raise ErroMetricas(
            "Total do resumo difere dos casos avaliados."
        )

    aprovados = _inteiro(
        resumo.get(
            "aprovados"
        ),
        campo="resumo.aprovados",
    )

    reprovados = _inteiro(
        resumo.get(
            "reprovados"
        ),
        campo="resumo.reprovados",
    )

    if (
        aprovados
        + reprovados
        != total_resumo
    ):
        raise ErroMetricas(
            "Aprovados e reprovados são inconsistentes."
        )

    return {
        "total_planejado": (
            total_planejado
        ),
        "avaliados": avaliados,
        "falhas_operacionais": (
            falhas_operacionais
        ),
        "aprovados": aprovados,
        "reprovados": reprovados,
        "taxa_aprovacao": (
            _validar_taxa(
                _numero(
                    resumo.get(
                        "taxa_aprovacao"
                    ),
                    campo=(
                        "taxa_aprovacao"
                    ),
                ),
                campo="taxa_aprovacao",
            )
        ),
        "precision_media": (
            _validar_taxa(
                _numero(
                    resumo.get(
                        "precision_media"
                    ),
                    campo=(
                        "precision_media"
                    ),
                ),
                campo="precision_media",
            )
        ),
        "recall_media": (
            _validar_taxa(
                _numero(
                    resumo.get(
                        "recall_media"
                    ),
                    campo=(
                        "recall_media"
                    ),
                ),
                campo="recall_media",
            )
        ),
        "mrr": (
            _validar_taxa(
                _numero(
                    resumo.get(
                        "mrr"
                    ),
                    campo="mrr",
                ),
                campo="mrr",
            )
        ),
        "taxa_citacoes_validas": (
            _validar_taxa(
                _numero(
                    resumo.get(
                        "taxa_citacoes_validas"
                    ),
                    campo=(
                        "taxa_citacoes_validas"
                    ),
                ),
                campo=(
                    "taxa_citacoes_validas"
                ),
            )
        ),
        "taxa_conteudo_valido": (
            _validar_taxa(
                _numero(
                    resumo.get(
                        "taxa_conteudo_valido"
                    ),
                    campo=(
                        "taxa_conteudo_valido"
                    ),
                ),
                campo=(
                    "taxa_conteudo_valido"
                ),
            )
        ),
        "taxa_status_valido": (
            _validar_taxa(
                _numero(
                    resumo.get(
                        "taxa_status_valido"
                    ),
                    campo=(
                        "taxa_status_valido"
                    ),
                ),
                campo=(
                    "taxa_status_valido"
                ),
            )
        ),
    }


def _extrair_metrica_item(
    item,
):
    """
    Detecta automaticamente arquivos novos e legados.
    """
    campos_novos = (
        "total_planejado",
        "avaliados",
        "falhas_operacionais",
    )

    if all(
        campo in item
        for campo in campos_novos
    ):
        return _extrair_metrica_atual(
            item
        )

    return _resumo_recalculado_legado(
        item
    )


def carregar_arquivo_avaliacao(
    caminho: Path,
) -> tuple[MetricaModo, ...]:
    """
    Lê JSONs novos e antigos gerados por avaliar_gemini.py.
    """
    if not isinstance(
        caminho,
        Path,
    ):
        raise ErroMetricas(
            "O caminho da avaliação precisa ser Path."
        )

    if not caminho.is_file():
        raise ErroMetricas(
            "Arquivo de avaliação não encontrado."
        )

    try:
        dados = json.loads(
            caminho.read_text(
                encoding="utf-8"
            )
        )

    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as erro:
        raise ErroMetricas(
            "Não consegui ler o arquivo de avaliação."
        ) from erro

    if not isinstance(
        dados,
        dict,
    ):
        raise ErroMetricas(
            "Estrutura da avaliação inválida."
        )

    executado_em = (
        _validar_data_iso(
            dados.get(
                "executado_em_utc"
            )
        )
    )

    modelo = _texto(
        dados.get(
            "modelo"
        ),
        campo="modelo",
    )

    resultados = dados.get(
        "resultados"
    )

    if not isinstance(
        resultados,
        list,
    ):
        raise ErroMetricas(
            "A avaliação não possui lista de resultados."
        )

    metricas = []

    for indice, item in enumerate(
        resultados,
        start=1,
    ):
        if not isinstance(
            item,
            dict,
        ):
            raise ErroMetricas(
                "Resultado de modo inválido."
            )

        modo = _texto(
            item.get(
                "modo"
            ),
            campo=(
                f"resultados[{indice}].modo"
            ),
        )

        valores = (
            _extrair_metrica_item(
                item
            )
        )

        metricas.append(
            MetricaModo(
                arquivo=caminho.name,
                executado_em_utc=(
                    executado_em
                ),
                modelo=modelo,
                modo=modo,
                total_planejado=(
                    valores[
                        "total_planejado"
                    ]
                ),
                avaliados=(
                    valores[
                        "avaliados"
                    ]
                ),
                falhas_operacionais=(
                    valores[
                        "falhas_operacionais"
                    ]
                ),
                aprovados=(
                    valores[
                        "aprovados"
                    ]
                ),
                reprovados=(
                    valores[
                        "reprovados"
                    ]
                ),
                taxa_aprovacao=(
                    valores[
                        "taxa_aprovacao"
                    ]
                ),
                precision_media=(
                    valores[
                        "precision_media"
                    ]
                ),
                recall_media=(
                    valores[
                        "recall_media"
                    ]
                ),
                mrr=(
                    valores[
                        "mrr"
                    ]
                ),
                taxa_citacoes_validas=(
                    valores[
                        "taxa_citacoes_validas"
                    ]
                ),
                taxa_conteudo_valido=(
                    valores[
                        "taxa_conteudo_valido"
                    ]
                ),
                taxa_status_valido=(
                    valores[
                        "taxa_status_valido"
                    ]
                ),
            )
        )

    return tuple(
        metricas
    )


def listar_arquivos_avaliacao(
    pasta: Path = PASTA_AVALIACOES,
) -> tuple[Path, ...]:
    if not isinstance(
        pasta,
        Path,
    ):
        raise ErroMetricas(
            "A pasta de avaliações precisa ser Path."
        )

    if not pasta.exists():
        return ()

    if not pasta.is_dir():
        raise ErroMetricas(
            "O caminho de avaliações não é uma pasta."
        )

    return tuple(
        sorted(
            pasta.glob(
                "avaliacao_gemini_*.json"
            ),
            key=lambda item: (
                item.name
            ),
        )
    )


def carregar_metricas(
    pasta: Path = PASTA_AVALIACOES,
) -> tuple[MetricaModo, ...]:
    metricas = []

    for caminho in (
        listar_arquivos_avaliacao(
            pasta
        )
    ):
        metricas.extend(
            carregar_arquivo_avaliacao(
                caminho
            )
        )

    return tuple(
        metricas
    )


def resumir_metricas(
    metricas,
) -> ResumoDashboard:
    metricas = tuple(
        metricas
    )

    if not metricas:
        return ResumoDashboard(
            arquivos_lidos=0,
            execucoes=0,
            modelos=(),
            modos=(),
            total_planejado=0,
            total_avaliados=0,
            total_falhas_operacionais=0,
            taxa_aprovacao_media=None,
            precision_media=None,
            recall_media=None,
            mrr_medio=None,
            taxa_citacoes_validas_media=None,
            taxa_conteudo_valido_media=None,
            taxa_status_valido_media=None,
            metricas=(),
        )

    arquivos = {
        metrica.arquivo
        for metrica in metricas
    }

    modelos = tuple(
        sorted(
            {
                metrica.modelo
                for metrica in metricas
            }
        )
    )

    modos = tuple(
        sorted(
            {
                metrica.modo
                for metrica in metricas
            }
        )
    )

    return ResumoDashboard(
        arquivos_lidos=len(
            arquivos
        ),
        execucoes=len(
            metricas
        ),
        modelos=modelos,
        modos=modos,
        total_planejado=sum(
            metrica.total_planejado
            for metrica in metricas
        ),
        total_avaliados=sum(
            metrica.avaliados
            for metrica in metricas
        ),
        total_falhas_operacionais=sum(
            metrica.falhas_operacionais
            for metrica in metricas
        ),
        taxa_aprovacao_media=(
            _media_opcional(
                metrica.taxa_aprovacao
                for metrica in metricas
            )
        ),
        precision_media=(
            _media_opcional(
                metrica.precision_media
                for metrica in metricas
            )
        ),
        recall_media=(
            _media_opcional(
                metrica.recall_media
                for metrica in metricas
            )
        ),
        mrr_medio=(
            _media_opcional(
                metrica.mrr
                for metrica in metricas
            )
        ),
        taxa_citacoes_validas_media=(
            _media_opcional(
                metrica.taxa_citacoes_validas
                for metrica in metricas
            )
        ),
        taxa_conteudo_valido_media=(
            _media_opcional(
                metrica.taxa_conteudo_valido
                for metrica in metricas
            )
        ),
        taxa_status_valido_media=(
            _media_opcional(
                metrica.taxa_status_valido
                for metrica in metricas
            )
        ),
        metricas=metricas,
    )


def metricas_por_modo(
    metricas,
) -> dict[
    str,
    tuple[MetricaModo, ...],
]:
    grupos = {}

    for metrica in metricas:
        grupos.setdefault(
            metrica.modo,
            [],
        ).append(
            metrica
        )

    return {
        modo: tuple(
            itens
        )
        for modo, itens
        in grupos.items()
    }


def ultima_metrica_por_modo(
    metricas,
) -> dict[
    str,
    MetricaModo,
]:
    ultimas = {}

    for metrica in metricas:
        atual = ultimas.get(
            metrica.modo
        )

        if atual is None:
            ultimas[
                metrica.modo
            ] = metrica

            continue

        data_atual = datetime.fromisoformat(
            atual.executado_em_utc.replace(
                "Z",
                "+00:00",
            )
        )

        data_nova = datetime.fromisoformat(
            metrica.executado_em_utc.replace(
                "Z",
                "+00:00",
            )
        )

        if data_nova > data_atual:
            ultimas[
                metrica.modo
            ] = metrica

    return ultimas


def percentual(
    valor: float | None,
) -> str:
    if valor is None:
        return "N/A"

    return (
        f"{valor * 100:.1f}%"
    )


def decimal(
    valor: float | None,
) -> str:
    if valor is None:
        return "N/A"

    return (
        f"{valor:.3f}"
    )