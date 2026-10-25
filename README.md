# Assistente de Procedimentos Administrativos

Aplicação em Python para pesquisar procedimentos administrativos, consultar documentos e gerar respostas opcionais com a Gemini API.

O projeto possui interface de consulta, conversa com contexto limitado, importação de documentos, busca por palavras, busca semântica local, sincronização com uma pasta aprovada no Google Drive e respostas com citações verificáveis.

> Projeto de estudo e portfólio. Utilize somente documentos fictícios. A aplicação não representa procedimentos oficiais de uma instituição.

## Objetivo

Aplicar programação a uma necessidade da rotina administrativa: localizar informações em documentos, gerar respostas assistidas por inteligência artificial e permitir a conferência das evidências utilizadas.

O desenvolvimento reúne processamento de documentos, pesquisa textual e semântica, interface web, integração com APIs, automação, validação local de respostas e testes automatizados.

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
| Citações verificáveis | Cada orientação precisa apontar para uma fonte e uma passagem existente no trecho enviado. |
| Fontes por consulta | Referências `F1`, `F2`, `F3` etc. são criadas localmente para cada consulta. |
| Histórico com evidências | O chat preserva uma cópia das fontes utilizadas em cada resposta. |
| Verificação do Drive | Confirmação de acesso e listagem dos itens da pasta. |
| Sincronização do Drive | Criação, atualização e retirada de cópias locais gerenciadas. |
| Repetição periódica | Sincronização em intervalos enquanto o programa estiver em execução. |
| Backups locais | Preservação das cópias anteriores antes de alterações. |
| Testes e GitHub Actions | Verificações automatizadas com documentos, respostas e integrações simuladas. |

## Citações verificáveis

O módulo `citacoes.py` centraliza a preparação, validação e apresentação das evidências utilizadas pela IA.

Para cada consulta, somente os trechos que realmente serão enviados ao modelo recebem identificadores locais:

```text
F1
F2
F3
...
```

Esses identificadores existem apenas dentro daquela consulta.

`F1` de uma pergunta não representa necessariamente o mesmo documento ou trecho de `F1` em outra pergunta.

### Fluxo de validação

```text
Pergunta
   ↓
Busca local
   ↓
Seleção de documentos e trechos
   ↓
Criação local das fontes F1, F2, F3...
   ↓
Revisão e autorização do usuário
   ↓
Envio ao Gemini
   ↓
Resposta JSON estruturada
   ↓
Validação local das fontes e citações
   ↓
Apresentação da resposta
```

A resposta esperada do modelo segue uma estrutura equivalente a:

```json
{
  "status": "respondida",
  "itens": [
    {
      "texto": "Orientação baseada nos documentos.",
      "evidencias": [
        {
          "fonte_id": "F1",
          "citacao": "Passagem literal existente no trecho enviado."
        }
      ]
    }
  ]
}
```

Os estados aceitos são:

| Status | Significado |
| --- | --- |
| `respondida` | Os itens apresentados possuem evidências. |
| `parcial` | Somente parte da pergunta pôde ser respondida com evidências. |
| `sem_evidencia` | Nenhuma orientação pôde ser fundamentada nos trechos enviados. |

Quando não existe evidência suficiente, a aplicação mostra uma mensagem definida localmente:

```text
Não encontrei essa informação nos trechos consultados.
```

O modelo não pode substituir essa mensagem por uma orientação livre.

### O que é conferido localmente

Antes de uma resposta ser exibida, a aplicação verifica se:

```text
o JSON possui uma estrutura aceita;
o status é permitido;
cada orientação possui pelo menos uma evidência;
o fonte_id pertence à consulta atual;
a citação não está vazia;
a passagem citada existe no trecho relacionado à fonte;
uma resposta sem evidência não contém orientações;
uma resposta respondida ou parcial possui itens fundamentados.
```

A comparação das passagens permite somente normalização de espaços e quebras de linha.

Números, palavras, negações e demais conteúdos não são alterados para tentar fazer uma citação parecer válida.

Por exemplo, se o documento contém:

```text
O prazo é de 5 dias úteis.
```

uma evidência com:

```text
O prazo é de 10 dias úteis.
```

é rejeitada.

Da mesma forma:

```text
O documento não precisa ser assinado.
```

não valida:

```text
O documento precisa ser assinado.
```

### Respostas inválidas

Se o modelo retornar:

```text
JSON inválido;
resposta interrompida;
fonte inexistente;
citação inventada;
orientação sem evidência;
estrutura inesperada;
```

a resposta não é considerada aprovada.

O texto bruto não é apresentado como se fosse uma resposta válida e não é salvo no histórico estruturado.

A aplicação também não realiza automaticamente uma segunda chamada ao Gemini para tentar corrigir a resposta.

### Limite da validação

A validação comprova que:

```text
a referência existe;
a fonte pertence à consulta;
a passagem citada realmente aparece no trecho enviado.
```

Ela não comprova que a interpretação feita pela IA é necessariamente correta.

Por isso a interface apresenta o aviso:

```text
Referências conferidas quanto à existência e ao trecho.
A interpretação da resposta ainda exige revisão.
```

## Localização das fontes

As buscas passaram a preservar a posição do trecho dentro do texto original sempre que possível.

O objeto `TrechoCandidato` registra:

```text
texto
inicio
fim
indice_recorte
```

O número de um recorte da busca semântica não é tratado como número de página.

### PDF

Quando o texto extraído possui marcadores confiáveis de página, a aplicação pode informar:

```text
Página 3
```

ou:

```text
Páginas 3-4
```

Se a associação não puder ser determinada:

```text
Página não determinada (metadados insuficientes).
```

### TXT, DOCX e Google Docs exportado

Esses formatos não recebem paginação inventada.

A localização é apresentada como:

```text
Sem paginação neste formato.
```

Documentos convertidos continuam sendo identificados como texto extraído, e não como representação visual do arquivo original.

## Fontes citadas e documentos recuperados

A aplicação diferencia:

```text
documentos encontrados pela busca;
fontes realmente utilizadas pela resposta.
```

Uma seção `Fontes citadas` apresenta as referências efetivamente utilizadas.

Ela pode mostrar:

```text
identificador;
documento;
localização disponível;
trecho enviado;
passagem citada;
indicação de conteúdo extraído;
link do Drive quando derivado de metadados confiáveis.
```

Documentos recuperados pela busca mas não utilizados pela resposta são separados dos documentos citados.

Links externos não são aceitos a partir de texto inventado pelo modelo.

Para cópias sincronizadas do Google Drive, um endereço só pode ser construído quando existe um ID de Drive reconhecido nos metadados locais.

## Interfaces

### Consulta individual — `interface.py`

Permite pesquisar uma pergunta, visualizar os parágrafos recuperados, consultar o conteúdo disponível dos documentos e gerar uma resposta opcional.

Essa interface utiliza a busca por palavras.

O fluxo é:

```text
Digitar pergunta
      ↓
Pesquisar localmente
      ↓
Conferir documentos e trechos
      ↓
Conferir o conteúdo que será enviado
      ↓
Autorizar o envio
      ↓
Gerar resposta
      ↓
Validar referências
      ↓
Exibir resposta e fontes
```

A resposta validada é armazenada na sessão juntamente com uma cópia das evidências daquela consulta.

Uma alteração posterior dos arquivos não modifica a evidência já apresentada.

### Conversa — `chat.py`

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
Gerar resposta estruturada
        ↓
Validar referências localmente
        ↓
