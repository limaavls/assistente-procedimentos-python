import unittest
from unittest.mock import MagicMock, patch

import verificar_drive as drive


class TestVerificarDrive(unittest.TestCase):
    def setUp(self):
        self.servico = MagicMock()
        self.arquivos = self.servico.files.return_value
        self.pasta_id = "pasta_ficticia_123"

        self.arquivos.get.return_value.execute.return_value = {
            "id": self.pasta_id,
            "name": "Procedimentos fictícios",
            "mimeType": drive.TIPO_PASTA,
            "trashed": False,
        }

        self.arquivos.list.return_value.execute.return_value = {
            "files": [
                {
                    "id": "2",
                    "name": "ponto.txt",
                    "mimeType": "text/plain",
                },
                {
                    "id": "1",
                    "name": "material.txt",
                    "mimeType": "text/plain",
                },
            ]
        }

    def test_lista_e_ordena_sem_alterar_arquivos(self):
        pasta, itens = drive.listar_pasta(
            self.servico, self.pasta_id
        )

        self.assertEqual(
            pasta["name"], "Procedimentos fictícios"
        )
        self.assertEqual(
            [item["name"] for item in itens],
            ["material.txt", "ponto.txt"],
        )
        self.assertEqual(
            self.arquivos.list.call_args.kwargs["q"],
            f"'{self.pasta_id}' in parents and trashed = false",
        )

        self.arquivos.create.assert_not_called()
        self.arquivos.update.assert_not_called()
        self.arquivos.delete.assert_not_called()
        self.arquivos.get_media.assert_not_called()

    def test_rejeita_id_invalido_sem_acessar_api(self):
        casos = (
            "",
            "https://drive.google.com/drive/folders/exemplo",
        )

        for identificador in casos:
            with self.subTest(identificador=identificador):
                with self.assertRaises(drive.ErroVerificacao):
                    drive.listar_pasta(
                        self.servico, identificador
                    )

        self.servico.files.assert_not_called()

    def test_rejeita_arquivo_ou_pasta_na_lixeira(self):
        casos = (
            ("text/plain", False),
            (drive.TIPO_PASTA, True),
        )

        for tipo, lixeira in casos:
            with self.subTest(tipo=tipo, lixeira=lixeira):
                self.arquivos.get.return_value.execute.return_value = {
                    "mimeType": tipo,
                    "trashed": lixeira,
                }

                with self.assertRaises(drive.ErroVerificacao):
                    drive.listar_pasta(
                        self.servico, self.pasta_id
                    )

        self.arquivos.list.assert_not_called()

    def test_le_pagina_seguinte_apos_pagina_vazia(self):
        self.arquivos.list.return_value.execute.side_effect = [
            {
                "files": [],
                "nextPageToken": "pagina2",
            },
            {
                "files": [
                    {
                        "id": "1",
                        "name": "exemplo.txt",
                        "mimeType": "text/plain",
                    }
                ]
            },
        ]

        _, itens = drive.listar_pasta(
            self.servico, self.pasta_id
        )

        self.assertEqual(len(itens), 1)
        self.assertEqual(self.arquivos.list.call_count, 2)
        self.assertEqual(
            self.arquivos.list.call_args.kwargs["pageToken"],
            "pagina2",
        )

    def test_rejeita_listagem_incompleta(self):
        self.arquivos.list.return_value.execute.return_value = {
            "incompleteSearch": True,
            "files": [],
        }

        with self.assertRaises(drive.ErroVerificacao):
            drive.listar_pasta(self.servico, self.pasta_id)

    def test_respeita_limite_da_demonstracao(self):
        with patch.object(drive, "MAX_ITENS", 1):
            with self.assertRaises(drive.ErroVerificacao):
                drive.listar_pasta(
                    self.servico, self.pasta_id
                )


if __name__ == "__main__":
    unittest.main()