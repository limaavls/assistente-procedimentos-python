# Assistente de Procedimentos Administrativos

Aplicação em Python para pesquisar procedimentos administrativos, consultar fontes e gerar respostas opcionais com a Gemini API.

O projeto possui interface de consulta, conversa com contexto limitado, importação de documentos, busca semântica local e sincronização de uma pasta aprovada no Google Drive.

> Projeto de estudo e portfólio. Utilize somente documentos fictícios. A aplicação não representa procedimentos oficiais de uma instituição.

## Objetivo

Aplicar programação a uma necessidade da rotina administrativa: localizar informações em documentos e conferir a origem das orientações apresentadas.

O desenvolvimento reúne processamento de documentos, pesquisa textual e semântica, interface web, integração com APIs, automação e testes.

A aplicação não aprova solicitações nem substitui a conferência dos procedimentos oficiais.

## Funcionalidades

| Recurso | Funcionamento |
| --- | --- |
| Consulta individual | Pesquisa e visualização de trechos e documentos completos. |
| Conversa | Perguntas complementares com memória limitada do assunto. |
| Importação local | Seleção de TXT, PDF ou DOCX pelo painel lateral do chat. |
| Prévia de importação | Conferência do texto antes da inclusão manual. |
| Busca por palavras | Normalização e ordenação por correspondências. |
| Busca semântica | Comparação local de embeddings da pergunta e dos trechos. |
| Respostas com Gemini | Geração opcional após revisão e autorização. |
| Verificação do Drive | Confirmação de acesso e listagem dos itens da pasta. |
| Sincronização do Drive | Criação, atualização e retirada de cópias locais gerenciadas. |
| Repetição periódica | Sincronização em intervalos enquanto o programa estiver em execução. |
| Backups locais | Preservação das cópias anteriores antes de alterações. |
| Testes e GitHub Actions | Verificações automatizadas com dados e respostas simuladas. |

As respostas e as fontes citadas pela IA precisam ser conferidas nos documentos originais.

## Interfaces

### Consulta individual — interface.py

Permite pesquisar uma pergunta, visualizar os parágrafos recuperados, consultar o conteúdo disponível de cada documento e gerar uma resposta opcional.

Essa interface mantém a busca por palavras.

### Conversa — chat.py

Permite importar documentos, escolher o modo de busca e fazer perguntas complementares.

```text
Escolher o modo de busca
        ↓
Digitar uma pergunta
        ↓
Conferir os documentos e os trechos
        ↓
Autorizar o envio ao Google
        ↓
Gerar e revisar a resposta
```

Pesquisar, importar ou sincronizar documentos não chama o Gemini.

A geração de uma resposta exige autorização separada.

Use `Nova conversa` para trocar de assunto, mudar o modo de busca ou consultar uma base atualizada pela sincronização.

## Memória da conversa

A preparação utiliza a pergunta atual, a primeira pergunta da conversa e a pergunta respondida mais recente.

As respostas anteriores da IA não são reenviadas como fontes.

Essa memória é limitada. Referências como “explique o segundo item da sua resposta” podem não funcionar adequadamente.

O histórico fica na sessão do navegador, sem banco de dados, e a versão atual permite até 10 respostas por conversa.

Uma pergunta já preparada não é atualizada automaticamente quando a base muda.

## Modos de busca

### Por palavras

Implementado em `busca.py`.

Extrai palavras da consulta, ignora alguns termos comuns e ordena os documentos pela quantidade de palavras distintas em comum.

A comparação desconsidera acentos e maiúsculas. Sinônimos e flexões não são reconhecidos automaticamente.

### Por significado — local

Implementado em `busca_semantica.py`.

Utiliza Sentence Transformers com o modelo `intfloat/multilingual-e5-small`.

O modelo transforma textos em embeddings e compara a pergunta com os trechos disponíveis. Ele localiza candidatos, mas não escreve a resposta.

| Configuração | Limite |
| --- | --- |
| Execução | Processador do computador. |
| Recortes | Até 300 tokens, com sobreposição de 50. |
| Base da demonstração | Até 500 trechos. |
| Seleção | Até três documentos e dois trechos por documento. |
| Atualização do índice | Na próxima pesquisa, quando a base mudar. |

O modelo é preparado em `.cache_modelos`. As pesquisas utilizam a cópia local.

O índice fica na memória do processo e não é um banco vetorial persistente.

Não existe um limiar de relevância validado. Uma pergunta sem relação com a base também pode receber candidatos.

A semelhança calculada não representa probabilidade de acerto.

## Importação manual de documentos

