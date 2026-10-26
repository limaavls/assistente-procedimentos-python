import hashlib
import re
import unicodedata
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from docx import Document
from docx.text.paragraph import Paragraph
from pypdf import PdfReader

from ocr import (
    ErroOCR,
    FORMATOS_IMAGEM,
    reconhecer_imagem,
    reconhecer_pagina_pdf,
)


MAX_BYTES = 5 * 1024 * 1024
MAX_TEXTO = 100_000
MAX_PAGINAS = 30

FORMATOS_DOCUMENTO = {
    ".txt",
    ".pdf",
    ".docx",
}

FORMATOS_ACEITOS = (
    FORMATOS_DOCUMENTO
    | FORMATOS_IMAGEM
)


class ErroImportacao(ValueError):
    pass


def _validar_arquivo(
    nome: str,
    dados: bytes,
) -> str:
    """
    Valida formato e tamanho e devolve a extensão normalizada.
    """
    extensao = (
        Path(nome)
        .suffix
        .lower()
    )

    if extensao not in FORMATOS_ACEITOS:
        raise ErroImportacao(
            "Use TXT, PDF, DOCX ou uma imagem "
            "PNG, JPG, JPEG, BMP, TIFF ou WEBP. "
            "O formato DOC antigo não é aceito."
        )

    if (
        not dados
        or len(dados) > MAX_BYTES
    ):
        raise ErroImportacao(
            "O arquivo deve conter dados "
            "e ter no máximo 5 MiB."
        )

    return extensao


def _extrair_txt(
    dados: bytes,
) -> str:
    """
    Extrai TXT em UTF-8.
    """
    return dados.decode(
        "utf-8-sig"
    )


def _extrair_pdf(
    dados: bytes,
) -> str:
    """
    Extrai texto de um PDF página a página.

    Quando uma página não possui texto extraível,
    aplica OCR somente naquela página.

    O marcador [Página N] é preservado para permitir
    localização posterior das citações.
    """
    leitor = PdfReader(
        BytesIO(dados)
    )

    if leitor.is_encrypted:
        raise ErroImportacao(
            "PDF protegido não é aceito."
        )

    quantidade_paginas = len(
        leitor.pages
    )

    if quantidade_paginas > MAX_PAGINAS:
        raise ErroImportacao(
            "Use PDFs com até 30 páginas."
        )

    if quantidade_paginas == 0:
        raise ErroImportacao(
            "PDF sem páginas utilizáveis."
        )

    partes = []

    for indice, pagina in enumerate(
        leitor.pages
    ):
        numero = indice + 1

        trecho = (
            pagina.extract_text()
            or ""
        ).strip()

        if trecho:
            partes.append(
                f"[Página {numero}]\n"
                f"{trecho}"
            )

            continue

        try:
            resultado_ocr = (
                reconhecer_pagina_pdf(
                    dados,
                    indice,
                )
            )

        except ErroOCR as erro:
            raise ErroImportacao(
                f"Página {numero} sem texto extraível "
                "e o OCR não conseguiu reconhecer "
                f"conteúdo utilizável: {erro}"
            ) from erro

        trecho_ocr = (
            resultado_ocr.texto
            .strip()
        )

        if not trecho_ocr:
            raise ErroImportacao(
                f"Página {numero} sem texto utilizável "
                "mesmo após OCR."
            )

        partes.append(
            f"[Página {numero}]\n"
            "[Extração: OCR]\n"
            f"{trecho_ocr}"
        )

    return "\n\n".join(
        partes
    )


def _extrair_docx(
    dados: bytes,
) -> str:
    """
    Extrai parágrafos e tabelas de DOCX mantendo
    a ordem oferecida pelo python-docx.
    """
    # Evita abrir um DOCX muito grande após descompactação.
    with ZipFile(
        BytesIO(dados)
    ) as pacote:
        tamanho = sum(
            item.file_size
            for item
            in pacote.infolist()
        )

        if (
            tamanho
            > 20 * 1024 * 1024
        ):
            raise ErroImportacao(
                "DOCX muito grande "
                "após descompactação."
            )

    documento = Document(
        BytesIO(dados)
    )

    partes = []

    for bloco in (
        documento
        .iter_inner_content()
    ):
        if isinstance(
            bloco,
            Paragraph,
        ):
            partes.append(
                bloco.text
            )

        else:
            partes.append(
                "\n".join(
                    " | ".join(
                        celula.text
                        for celula
                        in linha.cells
                    )
                    for linha
                    in bloco.rows
                )
            )

    return "\n\n".join(
        parte
        for parte in partes
        if parte.strip()
    )


