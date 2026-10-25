# Assistente de Procedimentos Administrativos

Aplicação em Python para pesquisar procedimentos administrativos, consultar documentos de origem e gerar respostas opcionais com a Gemini API.

O projeto possui uma interface de consulta com Streamlit e um modo de conversa com memória simples do assunto.

> Projeto de estudo e portfólio. Todos os documentos de demonstração são fictícios e não representam procedimentos oficiais de uma instituição.

## Objetivo

Aplicar programação a uma necessidade da rotina administrativa: localizar informações em documentos e conferir a origem das orientações apresentadas.

O desenvolvimento envolve leitura de arquivos, pesquisa textual, interface web, integração com IA, testes automatizados e controle de versões.

A aplicação não aprova solicitações, não executa procedimentos administrativos e não substitui a conferência das orientações oficiais.

## Funcionalidades

| Recurso | Funcionamento |
| --- | --- |
| Interface de consulta | Pesquisa pelo navegador, com visualização de trechos e documentos completos. |
| Busca por perguntas | Extrai palavras da consulta e procura correspondências nos documentos. |
| Normalização | Compara textos sem depender de acentos ou maiúsculas. |
| Ordenação | Prioriza documentos com mais palavras distintas em comum com a pesquisa. |
| Respostas com Gemini | Geração opcional com confirmação antes do envio. |
| Modo de conversa | Mantém perguntas e respostas na sessão e permite perguntas complementares. |
| Memória simples do assunto | Reutiliza a primeira pergunta e a pergunta respondida mais recente. |
| Testes automatizados | Verificações da busca, integração simulada, interface de consulta e preparação da conversa. |
| GitHub Actions | Instala dependências e executa os testes a cada push. |

A geração com IA é experimental. As afirmações e referências precisam ser conferidas nos documentos originais.

## Interfaces disponíveis

Existem duas entradas alternativas para o mesmo projeto. Elas compartilham a busca, a integração com Gemini e a configuração local.

### Consulta individual: interface.py

Permite pesquisar uma pergunta, conferir os documentos candidatos e solicitar uma resposta com IA.

Pesquisar é uma operação local. O envio ao Google depende da autorização e do botão de geração.

Uma nova pesquisa limpa a resposta e a autorização anteriores.

### Conversa: chat.py

Permite fazer perguntas complementares sobre o mesmo assunto:

```text
Como solicitar material?
        ↓
Resposta baseada nos documentos
        ↓
E quais dados preciso informar?
        ↓
Nova consulta considerando o assunto anterior
```

Cada pergunta é preparada localmente antes de qualquer envio à API.

O usuário pode conferir o pedido completo, as perguntas anteriores selecionadas e os trechos que serão enviados.

Depois, precisa autorizar e clicar em `Gerar resposta com IA`.

Também é possível cancelar a pergunta pendente sem realizar o envio.

## Como funciona a memória da conversa

A preparação está em `conversa.py`.

Para cada pergunta, o programa considera:

- A pergunta atual.
- A primeira pergunta da conversa.
- A pergunta respondida mais recente, quando for diferente da primeira.

Essas perguntas ajudam a manter o assunto na busca e na solicitação ao Gemini.

As respostas anteriores da IA são mostradas na tela, mas não são reenviadas como fontes. As informações usadas para responder devem vir dos trechos dos documentos.

Essa é uma memória limitada de assunto, não uma interpretação completa de todo o histórico.

Referências como “explique o segundo item da sua resposta” podem não funcionar adequadamente, pois as respostas anteriores não são enviadas ao modelo.

### Troca de tema e duração

Use `Nova conversa` para mudar de assunto. A aplicação não identifica automaticamente uma mudança de tema.

O histórico fica na sessão do navegador, sem banco de dados. Ele pode ser perdido ao recarregar a página ou encerrar a sessão.

A versão atual permite até 10 respostas por conversa. Após esse limite, inicie uma nova.

Limpar a conversa remove o histórico da aplicação, mas não apaga informações que já tenham sido enviadas ao provedor da API.

## Como funciona a busca

Os arquivos são lidos em formato TXT, com codificação UTF-8, diretamente da pasta `documentos`.

