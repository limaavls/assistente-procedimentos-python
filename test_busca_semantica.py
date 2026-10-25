import re
import unittest
from pathlib import Path
from unittest.mock import patch

import busca_semantica as bs


class ModeloSimulado:
    """Vetores didáticos, sem avaliação do modelo real."""

    max_seq_length = 512

    def __init__(self):
        self.chamadas = []

    def tokenizer(self, texto, **opcoes):
        posicoes = [
            (item.start(), item.end())
            for item in re.finditer(r"\S+", texto)
        ]

        extras = (
            2 if opcoes.get("add_special_tokens") else 0
        )

        return {
            "offset_mapping": posicoes,
            "input_ids": list(
                range(len(posicoes) + extras)
            ),
        }

    def encode(self, textos, **opcoes):
        self.chamadas.append(list(textos))

        return [
            [1.0, 0.0]
            if any(
                palavra in texto
                for palavra in ("frequência", "jornada")
            )
            else [0.0, 1.0]
            for texto in textos
        ]


class TestBuscaSemantica(unittest.TestCase):
    def setUp(self):
        self.modelo = ModeloSimulado()
        self.indice = bs.IndiceSemantico(self.modelo)

        self.docs = [
            (
                Path("material.txt"),
                "Solicitação de material.",
            ),
            (
                Path("ponto.txt"),
                "Correção de frequência.",
            ),
        ]

    def test_recortes_preservam_texto_e_sobreposicao(self):
        partes = bs.dividir_texto(
            "um dois três quatro cinco seis",
            self.modelo.tokenizer,
            4,
            1,
        )

        self.assertEqual(
            partes,
            [
                "um dois três quatro",
                "quatro cinco seis",
            ],
        )

    def test_parametros_de_recorte_invalidos(self):
        with self.assertRaises(ValueError):
            bs.dividir_texto(
                "texto",
                self.modelo.tokenizer,
                3,
                3,
            )

    def test_ordena_por_vetores_e_preserva_fonte(self):
        resultado = self.indice.buscar(
            self.docs,
            "Ajustar jornada",
        )

        self.assertEqual(
            resultado[0][0],
            Path("ponto.txt"),
        )
        self.assertEqual(
            resultado[0][1],
            "Correção de frequência.",
        )
        self.assertIn(
            "Correção de frequência.",
            resultado[0][2][0],
        )

    def test_aplica_prefixos_do_modelo(self):
        self.indice.buscar(self.docs, "jornada")

        self.assertTrue(
            all(
                texto.startswith("passage: ")
                for texto in self.modelo.chamadas[0]
            )
        )
        self.assertEqual(
            self.modelo.chamadas[1],
            ["query: jornada"],
        )

    def test_reutiliza_vetores_da_mesma_base(self):
        self.indice.buscar(self.docs, "jornada")
        self.indice.buscar(self.docs, "material")

        chamadas_base = [
            chamada
            for chamada in self.modelo.chamadas
            if chamada[0].startswith("passage: ")
        ]

        self.assertEqual(len(chamadas_base), 1)

    def test_alteracao_ou_exclusao_atualiza_base(self):
        self.indice.buscar(self.docs, "jornada")

        novos = [
            (
                Path("ponto.txt"),
                "Nova regra de frequência.",
            )
        ]

        resultado = self.indice.buscar(novos, "jornada")

        self.assertEqual(len(resultado), 1)
        self.assertEqual(
            resultado[0][1],
            "Nova regra de frequência.",
        )
        self.assertEqual(
            self.indice.buscar([], "jornada"),
            [],
        )

    def test_entradas_vazias_nao_codificam(self):
        self.assertEqual(
            self.indice.buscar([], "material"),
            [],
        )
        self.assertEqual(
            self.indice.buscar(self.docs, ""),
            [],
        )
        self.assertEqual(
            self.indice.buscar(self.docs, "???"),
            [],
        )
        self.assertEqual(self.modelo.chamadas, [])

    def test_limita_documentos_e_trechos(self):
        documentos = [
            (
                Path(f"doc{numero}.txt"),
                "material " * 600,
            )
            for numero in range(5)
        ]

        resultado = self.indice.buscar(
            documentos,
            "material",
        )

        self.assertEqual(len(resultado), 3)
        self.assertTrue(
            all(len(item[2]) == 2 for item in resultado)
        )

    def test_rejeita_excesso_sem_truncar(self):
        with patch.object(bs, "MAX_TRECHOS", 1):
            with self.assertRaises(ValueError):
                self.indice.buscar(self.docs, "material")

        with self.assertRaises(ValueError):
            self.indice.buscar(
                self.docs,
                "jornada " * 600,
            )

    def test_rejeita_vetor_invalido(self):
        with patch.object(
            self.modelo,
            "encode",
            return_value=[[float("nan"), 0.0]],
        ):
            with self.assertRaises(ValueError):
                self.indice.buscar(
                    [self.docs[0]],
                    "material",
                )


if __name__ == "__main__":
    unittest.main()