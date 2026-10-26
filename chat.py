import os
from pathlib import Path

import httpx
import streamlit as st
from dotenv import dotenv_values
from google.genai import errors

from app import carregar_documentos
from busca import buscar_por_pergunta
from citacoes import (
    apresentacao_do_historico,
    apresentacao_para_historico,
    renderizar_resposta,
)
from consulta_ia import (
    MODELO_PADRAO,
    gerar_resposta,
    preparar_pacote,
)
from conversa import montar_consulta
from painel_documentos import mostrar_importacao


BASE = Path(__file__).resolve().parent
MAX_TURNOS = 10

MODO_PALAVRAS = "Por palavras"
MODO_SEMANTICO = "Por significado (local)"
MODO_HIBRIDO = "Híbrida (palavras + significado)"

MODOS_BUSCA = [
    MODO_PALAVRAS,
    MODO_SEMANTICO,
    MODO_HIBRIDO,
]


# -------------------------------------------------------------------
# Funções de estado
# -------------------------------------------------------------------

def limpar_autorizacao() -> None:
    """
    Limpa tanto o estado lógico da autorização quanto o estado
    visual do checkbox.

    Esta função deve ser utilizada antes da criação do widget
    ou por callbacks, evitando modificar diretamente uma chave
    de widget depois que ele já foi instanciado.
    """
    st.session_state["chat_autoriza"] = False
    st.session_state["chat_autoriza_widget"] = False


def nova_conversa() -> None:
    """
    Limpa toda a conversa atual.
    """
    st.session_state["chat_historico"] = []
    st.session_state["chat_pendente"] = None
    limpar_autorizacao()


def cancelar_pergunta() -> None:
    """
    Descarta somente a pergunta que ainda aguardava autorização.
    """
    st.session_state["chat_pendente"] = None
    limpar_autorizacao()


def atualizar_autorizacao() -> None:
    """
    Copia o estado visual do checkbox para o estado lógico
    utilizado pela aplicação.
    """
    st.session_state["chat_autoriza"] = bool(
        st.session_state.get(
            "chat_autoriza_widget",
            False,
        )
    )


def executar_busca(
    modo_busca: str,
    documentos,
    texto_busca: str,
):
    """
    Executa o mecanismo selecionado pelo usuário.

    A função centraliza a escolha entre:
    - busca por palavras;
    - busca semântica local;
    - busca híbrida.

    O contrato de retorno é o mesmo para os três modos.
    """
    if modo_busca == MODO_PALAVRAS:
        return buscar_por_pergunta(
            documentos,
            texto_busca,
        )

    if modo_busca == MODO_SEMANTICO:
        try:
            from busca_semantica import (
                buscar_semantico,
            )

        except ImportError as erro:
            raise ValueError(
                "Não consegui carregar a busca semântica. "
                "Confira se busca_semantica.py está na pasta "
                "do projeto e se as dependências foram "
                "instaladas. "
                "A busca por palavras continua disponível."
            ) from erro

        with st.spinner(
            "Buscando por significado "
            "no computador..."
        ):
            return buscar_semantico(
                documentos,
                texto_busca,
            )

    if modo_busca == MODO_HIBRIDO:
        try:
            from busca_hibrida import (
                buscar_hibrido,
            )

        except ImportError as erro:
            raise ValueError(
                "Não consegui carregar a busca híbrida. "
                "Confira busca_hibrida.py e as dependências "
                "da busca semântica. "
                "A busca por palavras continua disponível."
            ) from erro

        with st.spinner(
            "Combinando busca por palavras "
            "e significado no computador..."
        ):
            return buscar_hibrido(
                documentos,
                texto_busca,
            )

    raise ValueError(
        "Modo de busca inválido."
    )


# -------------------------------------------------------------------
# Configuração da página
# -------------------------------------------------------------------

st.set_page_config(
    page_title="Conversa sobre procedimentos",
    page_icon="💬",
    initial_sidebar_state="expanded",
)

st.title(
    "💬 Conversa sobre procedimentos"
)

st.caption(
    "Documentos fictícios. "
    "Cada resposta exige autorização de envio."
)


# -------------------------------------------------------------------
# Estado da sessão
# -------------------------------------------------------------------

estado = st.session_state

estado.setdefault(
    "chat_historico",
    [],
)

estado.setdefault(
    "chat_pendente",
    None,
)

estado.setdefault(
    "chat_autoriza",
    False,
)

