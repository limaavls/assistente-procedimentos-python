from pathlib import Path

import streamlit as st

from app import (
    TAMANHO_MINIMO_DO_TERMO,
    carregar_documentos,
    normalizar,
    trechos_com_termo,
)


# Configura e apresenta a tela.
st.set_page_config(
    page_title="Assistente de Procedimentos",
    page_icon="📚",
    layout="centered",
)

st.title("📚 Assistente de Procedimentos")
st.caption("Demonstração com documentos fictícios — busca textual, sem IA.")

# Reutiliza a leitura de documentos que já existe no app.py.
pasta = Path(__file__).resolve().parent / "documentos"

if not pasta.is_dir():
    st.error("Não encontrei a pasta documentos ao lado de interface.py.")
    st.stop()

documentos = carregar_documentos(pasta)

if not documentos:
    st.warning("Nenhum arquivo TXT com conteúdo pôde ser carregado.")
    st.stop()

st.caption(f"Documentos carregados: {len(documentos)}")

# Cria o campo de pesquisa e o botão.
with st.form("formulario_busca"):
    termo = st.text_input(
        "Digite uma palavra ou expressão presente nos documentos:",
        placeholder="Ex.: material, solicitação ou RH",
    )
    pesquisar = st.form_submit_button("Pesquisar")

# Executa a busca quando o formulário é enviado.
if pesquisar:
    termo = termo.strip()

    if len(normalizar(termo)) < TAMANHO_MINIMO_DO_TERMO:
        st.warning(
            f"Digite pelo menos {TAMANHO_MINIMO_DO_TERMO} caracteres."
        )
        st.stop()

    resultados = []

    for arquivo, texto in documentos:
        trechos = trechos_com_termo(texto, termo)

        if trechos:
            resultados.append((arquivo, texto, trechos))

    if not resultados:
        st.info("Não localizei esse termo nos documentos carregados.")
        st.stop()

    st.success(f"Documentos com correspondência: {len(resultados)}")

    # Mostra os trechos e permite conferir o documento inteiro.
    for arquivo, texto, trechos in resultados:
        st.subheader(f"Fonte: {arquivo.name}")

        for numero, trecho in enumerate(trechos, start=1):
            st.caption(f"Trecho {numero}")
            st.text(trecho)

        with st.expander("Ver documento completo"):
            st.text(texto)

    st.caption(
        "Confira o documento completo antes de utilizar a orientação."
    )