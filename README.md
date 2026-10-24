# Assistente de Procedimentos Administrativos

Projeto de estudo em Python para facilitar a consulta
a procedimentos administrativos.

## Versão atual

- Consulta um documento fictício em formato TXT.
- Busca um termo sem diferenciar maiúsculas e minúsculas.
- Mostra o conteúdo original e o nome do arquivo encontrado.
- Informa quando não encontra o termo ou não consegue ler o arquivo.

## Como executar

É necessário ter Python 3 instalado.

Na pasta principal do projeto, execute:

`python app.py`

Para experimentar, pesquise por: material

## Limitações

A versão atual consulta apenas um arquivo e faz busca literal.
Ainda não utiliza IA e não interpreta perguntas ou sinônimos.

## Próximas melhorias

- Consultar vários documentos.
- Mostrar os trechos relevantes e suas fontes.
- Adicionar respostas com IA baseadas nos documentos.
- Criar testes automatizados.
- Automatizar a atualização da base de procedimentos.

## Dados utilizados

Todos os documentos publicados são fictícios.
Este projeto não representa procedimentos oficiais de uma instituição.

## Testes automatizados

O projeto utiliza unittest, disponível na biblioteca padrão do Python.

Para executar os testes, use na pasta principal:

`python -m unittest -v test_app`

As sete verificações atuais cobrem:

- Normalização de acentos e maiúsculas.
- Busca sem acento.
- Busca com letras maiúsculas.
- Rejeição de correspondências parciais de palavras.
- Termo inexistente.
- Documento vazio.
- União de trechos sobrepostos sem repetir linhas.

Os testes atuais não cobrem a leitura dos arquivos
nem a interação pelo terminal.

## Verificação automática no GitHub

O projeto inclui uma configuração do GitHub Actions
para executar os testes a cada atualização enviada
ao repositório.

A automação prepara o Python e executa:

`python -m unittest -v test_app`

Os resultados podem ser consultados na aba Actions.

Essa verificação cobre os testes existentes de busca
e normalização. Ela não garante que todas as funcionalidades
do projeto estejam livres de erros.

## Interface no navegador

O projeto possui uma interface com Streamlit para pesquisar
nos documentos fictícios e visualizar os resultados.

A interface permite:

- Digitar um termo de pesquisa.
- Visualizar os trechos encontrados e seus arquivos de origem.
- Abrir o conteúdo completo de cada documento encontrado.

### Como executar no Windows

Caso ainda não exista um ambiente virtual neste projeto:

```powershell
python -m venv venv
```

Instale as bibliotecas:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Inicie a interface:

```powershell
.\venv\Scripts\python.exe -m streamlit run interface.py --server.address=127.0.0.1 --browser.gatherUsageStats=false
```

Abra o endereço informado no terminal.

### Limitações

A pesquisa continua sendo textual: não interpreta perguntas,
sinônimos nem o significado dos documentos.

Esta versão não utiliza IA e não possui controle de acesso
para uso compartilhado em uma instituição.

Os testes automatizados atuais cobrem a lógica da busca,
não a interface.