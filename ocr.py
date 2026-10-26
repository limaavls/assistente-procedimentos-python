from dataclasses import dataclass
from functools import lru_cache
from statistics import mean


DPI_PDF = 200
MAX_PIXELS = 25_000_000

FORMATOS_IMAGEM = {
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".tif",
    ".tiff",
    ".webp",
}


class ErroOCR(ValueError):
    """Erro controlado durante reconhecimento óptico de caracteres."""


@dataclass(frozen=True)
class ResultadoOCR:
    texto: str
    confianca_media: float | None
    linhas_reconhecidas: int


@lru_cache(maxsize=1)
def carregar_motor():
    """
    Carrega o RapidOCR somente quando o OCR for realmente utilizado.
    """
    try:
        from rapidocr import RapidOCR

    except ImportError as erro:
        raise ErroOCR(
            "OCR não está instalado. "
            "Instale as dependências de requirements-ocr.txt."
        ) from erro

    try:
        return RapidOCR()

    except Exception as erro:
        raise ErroOCR(
            "Não consegui inicializar o mecanismo de OCR."
        ) from erro


def _resultado_para_texto(resultado) -> ResultadoOCR:
    """
    Converte a saída do RapidOCR em texto simples.

    Nenhuma correção ortográfica é aplicada automaticamente.
    """
    if resultado is None:
        raise ErroOCR(
            "O OCR não retornou resultado."
        )

    textos = getattr(
        resultado,
        "txts",
        None,
    )

    scores = getattr(
        resultado,
        "scores",
        None,
    )

    if textos is None:
        raise ErroOCR(
            "O OCR retornou uma estrutura inesperada."
        )

    linhas = [
        str(texto).strip()
        for texto in textos
        if str(texto).strip()
    ]

    if not linhas:
        raise ErroOCR(
            "Não encontrei texto legível na imagem."
        )

    confiancas = []

    if scores is not None:
        for score in scores:
            try:
                numero = float(score)

            except (TypeError, ValueError):
                continue

            if 0 <= numero <= 1:
                confiancas.append(numero)

    confianca_media = (
        mean(confiancas)
        if confiancas
        else None
    )

    return ResultadoOCR(
        texto="\n".join(linhas),
        confianca_media=confianca_media,
        linhas_reconhecidas=len(linhas),
    )


def reconhecer_imagem(
    dados: bytes,
    motor=None,
) -> ResultadoOCR:
    """
    Executa OCR diretamente sobre uma imagem em memória.
    """
    if not isinstance(
        dados,
        (bytes, bytearray),
    ):
        raise ErroOCR(
            "A imagem precisa ser fornecida em bytes."
        )

    if not dados:
        raise ErroOCR(
            "A imagem está vazia."
        )

    if motor is None:
        motor = carregar_motor()

    try:
        resultado = motor(
            bytes(dados)
        )

    except ErroOCR:
        raise

    except Exception as erro:
        raise ErroOCR(
            "Não consegui executar OCR na imagem."
        ) from erro

    return _resultado_para_texto(
        resultado
    )


def renderizar_pagina_pdf(
    dados: bytes,
    indice_pagina: int,
    dpi: int = DPI_PDF,
) -> bytes:
    """
    Renderiza uma página de PDF como PNG para OCR.

    indice_pagina é baseado em zero:
    0 = primeira página.
    """
    if not dados:
        raise ErroOCR(
            "O PDF está vazio."
        )

    if (
        not isinstance(
            indice_pagina,
            int,
        )
        or indice_pagina < 0
    ):
        raise ErroOCR(
            "Índice de página inválido."
        )

    if (
        not isinstance(dpi, int)
        or dpi < 72
        or dpi > 300
    ):
        raise ErroOCR(
            "O DPI do OCR deve ficar entre 72 e 300."
        )

    try:
        import pymupdf

    except ImportError as erro:
        raise ErroOCR(
            "PyMuPDF não está instalado. "
            "Instale requirements-ocr.txt."
        ) from erro

    try:
        documento = pymupdf.open(
            stream=dados,
            filetype="pdf",
        )

    except Exception as erro:
        raise ErroOCR(
            "Não consegui abrir o PDF para OCR."
        ) from erro

    try:
        if documento.needs_pass:
            raise ErroOCR(
                "PDF protegido não é aceito para OCR."
            )

        if indice_pagina >= documento.page_count:
            raise ErroOCR(
                "A página solicitada não existe no PDF."
            )

        pagina = documento.load_page(
            indice_pagina
        )

        pixmap = pagina.get_pixmap(
            dpi=dpi,
            colorspace=pymupdf.csRGB,
            alpha=False,
        )

        pixels = (
            pixmap.width
            * pixmap.height
        )

        if pixels > MAX_PIXELS:
            raise ErroOCR(
                "A página ficou grande demais para OCR."
            )

        return pixmap.tobytes(
            "png"
        )

    except ErroOCR:
        raise

    except Exception as erro:
        raise ErroOCR(
            "Não consegui renderizar a página do PDF."
        ) from erro

    finally:
        documento.close()


def reconhecer_pagina_pdf(
    dados: bytes,
    indice_pagina: int,
    motor=None,
    dpi: int = DPI_PDF,
) -> ResultadoOCR:
    """
    Renderiza uma página do PDF e executa OCR nela.
    """
    imagem = renderizar_pagina_pdf(
        dados,
        indice_pagina,
        dpi=dpi,
    )

    return reconhecer_imagem(
        imagem,
        motor=motor,
    )