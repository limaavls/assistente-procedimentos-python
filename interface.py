from pathlib import Path

import streamlit as st

from app import carregar_documentos
from busca import buscar_por_pergunta, extrair_palavras

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
        "Digite uma pergunta ou palavra-chave:",
        placeholder="Ex.: Como solicitar material?",
    )
    pesquisar = st.form_submit_button("Pesquisar")

# Executa a busca quando o formulário é enviado.
if pesquisar:
    termo = termo.strip()
    palavras = extrair_palavras(termo)

    if not palavras:
        st.warning(
            "Digite uma palavra específica, como material ou RH."
        )
        st.stop()

    resultados = buscar_por_pergunta(documentos, termo)

    if not resultados:
        st.info(
            "Não encontrei documentos com as palavras da sua pesquisa."
        )
        st.stop()

    st.info(f"Documentos candidatos: {len(resultados)}")

    st.caption(
        "Resultados ordenados por palavras em comum. "
        "Encontrar um documento não garante que ele responda à pergunta."
    )

    for arquivo, texto, trechos in resultados:
        st.subheader(f"Fonte: {arquivo.name}")

        palavras_encontradas = palavras & extrair_palavras(texto)

        st.caption(
            "Palavras encontradas: "
            + ", ".join(sorted(palavras_encontradas))
        )

        for numero, trecho in enumerate(trechos, start=1):
            st.caption(f"Trecho {numero}")
            st.text(trecho)

        with st.expander("Ver documento completo"):
            st.text(texto)

    st.caption(
        "Confira o documento completo antes de utilizar a orientação."
    )