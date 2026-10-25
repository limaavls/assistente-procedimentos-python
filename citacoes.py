import json
import re
from dataclasses import dataclass, field

MENSAGEM_SEM_EVIDENCIA = (
    "Não encontrei essa informação nos trechos consultados."
)
AVISO_PARCIAL = (
    "Informação incompleta nos trechos consultados. "
    "Não há orientação adicional sem referência."
)
AVISO_CONFERENCIA = (
    "Referências conferidas quanto à existência e ao trecho. "
    "A interpretação da resposta ainda exige revisão."
)
ERRO_VALIDACAO = (
    "A resposta da IA não passou na conferência das referências. "
    "Nenhum texto gerado foi apresentado."
)

ESTADOS = frozenset({"respondida", "parcial", "sem_evidencia"})
DRIVE_ID = re.compile(r"^[A-Za-z0-9_-]{10,128}$")
MARCADOR_MODELO = re.compile(r"\[F\d+\]")
MARCADOR_PAGINA = re.compile(r"\[Página (\d+)\]")


@dataclass(frozen=True)
class TrechoCandidato:
    texto: str
    inicio: int | None = None
    fim: int | None = None
    indice_recorte: int | None = None


@dataclass(frozen=True)
class OrigemDocumento:
    arquivo: str
    nome_origem: str | None
    drive_id: str | None
    tipo: str
    texto_extraido: bool


@dataclass(frozen=True)
class FonteRegistro:
    identificador: str
    documento: str
    trecho: str
    localizacao: str
    origem: OrigemDocumento
    inicio: int | None = None
    fim: int | None = None


@dataclass(frozen=True)
class EvidenciaValidada:
    fonte_id: str
    citacao: str


@dataclass(frozen=True)
class ItemValidado:
    texto: str
    evidencias: tuple[EvidenciaValidada, ...]


@dataclass(frozen=True)
class PacoteEnvio:
    contexto: str
    registro: tuple[FonteRegistro, ...]
    documentos_recuperados: tuple[str, ...]


@dataclass(frozen=True)
class RespostaValidada:
    status: str
    itens: tuple[ItemValidado, ...]
    registro: tuple[FonteRegistro, ...]


@dataclass
class FonteApresentada:
    identificador: str
    documento: str
    localizacao: str
    trecho: str
    citacoes: list[str]
    texto_extraido: bool
    link_drive: str | None = None


@dataclass
class ApresentacaoResposta:
    status: str
    mensagem_principal: str
    linhas_itens: list[str] = field(default_factory=list)
    aviso_status: str | None = None
    aviso_conferencia: str = AVISO_CONFERENCIA
    fontes_citadas: list[FonteApresentada] = field(default_factory=list)
    nao_citados: list[str] = field(default_factory=list)


def normalizar_espacos(texto: str) -> str:
    """Junta espaços e quebras de linha. Não altera letras, acentos ou dígitos."""
    return " ".join(texto.split())


def tipo_por_nome(nome: str | None) -> str:
    if not nome:
        return "desconhecido"

    sufixo = nome.rsplit(".", 1)[-1].lower() if "." in nome else ""
    if sufixo == "pdf":
        return "pdf"
    if sufixo == "docx":
        return "docx"
    if sufixo in {"txt", "text"}:
        return "txt"
    return "desconhecido"


def interpretar_origem(nome_arquivo: str, texto: str) -> OrigemDocumento:
    linhas = texto.splitlines()
    primeira = linhas[0].strip() if linhas else ""
    nome_origem = None
    drive_id = None
    texto_extraido = False

    if primeira.startswith("Arquivo de origem:"):
        nome_origem = primeira.split(":", 1)[1].strip() or None
        texto_extraido = True
        tipo = tipo_por_nome(nome_origem)
    elif primeira.startswith("Fonte no Google Drive:"):
        nome_origem = primeira.split(":", 1)[1].strip() or None
        texto_extraido = True
        for linha in linhas[1:5]:
            if linha.startswith("ID:"):
                candidato = linha.split(":", 1)[1].strip()
                if DRIVE_ID.fullmatch(candidato):
                    drive_id = candidato
                break
        tipo = tipo_por_nome(nome_origem)
        if tipo == "desconhecido":
            tipo = "gdoc"
    else:
        tipo = tipo_por_nome(nome_arquivo)
        if tipo not in {"txt", "desconhecido"}:
            texto_extraido = True

    return OrigemDocumento(
        arquivo=nome_arquivo,
        nome_origem=nome_origem,
        drive_id=drive_id,
        tipo=tipo,
        texto_extraido=texto_extraido,
    )


