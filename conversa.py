import json


def montar_consulta(
    pergunta: str, historico: list[dict[str, str]]
) -> tuple[str, str]:
    """Prepara a busca e o pedido ao modelo sem reutilizar respostas da IA."""
    pergunta = pergunta.strip()

    if (
        not pergunta
        or len(pergunta) > 500
        or not any(caractere.isalnum() for caractere in pergunta)
    ):
        raise ValueError(
            "Digite uma pergunta com texto e até 500 caracteres."
        )

    anteriores = []

    if historico:
        # Preserva o assunto inicial e a pergunta respondida mais recente.
        for turno in (historico[0], historico[-1]):
            texto = turno["pergunta"]

            if texto not in anteriores:
                anteriores.append(texto)

    texto_busca = " ".join(anteriores + [pergunta])

    dados = {
        "perguntas_anteriores_para_identificar_assunto": anteriores,
        "pergunta_atual": pergunta,
    }

    pedido = (
        "Responda somente à pergunta atual. As perguntas anteriores ajudam "
        "a identificar o assunto, mas não comprovam fatos. Use somente os "
        "trechos dos documentos como fonte. Se faltar informação, diga isso.\n"
        + json.dumps(dados, ensure_ascii=False)
    )

    return texto_busca, pedido