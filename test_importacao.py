import unittest
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from docx import Document
from pypdf import PdfWriter

import importacao as imp


class TestImportacao(unittest.TestCase):
    def test_txt_preserva_acentos(self):
        dados = "Solicitação de material.".encode("utf-8-sig")

        self.assertEqual(
            imp.extrair_texto("teste.TXT", dados),
            "Solicitação de material.",
        )

    def test_docx_le_paragrafos_e_tabela_em_ordem(self):
        documento = Document()
        documento.add_paragraph("Antes da tabela.")

        tabela = documento.add_table(rows=1, cols=2)
        tabela.cell(0, 0).text = "Setor"
        tabela.cell(0, 1).text = "RH"

        documento.add_paragraph("Depois da tabela.")
        memoria = BytesIO()
        documento.save(memoria)

        texto = imp.extrair_texto(
            "teste.docx", memoria.getvalue()
        )

        self.assertEqual(
            texto,
            "Antes da tabela.\n\nSetor | RH\n\nDepois da tabela.",
        )

    def test_pdf_identifica_pagina(self):
        leitor = SimpleNamespace(
            is_encrypted=False,
            pages=[
                SimpleNamespace(
                    extract_text=lambda: "Material fictício."
                )
            ],
        )

        with patch("importacao.PdfReader", return_value=leitor):
            texto = imp.extrair_texto("teste.pdf", b"simulado")

        self.assertEqual(
            texto, "[Página 1]\nMaterial fictício."
        )

    def test_rejeita_formatos_conteudos_e_tamanho_invalidos(self):
        casos = [
            ("a.exe", b"abc"),
            ("a.txt", b""),
            ("a.txt", b"   "),
            ("a.txt", b"\xff"),
        ]

        for nome, dados in casos:
            with self.subTest(nome=nome, dados=dados):
                with self.assertRaises(imp.ErroImportacao):
                    imp.extrair_texto(nome, dados)

        with patch("importacao.MAX_BYTES", 2):
            with self.assertRaises(imp.ErroImportacao):
                imp.extrair_texto("a.txt", b"abc")

    def test_rejeita_pdf_sem_texto_ou_protegido(self):
        for protegido in (False, True):
            with self.subTest(protegido=protegido):
                escritor = PdfWriter()
                escritor.add_blank_page(width=200, height=200)

                if protegido:
                    escritor.encrypt("senha-ficticia")

                memoria = BytesIO()
                escritor.write(memoria)

                with self.assertRaises(imp.ErroImportacao):
                    imp.extrair_texto(
                        "teste.pdf", memoria.getvalue()
                    )

    def test_rejeita_texto_extraido_acima_do_limite(self):
        with patch("importacao.MAX_TEXTO", 3):
            with self.assertRaises(imp.ErroImportacao):
                imp.extrair_texto("teste.txt", b"abcd")

    def test_salva_apenas_na_pasta_de_destino(self):
        with TemporaryDirectory() as temporaria:
            pasta = Path(temporaria) / "documentos"

            destino, criado = imp.salvar_texto(
                pasta, "../../fora.txt", "Conteúdo fictício."
            )

            self.assertTrue(criado)
            self.assertEqual(destino.parent, pasta)
            self.assertTrue(
                destino.name.startswith("importado_")
            )
            self.assertIn(
                "Conteúdo fictício.",
                destino.read_text(encoding="utf-8"),
            )

    def test_reenvio_nao_duplica_nem_sobrescreve(self):
        with TemporaryDirectory() as temporaria:
            pasta = Path(temporaria)

            primeiro, _ = imp.salvar_texto(
                pasta, "teste.txt", "Conteúdo."
            )
            segundo, criado = imp.salvar_texto(
                pasta, "teste.txt", "Conteúdo."
            )

            self.assertEqual(primeiro, segundo)
            self.assertFalse(criado)
            self.assertEqual(
                len(list(pasta.glob("*.txt"))), 1
            )

    def test_texto_alterado_cria_outra_copia(self):
        with TemporaryDirectory() as temporaria:
            pasta = Path(temporaria)

            primeiro, _ = imp.salvar_texto(
                pasta, "teste.txt", "Versão inicial."
            )
            segundo, criado = imp.salvar_texto(
                pasta, "teste.txt", "Versão nova."
            )

            self.assertTrue(criado)
            self.assertNotEqual(primeiro, segundo)
            self.assertIn(
                "Versão inicial.",
                primeiro.read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()