def paginas_do_intervalo(
    texto: str, inicio: int, fim: int
) -> str | None:
    if inicio is None or fim is None:
        return None
    if not 0 <= inicio < fim <= len(texto):
        return None

    marcadores = list(MARCADOR_PAGINA.finditer(texto))
    if not marcadores:
        return None

    tocadas: list[int] = []
    for indice, marcador in enumerate(marcadores):
        comeco = marcador.start()
        termino = (
            marcadores[indice + 1].start()
            if indice + 1 < len(marcadores)
            else len(texto)
        )
        if inicio < termino and fim > comeco:
            tocadas.append(int(marcador.group(1)))

    if not tocadas:
        return None

    primeira, ultima = tocadas[0], tocadas[-1]
    if primeira == ultima:
        return f"Página {primeira}"
    return f"Páginas {primeira}-{ultima}"


def descrever_localizacao(
    origem: OrigemDocumento,
    texto: str,
    inicio: int | None,
    fim: int | None,
) -> str:
    if origem.tipo == "pdf":
        pagina = paginas_do_intervalo(texto, inicio, fim)
        if pagina:
            return pagina
        return "Página não determinada (metadados insuficientes)."

    if origem.tipo in {"txt", "docx", "gdoc"}:
        return "Sem paginação neste formato."

    return "Localização não disponível (metadados insuficientes)."


def link_drive(origem: OrigemDocumento) -> str | None:
    if origem.drive_id and DRIVE_ID.fullmatch(origem.drive_id):
        return (
            "https://drive.google.com/file/d/"
            f"{origem.drive_id}/view"
        )
    return None


def _como_trecho(item: TrechoCandidato | str) -> TrechoCandidato:
    if isinstance(item, TrechoCandidato):
        return item
    return TrechoCandidato(texto=item)


def preparar_envio(
    resultados: list[tuple],
    max_documentos: int,
    max_caracteres: int,
) -> PacoteEnvio:
    """Cria identificadores F1, F2... só para os trechos desta consulta."""
    fontes: list[FonteRegistro] = []
    blocos: list[str] = []
    documentos: list[str] = []
    numero = 0

    for arquivo, texto, trechos in resultados[:max_documentos]:
        origem = interpretar_origem(arquivo.name, texto)
        enviados = []

        for bruto in trechos:
            trecho = _como_trecho(bruto)
            conteudo = trecho.texto.strip()
            if not conteudo:
                continue

            numero += 1
            identificador = f"F{numero}"
            fonte = FonteRegistro(
                identificador=identificador,
                documento=arquivo.name,
                trecho=conteudo,
                localizacao=descrever_localizacao(
                    origem,
                    texto,
                    trecho.inicio,
                    trecho.fim,
                ),
                origem=origem,
                inicio=trecho.inicio,
                fim=trecho.fim,
            )
            fontes.append(fonte)
            enviados.append(
                f"[{identificador}]\n"
                f"Documento: {arquivo.name}\n"
                f"Trecho:\n{conteudo}"
            )

        if enviados:
            documentos.append(arquivo.name)
            blocos.append("\n\n".join(enviados))

    contexto = "\n\n---\n\n".join(blocos)

    if not contexto.strip() or not fontes:
        raise ValueError("Nenhum trecho disponível para enviar.")

    if len(contexto) > max_caracteres:
        raise ValueError(
            "Há texto demais. Faça uma pergunta mais específica."
        )

    return PacoteEnvio(
        contexto=contexto,
        registro=tuple(fontes),
        documentos_recuperados=tuple(documentos),
    )


def citacao_contida(trecho: str, citacao: str) -> bool:
    normal_citacao = normalizar_espacos(citacao)
    normal_trecho = normalizar_espacos(trecho)
    if not normal_citacao or not normal_trecho:
        return False
    return normal_citacao in normal_trecho


def limpar_marcadores_do_modelo(texto: str) -> str:
    limpo = MARCADOR_MODELO.sub("", texto)
    limpo = re.sub(r"[ \t]+", " ", limpo)
    return "\n".join(
        linha.rstrip() for linha in limpo.splitlines()
    ).strip()


