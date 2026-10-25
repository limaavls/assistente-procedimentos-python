# Assistente de Procedimentos Administrativos

Aplicação em Python para pesquisar procedimentos administrativos, consultar fontes e gerar respostas opcionais com a Gemini API.

O projeto possui consulta individual, conversa com contexto limitado, importação local de documentos e busca semântica executada no computador.

A integração com Google Drive está em desenvolvimento. Nesta etapa, é possível verificar o acesso a uma pasta compartilhada com a aplicação e listar seus itens, sem baixar ou alterar documentos.

> Projeto de estudo e portfólio. Utilize somente documentos fictícios. A aplicação não representa procedimentos oficiais de uma instituição.

## Objetivo

Aplicar programação a uma necessidade da rotina administrativa: localizar informações em documentos e conferir a origem das orientações apresentadas.

O desenvolvimento envolve processamento de arquivos, pesquisa textual e semântica, interface web, integração com APIs, testes automatizados e controle de versões.

A aplicação não aprova solicitações nem substitui a conferência dos procedimentos oficiais.

## Funcionalidades

| Recurso | Funcionamento |
| --- | --- |
| Consulta individual | Pesquisa e visualização de trechos e documentos completos. |
| Conversa | Perguntas complementares com memória limitada do assunto. |
| Importação local | Seleção de TXT, PDF ou DOCX pelo painel lateral do chat. |
| Prévia de importação | Conferência do texto extraído antes da inclusão na base. |
| Busca por palavras | Normalização de acentos e maiúsculas e ordenação por correspondências. |
| Busca semântica | Comparação local de representações numéricas da pergunta e dos trechos. |
| Escolha do modo de busca | Disponível no chat. |
| Respostas com Gemini | Geração opcional, após revisão e autorização. |
| Google Drive | Verificação de acesso e listagem de itens de uma pasta. |
| Testes automatizados | Verificações da lógica com dados e respostas simuladas. |
| GitHub Actions | Instalação das dependências básicas e execução dos testes. |

A sincronização automática com Google Drive ainda não está implementada.

As respostas e as fontes citadas pela IA precisam ser conferidas nos documentos originais.

## Interfaces

### Consulta individual — interface.py

Permite pesquisar uma pergunta, visualizar os parágrafos encontrados, consultar o conteúdo integral disponível e solicitar uma resposta com IA.

Essa interface mantém a busca por palavras.

### Conversa e importação — chat.py

Permite adicionar documentos, escolher o modo de busca e fazer perguntas complementares.

```text
Escolher o modo de busca
        ↓
Digitar uma pergunta
        ↓
Conferir os trechos candidatos
        ↓
Autorizar o envio ao Google
        ↓
Gerar e revisar a resposta
```

O seletor oferece:

- Por palavras.
- Por significado (local).

A escolha fica bloqueada durante uma conversa ou pergunta pendente. Utilize `Nova conversa` para mudar de modo ou de assunto.

Pesquisar e importar documentos não chamam o Gemini. A geração da resposta exige uma ação separada.

## Conversa com contexto

A preparação considera a pergunta atual, a primeira pergunta da conversa e a pergunta respondida mais recente.

As perguntas anteriores ajudam a identificar o assunto. As respostas anteriores da IA são exibidas, mas não são reenviadas como fontes.

Essa memória não representa uma compreensão completa do histórico. Referências como “explique o segundo item da sua resposta” podem não funcionar adequadamente.

O histórico fica na sessão do navegador, sem banco de dados. A versão atual permite até 10 respostas por conversa.

A inclusão de um documento reinicia a conversa e descarta a pergunta pendente.

## Modos de busca

### Busca por palavras

Implementada em `busca.py`.

A pergunta é separada em palavras, alguns termos comuns são ignorados e os documentos são ordenados pela quantidade de palavras distintas em comum.

A comparação desconsidera acentos e maiúsculas, mas não reconhece automaticamente sinônimos ou flexões.

### Busca semântica local

Implementada em `busca_semantica.py`.

