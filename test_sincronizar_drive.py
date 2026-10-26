import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import sincronizar_drive as sd


class TestSincronizarDrive(
    unittest.TestCase
):

    def setUp(self):
        temporaria = (
            TemporaryDirectory()
        )

        self.addCleanup(
            temporaria.cleanup
        )

        self.base = Path(
            temporaria.name
        )

        self.pasta = (
            self.base
            / "documentos"
        )

        self.estado = (
            self.base
            / ".estado_drive"
        )

        self.nome = (
            "drive_"
            + "a" * 24
            + ".txt"
        )

        self.pasta_id = (
            "pasta_ficticia_123"
        )

    def aplicar(
        self,
        dados,
    ):
        return sd.aplicar_copias(
            self.pasta,
            self.estado,
            self.pasta_id,
            dados,
        )

    def test_formatos_incluem_imagens_ocr(self):
        esperados = {
            "text/plain": ".txt",
            "application/pdf": ".pdf",
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/bmp": ".bmp",
            "image/tiff": ".tiff",
            "image/webp": ".webp",
        }

        for tipo, extensao in (
            esperados.items()
        ):
            with self.subTest(
                tipo=tipo
            ):
                self.assertEqual(
                    sd.FORMATOS[
                        tipo
                    ],
                    extensao,
                )

    def test_cria_copia_e_registro(self):
        resultado = self.aplicar(
            {
                self.nome:
                b"Primeira versao."
            }
        )

        self.assertEqual(
            resultado[
                "incluidos"
            ],
            1,
        )

        self.assertEqual(
            (
                self.pasta
                / self.nome
            ).read_bytes(),
            b"Primeira versao.",
        )

        registro = json.loads(
            (
                self.estado
                / "manifesto.json"
            ).read_text(
                encoding="utf-8"
            )
        )

        self.assertIn(
            self.nome,
            registro[
                "arquivos"
            ],
        )

    def test_repeticao_nao_duplica(self):
        self.aplicar(
            {
                self.nome:
                b"Conteudo."
            }
        )

        resultado = self.aplicar(
            {
                self.nome:
                b"Conteudo."
            }
        )

        self.assertEqual(
            resultado[
                "mantidos"
            ],
            1,
        )

        self.assertEqual(
            len(
                list(
                    self.pasta.glob(
                        "*.txt"
                    )
                )
            ),
            1,
        )

    def test_atualiza_e_preserva_backup(self):
        self.aplicar(
            {
                self.nome:
                b"Antes."
            }
        )

        resultado = self.aplicar(
            {
                self.nome:
                b"Depois."
            }
        )

        self.assertEqual(
            resultado[
                "atualizados"
            ],
            1,
        )

        self.assertEqual(
            (
                self.pasta
                / self.nome
            ).read_bytes(),
            b"Depois.",
        )

        self.assertTrue(
            any(
                arquivo.read_bytes()
                == b"Antes."
                for arquivo
                in self.estado.glob(
                    "historico/*/"
                    + self.nome
                )
            )
        )

    def test_retirada_preserva_arquivos_manuais(self):
        self.aplicar(
            {
                self.nome:
                b"Conteudo do Drive."
            }
        )

        manual = (
            self.pasta
            / "meu_exercicio.txt"
        )

        manual.write_text(
            "Nao apagar.",
            encoding="utf-8",
        )

        resultado = self.aplicar(
            {}
        )

        self.assertEqual(
            resultado[
                "retirados"
            ],
            1,
        )

        self.assertFalse(
            (
                self.pasta
                / self.nome
            ).exists()
        )

        self.assertEqual(
            manual.read_text(
                encoding="utf-8"
            ),
            "Nao apagar.",
        )

        self.assertTrue(
            list(
                self.estado.glob(
                    "historico/*/"
                    + self.nome
                )
            )
        )

    def test_edicao_local_interrompe_atualizacao(self):
        self.aplicar(
            {
                self.nome:
                b"Versao original."
            }
        )

        (
            self.pasta
            / self.nome
        ).write_bytes(
            b"Edicao manual."
        )

        with self.assertRaises(
            ValueError
        ):
            self.aplicar(
                {
                    self.nome:
                    b"Outra versao."
                }
            )

        self.assertEqual(
            (
                self.pasta
                / self.nome
            ).read_bytes(),
            b"Edicao manual.",
        )

    def test_colisao_com_arquivo_nao_registrado(self):
        self.pasta.mkdir()

        (
            self.pasta
            / self.nome
        ).write_bytes(
            b"Arquivo particular."
        )

        with self.assertRaises(
            ValueError
        ):
            self.aplicar(
                {
                    self.nome:
                    b"Conteudo do Drive."
                }
            )

        self.assertEqual(
            (
                self.pasta
                / self.nome
            ).read_bytes(),
            b"Arquivo particular.",
        )

    def test_rejeita_caminho_invalido_e_troca_de_pasta(self):
        with self.assertRaises(
            ValueError
        ):
            self.aplicar(
                {
                    "../fora.txt":
                    b"Invalido."
                }
            )

        self.aplicar(
            {
                self.nome:
                b"Conteudo."
            }
        )

        with self.assertRaises(
            ValueError
        ):
            sd.aplicar_copias(
                self.pasta,
                self.estado,
                "outra_pasta",
                {},
            )

    def test_falha_de_gravacao_tenta_restaurar_versao_anterior(self):
        self.aplicar(
            {
                self.nome:
                b"Antes."
            }
        )

        manifesto = (
            self.estado
            / "manifesto.json"
        ).read_bytes()

        original = (
            sd.gravar
        )

        chamadas = []

        def falhar_uma_vez(
            caminho,
            dados,
        ):
            chamadas.append(
                caminho
            )

            if len(
                chamadas
            ) == 2:
                raise OSError(
                    "Falha simulada "
                    "na gravacao do registro."
                )

            original(
                caminho,
                dados,
            )

        with patch.object(
            sd,
            "gravar",
            side_effect=(
                falhar_uma_vez
            ),
        ):
            with self.assertRaises(
                OSError
            ):
                self.aplicar(
                    {
                        self.nome:
                        b"Depois."
                    }
                )

        self.assertEqual(
            (
                self.pasta
                / self.nome
            ).read_bytes(),
            b"Antes.",
        )

        self.assertEqual(
            (
                self.estado
                / "manifesto.json"
            ).read_bytes(),
            manifesto,
        )

    def test_erro_de_download_nao_aplica_mudancas(self):
        self.aplicar(
            {
                self.nome:
                b"Antes."
            }
        )

        itens = [
            {
                "id": "abc123",
                "name": "teste.txt",
                "mimeType": "text/plain",
            }
        ]

        with patch(
            "verificar_drive.listar_pasta",
            return_value=(
                {},
                itens,
            ),
        ):
            with patch.object(
                sd,
                "baixar_texto",
                side_effect=ValueError(
                    "Falha simulada."
                ),
            ):
                with self.assertRaises(
                    ValueError
                ):
                    sd.sincronizar(
                        MagicMock(),
                        self.pasta_id,
                        self.base,
                    )

        self.assertEqual(
            (
                self.pasta
                / self.nome
            ).read_bytes(),
            b"Antes.",
        )

    def test_imagem_agora_e_selecionada_na_sincronizacao(self):
        itens = [
            {
                "id": "texto",
                "name": "procedimento.txt",
                "mimeType": "text/plain",
            },
            {
                "id": "imagem",
                "name": "scan.png",
                "mimeType": "image/png",
            },
            {
                "id": "nao_suportado",
                "name": "planilha.xlsx",
                "mimeType": (
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
            },
        ]

        def resposta_download(
            servico,
            item,
            pasta_id,
        ):
            return (
                f"Fonte no Google Drive: "
                f"{item['name']}\n"
                f"ID: {item['id']}\n\n"
                "Conteúdo convertido."
            )

        with patch(
            "verificar_drive.listar_pasta",
            return_value=(
                {},
                itens,
            ),
        ):
            with patch.object(
                sd,
                "baixar_texto",
                side_effect=(
                    resposta_download
                ),
            ) as baixar:
                resultado = (
                    sd.sincronizar(
                        MagicMock(),
                        self.pasta_id,
                        self.base,
                    )
                )

        self.assertEqual(
            baixar.call_count,
            2,
        )

        ids_baixados = {
            chamada.args[1][
                "id"
            ]
            for chamada
            in baixar.call_args_list
        }

        self.assertEqual(
            ids_baixados,
            {
                "texto",
                "imagem",
            },
        )

        self.assertEqual(
            resultado[
                "ignorados"
            ],
            1,
        )

        self.assertEqual(
            resultado[
                "incluidos"
            ],
            2,
        )

    def test_mesmo_id_continua_sem_duplicar(self):
        itens = [
            {
                "id": "mesmo_id",
                "name": "antes.png",
                "mimeType": "image/png",
            }
        ]

        with patch(
            "verificar_drive.listar_pasta",
            return_value=(
                {},
                itens,
            ),
        ):
            with patch.object(
                sd,
                "baixar_texto",
                return_value=(
                    "Primeira versao."
                ),
            ):
                primeiro = (
                    sd.sincronizar(
                        MagicMock(),
                        self.pasta_id,
                        self.base,
                    )
                )

            itens[0][
                "name"
            ] = "renomeado.png"

            with patch.object(
                sd,
                "baixar_texto",
                return_value=(
                    "Versao nova."
                ),
            ):
                segundo = (
                    sd.sincronizar(
                        MagicMock(),
                        self.pasta_id,
                        self.base,
                    )
                )

        self.assertEqual(
            primeiro[
                "incluidos"
            ],
            1,
        )

        self.assertEqual(
            segundo[
                "atualizados"
            ],
            1,
        )

        self.assertEqual(
            len(
                list(
                    self.pasta.glob(
                        "drive_*.txt"
                    )
                )
            ),
            1,
        )

    def test_baixar_imagem_envia_extensao_correta_para_extracao(self):
        arquivos = MagicMock()

        meta = {
            "id": "img1",
            "name": "foto.png",
            "mimeType": "image/png",
            "size": "100",
            "version": "1",
            "parents": [
                self.pasta_id
            ],
            "trashed": False,
            "capabilities": {
                "canDownload": True
            },
        }

        depois = {
            "version": "1",
            "parents": [
                self.pasta_id
            ],
            "trashed": False,
        }

        arquivos.get.return_value.execute.side_effect = [
            meta,
            depois,
        ]

        arquivos.get_media.return_value.execute.return_value = (
            b"imagem-ficticia"
        )

        servico = MagicMock()

        servico.files.return_value = (
            arquivos
        )

        with patch(
            "importacao.extrair_texto",
            return_value=(
                "[Extração: OCR]\n"
                "Texto reconhecido."
            ),
        ) as extrair:
            texto = sd.baixar_texto(
                servico,
                {
                    "id": "img1",
                    "name": "foto.png",
                    "mimeType": "image/png",
                },
                self.pasta_id,
            )

        extrair.assert_called_once_with(
            "documento.png",
            b"imagem-ficticia",
        )

        self.assertIn(
            "Fonte no Google Drive: foto.png",
            texto,
        )

        self.assertIn(
            "[Extração: OCR]",
            texto,
        )

    def test_baixar_pdf_pode_preservar_resultado_ocr(self):
        arquivos = MagicMock()

        meta = {
            "id": "pdf1",
            "name": "digitalizado.pdf",
            "mimeType": "application/pdf",
            "size": "100",
            "version": "1",
            "parents": [
                self.pasta_id
            ],
            "trashed": False,
            "capabilities": {
                "canDownload": True
            },
        }

        depois = {
            "version": "1",
            "parents": [
                self.pasta_id
            ],
            "trashed": False,
        }

        arquivos.get.return_value.execute.side_effect = [
            meta,
            depois,
        ]

        arquivos.get_media.return_value.execute.return_value = (
            b"pdf-ficticio"
        )

        servico = MagicMock()

        servico.files.return_value = (
            arquivos
        )

        with patch(
            "importacao.extrair_texto",
            return_value=(
                "[Página 1]\n"
                "[Extração: OCR]\n"
                "Texto digitalizado."
            ),
        ) as extrair:
            texto = sd.baixar_texto(
                servico,
                {
                    "id": "pdf1",
                    "name": "digitalizado.pdf",
                    "mimeType": "application/pdf",
                },
                self.pasta_id,
            )

        extrair.assert_called_once_with(
            "documento.pdf",
            b"pdf-ficticio",
        )

        self.assertIn(
            "[Página 1]",
            texto,
        )

        self.assertIn(
            "[Extração: OCR]",
            texto,
        )

    def test_baixar_rejeita_arquivo_acima_do_limite(self):
        arquivos = MagicMock()

        meta = {
            "id": "img1",
            "name": "foto.png",
            "mimeType": "image/png",
            "size": str(
                6
                * 1024
                * 1024
            ),
            "version": "1",
            "parents": [
                self.pasta_id
            ],
            "trashed": False,
            "capabilities": {
                "canDownload": True
            },
        }

        arquivos.get.return_value.execute.return_value = (
            meta
        )

        servico = MagicMock()

        servico.files.return_value = (
            arquivos
        )

        with self.assertRaisesRegex(
            ValueError,
            "acima de 5 MiB",
        ):
            sd.baixar_texto(
                servico,
                {
                    "id": "img1",
                    "name": "foto.png",
                    "mimeType": "image/png",
                },
                self.pasta_id,
            )

        arquivos.get_media.assert_not_called()

    def test_falha_de_ocr_no_drive_nao_aplica_base_parcial(self):
        self.aplicar(
            {
                self.nome:
                b"Base anterior."
            }
        )

        itens = [
            {
                "id": "texto",
                "name": "normal.txt",
                "mimeType": "text/plain",
            },
            {
                "id": "imagem",
                "name": "ilegivel.png",
                "mimeType": "image/png",
            },
        ]

        def falhar_imagem(
            servico,
            item,
            pasta_id,
        ):
            if (
                item[
                    "mimeType"
                ]
                == "image/png"
            ):
                raise ValueError(
                    "OCR não conseguiu "
                    "reconhecer a imagem."
                )

            return (
                "Novo conteúdo."
            )

        with patch(
            "verificar_drive.listar_pasta",
            return_value=(
                {},
                itens,
            ),
        ):
            with patch.object(
                sd,
                "baixar_texto",
                side_effect=(
                    falhar_imagem
                ),
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "OCR",
                ):
                    sd.sincronizar(
                        MagicMock(),
                        self.pasta_id,
                        self.base,
                    )

        self.assertEqual(
            (
                self.pasta
                / self.nome
            ).read_bytes(),
            b"Base anterior.",
        )


if __name__ == "__main__":
    unittest.main()