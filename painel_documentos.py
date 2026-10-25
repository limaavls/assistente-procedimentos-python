from pathlib import Path

import streamlit as st

from importacao import (
    MAX_BYTES,
    ErroImportacao,
    extrair_texto,
    salvar_texto,
)


def limpar_previa() -> None:
    st.session_state["imp_previa"] = None
    st.session_state["imp_confirmar"] = False
    st.session_state["imp_mensagem"] = ""


def mostrar_importacao(pasta: Path) -> bool:
    """Retorna True após a inclusão para reiniciar a conversa."""
    estado = st.session_state

    with st.sidebar:
        st.header("Adicionar documento")
        st.caption(
            "Somente arquivos fictícios de sua confiança. "
            "Até 5 MiB por arquivo."
        )

        if estado.get("imp_mensagem"):
            st.success(estado["imp_mensagem"])

        enviado = st.file_uploader(
            "Selecione TXT, PDF ou Word (DOCX)",
            type=["txt", "pdf", "docx"],
            key="imp_arquivo",
            on_change=limpar_previa,
        )

        if enviado is None:
            return False

        if enviado.size > MAX_BYTES:
            st.error("O limite desta etapa é de 5 MiB por arquivo.")
            return False

        if st.button("Extrair e revisar", key="imp_extrair"):
            limpar_previa()

            try:
                texto = extrair_texto(
                    enviado.name, enviado.getvalue()
                )
                estado["imp_previa"] = {
                    "nome": enviado.name,
                    "texto": texto,
                }

            except ErroImportacao as erro:
                st.error(str(erro))

        previa = estado.get("imp_previa")

        if previa is None:
            return False

        st.text_area(
            "Texto extraído — confira com o original",
            value=previa["texto"],
            height=260,
            disabled=True,
        )

        st.caption(
            "Apenas texto: imagens e elementos especiais podem "
            "ficar de fora. A inclusão salva uma cópia TXT "
            "e reinicia a conversa atual."
        )

        aprovado = st.checkbox(
            "Revisei o texto e confirmo que o documento é fictício.",
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
                destino, criado = salvar_texto(
                    pasta, previa["nome"], previa["texto"]
                )

            except (ErroImportacao, OSError) as erro:
                st.error(f"Não foi possível salvar: {erro}")
                return False

            estado["imp_mensagem"] = (
                f"Adicionado: {destino.name}"
                if criado
                else "Esta cópia já estava na base."
            )
            estado["imp_previa"] = None
            return True

    return False