estado.setdefault(
    "chat_autoriza_widget",
    False,
)


# -------------------------------------------------------------------
# Nova conversa
# -------------------------------------------------------------------

st.button(
    "Nova conversa",
    key="chat_nova",
    on_click=nova_conversa,
)


# -------------------------------------------------------------------
# Configurações
# -------------------------------------------------------------------

st.sidebar.header(
    "Configurações da consulta"
)

modo_busca = st.sidebar.selectbox(
    "Modo de busca",
    MODOS_BUSCA,
    key="chat_modo_busca",
    disabled=bool(
        estado["chat_historico"]
        or estado["chat_pendente"]
    ),
)

st.sidebar.caption(
    "Para trocar o modo durante uma conversa, "
    "clique em Nova conversa."
)


if modo_busca == MODO_SEMANTICO:
    st.sidebar.warning(
        "Os resultados são documentos candidatos "
        "recuperados por significado. "
        "Confira os trechos antes de autorizar a IA."
    )


if modo_busca == MODO_HIBRIDO:
    st.sidebar.info(
        "A busca híbrida combina a ordem da busca "
        "por palavras com a busca semântica local. "
        "Os resultados continuam sendo apenas candidatos."
    )

    st.sidebar.caption(
        "A fusão de rankings não representa "
        "probabilidade de acerto."
    )


st.sidebar.divider()


# -------------------------------------------------------------------
# Importação de documentos
# -------------------------------------------------------------------

if mostrar_importacao(
    BASE / "documentos"
):
    estado["chat_historico"] = []
    estado["chat_pendente"] = None

    limpar_autorizacao()

    st.rerun()


historico = estado[
    "chat_historico"
]


st.caption(
    f"Modo de busca selecionado: {modo_busca}"
)


if historico:
    st.caption(
        "Assunto inicial: "
        + historico[0]["pergunta"]
    )


st.info(
    "Continue no mesmo assunto. "
    "Para trocar de tema, clique em Nova conversa."
)


# -------------------------------------------------------------------
# Histórico concluído
# -------------------------------------------------------------------

for turno in historico:
    with st.chat_message(
        "user"
    ):
        st.text(
            turno["pergunta"]
        )

    with st.chat_message(
        "assistant"
    ):
        dados_resposta = turno.get(
            "resposta_validada"
        )

        if dados_resposta:
            apresentacao = (
                apresentacao_do_historico(
                    dados_resposta
                )
            )

            renderizar_resposta(
                st,
                apresentacao,
            )

        else:
            # Compatibilidade defensiva com sessões criadas
            # pelo formato anterior.
            resposta_antiga = turno.get(
                "resposta"
            )

            if resposta_antiga:
                st.text(
                    str(resposta_antiga)
                )

                st.warning(
                    "Esta resposta pertence ao formato antigo "
                    "da sessão e não possui o registro estruturado "
                    "de referências desta versão."
                )

        contexto_turno = turno.get(
            "contexto",
            "",
        )

        if contexto_turno:
            with st.expander(
                "Trechos enviados nesta consulta"
            ):
                st.text(
                    contexto_turno
                )


# -------------------------------------------------------------------
# Limite da conversa
# -------------------------------------------------------------------

if len(historico) >= MAX_TURNOS:
    st.warning(
        "Limite de 10 respostas nesta conversa. "
        "Inicie uma nova para continuar."
    )


# -------------------------------------------------------------------
# Entrada de nova pergunta
# -------------------------------------------------------------------

nova = st.chat_input(
    "Pergunte sobre um procedimento...",
    key="chat_entrada",
    max_chars=500,
    disabled=(
        estado["chat_pendente"]
        is not None
        or len(historico) >= MAX_TURNOS
    ),
)


# -------------------------------------------------------------------
# Preparação local da consulta
# -------------------------------------------------------------------

if nova:
    try:
        texto_busca, pedido = montar_consulta(
            nova,
            historico,
        )

        pasta = (
            BASE
            / "documentos"
        )

        if not pasta.is_dir():
            raise ValueError(
                "Não encontrei a pasta documentos."
            )

        documentos = carregar_documentos(
            pasta
        )

        if not documentos:
            raise ValueError(
                "Nenhum documento TXT com conteúdo "
                "pôde ser carregado."
            )

        resultados = executar_busca(
            modo_busca,
            documentos,
            texto_busca,
        )

        if not resultados:
            raise ValueError(
                "Não encontrei documentos candidatos. "
                "A IA não foi consultada."
            )

        pacote = preparar_pacote(
            resultados
        )

    except ValueError as erro:
        st.warning(
            str(erro)
        )

    else:
        estado["chat_pendente"] = {
            "pergunta": nova.strip(),
            "pedido": pedido,
            "pacote": pacote,
            "modo_busca": modo_busca,
        }

        limpar_autorizacao()

        st.rerun()