Exibir resposta e fontes
```

Pesquisar, importar ou sincronizar documentos não chama o Gemini.

Cada geração de resposta exige autorização separada.

Use `Nova conversa` para trocar de assunto, mudar o modo de busca ou consultar uma base atualizada pela sincronização.

## Memória da conversa

A preparação utiliza:

```text
a pergunta atual;
a primeira pergunta da conversa;
a pergunta respondida mais recente.
```

As respostas anteriores da IA não são reenviadas como fontes.

Essa memória é limitada. Referências como:

```text
explique o segundo item da sua resposta
```

podem não funcionar adequadamente.

O histórico fica na sessão do navegador, sem banco de dados, e a versão atual permite até 10 respostas por conversa.

Cada turno concluído armazena uma cópia serializável das fontes citadas.

Isso permite reexibir:

```text
documento;
trecho;
localização;
passagens citadas;
```

sem consultar novamente a versão atual dos arquivos.

Uma pergunta já preparada não é atualizada automaticamente quando a base muda.

## Modos de busca

### Por palavras

Implementado em `busca.py`.

Extrai palavras da consulta, ignora alguns termos comuns e ordena os documentos pela quantidade de palavras distintas em comum.

A comparação desconsidera acentos e maiúsculas.

Sinônimos e flexões não são reconhecidos automaticamente.

Os parágrafos recuperados preservam, quando possível, sua posição no texto de origem.

### Por significado — local

Implementado em `busca_semantica.py`.

Utiliza Sentence Transformers com o modelo:

```text
intfloat/multilingual-e5-small
```

O modelo transforma textos em embeddings e compara a pergunta com os trechos disponíveis.

Ele localiza candidatos, mas não escreve a resposta.

| Configuração | Limite |
| --- | --- |
| Execução | Processador do computador |
| Recortes | Até 300 tokens |
| Sobreposição | 50 tokens |
| Base da demonstração | Até 500 trechos |
| Seleção | Até três documentos |
| Trechos por documento | Até dois |
| Atualização do índice | Na próxima pesquisa, quando a base mudar |

Os recortes preservam:

```text
texto;
posição inicial;
posição final;
número interno do recorte.
```

O número interno do recorte é usado somente pela busca e não é apresentado como número de página.

O modelo é preparado em:

```text
.cache_modelos
```

As pesquisas utilizam a cópia local.

O índice fica na memória do processo e ainda não é um banco vetorial persistente.

Não existe um limiar de relevância validado.

Uma pergunta sem relação com a base também pode receber documentos candidatos.

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

Formatos aceitos atualmente:

```text
TXT em UTF-8;
PDF com texto extraível;
DOCX.
```

A extração atual não utiliza OCR e não preserva todos os elementos visuais ou especiais do original.

### Limites da conversão

| Item | Regra |
| --- | --- |
| Arquivo processado | Até 5 MiB |
| PDF | Até 30 páginas |
| Texto extraído | Até 100.000 caracteres |
| PDF protegido | Recusado |
| Página de PDF sem texto extraível | O arquivo inteiro é recusado |
| DOCX expandido | Limite interno de 20 MiB |
| DOC antigo | Não aceito |

As cópias manuais utilizam o padrão:

```text
documentos/importado_nome_identificador.txt
```

Conteúdos diferentes podem gerar cópias diferentes.

Não há substituição automática de versões nesse modo manual.

Para documentos convertidos, a consulta apresenta o texto extraído, não a aparência original do arquivo.

A próxima melhoria planejada do projeto é acrescentar OCR para documentos digitalizados e imagens.

## Sincronização com Google Drive

A integração utiliza uma conta de serviço com acesso de leitura a uma pasta exclusiva de demonstração.

### Verificação de acesso

`verificar_drive.py` confirma a pasta e lista os itens diretamente dentro dela.

Essa operação consulta metadados sem baixar o conteúdo.

### Sincronização

`sincronizar_drive.py` lê os documentos compatíveis e mantém cópias TXT na base local.

Formatos suportados nesta etapa:

```text
TXT;
PDF;
DOCX;
Google Docs exportado como texto.
```

Planilhas, apresentações, imagens, atalhos, outros formatos e subpastas não são processados.

A seleção considera o tipo de arquivo informado pelo Drive.

### Regras da atualização

| Situação | Comportamento |
| --- | --- |
| Arquivo novo | Cria uma cópia local |
| Mesmo ID com conteúdo ou nome alterado | Atualiza a cópia correspondente |
| Mesmo conteúdo já sincronizado | Mantém a cópia, sem duplicá-la |
| Arquivo deixa de aparecer na pasta | Retira a cópia gerenciada da base ativa e preserva backup |
| Documento compatível não pode ser lido | Interrompe antes de aplicar as novas cópias |
| Cópia gerenciada editada manualmente | Interrompe para evitar sobrescrever a edição |
| Arquivo local não gerenciado | Não é removido pela rotina |
| Pasta configurada muda | Interrompe para evitar misturar duas bases |

O ID identifica o documento.

Criar outro arquivo com o mesmo nome não equivale a editar o mesmo documento.

A ausência na listagem não comprova que um arquivo foi excluído: ele também pode ter sido movido ou deixado de ser visível para a conta utilizada.

### Cópias, controle e backups

```text
documentos/drive_identificador.txt
.estado_drive/manifesto.json
.estado_drive/historico/
```

O cabeçalho de cada cópia informa o nome original e o ID do Drive.

Não edite os arquivos gerenciados nem o manifesto manualmente.

Os backups ficam fora da pasta pesquisada, mas permanecem no computador.

Não há limpeza automática do histórico.

A sincronização não altera arquivos no Google Drive.

### Limites e comportamento em falhas

A demonstração aceita até 30 documentos compatíveis por execução.

A listagem reutilizada aceita até 200 itens na pasta.

Os limites de extração existentes continuam sendo aplicados.

Exportações do Google Docs também passam pela validação do texto recebido.

Todos os documentos compatíveis são lidos novamente em cada ciclo.

Ainda não existe uma otimização para baixar apenas arquivos modificados.

A gravação utiliza arquivos temporários e tenta restaurar as cópias anteriores se ocorrer uma falha durante a aplicação das mudanças.

Isso não constitui uma transação de toda a base.

Falta de energia, encerramento forçado, problemas de disco ou falha na restauração podem exigir recuperação manual.

Uma pasta `em_execucao` impede duas sincronizações simultâneas.

Se ela permanecer após um encerramento inesperado, confira os processos e os backups antes de qualquer remoção manual.

Se a consulta ao Drive falhar, não presuma que a base está atualizada.

Cópias antigas podem continuar disponíveis.

### Atualização no chat

A sincronização não modifica uma pergunta que já esteja aguardando autorização.

Respostas concluídas preservam as evidências utilizadas no momento da consulta e não são reconstruídas a partir da nova versão da base.

Espere a conclusão da sincronização e clique em `Nova conversa` antes de consultar o conteúdo atualizado.

O índice semântico percebe mudanças na base na próxima pesquisa.

## Integração com Gemini

O módulo `consulta_ia.py` prepara os trechos e realiza a chamada ao modelo gerador.

| Item | Limite |
| --- | --- |
| Pergunta digitada | 500 caracteres |
| Documentos enviados | Até três candidatos |
| Contexto dos documentos | 12.000 caracteres, incluindo identificação das fontes |
| Saída | JSON estruturado |
| Tentativas automáticas extras | Nenhuma |

No chat, o pedido também inclui perguntas anteriores selecionadas.

Importação, sincronização, busca e envio à IA possuem limites diferentes.

Um arquivo aceito pode gerar contexto grande demais para uma consulta.

A integração solicita ao Gemini que cada orientação possua evidências estruturadas.

A resposta retornada pelo modelo não é confiada diretamente.

Antes da apresentação, `citacoes.py` confere as referências contra o registro local da consulta.

## Organização do projeto

```text
assistente-procedimentos-python/
├── .github/
│   └── workflows/
│       └── testes.yml
├── documentos/
├── .secrets/
├── .estado_drive/
├── .cache_modelos/
├── .gitignore
├── README.md
├── requirements.txt
├── requirements-semantica.txt
├── requirements-drive.txt
├── app.py
├── busca.py
├── busca_semantica.py
├── citacoes.py
├── consulta_ia.py
├── conversa.py
├── importacao.py
├── painel_documentos.py
├── interface.py
├── chat.py
├── verificar_drive.py
├── sincronizar_drive.py
├── test_app.py
├── test_busca.py
├── test_busca_semantica.py
├── test_citacoes.py
├── test_consulta_ia.py
├── test_conversa.py
├── test_importacao.py
├── test_interface.py
├── test_chat.py
├── test_verificar_drive.py
└── test_sincronizar_drive.py
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

