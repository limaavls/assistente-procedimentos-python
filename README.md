# Assistente de Procedimentos Administrativos

Aplicação em Python para pesquisar procedimentos administrativos, consultar documentos e gerar respostas opcionais com a Gemini API.

O projeto possui interface de consulta, conversa com contexto limitado, importação de documentos, OCR local para imagens e PDFs digitalizados, busca por palavras, busca semântica local, busca híbrida, sincronização com uma pasta aprovada no Google Drive, respostas com citações verificáveis, avaliação automática da qualidade, dashboard local de métricas, execução em Docker e demonstração online pública.

> Projeto de estudo e portfólio. Utilize somente documentos fictícios. A aplicação não representa procedimentos oficiais de uma instituição.

# Demonstração online

A versão pública está disponível em:

```text
https://assistente-procedimentos-victor.streamlit.app/
```

A demonstração utiliza Streamlit Community Cloud e executa o `chat.py`.

# Objetivo

Aplicar programação, inteligência artificial e automação a uma necessidade da rotina administrativa: localizar informações em documentos, extrair texto de arquivos digitais e digitalizados, recuperar trechos relevantes por diferentes estratégias, gerar respostas fundamentadas e medir automaticamente a qualidade do sistema.

O desenvolvimento reúne:

```text
processamento de documentos;
OCR local;
busca por palavras;
busca semântica;
busca híbrida;
interface web;
integração com Gemini;
integração com Google Drive;
validação local de citações;
avaliação automática;
métricas de recuperação;
dashboard de métricas;
Docker;
deploy online;
testes automatizados.
```

A aplicação não aprova solicitações nem substitui a conferência dos procedimentos oficiais.

# Funcionalidades

| Recurso | Funcionamento |
| --- | --- |
| Consulta individual | Pesquisa e visualização de trechos e documentos completos. |
| Conversa | Perguntas complementares com memória limitada do assunto. |
| Importação local | Seleção de TXT, PDF, DOCX e imagens pelo painel lateral do chat. |
| Prévia de importação | Conferência do texto antes da inclusão manual. |
| OCR local | Reconhecimento de texto em imagens e páginas digitalizadas de PDFs. |
| PDFs mistos | Usa extração textual nas páginas normais e OCR somente nas páginas sem texto. |
| Busca por palavras | Ordenação por correspondência de termos da pergunta. |
| Busca semântica | Comparação local de embeddings da pergunta e dos trechos. |
| Busca híbrida | Combina os rankings lexical e semântico usando Reciprocal Rank Fusion. |
| Respostas com Gemini | Geração opcional após revisão e autorização. |
| Citações verificáveis | Cada orientação precisa apontar para uma fonte e uma passagem existente no trecho enviado. |
| Fontes por consulta | Referências `F1`, `F2`, `F3` etc. são criadas localmente por consulta. |
| Histórico com evidências | O chat preserva uma cópia das fontes utilizadas em cada resposta. |
| Avaliação de recuperação | Mede Precision, Recall e MRR dos modos de busca. |
| Avaliação de respostas | Confere termos esperados, termos proibidos, status e citações. |
| Benchmark controlado | Testa o avaliador sem chamar Gemini. |
| Benchmark real opcional | Executa casos fictícios com Gemini após autorização explícita. |
| Separação de falhas | Diferencia falhas de qualidade de falhas operacionais, como HTTP 429. |
| Dashboard de métricas | Exibe KPIs, histórico, comparação entre modos e falhas operacionais. |
| Compatibilidade histórica | O dashboard interpreta resultados gerados antes e depois da separação de falhas operacionais. |
| Filtros do dashboard | Permite filtrar avaliações por modo de busca e modelo. |
| Docker | Executa a aplicação em ambiente Linux isolado e reproduzível. |
| PyTorch CPU-only | Evita dependências CUDA desnecessárias na imagem Docker. |
| Healthcheck Docker | Valida automaticamente a disponibilidade do Streamlit. |
| Demo online | Publicação em Streamlit Community Cloud. |
| Verificação do Drive | Confirma acesso e lista itens da pasta aprovada. |
| Sincronização do Drive | Criação, atualização e retirada de cópias locais gerenciadas. |
| OCR no Drive | Imagens e PDFs digitalizados compatíveis podem entrar na base sincronizada. |
| Repetição periódica | Sincronização em intervalos enquanto o programa estiver em execução. |
| Backups locais | Preservação das cópias anteriores antes de alterações. |
| Testes e GitHub Actions | Verificações automatizadas sem depender de credenciais reais. |

