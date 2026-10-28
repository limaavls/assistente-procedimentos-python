import unittest
from pathlib import Path


BASE = Path(__file__).resolve().parent


class TestDockerConfig(
    unittest.TestCase
):

    def test_dockerfile_existe(self):
        caminho = (
            BASE
            / "Dockerfile"
        )

        self.assertTrue(
            caminho.is_file()
        )

    def test_dockerignore_existe(self):
        caminho = (
            BASE
            / ".dockerignore"
        )

        self.assertTrue(
            caminho.is_file()
        )

    def test_requirements_demo_existe(self):
        caminho = (
            BASE
            / "requirements-demo.txt"
        )

        self.assertTrue(
            caminho.is_file()
        )

    def test_requirements_principal_inclui_semantica(self):
        texto = (
            BASE
            / "requirements.txt"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "-r requirements-semantica.txt",
            texto,
        )

    def test_requirements_principal_inclui_ocr(self):
        texto = (
            BASE
            / "requirements.txt"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "-r requirements-ocr.txt",
            texto,
        )

    def test_requirements_demo_aponta_para_principal(self):
        texto = (
            BASE
            / "requirements-demo.txt"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "-r requirements.txt",
            texto,
        )

    def test_requirements_semantica_tem_sentence_transformers(self):
        texto = (
            BASE
            / "requirements-semantica.txt"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "sentence-transformers",
            texto,
        )

    def test_packages_existe(self):
        caminho = (
            BASE
            / "packages.txt"
        )

        self.assertTrue(
            caminho.is_file()
        )

    def test_packages_tem_dependencias_linux(self):
        texto = (
            BASE
            / "packages.txt"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "libgl1",
            texto,
        )

        self.assertIn(
            "libglib2.0-0",
            texto,
        )

    def test_dockerfile_usa_python_312(self):
        texto = (
            BASE
            / "Dockerfile"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "FROM python:3.12-slim",
            texto,
        )

    def test_dockerfile_instala_dependencias_demo(self):
        texto = (
            BASE
            / "Dockerfile"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "-r requirements-demo.txt",
            texto,
        )

    def test_dockerfile_usa_pytorch_cpu_only(self):
        texto = (
            BASE
            / "Dockerfile"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "https://download.pytorch.org/whl/cpu",
            texto,
        )

        self.assertIn(
            "torch",
            texto,
        )

    def test_dockerfile_prepara_modelo_semantico(self):
        texto = (
            BASE
            / "Dockerfile"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "RUN python busca_semantica.py",
            texto,
        )

    def test_dockerfile_nao_copia_env_explicitamente(self):
        texto = (
            BASE
            / "Dockerfile"
        ).read_text(
            encoding="utf-8"
        )

        self.assertNotIn(
            "COPY .env",
            texto,
        )

    def test_dockerfile_expoe_porta_streamlit(self):
        texto = (
            BASE
            / "Dockerfile"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "EXPOSE 8501",
            texto,
        )

    def test_dockerfile_usa_chat_como_entrada(self):
        texto = (
            BASE
            / "Dockerfile"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            '"chat.py"',
            texto,
        )

        self.assertIn(
            '"--server.address=0.0.0.0"',
            texto,
        )

    def test_dockerfile_tem_healthcheck(self):
        texto = (
            BASE
            / "Dockerfile"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "HEALTHCHECK",
            texto,
        )

        self.assertIn(
            "/_stcore/health",
            texto,
        )

    def test_dockerignore_protege_env(self):
        texto = (
            BASE
            / ".dockerignore"
        ).read_text(
            encoding="utf-8"
        )

        linhas = {
            linha.strip()
            for linha in texto.splitlines()
        }

        self.assertIn(
            ".env",
            linhas,
        )

    def test_dockerignore_protege_secrets(self):
        texto = (
            BASE
            / ".dockerignore"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            ".secrets/",
            texto,
        )

    def test_dockerignore_exclui_cache_local(self):
        texto = (
            BASE
            / ".dockerignore"
        ).read_text(
            encoding="utf-8"
        )

        self.assertIn(
            ".cache_modelos/",
            texto,
        )


if __name__ == "__main__":
    unittest.main()