Utiliza Sentence Transformers e o modelo `intfloat/multilingual-e5-small` para transformar textos em representações numéricas chamadas embeddings.

A pergunta é comparada com trechos dos documentos. Os candidatos mais semelhantes são apresentados para revisão.

Essa etapa localiza conteúdo. A resposta escrita continua sendo gerada separadamente pelo Gemini.

| Configuração | Comportamento |
| --- | --- |
| Execução | No processador do computador. |
| Recortes | Até 300 tokens, com sobreposição de 50. |
| Base desta demonstração | Até 500 trechos. |
| Seleção | Até três documentos e dois trechos por documento. |
| Entradas longas demais | Recusadas, sem truncamento silencioso. |
| Atualização do índice | Na próxima busca, quando nomes ou conteúdos da base mudam. |

Os recortes preservam o texto original, mas podem dividir uma orientação. Confira a fonte completa.

Não existe um limiar de relevância validado. Uma pergunta sem relação com os documentos também pode receber candidatos.

A semelhança calculada não representa probabilidade de acerto.

### Armazenamento do modelo

Os arquivos do modelo são baixados para `.cache_modelos`.

As consultas utilizam a cópia local. Os embeddings dos documentos são mantidos na memória do processo, sem banco vetorial persistente.

Reiniciar a aplicação exige reconstruir o índice, mas não baixar novamente um modelo já preparado.

## Importação local

Disponível no painel lateral do chat.

```text
Selecionar o arquivo
        ↓
Extrair e revisar o texto
        ↓
Confirmar a inclusão
        ↓
Salvar uma cópia TXT local
        ↓
Pesquisar
```

A importação não consulta o Gemini.

| Item | Regra |
| --- | --- |
| TXT | UTF-8, com ou sem BOM. |
| PDF | Texto extraível, sem OCR. |
| DOCX | Parágrafos e tabelas principais. |
| DOC antigo | Não aceito. |
| Tamanho para processamento | Até 5 MiB por arquivo. |
| PDF | Até 30 páginas. |
| Texto extraído | Até 100.000 caracteres. |
| PDF protegido | Recusado. |
| Página sem texto extraível | O PDF inteiro é recusado, inclusive se houver página em branco. |
| DOCX expandido | Limite interno de 20 MiB. |

O limite de processamento é verificado depois da seleção e não substitui a configuração do servidor Streamlit.

A extração não preserva todos os elementos visuais ou especiais. Utilize documentos pequenos e de sua confiança e compare a prévia com o original.

### Cópias importadas

São gravadas em:

```text
documentos/importado_nome_identificador.txt
```

O original não é alterado nem armazenado integralmente pelo projeto.

Reenviar o mesmo nome com o mesmo texto extraído não duplica a cópia. Um conteúdo diferente gera outro arquivo sem apagar a versão anterior.

Versões antigas e novas podem coexistir e participar da pesquisa. Ainda não há seleção automática do procedimento vigente.

A visualização do documento importado apresenta a cópia textual, não a aparência original do PDF ou Word.

Para excluir uma importação, remova sua cópia TXT e inicie uma nova conversa ou pesquisa.

## Google Drive — etapa de conexão

O arquivo `verificar_drive.py` confirma acesso a uma pasta e lista os itens diretamente dentro dela.

### Implementado nesta etapa

- Autenticação por conta de serviço.
- Uso do escopo `drive.readonly`.
- Consulta de uma pasta indicada no `.env`.
- Verificação de pasta ativa.
- Listagem com paginação.
- Exclusão dos itens da lixeira.
- Interrupção se a API informar listagem incompleta.
- Limite de 200 itens para a demonstração.

O programa consulta somente metadados, como nome e tipo do arquivo.

### Ainda não implementado

- Download ou exportação do conteúdo.
- Conversão automática dos arquivos do Drive para a base local.
- Detecção e aplicação de alterações.
- Atualização periódica.
- Tratamento de versões substituídas ou removidas.
- Painel de sincronização na interface.

A listagem não entra em subpastas e não segue atalhos.

Confirmar acesso aos metadados não comprova que todos os arquivos possam ser baixados.

## Integração com Gemini

O módulo `consulta_ia.py` prepara os trechos e realiza a chamada à API.

| Limite da aplicação | Configuração |
| --- | --- |
| Pergunta digitada | Até 500 caracteres. |
| Documentos enviados | Até três candidatos. |
| Contexto dos documentos | Até 12.000 caracteres, incluindo as fontes. |

No chat, o pedido inclui também as perguntas anteriores selecionadas.

Os limites de importação, busca e envio à IA são diferentes. Um documento aceito na importação pode produzir contexto grande demais para uma consulta.

As instruções pedem que o modelo utilize os trechos, cite as fontes e reconheça informações ausentes. Não existe validação automática de todas as afirmações e referências.

## Estrutura

```text
assistente-procedimentos-python/
├── .github/
│   └── workflows/
│       └── testes.yml
├── documentos/
│   ├── documentos fictícios publicados
│   └── importado_*.txt
├── .secrets/                       # Somente local
│   └── google-drive.json
├── .gitignore
├── README.md
├── requirements.txt
├── requirements-semantica.txt
├── requirements-drive.txt
├── app.py
├── busca.py
├── busca_semantica.py
├── consulta_ia.py
├── conversa.py
├── importacao.py
├── painel_documentos.py
├── interface.py
├── chat.py
├── verificar_drive.py
├── test_app.py
├── test_busca.py
├── test_busca_semantica.py
├── test_consulta_ia.py
├── test_interface.py
├── test_conversa.py
├── test_importacao.py
└── test_verificar_drive.py
```

O `.env`, as credenciais, o ambiente virtual, o cache do modelo e as cópias importadas não devem ser publicados.

## Instalação no Windows

### 1. Obter o projeto

```powershell
git clone https://github.com/limaavls/assistente-procedimentos-python.git
cd assistente-procedimentos-python
```

Se já houver uma cópia, abra a pasta existente.

### 2. Criar o ambiente virtual

Com Python instalado, execute apenas se o ambiente ainda não existir:

```powershell
python -m venv venv
```

O workflow de testes utiliza Python 3.13.

Se seu ambiente se chama `.venv`, utilize esse nome nos comandos.

### 3. Dependências básicas

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

### 4. Busca semântica opcional

O `requirements-semantica.txt` contém:

```text
-r requirements.txt
sentence-transformers
```

Instale:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements-semantica.txt
```

Prepare o modelo com internet disponível:

```powershell
.\venv\Scripts\python.exe busca_semantica.py
```

Esse comando baixa os arquivos do modelo. Não consulta o Gemini nem envia a base de procedimentos.

### 5. Google Drive opcional

O `requirements-drive.txt` contém:

```text
-r requirements.txt
google-api-python-client
google-auth
google-auth-httplib2
```

Instale:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements-drive.txt
```

A instalação não concede acesso ao Drive. A configuração da conta de serviço e o compartilhamento da pasta são necessários.

## Executar o chat

```powershell
.\venv\Scripts\python.exe -m streamlit run chat.py --server.address=127.0.0.1 --browser.gatherUsageStats=false
```

Escolha o modo na lateral. Para trocar após uma consulta, utilize `Nova conversa`.

O painel de importação continua disponível.

## Executar a consulta individual

```powershell
.\venv\Scripts\python.exe -m streamlit run interface.py --server.address=127.0.0.1 --browser.gatherUsageStats=false
```

Essa interface mantém a busca por palavras.

Os comandos iniciam a aplicação localmente e desativam o envio de estatísticas de uso do Streamlit. Não publicam a ferramenta na internet.

Para encerrar, pressione `Ctrl + C`.

## Configuração do Gemini

A importação e as buscas locais não exigem chave do Gemini.

Para gerar respostas, configure no `.env`:

```dotenv
GEMINI_API_KEY=COLE_SUA_CHAVE_AQUI
```

O modelo pode ser definido por `GEMINI_MODEL`. Na ausência dessa variável, utiliza-se `MODELO_PADRAO` de `consulta_ia.py`.

