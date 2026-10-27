from dataclasses import dataclass
from statistics import mean

from avaliacao import (
    ResultadoCaso,
    avaliar_caso,
    resumir_resultados,
)
from casos_avaliacao import (
    CASOS_AVALIACAO,
)


@dataclass(frozen=True)
class RespostaControlada:
    """
    Resposta fictícia usada para validar o mecanismo
    de avaliação sem chamar uma IA real.
    """

    texto: str
    documentos_encontrados: tuple[str, ...]
    documentos_citados: tuple[str, ...]
    citacoes_validas: bool
    status: str


RESPOSTAS_CONTROLADAS = {
    "material_001": RespostaControlada(
        texto=(
            "Informe o setor solicitante, a descrição do item "
            "e a quantidade necessária. "
            "Encaminhe a solicitação ao setor de Compras."
        ),
        documentos_encontrados=(
            "material.txt",
        ),
        documentos_citados=(
            "material.txt",
        ),
        citacoes_validas=True,
        status="respondida",
    ),
    "material_002": RespostaControlada(
        texto=(
            "A solicitação deve informar o setor, "
            "a descrição e a quantidade."
        ),
        documentos_encontrados=(
            "material.txt",
        ),
        documentos_citados=(
            "material.txt",
        ),
        citacoes_validas=True,
        status="respondida",
    ),
    "frequencia_001": RespostaControlada(
        texto=(
            "Informe a data da ocorrência, o horário correto "
            "e a justificativa. Encaminhe ao RH."
        ),
        documentos_encontrados=(
            "frequencia.txt",
        ),
        documentos_citados=(
            "frequencia.txt",
        ),
        citacoes_validas=True,
        status="respondida",
    ),
    "frequencia_002": RespostaControlada(
        texto=(
            "Informe a data, o horário correto "
            "e a justificativa."
        ),
        documentos_encontrados=(
            "frequencia.txt",
        ),
        documentos_citados=(
            "frequencia.txt",
        ),
        citacoes_validas=True,
        status="respondida",
    ),
    "reembolso_001": RespostaControlada(
        texto=(
            "Apresente a nota fiscal, o comprovante de pagamento "
            "e a justificativa da despesa."
        ),
        documentos_encontrados=(
            "reembolso.txt",
        ),
        documentos_citados=(
            "reembolso.txt",
        ),
        citacoes_validas=True,
        status="respondida",
    ),
    "reembolso_002": RespostaControlada(
        texto=(
            "O pedido deve conter nota fiscal e comprovante "
            "de pagamento e deve ser encaminhado ao Financeiro."
        ),
        documentos_encontrados=(
            "reembolso.txt",
        ),
        documentos_citados=(
            "reembolso.txt",
        ),
        citacoes_validas=True,
        status="respondida",
    ),
    "ferias_001": RespostaControlada(
        texto=(
            "Informe o período desejado e encaminhe o pedido "
            "ao gestor. Depois da aprovação, o RH processa "
            "a solicitação."
        ),
        documentos_encontrados=(
            "ferias.txt",
        ),
        documentos_citados=(
            "ferias.txt",
        ),
        citacoes_validas=True,
        status="respondida",
    ),
    "ferias_002": RespostaControlada(
        texto=(
            "O gestor responsável precisa aprovar "
            "o pedido de férias."
        ),
        documentos_encontrados=(
            "ferias.txt",
        ),
        documentos_citados=(
            "ferias.txt",
        ),
        citacoes_validas=True,
        status="respondida",
    ),
    "acesso_001": RespostaControlada(
        texto=(
            "Informe o nome do usuário, o setor, o perfil "
            "necessário e a justificativa. "
            "Encaminhe a solicitação à equipe de TI."
        ),
        documentos_encontrados=(
            "acesso.txt",
        ),
        documentos_citados=(
            "acesso.txt",
        ),
        citacoes_validas=True,
        status="respondida",
    ),
    "acesso_002": RespostaControlada(
        texto=(
            "Informe o nome do usuário, o setor, "
            "o perfil de acesso e a justificativa."
        ),
        documentos_encontrados=(
            "acesso.txt",
        ),
        documentos_citados=(
            "acesso.txt",
        ),
        citacoes_validas=True,
        status="respondida",
    ),
    "equipamento_001": RespostaControlada(
        texto=(
            "Informe o patrimônio, o responsável pela retirada "
            "e a data prevista para devolução."
        ),
        documentos_encontrados=(
            "equipamento.txt",
        ),
        documentos_citados=(
            "equipamento.txt",
        ),
        citacoes_validas=True,
        status="respondida",
    ),
    "equipamento_002": RespostaControlada(
        texto=(
            "Registre o patrimônio, o responsável pela retirada "
            "e a data prevista para devolução."
        ),
        documentos_encontrados=(
            "equipamento.txt",
        ),
        documentos_citados=(
            "equipamento.txt",
        ),
        citacoes_validas=True,
        status="respondida",
    ),
}