# -------------------------------------------------------------------
# Pergunta pendente
# -------------------------------------------------------------------

pendente = estado[
    "chat_pendente"
]


if pendente is not None:
    pacote = pendente[
        "pacote"
    ]

    with st.chat_message(
        "user"
    ):
        st.text(
            pendente["pergunta"]
        )

    st.caption(
        "Pergunta aguardando sua revisão "
        "e autorização."
    )

    st.caption(
        "Busca utilizada: "
        + pendente.get(
            "modo_busca",
            modo_busca,
        )
    )

    with st.expander(
        "Conferir pergunta, memória utilizada "
        "e trechos para envio"
    ):
        st.text(
            pendente["pedido"]
        )

        st.text(
            pacote.contexto
        )


    st.button(
        "Cancelar pergunta",
        key="chat_cancelar",
        on_click=cancelar_pergunta,
    )


    # ---------------------------------------------------------------
    # Configuração da IA
    # ---------------------------------------------------------------

    config = dotenv_values(
        BASE / ".env"
    )

    chave = (
        os.getenv(
            "GEMINI_API_KEY"
        )
        or config.get(
            "GEMINI_API_KEY"
        )
        or ""
    ).strip()

    modelo = (
        os.getenv(
            "GEMINI_MODEL"
        )
        or config.get(
            "GEMINI_MODEL"
        )
        or MODELO_PADRAO
    ).strip() or MODELO_PADRAO

    tem_chave = bool(
        chave
        and chave
        != "COLE_SUA_CHAVE_AQUI"
    )


    if not tem_chave:
        st.warning(
            "Configure GEMINI_API_KEY no .env "
            "para gerar respostas."
        )


    st.caption(
        f"Modelo configurado: {modelo}"
    )

    st.warning(
        "O pedido, incluindo perguntas anteriores "
        "selecionadas, e os trechos serão enviados "
        "ao Google. Use somente dados fictícios."
    )


    st.checkbox(
        "Conferi o conteúdo e autorizo "
        "este envio ao Google.",
        key="chat_autoriza_widget",
        on_change=atualizar_autorizacao,
    )


    autorizado = bool(
        estado.get(
            "chat_autoriza",
            False,
        )
    )


    enviar = st.button(
        "Gerar resposta com IA",
        key="chat_gerar",
        disabled=(
            not autorizado
            or not tem_chave
        ),
    )


    # ---------------------------------------------------------------
    # Geração e validação
    # ---------------------------------------------------------------

    if (
        enviar
        and autorizado
        and tem_chave
    ):
        try:
            with st.spinner(
                "Consultando os documentos "
                "com Gemini..."
            ):
                apresentacao = gerar_resposta(
                    pendente["pedido"],
                    pacote,
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

        except ValueError as erro:
            st.error(
                str(erro)
            )

        else:
            resposta_historico = (
                apresentacao_para_historico(
                    apresentacao
                )
            )

            historico.append(
                {
                    "pergunta": (
                        pendente[
                            "pergunta"
                        ]
                    ),
                    "resposta_validada": (
                        resposta_historico
                    ),
                    "contexto": (
                        pacote.contexto
                    ),
                    "modo_busca": (
                        pendente.get(
                            "modo_busca",
                            modo_busca,
                        )
                    ),
                }
            )

            estado[
                "chat_pendente"
            ] = None

            # Não alteramos a chave do checkbox diretamente.
            # O próximo rerun recria o estado visual de forma segura.
            estado[
                "chat_autoriza"
            ] = False

            st.rerun()


# -------------------------------------------------------------------
# Aviso final
# -------------------------------------------------------------------

st.caption(
    "Memória temporária desta sessão. "
    "As referências exibidas são conferidas quanto "
    "à existência e ao trecho citado. "
    "A interpretação da resposta ainda exige revisão. "
    "A busca híbrida combina rankings locais e não representa "
    "probabilidade de acerto. "
    "Limpar a conversa não apaga informações já "
    "enviadas ao provedor."
)