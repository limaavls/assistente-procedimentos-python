# Assistente de Procedimentos Administrativos

Aplicação em Python com interface web desenvolvida em Streamlit para pesquisar procedimentos administrativos, visualizar trechos relevantes e consultar os documentos de origem.

O usuário pode fazer a pesquisa diretamente pelo navegador, sem precisar utilizar comandos no terminal a cada consulta.

O projeto aplica programação a uma necessidade da rotina administrativa: localizar informações em documentos de maneira organizada e conferir a origem de cada orientação.

> Projeto de estudo e portfólio. A interface web e a busca em documentos já estão implementadas. Os documentos de demonstração são fictícios e não representam orientações oficiais de uma instituição.

## Interface web — implementada

A interface está no arquivo `interface.py` e utiliza Streamlit.

Pela tela, o usuário pode:

- Digitar uma pergunta ou palavra-chave.
- Realizar a consulta pelo botão `Pesquisar`.
- Visualizar a quantidade de documentos carregados e encontrados.
- Consultar os nomes dos arquivos e as palavras que corresponderam à pesquisa.
- Ler os parágrafos encontrados.
- Expandir a opção `Ver documento completo` para conferir a fonte integral.

Os documentos são apresentados conforme a quantidade de palavras da pesquisa encontradas em cada arquivo.

Essa ordenação ajuda a localizar fontes candidatas, mas não garante que elas contenham uma resposta completa.

### Fluxo de uso da interface

```text
Abrir a aplicação no navegador
              ↓
Digitar uma pergunta ou palavra-chave
              ↓
Clicar em Pesquisar
              ↓
Conferir os documentos e os trechos encontrados
              ↓
Abrir o documento completo para verificar a informação
```

### Como abrir a interface

Com o ambiente virtual e as dependências instalados, execute na pasta principal:

```powershell
.\venv\Scripts\python.exe -m streamlit run interface.py --server.address=127.0.0.1 --browser.gatherUsageStats=false
```

Abra o endereço informado no terminal.

A interface funciona localmente no navegador. Esse comando não publica a aplicação na internet.

As instruções de instalação estão nas próximas seções deste README.

## Interface e inteligência artificial

A interface web já existe e funciona para consultar os documentos.

Na versão publicada, essa tela utiliza a busca textual: ela encontra e apresenta conteúdo original dos arquivos, sem gerar uma nova resposta com IA.

A consulta experimental com Gemini foi organizada separadamente em `consulta_ia.py`, conforme a etapa de integração descrita neste README. Sua utilização depende da implementação desse módulo, das dependências e da configuração local da API.

Integrar essa consulta à interface é uma evolução posterior. Não será necessário criar outra tela do zero: a proposta é acrescentar a geração de respostas à interface existente.

## Estado do projeto

| Recurso | Situação |
| --- | --- |
| Interface web com Streamlit | Implementada em `interface.py`. |
| Pesquisa de perguntas e palavras-chave pela interface | Implementada com a busca de `busca.py`. |
| Exibição de trechos e arquivos de origem | Implementada. |
| Consulta ao documento completo pela tela | Implementada. |
| Pesquisa literal pelo terminal | Disponível em `app.py`. |
| Testes automatizados da busca | Organizados em `test_app.py` e `test_busca.py`. |
| Verificação dos testes no GitHub | Configurada com GitHub Actions. |
| Consulta experimental com Gemini pelo terminal | Descrita na seção de integração; depende da configuração local e da validação. |
| Geração de respostas com Gemini na interface | Próxima evolução. |

## Objetivo

Desenvolver uma ferramenta de apoio à consulta de procedimentos e praticar:

- Leitura, tratamento e pesquisa de textos com Python.
- Organização do código em funções e módulos.
- Criação de interface com Streamlit.
- Testes automatizados e controle de versões.
- Integração experimental com IA, preservando fontes e revisão humana.

O projeto não executa procedimentos administrativos, não aprova solicitações e não substitui a conferência das orientações oficiais.