def avaliar_respostas(
    respostas=None,
    casos=None,
):
    """
    Avalia respostas controladas usando os mesmos critérios
    que futuramente poderão ser aplicados às respostas reais.
    """
    if respostas is None:
        respostas = RESPOSTAS_CONTROLADAS

    if casos is None:
        casos = CASOS_AVALIACAO

    resultados = []

    for caso in casos:
        resposta = respostas.get(
            caso.identificador
        )

        if resposta is None:
            raise ValueError(
                "Não existe resposta controlada para "
                f"{caso.identificador}."
            )

        if not isinstance(
            resposta,
            RespostaControlada,
        ):
            raise ValueError(
                "Resposta controlada em formato inválido."
            )

        resultados.append(
            avaliar_caso(
                caso,
                documentos_encontrados=(
                    resposta.documentos_encontrados
                ),
                texto_resposta=resposta.texto,
                documentos_citados=(
                    resposta.documentos_citados
                ),
                citacoes_validas=(
                    resposta.citacoes_validas
                ),
                status_obtido=(
                    resposta.status
                ),
            )
        )

    return resumir_resultados(
        resultados
    )


def percentual(
    valor: float,
) -> str:
    return (
        f"{valor * 100:.1f}%"
    )


def imprimir_resultado(
    resumo,
) -> None:
    print()

    print(
        "AVALIAÇÃO CONTROLADA DE RESPOSTAS"
    )

    print(
        "=" * 72
    )

    print(
        f"Casos: {resumo.total}"
    )

    print(
        "Aprovados: "
        f"{resumo.aprovados}"
    )

    print(
        "Reprovados: "
        f"{resumo.reprovados}"
    )

    print(
        "Taxa de aprovação: "
        f"{percentual(resumo.taxa_aprovacao)}"
    )

    print(
        "Recall de documentos: "
        f"{resumo.recall_media:.3f}"
    )

    print(
        "MRR: "
        f"{resumo.mrr:.3f}"
    )

    print(
        "Citações válidas: "
        f"{percentual(resumo.taxa_citacoes_validas)}"
    )

    print(
        "Conteúdo válido: "
        f"{percentual(resumo.taxa_conteudo_valido)}"
    )

    print(
        "Status válido: "
        f"{percentual(resumo.taxa_status_valido)}"
    )

    print(
        "=" * 72
    )

    falhas = [
        resultado
        for resultado
        in resumo.resultados
        if not resultado.aprovado
    ]

    if not falhas:
        print(
            "Todos os casos controlados foram aprovados."
        )

    else:
        print(
            "Falhas:"
        )

        for resultado in falhas:
            print()
            print(
                resultado.identificador
            )

            if (
                resultado.termos_obrigatorios_ausentes
            ):
                print(
                    "  Termos obrigatórios ausentes:",
                    resultado.termos_obrigatorios_ausentes,
                )

            if (
                resultado.termos_proibidos_encontrados
            ):
                print(
                    "  Termos proibidos encontrados:",
                    resultado.termos_proibidos_encontrados,
                )

            if not resultado.citacoes_validas:
                print(
                    "  Citações inválidas."
                )

            if not resultado.status_valido:
                print(
                    "  Status obtido:",
                    resultado.status_obtido,
                    "esperado:",
                    resultado.status_esperado,
                )


def main() -> int:
    try:
        resumo = avaliar_respostas()

    except ValueError as erro:
        print(
            f"Avaliação não concluída: {erro}"
        )

        return 1

    imprimir_resultado(
        resumo
    )

    print()
    print(
        "Esta execução utiliza respostas controladas "
        "e não chama Gemini."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )