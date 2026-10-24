import unittest

from app import normalizar, trechos_com_termo


class TestBuscaDocumentos(unittest.TestCase):

    def test_normaliza_acentos_e_maiusculas(self):
        resultado = normalizar("SOLICITAÇÃO")
        self.assertEqual(resultado, "solicitacao")

    def test_busca_sem_acento(self):
        texto = "Procedimento de solicitação de material."
        resultado = trechos_com_termo(texto, "solicitacao")
        self.assertEqual(resultado, [texto])

    def test_busca_com_maiusculas(self):
        texto = "Material disponível."
        resultado = trechos_com_termo(texto, "MATERIAL")
        self.assertEqual(resultado, [texto])

    def test_nao_busca_parte_de_palavra(self):
        texto = "Material disponível."
        resultado = trechos_com_termo(texto, "mat")
        self.assertEqual(resultado, [])

    def test_termo_inexistente(self):
        texto = "Solicitação de material."
        resultado = trechos_com_termo(texto, "ferias")
        self.assertEqual(resultado, [])

    def test_documento_vazio(self):
        resultado = trechos_com_termo("", "material")
        self.assertEqual(resultado, [])

    def test_junta_trechos_sobrepostos(self):
        texto = (
            "Início do procedimento.\n"
            "Material pendente.\n"
            "Material aprovado.\n"
            "Fim do procedimento."
        )
        resultado = trechos_com_termo(texto, "material")
        self.assertEqual(resultado, [texto])


if __name__ == "__main__":
    unittest.main()