Preserve a configuração já validada no seu ambiente.

O modelo gerador é independente do modelo local de busca semântica. Confira disponibilidade, cotas e condições do provedor antes de utilizar a API.

## Configuração do Google Drive

Esta credencial é separada da chave do Gemini.

### Preparação

1. Crie uma pasta exclusiva com documentos fictícios.
2. Ative a Google Drive API em um projeto Google Cloud.
3. Crie uma conta de serviço dedicada.
4. Compartilhe somente a pasta de demonstração com essa conta como Leitor/Visualizador.
5. Guarde a credencial JSON localmente em `.secrets/google-drive.json`.

Não conceda acesso público à pasta, papéis administrativos ao programa ou delegação ampla sobre contas de uma organização.

Caso políticas institucionais bloqueiem a configuração, solicite orientação ao administrador. Não altere controles de segurança para contornar o bloqueio.

### Variáveis locais

Acrescente ao `.env`, preservando a configuração do Gemini:

```dotenv
DRIVE_FOLDER_ID=COLE_AQUI_SOMENTE_O_ID_DA_PASTA
DRIVE_CREDENTIALS_FILE=.secrets/google-drive.json
```

O ID é a parte do endereço após `/folders/`. Não utilize o link completo.

### Verificação real de acesso

```powershell
.\venv\Scripts\python.exe verificar_drive.py
```

O resultado esperado inclui o nome da pasta e os itens encontrados.

Essa execução acessa a API do Drive, mas não baixa o conteúdo dos documentos, não os modifica e não envia dados ao Gemini.

Ela não inicia uma sincronização automática.

## Proteção no Git

Mantenha estas regras no `.gitignore`:

```gitignore
.env
venv/
.venv/
__pycache__/
documentos/importado_*.txt
.cache_modelos/
.secrets/
```

Confira as credenciais:

```powershell
git check-ignore -v .env .secrets/google-drive.json
git ls-files -- .env .secrets/
```

O segundo comando não deve listar arquivos.

Uma regra no `.gitignore` não retira arquivos já registrados. Se uma credencial for exposta, revogue-a no provedor e gere outra.

Não publique chaves, arquivos internos reais ou dados pessoais.

## Uso pelo terminal

Busca literal:

```powershell
.\venv\Scripts\python.exe app.py
```

Consulta individual com IA:

```powershell
.\venv\Scripts\python.exe consulta_ia.py
```

Essas entradas mantêm a busca anterior por palavras. O seletor semântico está no chat.

## Testes automatizados

Execute toda a suíte:

```powershell
.\venv\Scripts\python.exe -m unittest discover -v
```

| Arquivo | Quantidade | Finalidade |
| --- | --- | --- |
| `test_app.py` | 7 | Normalização e busca literal. |
| `test_busca.py` | 6 | Extração de palavras e ordenação. |
| `test_consulta_ia.py` | 12 | Integração com respostas simuladas. |
| `test_interface.py` | 10 | Interações simuladas da consulta individual. |
| `test_conversa.py` | 6 | Preparação do contexto da conversa. |
| `test_importacao.py` | 9 | Extração, validações e armazenamento. |
| `test_busca_semantica.py` | 10 | Recortes, vetores simulados, cache e limites. |
| `test_verificar_drive.py` | 6 | Listagem simulada, validações e paginação. |
| Total | 66 | Verificações definidas nesta etapa. |

Mantendo os arquivos desta versão, uma execução bem-sucedida deve terminar com:

```text
Ran 66 tests in ...

OK
```

Esse é o resultado esperado. Confira a execução local ou o GitHub Actions para verificar o resultado real.

### Testes específicos

Busca semântica simulada:

```powershell
.\venv\Scripts\python.exe -m unittest -v test_busca_semantica
```

Listagem simulada do Drive:

```powershell
.\venv\Scripts\python.exe -m unittest -v test_verificar_drive
```

Os testes do Drive não utilizam credenciais, não leem o `.env` e não acessam uma conta real.

