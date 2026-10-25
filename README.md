# Assistente de Procedimentos Administrativos

Aplicação em Python para pesquisar procedimentos administrativos, consultar fontes e gerar respostas opcionais com a Gemini API.

O projeto possui uma interface de consulta individual, um modo de conversa com memória simples do assunto e importação local de documentos TXT, PDF e DOCX pelo navegador.

> Projeto de estudo e portfólio. Utilize somente documentos fictícios. A aplicação não representa procedimentos oficiais de uma instituição.

## Objetivo

Aplicar programação a uma necessidade da rotina administrativa: localizar informações em documentos e conferir a origem das orientações apresentadas.

O desenvolvimento envolve leitura de arquivos, pesquisa textual, interface web, integração com IA, testes e controle de versões.

A aplicação não aprova solicitações nem substitui a conferência dos procedimentos oficiais.

## Funcionalidades

| Recurso | Funcionamento |
| --- | --- |
| Consulta individual | Pesquisa pelo navegador, com apresentação de trechos e documentos completos. |
| Conversa | Perguntas complementares com memória limitada do assunto. |
| Importação de documentos | Seleção de TXT, PDF ou DOCX pelo painel lateral do chat. |
| Prévia da importação | Exibição do texto extraído antes de incluí-lo na base. |
| Busca textual | Normalização de acentos e maiúsculas e ordenação por palavras em comum. |
| Respostas com Gemini | Geração opcional após autorização de envio. |
| Testes automatizados | Verificações da busca, integração, interface individual, conversa e importação. |
| GitHub Actions | Instalação das dependências e execução dos testes a cada push. |

As respostas com IA são experimentais. Afirmações e citações precisam ser conferidas nos documentos originais.

## Interfaces

### Consulta individual — interface.py

Permite pesquisar uma pergunta, visualizar os parágrafos encontrados, consultar o conteúdo disponível de cada fonte e solicitar uma resposta com IA.

Pesquisar não consulta a API. O envio exige autorização e clique no botão de geração.

### Conversa e importação — chat.py

Permite continuar um assunto com perguntas complementares e adicionar documentos pelo painel lateral.

A memória utiliza a primeira pergunta e a pergunta respondida mais recente. As respostas anteriores da IA são exibidas, mas não são reenviadas como fontes.

Use `Nova conversa` para mudar de assunto.

O histórico fica na sessão do navegador, sem banco de dados. A versão atual permite até 10 respostas por conversa.

A inclusão de um documento reinicia a conversa e descarta a pergunta pendente, evitando continuar com trechos preparados antes da mudança na base.

## Importação de documentos

```text
Selecionar um arquivo
        ↓
Extrair e revisar o texto
        ↓
Confirmar a inclusão
        ↓
Salvar uma cópia TXT na base local
        ↓
Pesquisar o conteúdo
```

A importação não chama o Gemini nem exige uma chave de API. O envio de trechos à IA continua sendo uma ação separada.

O painel de importação está disponível em `chat.py`. Os arquivos incluídos também podem ser consultados por `interface.py`, pois ambas as telas utilizam a mesma pasta.

### Formatos e limites

| Item | Comportamento desta versão |
| --- | --- |
| TXT | Leitura em UTF-8, com ou sem BOM. |
| PDF | Extração de texto, sem reconhecimento de imagens. |
| DOCX | Leitura de parágrafos e tabelas principais na ordem do documento. |
| DOC antigo | Não aceito. |
| Tamanho do arquivo | Até 5 MiB para processamento. |
| PDF | Até 30 páginas. |
| Texto extraído | Até 100.000 caracteres. |
| PDF protegido | Recusado. |
| Página de PDF sem texto extraível | O arquivo inteiro é recusado, inclusive se houver uma página em branco. |
| DOCX expandido | Recusado quando ultrapassa o limite interno de 20 MiB. |

O limite de 5 MiB é verificado pela aplicação após a seleção do arquivo; não substitui a configuração de tamanho máximo do servidor Streamlit.

Não existe OCR nesta versão. PDFs digitalizados apenas como imagem não são convertidos.

A extração de DOCX não garante a inclusão de cabeçalhos, rodapés, caixas de texto, imagens, numeração automática ou outros elementos especiais.

A extração de PDF pode alterar a organização de colunas e tabelas. Confira a prévia com o original antes de confirmar.

Essas verificações não tornam a aplicação adequada para receber arquivos arbitrários de terceiros. Use arquivos pequenos e de sua confiança.

### Armazenamento e fontes

A confirmação salva apenas o texto extraído:

```text
documentos/importado_nome_identificador.txt
```

A cópia inclui o nome do arquivo de origem. No PDF, o texto também recebe marcadores de página.

O original não é alterado e não é guardado integralmente pelo projeto.

Para documentos importados, a visualização de “documento completo” mostra a cópia textual extraída, não uma reprodução visual do PDF ou do Word. Preserve o original para conferência.

Reenviar o mesmo nome com o mesmo texto extraído não cria outra cópia. Se o conteúdo mudar, uma nova cópia é criada sem apagar a anterior.

Não existe substituição automática de versões: documentos antigos e novos podem continuar participando da busca.

As cópias persistem no disco depois de fechar a aplicação. Elas não são isoladas por sessão ou por usuário.

### Excluir uma importação

Exclua manualmente o arquivo correspondente a `importado_*.txt` na pasta `documentos`.

Depois, inicie uma nova conversa ou faça outra pesquisa para evitar utilizar resultados preparados anteriormente.

A exclusão local não apaga informações que já tenham sido enviadas à API.

## Como funciona a busca

A base consultada continua sendo formada por TXT em UTF-8 diretamente na pasta `documentos`.

Os arquivos PDF e DOCX passam pela importação antes de participar dessa busca.

| Módulo | Responsabilidade |
| --- | --- |
| `app.py` | Leitura dos TXT, normalização e busca literal pelo terminal. |
| `busca.py` | Extração de palavras da pergunta, ordenação e recuperação de parágrafos. |
| `conversa.py` | Preparação da pergunta atual com referência ao assunto anterior. |

Uma pesquisa por `solicitacao` pode encontrar `solicitação`. `Mat` não encontra `material` apenas por ser parte da palavra.

Sinônimos e flexões não são reconhecidos automaticamente.

A ordenação é baseada em palavras em comum, não em uma porcentagem de confiança. Encontrar um documento não comprova que ele responda à pergunta.

## Integração com Gemini

O módulo `consulta_ia.py` prepara os trechos e solicita a geração da resposta. As duas interfaces reutilizam essas funções.

| Configuração | Limite |
| --- | --- |
| Pergunta digitada | 500 caracteres. |
| Documentos selecionados | Até três candidatos. |
| Contexto dos documentos | 12.000 caracteres, incluindo identificação das fontes. |

Uma importação pode ser aceita e, mesmo assim, produzir trechos grandes demais para uma determinada consulta. Os limites de importação e de envio à IA são diferentes.

No chat, o pedido inclui também as perguntas anteriores selecionadas para identificar o assunto.

As instruções pedem que o modelo use os documentos, cite as fontes e reconheça informações ausentes. A aplicação ainda não valida automaticamente essas afirmações e referências.

## Tecnologias

Python, Streamlit, Gemini API, google-genai, python-dotenv, httpx, pypdf, python-docx, unittest, unittest.mock, Git e GitHub Actions.

## Estrutura

```text
assistente-procedimentos-python/
├── .github/
│   └── workflows/
│       └── testes.yml
├── documentos/
│   ├── documentos fictícios publicados
│   └── importado_*.txt              # Cópias locais ignoradas pelo Git
├── .gitignore
├── README.md
├── requirements.txt
├── app.py
├── busca.py
├── consulta_ia.py
├── conversa.py
├── importacao.py
├── painel_documentos.py
├── interface.py
├── chat.py
├── test_app.py
├── test_busca.py
├── test_consulta_ia.py
├── test_interface.py
├── test_conversa.py
└── test_importacao.py
```

## Instalação no Windows

### 1. Obter o projeto

```powershell
git clone https://github.com/limaavls/assistente-procedimentos-python.git
cd assistente-procedimentos-python
```

Se já houver uma cópia, abra a pasta existente no Cursor.

### 2. Criar o ambiente virtual

Com Python instalado, execute somente se o ambiente ainda não existir:

```powershell
python -m venv venv
```

O workflow de testes utiliza Python 3.13.

Se seu ambiente se chama `.venv`, substitua `venv` por `.venv` nos comandos seguintes.

### 3. Instalar as dependências

O `requirements.txt` inclui:

```text
streamlit
google-genai
python-dotenv
httpx
pypdf>=5.9
python-docx>=1.2
```

Instale:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Executar as interfaces

### Conversa com painel de importação

```powershell
.\venv\Scripts\python.exe -m streamlit run chat.py --server.address=127.0.0.1 --browser.gatherUsageStats=false
```

No painel lateral, selecione o arquivo, extraia o texto, revise e confirme a inclusão.

Para testar, use uma pergunta que mencione um assunto do documento importado.

### Consulta individual

```powershell
.\venv\Scripts\python.exe -m streamlit run interface.py --server.address=127.0.0.1 --browser.gatherUsageStats=false
```

Abra o endereço informado no terminal. Para encerrar, pressione `Ctrl + C`.

Esses comandos iniciam a aplicação localmente e desativam o envio de estatísticas de uso do Streamlit. Não publicam a ferramenta na internet.

## Configurar a API

A importação e a busca local não precisam de chave. A geração de respostas precisa da configuração do Gemini.

Crie `.env` na pasta principal:

```dotenv
GEMINI_API_KEY=COLE_SUA_CHAVE_AQUI
```

Substitua o exemplo apenas no arquivo local.

O modelo pode ser configurado por `GEMINI_MODEL`. Quando essa variável não está definida, a aplicação utiliza `MODELO_PADRAO` de `consulta_ia.py`.

Se a integração já estiver funcionando, preserve sua configuração atual.

Confira a disponibilidade, as cotas e o plano do modelo na conta utilizada. O código não verifica faturamento nem garante ausência de cobrança.

### Proteção no Git

O `.gitignore` deve conter:

```gitignore
.env
venv/
.venv/
__pycache__/
documentos/importado_*.txt
```

Preserve as demais regras existentes.

Confira o `.env`:

```powershell
git check-ignore -v .env
git ls-files -- .env
```

O segundo comando não deve listar o arquivo.

Regras de exclusão não retiram automaticamente arquivos já registrados. Se uma chave for exposta, revogue-a e crie outra.

Não publique arquivos reais de trabalho, credenciais ou informações pessoais.

## Uso pelo terminal

Busca literal:

```powershell
.\venv\Scripts\python.exe app.py
```

Consulta individual com IA:

```powershell
.\venv\Scripts\python.exe consulta_ia.py
```

Confira os trechos antes de autorizar o envio.

## Testes automatizados

Execute:

```powershell
.\venv\Scripts\python.exe -m unittest discover -v
```

| Arquivo | Quantidade | Finalidade |
| --- | --- | --- |
| `test_app.py` | 7 | Normalização e busca literal. |
| `test_busca.py` | 6 | Extração de palavras e ordenação. |
| `test_consulta_ia.py` | 12 | Integração com respostas simuladas. |
| `test_interface.py` | 10 | Interações simuladas da consulta individual. |
| `test_conversa.py` | 6 | Preparação da conversa com contexto limitado. |
| `test_importacao.py` | 9 | Extração, validações e armazenamento da importação. |
| Total | 50 | Testes definidos nesta etapa. |

Mantendo esses arquivos, o resultado esperado é:

```text
Ran 50 tests in ...

OK
```

Consulte a execução local ou o GitHub Actions para verificar o resultado real de cada versão.

### Testar somente a importação

```powershell
.\venv\Scripts\python.exe -m unittest -v test_importacao
```

Os testes verificam preservação de acentos, leitura de DOCX, identificação de página, entradas inválidas, PDFs recusados, limites de texto, destino da gravação e comportamento das cópias repetidas ou alteradas.

Alguns cenários usam documentos gerados em memória; a leitura do conteúdo de uma página PDF também possui um caso simulado.

Os testes não utilizam arquivos particulares nem fazem chamadas reais à IA.

### Limites da cobertura

A suíte não comprova a veracidade das respostas reais do Gemini.

Os testes de interface continuam cobrindo `interface.py`, não todos os controles de `chat.py` ou do painel de upload.

Os testes da conversa verificam a preparação do pedido, não o entendimento real do modelo.

A importação ainda precisa de avaliação manual com diferentes documentos. Os testes não garantem segurança contra todo arquivo malformado ou malicioso.

## GitHub Actions

O workflow em `.github/workflows/testes.yml` instala as dependências e executa:

```text
python -m unittest discover -v
```

A execução ocorre a cada push e também pode ser iniciada manualmente pela aba Actions.

Não é necessário colocar a chave do Gemini no GitHub para executar os testes.

Uma execução verde indica que os testes configurados passaram, não que toda a aplicação esteja livre de erros.

## Privacidade

Na execução local, a extração e a busca ocorrem no computador que executa o aplicativo.

Ao autorizar uma resposta com Gemini, a pergunta, o contexto selecionado e, no chat, as perguntas anteriores escolhidas são enviados ao Google.

Nos serviços gratuitos, os termos aplicáveis podem permitir uso dos dados para melhoria dos produtos e revisão humana. Utilize somente dados fictícios.

As cópias importadas ficam em disco. O `.gitignore` evita sua inclusão normal no Git, mas não criptografa os arquivos nem restringe o acesso à aplicação.

Não existe autenticação ou separação da base por usuário.

Antes de qualquer uso institucional, será necessário avaliar autorização, tratamento dos dados e controle de acesso.

## Limitações atuais

A busca continua baseada em palavras, sem embeddings ou busca semântica.

A memória da conversa considera o assunto inicial e a pergunta respondida mais recente. Para mudar de tema, utilize `Nova conversa`.

A extração não preserva a aparência dos documentos nem garante todos os elementos de PDF e Word.

Versões importadas diferentes podem coexistir na base. Não há identificação automática de qual procedimento está vigente.

As fontes citadas pela IA não são validadas automaticamente, e trechos importantes podem não ser recuperados.

O projeto não possui sincronização com Google Drive, histórico permanente de conversas ou resultados medidos de economia de tempo em uma rotina real.

## Ciclo de melhorias

| Ordem | Melhoria | Situação desta versão |
| --- | --- | --- |
| 1 | Conversa com contexto | Versão inicial implementada. |
| 2 | Importação de TXT, PDF e Word pela interface | Versão inicial adicionada nesta etapa. |
| 3 | Busca por significado | Próxima etapa planejada. |
| 4 | Atualização automática de pasta aprovada no Google Drive | Planejada após a busca por significado. |

## Referências

- [Streamlit: seleção de arquivos](https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader)
- [pypdf: extração de texto](https://pypdf.readthedocs.io/en/stable/user/extract-text.html)
- [python-docx: documentos](https://python-docx.readthedocs.io/en/latest/api/document.html)
- [Termos da Gemini API](https://ai.google.dev/gemini-api/terms)

## Autor

Desenvolvido por Victor Lima Silva como projeto de aprendizado em Python e aplicação de tecnologia à rotina administrativa.

[Perfil no GitHub](https://github.com/limaavls)