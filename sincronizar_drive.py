import argparse
import hashlib
import json
import os
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

BASE = Path(__file__).resolve().parent

GOOGLE_DOC = "application/vnd.google-apps.document"

FORMATOS = {
    "text/plain": ".txt",
    "application/pdf": ".pdf",
    (
        "application/vnd.openxmlformats-officedocument."
        "wordprocessingml.document"
    ): ".docx",
    GOOGLE_DOC: ".txt",
}

MAX_ARQUIVOS = 30


def resumo(dados: bytes) -> str:
    """Calcula uma identificação para comparar conteúdos."""
    return hashlib.sha256(dados).hexdigest()


def gravar(caminho: Path, dados: bytes) -> None:
    """Prepara um arquivo temporário antes de substituir o destino."""
    caminho.parent.mkdir(parents=True, exist_ok=True)

    with NamedTemporaryFile(
        dir=caminho.parent,
        delete=False,
    ) as arquivo:
        temporario = Path(arquivo.name)
        arquivo.write(dados)

    try:
        temporario.replace(caminho)
    finally:
        temporario.unlink(missing_ok=True)


def baixar_texto(servico, item: dict, pasta_id: str) -> str:
    from importacao import MAX_BYTES, extrair_texto

    arquivos = servico.files()

    campos = (
        "id,name,mimeType,size,version,parents,trashed,"
        "capabilities(canDownload)"
    )

    meta = arquivos.get(
        fileId=item["id"],
        fields=campos,
        supportsAllDrives=True,
    ).execute(num_retries=2)

    if (
        meta.get("trashed")
        or pasta_id not in meta.get("parents", [])
    ):
        raise ValueError(
            "A pasta mudou durante a leitura. Repita a execução."
        )

    tipo = meta.get("mimeType")

    if (
        tipo not in FORMATOS
        or not meta.get("capabilities", {}).get("canDownload")
    ):
        raise ValueError(
            "Formato alterado ou download não autorizado."
        )

    if tipo == GOOGLE_DOC:
        dados = arquivos.export_media(
            fileId=item["id"],
            mimeType="text/plain",
        ).execute(num_retries=2)

    else:
        if int(meta.get("size", MAX_BYTES + 1)) > MAX_BYTES:
            raise ValueError(
                "Arquivo do Drive acima de 5 MiB."
            )

        dados = arquivos.get_media(
            fileId=item["id"],
            supportsAllDrives=True,
        ).execute(num_retries=2)

    texto = extrair_texto(
        "documento" + FORMATOS[tipo],
        dados,
    )

    # Confere se o documento mudou enquanto era baixado.
    depois = arquivos.get(
        fileId=item["id"],
        fields="version,parents,trashed",
        supportsAllDrives=True,
    ).execute(num_retries=2)

    if (
        depois.get("version") != meta.get("version")
        or depois.get("trashed")
        or pasta_id not in depois.get("parents", [])
    ):
        raise ValueError(
            "Um documento mudou durante o download. "
            "Repita a execução."
        )

    nome = " ".join(meta["name"].split())

    return (
        f"Fonte no Google Drive: {nome}\n"
        f"ID: {item['id']}\n\n"
        f"{texto}\n"
    )


