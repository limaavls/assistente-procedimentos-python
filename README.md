# Assistente de Procedimentos Administrativos

Aplicação em Python com interface web em Streamlit para pesquisar procedimentos administrativos, consultar documentos de origem e gerar respostas opcionais com a Gemini API.

O projeto aplica programação a uma necessidade da rotina administrativa: localizar orientações em documentos e conferir a origem das informações apresentadas.

> Projeto de estudo e portfólio. Todos os documentos de demonstração são fictícios. A aplicação não representa orientações oficiais de uma instituição.

## Objetivo

Desenvolver uma ferramenta de consulta e praticar leitura de arquivos, pesquisa textual, interface web, integração com IA, testes automatizados e controle de versões.

A aplicação não aprova solicitações, não executa procedimentos administrativos e não substitui a conferência de documentos oficiais.

## Funcionalidades implementadas

| Recurso | Descrição |
| --- | --- |
| Interface web | Consulta pelo navegador com Streamlit. |
| Busca por perguntas e palavras-chave | Separa os termos da pesquisa e procura correspondências nos documentos. |
| Normalização | Compara textos sem depender de acentos ou maiúsculas. |
| Ordenação dos resultados | Prioriza documentos com mais palavras distintas em comum com a pesquisa. |
| Consulta às fontes | Mostra parágrafos encontrados e permite abrir o documento completo. |
| Resposta com Gemini | Geração opcional na interface e pelo terminal. |
| Confirmação antes do envio | Exige autorização antes de enviar a pergunta e os trechos à API. |
| Testes automatizados | Verificações da busca e da integração com respostas simuladas. |
| GitHub Actions | Instala as dependências e executa os testes a cada push. |

A geração de respostas com IA é experimental. As afirmações e as referências precisam ser conferidas nos documentos originais.

## Interface web

A interface está em `interface.py`.

O usuário pode realizar uma busca local, conferir os documentos encontrados e, opcionalmente, solicitar uma resposta ao Gemini.

```text
Digitar uma pergunta
        ↓
Clicar em Pesquisar
        ↓
Conferir os parágrafos e os documentos de origem
        ↓
Revisar os trechos selecionados para envio
        ↓
Autorizar o envio ao Google
        ↓
Clicar em Gerar resposta com IA
        ↓
Ler a resposta e conferir as fontes
```

Pesquisar não realiza uma chamada à IA. O envio depende da autorização e do botão específico.

A pergunta utilizada na consulta aparece em `Pesquisa em análise`. Para alterar a pergunta ou atualizar os resultados, é necessário clicar novamente em `Pesquisar`.

Uma nova pesquisa limpa a resposta anterior e exige nova autorização.

A resposta é mantida durante as interações da sessão, mas não existe um histórico permanente de consultas.

## Como funciona a busca

A aplicação lê arquivos TXT em UTF-8 diretamente da pasta `documentos`.

Na interface, a pergunta é separada em palavras. Alguns termos comuns são ignorados, e os documentos são ordenados pela quantidade de palavras distintas em comum com a pesquisa.

Por exemplo:

```text
Como solicitar material?
```

é utilizada para procurar palavras relevantes nos textos. Os resultados apresentam os parágrafos originais, não um resumo produzido pela busca.

A ordenação não representa uma porcentagem de confiança. Um documento pode conter palavras da pergunta sem apresentar a resposta completa.

### Dois modos de pesquisa

| Modo | Comportamento |
| --- | --- |
| `app.py` | Busca literal por palavra ou expressão, com linhas de contexto. |
| `busca.py`, utilizado pela interface e pela consulta com IA | Extração de palavras da pergunta, ordenação dos documentos e recuperação de parágrafos. |

A busca considera palavras completas. `mat` não encontra `material` por correspondência parcial.

Sinônimos e flexões não são reconhecidos automaticamente: `material`, `materiais` e `suprimentos` são termos diferentes.

## Integração com Gemini

O módulo `consulta_ia.py` prepara os trechos e realiza a chamada à API.

A interface e o programa pelo terminal reutilizam as mesmas funções de preparação do contexto e geração da resposta.

| Limite da aplicação | Configuração |
| --- | --- |
| Pergunta | Até 500 caracteres. |
| Documentos enviados | Até três documentos candidatos. |
| Contexto preparado | Até 12.000 caracteres, incluindo identificação das fontes. |
| Contexto acima do limite | A operação é interrompida, sem cortar o texto silenciosamente. |

Esses valores são escolhas do projeto, não limites gerais da Gemini API.

As instruções solicitam que o modelo utilize somente os trechos fornecidos, cite os arquivos e reconheça informações ausentes.

A aplicação ainda não verifica automaticamente se cada afirmação está apoiada na fonte citada. Uma referência como `[arquivo.txt]` não comprova a correção da resposta.

## Tecnologias

| Tecnologia | Uso |
| --- | --- |
| Python | Leitura de arquivos, normalização, busca e integração. |
| Streamlit | Interface no navegador. |
| Gemini API e google-genai | Geração de respostas com IA. |
| python-dotenv | Leitura das configurações locais. |
| httpx | Tratamento de falhas de conexão na integração. |
| unittest e unittest.mock | Testes e simulação das chamadas ao Gemini. |
| Git e GitHub | Controle de versões e publicação. |
| GitHub Actions | Execução automática dos testes. |

## Estrutura

```text
assistente-procedimentos-python/
│
├── .github/
│   └── workflows/
│       └── testes.yml
│
├── documentos/
│   └── arquivos TXT fictícios
│
├── .gitignore
├── README.md
├── requirements.txt
├── app.py
├── busca.py
├── consulta_ia.py
├── interface.py
├── test_app.py
├── test_busca.py
└── test_consulta_ia.py
```

O arquivo `.env` e a pasta `venv` são locais e não devem ser publicados.

## Instalação no Windows

### 1. Obter o projeto

Com o Git instalado:

```powershell
git clone https://github.com/limaavls/assistente-procedimentos-python.git
cd assistente-procedimentos-python
```

Se já houver uma cópia no computador, abra a pasta existente no Cursor.

Execute os próximos comandos no terminal da pasta principal.

### 2. Criar o ambiente virtual

É necessário ter Python instalado. A automação do projeto utiliza Python 3.13.

Crie o ambiente apenas se ele ainda não existir:

```powershell
python -m venv venv
```

Os comandos deste README chamam diretamente o Python do ambiente, sem exigir ativação separada.

Caso a pasta do seu ambiente se chame `.venv`, utilize esse nome nos caminhos.

### 3. Instalar as dependências

O `requirements.txt` contém:

```text
streamlit
google-genai
python-dotenv
httpx
```

Instale:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

A instalação pode precisar de internet para baixar as bibliotecas. Ela não realiza uma consulta ao Gemini.

## Executar a interface

```powershell
.\venv\Scripts\python.exe -m streamlit run interface.py --server.address=127.0.0.1 --browser.gatherUsageStats=false
```

Abra no navegador o endereço informado no terminal.

Exemplos de pesquisa:

```text
Como solicitar material?
Como solicitar ajuste do ponto?
Como abrir um chamado de suporte para impressora?
RH
digitalizacao
```

Os resultados dependem dos documentos disponíveis.

A busca local pode ser utilizada sem configurar uma chave do Gemini. A chave é necessária apenas para gerar respostas com IA.

O comando limita o servidor ao endereço local do computador e desativa o envio de estatísticas de uso do Streamlit. Não publica a aplicação na internet.

Para encerrar, pressione `Ctrl + C` no terminal.

## Configurar o Gemini

### Chave de acesso

Crie uma chave no [Google AI Studio](https://aistudio.google.com/) e confira o plano do projeto utilizado.

Na pasta principal, crie um arquivo `.env`:

```dotenv
GEMINI_API_KEY=COLE_SUA_CHAVE_AQUI
GEMINI_MODEL=gemini-3.5-flash-lite
```

Substitua o exemplo pela chave real somente no arquivo local.

O nome do modelo pode ser configurado por `GEMINI_MODEL`. Confira sua disponibilidade e as condições de uso na conta utilizada.

### Proteger o arquivo

O `.gitignore` deve incluir:

```gitignore
.env
venv/
.venv/
__pycache__/
```

Confira a regra:

```powershell
git check-ignore -v .env
```

Confira também se o arquivo já está sendo acompanhado pelo Git:

```powershell
git ls-files -- .env
```

O segundo comando não deve listar o arquivo.

Adicionar uma regra ao `.gitignore` não remove automaticamente um arquivo já registrado. Se uma chave for exposta, revogue-a e crie outra.

## Consultas pelo terminal

### Busca literal, sem IA

```powershell
.\venv\Scripts\python.exe app.py
```

Digite uma palavra ou expressão. Para outra pesquisa, execute novamente.

### Consulta com IA

```powershell
.\venv\Scripts\python.exe consulta_ia.py
```

Informe a pergunta e confira os trechos selecionados. Digite `SIM` somente quando desejar autorizar o envio ao Google.

Outra resposta cancela a operação.

## Documentos fictícios

Os exemplos preparados para a demonstração incluem:

| Arquivo | Tema |
| --- | --- |
| `solicitacao_material.txt` | Solicitação de materiais. |
| `teste_busca.txt` | Acentos, siglas e ocorrências próximas. |
| `ajuste_registro_ponto.txt` | Correção do ponto e encaminhamento ao RH. |
| `suporte_tecnico_ti.txt` | Abertura e acompanhamento de chamados. |
| `protocolo_documentos.txt` | Conferência e encaminhamento de documentos. |

Cada arquivo precisa estar diretamente na pasta `documentos` para participar das pesquisas.

Para ampliar a base, adicione outro TXT em UTF-8 e realize uma nova pesquisa. Não é necessário cadastrar o nome do arquivo no código.

A leitura não percorre subpastas e não abre ZIP, PDF, DOCX ou imagens. Arquivos vazios são ignorados, e falhas de leitura são informadas no terminal.

Os procedimentos, prazos e situações dos exemplos são fictícios.

## Testes automatizados

Execute todos os testes:

```powershell
.\venv\Scripts\python.exe -m unittest discover -v
```

### Suíte desta versão

| Arquivo | Testes | O que verifica |
| --- | --- | --- |
| `test_app.py` | 7 | Normalização, busca literal e união de trechos. |
| `test_busca.py` | 6 | Extração de palavras, ordenação e recuperação de parágrafos. |
| `test_consulta_ia.py` | 12 | Preparação do contexto e comportamento da integração com respostas simuladas. |
| Total | 25 | Busca e funções da integração. |

Mantendo esses arquivos, uma execução bem-sucedida deve terminar com:

```text
Ran 25 tests in ...

OK
```

Esse é o resultado esperado. Consulte a execução local ou a aba Actions para verificar o resultado real de uma versão.

### Testes da integração com IA

Para executar somente os testes novos:

```powershell
.\venv\Scripts\python.exe -m unittest -v test_consulta_ia
```

Esses testes verificam:

- Identificação das fontes e seleção dos trechos.
- Limites de quantidade de documentos e tamanho do contexto.
- Rejeição de pergunta ou contexto vazio.
- Preparação da pergunta, dos trechos e das instruções.
- Processamento de uma resposta simulada válida.
- Rejeição de resposta vazia, sem candidatos ou interrompida.
- Propagação de erros simulados de conexão e de cota.

O cliente do Gemini é substituído durante os testes por um objeto simulado.

Não é utilizada uma chave real, não há consulta ao Gemini e não é consumida cota da API por esses testes.

As bibliotecas precisam estar instaladas para importar os módulos, mesmo sem uma chamada real.

### O que os testes ainda não comprovam

A suíte não avalia a veracidade das respostas da IA, a qualidade das citações ou a conexão real com o serviço.

Também não verifica automaticamente os botões e avisos da interface, o fluxo completo de autorização ou a leitura real dos arquivos.

Nos testes de falha da API, é verificado se a função repassa o erro. Não é validada a mensagem apresentada ao usuário na tela.

## GitHub Actions

O workflow está em:

```text
.github/workflows/testes.yml
```

A cada push, a automação prepara Python 3.13, instala as dependências de `requirements.txt` e executa:

```text
python -m unittest discover -v
```

Também é possível iniciar a execução manualmente pela aba `Actions`.

Não é necessário cadastrar a chave do Gemini no GitHub para essa suíte.

Uma execução verde indica que os testes configurados passaram. Não significa que toda a aplicação esteja livre de erros ou que todas as respostas da IA sejam corretas.

## Avaliação manual da aplicação

Além dos testes automáticos, a demonstração precisa de conferência manual.

| Cenário | O que verificar |
| --- | --- |
| Pergunta respondida pelo documento | A resposta deve utilizar somente informações presentes nos trechos. |
| Informação ausente | A IA deve reconhecer a ausência, sem inventar valores, prazos ou regras. |
| Pedido para ignorar as fontes | A IA não deve abandonar as instruções de consulta aos documentos. |
| Pesquisa sem correspondência | A aplicação deve informar a ausência de documentos candidatos. |
| Falta de autorização | A interface não deve enviar a consulta. |
| Nova pesquisa | A resposta e a autorização anteriores devem ser limpas. |

Exemplo de informação ausente:

```text
Qual é o valor da taxa de segunda via do protocolo?
```

No documento fictício preparado para essa situação, o valor não está definido. A resposta desejada é reconhecer essa ausência.

Esses são critérios de avaliação, não resultados garantidos. Ainda não há uma medição sistemática da qualidade das respostas.

## Privacidade e custos

A pesquisa textual é local. Ao gerar uma resposta com Gemini, a pergunta e os trechos selecionados são enviados ao Google.

Utilize somente dados fictícios nesta demonstração. Não envie documentos internos reais, informações pessoais, senhas ou registros administrativos reais.

Nos serviços gratuitos, os termos do provedor permitem o uso de entradas e respostas para melhoria dos produtos e podem incluir revisão humana. Confira as condições aplicáveis à conta e à região utilizadas.

A disponibilidade gratuita depende do modelo, do plano e das cotas do projeto. O código não verifica o faturamento e não garante ausência de cobrança.

Referências oficiais:

- [Preços e modalidades](https://ai.google.dev/gemini-api/docs/pricing)
- [Limites de uso](https://ai.google.dev/gemini-api/docs/rate-limits)
- [Termos da Gemini API](https://ai.google.dev/gemini-api/terms)

Antes de um uso institucional, será necessário avaliar autorização, privacidade e controle de acesso.

## Limitações

A recuperação dos documentos é baseada em palavras. Ela não utiliza busca semântica, banco vetorial ou reconhecimento automático de sinônimos.

A IA recebe apenas os trechos selecionados. Informações importantes podem ficar de fora, e as respostas podem conter erros ou citações inadequadas.

Encontrar palavras em comum não comprova que o documento responda à pergunta. Não encontrar um termo também não comprova que uma regra não exista.

A aplicação não possui autenticação, histórico permanente de consultas, atualização automática por fontes externas ou controle de versões dos procedimentos.

O projeto ainda não apresenta resultados medidos de economia de tempo ou precisão em uma rotina administrativa real.

## Próximas melhorias

- Automatizar testes da interface e do fluxo de autorização.
- Acrescentar testes de leitura de arquivos.
- Registrar casos de avaliação das respostas reais da IA.
- Melhorar a seleção de documentos e a conferência das citações.
- Automatizar a atualização da base a partir de fontes aprovadas.
- Avaliar autenticação antes de disponibilizar a ferramenta a outras pessoas.

## Autor

Desenvolvido por Victor Lima Silva como projeto de aprendizado em Python e aplicação de tecnologia à rotina administrativa.

[Perfil no GitHub](https://github.com/limaavls)