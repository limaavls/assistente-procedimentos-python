import math
import os
from functools import lru_cache
from pathlib import Path
from threading import RLock

from citacoes import TrechoCandidato


MODELO = "intfloat/multilingual-e5-small"
CACHE = Path(__file__).resolve().parent / ".cache_modelos"
MAX_TRECHOS = 500


def carregar_modelo(permitir_download: bool = False):
    """
    Carrega o modelo semântico.

    Por padrão, utiliza somente os arquivos já disponíveis
    no cache local. O download precisa ser autorizado
    explicitamente.
    """
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

    # Importação adiada para que testes simulados não precisem
    # carregar sentence-transformers.
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(
        MODELO,
        device="cpu",
        cache_folder=str(CACHE),
        local_files_only=not permitir_download,
        trust_remote_code=False,
    )


def dividir_texto(
    texto,
    tokenizador,
    tamanho=300,
    sobreposicao=50,
):
    """
    Divide o texto usando as posições reais dos tokens.

    Retorna:
        [
            (trecho, inicio_no_texto, fim_no_texto),
            ...
        ]

    As posições permitem identificar posteriormente a origem
    exata do trecho e, quando houver metadados confiáveis,
    determinar páginas de PDFs.
    """
    if not 0 <= sobreposicao < tamanho:
        raise ValueError(
            "Tamanho e sobreposição inválidos."
        )

    dados = tokenizador(
        texto,
        add_special_tokens=False,
        return_offsets_mapping=True,
        truncation=False,
    )

    posicoes = [
        (inicio, fim)
        for inicio, fim in dados["offset_mapping"]
        if fim > inicio
    ]

    if not posicoes:
        return []

    trechos = []

    passo = tamanho - sobreposicao

    for indice_inicio in range(
        0,
        len(posicoes),
        passo,
    ):
        indice_fim = min(
            indice_inicio + tamanho,
            len(posicoes),
        )

        comeco = posicoes[indice_inicio][0]
        termino = posicoes[indice_fim - 1][1]

        bruto = texto[comeco:termino]
        trecho = bruto.strip()

        if trecho:
            esquerda = (
                len(bruto)
                - len(bruto.lstrip())
            )

            direita = (
                len(bruto)
                - len(bruto.rstrip())
            )

            inicio_real = comeco + esquerda
            fim_real = termino - direita

            if (
                0 <= inicio_real
                < fim_real
                <= len(texto)
                and texto[inicio_real:fim_real]
                == trecho
            ):
                trechos.append(
                    (
                        trecho,
                        inicio_real,
                        fim_real,
                    )
                )
            else:
                # Compatibilidade defensiva caso o tokenizador
                # devolva offsets inesperados.
                trechos.append(
                    (
                        trecho,
                        None,
                        None,
                    )
                )

        if indice_fim == len(posicoes):
            break

    return trechos


