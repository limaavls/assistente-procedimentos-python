import os
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
ESCOPO = "https://www.googleapis.com/auth/drive.readonly"
TIPO_PASTA = "application/vnd.google-apps.folder"
MAX_ITENS = 200


class ErroVerificacao(ValueError):
    pass


def listar_pasta(servico, pasta_id: str) -> tuple[dict, list[dict]]:
    """Consulta apenas metadados. Não baixa nem altera documentos."""
    if not re.fullmatch(r"[A-Za-z0-9_-]{10,}", pasta_id):
        raise ErroVerificacao(
            "Confira DRIVE_FOLDER_ID: informe somente o ID, não o link."
        )

    pasta = servico.files().get(
        fileId=pasta_id,
        fields="id,name,mimeType,trashed",
        supportsAllDrives=True,
    ).execute(num_retries=2)

    if pasta.get("mimeType") != TIPO_PASTA or pasta.get("trashed"):
        raise ErroVerificacao("O ID não corresponde a uma pasta ativa.")

    itens = []
    pagina = None
    tokens = set()

    while True:
        resposta = servico.files().list(
            q=f"'{pasta_id}' in parents and trashed = false",
            fields="nextPageToken,incompleteSearch,files(id,name,mimeType)",
            pageSize=100,
            pageToken=pagina,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute(num_retries=2)

        if resposta.get("incompleteSearch"):
            raise ErroVerificacao("O Drive informou uma listagem incompleta.")

        itens.extend(resposta.get("files", []))
        if len(itens) > MAX_ITENS:
            raise ErroVerificacao(
                "Use uma pasta de demonstração com até 200 itens."
            )

        pagina = resposta.get("nextPageToken")
        if not pagina:
            break

        if pagina in tokens:
            raise ErroVerificacao(
                "A paginação se repetiu. Consulta interrompida."
            )

        tokens.add(pagina)

    itens.sort(key=lambda item: item.get("name", "").casefold())
    return pasta, itens


def main() -> int:
    # Importações opcionais: os testes simulados não precisam dessas bibliotecas.
    try:
        from dotenv import dotenv_values
        from google.auth.exceptions import GoogleAuthError
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
    except ImportError:
        print("Instale as dependências de requirements-drive.txt.")
        return 1

    config = dotenv_values(BASE / ".env")

    pasta_id = (
        os.getenv("DRIVE_FOLDER_ID")
        or config.get("DRIVE_FOLDER_ID")
        or ""
    ).strip()

    caminho = (
        os.getenv("DRIVE_CREDENTIALS_FILE")
        or config.get("DRIVE_CREDENTIALS_FILE")
        or ".secrets/google-drive.json"
    ).strip()

    credencial = Path(caminho).expanduser()
    if not credencial.is_absolute():
        credencial = BASE / credencial

    if not pasta_id:
        print("Configure DRIVE_FOLDER_ID no .env.")
        return 1

    if not credencial.is_file():
        print(
            "Não encontrei a credencial. "
            "Confira DRIVE_CREDENTIALS_FILE."
        )
        return 1

    try:
        acesso = Credentials.from_service_account_file(
            str(credencial),
            scopes=[ESCOPO],
        )

        with build(
            "drive",
            "v3",
            credentials=acesso,
            cache_discovery=False,
        ) as servico:
            pasta, itens = listar_pasta(servico, pasta_id)

    except ErroVerificacao as erro:
        print(str(erro))
        return 1

    except HttpError as erro:
        avisos = {
            403: (
                "Confira se a Drive API está ativada "
                "e se a conta tem acesso."
            ),
            404: (
                "Confira o ID da pasta e o compartilhamento "
                "com a conta de serviço."
            ),
            429: (
                "Limite temporário de consultas. "
                "Tente novamente mais tarde."
            ),
        }

        print(f"Erro HTTP {erro.resp.status} na consulta ao Drive.")
        print(
            avisos.get(
                erro.resp.status,
                "Não foi possível confirmar o acesso.",
            )
        )
        return 1

    except (GoogleAuthError, OSError, ValueError):
        print(
            "Falha de autenticação, conexão ou leitura da credencial. "
            "Confira o JSON, a internet e a configuração local. "
            "Não compartilhe o conteúdo da chave."
        )
        return 1

    print(f"\nAcesso confirmado à pasta: {pasta['name']}")
    print(f"Itens diretamente nesta pasta: {len(itens)}\n")

    for item in itens:
        print(f"- {item['name']} ({item['mimeType']})")

    if not itens:
        print("A pasta está acessível, mas nenhum item foi listado.")

    print("\nSomente metadados foram consultados.")
    print("Nenhum conteúdo foi baixado, alterado ou enviado ao Gemini.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())