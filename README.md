# Assistente de Procedimentos Administrativos

Aplicação em Python com interface web em Streamlit para pesquisar procedimentos administrativos, visualizar trechos relevantes e consultar os documentos de origem.

O projeto também possui uma integração experimental com a Gemini API para gerar respostas a partir dos trechos encontrados. A consulta com IA está implementada pelo terminal, e sua integração à interface está em andamento.

A proposta é aplicar programação a uma necessidade da rotina administrativa: localizar informações em documentos de maneira organizada e conferir a origem de cada orientação.

> Projeto de estudo e portfólio. Os documentos de demonstração são fictícios e não representam procedimentos oficiais de uma instituição.

## Objetivo

Desenvolver uma ferramenta de apoio à consulta de procedimentos e praticar Python em um problema relacionado ao trabalho administrativo.

O desenvolvimento reúne leitura de arquivos, pesquisa de textos, interface web, integração com API de IA, testes automatizados e controle de versões.

O programa não aprova solicitações, não executa procedimentos administrativos e não substitui a conferência das orientações oficiais.

## Estado do projeto

| Recurso | Situação |
| --- | --- |
| Interface web com Streamlit | Implementada. |
| Pesquisa de perguntas e palavras-chave | Implementada com comparação textual. |
| Ordenação dos documentos por palavras em comum | Implementada. |
| Exibição de parágrafos e arquivos de origem | Implementada. |
| Consulta ao documento completo pela interface | Implementada. |
| Pesquisa literal pelo terminal | Implementada em `app.py`. |
| Consulta com Gemini pelo terminal | Implementação experimental em `consulta_ia.py`. |
| Respostas com Gemini na interface | Etapa de integração e validação em andamento. |
| Testes automatizados da busca | 13 testes definidos. |
| Execução automática dos testes | Configurada com GitHub Actions. |

Ter uma integração implementada não comprova a qualidade das respostas. A comunicação real com a API e o comportamento da IA precisam ser avaliados separadamente.

## Interface web

A interface existente está em [interface.py](interface.py).

Pelo navegador, o usuário pode digitar uma pergunta ou palavra-chave, clicar em `Pesquisar` e consultar:

- A quantidade de documentos carregados e encontrados.
- Os nomes dos arquivos e as palavras correspondentes à pesquisa.
- Os parágrafos recuperados.
- O conteúdo integral de cada arquivo em `Ver documento completo`.

A busca funciona localmente e não precisa de uma chave de API.

### Fluxo da busca na interface

```text
Abrir a aplicação no navegador
              ↓
Digitar uma pergunta ou palavra-chave
              ↓
Clicar em Pesquisar
              ↓
Conferir os documentos e os parágrafos encontrados
              ↓
Abrir o documento completo para verificar a informação
```

### Evolução em andamento: IA na mesma tela

A etapa de integração acrescenta uma ação separada para gerar uma resposta com Gemini, reutilizando a busca e o módulo `consulta_ia.py`.

O comportamento definido para essa atualização é:

```text
Pesquisar
    ↓
Conferir os documentos candidatos
    ↓
Visualizar os trechos selecionados para envio
    ↓
Autorizar o envio ao Google
    ↓
Clicar em Gerar resposta com IA
    ↓
Ler a resposta e conferir as fontes
```

Nessa atualização, apenas pesquisar não deve enviar informações ao Gemini. A chamada depende da autorização e do botão específico.

A implementação preparada para essa etapa também mantém a resposta durante as interações da sessão e limpa a resposta e a autorização anteriores quando uma nova pesquisa é realizada.

Essa integração precisa estar presente no `interface.py` utilizado e ser validada antes de ser considerada concluída. Alterar o README não implementa o botão na aplicação.

## Como a busca funciona

A lógica está dividida entre [app.py](app.py) e [busca.py](busca.py).

Os arquivos TXT são lidos diretamente da pasta `documentos`. Para comparar os textos, o programa normaliza acentos e maiúsculas, sem modificar os documentos originais.

Existem dois modos de pesquisa:

| Modo | Funcionamento |
| --- | --- |
| Terminal com `app.py` | Procura uma palavra ou expressão literal e apresenta linhas próximas às ocorrências. |
| Interface com `busca.py` | Separa a pergunta em palavras, remove alguns termos comuns e ordena os documentos pela quantidade de palavras distintas em comum. |

Na busca por perguntas, uma consulta como:

```text
Como solicitar material?
```

é tratada como um conjunto de palavras de pesquisa. Os documentos com mais palavras distintas correspondentes aparecem primeiro.

Essa ordenação não é uma porcentagem de confiança nem uma avaliação do significado do texto.

### Características

- Comparação sem diferenciar acentos e maiúsculas.
- Pesquisa por palavras completas.
- Aceitação de termos a partir de dois caracteres.
- Preservação do texto original nos resultados.
- Exibição do nome do arquivo de origem.
- Apresentação de parágrafos completos na busca por perguntas.

Uma pesquisa por `solicitacao` pode encontrar `solicitação`. Já `mat` não encontra `material` apenas por ser parte da palavra.

A busca ainda não reconhece automaticamente sinônimos ou flexões. Por exemplo, `material`, `materiais` e `suprimentos` são termos diferentes.

## Consulta experimental com Gemini

O módulo [consulta_ia.py](consulta_ia.py) utiliza os resultados da busca local para preparar uma consulta à Gemini API.

Pelo terminal, o programa:

1. Recebe uma pergunta.
2. Localiza documentos candidatos.
3. Reúne trechos de até três documentos.
4. Mostra o conteúdo selecionado.
5. Solicita confirmação antes do envio.
6. Apresenta a resposta gerada para revisão.

As instruções enviadas ao modelo pedem que ele utilize somente os trechos fornecidos, cite os nomes dos arquivos e reconheça informações ausentes.

Essas instruções não impedem todos os erros. A implementação não valida automaticamente se cada afirmação ou referência está realmente apoiada nos documentos.

### Limites definidos no projeto

| Item | Configuração |
| --- | --- |
| Tamanho máximo da pergunta | 500 caracteres. |
| Quantidade máxima de documentos enviados | 3 documentos. |
| Tamanho máximo do contexto preparado | 12.000 caracteres. |
| Conteúdo acima do limite | A consulta é interrompida, sem cortar o texto silenciosamente. |
| Ausência de documentos ou correspondência | A API não é consultada. |
| Ausência de chave | O programa informa que a configuração está pendente. |
| Confirmação pelo terminal | Exige a resposta `SIM` antes do envio. |

Esses limites são escolhas da aplicação, não limites gerais da Gemini API.

## Tecnologias utilizadas

| Tecnologia | Aplicação |
| --- | --- |
| Python | Leitura de arquivos, normalização e pesquisa. |
| Streamlit | Interface no navegador. |
| Gemini API | Geração experimental de respostas com base nos trechos. |
| google-genai | Acesso à API do Gemini. |
| python-dotenv | Leitura das configurações locais do `.env`. |
| httpx | Tratamento de falhas de conexão na integração. |
| unittest | Testes automatizados da busca. |
| Git e GitHub | Controle de versões e publicação do projeto. |
| GitHub Actions | Execução automática dos testes. |

## Estrutura principal