| Modo | Comportamento |
| --- | --- |
| `app.py` | Busca literal por palavra ou expressão, com linhas de contexto. |
| `busca.py` | Extrai palavras da pergunta, ordena os documentos e recupera parágrafos. |

A interface de consulta, o chat e a consulta com IA utilizam a busca por palavras.

Uma pesquisa por `solicitacao` pode encontrar `solicitação`. Já `mat` não encontra `material` por correspondência parcial.

A ordenação não representa uma porcentagem de confiança. Encontrar palavras em comum não garante que o documento responda à pergunta.

A busca ainda não reconhece automaticamente sinônimos ou flexões. `Material`, `materiais` e `suprimentos` são termos diferentes.

## Integração com Gemini

O arquivo `consulta_ia.py` prepara os trechos e realiza a chamada à API.

As duas interfaces reutilizam essas funções.

| Limite | Configuração |
| --- | --- |
| Pergunta digitada | Até 500 caracteres. |
| Documentos selecionados | Até três documentos candidatos. |
| Contexto dos documentos | Até 12.000 caracteres, incluindo identificação das fontes. |
| Conteúdo acima do limite | Interrompe a operação sem cortar o texto silenciosamente. |

No chat, o pedido enviado ao modelo inclui também as perguntas anteriores selecionadas e as instruções de contextualização. Por isso, o pedido completo pode ultrapassar 500 caracteres.

Os limites são escolhas da aplicação, não limites gerais da Gemini API.

As instruções pedem que o modelo utilize os trechos recebidos, indique as fontes e reconheça informações ausentes.

A aplicação não verifica automaticamente se cada afirmação está apoiada na fonte citada.

## Tecnologias