def _extrair_imagem(
    dados: bytes,
) -> str:
    """
    Executa OCR em uma imagem.

    O texto reconhecido não recebe correção automática.
    """
    try:
        resultado = reconhecer_imagem(
            dados
        )

    except ErroOCR as erro:
        raise ErroImportacao(
            "Não consegui extrair texto da imagem "
            f"com OCR: {erro}"
        ) from erro

    texto = (
        resultado.texto
        .strip()
    )

    if not texto:
        raise ErroImportacao(
            "A imagem não possui texto "
            "utilizável após OCR."
        )

    return (
        "[Extração: OCR]\n"
        f"{texto}"
    )


def _normalizar_texto_extraido(
    texto: str,
) -> str:
    """
    Normaliza somente as quebras de linha do conteúdo extraído.
    """
    texto = (
        texto
        .replace(
            "\r\n",
            "\n",
        )
        .replace(
            "\r",
            "\n",
        )
        .strip()
    )

    if (
        not texto
        or "\x00" in texto
    ):
        raise ErroImportacao(
            "Arquivo sem texto utilizável."
        )

    if len(texto) > MAX_TEXTO:
        raise ErroImportacao(
            "O texto extraído excedeu "
            "100.000 caracteres."
        )

    return texto


def extrair_texto(
    nome: str,
    dados: bytes,
) -> str:
    """
    Lê texto localmente.

    Não salva arquivos nem consulta APIs externas.

    PDFs utilizam extração textual sempre que possível
    e OCR somente nas páginas sem texto extraível.

    Imagens utilizam OCR local.
    """
    extensao = _validar_arquivo(
        nome,
        dados,
    )

    try:
        if extensao == ".txt":
            texto = _extrair_txt(
                dados
            )

        elif extensao == ".pdf":
            texto = _extrair_pdf(
                dados
            )

        elif extensao == ".docx":
            texto = _extrair_docx(
                dados
            )

        elif extensao in FORMATOS_IMAGEM:
            texto = _extrair_imagem(
                dados
            )

        else:
            # Proteção defensiva.
            raise ErroImportacao(
                "Formato não suportado."
            )

    except ErroImportacao:
        raise

    except UnicodeDecodeError as erro:
        raise ErroImportacao(
            "Não consegui ler o TXT. "
            "O arquivo precisa estar em UTF-8."
        ) from erro

    except Exception as erro:
        raise ErroImportacao(
            "Não consegui ler o arquivo. "
            "Confira se ele é válido."
        ) from erro

    return _normalizar_texto_extraido(
        texto
    )


def salvar_texto(
    pasta: Path,
    nome: str,
    texto: str,
) -> tuple[Path, bool]:
    """
    Salva uma cópia TXT sem substituir
    arquivos já existentes.
    """
    if (
        not texto.strip()
        or len(texto) > MAX_TEXTO
    ):
        raise ErroImportacao(
            "Texto vazio ou acima do limite."
        )

    origem = Path(
        nome.replace(
            "\\",
            "/",
        )
    ).name

    origem = "".join(
        caractere
        for caractere in origem
        if caractere.isprintable()
    )[:150]

    base = unicodedata.normalize(
        "NFKD",
        Path(origem).stem,
    )

    base = (
        base
        .encode(
            "ascii",
            "ignore",
        )
        .decode()
        .lower()
    )

    base = re.sub(
        r"[^a-z0-9]+",
        "_",
        base,
    ).strip("_")[:40]

    base = (
        base
        or "documento"
    )

    conteudo = (
        f"Arquivo de origem: {origem}\n\n"
        f"{texto.strip()}\n"
    )

    codigo = hashlib.sha256(
        conteudo.encode(
            "utf-8"
        )
    ).hexdigest()[:16]

    pasta.mkdir(
        parents=True,
        exist_ok=True,
    )

    destino = (
        pasta
        / (
            f"importado_"
            f"{base}_"
            f"{codigo}.txt"
        )
    )

    try:
        with destino.open(
            "x",
            encoding="utf-8",
        ) as arquivo:
            arquivo.write(
                conteudo
            )

    except FileExistsError:
        return (
            destino,
            False,
        )

    return (
        destino,
        True,
    )