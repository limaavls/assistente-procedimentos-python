import os
from pathlib import Path

import httpx
import streamlit as st
from dotenv import dotenv_values
from google.genai import errors

from app import carregar_documentos
from busca import buscar_por_pergunta
from consulta_ia import MODELO_PADRAO, gerar_resposta, preparar_contexto
from conversa import montar_consulta

BASE = Path(__file__).resolve().parent
MAX_TURNOS = 10

st.set_page_config(
    page_title="Conversa sobre procedimentos",
    page_icon="💬",
)
st.title("💬 Conversa sobre procedimentos")
st.caption(
    "Documentos fictícios. Cada resposta exige autorização de envio."
)

estado = st.session_state
estado.setdefault("chat_historico", [])
estado.setdefault("chat_pendente", None)

# Aparece antes dos outros controles para limpar o estado com segurança.
if st.button("Nova conversa", key="chat_nova"):
    estado["chat_historico"] = []
    estado["chat_pendente"] = None
    estado["chat_autoriza"] = False
    st.rerun()

historico = estado["chat_historico"]

if historico:
    st.caption("Assunto inicial: " + historico[0]["pergunta"])

st.info(
    "Continue no mesmo assunto. "
    "Para trocar de tema, clique em Nova conversa."
)

# Mostra as perguntas e respostas já concluídas.
for turno in historico:
    with st.chat_message("user"):
        st.text(turno["pergunta"])

    with st.chat_message("assistant"):
        st.text(turno["resposta"])

        with st.expander("Trechos enviados nesta consulta"):
            st.text(turno["contexto"])

if len(historico) >= MAX_TURNOS:
    st.warning(
        "Limite de 10 respostas nesta conversa. "
        "Inicie uma nova para continuar."
    )

nova = st.chat_input(
    "Pergunte sobre um procedimento...",
    key="chat_entrada",
    max_chars=500,
    disabled=(
        estado["chat_pendente"] is not None
        or len(historico) >= MAX_TURNOS
    ),
)

# Primeiro prepara a consulta localmente, sem chamar a API.
if nova:
    try:
        texto_busca, pedido = montar_consulta(nova, historico)

        pasta = BASE / "documentos"
        if not pasta.is_dir():
            raise ValueError("Não encontrei a pasta documentos.")

        documentos = carregar_documentos(pasta)
        resultados = buscar_por_pergunta(documentos, texto_busca)

        if not resultados:
            raise ValueError(
                "Não encontrei documentos candidatos. "
                "A IA não foi consultada."
            )

        contexto = preparar_contexto(resultados)

    except ValueError as erro:
        st.warning(str(erro))

    else:
        estado["chat_pendente"] = {
            "pergunta": nova.strip(),
            "pedido": pedido,
            "contexto": contexto,
        }
        estado["chat_autoriza"] = False
        st.rerun()

pendente = estado["chat_pendente"]

if pendente is not None:
    with st.chat_message("user"):
        st.text(pendente["pergunta"])

    st.caption("Pergunta aguardando sua revisão e autorização.")

    with st.expander(
        "Conferir pergunta, memória utilizada e trechos para envio"
    ):
        st.text(pendente["pedido"])
        st.text(pendente["contexto"])

    if st.button("Cancelar pergunta", key="chat_cancelar"):
        estado["chat_pendente"] = None
        estado["chat_autoriza"] = False
        st.rerun()

    # Reutiliza sua configuração local, sem mostrar a chave.
    config = dotenv_values(BASE / ".env")

    chave = (
        os.getenv("GEMINI_API_KEY")
        or config.get("GEMINI_API_KEY")
        or ""
    ).strip()

    modelo = (
        os.getenv("GEMINI_MODEL")
        or config.get("GEMINI_MODEL")
        or MODELO_PADRAO
    ).strip() or MODELO_PADRAO

    tem_chave = bool(chave and chave != "COLE_SUA_CHAVE_AQUI")

    if not tem_chave:
        st.warning(
            "Configure GEMINI_API_KEY no .env para gerar respostas."
        )

    st.caption(f"Modelo configurado: {modelo}")

    st.warning(
        "O pedido, incluindo perguntas anteriores selecionadas, "
        "e os trechos serão enviados ao Google. "
        "Use somente dados fictícios."
    )

    autorizado = st.checkbox(
        "Conferi o conteúdo e autorizo este envio ao Google.",
        key="chat_autoriza",
    )

    enviar = st.button(
        "Gerar resposta com IA",
        key="chat_gerar",
        disabled=not autorizado or not tem_chave,
    )

    if enviar and autorizado and tem_chave:
        try:
            with st.spinner("Consultando os documentos com Gemini..."):
                resposta = gerar_resposta(
                    pendente["pedido"],
                    pendente["contexto"],
                    chave,
                    modelo,
                )

        except errors.APIError as erro:
            if erro.code == 429:
                st.error(
                    "Cota atingida ou indisponível. "
                    "Confira o AI Studio."
                )
            else:
                st.error(
                    f"Erro da API ({erro.code}). "
                    "Confira o acesso e o modelo."
                )

        except httpx.HTTPError:
            st.error(
                "Falha de conexão ou tempo limite. "
                "Nenhuma resposta foi registrada."
            )

        except ValueError:
            st.error(
                "Não foi possível obter uma resposta completa. "
                "Revise a consulta."
            )

        else:
            historico.append(
                {
                    "pergunta": pendente["pergunta"],
                    "resposta": resposta,
                    "contexto": pendente["contexto"],
                }
            )

            estado["chat_pendente"] = None
            st.rerun()

st.caption(
    "Memória temporária desta sessão. "
    "Respostas e citações precisam de conferência. "
    "Limpar a conversa não apaga informações já enviadas ao provedor."
)