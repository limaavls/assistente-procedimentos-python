import hashlib
import re
import unicodedata
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from docx import Document
from docx.text.paragraph import Paragraph
from pypdf import PdfReader

MAX_BYTES = 5 * 1024 * 1024
MAX_TEXTO = 100_000
MAX_PAGINAS = 30


class ErroImportacao(ValueError):
    pass


def extrair_texto(nome: str, dados: bytes) -> str:
    """Lê texto localmente. Não salva arquivos nem consulta uma API."""
    extensao = Path(nome).suffix.lower()

    if extensao not in {".txt", ".pdf", ".docx"}:
        raise ErroImportacao(
            "Use TXT, PDF ou DOCX. O formato DOC antigo não é aceito."
        )

    if not dados or len(dados) > MAX_BYTES:
        raise ErroImportacao(
            "O arquivo deve conter dados e ter no máximo 5 MiB."
        )

    try:
        if extensao == ".txt":
            texto = dados.decode("utf-8-sig")

        elif extensao == ".pdf":
            leitor = PdfReader(BytesIO(dados))

            if leitor.is_encrypted:
                raise ErroImportacao(
                    "PDF protegido não é aceito nesta versão."
                )

            if len(leitor.pages) > MAX_PAGINAS:
                raise ErroImportacao("Use PDFs com até 30 páginas.")

            partes = []

            for numero, pagina in enumerate(leitor.pages, start=1):
                trecho = (pagina.extract_text() or "").strip()

                if not trecho:
                    raise ErroImportacao(
                        f"Página {numero} sem texto extraível. "
                        "Esta versão recusa o PDF inteiro; não utiliza OCR."
                    )

                partes.append(f"[Página {numero}]\n{trecho}")

            texto = "\n\n".join(partes)

        else:
            # Evita abrir um DOCX muito grande após descompactação.
            with ZipFile(BytesIO(dados)) as pacote:
                tamanho = sum(
                    item.file_size for item in pacote.infolist()
                )

                if tamanho > 20 * 1024 * 1024:
                    raise ErroImportacao(
                        "DOCX muito grande após descompactação."
                    )

            documento = Document(BytesIO(dados))
            partes = []

            for bloco in documento.iter_inner_content():
                if isinstance(bloco, Paragraph):
                    partes.append(bloco.text)
                else:
                    partes.append(
                        "\n".join(
                            " | ".join(
                                celula.text for celula in linha.cells
                            )
                            for linha in bloco.rows
                        )
                    )

            texto = "\n\n".join(
                parte for parte in partes if parte.strip()
            )

    except ErroImportacao:
        raise

    except Exception as erro:
        raise ErroImportacao(
            "Não consegui ler o arquivo. Confira se ele é válido; "
            "TXT precisa ser UTF-8."
        ) from erro

    texto = texto.replace("\r\n", "\n").replace("\r", "\n").strip()

    if not texto or "\x00" in texto:
        raise ErroImportacao("Arquivo sem texto utilizável.")

    if len(texto) > MAX_TEXTO:
        raise ErroImportacao(
            "O texto extraído excedeu 100.000 caracteres."
        )

    return texto


def salvar_texto(
    pasta: Path, nome: str, texto: str
) -> tuple[Path, bool]:
    """Salva uma cópia TXT sem substituir arquivos já existentes."""
    if not texto.strip() or len(texto) > MAX_TEXTO:
        raise ErroImportacao("Texto vazio ou acima do limite.")

    origem = Path(nome.replace("\\", "/")).name
    origem = "".join(
        caractere for caractere in origem if caractere.isprintable()
    )[:150]

    base = unicodedata.normalize("NFKD", Path(origem).stem)
    base = base.encode("ascii", "ignore").decode().lower()
    base = re.sub(r"[^a-z0-9]+", "_", base).strip("_")[:40]
    base = base or "documento"

    conteudo = f"Arquivo de origem: {origem}\n\n{texto.strip()}\n"
    codigo = hashlib.sha256(
        conteudo.encode("utf-8")
    ).hexdigest()[:16]

    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / f"importado_{base}_{codigo}.txt"

    try:
        with destino.open("x", encoding="utf-8") as arquivo:
            arquivo.write(conteudo)

    except FileExistsError:
        return destino, False

    return destino, True