def aplicar_copias(
    pasta: Path,
    estado: Path,
    pasta_id: str,
    novas: dict[str, bytes],
) -> dict:
    """Atualiza somente as cópias registradas pela sincronização."""
    pasta.mkdir(parents=True, exist_ok=True)
    estado.mkdir(parents=True, exist_ok=True)

    manifesto = estado / "manifesto.json"

    anterior = (
        json.loads(manifesto.read_text(encoding="utf-8"))
        if manifesto.exists()
        else {"pasta": pasta_id, "arquivos": {}}
    )

    if anterior["pasta"] != pasta_id:
        raise ValueError(
            "A pasta configurada mudou. "
            "Não misture duas bases neste estado."
        )

    antigos = anterior["arquivos"]

    # Protege os caminhos e identifica alterações manuais locais.
    for nome in set(antigos) | set(novas):
        if not re.fullmatch(
            r"drive_[0-9a-f]{24}\.txt",
            nome,
        ):
            raise ValueError(
                "Nome inválido no registro local. "
                "Operação interrompida."
            )

        destino = pasta / nome

        if destino.is_symlink():
            raise ValueError(
                "Links simbólicos não são aceitos "
                "na base sincronizada."
            )

        if destino.exists():
            if (
                nome not in antigos
                or resumo(destino.read_bytes()) != antigos[nome]
            ):
                raise ValueError(
                    "Uma cópia local foi criada ou editada "
                    "manualmente. Revise antes de sincronizar."
                )

    alterados = {
        nome
        for nome, dados in novas.items()
        if (
            not (pasta / nome).exists()
            or antigos.get(nome) != resumo(dados)
        )
    }

    retirados = set(antigos) - set(novas)
    afetados = alterados | retirados

    registros = {
        "incluidos": len(alterados - set(antigos)),
        "atualizados": len(alterados & set(antigos)),
        "retirados": len(retirados),
        "mantidos": len(novas) - len(alterados),
    }

    # Guarda as versões anteriores fora da pasta pesquisada.
    backup = None

    if afetados:
        backup = estado / "historico" / uuid4().hex
        backup.mkdir(parents=True)

        for nome in afetados:
            if (pasta / nome).exists():
                shutil.copy2(
                    pasta / nome,
                    backup / nome,
                )

        if manifesto.exists():
            shutil.copy2(
                manifesto,
                backup / "manifesto.json",
            )

    try:
        for nome in sorted(alterados):
            gravar(pasta / nome, novas[nome])

        for nome in sorted(retirados):
            (pasta / nome).unlink(missing_ok=True)

        novo = {
            "pasta": pasta_id,
            "ultima_execucao": (
                datetime.now(timezone.utc).isoformat()
            ),
            "arquivos": {
                nome: resumo(dados)
                for nome, dados in novas.items()
            },
        }

        gravar(
            manifesto,
            json.dumps(novo, indent=2).encode("utf-8"),
        )

    except BaseException:
        # Tenta restaurar o estado anterior se a aplicação falhar.
        if backup is not None:
            for nome in afetados:
                if (backup / nome).exists():
                    gravar(
                        pasta / nome,
                        (backup / nome).read_bytes(),
                    )
                else:
                    (pasta / nome).unlink(missing_ok=True)

            if (backup / "manifesto.json").exists():
                gravar(
                    manifesto,
                    (backup / "manifesto.json").read_bytes(),
                )
            else:
                manifesto.unlink(missing_ok=True)

        raise

    return registros


def sincronizar(
    servico,
    pasta_id: str,
    base: Path,
) -> dict:
    from verificar_drive import listar_pasta

    estado = base / ".estado_drive"
    estado.mkdir(parents=True, exist_ok=True)

    trava = estado / "em_execucao"

    try:
        trava.mkdir()
    except FileExistsError:
        raise ValueError(
            "Existe uma execução ou interrupção pendente. "
            "Não inicie duas sincronizações."
        )

    try:
        _, itens = listar_pasta(servico, pasta_id)

        selecionados = [
            item
            for item in itens
            if item["mimeType"] in FORMATOS
        ]

        if len(selecionados) > MAX_ARQUIVOS:
            raise ValueError(
                "Use no máximo 30 documentos compatíveis "
                "nesta demonstração."
            )

        novas = {}

        for item in selecionados:
            nome = (
                "drive_"
                + resumo(item["id"].encode("utf-8"))[:24]
                + ".txt"
            )

            novas[nome] = baixar_texto(
                servico,
                item,
                pasta_id,
            ).encode("utf-8")

        # Aplica mudanças somente após concluir a leitura da base.
        resultado = aplicar_copias(
            base / "documentos",
            estado,
            pasta_id,
            novas,
        )

        resultado["ignorados"] = (
            len(itens) - len(selecionados)
        )

        return resultado

    finally:
        trava.rmdir()


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--intervalo",
        type=int,
        default=0,
        help=(
            "0: uma execução; "
            "300 ou mais: repetir a cada N segundos."
        ),
    )

    args = parser.parse_args()

    if args.intervalo != 0 and args.intervalo < 300:
        parser.error(
            "Use 0 ou um intervalo de pelo menos 300 segundos."
        )

    try:
        from dotenv import dotenv_values
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build

        from verificar_drive import ESCOPO

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
            while True:
                try:
                    resultado = sincronizar(
                        servico,
                        pasta_id,
                        BASE,
                    )

                    print(
                        datetime.now().strftime("%H:%M:%S"),
                        resultado,
                        flush=True,
                    )

                    print(
                        "Base local atualizada. "
                        "Inicie uma nova conversa no chat.",
                        flush=True,
                    )

                except Exception as erro:
                    print(
                        "Sincronização não concluída "
                        f"({type(erro).__name__}).",
                        flush=True,
                    )

                    if isinstance(erro, ValueError):
                        print(str(erro), flush=True)

                    print(
                        "Não presuma que a base local está "
                        "atualizada. Confira o acesso e os arquivos.",
                        flush=True,
                    )

                    if not args.intervalo:
                        return 1

                if not args.intervalo:
                    return 0

                time.sleep(args.intervalo)

    except KeyboardInterrupt:
        print("\nMonitor encerrado.")
        return 0

    except Exception as erro:
        print(
            f"Falha de configuração ({type(erro).__name__}). "
            "Confira as dependências e credenciais locais."
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())