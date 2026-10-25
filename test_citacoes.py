import json
import unittest
from pathlib import Path

from citacoes import (
    AVISO_CONFERENCIA,
    AVISO_PARCIAL,
    ERRO_VALIDACAO,
    MENSAGEM_SEM_EVIDENCIA,
    FonteRegistro,
    OrigemDocumento,
    TrechoCandidato,
    apresentacao_do_historico,
    apresentacao_para_historico,
    citacao_contida,
    formatar_resposta,
    interpretar_origem,
    limpar_marcadores_do_modelo,
    paginas_do_intervalo,
    preparar_envio,
    texto_para_terminal,
    validar_resposta,
)


class TestCitacoes(unittest.TestCase):

    def criar_origem_txt(self):
        return OrigemDocumento(
            arquivo="procedimento.txt",
            nome_origem=None,
            drive_id=None,
            tipo="txt",
            texto_extraido=False,
        )

    def criar_fonte(
        self,
        identificador="F1",
        documento="procedimento.txt",
        trecho="Apresente a nota fiscal e o comprovante de pagamento.",
        localizacao="Sem paginação neste formato.",
        origem=None,
        inicio=0,
        fim=None,
    ):
        if origem is None:
            origem = self.criar_origem_txt()

        if fim is None:
            fim = inicio + len(trecho)

        return FonteRegistro(
            identificador=identificador,
            documento=documento,
            trecho=trecho,
            localizacao=localizacao,
            origem=origem,
            inicio=inicio,
            fim=fim,
        )

    def test_preparar_envio_cria_referencias_deterministicas(self):
        texto = (
            "Primeiro parágrafo.\n\n"
            "Segundo parágrafo."
        )

        resultados = [
            (
                Path("procedimento.txt"),
                texto,
                [
                    TrechoCandidato(
                        texto="Primeiro parágrafo.",
                        inicio=0,
                        fim=19,
                    ),
                    TrechoCandidato(
                        texto="Segundo parágrafo.",
                        inicio=21,
                        fim=39,
                    ),
                ],
            )
        ]

        pacote = preparar_envio(
            resultados,
            max_documentos=3,
            max_caracteres=5000,
        )

        self.assertEqual(
            [
                fonte.identificador
                for fonte in pacote.registro
            ],
            ["F1", "F2"],
        )

        self.assertEqual(
            pacote.registro[0].trecho,
            "Primeiro parágrafo.",
        )

        self.assertEqual(
            pacote.registro[1].trecho,
            "Segundo parágrafo.",
        )

        self.assertIn(
            "[F1]",
            pacote.contexto,
        )

        self.assertIn(
            "[F2]",
            pacote.contexto,
        )

    def test_preparar_envio_respeita_limite_de_documentos(self):
        resultados = [
            (
                Path(f"doc{numero}.txt"),
                f"Conteúdo {numero}.",
                [
                    TrechoCandidato(
                        texto=f"Conteúdo {numero}.",
                        inicio=0,
                        fim=len(f"Conteúdo {numero}."),
                    )
                ],
            )
            for numero in range(5)
        ]

        pacote = preparar_envio(
            resultados,
            max_documentos=2,
            max_caracteres=5000,
        )

        self.assertEqual(
            pacote.documentos_recuperados,
            (
                "doc0.txt",
                "doc1.txt",
            ),
        )

        self.assertEqual(
            len(pacote.registro),
            2,
        )

    def test_preparar_envio_rejeita_contexto_acima_do_limite(self):
        resultados = [
            (
                Path("grande.txt"),
                "A" * 1000,
                [
                    TrechoCandidato(
                        texto="A" * 1000,
                        inicio=0,
                        fim=1000,
                    )
                ],
            )
        ]

        with self.assertRaises(ValueError):
            preparar_envio(
                resultados,
                max_documentos=1,
                max_caracteres=100,
            )

    def test_validar_resposta_aceita_referencia_valida(self):
        registro = (
            self.criar_fonte(),
        )

        resposta = json.dumps(
            {
                "status": "respondida",
                "itens": [
                    {
                        "texto": (
                            "É necessário apresentar os comprovantes."
                        ),
                        "evidencias": [
                            {
                                "fonte_id": "F1",
                                "citacao": (
                                    "Apresente a nota fiscal "
                                    "e o comprovante de pagamento."
                                ),
                            }
                        ],
                    }
                ],
            },
            ensure_ascii=False,
        )

        validada = validar_resposta(
            resposta,
            registro,
        )

        self.assertEqual(
            validada.status,
            "respondida",
        )

        self.assertEqual(
            len(validada.itens),
            1,
        )

        self.assertEqual(
            validada.itens[0].evidencias[0].fonte_id,
            "F1",
        )

    def test_validar_resposta_rejeita_fonte_inexistente(self):
        registro = (
            self.criar_fonte(),
        )

        resposta = json.dumps(
            {
                "status": "respondida",
                "itens": [
                    {
                        "texto": "Orientação.",
                        "evidencias": [
                            {
                                "fonte_id": "F99",
                                "citacao": "Orientação.",
                            }
                        ],
                    }
                ],
            }
        )

        with self.assertRaisesRegex(
            ValueError,
            ERRO_VALIDACAO,
        ):
            validar_resposta(
                resposta,
                registro,
            )

    def test_referencia_de_outra_consulta_e_rejeitada(self):
        registro_atual = (
            self.criar_fonte(
                identificador="F1",
                trecho="Conteúdo desta consulta.",
            ),
        )

        resposta = json.dumps(
            {
                "status": "respondida",
                "itens": [
                    {
                        "texto": "Orientação.",
                        "evidencias": [
                            {
                                "fonte_id": "F2",
                                "citacao": "Conteúdo antigo.",
                            }
                        ],
                    }
                ],
            }
        )

        with self.assertRaisesRegex(
            ValueError,
            ERRO_VALIDACAO,
        ):
            validar_resposta(
                resposta,
                registro_atual,
            )

    def test_validar_resposta_rejeita_citacao_inventada(self):
        registro = (
            self.criar_fonte(),
        )

        resposta = json.dumps(
            {
                "status": "respondida",
                "itens": [
                    {
                        "texto": "O prazo é de dez dias.",
                        "evidencias": [
                            {
                                "fonte_id": "F1",
                                "citacao": (
                                    "O prazo é de dez dias."
                                ),
                            }
                        ],
                    }
                ],
            },
            ensure_ascii=False,
        )

        with self.assertRaisesRegex(
            ValueError,
            ERRO_VALIDACAO,
        ):
            validar_resposta(
                resposta,
                registro,
            )

    def test_validar_resposta_rejeita_numero_alterado(self):
        registro = (
            self.criar_fonte(
                trecho="O prazo é de 5 dias úteis.",
            ),
        )

        resposta = json.dumps(
            {
                "status": "respondida",
                "itens": [
                    {
                        "texto": "O prazo é de 10 dias.",
                        "evidencias": [
                            {
                                "fonte_id": "F1",
                                "citacao": (
                                    "O prazo é de 10 dias úteis."
                                ),
                            }
                        ],
                    }
                ],
            },
            ensure_ascii=False,
        )

        with self.assertRaisesRegex(
            ValueError,
            ERRO_VALIDACAO,
        ):
            validar_resposta(
                resposta,
                registro,
            )

    def test_validar_resposta_rejeita_negacao_alterada(self):
        registro = (
            self.criar_fonte(
                trecho=(
                    "O documento não precisa ser assinado."
                ),
            ),
        )

        resposta = json.dumps(
            {
                "status": "respondida",
                "itens": [
                    {
                        "texto": (
                            "O documento precisa ser assinado."
                        ),
                        "evidencias": [
                            {
                                "fonte_id": "F1",
                                "citacao": (
                                    "O documento precisa ser assinado."
                                ),
                            }
                        ],
                    }
                ],
            },
            ensure_ascii=False,
        )

        with self.assertRaisesRegex(
            ValueError,
            ERRO_VALIDACAO,
        ):
            validar_resposta(
                resposta,
                registro,
            )

    def test_validar_resposta_rejeita_item_sem_evidencia(self):
        registro = (
            self.criar_fonte(),
        )

        resposta = json.dumps(
            {
                "status": "respondida",
                "itens": [
                    {
                        "texto": "Orientação sem fonte.",
                        "evidencias": [],
                    }
                ],
            }
        )

        with self.assertRaisesRegex(
            ValueError,
            ERRO_VALIDACAO,
        ):
            validar_resposta(
                resposta,
                registro,
            )

    def test_validar_resposta_rejeita_json_invalido(self):
        registro = (
            self.criar_fonte(),
        )

        with self.assertRaisesRegex(
            ValueError,
            ERRO_VALIDACAO,
        ):
            validar_resposta(
                '{"status": "respondida"',
                registro,
            )

    def test_validar_resposta_rejeita_resposta_interrompida(self):
        registro = (
            self.criar_fonte(),
        )

        resposta = (
            '{"status":"respondida","itens":['
            '{"texto":"Resposta","evidencias":['
        )

        with self.assertRaisesRegex(
            ValueError,
            ERRO_VALIDACAO,
        ):
            validar_resposta(
                resposta,
                registro,
            )

    def test_status_respondida_exige_itens(self):
        registro = (
            self.criar_fonte(),
        )

        resposta = json.dumps(
            {
                "status": "respondida",
                "itens": [],
            }
        )

        with self.assertRaisesRegex(
            ValueError,
            ERRO_VALIDACAO,
        ):
            validar_resposta(
                resposta,
                registro,
            )

    def test_status_parcial_e_formatado_com_aviso(self):
        registro = (
            self.criar_fonte(),
        )

        resposta = json.dumps(
            {
                "status": "parcial",
                "itens": [
                    {
                        "texto": (
                            "É necessário apresentar a nota fiscal."
                        ),
                        "evidencias": [
                            {
                                "fonte_id": "F1",
                                "citacao": (
                                    "Apresente a nota fiscal "
                                    "e o comprovante de pagamento."
                                ),
                            }
                        ],
                    }
                ],
            },
            ensure_ascii=False,
        )

        validada = validar_resposta(
            resposta,
            registro,
        )

        apresentacao = formatar_resposta(
            validada,
            documentos_recuperados=(
                "procedimento.txt",
            ),
        )

        self.assertEqual(
            apresentacao.status,
            "parcial",
        )

        self.assertEqual(
            apresentacao.aviso_status,
            AVISO_PARCIAL,
        )

    def test_status_sem_evidencia_usa_mensagem_fixa(self):
        resposta = json.dumps(
            {
                "status": "sem_evidencia",
                "itens": [],
            }
        )

        validada = validar_resposta(
            resposta,
            (),
        )

        apresentacao = formatar_resposta(
            validada,
        )

        self.assertEqual(
            apresentacao.mensagem_principal,
            MENSAGEM_SEM_EVIDENCIA,
        )

        self.assertEqual(
            apresentacao.fontes_citadas,
            [],
        )

    def test_sem_evidencia_rejeita_itens(self):
        registro = (
            self.criar_fonte(),
        )

        resposta = json.dumps(
            {
                "status": "sem_evidencia",
                "itens": [
                    {
                        "texto": "Não deveria existir.",
                        "evidencias": [
                            {
                                "fonte_id": "F1",
                                "citacao": (
                                    "Apresente a nota fiscal"
                                ),
                            }
                        ],
                    }
                ],
            },
            ensure_ascii=False,
        )

        with self.assertRaisesRegex(
            ValueError,
            ERRO_VALIDACAO,
        ):
            validar_resposta(
                resposta,
                registro,
            )

    def test_formatacao_nao_duplica_fonte_repetida(self):
        registro = (
            self.criar_fonte(),
        )

        resposta = json.dumps(
            {
                "status": "respondida",
                "itens": [
                    {
                        "texto": "Primeira orientação.",
                        "evidencias": [
                            {
                                "fonte_id": "F1",
                                "citacao": (
                                    "Apresente a nota fiscal"
                                ),
                            }
                        ],
                    },
                    {
                        "texto": "Segunda orientação.",
                        "evidencias": [
                            {
                                "fonte_id": "F1",
                                "citacao": (
                                    "comprovante de pagamento"
                                ),
                            }
                        ],
                    },
                ],
            },
            ensure_ascii=False,
        )

        validada = validar_resposta(
            resposta,
            registro,
        )

        apresentacao = formatar_resposta(
            validada,
            documentos_recuperados=(
                "procedimento.txt",
            ),
        )

        self.assertEqual(
            len(apresentacao.fontes_citadas),
            1,
        )

        self.assertEqual(
            apresentacao.fontes_citadas[0].identificador,
            "F1",
        )

        self.assertEqual(
            len(
                apresentacao.fontes_citadas[0].citacoes
            ),
            2,
        )

    def test_marcadores_do_modelo_sao_removidos(self):
        texto = (
            "Apresente a documentação. [F1]"
        )

        self.assertEqual(
            limpar_marcadores_do_modelo(texto),
            "Apresente a documentação.",
        )

    def test_citacao_permite_apenas_normalizacao_de_espacos(self):
        trecho = (
            "Apresente a nota fiscal\n"
            "e o comprovante."
        )

        self.assertTrue(
            citacao_contida(
                trecho,
                "Apresente a nota fiscal e o comprovante.",
            )
        )

        self.assertFalse(
            citacao_contida(
                trecho,
                "Apresente a nota fiscal e não o comprovante.",
            )
        )

    def test_txt_nao_recebe_paginacao_inventada(self):
        texto = (
            "Documento simples em texto."
        )

        origem = interpretar_origem(
            "arquivo.txt",
            texto,
        )

        resultados = [
            (
                Path("arquivo.txt"),
                texto,
                [
                    TrechoCandidato(
                        texto=texto,
                        inicio=0,
                        fim=len(texto),
                    )
                ],
            )
        ]

        pacote = preparar_envio(
            resultados,
            max_documentos=1,
            max_caracteres=1000,
        )

        self.assertEqual(
            origem.tipo,
            "txt",
        )

        self.assertEqual(
            pacote.registro[0].localizacao,
            "Sem paginação neste formato.",
        )

    def test_docx_extraido_nao_recebe_paginacao_inventada(self):
        texto = (
            "Arquivo de origem: manual.docx\n\n"
            "Conteúdo do documento."
        )

        resultados = [
            (
                Path("manual_extraido.txt"),
                texto,
                [
                    TrechoCandidato(
                        texto="Conteúdo do documento.",
                        inicio=31,
                        fim=53,
                    )
                ],
            )
        ]

        pacote = preparar_envio(
            resultados,
            max_documentos=1,
            max_caracteres=1000,
        )

        self.assertEqual(
            pacote.registro[0].origem.tipo,
            "docx",
        )

        self.assertEqual(
            pacote.registro[0].localizacao,
            "Sem paginação neste formato.",
        )

    def test_pdf_identifica_pagina_quando_marcador_existe(self):
        texto = (
            "[Página 1]\n"
            "Introdução.\n"
            "[Página 2]\n"
            "Procedimento especial."
        )

        inicio = texto.index(
            "Procedimento especial."
        )

        fim = (
            inicio
            + len("Procedimento especial.")
        )

        self.assertEqual(
            paginas_do_intervalo(
                texto,
                inicio,
                fim,
            ),
            "Página 2",
        )

    def test_pdf_identifica_intervalo_de_paginas(self):
        texto = (
            "[Página 1]\n"
            "Início do procedimento.\n"
            "[Página 2]\n"
            "Continuação do procedimento."
        )

        inicio = texto.index(
            "Início do procedimento."
        )

        fim = len(texto)

        self.assertEqual(
            paginas_do_intervalo(
                texto,
                inicio,
                fim,
            ),
            "Páginas 1-2",
        )

    def test_pdf_sem_metadados_nao_inventa_pagina(self):
        texto = (
            "Arquivo de origem: procedimento.pdf\n\n"
            "Texto sem marcador de página."
        )

        resultados = [
            (
                Path("procedimento_extraido.txt"),
                texto,
                [
                    TrechoCandidato(
                        texto="Texto sem marcador de página.",
                        inicio=38,
                        fim=67,
                    )
                ],
            )
        ]

        pacote = preparar_envio(
            resultados,
            max_documentos=1,
            max_caracteres=1000,
        )

        self.assertEqual(
            pacote.registro[0].localizacao,
            (
                "Página não determinada "
                "(metadados insuficientes)."
            ),
        )

    def test_trecho_repetido_preserva_posicao_recebida(self):
        texto = (
            "Regra repetida.\n\n"
            "Outro conteúdo.\n\n"
            "Regra repetida."
        )

        segunda_posicao = texto.rindex(
            "Regra repetida."
        )

        resultados = [
            (
                Path("repetido.txt"),
                texto,
                [
                    TrechoCandidato(
                        texto="Regra repetida.",
                        inicio=segunda_posicao,
                        fim=(
                            segunda_posicao
                            + len("Regra repetida.")
                        ),
                    )
                ],
            )
        ]

        pacote = preparar_envio(
            resultados,
            max_documentos=1,
            max_caracteres=1000,
        )

        fonte = pacote.registro[0]

        self.assertEqual(
            fonte.inicio,
            segunda_posicao,
        )

        self.assertEqual(
            texto[
                fonte.inicio:
                fonte.fim
            ],
            "Regra repetida.",
        )

    def test_historico_preserva_fontes_sem_reler_arquivo(self):
        registro = (
            self.criar_fonte(),
        )

        resposta = json.dumps(
            {
                "status": "respondida",
                "itens": [
                    {
                        "texto": "Orientação.",
                        "evidencias": [
                            {
                                "fonte_id": "F1",
                                "citacao": (
                                    "Apresente a nota fiscal"
                                ),
                            }
                        ],
                    }
                ],
            },
            ensure_ascii=False,
        )

        validada = validar_resposta(
            resposta,
            registro,
        )

        apresentacao = formatar_resposta(
            validada,
            documentos_recuperados=(
                "procedimento.txt",
            ),
        )

        historico = apresentacao_para_historico(
            apresentacao
        )

        historico["fontes_citadas"][0]["trecho"] = (
            "Trecho preservado no histórico."
        )

        restaurada = apresentacao_do_historico(
            historico
        )

        self.assertEqual(
            restaurada.fontes_citadas[0].trecho,
            "Trecho preservado no histórico.",
        )

    def test_documentos_recuperados_nao_citados_ficam_separados(self):
        registro = (
            self.criar_fonte(),
        )

        resposta = json.dumps(
            {
                "status": "respondida",
                "itens": [
                    {
                        "texto": "Orientação.",
                        "evidencias": [
                            {
                                "fonte_id": "F1",
                                "citacao": (
                                    "Apresente a nota fiscal"
                                ),
                            }
                        ],
                    }
                ],
            },
            ensure_ascii=False,
        )

        validada = validar_resposta(
            resposta,
            registro,
        )

        apresentacao = formatar_resposta(
            validada,
            documentos_recuperados=(
                "procedimento.txt",
                "outro.txt",
            ),
        )

        self.assertEqual(
            apresentacao.nao_citados,
            ["outro.txt"],
        )

    def test_texto_terminal_inclui_aviso_de_conferencia(self):
        resposta = json.dumps(
            {
                "status": "sem_evidencia",
                "itens": [],
            }
        )

        validada = validar_resposta(
            resposta,
            (),
        )

        apresentacao = formatar_resposta(
            validada,
        )

        texto = texto_para_terminal(
            apresentacao
        )

        self.assertIn(
            AVISO_CONFERENCIA,
            texto,
        )


if __name__ == "__main__":
    unittest.main()