## Como funciona

### Busca local, sem IA

```text
Pergunta ou palavra-chave
           ↓
Separação e normalização das palavras
           ↓
Pesquisa nos arquivos TXT
           ↓
Ordenação dos documentos por palavras em comum
           ↓
Exibição dos parágrafos encontrados e das fontes
```

Na interface, uma pergunta como:

```text
Como solicitar material?
```

é transformada em palavras de pesquisa. O programa compara essas palavras com os documentos e coloca primeiro os arquivos com mais termos diferentes em comum.

Essa ordenação não representa uma porcentagem de confiança. Um documento pode conter palavras da pergunta sem apresentar a resposta completa.

### Consulta experimental com Gemini

```text
Pergunta
    ↓
Busca local de documentos candidatos
    ↓
Seleção de trechos de até três documentos
    ↓
Exibição do conteúdo que será enviado
    ↓
Confirmação do usuário no terminal
    ↓
Envio da pergunta e dos trechos ao Gemini
    ↓
Apresentação da resposta para revisão
```

A integração solicita que o modelo use os trechos fornecidos, indique os arquivos utilizados e reconheça quando uma informação não estiver disponível.

Essas instruções não garantem que a resposta esteja correta. As afirmações e as fontes precisam ser conferidas nos documentos originais.

## Funcionalidades da busca

A leitura considera arquivos `.txt` em UTF-8 diretamente na pasta `documentos`. Arquivos vazios são ignorados, e falhas de leitura são informadas no terminal.

A comparação desconsidera diferenças de maiúsculas, minúsculas e acentos. Por exemplo, uma pesquisa por `solicitacao` pode encontrar `solicitação`.

Existem dois modos de pesquisa:

| Modo | Funcionamento |
| --- | --- |
| Terminal com `app.py` | Pesquisa uma palavra ou expressão literal e mostra linhas próximas às ocorrências. Trechos sobrepostos são unidos para evitar repetição. |
| Interface com `interface.py` | Separa a pergunta em palavras, remove alguns termos comuns, ordena os documentos por correspondência e mostra parágrafos completos. |

A interface também permite abrir o conteúdo integral de cada documento encontrado.

A busca considera palavras completas: `mat` não encontra `material` apenas por ser parte da palavra.

## Tecnologias

| Tecnologia | Aplicação |
| --- | --- |
| Python | Leitura de arquivos, normalização e lógica de busca. |
| Streamlit | Interface de consulta no navegador. |
| Gemini API | Geração experimental de respostas a partir de trechos. |
| google-genai | Biblioteca de acesso à API do Gemini. |
| python-dotenv | Carregamento da configuração local do arquivo `.env`. |
| httpx | Tratamento de falhas de conexão na integração. |
| unittest | Testes automatizados da lógica de busca. |
| Git e GitHub | Controle de versões e publicação do projeto. |
| GitHub Actions | Execução automática dos testes. |

A busca pelo terminal e os testes atuais utilizam a biblioteca padrão do Python. A interface e a integração com Gemini precisam das dependências adicionais.

## Organização dos arquivos

