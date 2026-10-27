# Assistente de Procedimentos Administrativos

Aplicação em Python para pesquisar procedimentos administrativos, consultar documentos e gerar respostas opcionais com a Gemini API.

O projeto possui interface de consulta, conversa com contexto limitado, importação de documentos, OCR local para imagens e PDFs digitalizados, busca por palavras, busca semântica local, busca híbrida, sincronização com uma pasta aprovada no Google Drive, respostas com citações verificáveis e uma camada de avaliação automática da qualidade da recuperação e das respostas.

> Projeto de estudo e portfólio. Utilize somente documentos fictícios. A aplicação não representa procedimentos oficiais de uma instituição.

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

## Fluxo

```text
                Pergunta
                   ↓
          ┌────────┴────────┐
          ↓                 ↓
       Palavras         Semântica
          ↓                 ↓
    Ranking lexical    Ranking vetorial
          └────────┬────────┘
                   ↓
                  RRF
                   ↓
            Ranking híbrido
```

## Configuração

```text
RRF_K = 60
PESO_PALAVRAS = 1.0
PESO_SEMANTICA = 1.0
```

A contribuição segue:

```text
peso / (K + posição)
```

## Deduplicação

Trechos encontrados pelos dois métodos não são enviados duas vezes.

Quando existem posições confiáveis:

```text
inicio
fim
texto
```

são utilizados para a identificação.

## Limites

| Item | Valor |
| --- | --- |
| Documentos finais | Até 3 |
| Trechos por documento | Até 4 |
| Peso lexical | 1.0 |
| Peso semântico | 1.0 |
| RRF K | 60 |

O ranking híbrido não representa probabilidade de acerto.

# Avaliação automática

A melhoria de avaliação adiciona uma camada independente para medir o comportamento do assistente.

Arquivos principais:

```text
avaliacao.py
casos_avaliacao.py
executar_avaliacao.py
avaliar_respostas_controladas.py
avaliar_gemini.py
```

# Casos de avaliação

A base de avaliação é definida em:

```text
casos_avaliacao.py
```

Ela utiliza documentos exclusivamente fictícios sobre:

```text
solicitação de material;
correção de frequência;
reembolso;
férias;
acesso a sistema;
empréstimo de equipamento.
```

Atualmente existem:

```text
12 casos de avaliação
```

Cada caso pode definir:

```text
pergunta;
documento esperado;
termos obrigatórios;
termos proibidos;
status esperado.
```

Exemplo conceitual:

```text
Pergunta:
Como pedir reembolso?

Documento esperado:
reembolso.txt

Termos obrigatórios:
nota fiscal
comprovante de pagamento
Financeiro

Termos proibidos:
RH

Status:
respondida
```

# Métricas de recuperação

O módulo:

```text
avaliacao.py
```

calcula métricas determinísticas.

## Precision

Mede quantos documentos recuperados pertencem ao conjunto esperado.

```text
documentos relevantes recuperados
÷
documentos recuperados
```

## Recall

Mede quantos documentos esperados foram recuperados.

```text
documentos relevantes recuperados
÷
documentos relevantes esperados
```

## Reciprocal Rank

Considera a posição do primeiro documento relevante.

```text
1º lugar = 1.000
2º lugar = 0.500
3º lugar = 0.333
```

## MRR

Mean Reciprocal Rank:

```text
média dos Reciprocal Ranks
```

Quanto mais próximo de:

```text
1.0
```

melhor a posição dos documentos corretos.

# Benchmark de recuperação

Execute:

```powershell
python executar_avaliacao.py
```

Esse benchmark:

```text
não chama Gemini;
não usa documentos privados;
compara palavras, semântica e híbrida;
mede Precision;
mede Recall;
mede MRR.
```

Em uma execução observada com os 12 casos fictícios:

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

Eles não devem ser generalizados para outras bases sem novos testes.

# Avaliação controlada de respostas

O módulo:

```text
avaliar_respostas_controladas.py
```

testa o mecanismo de avaliação com respostas cujo conteúdo esperado é conhecido antecipadamente.

Ele verifica:

```text
documento encontrado;
documento citado;
citação validada;
termos obrigatórios;
termos proibidos;
status.
```

Execute:

```powershell
python avaliar_respostas_controladas.py
```

A função dessa etapa é validar o avaliador.

Uma taxa de 100% nessa execução não significa que Gemini possui 100% de qualidade.

# Avaliação opcional com Gemini

O módulo:

```text
avaliar_gemini.py
```

permite executar os mesmos casos com Gemini real.

Nenhuma chamada acontece sem autorização explícita.

Exemplo:

```powershell
python avaliar_gemini.py --modo hibrida --limite 2
```

O programa informa:

```text
modelo;
modos;
quantidade de casos;
máximo de chamadas.
```

Depois exige:

```text
Digite SIM para autorizar essas chamadas:
```

Sem `SIM`:

