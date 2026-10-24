# Assistente de Procedimentos Administrativos

Aplicação em Python com interface web em Streamlit para pesquisar procedimentos administrativos, consultar documentos de origem e gerar respostas opcionais com a Gemini API.

O projeto aplica programação a uma necessidade da rotina administrativa: localizar informações em documentos e conferir a origem das orientações apresentadas.

> Projeto de estudo e portfólio. Os documentos de demonstração são fictícios e não representam procedimentos oficiais de uma instituição.

## Objetivo

Desenvolver uma ferramenta de consulta e praticar leitura de arquivos, pesquisa textual, interface web, integração com IA, testes automatizados e controle de versões.

A aplicação não aprova solicitações, não executa procedimentos administrativos e não substitui a conferência de documentos oficiais.

## Funcionalidades

| Recurso | Funcionamento |
| --- | --- |
| Interface web | Pesquisa e consulta pelo navegador com Streamlit. |
| Busca por perguntas | Extrai palavras e procura correspondências nos documentos. |
| Normalização | Compara textos sem depender de acentos ou maiúsculas. |
| Ordenação | Prioriza documentos com mais palavras distintas em comum com a pesquisa. |
| Consulta às fontes | Mostra parágrafos e permite abrir o documento completo. |
| Respostas com Gemini | Geração opcional pela interface ou pelo terminal. |
| Autorização de envio | Exige confirmação antes de consultar a IA. |
| Testes automatizados | Verificações da busca, integração e comportamento simulado da interface. |
| GitHub Actions | Instala as dependências e executa os testes a cada push. |

As respostas com IA são experimentais. As afirmações e referências precisam ser conferidas nos documentos originais.

## Interface web

A interface está em `interface.py`.

```text
Digitar uma pergunta
        ↓
Clicar em Pesquisar
        ↓
Conferir os parágrafos e os documentos encontrados
        ↓
Revisar os trechos selecionados para envio
        ↓
Autorizar o envio ao Google
        ↓
Clicar em Gerar resposta com IA
        ↓
Conferir a resposta e suas fontes
```

Pesquisar é uma operação local. Marcar a autorização, sozinho, também não envia a consulta: é necessário clicar no botão de geração.

A seção `Pesquisa em análise` mostra a pergunta efetivamente pesquisada. Para alterar a consulta, é necessário clicar novamente em `Pesquisar`.

Uma nova pesquisa limpa a resposta anterior e exige outra autorização. A resposta é mantida durante as interações da sessão, mas não existe histórico permanente de consultas.

## Como a busca funciona

Os documentos são arquivos TXT em UTF-8, lidos diretamente da pasta `documentos`.

Existem dois modos:

| Modo | Comportamento |
| --- | --- |
| `app.py` | Busca literal por palavra ou expressão, com linhas de contexto. |
| `busca.py` | Extrai palavras da pergunta, ordena documentos e recupera parágrafos. |

A interface e a consulta com IA utilizam `busca.py`.

A busca considera palavras completas. Por exemplo, `solicitacao` pode encontrar `solicitação`, mas `mat` não encontra `material` por correspondência parcial.

A ordenação utiliza palavras em comum, não uma porcentagem de confiança. Um documento pode conter termos da pergunta sem apresentar a resposta completa.

Sinônimos e flexões não são reconhecidos automaticamente. `Material`, `materiais` e `suprimentos` são termos diferentes.

## Integração com Gemini

O módulo `consulta_ia.py` prepara os trechos e realiza a chamada à API. A interface e a execução pelo terminal reutilizam essas funções.

| Limite da aplicação | Configuração |
| --- | --- |
| Pergunta | Até 500 caracteres. |
| Documentos selecionados | Até três documentos candidatos. |
| Contexto preparado | Até 12.000 caracteres, incluindo as fontes. |
| Conteúdo acima do limite | Interrompe a operação sem cortar o texto silenciosamente. |

Esses valores são escolhas do projeto, não limites gerais da Gemini API.

As instruções solicitam que o modelo utilize os trechos recebidos, cite os arquivos e reconheça informações ausentes.

As citações não são validadas automaticamente. Mostrar `[arquivo.txt]` não comprova que a afirmação esteja apoiada no documento.

## Tecnologias

| Tecnologia | Uso |
| --- | --- |
| Python | Leitura, normalização, pesquisa e integração. |
| Streamlit | Interface web e testes com AppTest. |
| Gemini API e google-genai | Geração de respostas com IA. |
| python-dotenv | Leitura das configurações locais. |
| httpx | Tratamento de falhas de conexão. |
| unittest e unittest.mock | Testes e simulação de dependências. |
| Git e GitHub | Controle de versões. |
| GitHub Actions | Verificação automática dos testes. |

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
├── interface.py
├── test_app.py
├── test_busca.py
├── test_consulta_ia.py
└── test_interface.py
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

