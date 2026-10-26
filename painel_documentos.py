from pathlib import Path

import streamlit as st

from importacao import (
    FORMATOS_IMAGEM,
    MAX_BYTES,
    ErroImportacao,
    extrair_texto,
    salvar_texto,
)


TIPOS_UPLOAD = [
    "txt",
    "pdf",
    "docx",
    "png",
    "jpg",
    "jpeg",
    "bmp",
    "tif",
    "tiff",
    "webp",
]


def limpar_previa() -> None:
    """
    Limpa a prévia e a confirmação quando o usuário
    troca o arquivo selecionado.
    """
    st.session_state["imp_previa"] = None
    st.session_state["imp_confirmar"] = False
    st.session_state["imp_mensagem"] = ""


def _arquivo_e_imagem(
    nome: str,
) -> bool:
    """
    Informa se o arquivo selecionado é um formato
    de imagem tratado por OCR.
    """
    return (
        Path(nome).suffix.lower()
        in FORMATOS_IMAGEM
    )


def _texto_usou_ocr(
    texto: str,
) -> bool:
    """
    Detecta a marca local adicionada pela extração
    quando OCR foi utilizado.

    Essa informação vem do processamento local,
    não da IA.
    """
    return (
        "[Extração: OCR]"
        in texto
    )


def mostrar_importacao(
    pasta: Path,
) -> bool:
    """
    Exibe o painel de importação.

    Retorna True após a inclusão de uma cópia
    na base para que o chat reinicie a conversa.
    """
    estado = st.session_state

    with st.sidebar:
        st.header(
            "Adicionar documento"
        )

        st.caption(
            "Somente arquivos fictícios de sua confiança. "
            "Até 5 MiB por arquivo."
        )

        st.caption(
            "Formatos aceitos: TXT, PDF, DOCX, "
            "PNG, JPG, JPEG, BMP, TIFF e WEBP."
        )

        st.caption(
            "PDFs digitalizados e imagens podem usar OCR local. "
            "O texto reconhecido deve ser revisado antes da inclusão."
        )

        if estado.get(
            "imp_mensagem"
        ):
            st.success(
                estado[
                    "imp_mensagem"
                ]
            )

        enviado = st.file_uploader(
            (
                "Selecione TXT, PDF, Word (DOCX) "
                "ou imagem"
            ),
            type=TIPOS_UPLOAD,
            key="imp_arquivo",
            on_change=limpar_previa,
        )

        if enviado is None:
            return False

        if enviado.size > MAX_BYTES:
            st.error(
                "O limite desta etapa é de "
                "5 MiB por arquivo."
            )

            return False

        nome = enviado.name

        if _arquivo_e_imagem(
            nome
        ):
            st.info(
                "Esta imagem será processada "
                "com OCR local."
            )

        if st.button(
            "Extrair e revisar",
            key="imp_extrair",
        ):
            limpar_previa()

            try:
                texto = extrair_texto(
                    nome,
                    enviado.getvalue(),
                )

                estado[
                    "imp_previa"
                ] = {
                    "nome": nome,
                    "texto": texto,
                    "usou_ocr": (
                        _texto_usou_ocr(
                            texto
                        )
                    ),
                }

            except ErroImportacao as erro:
                st.error(
                    str(erro)
                )

        previa = estado.get(
            "imp_previa"
        )

        if previa is None:
            return False

        if previa.get(
            "usou_ocr",
            False,
        ):
            st.warning(
                "OCR foi utilizado nesta extração. "
                "Confira cuidadosamente o texto reconhecido "
                "com o documento original antes de adicionar "
                "à base."
            )

        st.text_area(
            (
                "Texto extraído — "
                "confira com o original"
            ),
            value=previa[
                "texto"
            ],
            height=260,
            disabled=True,
        )

        st.caption(
            "A base armazena uma cópia TXT do conteúdo "
            "extraído. Formatação visual, imagens, assinaturas "
            "e outros elementos especiais não são preservados."
        )

        if previa.get(
            "usou_ocr",
            False,
        ):
            st.caption(
                "OCR pode reconhecer letras, números ou palavras "
                "incorretamente. A aplicação não corrige "
                "automaticamente o texto reconhecido."
            )

        aprovado = st.checkbox(
            (
                "Revisei o texto e confirmo que "
                "o documento é fictício."
            ),
            key="imp_confirmar",
        )

        if st.button(
            "Adicionar à base",
            key="imp_adicionar",
            disabled=not aprovado,
        ):
            if not aprovado:
                return False

            try:
                destino, criado = (
                    salvar_texto(
                        pasta,
                        previa["nome"],
                        previa["texto"],
                    )
                )

            except (
                ErroImportacao,
                OSError,
            ) as erro:
                st.error(
                    "Não foi possível salvar: "
                    f"{erro}"
                )

                return False

            estado[
                "imp_mensagem"
            ] = (
                f"Adicionado: {destino.name}"
                if criado
                else (
                    "Esta cópia já estava "
                    "na base."
                )
            )

            estado[
                "imp_previa"
            ] = None

            return True

    return False