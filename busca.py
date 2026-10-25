import re
from pathlib import Path

from app import TAMANHO_MINIMO_DO_TERMO, normalizar
from citacoes import TrechoCandidato


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


def _trechos_com_posicao(
    texto: str, palavras: set[str]
) -> list[TrechoCandidato]:
    """Recorta parágrafos e guarda a posição de cada um no texto original."""
    corpo = texto.strip()
    base = texto.find(corpo)
    if base < 0:
        base = 0
        corpo = texto

    paragrafos = re.split(r"\n\s*\n", corpo)
    cursor = 0
    trechos: list[TrechoCandidato] = []

    for paragrafo in paragrafos:
        posicao = corpo.find(paragrafo, cursor)
        if posicao >= 0:
            cursor = posicao + len(paragrafo)

        if not (palavras & extrair_palavras(paragrafo)):
            continue

        limpo = paragrafo.strip()
        if not limpo:
            continue

        inicio = None
        fim = None
        if posicao >= 0:
            deslocamento = paragrafo.find(limpo)
            candidato = base + posicao + max(deslocamento, 0)
            termino = candidato + len(limpo)
            if texto[candidato:termino] == limpo:
                inicio = candidato
                fim = termino

        trechos.append(
            TrechoCandidato(texto=limpo, inicio=inicio, fim=fim)
        )

    return trechos


def buscar_por_pergunta(
    documentos: list[tuple[Path, str]],
    pergunta: str,
) -> list[tuple[Path, str, list[TrechoCandidato]]]:
    """Ordena documentos pela quantidade de palavras distintas em comum."""
    palavras = extrair_palavras(pergunta)

    if not palavras:
        return []

    classificados: list[
        tuple[int, Path, str, list[TrechoCandidato]]
    ] = []

    for arquivo, texto in documentos:
        pontos = len(palavras & extrair_palavras(texto))

        if pontos == 0:
            continue

        trechos = _trechos_com_posicao(texto, palavras)
        classificados.append((pontos, arquivo, texto, trechos))

    # Mais palavras em comum primeiro; nome do arquivo desempata.
    classificados.sort(
        key=lambda item: (-item[0], item[1].name.casefold())
    )

    return [
        (arquivo, texto, trechos)
        for _, arquivo, texto, trechos in classificados
    ]