Estrutura considerada para a etapa com Gemini e os documentos de demonstração:

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
├── interface.py
├── consulta_ia.py
├── test_app.py
└── test_busca.py
```

Os arquivos locais `.env` e a pasta `venv` não devem ser publicados no GitHub.

| Arquivo | Responsabilidade |
| --- | --- |
| `app.py` | Carrega os documentos, normaliza textos e oferece a busca literal pelo terminal. |
| `busca.py` | Extrai palavras de perguntas e ordena os documentos encontrados. |
| `interface.py` | Apresenta a busca e os documentos no navegador. |
| `consulta_ia.py` | Implementa a etapa experimental de consulta ao Gemini pelo terminal. |
| `test_app.py` | Testa normalização e seleção de trechos. |
| `test_busca.py` | Testa a pesquisa por palavras extraídas de perguntas. |
| `requirements.txt` | Relaciona as dependências adicionais. |

## Instalação no Windows

### 1. Obter o projeto

Com o Git instalado, execute:

```powershell
git clone https://github.com/limaavls/assistente-procedimentos-python.git
cd assistente-procedimentos-python
```

Se já tiver uma cópia no computador, abra essa pasta no Cursor. Não é necessário clonar novamente.

Os comandos seguintes devem ser executados no terminal, dentro da pasta principal do projeto.

### 2. Criar o ambiente virtual

É necessário ter Python instalado. O workflow de testes está configurado para Python 3.13.

Crie o ambiente somente se ele ainda não existir:

```powershell
python -m venv venv
```

Os comandos deste README chamam diretamente o Python desse ambiente, sem exigir sua ativação.

Caso seu ambiente se chame `.venv`, substitua `venv` por `.venv` nos caminhos apresentados.

### 3. Instalar as dependências

Para a etapa que inclui a interface e a consulta com Gemini, o `requirements.txt` deve conter:

```text
streamlit
google-genai
python-dotenv
httpx
```

Instale as dependências:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

A instalação das bibliotecas não configura a chave de acesso nem realiza uma consulta à IA.

## Executar a interface

```powershell
.\venv\Scripts\python.exe -m streamlit run interface.py --server.address=127.0.0.1 --browser.gatherUsageStats=false
```

Abra no navegador o endereço informado no terminal.

Digite uma palavra ou pergunta, clique em `Pesquisar` e confira os resultados. A opção `Ver documento completo` permite consultar o conteúdo integral de cada fonte.

Exemplos:

```text
Como solicitar material?
Como solicitar ajuste do ponto?
Como abrir um chamado de suporte para impressora?
RH
digitalizacao
```

Nesta etapa, a interface realiza apenas a busca local. Ela não gera respostas com Gemini e não precisa de uma chave de API.

O comando utiliza o endereço local do computador e desativa o envio de estatísticas de uso do Streamlit. Ele não publica a aplicação na internet.

Para encerrar, pressione `Ctrl + C` no terminal.

## Executar a busca literal pelo terminal

```powershell
.\venv\Scripts\python.exe app.py
```

Digite uma palavra ou expressão presente nos documentos, como:

```text
material
```

Esse modo mantém a pesquisa literal. Não possui a mesma separação de perguntas em palavras utilizada pela interface.

Para realizar outra pesquisa, execute o comando novamente.

## Configurar a consulta experimental com Gemini

Esta seção corresponde à integração em `consulta_ia.py`, separada da interface Streamlit. Antes de executar, confirme que esse módulo foi adicionado e que as dependências foram instaladas.

### 1. Criar uma chave de acesso

Acesse o [Google AI Studio](https://aistudio.google.com/) e utilize a área de chaves de API para criar uma chave no seu projeto.

Para desenvolver com a modalidade gratuita, confira se o projeto está no Free Tier e se o modelo escolhido está disponível nesse plano.

A configuração de referência desta etapa utiliza:

```text
gemini-3.5-flash-lite
```

A disponibilidade, as cotas e as condições de cobrança podem mudar. Confira as informações do seu projeto e a documentação oficial antes de utilizar.

### 2. Proteger a configuração local

Confira se o `.gitignore` contém:

```gitignore
.env
venv/
.venv/
__pycache__/
```

Verifique a regra do arquivo `.env`:

```powershell
git check-ignore -v .env
```

Confira também se ele já está sendo acompanhado pelo Git:

```powershell
git ls-files -- .env
```

O segundo comando não deve listar o arquivo. Se listar, resolva o rastreamento antes de colocar uma chave real nele.

Adicionar uma regra ao `.gitignore` não remove automaticamente arquivos que já foram registrados no Git.

### 3. Criar o arquivo `.env`

Na pasta principal, crie um arquivo chamado `.env`:

```dotenv
GEMINI_API_KEY=COLE_SUA_CHAVE_AQUI
GEMINI_MODEL=gemini-3.5-flash-lite
```

Substitua o exemplo pela chave real somente no arquivo local.

Não coloque a chave no código, no README, em capturas de tela ou em mensagens públicas.

Caso uma chave seja exposta, revogue-a no provedor e crie outra. Apagar o texto da versão atual do arquivo não elimina a exposição anterior.

### 4. Executar a consulta

```powershell
.\venv\Scripts\python.exe consulta_ia.py
```

Exemplo de pergunta:

```text
Quais informações preciso informar para solicitar material?
```

O programa mostra os trechos candidatos antes do envio. Com a chave configurada, solicita:

```text
Enviar? Digite SIM para continuar:
```

Digite `SIM` para autorizar o envio. Outra resposta cancela a consulta.

A pergunta e os trechos são enviados ao Google. Não utilize dados reais, pessoais ou confidenciais nesta demonstração.

### Regras da implementação experimental

| Configuração | Comportamento |
| --- | --- |
| Tamanho da pergunta | Até 500 caracteres. |
| Documentos selecionados | Até três, conforme a ordenação da busca. |
| Limite do contexto | Até 12.000 caracteres reunindo fontes e trechos. Acima disso, a consulta é interrompida. |
| Confirmação | Exigida antes da solicitação à API. |
| Falta de documentos ou de correspondência | Encerra sem consultar a IA. |
| Falta de chave | Avisa que a configuração está pendente. |
| Resposta interrompida ou bloqueada | Não apresenta texto parcial como resposta concluída. |

Os limites de caracteres são escolhas deste projeto, não limites gerais da Gemini API.

As instruções solicitam referências no formato `[arquivo.txt]`, mas a implementação ainda não valida automaticamente se cada afirmação está apoiada na fonte citada.

## Documentos de demonstração

| Arquivo | Conteúdo fictício |
| --- | --- |
| `solicitacao_material.txt` | Informações necessárias para solicitar materiais. |
| `teste_busca.txt` | Texto curto para testar acentos, siglas e ocorrências próximas. |
| `ajuste_registro_ponto.txt` | Solicitação de correção do ponto e encaminhamento ao RH. |
| `suporte_tecnico_ti.txt` | Abertura de chamados e informações para atendimento de TI. |
| `protocolo_documentos.txt` | Conferência, digitalização e encaminhamento de documentos. |

Os arquivos precisam estar diretamente em `documentos` para participar das pesquisas. Os nomes listados no README, por si só, não cadastram documentos.

Para ampliar a base, salve um novo arquivo `.txt` em UTF-8 nessa pasta. Depois, faça uma nova pesquisa pela interface ou execute novamente o programa pelo terminal.

A leitura atual não percorre subpastas nem abre arquivos ZIP, PDF, DOCX ou imagens.

## Testes automatizados

Execute:

```powershell
.\venv\Scripts\python.exe -m unittest discover -v
```

O comando encontra os arquivos de testes do projeto.

A suíte desta etapa contém 13 testes:

| Arquivo | Quantidade | Verificações |
| --- | --- | --- |
| `test_app.py` | 7 | Normalização, acentos, maiúsculas, palavras completas, ausência de correspondência, texto vazio e união de trechos sobrepostos. |
| `test_busca.py` | 6 | Extração de palavras, ordenação dos documentos, rejeição de correspondências parciais, perguntas sem termos úteis, preservação de parágrafos e ausência de correspondência. |

Mantendo essa suíte, uma execução bem-sucedida deve terminar com:

```text
Ran 13 tests in ...