| Tecnologia | Uso |
| --- | --- |
| Python | Leitura de arquivos, normalização, pesquisa e preparação das consultas. |
| Streamlit | Interfaces web e testes da interface de consulta com AppTest. |
| Gemini API e google-genai | Geração de respostas com IA. |
| python-dotenv | Leitura das configurações locais. |
| httpx | Tratamento de falhas de conexão. |
| unittest e unittest.mock | Testes e simulação de dependências. |
| Git e GitHub | Controle de versões. |
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
│   ├── solicitacao_material.txt
│   ├── teste_busca.txt
│   ├── ajuste_registro_ponto.txt
│   ├── suporte_tecnico_ti.txt
│   └── protocolo_documentos.txt
│
├── .gitignore
├── README.md
├── requirements.txt
├── app.py
├── busca.py
├── consulta_ia.py
├── conversa.py
├── interface.py
├── chat.py
├── test_app.py
├── test_busca.py
├── test_consulta_ia.py
├── test_interface.py
└── test_conversa.py
```

O arquivo `.env` e a pasta `venv` são locais e não devem ser publicados.

## Instalação no Windows

### 1. Obter o projeto

Com o Git instalado:

```powershell
git clone https://github.com/limaavls/assistente-procedimentos-python.git
cd assistente-procedimentos-python
```

Se já houver uma cópia, abra a pasta existente no Cursor.

Execute os comandos seguintes no terminal da pasta principal.

### 2. Criar o ambiente virtual

É necessário ter Python instalado. A automação utiliza Python 3.13.

Crie o ambiente apenas se ele ainda não existir:

```powershell
python -m venv venv
```

Os comandos deste README chamam diretamente o Python do ambiente, sem exigir ativação separada.

Se o ambiente se chama `.venv`, utilize esse nome nos caminhos.

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

A instalação não realiza consultas ao Gemini.

## Executar o modo de conversa

```powershell
.\venv\Scripts\python.exe -m streamlit run chat.py --server.address=127.0.0.1 --browser.gatherUsageStats=false
```

Abra o endereço informado no terminal.

Comece com uma pergunta específica, como:

```text
Como solicitar material?
```

Depois de conferir e gerar a resposta, experimente:

```text
E quais dados preciso informar?
```

Para mudar de assunto, clique em `Nova conversa`.

O chat exige a configuração da API para gerar respostas. Sem chave, o conteúdo pode ser preparado localmente, mas o envio fica indisponível.

## Executar a interface de consulta individual

```powershell
.\venv\Scripts\python.exe -m streamlit run interface.py --server.address=127.0.0.1 --browser.gatherUsageStats=false
```

Essa interface permite pesquisar, visualizar parágrafos, consultar documentos completos e gerar uma resposta opcional.

A pesquisa local funciona sem chave de API.

Os comandos das interfaces utilizam o endereço local do computador e desativam o envio de estatísticas de uso do Streamlit. Eles não publicam a aplicação na internet.

Para encerrar uma aplicação, pressione `Ctrl + C` no terminal. Depois, execute o comando da outra interface.

## Configurar o Gemini

Utilize uma chave do Google AI Studio e confira as condições do projeto utilizado.

Na pasta principal, crie `.env`:

```dotenv
GEMINI_API_KEY=COLE_SUA_CHAVE_AQUI
GEMINI_MODEL=gemini-3.5-flash-lite
```

Substitua o exemplo pela chave real somente no arquivo local.

O modelo pode ser configurado por `GEMINI_MODEL`. Confira sua disponibilidade e o plano da conta utilizada.

O `.gitignore` deve incluir:

```gitignore
.env
venv/
.venv/
__pycache__/
```

Verifique a regra:

```powershell
git check-ignore -v .env
```

Confira se o arquivo já está sendo acompanhado pelo Git:

```powershell
git ls-files -- .env
```

O segundo comando não deve listar o arquivo.

Uma regra no `.gitignore` não remove automaticamente arquivos já registrados. Se uma chave for exposta, revogue-a no provedor e crie outra.

Não coloque chaves reais nos testes, no código, no README ou em capturas de tela.

## Execução pelo terminal

Busca literal, sem IA:

```powershell
.\venv\Scripts\python.exe app.py
```

Consulta individual com IA:

```powershell
.\venv\Scripts\python.exe consulta_ia.py
```

Na consulta com IA, confira os trechos antes de digitar `SIM` para autorizar o envio.

## Documentos de demonstração

| Arquivo | Tema fictício |
| --- | --- |
| `solicitacao_material.txt` | Solicitação de materiais. |
| `teste_busca.txt` | Acentos, siglas e ocorrências próximas. |
| `ajuste_registro_ponto.txt` | Correção do ponto e encaminhamento ao RH. |
| `suporte_tecnico_ti.txt` | Abertura e acompanhamento de chamados. |
| `protocolo_documentos.txt` | Conferência e encaminhamento de documentos. |

Os arquivos precisam estar diretamente na pasta `documentos`.

Para ampliar a base atual, adicione outro TXT em UTF-8 e faça uma nova consulta.

A leitura ainda não percorre subpastas nem abre PDF, DOCX, ZIP ou imagens.

O envio de arquivos pela interface será desenvolvido na próxima etapa.

## Testes automatizados

Execute toda a suíte:

```powershell
.\venv\Scripts\python.exe -m unittest discover -v
```

| Arquivo | Testes | Cobertura |
| --- | --- | --- |
| `test_app.py` | 7 | Normalização, busca literal e união de trechos. |
| `test_busca.py` | 6 | Extração de palavras, ordenação e recuperação de parágrafos. |
| `test_consulta_ia.py` | 12 | Preparação do contexto e integração com respostas simuladas. |
| `test_interface.py` | 10 | Interações simuladas de `interface.py`. |
| `test_conversa.py` | 6 | Preparação das perguntas com memória simples do assunto. |
| Total | 41 | Verificações definidas nesta versão. |

Mantendo esses arquivos, uma execução bem-sucedida deve terminar com:

```text
Ran 41 tests in ...