def _exige(condicao: bool) -> None:
    if not condicao:
        raise ValueError(ERRO_VALIDACAO)


def validar_resposta(
    bruto: str, registro: tuple[FonteRegistro, ...]
) -> RespostaValidada:
    """Valida o JSON contra o registro local desta consulta."""
    indice = {fonte.identificador: fonte for fonte in registro}

    try:
        dados = json.loads(bruto)
    except (TypeError, json.JSONDecodeError) as erro:
        raise ValueError(ERRO_VALIDACAO) from erro

    _exige(isinstance(dados, dict))
    status = dados.get("status")
    itens_brutos = dados.get("itens")
    _exige(status in ESTADOS)
    _exige(isinstance(itens_brutos, list))

    itens: list[ItemValidado] = []

    for item in itens_brutos:
        _exige(isinstance(item, dict))
        texto = item.get("texto")
        evidencias_brutas = item.get("evidencias")
        _exige(isinstance(texto, str) and texto.strip())
        _exige(isinstance(evidencias_brutas, list) and evidencias_brutas)

        evidencias: list[EvidenciaValidada] = []
        for evidencia in evidencias_brutas:
            _exige(isinstance(evidencia, dict))
            fonte_id = evidencia.get("fonte_id")
            citacao = evidencia.get("citacao")
            _exige(isinstance(fonte_id, str) and fonte_id in indice)
            _exige(isinstance(citacao, str) and citacao.strip())
            _exige(citacao_contida(indice[fonte_id].trecho, citacao))
            evidencias.append(
                EvidenciaValidada(
                    fonte_id=fonte_id,
                    citacao=citacao.strip(),
                )
            )

        itens.append(
            ItemValidado(
                texto=limpar_marcadores_do_modelo(texto),
                evidencias=tuple(evidencias),
            )
        )

    if status == "sem_evidencia":
        _exige(not itens)
    else:
        _exige(bool(itens))

    return RespostaValidada(
        status=status,
        itens=tuple(itens),
        registro=registro,
    )


def formatar_resposta(
    resposta: RespostaValidada,
    documentos_recuperados: tuple[str, ...] = (),
) -> ApresentacaoResposta:
    indice = {fonte.identificador: fonte for fonte in resposta.registro}

    if resposta.status == "sem_evidencia":
        return ApresentacaoResposta(
            status=resposta.status,
            mensagem_principal=MENSAGEM_SEM_EVIDENCIA,
            nao_citados=list(documentos_recuperados),
        )

    linhas = []
    ordem_fontes: list[str] = []
    citacoes_por_fonte: dict[str, list[str]] = {}

    for item in resposta.itens:
        ids: list[str] = []
        for evidencia in item.evidencias:
            if evidencia.fonte_id not in ids:
                ids.append(evidencia.fonte_id)
            if evidencia.fonte_id not in ordem_fontes:
                ordem_fontes.append(evidencia.fonte_id)
            lista = citacoes_por_fonte.setdefault(evidencia.fonte_id, [])
            if evidencia.citacao not in lista:
                lista.append(evidencia.citacao)

        marcadores = " ".join(f"[{identificador}]" for identificador in ids)
        linhas.append(f"{item.texto} {marcadores}".strip())

    fontes = []
    for identificador in ordem_fontes:
        fonte = indice[identificador]
        fontes.append(
            FonteApresentada(
                identificador=identificador,
                documento=fonte.documento,
                localizacao=fonte.localizacao,
                trecho=fonte.trecho,
                citacoes=citacoes_por_fonte[identificador],
                texto_extraido=fonte.origem.texto_extraido,
                link_drive=link_drive(fonte.origem),
            )
        )

    citados = {fonte.documento for fonte in fontes}
    nao_citados = [
        nome for nome in documentos_recuperados if nome not in citados
    ]

    return ApresentacaoResposta(
        status=resposta.status,
        mensagem_principal="",
        linhas_itens=linhas,
        aviso_status=(
            AVISO_PARCIAL if resposta.status == "parcial" else None
        ),
        fontes_citadas=fontes,
        nao_citados=nao_citados,
    )