```text
nenhuma chamada ao Gemini é realizada.
```

## Modos disponíveis

```powershell
python avaliar_gemini.py --modo palavras
```

```powershell
python avaliar_gemini.py --modo semantica
```

```powershell
python avaliar_gemini.py --modo hibrida
```

```powershell
python avaliar_gemini.py --modo todos
```

## Limite de casos

Exemplo:

```powershell
python avaliar_gemini.py --modo hibrida --limite 2
```

Isso permite validar configuração e cota antes de uma execução maior.

# Resultados reais observados

Uma execução isolada da busca híbrida com os 12 casos fictícios obteve:

```text
12 casos
12 aprovados
0 reprovados

Taxa de aprovação: 100%
Recall: 1.000
MRR: 0.903
Citações válidas: 100%
Conteúdo válido: 100%
Status válido: 100%
```

Modelo utilizado nessa execução:

```text
gemini-3.5-flash-lite
```

Esse resultado corresponde somente:

```text
à versão testada;
ao modelo utilizado;
aos 12 casos fictícios;
ao momento daquela execução.
```

Não é garantia de desempenho futuro.

# Comparação real dos modos

Uma execução comparativa também foi realizada.

Na parte concluída sem falhas operacionais:

```text
palavras:
9/12 aprovados
75% de aprovação
Recall: 0.917
MRR: 0.819

semântica:
12/12 aprovados
100% de aprovação
Recall: 1.000
MRR: 1.000
```

A execução híbrida dessa bateria encontrou erros HTTP:

```text
429 RESOURCE_EXHAUSTED
```

em parte das chamadas.

Esses erros são problemas de cota/rate limit e não devem ser tratados como reprovação de qualidade.

Por isso o avaliador foi atualizado para separar:

```text
falhas de qualidade
```

de:

```text
falhas operacionais
```

# Falhas de qualidade x falhas operacionais

A versão atual do avaliador classifica resultados.

## Falha de qualidade

Exemplos:

```text
documento esperado não recuperado;
resposta sem evidência quando deveria responder;
resposta rejeitada pela validação;
termos obrigatórios ausentes;
termos proibidos presentes;
status incorreto;
citação incorreta.
```

Esses casos entram no denominador da taxa de aprovação.

## Falha operacional

Exemplos:

```text
HTTP 429;
falha de conexão;
indisponibilidade do serviço;
erro técnico inesperado;
falha operacional da busca.
```

Esses casos são registrados separadamente.

Eles não reduzem artificialmente a taxa de qualidade.

Exemplo:

```text
Casos planejados: 12
Casos avaliados: 8
Falhas operacionais: 4

Aprovados entre os avaliados: 8/8

Taxa de qualidade:
100%
```

Isso é diferente de afirmar:

```text
8/12 = 66,7%
```

quando os quatro casos restantes nem chegaram a ser avaliados.

# Resultados locais

As execuções reais são salvas em:

```text
.avaliacoes/
```

Exemplo:

```text
.avaliacoes/avaliacao_gemini_20261027T200753Z.json
```

Essa pasta está no `.gitignore`.

Os resultados não devem ser publicados automaticamente.

A chave da API não é gravada nesses arquivos.

# Interfaces

## Consulta individual

`interface.py` oferece:

```text
Por palavras
Por significado (local)
Híbrida (palavras + significado)
```

Fluxo:

```text
Escolher modo
    ↓
Pergunta
    ↓
Busca
    ↓
Revisão
    ↓
Autorização
    ↓
Gemini
    ↓
Validação
    ↓
Resposta
```

## Chat

`chat.py` também oferece os três modos.

O modo é bloqueado quando já existe:

```text
histórico;
ou pergunta pendente.
```

Para trocar:

```text
Nova conversa
```

O modo utilizado é preservado no turno.

# Memória da conversa

A conversa utiliza:

```text
pergunta atual;
primeira pergunta;
última pergunta respondida.
```

As respostas anteriores da IA não são utilizadas como fontes.

O histórico é temporário e fica na sessão do navegador.

Limite atual:

```text
10 respostas por conversa
```

# Importação manual

Fluxo:

```text
arquivo
  ↓
extração
  ↓
OCR se necessário
  ↓
prévia
  ↓
revisão
  ↓
confirmação
  ↓
TXT local
```

Formatos:

```text
TXT
PDF
DOCX
PNG
JPG
JPEG
BMP
TIF
TIFF
WEBP
```

Limites:

| Item | Limite |
| --- | --- |
| Arquivo | 5 MiB |
| PDF | 30 páginas |
| Texto | 100.000 caracteres |
| DOCX descompactado | 20 MiB |
| Página OCR | 25 milhões de pixels |

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

Fluxo:

```text
Drive
 ↓
listagem
 ↓
download
 ↓
extração/OCR
 ↓
validação
 ↓
preparação
 ↓
aplicação
```

Se um arquivo compatível falhar antes da aplicação:

```text
a base nova não é aplicada parcialmente.
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
├── .gitignore
├── README.md
├── requirements.txt
├── requirements-semantica.txt
├── requirements-drive.txt
├── requirements-ocr.txt
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
└── test_avaliar_gemini.py
```

# Instalação

## Ambiente virtual

```powershell
git clone https://github.com/limaavls/assistente-procedimentos-python.git
cd assistente-procedimentos-python
python -m venv venv
```

## Dependências principais

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Busca semântica

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements-semantica.txt
.\venv\Scripts\python.exe busca_semantica.py
```

## OCR

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements-ocr.txt
```

## Google Drive

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements-drive.txt
```

# Configuração

`.env`:

```env
GEMINI_API_KEY=COLE_SUA_CHAVE_AQUI
```

Opcional:

```env
GEMINI_MODEL=SEU_MODELO
```

Drive:

```env
DRIVE_FOLDER_ID=ID_DA_PASTA
DRIVE_CREDENTIALS_FILE=.secrets/google-drive.json
```

# Executar

## Chat

```powershell
python -m streamlit run chat.py --server.address=127.0.0.1 --browser.gatherUsageStats=false
```

## Interface individual

```powershell
python -m streamlit run interface.py --server.address=127.0.0.1 --browser.gatherUsageStats=false
```

## Benchmark de recuperação

```powershell
python executar_avaliacao.py
```

## Benchmark controlado de respostas

```powershell
python avaliar_respostas_controladas.py
```

## Avaliação real

```powershell
python avaliar_gemini.py --modo hibrida
```

# Proteção no Git

O `.gitignore` inclui:

```gitignore
.env
venv/
.venv/
__pycache__/
documentos/importado_*.txt
documentos/drive_*.txt
.cache_modelos/
.secrets/
.estado_drive/
.avaliacoes/
```

Isso protege:

```text
credenciais;
modelos locais;
documentos importados;
documentos sincronizados;
backups;
resultados locais de avaliação.
```

# Testes automatizados

Execute:

```powershell
python -m unittest discover -v
```

Após a implementação da melhoria de avaliação automática, a suíte completa executada localmente apresentou:

```text
Ran 261 tests in 24.143s

OK
```

Os testes não dependem de:

```text
Gemini real;
Google Drive real;
credenciais reais;
documentos privados.
```

# Cobertura da avaliação

Os testes incluem:

```text
Precision;
Recall;
Reciprocal Rank;
MRR;
termos obrigatórios;
termos proibidos;
status esperado;
documento esperado;
documento citado;
citações válidas;
falhas de qualidade;
falhas operacionais;
HTTP 429;
falhas de conexão;
resultados controlados;
salvamento sem chave da API;
comparação dos três modos.
```

Arquivos principais de teste da melhoria:

```text
test_avaliacao.py
test_executar_avaliacao.py
test_avaliar_respostas_controladas.py
test_avaliar_gemini.py
```

# Limitações da avaliação

Os 12 casos atuais são uma base pequena e fictícia.

Eles servem para:

```text
regressão;
comparação inicial;
validação da arquitetura;
demonstração de métricas.
```

Eles não representam:

```text
benchmark científico;
garantia de generalização;
garantia de precisão em documentos reais;
garantia de qualidade futura do modelo.
```

Uma avaliação maior deveria incluir:

```text
mais documentos;
mais perguntas;
perguntas ambíguas;
perguntas sem resposta;
documentos conflitantes;
documentos longos;
documentos semelhantes;
casos negativos;
avaliação repetida em diferentes execuções.
```

# Privacidade

OCR, importação e buscas são locais.

Somente a geração de respostas com Gemini envia os trechos autorizados.

A avaliação real utiliza exclusivamente:

```text
DOCUMENTOS_AVALIACAO
```

definidos em:

```text
casos_avaliacao.py
```

Ela não utiliza automaticamente:

```text
documentos/
```

A chave da API não é salva nos resultados.

# Limitações gerais

O projeto ainda não possui:

```text
autenticação de usuários;
banco persistente de conversas;
controle institucional de versões;
controle de vigência;
banco vetorial persistente;
dashboard visual de métricas;
n8n integrado;
deploy em Docker;
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

# Próximas melhorias

| Ordem | Melhoria | Situação |
| --- | --- | --- |
| 1 | Citações verificáveis | Concluída |
| 2 | OCR | Concluída |
| 3 | Busca híbrida | Concluída |
| 4 | Avaliação automática da qualidade | Concluída |
| 5 | Integração com n8n e automações | Próxima etapa |
| 6 | Dashboard de métricas | Planejada |
| 7 | Docker e demonstração online | Planejada |

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
- Python `unittest`

# Autor

Desenvolvido por Victor Lima Silva como projeto de aprendizado em Python, inteligência artificial, automação e aplicação de tecnologia à rotina administrativa.

GitHub:

```text
https://github.com/limaavls
```