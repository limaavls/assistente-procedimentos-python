from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Callable

from avaliacao import (
    precision_recall_documentos,
    reciprocal_rank,
)
from busca import buscar_por_pergunta
from busca_hibrida import buscar_hibrido
from busca_semantica import buscar_semantico
from casos_avaliacao import (
    CASOS_AVALIACAO,
    DOCUMENTOS_AVALIACAO,
)


ResultadoBusca = list[
    tuple[
        Path,
        str,
        list,
    ]
]

FuncaoBusca = Callable[
    [
        list[tuple[Path, str]],
        str,
    ],
    ResultadoBusca,
]


@dataclass(frozen=True)
class ResultadoRecuperacao:
    caso_id: str
    pergunta: str
    esperados: tuple[str, ...]
    encontrados: tuple[str, ...]

    precision: float
    recall: float
    reciprocal_rank: float

    aprovado: bool


@dataclass(frozen=True)
class ResumoModo:
    modo: str
    total: int

    aprovados: int
    taxa_aprovacao: float

    precision_media: float
    recall_media: float
    mrr: float

    resultados: tuple[
        ResultadoRecuperacao,
        ...
    ]


MODOS = {
    "palavras": buscar_por_pergunta,
    "semantica": buscar_semantico,
    "hibrida": buscar_hibrido,
}


def nomes_documentos(
    resultados: ResultadoBusca,
) -> tuple[str, ...]:
    """
    Obtém os nomes dos documentos preservando
    a ordem do ranking.
    """
    nomes = []
    vistos = set()

    for resultado in resultados:
        if (
            not isinstance(
                resultado,
                tuple,
            )
            or len(resultado) != 3
        ):
            raise ValueError(
                "Resultado de busca em formato inválido."
            )

        arquivo = resultado[0]

        if not isinstance(
            arquivo,
            Path,
        ):
            raise ValueError(
                "Documento recuperado em formato inválido."
            )

        chave = (
            arquivo.name
            .casefold()
        )

        if chave in vistos:
            continue

        vistos.add(
            chave
        )

        nomes.append(
            arquivo.name
        )

    return tuple(
        nomes
    )


def avaliar_modo(
    modo: str,
    funcao_busca: FuncaoBusca,
    documentos=DOCUMENTOS_AVALIACAO,
    casos=CASOS_AVALIACAO,
) -> ResumoModo:
    """
    Executa todos os casos de recuperação
    com um mecanismo de busca.
    """
    resultados_finais = []

    for caso in casos:
        resultados = funcao_busca(
            documentos,
            caso.pergunta,
        )

        encontrados = nomes_documentos(
            resultados
        )

        precision, recall = (
            precision_recall_documentos(
                encontrados,
                caso.documentos_esperados,
            )
        )

        rr = reciprocal_rank(
            encontrados,
            caso.documentos_esperados,
        )

        aprovado = (
            recall == 1.0
        )

        resultados_finais.append(
            ResultadoRecuperacao(
                caso_id=(
                    caso.identificador
                ),
                pergunta=caso.pergunta,
                esperados=(
                    caso.documentos_esperados
                ),
                encontrados=encontrados,
                precision=precision,
                recall=recall,
                reciprocal_rank=rr,
                aprovado=aprovado,
            )
        )

    if not resultados_finais:
        raise ValueError(
            "Nenhum caso de avaliação disponível."
        )

    total = len(
        resultados_finais
    )

    aprovados = sum(
        1
        for resultado
        in resultados_finais
        if resultado.aprovado
    )

    return ResumoModo(
        modo=modo,
        total=total,
        aprovados=aprovados,
        taxa_aprovacao=(
            aprovados
            / total
        ),
        precision_media=mean(
            resultado.precision
            for resultado
            in resultados_finais
        ),
        recall_media=mean(
            resultado.recall
            for resultado
            in resultados_finais
        ),
        mrr=mean(
            resultado.reciprocal_rank
            for resultado
            in resultados_finais
        ),
        resultados=tuple(
            resultados_finais
        ),
    )


def executar_comparacao(
    modos=None,
) -> tuple[ResumoModo, ...]:
    """
    Executa a avaliação comparativa dos modos.

    Nenhuma chamada ao Gemini é feita.
    """
    if modos is None:
        modos = MODOS

    resumos = []

    for nome, funcao in (
        modos.items()
    ):
        resumos.append(
            avaliar_modo(
                nome,
                funcao,
            )
        )

    return tuple(
        resumos
    )


def percentual(
    valor: float,
) -> str:
    return (
        f"{valor * 100:.1f}%"
    )


def imprimir_resumo(
    resumos: tuple[
        ResumoModo,
        ...
    ],
) -> None:
    """
    Exibe comparação simples no terminal.
    """
    print()

    print(
        "AVALIAÇÃO DE RECUPERAÇÃO"
    )

    print(
        "=" * 72
    )

    print(
        f"{'Modo':<14}"
        f"{'Aprovação':>12}"
        f"{'Precision':>12}"
        f"{'Recall':>12}"
        f"{'MRR':>12}"
    )

    print(
        "-" * 72
    )

    for resumo in resumos:
        print(
            f"{resumo.modo:<14}"
            f"{percentual(resumo.taxa_aprovacao):>12}"
            f"{resumo.precision_media:>12.3f}"
            f"{resumo.recall_media:>12.3f}"
            f"{resumo.mrr:>12.3f}"
        )

    print(
        "=" * 72
    )

    print()

    for resumo in resumos:
        falhas = [
            resultado
            for resultado
            in resumo.resultados
            if not resultado.aprovado
        ]

        print(
            f"{resumo.modo}: "
            f"{resumo.aprovados}/{resumo.total} "
            "casos com todos os documentos esperados."
        )

        if not falhas:
            print(
                "  Nenhuma falha de recuperação."
            )

        else:
            for resultado in falhas:
                print(
                    "  "
                    f"{resultado.caso_id}: "
                    f"esperado={resultado.esperados} "
                    f"encontrado={resultado.encontrados}"
                )

        print()


def main() -> int:
    try:
        resumos = executar_comparacao()

    except ValueError as erro:
        print(
            f"Avaliação não concluída: {erro}"
        )

        return 1

    imprimir_resumo(
        resumos
    )

    print(
        "Esta avaliação mede recuperação de documentos. "
        "Ela não mede ainda a qualidade real das respostas "
        "geradas pelo Gemini."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )