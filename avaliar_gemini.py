import argparse
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import httpx
from dotenv import dotenv_values
from google.genai import errors

from avaliacao import (
    CasoAvaliacao,
    ResultadoCaso,
    ResumoAvaliacao,
    avaliar_caso,
    resumir_resultados,
)
from busca import buscar_por_pergunta
from busca_hibrida import buscar_hibrido
from busca_semantica import buscar_semantico
from casos_avaliacao import (
    CASOS_AVALIACAO,
    DOCUMENTOS_AVALIACAO,
)
from citacoes import ApresentacaoResposta
from consulta_ia import (
    MODELO_PADRAO,
    gerar_resposta,
    preparar_pacote,
)


BASE = Path(__file__).resolve().parent

PASTA_RESULTADOS = (
    BASE
    / ".avaliacoes"
)


FuncaoBusca = Callable[
    [
        list[tuple[Path, str]],
        str,
    ],
    list[tuple],
]


MODOS_BUSCA = {
    "palavras": buscar_por_pergunta,
    "semantica": buscar_semantico,
    "hibrida": buscar_hibrido,
}


@dataclass(frozen=True)
class RegistroExecucao:
    caso_id: str
    modo: str
    pergunta: str

    documentos_encontrados: tuple[str, ...]
    documentos_citados: tuple[str, ...]

    status: str | None
    texto_resposta: str

    aprovado: bool | None

    tipo_resultado: str
    erro: str | None = None


@dataclass(frozen=True)
class ResultadoModoReal:
    modo: str

    total_planejado: int
    avaliados: int
    falhas_operacionais: int

    resumo: ResumoAvaliacao | None

    execucoes: tuple[
        RegistroExecucao,
        ...
    ]