OK
```

Esse é o resultado esperado. Confira a execução local ou a aba Actions para consultar o resultado real de cada versão.

### Testes da conversa

```powershell
.\venv\Scripts\python.exe -m unittest -v test_conversa
```

Verificam a primeira pergunta, a manutenção do assunto, a seleção das perguntas anteriores, a exclusão das respostas da IA do pedido, a validação da entrada e a preservação do histórico recebido pela função.

Esses testes não chamam a API.

### Limites da cobertura

Os testes de `test_interface.py` continuam cobrindo a interface de consulta individual. Eles não cobrem automaticamente a nova tela `chat.py`.

Os testes de `test_conversa.py` verificam a preparação do pedido, não o funcionamento visual do chat ou o entendimento real do modelo.

A suíte não comprova a veracidade das respostas da IA, a correção das citações ou todos os comportamentos possíveis da aplicação.

A quantidade de testes não representa uma porcentagem de cobertura.

## GitHub Actions

O workflow está em `.github/workflows/testes.yml`.

Ele prepara Python 3.13, instala as dependências e executa:

```text
python -m unittest discover -v
```

A execução ocorre a cada push e também pode ser iniciada manualmente pela aba Actions.

Não é necessário cadastrar a chave do Gemini para executar os testes atuais.

Uma execução verde indica que os testes configurados passaram, não que todas as respostas reais da IA estejam corretas.

## Avaliação manual do chat

| Cenário | O que verificar |
| --- | --- |
| Primeira pergunta | Os trechos devem corresponder ao assunto solicitado. |
| Pergunta complementar | O pedido deve incluir o assunto inicial e a pergunta atual. |
| Autorização | Digitar ou revisar uma pergunta não deve enviar a consulta ao Gemini. |
| Cancelamento | A pergunta pendente deve ser descartada sem envio. |
| Nova conversa | Deve limpar o histórico e a pergunta pendente. |
| Informação ausente | A resposta deve reconhecer a ausência, sem inventar regras. |
| Erro da API | Não deve registrar uma resposta inexistente como concluída. |

As respostas devem ser comparadas com os documentos. O sucesso da chamada à API não significa que a resposta passou na avaliação de conteúdo.

## Privacidade e uso da API

A pesquisa é local. A geração de uma resposta envia informações ao Google.

No chat, o envio inclui a pergunta atual, as perguntas anteriores selecionadas e os trechos dos documentos. As respostas anteriores da IA não são incluídas.

Utilize somente dados fictícios nesta demonstração. Não envie documentos internos reais, informações pessoais, senhas ou registros administrativos reais.

Nos serviços gratuitos, os termos do provedor permitem o uso de entradas e respostas para melhoria dos produtos, com possibilidade de revisão humana. Confira as condições aplicáveis à conta utilizada.

A gratuidade depende do modelo, do plano e das cotas. O código não verifica faturamento nem garante ausência de cobrança.

Referências oficiais:

- [Preços da Gemini API](https://ai.google.dev/gemini-api/docs/pricing)
- [Limites de uso](https://ai.google.dev/gemini-api/docs/rate-limits)
- [Termos da Gemini API](https://ai.google.dev/gemini-api/terms)
- [Estado de sessão do Streamlit](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state)

## Limitações

A busca ainda depende de palavras. Não utiliza embeddings, banco vetorial ou busca semântica.

A memória da conversa é limitada ao assunto inicial e à pergunta respondida mais recente. Ela não representa uma compreensão completa do histórico.

Perguntas sobre outro tema podem continuar recuperando documentos do assunto inicial. Use `Nova conversa` para mudar de assunto.

O modelo recebe apenas os trechos selecionados. Informações importantes podem ficar de fora, e as respostas podem conter erros ou referências inadequadas.

A aplicação não possui autenticação, histórico permanente, controle de versões dos procedimentos ou atualização automática por fontes externas.

Não há resultados medidos de economia de tempo ou precisão em uma rotina administrativa real.

## Ciclo de melhorias definido

As próximas etapas serão desenvolvidas uma por vez, nesta ordem:

| Ordem | Melhoria | Situação |
| --- | --- | --- |
| 1 | Conversa com contexto | Versão inicial adicionada nesta etapa; requer validação no navegador. |
| 2 | Envio de documentos pela interface, incluindo PDF e Word | Planejado. |
| 3 | Busca por significado | Planejado. |
| 4 | Atualização automática de uma pasta aprovada no Google Drive | Planejado. |

As três últimas funcionalidades ainda não estão implementadas.

## Autor

Desenvolvido por Victor Lima Silva como projeto de aprendizado em Python e aplicação de tecnologia à rotina administrativa.

[Perfil no GitHub](https://github.com/limaavls)