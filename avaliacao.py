from dataclasses import dataclass, field
from statistics import mean
from typing import Iterable


@dataclass(frozen=True)
class CasoAvaliacao:
    """
    Define um caso esperado para avaliação automática.

    Nenhum campo depende de uma chamada real à IA.
    """
    identificador: str
    pergunta: str

    documentos_esperados: tuple[str, ...] = ()
    termos_obrigatorios: tuple[str, ...] = ()
    termos_proibidos: tuple[str, ...] = ()

    status_esperado: str | None = None


@dataclass(frozen=True)
class ResultadoCaso:
    identificador: str

    documentos_encontrados: tuple[str, ...]
    documentos_esperados: tuple[str, ...]

    citacoes_encontradas: tuple[str, ...]
    termos_obrigatorios_encontrados: tuple[str, ...]
    termos_obrigatorios_ausentes: tuple[str, ...]
    termos_proibidos_encontrados: tuple[str, ...]

    status_obtido: str | None
    status_esperado: str | None

    precision_documentos: float
    recall_documentos: float
    reciprocal_rank: float

    citacoes_validas: bool
    conteudo_valido: bool
    status_valido: bool

    aprovado: bool


@dataclass(frozen=True)
class ResumoAvaliacao:
    total: int
    aprovados: int
    reprovados: int

    taxa_aprovacao: float

    precision_media: float
    recall_media: float
    mrr: float

    taxa_citacoes_validas: float
    taxa_conteudo_valido: float
    taxa_status_valido: float

    resultados: tuple[ResultadoCaso, ...] = field(
        default_factory=tuple
    )


def normalizar_texto(
    texto: str,
) -> str:
    """
    Normalização simples para avaliação textual.

    A avaliação ignora:
    - diferenças entre maiúsculas e minúsculas;
    - excesso de espaços;
    - quebras de linha.

    Não remove palavras, números ou negações.
    """
    if not isinstance(
        texto,
        str,
    ):
        raise ValueError(
            "O texto avaliado precisa ser string."
        )

    return " ".join(
        texto.casefold().split()
    )


def _unicos_preservando_ordem(
    valores: Iterable[str],
) -> tuple[str, ...]:
    vistos = set()
    resultado = []

    for valor in valores:
        chave = valor.casefold()

        if chave in vistos:
            continue

        vistos.add(
            chave
        )

        resultado.append(
            valor
        )

    return tuple(
        resultado
    )


def precision_recall_documentos(
    encontrados: Iterable[str],
    esperados: Iterable[str],
) -> tuple[float, float]:
    """
    Calcula precision e recall usando nomes de documentos.

    Precision:
        quantos recuperados eram relevantes.

    Recall:
        quantos documentos esperados foram recuperados.
    """
    encontrados_unicos = {
        item.casefold()
        for item in encontrados
    }

    esperados_unicos = {
        item.casefold()
        for item in esperados
    }

    if not esperados_unicos:
        recall = 1.0
    else:
        recall = (
            len(
                encontrados_unicos
                & esperados_unicos
            )
            / len(
                esperados_unicos
            )
        )

    if not encontrados_unicos:
        precision = (
            1.0
            if not esperados_unicos
            else 0.0
        )
    else:
        precision = (
            len(
                encontrados_unicos
                & esperados_unicos
            )
            / len(
                encontrados_unicos
            )
        )

    return (
        precision,
        recall,
    )


def reciprocal_rank(
    encontrados: Iterable[str],
    esperados: Iterable[str],
) -> float:
    """
    Reciprocal Rank do primeiro documento esperado encontrado.

    Primeiro lugar:
        1.0

    Segundo lugar:
        0.5

    Terceiro lugar:
        0.333...
    """
    esperados_normalizados = {
        item.casefold()
        for item in esperados
    }

    if not esperados_normalizados:
        return 1.0

    for posicao, documento in enumerate(
        encontrados,
        start=1,
    ):
        if (
            documento.casefold()
            in esperados_normalizados
        ):
            return (
                1.0
                / posicao
            )

    return 0.0


def avaliar_conteudo(
    texto: str,
    termos_obrigatorios: Iterable[str],
    termos_proibidos: Iterable[str],
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    bool,
]:
    """
    Verifica termos obrigatórios e proibidos.

    A avaliação é determinística e não usa outro modelo de IA.
    """
    normalizado = normalizar_texto(
        texto
    )

    obrigatorios = tuple(
        termos_obrigatorios
    )

    proibidos = tuple(
        termos_proibidos
    )

    encontrados = tuple(
        termo
        for termo in obrigatorios
        if normalizar_texto(
            termo
        ) in normalizado
    )

    ausentes = tuple(
        termo
        for termo in obrigatorios
        if normalizar_texto(
            termo
        ) not in normalizado
    )

    proibidos_encontrados = tuple(
        termo
        for termo in proibidos
        if normalizar_texto(
            termo
        ) in normalizado
    )

    valido = (
        not ausentes
        and not proibidos_encontrados
    )

    return (
        encontrados,
        ausentes,
        proibidos_encontrados,
        valido,
    )


def avaliar_caso(
    caso: CasoAvaliacao,
    *,
    documentos_encontrados: Iterable[str],
    texto_resposta: str,
    documentos_citados: Iterable[str],
    citacoes_validas: bool,
    status_obtido: str | None,
) -> ResultadoCaso:
    """
    Avalia uma execução individual.

    A função não executa busca nem chama Gemini.
    Ela recebe os resultados de uma execução e calcula métricas.
    """
    if not isinstance(
        caso,
        CasoAvaliacao,
    ):
        raise ValueError(
            "Caso de avaliação inválido."
        )

    documentos_encontrados = (
        _unicos_preservando_ordem(
            documentos_encontrados
        )
    )

    documentos_citados = (
        _unicos_preservando_ordem(
            documentos_citados
        )
    )

    precision, recall = (
        precision_recall_documentos(
            documentos_encontrados,
            caso.documentos_esperados,
        )
    )

    rr = reciprocal_rank(
        documentos_encontrados,
        caso.documentos_esperados,
    )

    (
        obrigatorios_encontrados,
        obrigatorios_ausentes,
        proibidos_encontrados,
        conteudo_valido,
    ) = avaliar_conteudo(
        texto_resposta,
        caso.termos_obrigatorios,
        caso.termos_proibidos,
    )

    if caso.status_esperado is None:
        status_valido = True

    else:
        status_valido = (
            status_obtido
            == caso.status_esperado
        )

    documentos_esperados = {
        item.casefold()
        for item in caso.documentos_esperados
    }

    citados_normalizados = {
        item.casefold()
        for item in documentos_citados
    }

    if documentos_esperados:
        citacoes_apontam_para_documento_esperado = bool(
            documentos_esperados
            & citados_normalizados
        )
    else:
        citacoes_apontam_para_documento_esperado = True

    citacoes_ok = (
        bool(
            citacoes_validas
        )
        and citacoes_apontam_para_documento_esperado
    )

    recuperacao_valida = (
        recall == 1.0
    )

    aprovado = all(
        (
            recuperacao_valida,
            citacoes_ok,
            conteudo_valido,
            status_valido,
        )
    )

    return ResultadoCaso(
        identificador=caso.identificador,
        documentos_encontrados=documentos_encontrados,
        documentos_esperados=caso.documentos_esperados,
        citacoes_encontradas=documentos_citados,
        termos_obrigatorios_encontrados=(
            obrigatorios_encontrados
        ),
        termos_obrigatorios_ausentes=(
            obrigatorios_ausentes
        ),
        termos_proibidos_encontrados=(
            proibidos_encontrados
        ),
        status_obtido=status_obtido,
        status_esperado=caso.status_esperado,
        precision_documentos=precision,
        recall_documentos=recall,
        reciprocal_rank=rr,
        citacoes_validas=citacoes_ok,
        conteudo_valido=conteudo_valido,
        status_valido=status_valido,
        aprovado=aprovado,
    )


def resumir_resultados(
    resultados: Iterable[ResultadoCaso],
) -> ResumoAvaliacao:
    """
    Consolida resultados individuais em métricas gerais.
    """
    resultados = tuple(
        resultados
    )

    if not resultados:
        raise ValueError(
            "Nenhum resultado disponível para avaliação."
        )

    total = len(
        resultados
    )

    aprovados = sum(
        1
        for resultado in resultados
        if resultado.aprovado
    )

    reprovados = (
        total
        - aprovados
    )

    return ResumoAvaliacao(
        total=total,
        aprovados=aprovados,
        reprovados=reprovados,
        taxa_aprovacao=(
            aprovados
            / total
        ),
        precision_media=mean(
            resultado.precision_documentos
            for resultado in resultados
        ),
        recall_media=mean(
            resultado.recall_documentos
            for resultado in resultados
        ),
        mrr=mean(
            resultado.reciprocal_rank
            for resultado in resultados
        ),
        taxa_citacoes_validas=mean(
            1.0
            if resultado.citacoes_validas
            else 0.0
            for resultado in resultados
        ),
        taxa_conteudo_valido=mean(
            1.0
            if resultado.conteudo_valido
            else 0.0
            for resultado in resultados
        ),
        taxa_status_valido=mean(
            1.0
            if resultado.status_valido
            else 0.0
            for resultado in resultados
        ),
        resultados=resultados,
    )