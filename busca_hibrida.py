from collections.abc import Callable
from pathlib import Path

from busca import buscar_por_pergunta
from busca_semantica import buscar_semantico
from citacoes import TrechoCandidato


MAX_DOCUMENTOS_HIBRIDOS = 3
MAX_TRECHOS_POR_DOCUMENTO = 4

RRF_K = 60
PESO_PALAVRAS = 1.0
PESO_SEMANTICA = 1.0


ResultadoBusca = tuple[
    Path,
    str,
    list[TrechoCandidato],
]

FuncaoBusca = Callable[
    [
        list[tuple[Path, str]],
        str,
    ],
    list[ResultadoBusca],
]


def _chave_documento(
    arquivo: Path,
) -> str:
    """
    Cria uma chave estável para combinar o mesmo documento
    recuperado por métodos diferentes.
    """
    return str(
        arquivo.resolve()
    ).casefold()


def _validar_trecho(
    trecho,
) -> TrechoCandidato:
    """
    Confirma que o trecho recebido segue o contrato atual
    das buscas.

    A validação fica centralizada para impedir AttributeError
    quando uma busca antiga ou incompatível devolver strings.
    """
    if not isinstance(
        trecho,
        TrechoCandidato,
    ):
        raise ValueError(
            "A busca híbrida recebeu um trecho "
            "em formato incompatível."
        )

    if not isinstance(
        trecho.texto,
        str,
    ):
        raise ValueError(
            "A busca híbrida recebeu um trecho "
            "em formato incompatível."
        )

    return trecho


def _chave_trecho(
    trecho: TrechoCandidato,
) -> tuple:
    """
    Cria uma chave para deduplicação sem usar comparação aproximada.

    Quando existem posições confiáveis, elas fazem parte da chave.
    Caso contrário, o texto exato normalizado apenas por espaços
    é utilizado.
    """
    trecho = _validar_trecho(
        trecho
    )

    texto = " ".join(
        trecho.texto.split()
    )

    if (
        trecho.inicio is not None
        and trecho.fim is not None
    ):
        return (
            "posicao",
            trecho.inicio,
            trecho.fim,
            texto,
        )

    return (
        "texto",
        texto,
    )


def _validar_resultados(
    resultados: list[ResultadoBusca],
) -> None:
    """
    Valida o contrato de uma busca antes de iniciar a fusão.
    """
    for resultado in resultados:
        if (
            not isinstance(
                resultado,
                tuple,
            )
            or len(resultado) != 3
        ):
            raise ValueError(
                "A busca híbrida recebeu um resultado "
                "em formato incompatível."
            )

        arquivo, texto, trechos = (
            resultado
        )

        if not isinstance(
            arquivo,
            Path,
        ):
            raise ValueError(
                "A busca híbrida recebeu um documento "
                "em formato incompatível."
            )

        if not isinstance(
            texto,
            str,
        ):
            raise ValueError(
                "A busca híbrida recebeu um documento "
                "em formato incompatível."
            )

        if not isinstance(
            trechos,
            list,
        ):
            raise ValueError(
                "A busca híbrida recebeu trechos "
                "em formato incompatível."
            )

        for trecho in trechos:
            _validar_trecho(
                trecho
            )


def _adicionar_trechos(
    destino: list[TrechoCandidato],
    novos: list[TrechoCandidato],
    vistos: set[tuple],
    limite: int,
) -> None:
    """
    Acrescenta trechos sem duplicação até o limite configurado.
    """
    for trecho in novos:
        if len(destino) >= limite:
            return

        trecho = _validar_trecho(
            trecho
        )

        chave = _chave_trecho(
            trecho
        )

        if chave in vistos:
            continue

        vistos.add(
            chave
        )

        destino.append(
            trecho
        )


def _pontuar_rrf(
    resultados: list[ResultadoBusca],
    peso: float,
    scores: dict[str, float],
) -> None:
    """
    Soma a contribuição de um ranking usando
    Reciprocal Rank Fusion.

    ranking 1 -> peso / (RRF_K + 1)
    ranking 2 -> peso / (RRF_K + 2)
    etc.
    """
    for posicao, (
        arquivo,
        _,
        _,
    ) in enumerate(
        resultados,
        start=1,
    ):
        chave = _chave_documento(
            arquivo
        )

        scores[chave] = (
            scores.get(
                chave,
                0.0,
            )
            + (
                peso
                / (
                    RRF_K
                    + posicao
                )
            )
        )