Disponível no painel lateral do chat.

```text
Selecionar arquivo
        ↓
Extrair e revisar
        ↓
Confirmar inclusão
        ↓
Salvar cópia TXT local
```

Formatos aceitos: TXT em UTF-8, PDF com texto extraível e DOCX.

A extração não utiliza OCR e não preserva todos os elementos visuais ou especiais do original.

### Limites da conversão

| Item | Regra |
| --- | --- |
| Arquivo processado | Até 5 MiB. |
| PDF | Até 30 páginas. |
| Texto extraído | Até 100.000 caracteres. |
| PDF protegido | Recusado. |
| Página de PDF sem texto extraível | O arquivo inteiro é recusado. |
| DOCX expandido | Limite interno de 20 MiB. |
| DOC antigo | Não aceito. |

As cópias manuais utilizam o padrão:

```text
documentos/importado_nome_identificador.txt
```

Conteúdos diferentes podem gerar cópias diferentes. Não há substituição automática de versões nesse modo manual.

Para documentos convertidos, a consulta ao conteúdo completo apresenta o texto extraído, não a aparência original do arquivo.

## Sincronização com Google Drive

A integração utiliza uma conta de serviço com acesso de leitura a uma pasta exclusiva de demonstração.

### Verificação de acesso

`verificar_drive.py` confirma a pasta e lista os itens diretamente dentro dela.

Essa operação consulta metadados, sem baixar o conteúdo.

### Sincronização

`sincronizar_drive.py` lê os documentos compatíveis e mantém cópias TXT na base local.

Formatos suportados nesta etapa:

- TXT.
- PDF.
- DOCX.
- Documentos nativos do Google Docs, exportados como texto.

Planilhas, apresentações, imagens, atalhos, outros formatos e subpastas não são processados.

A seleção considera o tipo de arquivo informado pelo Drive.

### Regras da atualização

| Situação | Comportamento |
| --- | --- |
| Arquivo novo | Cria uma cópia local. |
| Mesmo ID com conteúdo ou nome alterado | Atualiza a cópia correspondente. |
| Mesmo conteúdo já sincronizado | Mantém a cópia, sem duplicá-la. |
| Arquivo deixa de aparecer na pasta | Retira a cópia gerenciada da base ativa e preserva backup. |
| Documento compatível não pode ser lido | Interrompe antes de aplicar as novas cópias. |
| Cópia gerenciada editada manualmente | Interrompe para evitar sobrescrever a edição. |
| Arquivo local não gerenciado | Não é removido pela rotina. |
| Pasta configurada muda | Interrompe para evitar misturar duas bases. |

O ID identifica o documento. Criar outro arquivo com o mesmo nome não equivale a editar o mesmo documento.

A ausência na listagem não comprova que um arquivo foi excluído: ele também pode ter sido movido ou deixado de ser visível para a conta utilizada.

### Cópias, controle e backups

```text
documentos/drive_identificador.txt
.estado_drive/manifesto.json
.estado_drive/historico/
```

O cabeçalho de cada cópia informa o nome original e o ID do Drive.

Não edite os arquivos gerenciados nem o manifesto manualmente.

Os backups ficam fora da pasta pesquisada, mas permanecem no computador. Não há limpeza automática do histórico.

A sincronização não altera arquivos no Google Drive.

### Limites e comportamento em falhas

A demonstração aceita até 30 documentos compatíveis por execução. A listagem reutilizada aceita até 200 itens na pasta.

Os limites de extração existentes continuam sendo aplicados. Exportações do Google Docs também passam pela validação do texto recebido.

Todos os documentos compatíveis são lidos novamente em cada ciclo. Ainda não existe uma otimização para baixar apenas arquivos modificados.

A gravação utiliza arquivos temporários e tenta restaurar as cópias anteriores se ocorrer uma falha durante a aplicação das mudanças.

Isso não constitui uma transação de toda a base. Falta de energia, encerramento forçado, problemas de disco ou falha na restauração podem exigir recuperação manual.

Uma pasta `em_execucao` impede duas sincronizações simultâneas. Se ela permanecer após um encerramento inesperado, confira os processos e os backups antes de qualquer remoção manual.

Se a consulta ao Drive falhar, não presuma que a base está atualizada. Cópias antigas podem continuar disponíveis.

### Atualização no chat

A sincronização não modifica uma pergunta que já esteja aguardando autorização nem reescreve respostas anteriores.

Espere a conclusão da execução e clique em `Nova conversa` antes de consultar o conteúdo atualizado.

