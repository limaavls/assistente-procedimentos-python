import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import painel_documentos as painel


class ArquivoSimulado:
    def __init__(
        self,
        nome,
        dados=b"arquivo",
    ):
        self.name = nome
        self._dados = dados
        self.size = len(dados)

    def getvalue(self):
        return self._dados


class ContextoSimulado:
    def __enter__(self):
        return self

    def __exit__(
        self,
        tipo,
        valor,
        traceback,
    ):
        return False


class StreamlitSimulado:
    def __init__(
        self,
        enviado=None,
    ):
        self.session_state = {}
        self.sidebar = ContextoSimulado()

        self.enviado = enviado

        self.headers = []
        self.captions = []
        self.infos = []
        self.warnings = []
        self.errors = []
        self.successes = []
        self.text_areas = []

        self.botoes = {}
        self.checkboxes = {}

    def header(
        self,
        texto,
    ):
        self.headers.append(
            texto
        )

    def caption(
        self,
        texto,
    ):
        self.captions.append(
            texto
        )

    def info(
        self,
        texto,
    ):
        self.infos.append(
            texto
        )

    def warning(
        self,
        texto,
    ):
        self.warnings.append(
            texto
        )

    def error(
        self,
        texto,
    ):
        self.errors.append(
            texto
        )

    def success(
        self,
        texto,
    ):
        self.successes.append(
            texto
        )

    def file_uploader(
        self,
        *args,
        **kwargs,
    ):
        self.tipo_upload = kwargs.get(
            "type"
        )

        return self.enviado

    def button(
        self,
        rotulo,
        key=None,
        disabled=False,
        **kwargs,
    ):
        if disabled:
            return False

        return bool(
            self.botoes.get(
                key,
                False,
            )
        )

    def checkbox(
        self,
        rotulo,
        key=None,
        **kwargs,
    ):
        return bool(
            self.checkboxes.get(
                key,
                False,
            )
        )

    def text_area(
        self,
        rotulo,
        value="",
        **kwargs,
    ):
        self.text_areas.append(
            (
                rotulo,
                value,
            )
        )


