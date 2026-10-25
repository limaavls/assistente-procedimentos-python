import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import sincronizar_drive as sd


class TestSincronizarDrive(unittest.TestCase):
    def setUp(self):
        temporaria = TemporaryDirectory()
        self.addCleanup(temporaria.cleanup)

        self.base = Path(temporaria.name)
        self.pasta = self.base / "documentos"
        self.estado = self.base / ".estado_drive"
        self.nome = "drive_" + "a" * 24 + ".txt"
        self.pasta_id = "pasta_ficticia_123"

    def aplicar(self, dados):
        return sd.aplicar_copias(
            self.pasta,
            self.estado,
            self.pasta_id,
            dados,
        )

    def test_cria_copia_e_registro(self):
        resultado = self.aplicar(
            {self.nome: b"Primeira versao."}
        )

        self.assertEqual(resultado["incluidos"], 1)
        self.assertEqual(
            (self.pasta / self.nome).read_bytes(),
            b"Primeira versao.",
        )

        registro = json.loads(
            (self.estado / "manifesto.json").read_text()
        )
        self.assertIn(self.nome, registro["arquivos"])

    def test_repeticao_nao_duplica(self):
        self.aplicar({self.nome: b"Conteudo."})
        resultado = self.aplicar(
            {self.nome: b"Conteudo."}
        )

        self.assertEqual(resultado["mantidos"], 1)
        self.assertEqual(
            len(list(self.pasta.glob("*.txt"))),
            1,
        )

    def test_atualiza_e_preserva_backup(self):
        self.aplicar({self.nome: b"Antes."})
        resultado = self.aplicar(
            {self.nome: b"Depois."}
        )

        self.assertEqual(resultado["atualizados"], 1)
        self.assertEqual(
            (self.pasta / self.nome).read_bytes(),
            b"Depois.",
        )

        self.assertTrue(
            any(
                arquivo.read_bytes() == b"Antes."
                for arquivo in self.estado.glob(
                    "historico/*/" + self.nome
                )
            )
        )

    def test_retirada_preserva_arquivos_manuais(self):
        self.aplicar(
            {self.nome: b"Conteudo do Drive."}
        )

        manual = self.pasta / "meu_exercicio.txt"
        manual.write_text(
            "Nao apagar.",
            encoding="utf-8",
        )

        resultado = self.aplicar({})

        self.assertEqual(resultado["retirados"], 1)
        self.assertFalse(
            (self.pasta / self.nome).exists()
        )
        self.assertEqual(
            manual.read_text(),
            "Nao apagar.",
        )
        self.assertTrue(
            list(
                self.estado.glob(
                    "historico/*/" + self.nome
                )
            )
        )

    def test_edicao_local_interrompe_atualizacao(self):
        self.aplicar(
            {self.nome: b"Versao original."}
        )

        (self.pasta / self.nome).write_bytes(
            b"Edicao manual."
        )

        with self.assertRaises(ValueError):
            self.aplicar(
                {self.nome: b"Outra versao."}
            )

        self.assertEqual(
            (self.pasta / self.nome).read_bytes(),
            b"Edicao manual.",
        )

    def test_colisao_com_arquivo_nao_registrado(self):
        self.pasta.mkdir()
        (self.pasta / self.nome).write_bytes(
            b"Arquivo particular."
        )

        with self.assertRaises(ValueError):
            self.aplicar(
                {self.nome: b"Conteudo do Drive."}
            )

        self.assertEqual(
            (self.pasta / self.nome).read_bytes(),
            b"Arquivo particular.",
        )

    def test_rejeita_caminho_invalido_e_troca_de_pasta(self):
        with self.assertRaises(ValueError):
            self.aplicar(
                {"../fora.txt": b"Invalido."}
            )

        self.aplicar({self.nome: b"Conteudo."})

        with self.assertRaises(ValueError):
            sd.aplicar_copias(
                self.pasta,
                self.estado,
                "outra_pasta",
                {},
            )

    def test_falha_de_gravacao_tenta_restaurar_versao_anterior(self):
        self.aplicar({self.nome: b"Antes."})

        manifesto = (
            self.estado / "manifesto.json"
        ).read_bytes()

        original = sd.gravar
        chamadas = []

        def falhar_uma_vez(caminho, dados):
            chamadas.append(caminho)

            if len(chamadas) == 2:
                raise OSError(
                    "Falha simulada na gravacao do registro."
                )

            original(caminho, dados)

        with patch.object(
            sd,
            "gravar",
            side_effect=falhar_uma_vez,
        ):
            with self.assertRaises(OSError):
                self.aplicar(
                    {self.nome: b"Depois."}
                )

        self.assertEqual(
            (self.pasta / self.nome).read_bytes(),
            b"Antes.",
        )
        self.assertEqual(
            (self.estado / "manifesto.json").read_bytes(),
            manifesto,
        )

    def test_erro_de_download_nao_aplica_mudancas(self):
        self.aplicar({self.nome: b"Antes."})

        itens = [
            {
                "id": "abc123",
                "name": "teste.txt",
                "mimeType": "text/plain",
            }
        ]

        with patch(
            "verificar_drive.listar_pasta",
            return_value=({}, itens),
        ):
            with patch.object(
                sd,
                "baixar_texto",
                side_effect=ValueError("Falha simulada."),
            ):
                with self.assertRaises(ValueError):
                    sd.sincronizar(
                        MagicMock(),
                        self.pasta_id,
                        self.base,
                    )

        self.assertEqual(
            (self.pasta / self.nome).read_bytes(),
            b"Antes.",
        )

    def test_filtra_formatos_e_usar_mesmo_id_nao_duplica(self):
        itens = [
            {
                "id": "mesmo_id",
                "name": "antes.txt",
                "mimeType": "text/plain",
            },
            {
                "id": "imagem",
                "name": "imagem.png",
                "mimeType": "image/png",
            },
        ]

        with patch(
            "verificar_drive.listar_pasta",
            return_value=({}, itens),
        ):
            with patch.object(
                sd,
                "baixar_texto",
                return_value="Primeira versao.",
            ):
                resultado = sd.sincronizar(
                    MagicMock(),
                    self.pasta_id,
                    self.base,
                )
                self.assertEqual(
                    resultado["ignorados"],
                    1,
                )

            itens[0]["name"] = "renomeado.txt"

            with patch.object(
                sd,
                "baixar_texto",
                return_value="Versao nova.",
            ):
                resultado = sd.sincronizar(
                    MagicMock(),
                    self.pasta_id,
                    self.base,
                )

        self.assertEqual(
            resultado["atualizados"],
            1,
        )
        self.assertEqual(
            len(list(self.pasta.glob("drive_*.txt"))),
            1,
        )


if __name__ == "__main__":
    unittest.main()