# Arquitetura geral

```text
Documentos
   ↓
Importação / Google Drive
   ↓
Extração de texto
   ↓
OCR quando necessário
   ↓
Base TXT local
   ↓
┌───────────────────────────────┐
│ Estratégia de recuperação     │
│                               │
│ • palavras                    │
│ • semântica                   │
│ • híbrida                     │
└───────────────────────────────┘
   ↓
Trechos candidatos
   ↓
Referências locais F1, F2, F3...
   ↓
Revisão do usuário
   ↓
Autorização explícita
   ↓
Gemini
   ↓
JSON estruturado
   ↓
Validação local das citações
   ↓
Resposta apresentada
   ↓
Avaliação opcional
   ↓
Resultados locais em JSON
   ↓
Dashboard de métricas
```

# Citações verificáveis

O módulo:

```text
citacoes.py
```

centraliza a preparação, validação e apresentação das evidências utilizadas pela IA.

Para cada consulta, somente os trechos realmente enviados recebem identificadores locais:

```text
F1
F2
F3
...
```

Esses identificadores existem apenas dentro daquela consulta.

`F1` de uma pergunta não representa necessariamente o mesmo documento ou trecho de `F1` em outra pergunta.

## Fluxo

```text
Pergunta
   ↓
Busca local
   ↓
Trechos candidatos
   ↓
Criação de F1, F2, F3...
   ↓
Revisão
   ↓
Autorização
   ↓
Gemini
   ↓
Resposta JSON estruturada
   ↓
Validação local
   ↓
Apresentação
```

A resposta esperada segue estrutura equivalente a:

```json
{
  "status": "respondida",
  "itens": [
    {
      "texto": "Orientação baseada nos documentos.",
      "evidencias": [
        {
          "fonte_id": "F1",
          "citacao": "Passagem literal existente no trecho enviado."
        }
      ]
    }
  ]
}
```

Estados aceitos:

| Status | Significado |
| --- | --- |
| `respondida` | Existem itens fundamentados nas evidências. |
| `parcial` | Somente parte da pergunta pôde ser respondida. |
| `sem_evidencia` | Nenhuma orientação pôde ser fundamentada. |

Quando não existe evidência suficiente:

```text
Não encontrei essa informação nos trechos consultados.
```

Essa mensagem é definida pela aplicação.

## Validação local

Antes da apresentação, a aplicação verifica:

```text
JSON válido;
status permitido;
estrutura esperada;
existência da fonte;
fonte pertencente à consulta atual;
citação não vazia;
citação contida no trecho correspondente;
orientação acompanhada de evidência;
ausência de itens em sem_evidencia.
```

A comparação normaliza apenas espaços e quebras de linha.

Não existe correção aproximada de:

```text
palavras;
números;
negações;
datas;
valores.
```

Exemplo:

```text
Documento:
O prazo é de 5 dias úteis.

Citação:
O prazo é de 10 dias úteis.

Resultado:
REJEITADA
```

## Limite da validação

A validação confirma que:

```text
a fonte existe;
a fonte pertence à consulta;
a passagem citada aparece no trecho.
```

Ela não comprova que a interpretação da IA está necessariamente correta.

Por isso a aplicação informa:

```text
Referências conferidas quanto à existência e ao trecho.
A interpretação da resposta ainda exige revisão.
```

# Localização das fontes

As buscas preservam a posição dos trechos sempre que possível.

`TrechoCandidato` registra:

```text
texto
inicio
fim
indice_recorte
```

## PDF

Marcadores de página são mantidos:

```text
[Página 1]
[Página 2]
[Página 3]
```

Isso permite localizar citações quando a posição é confiável.

Exemplos:

```text
Página 3
```

ou:

```text
Páginas 3-4
```

O número interno de um recorte semântico não é considerado número de página.

# OCR local

O módulo:

```text
ocr.py
```

permite trabalhar com imagens e páginas digitalizadas.

Tecnologias:

```text
RapidOCR
ONNX Runtime
PyMuPDF
```

## Formatos aceitos

```text
PNG
JPG
JPEG
BMP
TIF
TIFF
WEBP
```

## PDFs digitalizados

O sistema tenta primeiro a extração textual comum.