def buscar_hibrido(
    documentos: list[
        tuple[Path, str]
    ],
    pergunta: str,
    *,
    busca_palavras: FuncaoBusca = buscar_por_pergunta,
    busca_semantica: FuncaoBusca = buscar_semantico,
    max_documentos: int = MAX_DOCUMENTOS_HIBRIDOS,
    max_trechos_por_documento: int = MAX_TRECHOS_POR_DOCUMENTO,
) -> list[ResultadoBusca]:
    """
    Combina busca por palavras e busca semântica usando RRF.

    O retorno mantém o mesmo contrato das buscas atuais:

        [
            (
                arquivo,
                texto_original,
                [TrechoCandidato, ...],
            ),
            ...
        ]

    Nenhum score de similaridade é apresentado como
    probabilidade ou nível de certeza.
    """
    if not isinstance(
        pergunta,
        str,
    ):
        raise ValueError(
            "A pergunta precisa ser texto."
        )

    if (
        not pergunta.strip()
        or not any(
            caractere.isalnum()
            for caractere in pergunta
        )
    ):
        return []

    if not documentos:
        return []

    if (
        not isinstance(
            max_documentos,
            int,
        )
        or max_documentos < 1
    ):
        raise ValueError(
            "max_documentos precisa ser "
            "um inteiro positivo."
        )

    if (
        not isinstance(
            max_trechos_por_documento,
            int,
        )
        or max_trechos_por_documento < 1
    ):
        raise ValueError(
            "max_trechos_por_documento precisa ser "
            "um inteiro positivo."
        )

    resultados_palavras = (
        busca_palavras(
            documentos,
            pergunta,
        )
    )

    resultados_semanticos = (
        busca_semantica(
            documentos,
            pergunta,
        )
    )

    _validar_resultados(
        resultados_palavras
    )

    _validar_resultados(
        resultados_semanticos
    )

    if (
        not resultados_palavras
        and not resultados_semanticos
    ):
        return []

    scores: dict[
        str,
        float,
    ] = {}

    _pontuar_rrf(
        resultados_palavras,
        PESO_PALAVRAS,
        scores,
    )

    _pontuar_rrf(
        resultados_semanticos,
        PESO_SEMANTICA,
        scores,
    )

    documentos_por_chave = {}

    for origem, resultados in (
        (
            "palavras",
            resultados_palavras,
        ),
        (
            "semantica",
            resultados_semanticos,
        ),
    ):
        for arquivo, texto, trechos in resultados:
            chave = _chave_documento(
                arquivo
            )

            if chave not in documentos_por_chave:
                documentos_por_chave[
                    chave
                ] = {
                    "arquivo": arquivo,
                    "texto": texto,
                    "palavras": [],
                    "semantica": [],
                }

            registro = (
                documentos_por_chave[
                    chave
                ]
            )

            if registro[
                "texto"
            ] != texto:
                raise ValueError(
                    "A base mudou durante a busca híbrida. "
                    "Repita a consulta."
                )

            registro[
                origem
            ].extend(
                trechos
            )

    ordem = sorted(
        documentos_por_chave,
        key=lambda chave: (
            -scores.get(
                chave,
                0.0,
            ),
            documentos_por_chave[
                chave
            ][
                "arquivo"
            ].name.casefold(),
            chave,
        ),
    )

    resultados_finais: list[
        ResultadoBusca
    ] = []

    for chave in ordem[
        :max_documentos
    ]:
        registro = (
            documentos_por_chave[
                chave
            ]
        )

        trechos: list[
            TrechoCandidato
        ] = []

        vistos: set[
            tuple
        ] = set()

        chaves_palavras = {
            _chave_trecho(
                trecho
            )
            for trecho
            in registro[
                "palavras"
            ]
        }

        chaves_semantica = {
            _chave_trecho(
                trecho
            )
            for trecho
            in registro[
                "semantica"
            ]
        }

        chaves_comuns = (
            chaves_palavras
            & chaves_semantica
        )

        comuns = [
            trecho
            for trecho
            in registro[
                "palavras"
            ]
            if _chave_trecho(
                trecho
            )
            in chaves_comuns
        ]

        _adicionar_trechos(
            trechos,
            comuns,
            vistos,
            max_trechos_por_documento,
        )

        _adicionar_trechos(
            trechos,
            registro[
                "palavras"
            ],
            vistos,
            max_trechos_por_documento,
        )

        _adicionar_trechos(
            trechos,
            registro[
                "semantica"
            ],
            vistos,
            max_trechos_por_documento,
        )

        if not trechos:
            continue

        resultados_finais.append(
            (
                registro[
                    "arquivo"
                ],
                registro[
                    "texto"
                ],
                trechos,
            )
        )

    return resultados_finais