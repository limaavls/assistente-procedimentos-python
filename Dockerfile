FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV HF_HUB_DISABLE_TELEMETRY=1

WORKDIR /app

COPY requirements.txt .
COPY requirements-semantica.txt .
COPY requirements-ocr.txt .
COPY requirements-demo.txt .

# Instala PyTorch CPU-only para evitar dependências CUDA
# desnecessárias em ambiente sem GPU.
RUN python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu \
        torch \
    && python -m pip install --no-cache-dir \
        -r requirements-demo.txt

COPY . .

# Prepara o modelo semântico durante a construção da imagem.
RUN python busca_semantica.py

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=5)"

CMD ["python", "-m", "streamlit", "run", "chat.py", "--server.address=0.0.0.0", "--server.port=8501", "--browser.gatherUsageStats=false", "--server.headless=true"]