```text
Página
   ↓
Possui texto?
 ↙       ↘
Sim      Não
 ↓        ↓
Texto   Renderização
nativo      ↓
           OCR
```

Assim, OCR é utilizado somente quando necessário.

## PDF misto

Exemplo:

```text
[Página 1]
Texto extraído normalmente.

[Página 2]
[Extração: OCR]
Texto reconhecido pelo OCR.

[Página 3]
Texto extraído normalmente.
```

## Limites

```text
DPI padrão: 200
DPI permitido: 72 a 300
Máximo: 25.000.000 de pixels por página renderizada
```

PDFs protegidos continuam sendo recusados.

## Revisão

OCR pode interpretar incorretamente:

```text
letras;
números;
datas;
acentos;
valores;
nomes;
pontuação.
```

A aplicação não corrige automaticamente o conteúdo reconhecido.

# Modos de busca

Existem três estratégias:

```text
Por palavras
Por significado (local)
Híbrida (palavras + significado)
```

Todas retornam o mesmo contrato interno:

```text
arquivo
texto original
lista de TrechoCandidato
```

# Busca por palavras

Implementada em:

```text
busca.py
```

Classifica documentos de acordo com palavras distintas em comum com a pergunta.

Características:

```text
desconsidera maiúsculas;
desconsidera minúsculas;
desconsidera acentos;
preserva posições dos parágrafos;
não reconhece sinônimos automaticamente.
```

É útil principalmente para:

```text
termos exatos;
siglas;
nomes;
códigos;
expressões literais.
```

# Busca semântica

Implementada em:

```text
busca_semantica.py
```

Modelo:

```text
intfloat/multilingual-e5-small
```

Fluxo:

```text
Pergunta
   ↓
Embedding

Documentos
   ↓
Recortes
   ↓
Embeddings
   ↓
Similaridade
   ↓
Ranking
```

Configuração:

| Item | Regra |
| --- | --- |
| Execução | CPU local |
| Recortes | Até 300 tokens |
| Sobreposição | 50 tokens |
| Base de demonstração | Até 500 trechos |
| Documentos | Até 3 |
| Trechos por documento | Até 2 |

O modelo fica em:

```text
.cache_modelos/
```

# Busca híbrida

Implementada em:

```text
busca_hibrida.py
```

Combina:

```text
busca por palavras
+
busca semântica
```

utilizando:

```text
Reciprocal Rank Fusion
```

ou:

```text
RRF
```

## Configuração

```text
RRF_K = 60
PESO_PALAVRAS = 1.0
PESO_SEMANTICA = 1.0
```

## Limites

| Item | Valor |
| --- | --- |
| Documentos finais | Até 3 |
| Trechos por documento | Até 4 |
| Peso lexical | 1.0 |
| Peso semântico | 1.0 |
| RRF K | 60 |

# Avaliação automática

Arquivos principais:

```text
avaliacao.py
casos_avaliacao.py
executar_avaliacao.py
avaliar_respostas_controladas.py
avaliar_gemini.py
```

Atualmente existem:

```text
12 casos de avaliação
```

A base utiliza documentos exclusivamente fictícios.

# Métricas de recuperação

São calculadas:

```text
Precision;
Recall;
Reciprocal Rank;
MRR.
```

# Benchmark de recuperação

Execute:

```powershell
python executar_avaliacao.py
```

Em uma execução observada:

```text
palavras:
aprovação de recuperação: 91,7%
recall: 0,917
MRR: 0,819

semântica:
aprovação de recuperação: 100%
recall: 1,000
MRR: 1,000

híbrida:
aprovação de recuperação: 100%
recall: 1,000
MRR: 0,903
```

Esses números se referem apenas ao conjunto fictício atual.

# Avaliação opcional com Gemini

Execute:

```powershell
python avaliar_gemini.py --modo hibrida
```

ou:

```powershell
python avaliar_gemini.py --modo todos
```

Nenhuma chamada ocorre sem autorização explícita.

# Falhas de qualidade x falhas operacionais

Falhas de qualidade entram na taxa de aprovação.

Exemplos:

```text
documento esperado não recuperado;
status incorreto;
conteúdo esperado ausente;
citação rejeitada.
```

Falhas operacionais são registradas separadamente.

Exemplos:

```text
HTTP 429;
falha de conexão;
indisponibilidade da API;
erro técnico.
```

# Resultados locais

As avaliações reais são salvas em:

```text
.avaliacoes/
```

Essa pasta está no `.gitignore`.

# Dashboard de métricas

O dashboard está em:

```text
dashboard_metricas.py
```

e a camada de leitura em:

```text
metricas_dashboard.py
```

Execute:

```powershell
python -m streamlit run dashboard_metricas.py --server.address=127.0.0.1 --browser.gatherUsageStats=false
```

O painel apresenta:

```text
execuções;
casos avaliados;
falhas operacionais;
taxa de aprovação;
Precision;
Recall;
MRR;
citações válidas;
conteúdo válido;
status válido;
histórico;
comparação entre modos.
```

O dashboard também possui compatibilidade com arquivos antigos de avaliação.

# Docker

O projeto possui suporte a execução em container através de:

```text
Dockerfile
.dockerignore
requirements-demo.txt
```

A imagem utiliza:

```text
python:3.12-slim
```

# PyTorch CPU-only

A imagem Docker instala PyTorch pela distribuição CPU-only:

```text
https://download.pytorch.org/whl/cpu
```

Isso evita dependências CUDA desnecessárias em um ambiente sem GPU.

Na comparação local, a otimização reduziu aproximadamente:

```text
Imagem anterior:
Disk usage: 11,4 GB
Content size: 3,82 GB

Imagem CPU-only:
Disk usage: 3,86 GB
Content size: aproximadamente 999 MB
```

Os números podem variar conforme cache e versão das dependências.

# Build Docker

Execute:

```powershell
docker build -t assistente-procedimentos .
```

Para reconstrução completa:

```powershell
docker build --no-cache -t assistente-procedimentos .
```

# Executar Docker

Com variáveis do `.env` local:

```powershell
docker run --name assistente-procedimentos-container --rm --env-file .env -p 8501:8501 assistente-procedimentos
```

Depois acesse:

```text
http://127.0.0.1:8501
```

# Healthcheck Docker

O Dockerfile utiliza:

```text
/_stcore/health
```

para verificar se o Streamlit está respondendo.

Consulte com:

```powershell
docker inspect --format='{{.State.Health.Status}}' assistente-procedimentos-container
```

Resultado esperado:

```text
healthy
```

# Testes dentro do container

A suíte também pode ser executada dentro da imagem Linux:

```powershell
docker exec assistente-procedimentos-container python -m unittest discover -v
```

Durante o desenvolvimento, uma execução dentro do container apresentou:

```text
Ran 300 tests in 15.673s

OK
```

# Dependências para deploy

A organização atual é:

```text
requirements.txt
├── dependências principais
├── requirements-semantica.txt
└── requirements-ocr.txt
```

`requirements-semantica.txt`:

```text
sentence-transformers
```

`requirements-ocr.txt`:

```text
RapidOCR
ONNX Runtime
PyMuPDF
```

`requirements-demo.txt`:

```text
-r requirements.txt
```

# Pacotes Linux

Para ambientes de deploy Linux, o projeto contém:

```text
packages.txt
```

com:

```text
libgl1
libglib2.0-0
```

# Demonstração online

A aplicação está publicada no Streamlit Community Cloud:

```text
https://assistente-procedimentos-victor.streamlit.app/
```

Configuração utilizada:

```text
Repository:
limaavls/assistente-procedimentos-python

Branch:
main

Main file:
chat.py

Python:
3.12
```

# Secrets do deploy

A chave Gemini não fica no GitHub.

Ela é configurada no painel de Secrets do Streamlit:

```toml
GEMINI_API_KEY = "CHAVE_CONFIGURADA_NO_STREAMLIT"
GEMINI_MODEL = "gemini-3.5-flash-lite"
```

Nunca publique a chave real no README ou no código.

# Interfaces

## Chat

Execute localmente:

```powershell
python -m streamlit run chat.py --server.address=127.0.0.1 --browser.gatherUsageStats=false
```

## Consulta individual

```powershell
python -m streamlit run interface.py --server.address=127.0.0.1 --browser.gatherUsageStats=false
```

## Dashboard

```powershell
python -m streamlit run dashboard_metricas.py --server.address=127.0.0.1 --browser.gatherUsageStats=false
```

# Google Drive

A sincronização suporta:

```text
TXT
PDF
DOCX
Google Docs
PNG
JPG/JPEG
BMP
TIFF
WEBP
```

Backups:

```text
.estado_drive/historico/
```

Manifesto:

