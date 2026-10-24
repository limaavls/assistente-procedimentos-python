# Assistente de Procedimentos Administrativos

Aplicação de estudo em Python para localizar informações em procedimentos administrativos, com pesquisa pelo terminal ou por uma interface no navegador.

O projeto foi pensado para situações do trabalho administrativo em que é necessário encontrar orientações em documentos e conferir sua origem. A base de demonstração utiliza somente textos fictícios.

> Estado atual: busca textual em arquivos TXT, interface com Streamlit, sete testes automatizados e verificação pelo GitHub Actions. A aplicação ainda não utiliza inteligência artificial.

## Objetivo

Desenvolver uma ferramenta de consulta e praticar Python em um problema relacionado à rotina administrativa. A evolução planejada inclui busca por perguntas e respostas com IA apoiadas nos documentos, mantendo a indicação das fontes e o reconhecimento de informações ausentes.

## Funcionalidades disponíveis

- Consulta vários arquivos `.txt` na pasta `documentos`.
- Pesquisa palavras ou expressões sem diferenciar maiúsculas, minúsculas e acentos.
- Busca palavras completas: `mat` não encontra `material` por correspondência parcial.
- Aceita termos com pelo menos dois caracteres, incluindo siglas como `RH` e `TI`.
- Apresenta o nome do arquivo de origem e trechos do conteúdo original.
- Mostra uma linha antes e uma depois de cada ocorrência, quando disponíveis.
- Une trechos sobrepostos para evitar a repetição das mesmas linhas. Um trecho unido pode ter mais de três linhas.
- Permite abrir o documento completo pela interface.
- Informa quando a pesquisa não encontra correspondência.

A lógica de leitura e busca está em [app.py](app.py). A interface está em [interface.py](interface.py) e reutiliza essas funções.

## Como a consulta funciona

```text
Arquivos TXT na pasta documentos
              ↓
Leitura dos textos em UTF-8
              ↓
Pesquisa de uma palavra ou expressão
              ↓
Comparação sem depender de acentos ou maiúsculas
              ↓
Exibição dos trechos originais e dos nomes dos arquivos
```

O programa não altera os documentos nem escreve uma resposta nova. A normalização é aplicada à comparação; os resultados preservam o texto original.

## Tecnologias utilizadas

| Tecnologia | Uso no projeto |
| --- | --- |
| Python | Leitura de arquivos e lógica de pesquisa. |
| Streamlit | Interface de consulta no navegador. |
| unittest | Testes da normalização e da seleção de trechos. |
| Git e GitHub | Controle de versões e publicação do projeto. |
| GitHub Actions | Execução automática dos testes a cada push. |

A interface utiliza a dependência declarada em [requirements.txt](requirements.txt). A busca pelo terminal e os testes atuais utilizam apenas a biblioteca padrão do Python.

## Estrutura do projeto

```text
assistente-procedimentos-python/
├── .github/
│   └── workflows/
│       └── testes.yml
├── documentos/
│   ├── solicitacao_material.txt
│   └── teste_busca.txt
├── .gitignore
├── app.py
├── interface.py
├── requirements.txt
├── test_app.py
└── README.md
```

Outros arquivos TXT de demonstração podem ser adicionados diretamente em `documentos`, conforme a seção de documentos de teste abaixo. O ambiente virtual `venv` é criado localmente e não deve ser incluído no repositório.

## Como executar no Windows

### 1. Obter o projeto

Com o Git instalado, execute:

```powershell
git clone https://github.com/limaavls/assistente-procedimentos-python.git
cd assistente-procedimentos-python
```

Se o projeto já estiver no computador, abra a pasta existente no Cursor e utilize um terminal nessa pasta. Não é necessário clonar novamente.

### 2. Criar o ambiente virtual

É necessário ter Python instalado. A automação de testes do repositório está configurada para Python 3.13.

Crie o ambiente somente se ele ainda não existir neste projeto:

```powershell
python -m venv venv
```

Os próximos comandos chamam diretamente o Python desse ambiente. Não é necessário ativá-lo separadamente.

### 3. Instalar as dependências

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 4. Abrir a interface

```powershell
.\venv\Scripts\python.exe -m streamlit run interface.py --server.address=127.0.0.1 --browser.gatherUsageStats=false
```

Abra no navegador o endereço informado no terminal. Digite um termo, clique em `Pesquisar` e confira os trechos encontrados. Use `Ver documento completo` para consultar o conteúdo integral de cada fonte.

O comando mantém a aplicação acessível localmente e desativa o envio de estatísticas de uso do Streamlit. Não publica a ferramenta na internet.

Mantenha o terminal aberto enquanto utiliza a interface. Para encerrar, pressione `Ctrl + C` no terminal.

### Alternativa: pesquisa pelo terminal

```powershell
.\venv\Scripts\python.exe app.py
```

Digite uma palavra ou expressão quando solicitado. O programa apresenta os trechos e as fontes no próprio terminal. Para fazer outra pesquisa nesse modo, execute o comando novamente.

## Documentos de demonstração

Os arquivos iniciais são:

| Arquivo | Finalidade |
| --- | --- |
| `solicitacao_material.txt` | Exemplo fictício de solicitação de material. |
| `teste_busca.txt` | Texto curto para verificar acentos, siglas e ocorrências próximas. |

A base pode ser ampliada com os três documentos adicionais preparados para o projeto:

| Arquivo | Tema do cenário fictício |
| --- | --- |
| `ajuste_registro_ponto.txt` | Correção do registro de ponto, conferência de frequência e encaminhamento ao RH. |
| `suporte_tecnico_ti.txt` | Abertura de chamados, problemas de acesso e atendimento de TI. |
| `protocolo_documentos.txt` | Conferência, digitalização, registro e encaminhamento de documentos. |

Esses três arquivos precisam ser copiados para `documentos` para participar da pesquisa. Todos os prazos, regras e situações neles descritos são inventados para estudo.

### Como adicionar um documento

Salve um arquivo com extensão `.txt` e codificação UTF-8 diretamente na pasta `documentos`, ao lado dos exemplos existentes. Depois, faça uma nova pesquisa pela interface ou execute novamente o programa no terminal.

Não é necessário cadastrar o nome do arquivo no código. A leitura atual não percorre subpastas e não abre arquivos ZIP. Arquivos vazios são ignorados; falhas de leitura são informadas no terminal.

Não publique documentos internos reais, informações pessoais, senhas ou credenciais nesta base de demonstração.

## Exemplos de pesquisa

### Com os documentos iniciais

| Pesquisa | Comportamento esperado |
| --- | --- |
| `material` | Localiza as ocorrências dessa palavra. |
| `MATERIAL` | Localiza as mesmas ocorrências, ignorando maiúsculas. |
| `solicitacao` | Localiza a palavra “solicitação”, apesar da diferença de acento. |
| `mat` | Não encontra “material” por correspondência parcial. |
| Campo vazio | Exibe um aviso para informar um termo válido. |

### Após adicionar os três documentos extras

| Pesquisa | Documento em que se espera uma correspondência |
| --- | --- |
| `frequencia` | `ajuste_registro_ponto.txt` |
| `RH` | `ajuste_registro_ponto.txt` |
| `TI` | `suporte_tecnico_ti.txt` |
| `SENHA` | `suporte_tecnico_ti.txt` |
| `digitalizacao` | `protocolo_documentos.txt` |

Outros documentos também podem aparecer se contiverem o mesmo termo.

Nesta versão, prefira palavras ou expressões presentes no texto. Uma pergunta como `Como solicitar material?` é tratada como uma expressão literal, e não como várias palavras independentes ou uma pergunta a ser respondida.

## Testes automatizados

Os testes estão em [test_app.py](test_app.py) e utilizam `unittest`.

Execute na pasta principal:

```powershell
.\venv\Scripts\python.exe -m unittest -v test_app
```

As sete verificações atuais cobrem:

1. Normalização de acentos e maiúsculas.
2. Busca sem acento.
3. Busca com maiúsculas.
4. Rejeição de correspondências parciais de palavras.
5. Termo sem correspondência.
6. Documento vazio.
7. União de trechos sobrepostos sem duplicar linhas.

Quando todas passam, o resultado termina com `Ran 7 tests` e `OK`.

Os testes usam textos definidos no próprio código. Adicionar documentos à pasta não cria novos testes automáticos nem altera essa quantidade.

A cobertura atual não inclui leitura de arquivos, validação da entrada no terminal ou comportamento da interface.

## Verificação automática no GitHub

O workflow [testes.yml](.github/workflows/testes.yml) executa os testes a cada `push` e permite execução manual pela aba `Actions`.

Ele prepara Python 3.13 em um ambiente Linux do GitHub e executa:

```text
python -m unittest -v test_app
```

Consulte a aba `Actions` para verificar o resultado de cada execução. A aprovação indica que os testes configurados passaram; não significa que todas as funcionalidades estejam livres de erros ou que a interface tenha sido testada automaticamente.

## Limitações atuais

- A pesquisa é literal e não utiliza IA nem interpretação de significado.
- Não há busca por perguntas com separação de palavras ou ordenação por relevância.
- Não reconhece sinônimos ou flexões automaticamente: `material` e `materiais` são termos diferentes.
- Expressões precisam aparecer na mesma linha do documento para serem encontradas.
- A leitura aceita TXT em UTF-8; não lê PDF, DOCX, imagens ou subpastas.
- A aplicação não possui autenticação nem controle de acesso para uso compartilhado.
- Os trechos encontrados podem não conter todas as condições e exceções do procedimento. Confira o documento completo.

Encontrar um termo não comprova que o documento responda à dúvida. Da mesma forma, a ausência de correspondência não comprova que uma regra ou procedimento não exista.

## Próximas melhorias

- [ ] Separar perguntas em palavras relevantes e ordenar documentos por correspondência.
- [ ] Acrescentar testes para a busca por perguntas, leitura de arquivos e interface.
- [ ] Gerar respostas com IA apoiadas nos trechos recuperados e com indicação das fontes.
- [ ] Avaliar respostas para perguntas cujas informações não estejam nos documentos.
- [ ] Automatizar a atualização da base a partir de fontes aprovadas.
- [ ] Avaliar autenticação e controle de acesso antes de qualquer uso institucional compartilhado.

Esses itens são planejados e não fazem parte da versão atual.

## Cuidados com os dados

Todos os documentos de demonstração são fictícios. O projeto não representa procedimentos oficiais da Prefeitura de Mauá ou de outra instituição e não substitui a consulta às orientações oficiais.

A versão atual não utiliza serviços externos de IA. Antes de uma futura integração, será necessário definir quais dados podem ser enviados ao serviço e obter as autorizações aplicáveis.

O ambiente virtual, arquivos de credenciais e informações confidenciais não devem ser publicados no GitHub.

## Autor

Desenvolvido por Victor Lima Silva como projeto de aprendizado em Python e aplicação de tecnologia à rotina administrativa.

[Perfil no GitHub](https://github.com/limaavls)