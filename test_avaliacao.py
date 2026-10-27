import unittest

import avaliacao as av


class TestAvaliacao(unittest.TestCase):

    def test_precision_recall_perfeitos(self):
        precision, recall = (
            av.precision_recall_documentos(
                [
                    "material.txt",
                    "ponto.txt",
                ],
                [
                    "material.txt",
                    "ponto.txt",
                ],
            )
        )

        self.assertEqual(
            precision,
            1.0,
        )

        self.assertEqual(
            recall,
            1.0,
        )

    def test_precision_penaliza_documento_irrelevante(self):
        precision, recall = (
            av.precision_recall_documentos(
                [
                    "material.txt",
                    "outro.txt",
                ],
                [
                    "material.txt",
                ],
            )
        )

        self.assertEqual(
            precision,
            0.5,
        )

        self.assertEqual(
            recall,
            1.0,
        )

    def test_recall_penaliza_documento_esperado_ausente(self):
        precision, recall = (
            av.precision_recall_documentos(
                [
                    "material.txt",
                ],
                [
                    "material.txt",
                    "ponto.txt",
                ],
            )
        )

        self.assertEqual(
            precision,
            1.0,
        )

        self.assertEqual(
            recall,
            0.5,
        )

    def test_reciprocal_rank_primeiro_lugar(self):
        resultado = av.reciprocal_rank(
            [
                "material.txt",
                "outro.txt",
            ],
            [
                "material.txt",
            ],
        )

        self.assertEqual(
            resultado,
            1.0,
        )

    def test_reciprocal_rank_segundo_lugar(self):
        resultado = av.reciprocal_rank(
            [
                "outro.txt",
                "material.txt",
            ],
            [
                "material.txt",
            ],
        )

        self.assertEqual(
            resultado,
            0.5,
        )

    def test_reciprocal_rank_zero_quando_nao_encontra(self):
        resultado = av.reciprocal_rank(
            [
                "outro.txt",
            ],
            [
                "material.txt",
            ],
        )

        self.assertEqual(
            resultado,
            0.0,
        )

    def test_conteudo_com_termos_obrigatorios(self):
        (
            encontrados,
            ausentes,
            proibidos,
            valido,
        ) = av.avaliar_conteudo(
            (
                "Informe o setor e "
                "a quantidade."
            ),
            [
                "setor",
                "quantidade",
            ],
            [],
        )

        self.assertEqual(
            encontrados,
            (
                "setor",
                "quantidade",
            ),
        )

        self.assertEqual(
            ausentes,
            (),
        )

        self.assertEqual(
            proibidos,
            (),
        )

        self.assertTrue(
            valido
        )

    def test_conteudo_detecta_termo_obrigatorio_ausente(self):
        (
            _,
            ausentes,
            _,
            valido,
        ) = av.avaliar_conteudo(
            "Informe o setor.",
            [
                "setor",
                "quantidade",
            ],
            [],
        )

        self.assertEqual(
            ausentes,
            (
                "quantidade",
            ),
        )

        self.assertFalse(
            valido
        )

    def test_conteudo_detecta_termo_proibido(self):
        (
            _,
            _,
            proibidos,
            valido,
        ) = av.avaliar_conteudo(
            (
                "O prazo é de 10 dias."
            ),
            [],
            [
                "10 dias",
            ],
        )

        self.assertEqual(
            proibidos,
            (
                "10 dias",
            ),
        )

        self.assertFalse(
            valido
        )

    def test_avaliar_caso_aprovado(self):
        caso = av.CasoAvaliacao(
            identificador="material_001",
            pergunta=(
                "Como solicitar material?"
            ),
            documentos_esperados=(
                "material.txt",
            ),
            termos_obrigatorios=(
                "setor",
                "quantidade",
            ),
            termos_proibidos=(
                "10 dias",
            ),
            status_esperado=(
                "respondida"
            ),
        )

        resultado = av.avaliar_caso(
            caso,
            documentos_encontrados=[
                "material.txt",
            ],
            texto_resposta=(
                "Informe o setor e "
                "a quantidade."
            ),
            documentos_citados=[
                "material.txt",
            ],
            citacoes_validas=True,
            status_obtido="respondida",
        )

        self.assertTrue(
            resultado.aprovado
        )

        self.assertEqual(
            resultado.recall_documentos,
            1.0,
        )

        self.assertEqual(
            resultado.reciprocal_rank,
            1.0,
        )

    def test_avaliar_caso_reprova_recuperacao(self):
        caso = av.CasoAvaliacao(
            identificador="material_002",
            pergunta="Pergunta.",
            documentos_esperados=(
                "material.txt",
            ),
            termos_obrigatorios=(
                "setor",
            ),
            status_esperado="respondida",
        )

        resultado = av.avaliar_caso(
            caso,
            documentos_encontrados=[
                "outro.txt",
            ],
            texto_resposta=(
                "Informe o setor."
            ),
            documentos_citados=[
                "material.txt",
            ],
            citacoes_validas=True,
            status_obtido="respondida",
        )

        self.assertFalse(
            resultado.aprovado
        )

        self.assertEqual(
            resultado.recall_documentos,
            0.0,
        )

    def test_avaliar_caso_reprova_citacao_errada(self):
        caso = av.CasoAvaliacao(
            identificador="material_003",
            pergunta="Pergunta.",
            documentos_esperados=(
                "material.txt",
            ),
            termos_obrigatorios=(
                "setor",
            ),
            status_esperado="respondida",
        )

        resultado = av.avaliar_caso(
            caso,
            documentos_encontrados=[
                "material.txt",
            ],
            texto_resposta=(
                "Informe o setor."
            ),
            documentos_citados=[
                "outro.txt",
            ],
            citacoes_validas=True,
            status_obtido="respondida",
        )

        self.assertFalse(
            resultado.aprovado
        )

        self.assertFalse(
            resultado.citacoes_validas
        )

    def test_avaliar_caso_reprova_status(self):
        caso = av.CasoAvaliacao(
            identificador="sem_evidencia_001",
            pergunta="Qual é o prazo?",
            documentos_esperados=(),
            termos_obrigatorios=(),
            termos_proibidos=(),
            status_esperado=(
                "sem_evidencia"
            ),
        )

        resultado = av.avaliar_caso(
            caso,
            documentos_encontrados=[],
            texto_resposta="",
            documentos_citados=[],
            citacoes_validas=True,
            status_obtido="respondida",
        )

        self.assertFalse(
            resultado.aprovado
        )

        self.assertFalse(
            resultado.status_valido
        )

    def test_documentos_sem_expectativa_nao_penalizam_vazio(self):
        precision, recall = (
            av.precision_recall_documentos(
                [],
                [],
            )
        )

        self.assertEqual(
            precision,
            1.0,
        )

        self.assertEqual(
            recall,
            1.0,
        )

    def test_remove_documentos_duplicados_preservando_ordem(self):
        caso = av.CasoAvaliacao(
            identificador="duplicado",
            pergunta="Pergunta.",
            documentos_esperados=(
                "material.txt",
            ),
        )

        resultado = av.avaliar_caso(
            caso,
            documentos_encontrados=[
                "material.txt",
                "material.txt",
                "outro.txt",
            ],
            texto_resposta="",
            documentos_citados=[
                "material.txt",
                "material.txt",
            ],
            citacoes_validas=True,
            status_obtido=None,
        )

        self.assertEqual(
            resultado.documentos_encontrados,
            (
                "material.txt",
                "outro.txt",
            ),
        )

        self.assertEqual(
            resultado.citacoes_encontradas,
            (
                "material.txt",
            ),
        )

    def test_resumo_consolida_metricas(self):
        caso_a = av.ResultadoCaso(
            identificador="a",
            documentos_encontrados=(
                "a.txt",
            ),
            documentos_esperados=(
                "a.txt",
            ),
            citacoes_encontradas=(
                "a.txt",
            ),
            termos_obrigatorios_encontrados=(),
            termos_obrigatorios_ausentes=(),
            termos_proibidos_encontrados=(),
            status_obtido="respondida",
            status_esperado="respondida",
            precision_documentos=1.0,
            recall_documentos=1.0,
            reciprocal_rank=1.0,
            citacoes_validas=True,
            conteudo_valido=True,
            status_valido=True,
            aprovado=True,
        )

        caso_b = av.ResultadoCaso(
            identificador="b",
            documentos_encontrados=(
                "x.txt",
            ),
            documentos_esperados=(
                "b.txt",
            ),
            citacoes_encontradas=(),
            termos_obrigatorios_encontrados=(),
            termos_obrigatorios_ausentes=(
                "prazo",
            ),
            termos_proibidos_encontrados=(),
            status_obtido="respondida",
            status_esperado="sem_evidencia",
            precision_documentos=0.0,
            recall_documentos=0.0,
            reciprocal_rank=0.0,
            citacoes_validas=False,
            conteudo_valido=False,
            status_valido=False,
            aprovado=False,
        )

        resumo = av.resumir_resultados(
            [
                caso_a,
                caso_b,
            ]
        )

        self.assertEqual(
            resumo.total,
            2,
        )

        self.assertEqual(
            resumo.aprovados,
            1,
        )

        self.assertEqual(
            resumo.reprovados,
            1,
        )

        self.assertEqual(
            resumo.taxa_aprovacao,
            0.5,
        )

        self.assertEqual(
            resumo.precision_media,
            0.5,
        )

        self.assertEqual(
            resumo.recall_media,
            0.5,
        )

        self.assertEqual(
            resumo.mrr,
            0.5,
        )

        self.assertEqual(
            resumo.taxa_citacoes_validas,
            0.5,
        )

    def test_resumo_rejeita_lista_vazia(self):
        with self.assertRaises(
            ValueError
        ):
            av.resumir_resultados(
                []
            )


if __name__ == "__main__":
    unittest.main()