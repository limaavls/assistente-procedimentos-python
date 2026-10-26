import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import ocr


class MotorSimulado:
    def __init__(
        self,
        textos=None,
        scores=None,
        erro=None,
    ):
        self.textos = (
            textos
            if textos is not None
            else (
                "Solicitação de material",
                "Setor responsável: RH",
            )
        )

        self.scores = (
            scores
            if scores is not None
            else (
                0.95,
                0.85,
            )
        )

        self.erro = erro
        self.recebido = None

    def __call__(
        self,
        dados,
    ):
        self.recebido = dados

        if self.erro is not None:
            raise self.erro

        return SimpleNamespace(
            txts=self.textos,
            scores=self.scores,
        )


class TestOCR(unittest.TestCase):

    def test_reconhece_imagem_em_memoria(self):
        motor = MotorSimulado()

        resultado = ocr.reconhecer_imagem(
            b"imagem-ficticia",
            motor=motor,
        )

        self.assertEqual(
            resultado.texto,
            (
                "Solicitação de material\n"
                "Setor responsável: RH"
            ),
        )

        self.assertEqual(
            resultado.linhas_reconhecidas,
            2,
        )

        self.assertAlmostEqual(
            resultado.confianca_media,
            0.90,
        )

        self.assertEqual(
            motor.recebido,
            b"imagem-ficticia",
        )

    def test_preserva_texto_sem_correcao_automatica(self):
        motor = MotorSimulado(
            textos=(
                "Materlal flctício",
            ),
            scores=(
                0.72,
            ),
        )

        resultado = ocr.reconhecer_imagem(
            b"imagem",
            motor=motor,
        )

        self.assertEqual(
            resultado.texto,
            "Materlal flctício",
        )

    def test_remove_apenas_linhas_vazias(self):
        motor = MotorSimulado(
            textos=(
                "Primeira linha",
                "   ",
                "Segunda linha",
            ),
            scores=(
                0.9,
                0.8,
                0.7,
            ),
        )

        resultado = ocr.reconhecer_imagem(
            b"imagem",
            motor=motor,
        )

        self.assertEqual(
            resultado.texto,
            "Primeira linha\nSegunda linha",
        )

        self.assertEqual(
            resultado.linhas_reconhecidas,
            2,
        )

    def test_calcula_confianca_apenas_com_scores_validos(self):
        motor = MotorSimulado(
            textos=(
                "Texto",
            ),
            scores=(
                0.8,
                "invalido",
                2,
                -1,
            ),
        )

        resultado = ocr.reconhecer_imagem(
            b"imagem",
            motor=motor,
        )

        self.assertEqual(
            resultado.confianca_media,
            0.8,
        )

    def test_funciona_sem_scores(self):
        motor = MotorSimulado(
            textos=(
                "Texto reconhecido",
            ),
        )

        motor.scores = None

        resultado = ocr.reconhecer_imagem(
            b"imagem",
            motor=motor,
        )

        self.assertIsNone(
            resultado.confianca_media,
        )

    def test_rejeita_imagem_vazia(self):
        motor = MotorSimulado()

        with self.assertRaises(
            ocr.ErroOCR
        ):
            ocr.reconhecer_imagem(
                b"",
                motor=motor,
            )

    def test_rejeita_tipo_invalido(self):
        motor = MotorSimulado()

        with self.assertRaises(
            ocr.ErroOCR
        ):
            ocr.reconhecer_imagem(
                "não são bytes",
                motor=motor,
            )

    def test_rejeita_resultado_sem_texto(self):
        motor = MotorSimulado(
            textos=(
                "",
                "   ",
            ),
        )

        with self.assertRaises(
            ocr.ErroOCR
        ):
            ocr.reconhecer_imagem(
                b"imagem",
                motor=motor,
            )

    def test_converte_erro_do_motor_em_erro_ocr(self):
        motor = MotorSimulado(
            erro=RuntimeError(
                "erro fictício"
            )
        )

        with self.assertRaisesRegex(
            ocr.ErroOCR,
            "executar OCR",
        ):
            ocr.reconhecer_imagem(
                b"imagem",
                motor=motor,
            )

    def test_renderiza_pagina_pdf_em_png(self):
        documento = MagicMock()

        documento.needs_pass = False
        documento.page_count = 2

        pagina = MagicMock()
        pixmap = MagicMock()

        pixmap.width = 1000
        pixmap.height = 1500
        pixmap.tobytes.return_value = (
            b"png-ficticio"
        )

        pagina.get_pixmap.return_value = (
            pixmap
        )

        documento.load_page.return_value = (
            pagina
        )

        modulo = SimpleNamespace(
            open=MagicMock(
                return_value=documento
            ),
            csRGB=object(),
        )

        with patch.dict(
            "sys.modules",
            {
                "pymupdf": modulo,
            },
        ):
            resultado = ocr.renderizar_pagina_pdf(
                b"pdf-ficticio",
                1,
                dpi=200,
            )

        self.assertEqual(
            resultado,
            b"png-ficticio",
        )

        documento.load_page.assert_called_once_with(
            1
        )

        pagina.get_pixmap.assert_called_once()

        pixmap.tobytes.assert_called_once_with(
            "png"
        )

        documento.close.assert_called_once()

    def test_rejeita_pagina_pdf_inexistente(self):
        documento = MagicMock()

        documento.needs_pass = False
        documento.page_count = 1

        modulo = SimpleNamespace(
            open=MagicMock(
                return_value=documento
            ),
            csRGB=object(),
        )

        with patch.dict(
            "sys.modules",
            {
                "pymupdf": modulo,
            },
        ):
            with self.assertRaisesRegex(
                ocr.ErroOCR,
                "não existe",
            ):
                ocr.renderizar_pagina_pdf(
                    b"pdf",
                    1,
                )

        documento.close.assert_called_once()

    def test_rejeita_pdf_protegido(self):
        documento = MagicMock()

        documento.needs_pass = True
        documento.page_count = 1

        modulo = SimpleNamespace(
            open=MagicMock(
                return_value=documento
            ),
            csRGB=object(),
        )

        with patch.dict(
            "sys.modules",
            {
                "pymupdf": modulo,
            },
        ):
            with self.assertRaisesRegex(
                ocr.ErroOCR,
                "protegido",
            ):
                ocr.renderizar_pagina_pdf(
                    b"pdf",
                    0,
                )

        documento.close.assert_called_once()

    def test_rejeita_dpi_invalido(self):
        for dpi in (
            50,
            301,
            "200",
        ):
            with self.subTest(
                dpi=dpi
            ):
                with self.assertRaises(
                    ocr.ErroOCR
                ):
                    ocr.renderizar_pagina_pdf(
                        b"pdf",
                        0,
                        dpi=dpi,
                    )

    def test_rejeita_pagina_grande_demais(self):
        documento = MagicMock()

        documento.needs_pass = False
        documento.page_count = 1

        pagina = MagicMock()
        pixmap = MagicMock()

        pixmap.width = 10_000
        pixmap.height = 10_000

        pagina.get_pixmap.return_value = (
            pixmap
        )

        documento.load_page.return_value = (
            pagina
        )

        modulo = SimpleNamespace(
            open=MagicMock(
                return_value=documento
            ),
            csRGB=object(),
        )

        with patch.dict(
            "sys.modules",
            {
                "pymupdf": modulo,
            },
        ):
            with self.assertRaisesRegex(
                ocr.ErroOCR,
                "grande demais",
            ):
                ocr.renderizar_pagina_pdf(
                    b"pdf",
                    0,
                )

        documento.close.assert_called_once()

    def test_reconhecer_pagina_pdf_encadeia_renderizacao_e_ocr(self):
        motor = MotorSimulado(
            textos=(
                "Texto da página",
            ),
            scores=(
                0.91,
            ),
        )

        with patch(
            "ocr.renderizar_pagina_pdf",
            return_value=b"imagem-pagina",
        ) as renderizar:
            resultado = ocr.reconhecer_pagina_pdf(
                b"pdf",
                2,
                motor=motor,
                dpi=180,
            )

        renderizar.assert_called_once_with(
            b"pdf",
            2,
            dpi=180,
        )

        self.assertEqual(
            motor.recebido,
            b"imagem-pagina",
        )

        self.assertEqual(
            resultado.texto,
            "Texto da página",
        )


if __name__ == "__main__":
    unittest.main()