class IndiceSemantico:
    def __init__(self, modelo):
        self.modelo = modelo
        self.base = None
        self.itens = []
        self.vetores = []
        self.trava = RLock()

    def codificar(self, textos):
        """
        Codifica textos e normaliza os vetores.

        Não permite truncamento silencioso.
        """
        for texto in textos:
            tokens = self.modelo.tokenizer(
                texto,
                add_special_tokens=True,
                truncation=False,
            )["input_ids"]

            if (
                len(tokens)
                > self.modelo.max_seq_length
            ):
                raise ValueError(
                    "Consulta ou trecho muito longo para o modelo. "
                    "Reduza a pergunta ou inicie uma nova conversa."
                )

        valores = self.modelo.encode(
            textos,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
            batch_size=8,
            prompt="",
        )

        if len(valores) != len(textos):
            raise ValueError(
                "Quantidade inesperada de vetores."
            )

        vetores = []

        for linha in valores:
            vetor = tuple(
                float(numero)
                for numero in linha
            )

            norma = math.sqrt(
                sum(
                    numero * numero
                    for numero in vetor
                )
            )

            if (
                not vetor
                or not math.isfinite(norma)
                or norma == 0
            ):
                raise ValueError(
                    "Vetor inválido retornado pelo modelo."
                )

            vetores.append(
                tuple(
                    numero / norma
                    for numero in vetor
                )
            )

        return vetores

    def buscar(
        self,
        documentos,
        pergunta,
    ):
        """
        Executa a busca protegida por trava para evitar alteração
        simultânea do índice.
        """
        with self.trava:
            return self._buscar(
                documentos,
                pergunta,
            )

    def _buscar(
        self,
        documentos,
        pergunta,
    ):
        if (
            not pergunta.strip()
            or not any(
                caractere.isalnum()
                for caractere in pergunta
            )
        ):
            return []

        base = tuple(
            sorted(
                (
                    str(arquivo),
                    texto,
                )
                for arquivo, texto
                in documentos
                if texto.strip()
            )
        )

        # Recalcula os embeddings dos documentos somente
        # quando a base muda.
        if base != self.base:
            itens = []

            for caminho, texto in base:
                partes = dividir_texto(
                    texto,
                    self.modelo.tokenizer,
                )

                for numero, (
                    trecho,
                    inicio,
                    fim,
                ) in enumerate(
                    partes,
                    start=1,
                ):
                    itens.append(
                        (
                            Path(caminho),
                            texto,
                            numero,
                            trecho,
                            inicio,
                            fim,
                        )
                    )

                    if (
                        len(itens)
                        > MAX_TRECHOS
                    ):
                        raise ValueError(
                            "A base excedeu 500 trechos. "
                            "Reduza os documentos desta demonstração."
                        )

            vetores = (
                self.codificar(
                    [
                        "passage: " + item[3]
                        for item in itens
                    ]
                )
                if itens
                else []
            )

            self.base = base
            self.itens = itens
            self.vetores = vetores

        if not self.itens:
            return []

        consulta = self.codificar(
            [
                "query: " + pergunta
            ]
        )[0]

        notas = [
            sum(
                a * b
                for a, b in zip(
                    consulta,
                    vetor,
                    strict=True,
                )
            )
            for vetor in self.vetores
        ]

        ordem = sorted(
            range(len(notas)),
            key=lambda indice: (
                -notas[indice],
                indice,
            ),
        )

        escolhidos = {}

        # Mantém o comportamento anterior:
        # até três documentos,
        # com até dois trechos de cada documento.
        for indice in ordem:
            (
                arquivo,
                texto,
                numero,
                trecho,
                inicio,
                fim,
            ) = self.itens[indice]

            if arquivo not in escolhidos:
                if len(escolhidos) == 3:
                    continue

                escolhidos[arquivo] = (
                    texto,
                    [],
                )

            partes = escolhidos[arquivo][1]

            if len(partes) < 2:
                partes.append(
                    (
                        numero,
                        trecho,
                        inicio,
                        fim,
                    )
                )

        resultados = []

        for arquivo, (
            texto,
            partes,
        ) in escolhidos.items():
            trechos = []

            for (
                numero,
                trecho,
                inicio,
                fim,
            ) in sorted(
                partes,
                key=lambda item: item[0],
            ):
                trechos.append(
                    TrechoCandidato(
                        texto=trecho,
                        inicio=inicio,
                        fim=fim,
                        indice_recorte=numero,
                    )
                )

            resultados.append(
                (
                    arquivo,
                    texto,
                    trechos,
                )
            )

        return resultados


@lru_cache(maxsize=1)
def obter_indice():
    """
    Mantém uma única instância local do índice semântico.
    """
    return IndiceSemantico(
        carregar_modelo()
    )


def buscar_semantico(
    documentos,
    pergunta,
):
    """
    Busca semanticamente nos documentos.

    O modelo precisa estar previamente disponível no cache.
    """
    if (
        not documentos
        or not pergunta.strip()
    ):
        return []

    try:
        return obter_indice().buscar(
            documentos,
            pergunta,
        )

    except ValueError:
        raise

    except Exception as erro:
        raise ValueError(
            "Não consegui executar a busca local. "
            "Instale requirements-semantica.txt e execute "
            "python busca_semantica.py para preparar o modelo. "
            "A busca por palavras continua disponível."
        ) from erro


if __name__ == "__main__":
    # Esta execução autoriza explicitamente o download
    # dos arquivos necessários do modelo.
    carregar_modelo(
        permitir_download=True
    )

    print(
        "Modelo preparado. "
        "As consultas semânticas usarão a cópia local."
    )