Eles verificam validação do ID, pasta ativa, ordenação, paginação, recusa de listagem incompleta e limite de itens.

Os testes semânticos não baixam nem executam o modelo real.

### Limitações da cobertura

A suíte não comprova a qualidade das respostas reais do Gemini, a qualidade da busca semântica ou a autenticação real no Drive.

Os testes de interface cobrem `interface.py`, não todos os controles do chat ou do painel de importação.

As verificações de listagem não testam download ou sincronização, pois essas funcionalidades ainda não estão implementadas.

## GitHub Actions

O workflow instala as dependências básicas e executa:

```text
python -m unittest discover -v
```

Os testes atuais não precisam de chave do Gemini, credencial do Google Drive, download do modelo ou instalação das dependências opcionais.

Uma execução verde indica que os cenários programados passaram. Não garante ausência de erros em toda a aplicação.

## Avaliação manual

Compare a mesma pergunta nos dois modos de busca, iniciando uma nova conversa antes de trocar.

Confira se os documentos encontrados são pertinentes e se os trechos contêm informação suficiente.

Teste também perguntas fora do domínio. A busca semântica pode retornar candidatos mesmo quando nenhum documento responde à questão.

Para a integração com Drive, confirme inicialmente a listagem de arquivos fictícios conhecidos. Não considere a sincronização concluída apenas porque o acesso foi confirmado.

## Privacidade e segurança

Na execução local, importação e busca ocorrem no computador que executa o aplicativo.

A busca semântica calcula os embeddings localmente. A preparação inicial baixa os arquivos do modelo.

Ao autorizar uma resposta com Gemini, a pergunta, os trechos e as perguntas anteriores selecionadas são enviados ao Google.

A verificação do Drive consulta metadados de uma pasta compartilhada com a conta de serviço. Não envia esses resultados ao Gemini.

As credenciais locais exigem proteção. O `.gitignore` não criptografa arquivos nem restringe o acesso de outras pessoas ao computador.

Não existe autenticação na aplicação nem separação da base por usuário. Antes de qualquer uso institucional, será necessário avaliar autorização, tratamento de dados e controle de acesso.

## Limitações atuais

A busca semântica é experimental e não possui um limiar de relevância validado.

Os recortes podem omitir condições ou exceções próximas. A extração de PDF e DOCX não preserva todos os elementos e não utiliza OCR.

Versões antigas e novas de arquivos importados podem coexistir na base.

A memória da conversa é limitada e não representa uma compreensão completa do histórico.

As respostas do Gemini podem conter erros ou citações inadequadas.

A conexão com Drive ainda não atualiza a base local. Não existe sincronização, monitoramento periódico ou controle automático da versão vigente dos documentos.

O projeto não apresenta resultados medidos de economia de tempo ou precisão em uma rotina administrativa real.

## Ciclo de melhorias

| Ordem | Melhoria | Situação |
| --- | --- | --- |
| 1 | Conversa com contexto | Versão inicial implementada. |
| 2 | Importação de TXT, PDF e DOCX | Versão inicial implementada. |
| 3 | Busca por significado | Alternativa local implementada; qualidade a avaliar com a base. |
| 4 | Atualização por pasta aprovada no Google Drive | Em desenvolvimento: conexão e listagem; sincronização ainda pendente. |

## Referências

- [Sentence Transformers](https://www.sbert.net/)
- [Modelo multilingual-e5-small](https://huggingface.co/intfloat/multilingual-e5-small)
- [Streamlit](https://docs.streamlit.io/)
- [Credenciais Google Workspace](https://developers.google.com/workspace/guides/create-credentials)
- [Listagem de arquivos do Drive](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/list)
- [Cuidados com chaves de contas de serviço](https://docs.cloud.google.com/iam/docs/best-practices-for-managing-service-account-keys)

## Autor

Desenvolvido por Victor Lima Silva como projeto de aprendizado em Python e aplicação de tecnologia à rotina administrativa.

[Perfil no GitHub](https://github.com/limaavls)