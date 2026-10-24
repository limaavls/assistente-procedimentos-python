import os
from pathlib import Path

import streamlit as st
from dotenv import dotenv_values

from app import carregar_documentos
from busca import buscar_por_pergunta, extrair_palavras

BASE = Path(__file__).resolve().parent

st.set_page_config(
    page_title="Assistente de Procedimentos",
    page_icon="📚",
    layout="centered",
)
st.title("📚 Assistente de Procedimentos")
st.caption("Busca local e resposta opcional com Gemini. Documentos fictícios.")

# Guarda a consulta enquanto você interage com a página.
st.session_state.setdefault("pesquisa_salva", None)
st.session_state.setdefault("resposta_ia", "")

pasta = BASE / "documentos"
if not pasta.is_dir():
    st.error("Não encontrei a pasta documentos.")
    st.stop()

documentos = carregar_documentos(pasta)
if not documentos:
    st.warning("Nenhum documento TXT com conteúdo pôde ser carregado.")
    st.stop()

st.caption(f"Documentos carregados: {len(documentos)}")

with st.form("formulario_busca"):
    pergunta = st.text_input(
        "Digite uma pergunta ou palavra-chave:",
        placeholder="Ex.: Como solicitar material?",
        max_chars=500,
    )
    pesquisar = st.form_submit_button("Pesquisar")

if pesquisar:
    # Uma nova pesquisa apaga a resposta e a autorização anteriores.
    st.session_state["pesquisa_salva"] = None
    st.session_state["resposta_ia"] = ""
    st.session_state["autorizar_envio"] = False
    pergunta = pergunta.strip()

    if not extrair_palavras(pergunta) or len(pergunta) > 500:
        st.warning("Digite uma pergunta específica, com até 500 caracteres.")
        st.stop()

    resultados = buscar_por_pergunta(documentos, pergunta)
    if not resultados:
        st.info("Não encontrei documentos candidatos. A IA não foi consultada.")
        st.stop()

    st.session_state["pesquisa_salva"] = {
        "pergunta": pergunta,
        "resultados": resultados,
    }

consulta = st.session_state["pesquisa_salva"]
if consulta is None:
    st.info("Faça uma pesquisa para começar.")
    st.stop()

# Mantém visíveis os resultados da última pesquisa realizada.
resultados = consulta["resultados"]
palavras = extrair_palavras(consulta["pergunta"])
st.subheader("Pesquisa em análise")
st.text(consulta["pergunta"])
st.caption("Para mudar a pergunta ou atualizar os documentos, clique em Pesquisar.")
st.info(f"Documentos candidatos: {len(resultados)}")

for arquivo, texto, trechos in resultados:
    st.subheader(f"Fonte: {arquivo.name}")
    encontradas = palavras & extrair_palavras(texto)
    st.caption("Palavras encontradas: " + ", ".join(sorted(encontradas)))

    for numero, trecho in enumerate(trechos, start=1):
        st.caption(f"Trecho {numero}")
        st.text(trecho)

    with st.expander(f"Ver documento completo: {arquivo.name}"):
        st.text(texto)

st.divider()
st.subheader("Resposta com inteligência artificial")

# A busca acima continua funcionando se a integração ainda não existir.
try:
    import httpx
    from google.genai import errors
    from consulta_ia import MODELO_PADRAO, gerar_resposta, preparar_contexto
except ImportError:
    st.info(
        "Para habilitar a IA, adicione a versão Gemini de consulta_ia.py "
        "da etapa anterior e instale as dependências de requirements.txt."
    )
    st.stop()

try:
    contexto = preparar_contexto(resultados)
except ValueError as erro:
    st.warning(str(erro))
    st.stop()

with st.expander("Conferir exatamente os trechos que serão enviados"):
    st.text(contexto)

# Lê a chave localmente, sem mostrá-la na tela.
config = dotenv_values(BASE / ".env")
chave = (os.getenv("GEMINI_API_KEY") or config.get("GEMINI_API_KEY") or "").strip()
modelo = (
    os.getenv("GEMINI_MODEL") or config.get("GEMINI_MODEL") or MODELO_PADRAO
).strip() or MODELO_PADRAO

if not chave or chave == "COLE_SUA_CHAVE_AQUI":
    st.warning("Configure GEMINI_API_KEY no .env. A busca local continua disponível.")
    st.stop()

st.caption(f"Modelo configurado: {modelo}")
st.warning(
    "A pergunta em análise e os trechos selecionados serão enviados ao Google. "
    "Use somente dados fictícios e confira o Free Tier da sua conta."
)

autorizado = st.checkbox(
    "Conferi a pergunta e os trechos fictícios e autorizo o envio ao Google.",
    key="autorizar_envio",
)
gerar = st.button(
    "Gerar resposta com IA",
    disabled=not autorizado or bool(st.session_state["resposta_ia"]),
)

if gerar and autorizado and not st.session_state["resposta_ia"]:
    try:
        with st.spinner("Consultando o Gemini..."):
            st.session_state["resposta_ia"] = gerar_resposta(
                consulta["pergunta"], contexto, chave, modelo
            )
    except errors.APIError as erro:
        avisos = {
            400: "Confira a chave, o modelo e a configuração da API.",
            401: "A autenticação falhou. Confira sua chave no .env.",
            403: "Acesso recusado. Confira as permissões do projeto.",
            404: "Modelo não encontrado. Confira GEMINI_MODEL no .env.",
            429: "Cota atingida ou indisponível. Confira os limites no AI Studio.",
        }
        st.error(avisos.get(erro.code, "Falha na API. Tente novamente mais tarde."))
    except httpx.HTTPError:
        st.error("Falha de conexão ou tempo limite. Confira sua internet.")
    except ValueError:
        st.error("Não recebi uma resposta completa. Refine a pergunta e tente novamente.")

if st.session_state["resposta_ia"]:
    st.subheader("Resposta gerada por IA — confira as fontes")
    st.text(st.session_state["resposta_ia"])
    st.caption(
        "As citações não são verificadas automaticamente. "
        "Compare a resposta com os documentos originais. "
        "Para outra consulta, faça uma nova pesquisa."
    )