O índice semântico percebe mudanças na base na próxima pesquisa.

## Integração com Gemini

O módulo `consulta_ia.py` prepara os trechos e realiza a chamada ao modelo gerador.

| Item | Limite |
| --- | --- |
| Pergunta digitada | 500 caracteres. |
| Documentos enviados | Até três candidatos. |
| Contexto dos documentos | 12.000 caracteres, incluindo identificação das fontes. |

No chat, o pedido também inclui as perguntas anteriores selecionadas.

Importação, sincronização, busca e envio à IA possuem limites diferentes. Um arquivo aceito pode gerar contexto grande demais para uma consulta.

As instruções solicitam respostas fundamentadas nos trechos, mas as afirmações e citações não são verificadas automaticamente.

## Organização do projeto

```text
assistente-procedimentos-python/
├── .github/workflows/testes.yml
├── documentos/
├── .secrets/                  # Credenciais locais
├── .estado_drive/             # Controle e backups locais
├── .cache_modelos/            # Modelo local
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
├── sincronizar_drive.py
└── test_*.py
```

Credenciais, modelos, cópias privadas e backups não devem ser publicados.

## Instalação no Windows

### Obter o projeto e preparar o ambiente

```powershell
git clone https://github.com/limaavls/assistente-procedimentos-python.git
cd assistente-procedimentos-python
python -m venv venv
```

Se já houver uma cópia e um ambiente virtual, reutilize-os.

O workflow de testes utiliza Python 3.13.

Os comandos seguintes chamam diretamente o Python do ambiente. Se sua pasta se chama `.venv`, ajuste os caminhos.

### Dependências básicas

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Incluem Streamlit, google-genai, python-dotenv, httpx, pypdf e python-docx.

### Busca semântica opcional

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements-semantica.txt
.\venv\Scripts\python.exe busca_semantica.py
```

A segunda execução baixa o modelo. Não envia a base de procedimentos.

### Google Drive opcional

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements-drive.txt
```

Esse arquivo acrescenta google-api-python-client, google-auth e google-auth-httplib2.

## Configuração local

### Gemini

No `.env`:

```dotenv
GEMINI_API_KEY=COLE_SUA_CHAVE_AQUI
```

O modelo gerador pode ser definido por `GEMINI_MODEL`. Quando ausente, utiliza-se `MODELO_PADRAO` de `consulta_ia.py`.

Preserve a configuração já validada. O modelo de geração é independente do modelo semântico local.

### Google Drive

1. Ative a Google Drive API no projeto Google Cloud.
2. Crie uma conta de serviço dedicada.
3. Compartilhe somente a pasta de demonstração como Leitor/Visualizador.
4. Guarde a credencial em `.secrets/google-drive.json`.

Acrescente ao `.env`:

```dotenv
DRIVE_FOLDER_ID=COLE_AQUI_SOMENTE_O_ID_DA_PASTA
DRIVE_CREDENTIALS_FILE=.secrets/google-drive.json
```

Não utilize o endereço inteiro da pasta.

A chave do Gemini e a credencial JSON do Drive são acessos diferentes.

## Executar a aplicação

### Chat

```powershell
.\venv\Scripts\python.exe -m streamlit run chat.py --server.address=127.0.0.1 --browser.gatherUsageStats=false
```

### Consulta individual

```powershell
.\venv\Scripts\python.exe -m streamlit run interface.py --server.address=127.0.0.1 --browser.gatherUsageStats=false
```

Os comandos iniciam a aplicação localmente. Não publicam a ferramenta na internet.

Para encerrar, pressione `Ctrl + C`.

### Busca literal pelo terminal

```powershell
.\venv\Scripts\python.exe app.py
```

### Consulta com IA pelo terminal

```powershell
.\venv\Scripts\python.exe consulta_ia.py
```

## Executar a sincronização

### Confirmar o acesso

```powershell
.\venv\Scripts\python.exe verificar_drive.py
```

### Sincronizar uma vez

```powershell
.\venv\Scripts\python.exe sincronizar_drive.py
```

O resultado informa quantidades de arquivos incluídos, atualizados, retirados, mantidos e ignorados.

### Repetir periodicamente

Após validar a execução manual:

```powershell
.\venv\Scripts\python.exe sincronizar_drive.py --intervalo 300
```

O programa executa um ciclo e aguarda 300 segundos antes do próximo.

O terminal precisa permanecer aberto. O computador precisa estar ligado e conectado à internet. Esse comando não instala um serviço nem configura inicialização automática no Windows.

Utilize outro terminal para executar o chat.

