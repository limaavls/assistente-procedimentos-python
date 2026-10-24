import re
from pathlib import Path

from app import TAMANHO_MINIMO_DO_TERMO, normalizar


# Palavras que, sozinhas, ajudam pouco nesta busca simples.
PALAVRAS_COMUNS = set(
    (
        "a ao aos as o os um uma uns umas de da das do dos "
        "e em no na nos nas para por que qual quais como onde quando "
        "quem eu voce voces me meu minha posso preciso devo gostaria saber"
    ).split()
)


def extrair_palavras(texto: str) -> set[str]:
    """Separa palavras, normaliza e elimina repetições e termos comuns."""
    palavras = re.findall(r"\b\w+\b", normalizar(texto))

    return {
        palavra
        for palavra in palavras
        if len(palavra) >= TAMANHO_MINIMO_DO_TERMO
        and palavra not in PALAVRAS_COMUNS
    }


def buscar_por_pergunta(
    documentos: list[tuple[Path, str]],
    pergunta: str,
) -> list[tuple[Path, str, list[str]]]:
    """Ordena documentos pela quantidade de palavras distintas em comum."""
    palavras = extrair_palavras(pergunta)

    if not palavras:
        return []

    classificados: list[tuple[int, Path, str, list[str]]] = []

    for arquivo, texto in documentos:
        pontos = len(palavras & extrair_palavras(texto))

        if pontos == 0:
            continue

        # Uma linha vazia separa os parágrafos.
        # O conteúdo original é preservado.
        paragrafos = re.split(r"\n\s*\n", texto.strip())

        trechos = [
            paragrafo.strip()
            for paragrafo in paragrafos
            if palavras & extrair_palavras(paragrafo)
        ]

        classificados.append((pontos, arquivo, texto, trechos))

    # Mais palavras em comum primeiro; nome do arquivo desempata.
    classificados.sort(
        key=lambda item: (-item[0], item[1].name.casefold())
    )

    return [
        (arquivo, texto, trechos)
        for _, arquivo, texto, trechos in classificados
    ]