```text
.estado_drive/manifesto.json
```

# Organização do projeto

```text
assistente-procedimentos-python/
├── .github/
│   └── workflows/
│       └── testes.yml
├── documentos/
├── .cache_modelos/
├── .secrets/
├── .estado_drive/
├── .avaliacoes/
├── .dockerignore
├── .gitignore
├── Dockerfile
├── README.md
├── packages.txt
├── requirements.txt
├── requirements-semantica.txt
├── requirements-drive.txt
├── requirements-ocr.txt
├── requirements-demo.txt
├── app.py
├── busca.py
├── busca_semantica.py
├── busca_hibrida.py
├── citacoes.py
├── consulta_ia.py
├── conversa.py
├── importacao.py
├── ocr.py
├── painel_documentos.py
├── interface.py
├── chat.py
├── verificar_drive.py
├── sincronizar_drive.py
├── avaliacao.py
├── casos_avaliacao.py
├── executar_avaliacao.py
├── avaliar_respostas_controladas.py
├── avaliar_gemini.py
├── metricas_dashboard.py
├── dashboard_metricas.py
├── test_app.py
├── test_busca.py
├── test_busca_semantica.py
├── test_busca_hibrida.py
├── test_citacoes.py
├── test_consulta_ia.py
├── test_conversa.py
├── test_importacao.py
├── test_ocr.py
├── test_painel_documentos.py
├── test_interface.py
├── test_chat.py
├── test_verificar_drive.py
├── test_sincronizar_drive.py
├── test_avaliacao.py
├── test_executar_avaliacao.py
├── test_avaliar_respostas_controladas.py
├── test_avaliar_gemini.py
├── test_metricas_dashboard.py
├── test_dashboard_metricas.py
└── test_docker_config.py
```

# Testes automatizados

Execute:

```powershell
python -m unittest discover -v
```

Durante o desenvolvimento, a suíte foi validada localmente e também dentro do container Docker.

Os testes não dependem de:

```text
Gemini real;
Google Drive real;
credenciais reais;
documentos privados.
```

# Privacidade

OCR, importação, buscas e dashboard são locais.

Somente a geração de respostas com Gemini envia os trechos autorizados.

Arquivos protegidos pelo Git incluem:

```text
.env
.secrets/
.estado_drive/
.avaliacoes/
.cache_modelos/
documentos/importado_*.txt
documentos/drive_*.txt
```

O `.dockerignore` também impede que credenciais e dados locais sejam incorporados à imagem.

# Limitações gerais

O projeto ainda não possui:

```text
autenticação própria de usuários;
banco persistente de conversas;
controle institucional de versões;
controle de vigência;
banco vetorial persistente;
integração com n8n;
garantia de resposta correta.
```

# Ciclo de melhorias

| Melhoria | Situação |
| --- | --- |
| Conversa com contexto | Concluída |
| Importação TXT/PDF/DOCX | Concluída |
| Busca semântica | Concluída |
| Sincronização Google Drive | Concluída |
| Citações verificáveis | Concluída |
| OCR | Concluída |
| Busca híbrida | Concluída |
| Avaliação automática da qualidade | Concluída |
| Dashboard de métricas | Concluída |
| Docker | Concluída |
| Demonstração online | Concluída |

# Próximas melhorias

A ordem atual é:

| Ordem | Melhoria | Situação |
| --- | --- | --- |
| 1 | Citações verificáveis | Concluída |
| 2 | OCR | Concluída |
| 3 | Busca híbrida | Concluída |
| 4 | Avaliação automática da qualidade | Concluída |
| 5 | Dashboard de métricas | Concluída |
| 6 | Docker e demonstração online | Concluída |
| 7 | Integração com n8n e automações | Próxima etapa |

# Referências

- Google Gemini API
- Google Drive API
- Sentence Transformers
- `intfloat/multilingual-e5-small`
- RapidOCR
- ONNX Runtime
- PyMuPDF
- Reciprocal Rank Fusion
- Streamlit
- Streamlit Community Cloud
- Docker
- PyTorch
- Pandas
- Python `unittest`

# Autor

Desenvolvido por Victor Lima Silva como projeto de aprendizado em Python, inteligência artificial, automação e aplicação de tecnologia à rotina administrativa.

GitHub:

```text
https://github.com/limaavls
```

Demo:

```text
https://assistente-procedimentos-victor.streamlit.app/
```