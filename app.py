import re
import unicodedata
from pathlib import Path

# Uma linha antes e uma depois da ocorrência (até 3 linhas no total).
LINHAS_DE_CONTEXTO = 1
TAMANHO_MINIMO_DO_TERMO = 2


def normalizar(texto: str) -> str:
    """Ignora maiúsculas/minúsculas e acentos (solicitação = solicitacao)."""
    decomposto = unicodedata.normalize("NFD", texto)
    sem_acento = "".join(
        caractere
        for caractere in decomposto
        if unicodedata.category(caractere) != "Mn"
    )
    return sem_acento.casefold()


def carregar_documentos(pasta: Path) -> list[tuple[Path, str]]:
    documentos: list[tuple[Path, str]] = []

    for arquivo in sorted(pasta.glob("*.txt")):
        try:
            texto = arquivo.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as erro:
            print(f"Não foi possível ler {arquivo.name}: {erro}")
            continue

        if texto.strip():
            documentos.append((arquivo, texto))

    return documentos


def padrao_de_palavra(termo: str) -> re.Pattern[str]:
    # \b evita que "mat" encontre "material".
    return re.compile(r"\b" + re.escape(normalizar(termo)) + r"\b")


def trechos_com_termo(texto: str, termo: str) -> list[str]:
    """Mostra ocorrências com contexto, sem repetir linhas sobrepostas."""
    padrao = padrao_de_palavra(termo)
    linhas = texto.splitlines()
    faixas: list[tuple[int, int]] = []

    for indice, linha in enumerate(linhas):
        if not padrao.search(normalizar(linha)):
            continue

        inicio = max(0, indice - LINHAS_DE_CONTEXTO)
        fim = min(len(linhas), indice + LINHAS_DE_CONTEXTO + 1)

        # Junta trechos que compartilham uma ou mais linhas.
        if faixas and inicio < faixas[-1][1]:
            inicio_anterior, fim_anterior = faixas[-1]
            faixas[-1] = (inicio_anterior, max(fim_anterior, fim))
        else:
            faixas.append((inicio, fim))

    trechos: list[str] = []

    for inicio, fim in faixas:
        trechos.append("\n".join(linhas[inicio:fim]))

    return trechos


def main() -> None:
    pasta = Path(__file__).resolve().parent / "documentos"
    documentos = carregar_documentos(pasta)

    if not documentos:
        print("Não encontrei documentos .txt na pasta documentos.")
        return

    termo = input("Digite um termo para buscar (ex.: material): ").strip()

    if not termo:
        print("Digite pelo menos uma palavra.")
        return

    if len(normalizar(termo)) < TAMANHO_MINIMO_DO_TERMO:
        print(
            f"Digite um termo com pelo menos {TAMANHO_MINIMO_DO_TERMO} caracteres."
        )
        return

    encontrou = False
    for arquivo, texto in documentos:
        trechos = trechos_com_termo(texto, termo)
        if not trechos:
            continue

        encontrou = True
        print(f"\nFonte: {arquivo.name}")
        for trecho in trechos:
            print()
            print(trecho)

    if not encontrou:
        print("Não encontrei esse termo nos documentos consultados.")


if __name__ == "__main__":
    main()