def apresentacao_para_historico(
    apresentacao: ApresentacaoResposta,
) -> dict:
    """Cópia serializável dos trechos desta consulta, sem reler arquivos."""
    return {
        "status": apresentacao.status,
        "mensagem_principal": apresentacao.mensagem_principal,
        "linhas_itens": list(apresentacao.linhas_itens),
        "aviso_status": apresentacao.aviso_status,
        "aviso_conferencia": apresentacao.aviso_conferencia,
        "fontes_citadas": [
            {
                "identificador": fonte.identificador,
                "documento": fonte.documento,
                "localizacao": fonte.localizacao,
                "trecho": fonte.trecho,
                "citacoes": list(fonte.citacoes),
                "texto_extraido": fonte.texto_extraido,
                "link_drive": fonte.link_drive,
            }
            for fonte in apresentacao.fontes_citadas
        ],
        "nao_citados": list(apresentacao.nao_citados),
    }


def apresentacao_do_historico(dados: dict) -> ApresentacaoResposta:
    fontes = [
        FonteApresentada(
            identificador=item["identificador"],
            documento=item["documento"],
            localizacao=item["localizacao"],
            trecho=item["trecho"],
            citacoes=list(item["citacoes"]),
            texto_extraido=bool(item.get("texto_extraido")),
            link_drive=item.get("link_drive"),
        )
        for item in dados.get("fontes_citadas", [])
    ]
    return ApresentacaoResposta(
        status=dados["status"],
        mensagem_principal=dados.get("mensagem_principal", ""),
        linhas_itens=list(dados.get("linhas_itens", [])),
        aviso_status=dados.get("aviso_status"),
        aviso_conferencia=dados.get(
            "aviso_conferencia", AVISO_CONFERENCIA
        ),
        fontes_citadas=fontes,
        nao_citados=list(dados.get("nao_citados", [])),
    )


def texto_para_terminal(apresentacao: ApresentacaoResposta) -> str:
    partes: list[str] = []

    if apresentacao.status == "sem_evidencia":
        partes.append(apresentacao.mensagem_principal)
    else:
        partes.extend(apresentacao.linhas_itens)
        if apresentacao.aviso_status:
            partes.append(apresentacao.aviso_status)

    partes.append(apresentacao.aviso_conferencia)

    if apresentacao.fontes_citadas:
        partes.append("\nFontes citadas:")
        for fonte in apresentacao.fontes_citadas:
            partes.append(
                f"- {fonte.identificador} — {fonte.documento}"
            )
            partes.append(f"  {fonte.localizacao}")
            if fonte.texto_extraido:
                partes.append(
                    "  Conteúdo exibido como texto extraído, "
                    "não como o arquivo original."
                )
            if fonte.link_drive:
                partes.append(f"  {fonte.link_drive}")
            partes.append("  Trecho enviado:")
            partes.append(fonte.trecho)
            partes.append("  Passagem citada:")
            partes.append("\n".join(fonte.citacoes))

    if apresentacao.nao_citados:
        partes.append("\nDocumentos recuperados não citados:")
        for nome in apresentacao.nao_citados:
            partes.append(f"- {nome}")

    return "\n".join(partes)


def renderizar_resposta(st, apresentacao: ApresentacaoResposta) -> None:
    if apresentacao.status == "sem_evidencia":
        st.text(apresentacao.mensagem_principal)
    else:
        for linha in apresentacao.linhas_itens:
            st.text(linha)
        if apresentacao.aviso_status:
            st.warning(apresentacao.aviso_status)

    st.caption(apresentacao.aviso_conferencia)

    with st.expander("Fontes citadas"):
        if not apresentacao.fontes_citadas:
            st.caption("Nenhuma fonte foi citada nesta resposta.")
        for fonte in apresentacao.fontes_citadas:
            st.text(f"{fonte.identificador} — {fonte.documento}")
            st.caption(fonte.localizacao)
            if fonte.texto_extraido:
                st.caption(
                    "Conteúdo exibido como texto extraído, "
                    "não como o arquivo original."
                )
            if fonte.link_drive:
                st.caption("Endereço montado a partir do ID local do Drive.")
                st.text(fonte.link_drive)
            st.text("Trecho enviado:\n" + fonte.trecho)
            st.text(
                "Passagem citada:\n" + "\n".join(fonte.citacoes)
            )

    if apresentacao.nao_citados:
        with st.expander("Documentos recuperados não citados"):
            for nome in apresentacao.nao_citados:
                st.text(nome)