OK
```

Esse é o resultado esperado, não um registro de uma execução específica.

Os testes atuais não fazem chamadas à API e não precisam de uma chave do Gemini. Eles também não validam a interface, a leitura dos arquivos ou a qualidade das respostas geradas pela IA.

Adicionar documentos à pasta não cria novos testes automaticamente.

### GitHub Actions

O workflow em `.github/workflows/testes.yml` executa:

```text
python -m unittest discover -v
```

A configuração utiliza Python 3.13 em um ambiente Linux e permite execução a cada `push` ou manualmente pela aba `Actions`.

Uma execução verde indica que os testes configurados passaram. Não significa que todo o projeto esteja livre de erros nem que a consulta ao Gemini tenha sido validada.

## Verificações manuais sugeridas

| Consulta ou ação | O que conferir |
| --- | --- |
| Pesquisar `solicitacao` | Deve localizar a palavra “solicitação”, apesar do acento. |
| Pesquisar `RH` | Deve encontrar os documentos que contenham essa sigla. |
| Pesquisar `mat` | Não deve localizar “material” por correspondência parcial. |
| Perguntar `Como solicitar material?` | Deve apresentar documentos candidatos relacionados às palavras da pergunta. |
| Perguntar à IA o valor da taxa de segunda via do protocolo | Deve reconhecer que o valor não está informado no documento fictício, sem inventar um preço. |
| Cancelar a confirmação da consulta com IA | Deve encerrar sem enviar a solicitação ao Gemini. |

Os comportamentos da IA são critérios de avaliação, não resultados garantidos. Registre respostas incorretas ou sem apoio nos documentos para orientar as próximas melhorias.

## Uso gratuito, privacidade e segurança

O modelo de referência possui uma modalidade gratuita sujeita a cotas e condições do Google. O programa não consulta o plano de faturamento da conta nem garante ausência de cobrança.

Confira o Free Tier, os limites e a disponibilidade do modelo no Google AI Studio. Um erro `429` pode indicar limite atingido ou cota indisponível.

Nos serviços gratuitos, os termos do Google permitem o uso de entradas e respostas para melhoria dos produtos, incluindo possibilidade de revisão humana. Por isso, utilize somente dados fictícios nesta demonstração.

Antes de qualquer uso com documentos reais, será necessário avaliar autorização institucional, tratamento dos dados, acesso aos documentos e condições do serviço externo.

A configuração atual não oferece autenticação ou controle de acesso para utilização compartilhada.

Referências oficiais:

- [Modelos Gemini](https://ai.google.dev/gemini-api/docs/models)
- [Preços e Free Tier](https://ai.google.dev/gemini-api/docs/pricing)
- [Limites de uso](https://ai.google.dev/gemini-api/docs/rate-limits)
- [Termos da Gemini API](https://ai.google.dev/gemini-api/terms)

## Limitações

A recuperação de documentos é baseada em palavras, não em interpretação de significado. Ela não reconhece automaticamente sinônimos ou flexões, como `material` e `materiais`.

Encontrar palavras em comum não comprova que o documento responda à pergunta. Da mesma forma, não encontrar um termo não comprova que uma regra não exista.

A consulta com IA recebe apenas os trechos selecionados. Informações importantes podem ficar de fora, e o modelo pode produzir uma resposta incorreta ou citar uma fonte que não sustente sua afirmação.

A solução ainda não possui avaliação automática das respostas, validação de citações, controle de versões dos procedimentos ou atualização automática da base.

Os documentos fictícios não devem ser utilizados como orientação administrativa real.

## Próximas melhorias

- Validar a integração real com Gemini e registrar os resultados dos testes manuais.
- Criar testes da integração usando respostas simuladas, sem consumir a API.
- Integrar a consulta com IA à interface Streamlit.
- Avaliar respostas para informações ausentes, documentos conflitantes e fontes insuficientes.
- Melhorar a seleção de trechos e a verificação das fontes citadas.
- Acrescentar testes de leitura de arquivos e da interface.
- Automatizar a atualização da base a partir de documentos aprovados.
- Avaliar autenticação e controle de acesso antes de um uso institucional.

Esses itens são melhorias planejadas, não funcionalidades concluídas.

## Autor

Desenvolvido por Victor Lima Silva como projeto de aprendizado em Python e aplicação de tecnologia à rotina administrativa.

[Perfil no GitHub](https://github.com/limaavls)