Os comandos seguintes chamam diretamente o Python do ambiente.

Se sua pasta se chama `.venv`, ajuste os caminhos.

### Dependências básicas

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Incluem Streamlit, `google-genai`, `python-dotenv`, `httpx`, `pypdf` e `python-docx`.

### Busca semântica opcional

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements-semantica.txt
.\venv\Scripts\python.exe busca_semantica.py
```

A segunda execução prepara o modelo.

O download do modelo é autorizado explicitamente por esse comando.

As consultas normais utilizam a cópia local.

### Google Drive opcional

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements-drive.txt
```

Esse arquivo acrescenta:

```text
google-api-python-client
google-auth
google-auth-httplib2
```

## Configuração local

### Gemini

Crie um arquivo `.env`:

```env
GEMINI_API_KEY=COLE_SUA_CHAVE_AQUI
```

O modelo gerador pode ser definido opcionalmente:

```env
GEMINI_MODEL=SEU_MODELO
```

Quando ausente, utiliza-se `MODELO_PADRAO` de `consulta_ia.py`.

O modelo de geração é independente do modelo semântico local.

### Google Drive

Ative a Google Drive API no projeto Google Cloud, crie uma conta de serviço dedicada e compartilhe somente a pasta de demonstração como Leitor/Visualizador.