Para encerrar o monitor, pressione `Ctrl + C`.

## Proteção no Git

O `.gitignore` deve incluir:

```gitignore
.env
venv/
.venv/
__pycache__/
documentos/importado_*.txt
documentos/drive_*.txt
.cache_modelos/
.secrets/
.estado_drive/
```

Preserve outras regras existentes.

Confira as credenciais:

```powershell
git check-ignore -v .env .secrets/google-drive.json
git ls-files -- .env .secrets/
```

O segundo comando não deve listar arquivos.

O `.gitignore` não remove automaticamente arquivos já registrados. Se uma credencial for exposta, revogue-a e crie outra.

## Testes automatizados

Execute:

```powershell
.\venv\Scripts\python.exe -m unittest discover -v
```

| Arquivo | Quantidade |
| --- | --- |
| `test_app.py` | 7 |
| `test_busca.py` | 6 |
| `test_consulta_ia.py` | 12 |
| `test_interface.py` | 10 |
| `test_conversa.py` | 6 |
| `test_importacao.py` | 9 |
| `test_busca_semantica.py` | 10 |
| `test_verificar_drive.py` | 6 |
| `test_sincronizar_drive.py` | 10 |
| Total | 76 |

Mantendo essa suíte, uma execução bem-sucedida deve terminar com:

```text
Ran 76 tests in ...

OK
```

Esse é o resultado esperado. Consulte a execução local ou o GitHub Actions para verificar cada versão.

### Testar somente a sincronização

```powershell
.\venv\Scripts\python.exe -m unittest -v test_sincronizar_drive
```

Os testes verificam criação, atualização, backups, prevenção de duplicação, retirada de cópias gerenciadas, preservação de arquivos manuais, colisões, restauração simulada e interrupção antes de aplicar downloads incompletos.

As respostas do Drive e os downloads são simulados. Não há leitura das credenciais nem acesso a uma conta real.

### Limites da cobertura

A suíte não valida a qualidade das respostas reais da IA, todos os controles do chat, a autenticação real ou todas as falhas de rede e disco.

Os testes semânticos usam um modelo simulado e não comprovam a qualidade do modelo real.

Uma quantidade de testes não representa uma porcentagem de cobertura.

## GitHub Actions

O workflow instala as dependências básicas e executa:

```text
python -m unittest discover -v
```

A suíte atual não precisa de credenciais, modelo baixado ou acesso real ao Drive e ao Gemini.

Uma execução verde indica que os cenários configurados passaram, não que toda a aplicação esteja livre de erros.

## Privacidade e limitações

A importação e as buscas são locais. A sincronização lê os documentos da pasta aprovada e grava suas cópias no computador.

Somente a geração de respostas envia a pergunta e os trechos selecionados ao Gemini. Confira os termos, cotas e condições da conta utilizada.

Cópias retiradas da base permanecem nos backups locais. Excluir um documento no Drive não elimina todas as cópias já armazenadas ou informações anteriormente enviadas a serviços externos.

O projeto não possui criptografia dos arquivos, autenticação de usuários ou isolamento da base por pessoa.

Documentos importados manualmente podem duplicar conteúdos também sincronizados do Drive. A sincronização não elimina essas importações independentes.

Não há aprovação automática de procedimentos, controle de vigência institucional ou garantia de que uma resposta esteja correta.

O projeto não apresenta resultados medidos de economia de tempo ou precisão em uma rotina administrativa real.

## Ciclo de melhorias

| Ordem | Melhoria | Situação |
| --- | --- | --- |
| 1 | Conversa com contexto | Versão inicial implementada. |
| 2 | Importação de TXT, PDF e DOCX | Versão inicial implementada. |
| 3 | Busca por significado | Alternativa local implementada. |
| 4 | Atualização por pasta aprovada no Drive | Sincronização local com repetição opcional implementada nesta etapa. |

A execução real e a qualidade dos resultados devem ser avaliadas no ambiente de uso.

## Referências

- [Google Drive: download e exportação](https://developers.google.com/workspace/drive/api/guides/manage-downloads)
- [Formatos de exportação](https://developers.google.com/workspace/drive/api/guides/ref-export-formats)
- [Sentence Transformers](https://www.sbert.net/)
- [Modelo multilingual-e5-small](https://huggingface.co/intfloat/multilingual-e5-small)
- [Streamlit](https://docs.streamlit.io/)

## Autor

Desenvolvido por Victor Lima Silva como projeto de aprendizado em Python e aplicação de tecnologia à rotina administrativa.

[Perfil no GitHub](https://github.com/limaavls)