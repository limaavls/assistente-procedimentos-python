# Assistente de Procedimentos Administrativos

Aplicação em Python para pesquisar procedimentos administrativos, consultar fontes e gerar respostas opcionais com a Gemini API.

O projeto possui interface de consulta individual, conversa com contexto limitado, importação local de documentos e uma alternativa de busca semântica executada no computador.

> Projeto de estudo e portfólio. Utilize somente documentos fictícios. A aplicação não representa orientações oficiais de uma instituição.

## Objetivo

Aplicar programação a uma necessidade da rotina administrativa: localizar informações em documentos e conferir a origem das orientações apresentadas.

O desenvolvimento envolve processamento de documentos, pesquisa textual e semântica, interface web, integração com IA, testes automatizados e controle de versões.

A aplicação não aprova solicitações nem substitui a conferência dos procedimentos oficiais.

## Funcionalidades

| Recurso | Funcionamento |
| --- | --- |
| Consulta individual | Pesquisa pelo navegador e visualização de documentos completos. |
| Conversa | Perguntas complementares com memória limitada do assunto. |
| Importação | Seleção de TXT, PDF ou DOCX pelo painel lateral do chat. |
| Prévia de importação | Conferência do texto extraído antes da inclusão na base. |
| Busca por palavras | Normalização de acentos e maiúsculas e ordenação por correspondências. |
| Busca semântica local | Comparação de representações numéricas da pergunta e dos trechos. |
| Seleção do modo de busca | Disponível no chat, antes de iniciar a conversa. |
| Respostas com Gemini | Geração opcional, após revisão e autorização de envio. |
| Testes automatizados | Verificações com dados e respostas simuladas. |
| GitHub Actions | Instalação das dependências básicas e execução dos testes. |

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

A seleção entre busca por palavras e busca semântica fica bloqueada durante uma conversa ou pergunta pendente. Utilize `Nova conversa` para trocar de modo ou de assunto.

Pesquisar e importar documentos não chamam o Gemini. A geração da resposta é uma ação separada.

## Conversa com contexto

A preparação da conversa utiliza:

- A pergunta atual.
- A primeira pergunta da conversa.
- A pergunta respondida mais recente, quando diferente da primeira.

As perguntas anteriores ajudam a identificar o assunto. As respostas anteriores da IA não são reenviadas como fontes.

Essa memória não representa uma compreensão completa de todo o histórico. Referências como “explique o segundo item da sua resposta” podem não funcionar adequadamente.

O histórico fica na sessão do navegador, sem banco de dados. A versão atual permite até 10 respostas por conversa.

A inclusão de um documento reinicia a conversa e descarta a pergunta pendente.

## Modos de busca

### Por palavras

Disponível em `busca.py`.

A pergunta é separada em palavras, alguns termos comuns são ignorados e os documentos são ordenados pela quantidade de palavras distintas em comum.

A comparação desconsidera acentos e maiúsculas. A busca não reconhece automaticamente sinônimos ou flexões.

### Por significado — local

Disponível em `busca_semantica.py` e selecionável no chat.

Utiliza o modelo `intfloat/multilingual-e5-small` por meio de Sentence Transformers. O modelo transforma textos em representações numéricas chamadas embeddings.

A pergunta é comparada com os trechos dos documentos, e os candidatos mais semelhantes são apresentados para revisão.

Essa etapa localiza conteúdo; ela não escreve a resposta. A geração continua sendo realizada separadamente pelo Gemini.

### Limites da busca semântica

| Configuração | Comportamento |
| --- | --- |
| Execução | No processador do computador, sem exigir GPU. |
| Divisão dos textos | Até 300 tokens por trecho, com sobreposição de 50 tokens. |
| Tamanho da base nesta demonstração | Até 500 trechos. |
| Documentos selecionados | Até três. |
| Trechos por documento selecionado | Até dois. |
| Entradas longas demais | Recusadas, sem truncamento silencioso. |
| Atualização | Recalcula as representações na próxima busca quando nomes ou conteúdos da base mudam. |

Tokens são unidades utilizadas pelo modelo e não correspondem necessariamente a palavras inteiras.

Os recortes preservam o conteúdo original. Podem atravessar limites de parágrafos ou dividir uma orientação; por isso, devem ser conferidos com a fonte completa.

Não existe um limiar de relevância validado nesta versão. Com uma base não vazia, uma pergunta sem relação com os procedimentos também pode receber documentos candidatos.

A semelhança calculada não representa probabilidade de acerto nem confirma que a pergunta tenha resposta na base.

## Modelo e armazenamento local

A preparação inicial baixa os arquivos do modelo para `.cache_modelos`.

As pesquisas carregam o modelo com a opção de utilizar somente arquivos locais. O código não envia documentos ou perguntas à Hugging Face para calcular os embeddings.

As representações dos documentos são mantidas na memória do processo. Não existe banco vetorial nem índice persistente em disco.

Quando a base muda, o índice é reconstruído na próxima pesquisa semântica. Reiniciar a aplicação também exige reconstruir o índice, mas não baixar novamente um modelo já preparado.

O cache do modelo permanece no disco e não deve ser enviado ao GitHub.

## Importação de documentos

```text
Selecionar um arquivo
        ↓
Extrair e revisar o texto
        ↓
Confirmar a inclusão
        ↓
Salvar uma cópia TXT local
        ↓
Pesquisar o conteúdo
```

A importação está no painel lateral de `chat.py`. Os arquivos incluídos também podem ser consultados por `interface.py`.

| Item | Regra desta versão |
| --- | --- |
| TXT | UTF-8, com ou sem BOM. |
| PDF | Texto extraível, sem OCR. |
| DOCX | Parágrafos e tabelas principais. |
| DOC antigo | Não aceito. |
| Arquivo selecionado | Até 5 MiB para processamento. |
| PDF | Até 30 páginas. |
| Texto extraído | Até 100.000 caracteres. |
| PDF protegido | Recusado. |
| Página de PDF sem texto extraível | O arquivo inteiro é recusado, inclusive se a página estiver em branco. |
| DOCX expandido | Limite interno de 20 MiB. |

O limite de 5 MiB é verificado após a seleção do arquivo e não substitui a configuração do servidor Streamlit.

A extração pode não preservar colunas, imagens, cabeçalhos, rodapés ou outros elementos especiais. Compare a prévia com o original.

Esta demonstração não é adequada para receber arquivos arbitrários de terceiros. Utilize documentos pequenos e de sua confiança.

### Cópias importadas

São gravadas como:

```text
documentos/importado_nome_identificador.txt
```

O original não é alterado nem armazenado integralmente pelo projeto.

A visualização do documento importado apresenta a cópia textual, não a aparência original do PDF ou Word.

Reenviar o mesmo nome com o mesmo texto extraído não duplica a cópia. Conteúdos alterados geram outro arquivo, sem apagar a versão anterior.

Versões antigas e novas podem coexistir e participar da busca. Não existe seleção automática de qual procedimento está vigente.

Para excluir uma importação, remova sua cópia TXT e inicie uma nova conversa ou pesquisa. O índice semântico será atualizado na próxima busca.

## Integração com Gemini

O módulo `consulta_ia.py` prepara os trechos e realiza a chamada à API. As interfaces reutilizam suas funções.

| Limite da aplicação | Configuração |
| --- | --- |
| Pergunta digitada | Até 500 caracteres. |
| Documentos enviados | Até três candidatos. |
| Contexto dos documentos | Até 12.000 caracteres, incluindo as fontes. |

Os limites da importação, da busca e do envio à IA são diferentes. Um documento aceito na importação ainda pode produzir um contexto grande demais para uma consulta.

No chat, o pedido também inclui as perguntas anteriores selecionadas para identificar o assunto.

As instruções solicitam que o modelo use os trechos, cite os arquivos e reconheça informações ausentes. Essas instruções não garantem uma resposta correta.

## Tecnologias

| Tecnologia | Aplicação |
| --- | --- |
| Python | Processamento, busca e integração. |
| Streamlit | Interfaces e testes com AppTest. |
| Sentence Transformers | Execução local do modelo de embeddings. |
| multilingual-e5-small | Representações numéricas dos textos. |
| Gemini API e google-genai | Geração de respostas. |
| pypdf e python-docx | Extração de texto de documentos. |
| python-dotenv e httpx | Configuração local e tratamento de conexão. |
| unittest e unittest.mock | Testes e simulação de dependências. |
| Git, GitHub e GitHub Actions | Versionamento e automação dos testes. |

## Estrutura