Guarde a credencial em:

```text
.secrets/google-drive.json
```

Acrescente ao `.env`:

```env
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

Os comandos iniciam a aplicação localmente.

Não publicam a ferramenta na internet.

Para encerrar:

```text
Ctrl + C
```

### Busca literal pelo terminal

```powershell
.\venv\Scripts\python.exe app.py
```

### Consulta com IA pelo terminal

```powershell
.\venv\Scripts\python.exe consulta_ia.py
```

A consulta pelo terminal também utiliza o registro local de fontes e a validação das citações.

## Executar a sincronização

### Confirmar acesso

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

O terminal precisa permanecer aberto.

O computador precisa estar ligado e conectado à internet.

Esse comando não instala um serviço nem configura inicialização automática no Windows.

Utilize outro terminal para executar o chat.

Para encerrar:

```text
Ctrl + C
```

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

O `.gitignore` não remove automaticamente arquivos já registrados.

Se uma credencial for exposta, revogue-a e crie outra.

## Testes automatizados

Execute toda a suíte:

```powershell
.\venv\Scripts\python.exe -m unittest discover -v
```

Na conclusão da melhoria de citações verificáveis, a suíte completa executada localmente apresentou:

```text
Ran 134 tests in ...

OK
```

A suíte inclui testes para:

```text
carregamento e busca local;
busca por palavras;
posições dos trechos;
busca semântica;
recortes e sobreposição;
importação de documentos;
conversa com contexto;
preparação das fontes;
validação de citações;
JSON inválido;
respostas interrompidas;
fontes inexistentes;
citações inventadas;
alteração de números e negações;
estados respondida, parcial e sem_evidencia;
histórico com evidências;
consulta individual;
chat;
autorização explícita;
falhas simuladas da API;
sincronização com Google Drive;
backups e restauração;
verificação de acesso ao Drive.
```

Arquivos específicos da melhoria de citações:

```text
test_citacoes.py
test_consulta_ia.py
test_interface.py
test_chat.py
test_busca.py
test_busca_semantica.py
```

Os testes do Gemini utilizam mocks e respostas simuladas.

Eles não precisam enviar documentos ou perguntas reais ao provedor.

Os testes semânticos utilizam um modelo simulado e não comprovam a qualidade do modelo real.

As respostas do Drive e os downloads também são simulados.

### Testes individuais úteis

Citações:

```powershell
python -m unittest -v test_citacoes
```

Busca por palavras:

```powershell
python -m unittest -v test_busca
```

Busca semântica:

```powershell
python -m unittest -v test_busca_semantica
```

Gemini e validação:

```powershell
python -m unittest -v test_consulta_ia
```

Interface individual:

```powershell
python -m unittest -v test_interface
```

Chat:

```powershell
python -m unittest -v test_chat
```

Conversa:

```powershell
python -m unittest -v test_conversa
```

Sincronização:

```powershell
python -m unittest -v test_sincronizar_drive
```

### Limites da cobertura

A suíte não comprova:

```text
qualidade das respostas reais da IA;
qualidade semântica do modelo real;
correção da interpretação feita pelo Gemini;
autenticação real do Google;
todas as condições de rede, disco ou sistema operacional.
```

Uma quantidade de testes não representa uma porcentagem de cobertura.

## GitHub Actions

O workflow instala as dependências básicas e executa:

```bash
python -m unittest discover -v
```

A suíte deve funcionar sem credenciais reais, sem acesso ao Google Drive e sem chamadas reais ao Gemini.

Uma execução verde indica que os cenários configurados passaram.

Isso não significa que toda a aplicação esteja livre de erros.

## Privacidade e limitações

A importação e as buscas são locais.

A sincronização lê os documentos da pasta aprovada e grava suas cópias no computador.

Somente a geração de respostas envia conteúdo ao Gemini.

Antes do envio, o usuário pode conferir os trechos selecionados e precisa autorizar explicitamente cada consulta.

Confira os termos, cotas e condições da conta utilizada.

Cópias retiradas da base permanecem nos backups locais.

Excluir um documento no Drive não elimina automaticamente:

```text
backups anteriores;
informações já enviadas a serviços externos;
evidências preservadas no histórico de uma sessão.
```

O projeto não possui atualmente:

```text
criptografia dos documentos;
autenticação de usuários;
isolamento da base por pessoa;
banco de dados de conversas;
controle institucional de versões;
controle automático de vigência;
OCR;
garantia de resposta correta.
```

Documentos importados manualmente podem duplicar conteúdos também sincronizados do Drive.

A sincronização não elimina essas importações independentes.

A validação de citações não transforma uma resposta de IA em verdade comprovada.

Ela verifica somente a relação entre a referência, a passagem citada e os trechos enviados.

O projeto não apresenta resultados medidos de economia de tempo ou precisão em uma rotina administrativa real.

## Ciclo de melhorias já implementado

| Melhoria | Situação |
| --- | --- |
| Conversa com contexto | Implementada |
| Importação de TXT, PDF e DOCX | Implementada |
| Busca semântica local | Implementada |
| Sincronização de pasta aprovada no Google Drive | Implementada |
| Citações verificáveis | Implementada e validada com a suíte automatizada |

## Próximas melhorias planejadas

A evolução planejada será feita uma etapa por vez:

| Ordem | Melhoria | Situação |
| --- | --- | --- |
| 1 | Citações verificáveis | Concluída |
| 2 | OCR para PDFs digitalizados e imagens | Próxima etapa |
| 3 | Busca híbrida | Planejada |
| 4 | Avaliação automática da qualidade da IA | Planejada |
| 5 | Integração com n8n e automações | Planejada |
| 6 | Dashboard de métricas | Planejada |
| 7 | Docker e demonstração online | Planejada |

Cada etapa deve manter testes automatizados, compatibilidade com as funcionalidades existentes e documentação atualizada.

## Referências

- Google Gemini API
- Google Drive API
- Sentence Transformers
- Modelo `intfloat/multilingual-e5-small`
- Streamlit
- Python `unittest`

## Autor

Desenvolvido por Victor Lima Silva como projeto de aprendizado em Python, inteligência artificial, automação e aplicação de tecnologia à rotina administrativa.

GitHub:

```
https://github.com/limaavls
```