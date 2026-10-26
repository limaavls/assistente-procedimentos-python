import unittest
from pathlib import Path

import busca_hibrida as bh
from citacoes import TrechoCandidato


class TestBuscaHibrida(
    unittest.TestCase
):

    def setUp(self):
        self.doc_a = Path(
            "a.txt"
        )

        self.doc_b = Path(
            "b.txt"
        )

        self.doc_c = Path(
            "c.txt"
        )

        self.texto_a = (
            "Solicitação de material."
        )

        self.texto_b = (
            "Procedimento de frequência."
        )

        self.texto_c = (
            "Orientação administrativa."
        )

        self.documentos = [
            (
                self.doc_a,
                self.texto_a,
            ),
            (
                self.doc_b,
                self.texto_b,
            ),
            (
                self.doc_c,
                self.texto_c,
            ),
        ]

        self.trecho_a = (
            TrechoCandidato(
                texto=(
                    "Solicitação de material."
                ),
                inicio=0,
                fim=len(
                    self.texto_a
                ),
            )
        )

        self.trecho_b = (
            TrechoCandidato(
                texto=(
                    "Procedimento de frequência."
                ),
                inicio=0,
                fim=len(
                    self.texto_b
                ),
            )
        )

        self.trecho_c = (
            TrechoCandidato(
                texto=(
                    "Orientação administrativa."
                ),
                inicio=0,
                fim=len(
                    self.texto_c
                ),
            )
        )

    def test_documento_presente_nas_duas_buscas_recebe_fusao(self):
        def palavras(
            documentos,
            pergunta,
        ):
            return [
                (
                    self.doc_a,
                    self.texto_a,
                    [
                        self.trecho_a
                    ],
                ),
                (
                    self.doc_b,
                    self.texto_b,
                    [
                        self.trecho_b
                    ],
                ),
            ]

        def semantica(
            documentos,
            pergunta,
        ):
            return [
                (
                    self.doc_b,
                    self.texto_b,
                    [
                        self.trecho_b
                    ],
                ),
                (
                    self.doc_c,
                    self.texto_c,
                    [
                        self.trecho_c
                    ],
                ),
            ]

        resultado = (
            bh.buscar_hibrido(
                self.documentos,
                "material frequência",
                busca_palavras=palavras,
                busca_semantica=semantica,
            )
        )

        self.assertEqual(
            resultado[
                0
            ][0],
            self.doc_b,
        )

    def test_documentos_de_apenas_um_metodo_continuam_elegiveis(self):
        def palavras(
            documentos,
            pergunta,
        ):
            return [
                (
                    self.doc_a,
                    self.texto_a,
                    [
                        self.trecho_a
                    ],
                )
            ]

        def semantica(
            documentos,
            pergunta,
        ):
            return [
                (
                    self.doc_c,
                    self.texto_c,
                    [
                        self.trecho_c
                    ],
                )
            ]

        resultado = (
            bh.buscar_hibrido(
                self.documentos,
                "consulta",
                busca_palavras=palavras,
                busca_semantica=semantica,
            )
        )

        arquivos = {
            item[0]
            for item
            in resultado
        }

        self.assertEqual(
            arquivos,
            {
                self.doc_a,
                self.doc_c,
            },
        )

    def test_trecho_igual_encontrado_pelos_dois_metodos_nao_duplica(self):
        def palavras(
            documentos,
            pergunta,
        ):
            return [
                (
                    self.doc_a,
                    self.texto_a,
                    [
                        self.trecho_a
                    ],
                )
            ]

        def semantica(
            documentos,
            pergunta,
        ):
            return [
                (
                    self.doc_a,
                    self.texto_a,
                    [
                        self.trecho_a
                    ],
                )
            ]

        resultado = (
            bh.buscar_hibrido(
                self.documentos,
                "material",
                busca_palavras=palavras,
                busca_semantica=semantica,
            )
        )

        self.assertEqual(
            len(
                resultado[
                    0
                ][2]
            ),
            1,
        )

    def test_preserva_posicao_do_trecho(self):
        def palavras(
            documentos,
            pergunta,
        ):
            return [
                (
                    self.doc_a,
                    self.texto_a,
                    [
                        self.trecho_a
                    ],
                )
            ]

        def semantica(
            documentos,
            pergunta,
        ):
            return []

        resultado = (
            bh.buscar_hibrido(
                self.documentos,
                "material",
                busca_palavras=palavras,
                busca_semantica=semantica,
            )
        )

        trecho = (
            resultado[
                0
            ][2][0]
        )

        self.assertEqual(
            trecho.inicio,
            0,
        )

        self.assertEqual(
            trecho.fim,
            len(
                self.texto_a
            ),
        )

    def test_preserva_indice_do_recorte_semantico(self):
        semantico = (
            TrechoCandidato(
                texto=(
                    "Procedimento de frequência."
                ),
                inicio=0,
                fim=len(
                    self.texto_b
                ),
                indice_recorte=7,
            )
        )

        def palavras(
            documentos,
            pergunta,
        ):
            return []

        def semantica(
            documentos,
            pergunta,
        ):
            return [
                (
                    self.doc_b,
                    self.texto_b,
                    [
                        semantico
                    ],
                )
            ]

        resultado = (
            bh.buscar_hibrido(
                self.documentos,
                "frequência",
                busca_palavras=palavras,
                busca_semantica=semantica,
            )
        )

        self.assertEqual(
            resultado[
                0
            ][2][0]
            .indice_recorte,
            7,
        )

    def test_limita_quantidade_de_documentos(self):
        def palavras(
            documentos,
            pergunta,
        ):
            return [
                (
                    self.doc_a,
                    self.texto_a,
                    [
                        self.trecho_a
                    ],
                ),
                (
                    self.doc_b,
                    self.texto_b,
                    [
                        self.trecho_b
                    ],
                ),
                (
                    self.doc_c,
                    self.texto_c,
                    [
                        self.trecho_c
                    ],
                ),
            ]

        def semantica(
            documentos,
            pergunta,
        ):
            return []

        resultado = (
            bh.buscar_hibrido(
                self.documentos,
                "consulta",
                busca_palavras=palavras,
                busca_semantica=semantica,
                max_documentos=2,
            )
        )

        self.assertEqual(
            len(
                resultado
            ),
            2,
        )

    def test_limita_trechos_por_documento(self):
        trechos = [
            TrechoCandidato(
                texto=f"Trecho {numero}.",
                inicio=(
                    numero
                    * 20
                ),
                fim=(
                    numero
                    * 20
                    + 10
                ),
            )
            for numero
            in range(
                10
            )
        ]

        def palavras(
            documentos,
            pergunta,
        ):
            return [
                (
                    self.doc_a,
                    self.texto_a,
                    trechos,
                )
            ]

        def semantica(
            documentos,
            pergunta,
        ):
            return []

        resultado = (
            bh.buscar_hibrido(
                self.documentos,
                "consulta",
                busca_palavras=palavras,
                busca_semantica=semantica,
                max_trechos_por_documento=3,
            )
        )

        self.assertEqual(
            len(
                resultado[
                    0
                ][2]
            ),
            3,
        )

    def test_empate_e_desempatado_pelo_nome_do_arquivo(self):
        def palavras(
            documentos,
            pergunta,
        ):
            return [
                (
                    self.doc_b,
                    self.texto_b,
                    [
                        self.trecho_b
                    ],
                ),
                (
                    self.doc_a,
                    self.texto_a,
                    [
                        self.trecho_a
                    ],
                ),
            ]

        def semantica(
            documentos,
            pergunta,
        ):
            return [
                (
                    self.doc_a,
                    self.texto_a,
                    [
                        self.trecho_a
                    ],
                ),
                (
                    self.doc_b,
                    self.texto_b,
                    [
                        self.trecho_b
                    ],
                ),
            ]

        resultado = (
            bh.buscar_hibrido(
                self.documentos,
                "consulta",
                busca_palavras=palavras,
                busca_semantica=semantica,
            )
        )

        # Os dois documentos possuem a mesma soma de RRF:
        # B = posição 1 lexical + posição 2 semântica
        # A = posição 2 lexical + posição 1 semântica.
        self.assertEqual(
            [
                item[
                    0
                ].name
                for item
                in resultado
            ],
            [
                "a.txt",
                "b.txt",
            ],
        )

    def test_pergunta_vazia_nao_executa_buscas(self):
        chamadas = {
            "palavras": 0,
            "semantica": 0,
        }

        def palavras(
            documentos,
            pergunta,
        ):
            chamadas[
                "palavras"
            ] += 1

            return []

        def semantica(
            documentos,
            pergunta,
        ):
            chamadas[
                "semantica"
            ] += 1

            return []

        resultado = (
            bh.buscar_hibrido(
                self.documentos,
                "???",
                busca_palavras=palavras,
                busca_semantica=semantica,
            )
        )

        self.assertEqual(
            resultado,
            [],
        )

        self.assertEqual(
            chamadas,
            {
                "palavras": 0,
                "semantica": 0,
            },
        )

    def test_sem_resultados_retorna_lista_vazia(self):
        resultado = (
            bh.buscar_hibrido(
                self.documentos,
                "consulta",
                busca_palavras=(
                    lambda documentos, pergunta: []
                ),
                busca_semantica=(
                    lambda documentos, pergunta: []
                ),
            )
        )

        self.assertEqual(
            resultado,
            [],
        )

    def test_base_diferente_entre_as_buscas_e_rejeitada(self):
        def palavras(
            documentos,
            pergunta,
        ):
            return [
                (
                    self.doc_a,
                    "Versão 1.",
                    [
                        self.trecho_a
                    ],
                )
            ]

        def semantica(
            documentos,
            pergunta,
        ):
            return [
                (
                    self.doc_a,
                    "Versão 2.",
                    [
                        self.trecho_a
                    ],
                )
            ]

        with self.assertRaisesRegex(
            ValueError,
            "base mudou",
        ):
            bh.buscar_hibrido(
                self.documentos,
                "consulta",
                busca_palavras=palavras,
                busca_semantica=semantica,
            )

    def test_trecho_em_formato_invalido_e_rejeitado(self):
        def palavras(
            documentos,
            pergunta,
        ):
            return [
                (
                    self.doc_a,
                    self.texto_a,
                    [
                        "trecho antigo"
                    ],
                )
            ]

        def semantica(
            documentos,
            pergunta,
        ):
            return []

        with self.assertRaisesRegex(
            ValueError,
            "formato incompatível",
        ):
            bh.buscar_hibrido(
                self.documentos,
                "consulta",
                busca_palavras=palavras,
                busca_semantica=semantica,
            )

    def test_limites_invalidos_sao_rejeitados(self):
        for campo, valor in (
            (
                "max_documentos",
                0,
            ),
            (
                "max_trechos_por_documento",
                0,
            ),
        ):
            with self.subTest(
                campo=campo
            ):
                argumentos = {
                    "max_documentos": 3,
                    "max_trechos_por_documento": 4,
                }

                argumentos[
                    campo
                ] = valor

                with self.assertRaises(
                    ValueError
                ):
                    bh.buscar_hibrido(
                        self.documentos,
                        "consulta",
                        busca_palavras=(
                            lambda documentos, pergunta: []
                        ),
                        busca_semantica=(
                            lambda documentos, pergunta: []
                        ),
                        **argumentos,
                    )


if __name__ == "__main__":
    unittest.main()