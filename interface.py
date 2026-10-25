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


# Mantém a consulta enquanto o Streamlit reexecuta a página.
st.session_state.setdefault(
    "pesquisa_salva",
    None,
)

# Guarda somente uma cópia serializável da resposta validada.
# Isso evita reconstruir posteriormente as referências lendo
# novamente os arquivos da base.
st.session_state.setdefault(
    "resposta_ia",
    None,
)

st.session_state.setdefault(
    "autorizar_envio",
    False,
)


pasta = BASE / "documentos"

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
    # Uma nova pesquisa invalida a resposta e a autorização
    # anteriores.
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
        not extrair_palavras(pergunta)
        or len(pergunta) > 500
    ):
        st.warning(
            "Digite uma pergunta específica, "
            "com até 500 caracteres."
        )
        st.stop()

    resultados = buscar_por_pergunta(
        documentos,
        pergunta,
    )

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
    }


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
    "Para mudar a pergunta ou atualizar os documentos, "
    "clique em Pesquisar."
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
        & extrair_palavras(texto)
    )

    st.caption(
        "Palavras encontradas: "
        + ", ".join(
            sorted(encontradas)
        )
    )

    for numero, trecho in enumerate(
        trechos,
        start=1,
    ):
        st.caption(
            f"Trecho {numero}"
        )

        # O contrato atual das buscas devolve
        # TrechoCandidato, mas mantemos uma
        # compatibilidade defensiva com strings antigas.
        conteudo = getattr(
            trecho,
            "texto",
            trecho,
        )

        st.text(
            str(conteudo)
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


# Lê a configuração localmente sem exibir a chave.
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

        # Salva uma cópia independente dos arquivos atuais.
        # Alterações posteriores da base não modificam a
        # evidência já apresentada ao usuário.
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
        # A resposta bruta não é salva nem exibida quando
        # falha na validação.
        st.error(
            str(erro)
        )


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