```text
assistente-procedimentos-python/
│
├── .github/
│   └── workflows/
│       └── testes.yml
│
├── documentos/
│   └── arquivos de demonstração em formato TXT
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

O arquivo `.env` e a pasta `venv` são criados localmente e não devem ser publicados.

| Arquivo | Responsabilidade |
| --- | --- |
| `app.py` | Carregamento dos documentos, normalização e busca literal pelo terminal. |
| `busca.py` | Extração de palavras das perguntas e ordenação dos documentos. |
| `interface.py` | Tela de pesquisa e apresentação dos documentos. |
| `consulta_ia.py` | Preparação dos trechos e integração experimental com Gemini. |
| `test_app.py` | Testes de normalização e seleção de trechos. |
| `test_busca.py` | Testes de pesquisa por palavras extraídas de perguntas. |
| `requirements.txt` | Dependências adicionais da aplicação. |

## Instalação no Windows

### 1. Obter o projeto

Com o Git instalado, execute:

```powershell
git clone https://github.com/limaavls/assistente-procedimentos-python.git
cd assistente-procedimentos-python
```

Se já tiver uma cópia, abra a pasta existente no Cursor. Não é necessário clonar novamente.

Execute os próximos comandos no terminal da pasta principal do projeto.

### 2. Criar o ambiente virtual

É necessário ter Python instalado. O workflow de testes utiliza Python 3.13.

Crie o ambiente apenas se ele ainda não existir:

```powershell
python -m venv venv
```

Os comandos deste README chamam diretamente o Python do ambiente, sem exigir ativação separada.

Caso seu ambiente se chame `.venv`, substitua `venv` por `.venv` nos caminhos.

### 3. Conferir as dependências

Para executar a etapa completa com interface e Gemini, o `requirements.txt` precisa incluir:

```text
streamlit
google-genai
python-dotenv
httpx
```

Preserve outras dependências que estejam sendo utilizadas.

Se sua cópia ainda tiver apenas `streamlit`, acrescente as bibliotecas da integração antes de executar a consulta com IA.

### 4. Instalar as dependências

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Instalar as bibliotecas não configura a chave e não realiza uma consulta ao Gemini.

## Executar a interface

Na pasta principal:

```powershell
.\venv\Scripts\python.exe -m streamlit run interface.py --server.address=127.0.0.1 --browser.gatherUsageStats=false
```

Abra o endereço informado no terminal.

Digite uma pergunta ou palavra-chave, clique em `Pesquisar` e confira as fontes. Utilize `Ver documento completo` para consultar o conteúdo integral de cada arquivo.

Exemplos:

```text
Como solicitar material?
Como solicitar ajuste do ponto?
Como abrir um chamado de suporte para impressora?
RH
digitalizacao
```

Os resultados dependem dos documentos existentes na pasta.

O comando mantém a aplicação acessível localmente e desativa o envio de estatísticas de uso do Streamlit. Ele não publica a ferramenta na internet.

Para encerrar, pressione `Ctrl + C` no terminal.

Caso a tela ainda apresente somente a busca, isso corresponde à versão anterior à integração visual com Gemini. A consulta com IA pode ser utilizada separadamente pelo terminal.

## Executar a busca literal pelo terminal

```powershell
.\venv\Scripts\python.exe app.py
```

Digite uma palavra ou expressão, como:

```text
material
```

Esse modo não utiliza IA e mantém a busca literal, sem a separação da pergunta em palavras realizada por `busca.py`.

Para outra pesquisa, execute o comando novamente.

## Configurar o Gemini

A busca local não exige essa configuração. Ela é necessária somente para gerar respostas com IA.

### 1. Obter a chave

Acesse o [Google AI Studio](https://aistudio.google.com/) e utilize a área de chaves de API.

Para utilizar a modalidade gratuita, confira o plano do projeto e a disponibilidade do modelo no Free Tier.

O modelo configurado nesta etapa é:

```text
gemini-3.5-flash-lite
```

As condições de disponibilidade, limites e cobrança podem mudar. O programa não verifica o plano de faturamento da conta.

### 2. Conferir o `.gitignore`

O arquivo deve conter as regras:

```gitignore
.env
venv/
.venv/
__pycache__/
```

Não apague outras regras existentes.

Confira se o `.env` está sendo ignorado:

```powershell
git check-ignore -v .env
```

Confira também se ele já está sendo acompanhado pelo Git:

```powershell
git ls-files -- .env
```

O segundo comando não deve listar o arquivo.

Se listar, resolva o rastreamento antes de colocar uma chave real. Uma regra no `.gitignore` não remove automaticamente um arquivo já registrado.

### 3. Criar o `.env`

Na pasta principal:

```dotenv
GEMINI_API_KEY=COLE_SUA_CHAVE_AQUI
GEMINI_MODEL=gemini-3.5-flash-lite
```

Substitua o exemplo pela chave real somente nesse arquivo local.

Não publique a chave no código, no README, em mensagens ou em capturas de tela.

### 4. Executar a consulta com IA

```powershell
.\venv\Scripts\python.exe consulta_ia.py
```

Exemplo:

```text
Quais informações preciso informar para solicitar material?
```

Leia os trechos exibidos antes de responder à confirmação:

```text
Enviar? Digite SIM para continuar:
```

Digite `SIM` para enviar. Outra resposta cancela a operação.

Compare a resposta com os trechos e com o documento completo. Uma referência como `[arquivo.txt]` não comprova, sozinha, que a informação está correta.

## Documentos de demonstração

Foram preparados os seguintes arquivos fictícios para os testes:

| Arquivo | Tema |
| --- | --- |
| `solicitacao_material.txt` | Informações necessárias para solicitar materiais. |
| `teste_busca.txt` | Acentos, siglas e ocorrências próximas. |
| `ajuste_registro_ponto.txt` | Correção do ponto e encaminhamento ao RH. |
| `suporte_tecnico_ti.txt` | Abertura e acompanhamento de chamados de TI. |
| `protocolo_documentos.txt` | Conferência, digitalização e encaminhamento de documentos. |

Cada arquivo precisa estar diretamente em `documentos` para participar das pesquisas. Listar seu nome no README não o adiciona à base.

Para incluir outro documento, salve um TXT em UTF-8 nessa pasta e realize uma nova pesquisa.

A leitura atual não percorre subpastas e não abre ZIP, PDF, DOCX ou imagens. Arquivos vazios são ignorados; falhas de leitura aparecem no terminal.

Todos os procedimentos, prazos e situações desses exemplos são fictícios.

## Testes automatizados

Execute:

```powershell
.\venv\Scripts\python.exe -m unittest discover -v
```

A suíte definida nesta etapa contém 13 testes:

| Arquivo | Quantidade | Cobertura |
| --- | --- | --- |
| [test_app.py](test_app.py) | 7 | Normalização, acentos, maiúsculas, palavras completas, ausência de correspondência, texto vazio e união de trechos sobrepostos. |
| [test_busca.py](test_busca.py) | 6 | Extração de palavras, ordenação, rejeição de correspondências parciais, perguntas sem termos úteis, preservação de parágrafos e ausência de correspondência. |

Mantendo essa suíte, uma execução bem-sucedida termina com:

```text
Ran 13 tests in ...

OK
```

Esse é o resultado esperado, não um registro de execução.

Os testes utilizam textos definidos no próprio código. Não fazem chamadas ao Gemini, não precisam de uma chave e não validam a qualidade das respostas da IA.

A cobertura atual também não inclui o comportamento da interface ou a leitura real dos arquivos.

Adicionar documentos à pasta não cria novos testes automaticamente.

## GitHub Actions

O workflow [testes.yml](.github/workflows/testes.yml) executa:

```text
python -m unittest discover -v
```

A automação utiliza Python 3.13 em um ambiente Linux. Ela é acionada a cada `push` e também permite execução manual pela aba `Actions`.

Uma execução verde indica que os testes configurados passaram. Não comprova que a interface ou a integração real com Gemini tenham sido validadas.

Não é necessário configurar a chave do Gemini no GitHub Actions para a suíte atual.

## Verificações manuais

| Ação | Comportamento esperado |
| --- | --- |
| Pesquisar `solicitacao` | Localizar “solicitação”, apesar da diferença de acento. |
| Pesquisar `RH` | Encontrar documentos que contenham essa sigla. |
| Pesquisar `mat` | Não localizar “material” por correspondência parcial. |
| Perguntar `Como solicitar material?` | Apresentar documentos com palavras correspondentes. |
| Abrir o documento completo | Permitir conferir informações além do trecho recuperado. |
| Cancelar a confirmação no terminal | Encerrar sem enviar a consulta ao Gemini. |
| Perguntar à IA o valor da taxa de segunda via do protocolo | Reconhecer que o valor não está informado no documento fictício. |

Na integração da IA à interface, verificar também:

- Pesquisar sem acionar a API.
- Exigir autorização antes do envio.
- Manter a resposta durante as interações da mesma consulta.
- Limpar a resposta e a autorização ao iniciar outra pesquisa.
- Não gerar resposta quando a busca não encontrar trechos.

Esses comportamentos são critérios de avaliação. Falhas devem ser registradas e corrigidas, não omitidas da demonstração.

## Privacidade e segurança

A busca textual é local. Na consulta com Gemini, a pergunta e os trechos selecionados são enviados ao Google.

As condições dos serviços gratuitos permitem o uso de entradas e respostas para melhoria dos produtos, com possibilidade de revisão humana. Consulte os termos aplicáveis à sua conta e região.

Por isso, esta demonstração deve utilizar somente dados fictícios. Não envie documentos internos reais, informações pessoais, registros de ponto reais, senhas ou credenciais.

Antes de uso institucional, será necessário avaliar autorização, tratamento dos dados, permissões e controle de acesso.

O projeto não possui autenticação para uso compartilhado.

Se uma chave for exposta, revogue-a no provedor e crie outra. Apagar o texto da versão atual do arquivo não elimina a exposição anterior.

## Uso gratuito e limites

O modelo de referência possui modalidade gratuita sujeita às condições e cotas do Google.

O código não garante gratuidade nem identifica se a conta está em um plano pago. Confira essas informações no AI Studio antes de utilizar a API.

Um erro `429` pode indicar cota atingida ou indisponível. Erros de autenticação, acesso ou modelo precisam ser investigados na configuração antes de repetir as solicitações.

Referências oficiais:

- [Preços e modalidades da Gemini API](https://ai.google.dev/gemini-api/docs/pricing)
- [Limites de uso](https://ai.google.dev/gemini-api/docs/rate-limits)
- [Termos da Gemini API](https://ai.google.dev/gemini-api/terms)
- [Primeiros passos com Gemini](https://ai.google.dev/gemini-api/docs/quickstart)

## Limitações atuais

A seleção dos documentos utiliza palavras, não busca por significado. Pode deixar de encontrar um procedimento que use termos diferentes dos presentes na pergunta.

Encontrar palavras em comum não comprova que um documento responda à dúvida. Não encontrar um termo também não comprova que uma regra não exista.

A IA recebe apenas os trechos selecionados, que podem estar incompletos. Ela pode produzir afirmações incorretas, referências inadequadas ou interpretações sem apoio nos textos.

A aplicação ainda não possui validação automática das citações, avaliação sistemática das respostas, controle de versões dos procedimentos ou atualização automática de fontes externas.

Não há medição documentada de economia de tempo ou de precisão para uso administrativo real.

## Próximas melhorias

- Concluir e validar a integração do Gemini à interface.
- Criar testes da integração com respostas simuladas, sem consumir a API.
- Acrescentar testes da interface e da leitura de arquivos.
- Avaliar respostas com informações ausentes, documentos conflitantes e fontes insuficientes.
- Melhorar a seleção de trechos e a verificação das citações.
- Automatizar a atualização da base a partir de fontes aprovadas.
- Avaliar autenticação e controle de acesso antes de uso compartilhado.

Esses itens são objetivos de desenvolvimento, não funcionalidades concluídas.

## Aprendizados demonstrados

O projeto reúne organização de código em módulos, manipulação de textos, leitura de arquivos, tratamento de erros, interface web e integração com um serviço externo.

Os testes e o histórico do Git permitem acompanhar a evolução da solução e verificar parte de seu comportamento a cada alteração.

A proposta do portfólio é demonstrar o funcionamento, explicar as decisões tomadas e apresentar as limitações com clareza.

## Autor

Desenvolvido por Victor Lima Silva como projeto de aprendizado em Python e aplicação de tecnologia à rotina administrativa.

[Perfil no GitHub](https://github.com/limaavls)