```text
assistente-procedimentos-python/
├── .github/
│   └── workflows/
│       └── testes.yml
├── documentos/
│   ├── documentos fictícios publicados
│   └── importado_*.txt
├── .gitignore
├── README.md
├── requirements.txt
├── requirements-semantica.txt
├── app.py
├── busca.py
├── busca_semantica.py
├── consulta_ia.py
├── conversa.py
├── importacao.py
├── painel_documentos.py
├── interface.py
├── chat.py
├── test_app.py
├── test_busca.py
├── test_busca_semantica.py
├── test_consulta_ia.py
├── test_interface.py
├── test_conversa.py
└── test_importacao.py
```

A pasta `.cache_modelos`, o ambiente virtual, o `.env` e as cópias importadas são locais e devem ser ignorados pelo Git.

## Instalação no Windows

### 1. Obter o projeto

```powershell
git clone https://github.com/limaavls/assistente-procedimentos-python.git
cd assistente-procedimentos-python
```

Se já houver uma cópia no computador, abra a pasta existente.

### 2. Criar o ambiente virtual

Com Python instalado, execute somente se o ambiente ainda não existir:

```powershell
python -m venv venv
```

O workflow de testes utiliza Python 3.13.

Se seu ambiente se chama `.venv`, substitua `venv` por `.venv` nos comandos.

### 3. Instalação básica

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

Essa instalação permite utilizar as funcionalidades anteriores e executar os testes simulados.

### 4. Instalação opcional da busca semântica

O arquivo `requirements-semantica.txt` contém:

```text
-r requirements.txt
sentence-transformers
```

Instale:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements-semantica.txt
```

Essa opção acrescenta bibliotecas maiores e exige espaço em disco e memória.

### 5. Preparar o modelo local

Com internet disponível:

```powershell
.\venv\Scripts\python.exe busca_semantica.py
```

Esse comando permite baixar os arquivos do modelo. Não lê a base de procedimentos nem consulta o Gemini.

Depois da preparação, as pesquisas utilizam a cópia local. Não é necessário repetir o comando para cada pergunta.

## Executar o chat

```powershell
.\venv\Scripts\python.exe -m streamlit run chat.py --server.address=127.0.0.1 --browser.gatherUsageStats=false
```

Na lateral, escolha:

- `Por palavras`, para utilizar a busca anterior.
- `Por significado (local)`, após preparar o modelo.

Utilize `Nova conversa` para alterar o modo depois de uma consulta.

O painel de importação continua disponível.

## Executar a consulta individual

```powershell
.\venv\Scripts\python.exe -m streamlit run interface.py --server.address=127.0.0.1 --browser.gatherUsageStats=false
```

Essa interface mantém a pesquisa por palavras. O seletor semântico foi acrescentado somente ao chat nesta etapa.

Os comandos iniciam a aplicação localmente e desativam o envio de estatísticas de uso do Streamlit. Não publicam o projeto na internet.

Para encerrar, pressione `Ctrl + C`.

## Configurar o Gemini

A busca por palavras, a importação e a busca semântica local não precisam de uma chave do Gemini.

Para gerar respostas, crie `.env` na pasta principal:

```dotenv
GEMINI_API_KEY=COLE_SUA_CHAVE_AQUI
```

Substitua o exemplo somente no arquivo local.

O modelo gerador pode ser configurado por `GEMINI_MODEL`. Na ausência dessa variável, a aplicação utiliza `MODELO_PADRAO` de `consulta_ia.py`.

Preserve a configuração já validada no seu ambiente. O modelo de busca local é independente do modelo de geração.

Confira disponibilidade, cotas e condições de cobrança no provedor. A aplicação não verifica o faturamento.

### Proteção no Git

O `.gitignore` deve incluir:

```gitignore
.env
venv/
.venv/
__pycache__/
documentos/importado_*.txt
.cache_modelos/
```

Preserve outras regras existentes.

Confira a configuração:

```powershell
git check-ignore -v .env
git ls-files -- .env
```

O segundo comando não deve listar o arquivo.

O `.gitignore` não remove automaticamente arquivos já registrados. Se uma chave for exposta, revogue-a e crie outra.

## Execução pelo terminal

Busca literal:

```powershell
.\venv\Scripts\python.exe app.py
```

Consulta individual com IA:

```powershell
.\venv\Scripts\python.exe consulta_ia.py
```

Essas entradas mantêm a busca anterior por palavras. O modo semântico está integrado ao chat.

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
| Total | 60 | Verificações definidas nesta etapa. |

Mantendo essa suíte, o resultado esperado é:

```text
Ran 60 tests in ...

OK
```

Consulte a execução local ou o GitHub Actions para verificar o resultado real.

### Testar somente a busca semântica

```powershell
.\venv\Scripts\python.exe -m unittest -v test_busca_semantica
```

Os testes utilizam um modelo simulado. Não baixam o E5, não exigem Sentence Transformers e não fazem chamadas ao Gemini.

Eles verificam o comportamento do código, não a capacidade real do modelo de reconhecer significados.

### Limitações da cobertura

Os testes da interface continuam cobrindo `interface.py`. Eles não verificam automaticamente todos os controles do chat, do seletor de busca ou do painel de importação.

A suíte não comprova a qualidade das respostas reais, a correção das citações ou a superioridade da busca semântica.

## GitHub Actions

O workflow em `.github/workflows/testes.yml` instala as dependências básicas e executa:

```text
python -m unittest discover -v
```

Não precisa instalar `requirements-semantica.txt`, baixar o modelo ou configurar a chave do Gemini para executar os testes atuais.

Uma execução verde indica que os cenários programados passaram. Não garante ausência de erros em toda a aplicação.

## Avaliação das buscas

Compare a mesma pergunta nos dois modos, iniciando uma nova conversa antes de trocar.

Exemplos para avaliar com os documentos fictícios:

```text
Minha entrada não foi registrada. Como corrigir?
O equipamento do setor não imprime. Como pedir ajuda?
Quais informações preciso fornecer para receber um crachá?
```

Confira se os trechos selecionados são pertinentes e se contêm informação suficiente.

Teste também uma pergunta fora do domínio:

```text
Como cultivar tomates em casa?
```

A busca semântica pode retornar candidatos mesmo sem um procedimento adequado. Isso não deve ser interpretado como evidência de que a base possui a resposta.

A versão atual não apresenta uma medição sistemática de precisão ou comparação quantitativa entre os modos.

## Privacidade e armazenamento

Na execução local, importação e busca ocorrem no computador que executa o aplicativo.

A busca semântica calcula os embeddings localmente. O download inicial obtém arquivos do modelo; não envia a base de procedimentos para treinamento.

Ao autorizar uma resposta com Gemini, a pergunta, os trechos e as perguntas anteriores selecionadas são enviados ao Google. Confira os termos do serviço antes de utilizar qualquer dado real.

As cópias importadas ficam em disco, e o índice semântico permanece na memória do processo até ser atualizado ou encerrado.

Não existe criptografia dos arquivos, autenticação ou separação da base por usuário. Não disponibilize esta demonstração como serviço institucional sem avaliar esses requisitos.

## Limitações atuais

A busca semântica é experimental e não substitui a revisão das fontes. Pode recuperar documentos inadequados ou deixar de recuperar uma orientação importante.

Não existe um limiar de relevância calibrado nem validação automática de que o documento responde à pergunta.

Os recortes podem omitir condições ou exceções próximas. Confira o procedimento completo.

A extração de PDF e DOCX não preserva todos os elementos do original e não utiliza OCR.

Versões antigas e novas de um documento podem coexistir na base.

A memória da conversa é limitada. Utilize `Nova conversa` para mudar de tema.

As respostas do Gemini podem conter erros ou citações inadequadas.

Ainda não há atualização por Google Drive, histórico permanente, controle de vigência dos documentos ou resultados medidos de economia de tempo no trabalho.

## Ciclo de melhorias

| Ordem | Melhoria | Situação |
| --- | --- | --- |
| 1 | Conversa com contexto | Versão inicial implementada. |
| 2 | Importação de TXT, PDF e DOCX | Versão inicial implementada. |
| 3 | Busca por significado | Alternativa local adicionada nesta etapa; qualidade a avaliar com a base. |
| 4 | Atualização automática de pasta aprovada no Google Drive | Próxima etapa planejada. |

## Referências

- [Sentence Transformers: busca semântica](https://www.sbert.net/examples/sentence_transformer/applications/semantic-search/README.html)
- [Modelo multilingual-e5-small](https://huggingface.co/intfloat/multilingual-e5-small)
- [Sentence Transformers: instalação](https://sbert.net/docs/installation.html)
- [Streamlit](https://docs.streamlit.io/)
- [Termos da Gemini API](https://ai.google.dev/gemini-api/terms)

## Autor

Desenvolvido por Victor Lima Silva como projeto de aprendizado em Python e aplicação de tecnologia à rotina administrativa.

[Perfil no GitHub](https://github.com/limaavls)