É necessário ter Python instalado. O workflow utiliza Python 3.13.

Crie o ambiente somente se ele ainda não existir:

```powershell
python -m venv venv
```

Os comandos deste README chamam diretamente o Python do ambiente, sem exigir ativação separada.

Se seu ambiente se chama `.venv`, substitua `venv` por `.venv` nos caminhos.

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

A busca local funciona sem chave de API. A configuração do Gemini é necessária somente para gerar respostas com IA.

O comando limita o servidor ao endereço local do computador e desativa o envio de estatísticas de uso do Streamlit. Ele não publica a aplicação na internet.

Para encerrar, pressione `Ctrl + C` no terminal.

## Configurar o Gemini

Crie uma chave no [Google AI Studio](https://aistudio.google.com/) e confira o plano do projeto utilizado.

Na pasta principal, crie `.env`:

```dotenv
GEMINI_API_KEY=COLE_SUA_CHAVE_AQUI
GEMINI_MODEL=gemini-3.5-flash-lite
```

Substitua o exemplo pela chave real somente no arquivo local. O modelo é configurável por `GEMINI_MODEL`; confira sua disponibilidade na conta utilizada.

### Proteção da chave

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

Confira se o arquivo já está sendo acompanhado pelo Git:

```powershell
git ls-files -- .env
```

O segundo comando não deve listar o arquivo.

Uma regra no `.gitignore` não remove automaticamente arquivos já registrados. Se uma chave for exposta, revogue-a no provedor e crie outra.

Não coloque chaves reais nos testes, no README, em capturas de tela ou no código.

## Consultas pelo terminal

### Busca literal, sem IA

```powershell
.\venv\Scripts\python.exe app.py
```

Digite uma palavra ou expressão. Execute novamente para outra pesquisa.

### Consulta com IA

```powershell
.\venv\Scripts\python.exe consulta_ia.py
```

Informe a pergunta, confira os trechos e digite `SIM` para autorizar o envio. Outra resposta cancela a operação.

## Documentos de demonstração

| Arquivo | Tema fictício |
| --- | --- |
| `solicitacao_material.txt` | Solicitação de materiais. |
| `teste_busca.txt` | Acentos, siglas e ocorrências próximas. |
| `ajuste_registro_ponto.txt` | Correção do ponto e encaminhamento ao RH. |
| `suporte_tecnico_ti.txt` | Abertura e acompanhamento de chamados. |
| `protocolo_documentos.txt` | Conferência e encaminhamento de documentos. |

Os arquivos precisam estar diretamente em `documentos`. Para ampliar a base, adicione outro TXT em UTF-8 e faça uma nova pesquisa.

A leitura não percorre subpastas nem abre ZIP, PDF, DOCX ou imagens. Arquivos vazios são ignorados, e falhas de leitura são informadas no terminal.

Todos os procedimentos, prazos e situações dos exemplos são fictícios.

## Testes automatizados

Execute toda a suíte:

```powershell
.\venv\Scripts\python.exe -m unittest discover -v
```

### Organização dos testes

| Arquivo | Quantidade | Cobertura |
| --- | --- | --- |
| `test_app.py` | 7 | Normalização, busca literal e união de trechos. |
| `test_busca.py` | 6 | Extração de palavras, ordenação e recuperação de parágrafos. |
| `test_consulta_ia.py` | 12 | Preparação do contexto e integração com respostas simuladas. |
| `test_interface.py` | 10 | Interações simuladas da interface com AppTest. |
| Total | 35 | Verificações definidas nesta versão. |

Mantendo esses arquivos, uma execução bem-sucedida deve terminar com:

```text
Ran 35 tests in ...

OK
```

Esse é o resultado esperado. Consulte a execução local ou a aba Actions para verificar o resultado real de uma versão.

### Testes da integração

```powershell
.\venv\Scripts\python.exe -m unittest -v test_consulta_ia
```

Verificam preparação das fontes, limites do contexto, entradas vazias, resposta válida, resposta incompleta e propagação de erros simulados.

O cliente da API é substituído durante os testes. Não é utilizada chave real nem consumida cota do Gemini.

### Testes da interface

```powershell
.\venv\Scripts\python.exe -m unittest -v test_interface
```

O AppTest executa a interface de forma simulada, sem abrir um navegador.

Os dez cenários verificam:

1. Pesquisa local sem envio e botão de geração desabilitado antes da autorização.
2. Autorização sem envio automático.
3. Geração com a pergunta pesquisada e apresentação da resposta.
4. Preservação da resposta sem novo envio em uma reexecução.
5. Limpeza da resposta e da autorização ao realizar nova pesquisa.
6. Ausência de geração quando não há correspondência.
7. Aviso para pergunta vazia.
8. Busca disponível e IA indisponível quando falta a chave.
9. Mensagem de falha de conexão.
10. Mensagem de cota esgotada.

Esses testes usam textos fictícios definidos no próprio arquivo. A leitura do `.env` é substituída, e as credenciais são fictícias.

A função de geração é simulada, e a criação do cliente real do Gemini também é bloqueada como proteção adicional.

As substituições são temporárias e não alteram o funcionamento normal da aplicação.

Mantenha a pasta `documentos` no projeto: a interface verifica sua existência, embora os textos sejam simulados nesses testes.

### Limites da cobertura

Os testes não comprovam a veracidade das respostas reais da IA nem a correção das citações.

O AppTest não avalia aparência visual, responsividade, acessibilidade ou comportamento em navegadores reais.

A suíte também não cobre integralmente a leitura dos arquivos, todos os erros possíveis da API ou todos os caminhos da aplicação.

A quantidade de testes não representa uma porcentagem de cobertura.

## GitHub Actions

O workflow está em `.github/workflows/testes.yml`.

A automação prepara Python 3.13, instala as dependências e executa:

```text
python -m unittest discover -v
```

A execução ocorre a cada push e também pode ser iniciada manualmente pela aba `Actions`.

Não é necessário cadastrar a chave do Gemini no GitHub para executar a suíte atual.

Uma execução verde indica que os testes configurados passaram. Não garante que toda a aplicação esteja livre de erros.

## Avaliação manual

A aplicação também precisa ser conferida no navegador, e as respostas reais devem ser comparadas com as fontes.

Exemplos de avaliação:

| Cenário | Critério |
| --- | --- |
| Informação disponível | A resposta deve utilizar somente o que os trechos informam. |
| Informação ausente | A IA deve reconhecer a ausência, sem inventar regras, valores ou prazos. |
| Pedido para ignorar as fontes | A IA não deve inventar uma orientação por solicitação do usuário. |
| Documentos conflitantes | A resposta deve apresentar a divergência, sem escolher uma regra sem justificativa. |

Pergunta de exemplo:

```text
Qual é o valor da taxa de segunda via do protocolo?
```

O documento fictício preparado para esse caso não define o valor. O comportamento desejado é reconhecer essa ausência.

Esses são critérios de avaliação, não resultados garantidos. Ainda não há uma medição sistemática da qualidade das respostas reais.

## Privacidade e custos

A pesquisa textual é local. Ao gerar uma resposta real com Gemini, a pergunta e os trechos selecionados são enviados ao Google.

Utilize somente dados fictícios nesta demonstração. Não envie documentos internos reais, informações pessoais, senhas ou registros administrativos reais.

Nos serviços gratuitos, as condições do provedor permitem o uso de entradas e respostas para melhoria dos produtos e podem incluir revisão humana. Confira os termos aplicáveis à conta e à região utilizadas.

A disponibilidade gratuita depende do modelo, do plano e das cotas do projeto. O código não verifica o faturamento e não garante ausência de cobrança.

Os testes simulados não consultam o Gemini. Essa característica dos testes não muda as condições de uso das consultas reais.

Referências oficiais:

- [Preços e modalidades da Gemini API](https://ai.google.dev/gemini-api/docs/pricing)
- [Limites de uso](https://ai.google.dev/gemini-api/docs/rate-limits)
- [Termos da Gemini API](https://ai.google.dev/gemini-api/terms)
- [AppTest do Streamlit](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest)

## Limitações da aplicação

A busca é baseada em palavras. Não utiliza busca semântica, banco vetorial ou reconhecimento automático de sinônimos.

A IA recebe apenas os trechos selecionados. Informações importantes podem ficar de fora, e as respostas podem conter erros ou referências inadequadas.

Encontrar palavras em comum não comprova que o documento responda à pergunta. Não encontrar um termo também não comprova que uma regra não exista.

A aplicação não possui autenticação, histórico permanente, controle de versões dos procedimentos ou atualização automática por fontes externas.

Antes de disponibilizar a ferramenta para uso institucional, será necessário avaliar autorização, privacidade e controle de acesso.

O projeto ainda não apresenta resultados medidos de economia de tempo ou precisão em uma rotina administrativa real.

## Próximas melhorias

- Acrescentar testes de leitura de arquivos e outros caminhos da interface.
- Registrar casos de avaliação das respostas reais da IA.
- Melhorar a seleção de documentos e a conferência das citações.
- Avaliar busca por significado para reduzir a dependência de palavras exatas.
- Automatizar a atualização da base a partir de fontes aprovadas.
- Avaliar autenticação antes de disponibilizar a ferramenta a outras pessoas.

## Autor

Desenvolvido por Victor Lima Silva como projeto de aprendizado em Python e aplicação de tecnologia à rotina administrativa.

[Perfil no GitHub](https://github.com/limaavls)