def nomes_documentos(
    resultados: list[tuple],
) -> tuple[str, ...]:
    """
    Obtém os nomes dos documentos preservando
    a ordem de recuperação.
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


def texto_da_apresentacao(
    apresentacao: ApresentacaoResposta,
) -> str:
    """
    Produz o texto utilizado pela avaliação automática.
    """
    if apresentacao.linhas_itens:
        return "\n".join(
            apresentacao.linhas_itens
        )

    return (
        apresentacao.mensagem_principal
        or ""
    )


def documentos_citados(
    apresentacao: ApresentacaoResposta,
) -> tuple[str, ...]:
    """
    Obtém documentos realmente citados
    pela resposta validada.
    """
    nomes = []
    vistos = set()

    for fonte in (
        apresentacao.fontes_citadas
    ):
        chave = (
            fonte.documento
            .casefold()
        )

        if chave in vistos:
            continue

        vistos.add(
            chave
        )

        nomes.append(
            fonte.documento
        )

    return tuple(
        nomes
    )


def resultado_de_falha_qualidade(
    caso: CasoAvaliacao,
    modo: str,
    documentos_encontrados: tuple[str, ...],
    mensagem: str,
) -> tuple[
    ResultadoCaso,
    RegistroExecucao,
]:
    """
    Registra uma falha que pertence à qualidade
    avaliada do sistema.

    Exemplos:
    - nenhum documento correto recuperado;
    - resposta inválida;
    - citação rejeitada;
    - resposta sem evidência quando deveria responder.

    Esse caso entra no denominador da taxa de aprovação.
    """
    resultado = avaliar_caso(
        caso,
        documentos_encontrados=(
            documentos_encontrados
        ),
        texto_resposta="",
        documentos_citados=(),
        citacoes_validas=False,
        status_obtido=None,
    )

    registro = RegistroExecucao(
        caso_id=caso.identificador,
        modo=modo,
        pergunta=caso.pergunta,
        documentos_encontrados=(
            documentos_encontrados
        ),
        documentos_citados=(),
        status=None,
        texto_resposta="",
        aprovado=False,
        tipo_resultado="qualidade",
        erro=mensagem,
    )

    return (
        resultado,
        registro,
    )


def resultado_de_falha_operacional(
    caso: CasoAvaliacao,
    modo: str,
    documentos_encontrados: tuple[str, ...],
    mensagem: str,
) -> tuple[
    None,
    RegistroExecucao,
]:
    """
    Registra uma falha operacional.

    Exemplos:
    - rate limit 429;
    - falha de conexão;
    - indisponibilidade da API;
    - erro técnico da busca.

    Esses casos NÃO entram no denominador da
    taxa de aprovação de qualidade.
    """
    registro = RegistroExecucao(
        caso_id=caso.identificador,
        modo=modo,
        pergunta=caso.pergunta,
        documentos_encontrados=(
            documentos_encontrados
        ),
        documentos_citados=(),
        status=None,
        texto_resposta="",
        aprovado=None,
        tipo_resultado="operacional",
        erro=mensagem,
    )

    return (
        None,
        registro,
    )


def executar_caso(
    caso: CasoAvaliacao,
    *,
    modo: str,
    funcao_busca: FuncaoBusca,
    chave: str,
    modelo: str,
    documentos=DOCUMENTOS_AVALIACAO,
) -> tuple[
    ResultadoCaso | None,
    RegistroExecucao,
]:
    """
    Executa um caso completo:

    busca
      ↓
    preparação das fontes
      ↓
    Gemini
      ↓
    validação local das citações
      ↓
    avaliação automática

    Falhas operacionais são separadas das
    reprovações de qualidade.
    """
    try:
        resultados = funcao_busca(
            documentos,
            caso.pergunta,
        )

    except Exception as erro:
        return resultado_de_falha_operacional(
            caso,
            modo,
            (),
            (
                "Falha operacional na busca: "
                f"{type(erro).__name__}: {erro}"
            ),
        )

    encontrados = nomes_documentos(
        resultados
    )

    if not resultados:
        return resultado_de_falha_qualidade(
            caso,
            modo,
            encontrados,
            (
                "Nenhum documento candidato "
                "foi recuperado."
            ),
        )

    try:
        pacote = preparar_pacote(
            resultados
        )

    except ValueError as erro:
        return resultado_de_falha_operacional(
            caso,
            modo,
            encontrados,
            (
                "Falha ao preparar os trechos: "
                f"{erro}"
            ),
        )

    try:
        apresentacao = gerar_resposta(
            caso.pergunta,
            pacote,
            chave,
            modelo,
        )

    except errors.APIError as erro:
        return resultado_de_falha_operacional(
            caso,
            modo,
            encontrados,
            (
                "Erro da API "
                f"({erro.code})."
            ),
        )

    except httpx.HTTPError as erro:
        return resultado_de_falha_operacional(
            caso,
            modo,
            encontrados,
            (
                "Falha de conexão: "
                f"{type(erro).__name__}."
            ),
        )

    except ValueError as erro:
        # Uma resposta inválida produzida pelo modelo
        # é considerada falha de qualidade.
        return resultado_de_falha_qualidade(
            caso,
            modo,
            encontrados,
            (
                "Resposta reprovada pela validação: "
                f"{erro}"
            ),
        )

    except Exception as erro:
        return resultado_de_falha_operacional(
            caso,
            modo,
            encontrados,
            (
                "Falha operacional inesperada: "
                f"{type(erro).__name__}: {erro}"
            ),
        )

    texto = texto_da_apresentacao(
        apresentacao
    )

    citados = documentos_citados(
        apresentacao
    )

    # Se gerar_resposta() retornou uma apresentação,
    # a estrutura e as citações já passaram pela
    # validação local do projeto.
    resultado = avaliar_caso(
        caso,
        documentos_encontrados=encontrados,
        texto_resposta=texto,
        documentos_citados=citados,
        citacoes_validas=True,
        status_obtido=(
            apresentacao.status
        ),
    )

    registro = RegistroExecucao(
        caso_id=caso.identificador,
        modo=modo,
        pergunta=caso.pergunta,
        documentos_encontrados=(
            encontrados
        ),
        documentos_citados=(
            citados
        ),
        status=apresentacao.status,
        texto_resposta=texto,
        aprovado=resultado.aprovado,
        tipo_resultado="qualidade",
        erro=None,
    )

    return (
        resultado,
        registro,
    )


def executar_modo(
    modo: str,
    funcao_busca: FuncaoBusca,
    *,
    chave: str,
    modelo: str,
    casos=CASOS_AVALIACAO,
    documentos=DOCUMENTOS_AVALIACAO,
) -> ResultadoModoReal:
    """
    Executa todos os casos de um modo.

    Apenas casos realmente avaliados entram nas
    métricas de qualidade.

    Falhas operacionais são contadas separadamente.
    """
    resultados_avaliados = []
    registros = []

    for numero, caso in enumerate(
        casos,
        start=1,
    ):
        print(
            f"[{modo}] "
            f"{numero}/{len(casos)} "
            f"{caso.identificador}",
            flush=True,
        )

        resultado, registro = (
            executar_caso(
                caso,
                modo=modo,
                funcao_busca=(
                    funcao_busca
                ),
                chave=chave,
                modelo=modelo,
                documentos=documentos,
            )
        )

        registros.append(
            registro
        )

        if resultado is not None:
            resultados_avaliados.append(
                resultado
            )

    total_planejado = len(
        casos
    )

    avaliados = len(
        resultados_avaliados
    )

    falhas_operacionais = (
        total_planejado
        - avaliados
    )

    resumo = (
        resumir_resultados(
            resultados_avaliados
        )
        if resultados_avaliados
        else None
    )

    return ResultadoModoReal(
        modo=modo,
        total_planejado=(
            total_planejado
        ),
        avaliados=avaliados,
        falhas_operacionais=(
            falhas_operacionais
        ),
        resumo=resumo,
        execucoes=tuple(
            registros
        ),
    )


def selecionar_modos(
    valor: str,
) -> dict[
    str,
    FuncaoBusca,
]:
    """
    Converte a opção de terminal em funções de busca.
    """
    if valor == "todos":
        return dict(
            MODOS_BUSCA
        )

    if valor not in MODOS_BUSCA:
        raise ValueError(
            "Modo de avaliação inválido."
        )

    return {
        valor: MODOS_BUSCA[
            valor
        ]
    }


def limitar_casos(
    limite: int | None,
):
    """
    Permite uma execução curta antes
    do benchmark completo.
    """
    if limite is None:
        return tuple(
            CASOS_AVALIACAO
        )

    if (
        not isinstance(
            limite,
            int,
        )
        or limite < 1
    ):
        raise ValueError(
            "O limite precisa ser "
            "um inteiro positivo."
        )

    return tuple(
        CASOS_AVALIACAO[
            :limite
        ]
    )


def percentual(
    valor: float,
) -> str:
    return (
        f"{valor * 100:.1f}%"
    )


def valor_ou_na(
    valor: float | None,
    *,
    percentual_valor: bool = False,
) -> str:
    """
    Formata métricas opcionais.
    """
    if valor is None:
        return "N/A"

    if percentual_valor:
        return percentual(
            valor
        )

    return (
        f"{valor:.3f}"
    )


def imprimir_resumos(
    resultados: tuple[
        ResultadoModoReal,
        ...
    ],
) -> None:
    """
    Mostra a comparação final no terminal.

    Falhas operacionais aparecem separadas
    das métricas de qualidade.
    """
    print()

    print(
        "AVALIAÇÃO REAL COM GEMINI"
    )

    print(
        "=" * 118
    )

    print(
        f"{'Modo':<12}"
        f"{'Planej.':>9}"
        f"{'Aval.':>8}"
        f"{'Oper.':>8}"
        f"{'Aprovação':>12}"
        f"{'Precision':>12}"
        f"{'Recall':>10}"
        f"{'MRR':>10}"
        f"{'Citações':>12}"
        f"{'Conteúdo':>12}"
    )

    print(
        "-" * 118
    )

    for resultado in resultados:
        resumo = resultado.resumo

        print(
            f"{resultado.modo:<12}"
            f"{resultado.total_planejado:>9}"
            f"{resultado.avaliados:>8}"
            f"{resultado.falhas_operacionais:>8}"
            f"{valor_ou_na(
                resumo.taxa_aprovacao
                if resumo
                else None,
                percentual_valor=True,
            ):>12}"
            f"{valor_ou_na(
                resumo.precision_media
                if resumo
                else None
            ):>12}"
            f"{valor_ou_na(
                resumo.recall_media
                if resumo
                else None
            ):>10}"
            f"{valor_ou_na(
                resumo.mrr
                if resumo
                else None
            ):>10}"
            f"{valor_ou_na(
                resumo.taxa_citacoes_validas
                if resumo
                else None,
                percentual_valor=True,
            ):>12}"
            f"{valor_ou_na(
                resumo.taxa_conteudo_valido
                if resumo
                else None,
                percentual_valor=True,
            ):>12}"
        )

    print(
        "=" * 118
    )

    for resultado in resultados:
        print()

        print(
            f"{resultado.modo}:"
        )

        print(
            "  Casos planejados: "
            f"{resultado.total_planejado}"
        )

        print(
            "  Casos avaliados: "
            f"{resultado.avaliados}"
        )

        print(
            "  Falhas operacionais: "
            f"{resultado.falhas_operacionais}"
        )

        if resultado.resumo is not None:
            print(
                "  Aprovados entre os avaliados: "
                f"{resultado.resumo.aprovados}/"
                f"{resultado.resumo.total}"
            )

        falhas_qualidade = [
            item
            for item
            in resultado.execucoes
            if (
                item.tipo_resultado
                == "qualidade"
                and item.aprovado is False
            )
        ]

        falhas_operacionais = [
            item
            for item
            in resultado.execucoes
            if (
                item.tipo_resultado
                == "operacional"
            )
        ]

        if falhas_qualidade:
            print(
                "  Falhas de qualidade:"
            )

            for falha in (
                falhas_qualidade
            ):
                print(
                    f"    {falha.caso_id}"
                )

                if falha.erro:
                    print(
                        "      "
                        f"{falha.erro}"
                    )

                else:
                    print(
                        "      documentos encontrados:",
                        falha.documentos_encontrados,
                    )

                    print(
                        "      documentos citados:",
                        falha.documentos_citados,
                    )

                    print(
                        "      status:",
                        falha.status,
                    )

        if falhas_operacionais:
            print(
                "  Falhas operacionais:"
            )

            for falha in (
                falhas_operacionais
            ):
                print(
                    f"    {falha.caso_id}: "
                    f"{falha.erro}"
                )

        if (
            not falhas_qualidade
            and not falhas_operacionais
        ):
            print(
                "  Nenhuma falha."
            )


def salvar_resultados(
    resultados: tuple[
        ResultadoModoReal,
        ...
    ],
    *,
    modelo: str,
) -> Path:
    """
    Salva resultados locais em JSON.

    A chave da API nunca é gravada.
    """
    PASTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    momento = datetime.now(
        timezone.utc
    )

    caminho = (
        PASTA_RESULTADOS
        / (
            "avaliacao_gemini_"
            + momento.strftime(
                "%Y%m%dT%H%M%SZ"
            )
            + ".json"
        )
    )

    dados = {
        "executado_em_utc": (
            momento.isoformat()
        ),
        "modelo": modelo,
        "resultados": [
            asdict(
                resultado
            )
            for resultado
            in resultados
        ],
    }

    caminho.write_text(
        json.dumps(
            dados,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return caminho


def carregar_configuracao():
    """
    Lê apenas a configuração necessária.

    A chave não é exibida nem salva.
    """
    config = dotenv_values(
        BASE
        / ".env"
    )

    chave = (
        os.getenv(
            "GEMINI_API_KEY"
        )
        or config.get(
            "GEMINI_API_KEY"
        )
        or ""
    ).strip()

    modelo = (
        os.getenv(
            "GEMINI_MODEL"
        )
        or config.get(
            "GEMINI_MODEL"
        )
        or MODELO_PADRAO
    ).strip() or MODELO_PADRAO

    if (
        not chave
        or chave
        == "COLE_SUA_CHAVE_AQUI"
    ):
        raise ValueError(
            "Configure GEMINI_API_KEY no .env."
        )

    return (
        chave,
        modelo,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Avaliação opcional do assistente "
            "com documentos exclusivamente fictícios."
        )
    )

    parser.add_argument(
        "--modo",
        choices=[
            "palavras",
            "semantica",
            "hibrida",
            "todos",
        ],
        default="hibrida",
        help=(
            "Modo a avaliar. "
            "O padrão é hibrida."
        ),
    )

    parser.add_argument(
        "--limite",
        type=int,
        default=None,
        help=(
            "Executa somente os primeiros N casos. "
            "Útil para teste curto."
        ),
    )

    args = parser.parse_args()

    try:
        modos = selecionar_modos(
            args.modo
        )

        casos = limitar_casos(
            args.limite
        )

        chave, modelo = (
            carregar_configuracao()
        )

    except ValueError as erro:
        print(
            f"Configuração inválida: {erro}"
        )

        return 1

    chamadas = (
        len(modos)
        * len(casos)
    )

    print()

    print(
        "AVALIAÇÃO OPCIONAL COM GEMINI"
    )

    print(
        "=" * 60
    )

    print(
        f"Modelo: {modelo}"
    )

    print(
        "Modos:",
        ", ".join(
            modos.keys()
        ),
    )

    print(
        f"Casos por modo: {len(casos)}"
    )

    print(
        f"Máximo de chamadas ao Gemini: {chamadas}"
    )

    print()

    print(
        "Serão enviados somente os documentos "
        "fictícios definidos em casos_avaliacao.py."
    )

    print(
        "Nenhum arquivo da pasta documentos/ "
        "é utilizado por esta avaliação."
    )

    print()

    confirmacao = input(
        "Digite SIM para autorizar essas chamadas: "
    ).strip().upper()

    if confirmacao != "SIM":
        print(
            "Avaliação cancelada. "
            "Nenhuma chamada ao Gemini foi realizada."
        )

        return 0

    resultados = []

    for nome, funcao in (
        modos.items()
    ):
        resultado = executar_modo(
            nome,
            funcao,
            chave=chave,
            modelo=modelo,
            casos=casos,
        )

        resultados.append(
            resultado
        )

    resultados = tuple(
        resultados
    )

    imprimir_resumos(
        resultados
    )

    caminho = salvar_resultados(
        resultados,
        modelo=modelo,
    )

    print()

    print(
        "Resultado salvo localmente em:"
    )

    print(
        caminho
    )

    print()

    print(
        "Falhas operacionais, como rate limit e conexão, "
        "são registradas separadamente e não reduzem "
        "a taxa de aprovação de qualidade."
    )

    print()

    print(
        "A avaliação automática é baseada em "
        "expectativas definidas manualmente. "
        "Ela não constitui prova absoluta de qualidade."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )