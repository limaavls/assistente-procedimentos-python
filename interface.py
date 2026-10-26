import os
from pathlib import Path

import streamlit as st
from dotenv import dotenv_values

from app import carregar_documentos
from busca import buscar_por_pergunta, extrair_palavras
from citacoes import (
    apresentacao_do_historico,
    apresentacao_para_historico,
    renderizar_resposta,
)


BASE = Path(__file__).resolve().parent

MODO_PALAVRAS = "Por palavras"
MODO_SEMANTICO = "Por significado (local)"
MODO_HIBRIDO = "Híbrida (palavras + significado)"

MODOS_BUSCA = [
    MODO_PALAVRAS,
    MODO_SEMANTICO,
    MODO_HIBRIDO,
]


def executar_busca(
    modo_busca: str,
    documentos,
    pergunta: str,
):
    """
    Executa o modo de busca selecionado.

    Todos os modos devolvem o mesmo contrato:
    [
        (
            arquivo,
            texto_original,
            [TrechoCandidato, ...],
        ),
        ...
    ]
    """
    if modo_busca == MODO_PALAVRAS:
        return buscar_por_pergunta(
            documentos,
            pergunta,
        )

    if modo_busca == MODO_SEMANTICO:
        try:
            from busca_semantica import (
                buscar_semantico,
            )

        except ImportError as erro:
            raise ValueError(
                "Não consegui carregar a busca semântica. "
                "Confira busca_semantica.py e instale "
                "requirements-semantica.txt."
            ) from erro

        with st.spinner(
            "Buscando por significado "
            "no computador..."
        ):
            return buscar_semantico(
                documentos,
                pergunta,
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
                "da busca semântica."
            ) from erro

        with st.spinner(
            "Combinando busca por palavras "
            "e significado no computador..."
        ):
            return buscar_hibrido(
                documentos,
                pergunta,
            )

    raise ValueError(
        "Modo de busca inválido."
    )


# -------------------------------------------------------------------
# Configuração da página
# -------------------------------------------------------------------

st.set_page_config(
    page_title="Assistente de Procedimentos",
    page_icon="📚",
    layout="centered",
)

st.title(
    "📚 Assistente de Procedimentos"
)

st.caption(
    "Busca local e resposta opcional com Gemini. "
    "Documentos fictícios."
)


# -------------------------------------------------------------------
# Estado da sessão
# -------------------------------------------------------------------

st.session_state.setdefault(
    "pesquisa_salva",
    None,
)

st.session_state.setdefault(
    "resposta_ia",
    None,
)

st.session_state.setdefault(
    "autorizar_envio",
    False,
)

st.session_state.setdefault(
    "modo_busca_individual",
    MODO_PALAVRAS,
)


# -------------------------------------------------------------------
# Base documental
# -------------------------------------------------------------------

pasta = (
    BASE
    / "documentos"
)

if not pasta.is_dir():
    st.error(
        "Não encontrei a pasta documentos."
    )

    st.stop()


documentos = carregar_documentos(
    pasta
)

if not documentos:
    st.warning(
        "Nenhum documento TXT com conteúdo "
        "pôde ser carregado."
    )

    st.stop()


st.caption(
    f"Documentos carregados: {len(documentos)}"
)


# -------------------------------------------------------------------
# Seleção do modo
# -------------------------------------------------------------------

modo_busca = st.selectbox(
    "Modo de busca:",
    MODOS_BUSCA,
    key="modo_busca_individual",
)


if modo_busca == MODO_SEMANTICO:
    st.caption(
        "A busca por significado usa embeddings "
        "locais para localizar documentos candidatos."
    )


if modo_busca == MODO_HIBRIDO:
    st.info(
        "A busca híbrida combina a busca por palavras "
        "com a busca semântica local."
    )

    st.caption(
        "A fusão dos rankings ajuda a ordenar candidatos, "
        "mas não representa probabilidade de acerto."
    )


# -------------------------------------------------------------------
# Pesquisa
# -------------------------------------------------------------------

with st.form(
    "formulario_busca"
):
    pergunta = st.text_input(
        "Digite uma pergunta ou palavra-chave:",
        placeholder=(
            "Ex.: Como solicitar material?"
        ),
        max_chars=500,
    )

    pesquisar = st.form_submit_button(
        "Pesquisar"
    )


if pesquisar:
    # Uma nova pesquisa invalida a resposta
    # e a autorização anteriores.
    st.session_state[
        "pesquisa_salva"
    ] = None

    st.session_state[
        "resposta_ia"
    ] = None

    st.session_state[
        "autorizar_envio"
    ] = False

    pergunta = pergunta.strip()

    if (
        not extrair_palavras(
            pergunta
        )
        or len(pergunta) > 500
    ):
        st.warning(
            "Digite uma pergunta específica, "
            "com até 500 caracteres."
        )

        st.stop()

    try:
        resultados = executar_busca(
            modo_busca,
            documentos,
            pergunta,
        )

    except ValueError as erro:
        st.warning(
            str(erro)
        )

        st.stop()

    if not resultados:
        st.info(
            "Não encontrei documentos candidatos. "
            "A IA não foi consultada."
        )

        st.stop()

    st.session_state[
        "pesquisa_salva"
    ] = {
        "pergunta": pergunta,
        "resultados": resultados,
        "modo_busca": modo_busca,
    }


# -------------------------------------------------------------------
# Resultado local
# -------------------------------------------------------------------

consulta = st.session_state[
    "pesquisa_salva"
]


if consulta is None:
    st.info(
        "Faça uma pesquisa para começar."
    )

    st.stop()


resultados = consulta[
    "resultados"
]

modo_consulta = consulta.get(
    "modo_busca",
    MODO_PALAVRAS,
)

palavras = extrair_palavras(
    consulta["pergunta"]
)


st.subheader(
    "Pesquisa em análise"
)

st.text(
    consulta["pergunta"]
)

st.caption(
    f"Modo utilizado: {modo_consulta}"
)

st.caption(
    "Para mudar a pergunta, o modo de busca "
    "ou atualizar os documentos, clique em Pesquisar."
)

st.info(
    f"Documentos candidatos: {len(resultados)}"
)


for arquivo, texto, trechos in resultados:
    st.subheader(
        f"Fonte: {arquivo.name}"
    )

    encontradas = (
        palavras
        & extrair_palavras(
            texto
        )
    )

    if encontradas:
        st.caption(
            "Palavras da pergunta encontradas "
            "neste documento: "
            + ", ".join(
                sorted(
                    encontradas
                )
            )
        )

    elif modo_consulta == MODO_SEMANTICO:
        st.caption(
            "Documento recuperado pela "
            "busca semântica local."
        )

    elif modo_consulta == MODO_HIBRIDO:
        st.caption(
            "Documento selecionado pela "
            "fusão dos rankings locais."
        )

    for numero, trecho in enumerate(
        trechos,
        start=1,
    ):
        st.caption(
            f"Trecho {numero}"
        )

        conteudo = getattr(
            trecho,
            "texto",
            trecho,
        )

        st.text(
            str(
                conteudo
            )
        )

    with st.expander(
        f"Ver documento completo: {arquivo.name}"
    ):
        st.text(
            texto
        )


st.divider()

st.subheader(
    "Resposta com inteligência artificial"
)


# -------------------------------------------------------------------
# Integração com Gemini
# -------------------------------------------------------------------

try:
    import httpx

    from google.genai import errors

    from consulta_ia import (
        MODELO_PADRAO,
        gerar_resposta,
        preparar_pacote,
    )

except ImportError:
    st.info(
        "Para habilitar a IA, instale as dependências "
        "de requirements.txt."
    )

    st.stop()


try:
    pacote = preparar_pacote(
        resultados
    )

except ValueError as erro:
    st.warning(
        str(erro)
    )

    st.stop()


with st.expander(
    "Conferir exatamente os trechos que serão enviados"
):
    st.text(
        pacote.contexto
    )


# -------------------------------------------------------------------
# Configuração local
# -------------------------------------------------------------------

config = dotenv_values(
    BASE
    / ".env"
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


if (
    not chave
    or chave
    == "COLE_SUA_CHAVE_AQUI"
):
    st.warning(
        "Configure GEMINI_API_KEY no .env. "
        "A busca local continua disponível."
    )

    st.stop()


st.caption(
    f"Modelo configurado: {modelo}"
)

st.warning(
    "A pergunta em análise e os trechos selecionados "
    "serão enviados ao Google. "
    "Use somente dados fictícios e confira o Free Tier "
    "da sua conta."
)


autorizado = st.checkbox(
    (
        "Conferi a pergunta e os trechos fictícios "
        "e autorizo o envio ao Google."
    ),
    key="autorizar_envio",
)


gerar = st.button(
    "Gerar resposta com IA",
    disabled=(
        not autorizado
        or st.session_state[
            "resposta_ia"
        ]
        is not None
    ),
)


# -------------------------------------------------------------------
# Geração da resposta
# -------------------------------------------------------------------

if (
    gerar
    and autorizado
    and st.session_state[
        "resposta_ia"
    ]
    is None
):
    try:
        with st.spinner(
            "Consultando o Gemini..."
        ):
            apresentacao = gerar_resposta(
                consulta["pergunta"],
                pacote,
                chave,
                modelo,
            )

        st.session_state[
            "resposta_ia"
        ] = apresentacao_para_historico(
            apresentacao
        )

    except errors.APIError as erro:
        avisos = {
            400: (
                "Confira a chave, o modelo "
                "e a configuração da API."
            ),
            401: (
                "A autenticação falhou. "
                "Confira sua chave no .env."
            ),
            403: (
                "Acesso recusado. "
                "Confira as permissões do projeto."
            ),
            404: (
                "Modelo não encontrado. "
                "Confira GEMINI_MODEL no .env."
            ),
            429: (
                "Cota atingida ou indisponível. "
                "Confira os limites no AI Studio."
            ),
        }

        st.error(
            avisos.get(
                erro.code,
                (
                    "Falha na API. "
                    "Tente novamente mais tarde."
                ),
            )
        )

    except httpx.HTTPError:
        st.error(
            "Falha de conexão ou tempo limite. "
            "Confira sua internet."
        )

    except ValueError as erro:
        st.error(
            str(erro)
        )


# -------------------------------------------------------------------
# Resposta validada
# -------------------------------------------------------------------

if (
    st.session_state[
        "resposta_ia"
    ]
    is not None
):
    st.subheader(
        "Resposta gerada por IA — "
        "referências conferidas"
    )

    apresentacao = (
        apresentacao_do_historico(
            st.session_state[
                "resposta_ia"
            ]
        )
    )

    renderizar_resposta(
        st,
        apresentacao,
    )

    st.caption(
        "Para outra consulta, faça uma nova pesquisa."
    )


# -------------------------------------------------------------------
# Limites
# -------------------------------------------------------------------

st.caption(
    "As buscas locais selecionam documentos candidatos. "
    "A busca híbrida combina rankings e não representa "
    "probabilidade de acerto."
)