class TestPainelDocumentos(
    unittest.TestCase
):

    def setUp(self):
        painel.st.session_state.clear()

    def test_lista_de_upload_inclui_imagens(self):
        esperados = {
            "txt",
            "pdf",
            "docx",
            "png",
            "jpg",
            "jpeg",
            "bmp",
            "tif",
            "tiff",
            "webp",
        }

        self.assertEqual(
            set(
                painel.TIPOS_UPLOAD
            ),
            esperados,
        )

    def test_detecta_extensao_de_imagem(self):
        for nome in (
            "imagem.png",
            "foto.JPG",
            "scan.jpeg",
            "pagina.tiff",
            "arquivo.webp",
        ):
            with self.subTest(
                nome=nome
            ):
                self.assertTrue(
                    painel._arquivo_e_imagem(
                        nome
                    )
                )

        self.assertFalse(
            painel._arquivo_e_imagem(
                "documento.pdf"
            )
        )

    def test_detecta_uso_de_ocr(self):
        self.assertTrue(
            painel._texto_usou_ocr(
                (
                    "[Extração: OCR]\n"
                    "Texto."
                )
            )
        )

        self.assertFalse(
            painel._texto_usou_ocr(
                "Texto normal."
            )
        )

    def test_sem_arquivo_retorna_false(self):
        simulado = (
            StreamlitSimulado()
        )

        with patch.object(
            painel,
            "st",
            simulado,
        ):
            resultado = (
                painel.mostrar_importacao(
                    Path("documentos")
                )
            )

        self.assertFalse(
            resultado
        )

        self.assertIn(
            "png",
            simulado.tipo_upload,
        )

    def test_imagem_exibe_aviso_de_ocr(self):
        simulado = (
            StreamlitSimulado(
                ArquivoSimulado(
                    "scan.png"
                )
            )
        )

        with patch.object(
            painel,
            "st",
            simulado,
        ):
            resultado = (
                painel.mostrar_importacao(
                    Path("documentos")
                )
            )

        self.assertFalse(
            resultado
        )

        self.assertTrue(
            any(
                (
                    "OCR local"
                    in mensagem
                )
                for mensagem
                in simulado.infos
            )
        )

    def test_extracao_com_ocr_salva_previa(self):
        simulado = (
            StreamlitSimulado(
                ArquivoSimulado(
                    "scan.png"
                )
            )
        )

        simulado.botoes[
            "imp_extrair"
        ] = True

        texto = (
            "[Extração: OCR]\n"
            "Texto reconhecido."
        )

        with patch.object(
            painel,
            "st",
            simulado,
        ):
            with patch.object(
                painel,
                "extrair_texto",
                return_value=texto,
            ) as extrair:
                resultado = (
                    painel.mostrar_importacao(
                        Path(
                            "documentos"
                        )
                    )
                )

        self.assertFalse(
            resultado
        )

        extrair.assert_called_once_with(
            "scan.png",
            b"arquivo",
        )

        previa = (
            simulado.session_state[
                "imp_previa"
            ]
        )

        self.assertEqual(
            previa["nome"],
            "scan.png",
        )

        self.assertEqual(
            previa["texto"],
            texto,
        )

        self.assertTrue(
            previa["usou_ocr"]
        )

        self.assertTrue(
            any(
                (
                    "OCR foi utilizado"
                    in mensagem
                )
                for mensagem
                in simulado.warnings
            )
        )

    def test_pdf_normal_nao_mostra_aviso_de_ocr(self):
        simulado = (
            StreamlitSimulado(
                ArquivoSimulado(
                    "documento.pdf"
                )
            )
        )

        simulado.botoes[
            "imp_extrair"
        ] = True

        with patch.object(
            painel,
            "st",
            simulado,
        ):
            with patch.object(
                painel,
                "extrair_texto",
                return_value=(
                    "[Página 1]\n"
                    "Texto normal."
                ),
            ):
                painel.mostrar_importacao(
                    Path("documentos")
                )

        previa = (
            simulado.session_state[
                "imp_previa"
            ]
        )

        self.assertFalse(
            previa["usou_ocr"]
        )

        self.assertFalse(
            any(
                (
                    "OCR foi utilizado"
                    in mensagem
                )
                for mensagem
                in simulado.warnings
            )
        )

    def test_pdf_misto_identifica_ocr(self):
        simulado = (
            StreamlitSimulado(
                ArquivoSimulado(
                    "misto.pdf"
                )
            )
        )

        simulado.botoes[
            "imp_extrair"
        ] = True

        texto = (
            "[Página 1]\n"
            "Texto normal.\n\n"
            "[Página 2]\n"
            "[Extração: OCR]\n"
            "Texto digitalizado."
        )

        with patch.object(
            painel,
            "st",
            simulado,
        ):
            with patch.object(
                painel,
                "extrair_texto",
                return_value=texto,
            ):
                painel.mostrar_importacao(
                    Path("documentos")
                )

        self.assertTrue(
            simulado.session_state[
                "imp_previa"
            ]["usou_ocr"]
        )

    def test_erro_de_extracao_e_exibido(self):
        simulado = (
            StreamlitSimulado(
                ArquivoSimulado(
                    "scan.jpg"
                )
            )
        )

        simulado.botoes[
            "imp_extrair"
        ] = True

        with patch.object(
            painel,
            "st",
            simulado,
        ):
            with patch.object(
                painel,
                "extrair_texto",
                side_effect=(
                    painel.ErroImportacao(
                        "OCR falhou."
                    )
                ),
            ):
                resultado = (
                    painel.mostrar_importacao(
                        Path("documentos")
                    )
                )

        self.assertFalse(
            resultado
        )

        self.assertIn(
            "OCR falhou.",
            simulado.errors,
        )

        self.assertIsNone(
            simulado.session_state.get(
                "imp_previa"
            )
        )

    def test_limite_de_tamanho_impede_extracao(self):
        simulado = (
            StreamlitSimulado(
                ArquivoSimulado(
                    "grande.png",
                    b"abc",
                )
            )
        )

        with patch.object(
            painel,
            "MAX_BYTES",
            2,
        ):
            with patch.object(
                painel,
                "st",
                simulado,
            ):
                resultado = (
                    painel.mostrar_importacao(
                        Path("documentos")
                    )
                )

        self.assertFalse(
            resultado
        )

        self.assertTrue(
            simulado.errors
        )

    def test_adicionar_salva_previa_aprovada(self):
        simulado = (
            StreamlitSimulado(
                ArquivoSimulado(
                    "scan.png"
                )
            )
        )

        simulado.session_state[
            "imp_previa"
        ] = {
            "nome": "scan.png",
            "texto": (
                "[Extração: OCR]\n"
                "Texto reconhecido."
            ),
            "usou_ocr": True,
        }

        simulado.checkboxes[
            "imp_confirmar"
        ] = True

        simulado.botoes[
            "imp_adicionar"
        ] = True

        with TemporaryDirectory() as temporaria:
            pasta = Path(
                temporaria
            )

            with patch.object(
                painel,
                "st",
                simulado,
            ):
                resultado = (
                    painel.mostrar_importacao(
                        pasta
                    )
                )

            self.assertTrue(
                resultado
            )

            arquivos = list(
                pasta.glob(
                    "*.txt"
                )
            )

            self.assertEqual(
                len(arquivos),
                1,
            )

            conteudo = (
                arquivos[0]
                .read_text(
                    encoding="utf-8"
                )
            )

            self.assertIn(
                "Arquivo de origem: scan.png",
                conteudo,
            )

            self.assertIn(
                "[Extração: OCR]",
                conteudo,
            )

    def test_nao_adiciona_sem_confirmacao(self):
        simulado = (
            StreamlitSimulado(
                ArquivoSimulado(
                    "scan.png"
                )
            )
        )

        simulado.session_state[
            "imp_previa"
        ] = {
            "nome": "scan.png",
            "texto": (
                "[Extração: OCR]\n"
                "Texto."
            ),
            "usou_ocr": True,
        }

        simulado.botoes[
            "imp_adicionar"
        ] = True

        simulado.checkboxes[
            "imp_confirmar"
        ] = False

        with TemporaryDirectory() as temporaria:
            pasta = Path(
                temporaria
            )

            with patch.object(
                painel,
                "st",
                simulado,
            ):
                resultado = (
                    painel.mostrar_importacao(
                        pasta
                    )
                )

            self.assertFalse(
                resultado
            )

            self.assertEqual(
                list(
                    pasta.glob(
                        "*.txt"
                    )
                ),
                [],
            )


if __name__ == "__main__":
    unittest.main()