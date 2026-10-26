# Assistente de Procedimentos Administrativos

Aplicação em Python para pesquisar procedimentos administrativos, consultar documentos e gerar respostas opcionais com a Gemini API.

O projeto possui interface de consulta, conversa com contexto limitado, importação de documentos, OCR local para imagens e PDFs digitalizados, busca por palavras, busca semântica local, busca híbrida, sincronização com uma pasta aprovada no Google Drive e respostas com citações verificáveis.

> Projeto de estudo e portfólio. Utilize somente documentos fictícios. A aplicação não representa procedimentos oficiais de uma instituição.

## Objetivo

Aplicar programação a uma necessidade da rotina administrativa: localizar informações em documentos, extrair texto de arquivos digitais e digitalizados, recuperar trechos relevantes por diferentes estratégias, gerar respostas assistidas por inteligência artificial e permitir a conferência das evidências utilizadas.

O desenvolvimento reúne:

```text
processamento de documentos;
OCR local;
busca por palavras;
busca semântica;
busca híbrida;
interface web;
integração com APIs;
automação;
validação local de respostas;
testes automatizados.
```

A aplicação não aprova solicitações nem substitui a conferência dos procedimentos oficiais.

# Funcionalidades

| Recurso | Funcionamento |
| --- | --- |
| Consulta individual | Pesquisa e visualização de trechos e documentos completos. |
| Conversa | Perguntas complementares com memória limitada do assunto. |
| Importação local | Seleção de TXT, PDF, DOCX e imagens pelo painel lateral do chat. |
| Prévia de importação | Conferência do texto antes da inclusão manual. |
| OCR local | Reconhecimento de texto em imagens e páginas digitalizadas de PDFs. |
| PDFs mistos | Usa extração textual nas páginas normais e OCR somente nas páginas sem texto. |
| Busca por palavras | Ordenação por correspondência de termos da pergunta. |
| Busca semântica | Comparação local de embeddings da pergunta e dos trechos. |
| Busca híbrida | Combina os rankings lexical e semântico usando Reciprocal Rank Fusion. |
| Respostas com Gemini | Geração opcional após revisão e autorização. |
| Citações verificáveis | Cada orientação precisa apontar para uma fonte e uma passagem existente no trecho enviado. |
| Fontes por consulta | Referências `F1`, `F2`, `F3` etc. são criadas localmente para cada consulta. |
| Histórico com evidências | O chat preserva uma cópia das fontes utilizadas em cada resposta. |
| Verificação do Drive | Confirmação de acesso e listagem dos itens da pasta. |
| Sincronização do Drive | Criação, atualização e retirada de cópias locais gerenciadas. |
| OCR no Drive | Imagens e PDFs digitalizados compatíveis também podem entrar na base sincronizada. |
| Repetição periódica | Sincronização em intervalos enquanto o programa estiver em execução. |
| Backups locais | Preservação das cópias anteriores antes de alterações. |
| Testes e GitHub Actions | Verificações automatizadas com documentos, respostas e integrações simuladas. |

# Citações verificáveis

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

## Fluxo de validação

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

## O que é conferido localmente

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

## Respostas inválidas

Se o modelo retornar:

```text
JSON inválido;
resposta interrompida;
fonte inexistente;
citação inventada;
orientação sem evidência;
estrutura inesperada.
```

a resposta não é considerada aprovada.

O texto bruto não é apresentado como se fosse uma resposta válida e não é salvo no histórico estruturado.

A aplicação também não realiza automaticamente uma segunda chamada ao Gemini para tentar corrigir a resposta.

## Limite da validação

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

# Localização das fontes

As buscas preservam a posição do trecho dentro do texto original sempre que possível.

O objeto `TrechoCandidato` registra:

```text
texto
inicio
fim
indice_recorte
```

O número de um recorte da busca semântica não é tratado como número de página.

## PDFs

A extração de PDFs preserva marcadores como:

```text
[Página 1]
[Página 2]
[Página 3]
```

Quando uma página possui texto extraível, esse conteúdo é utilizado diretamente.

Quando a página não possui texto extraível, o sistema tenta OCR somente naquela página.

Exemplo:

```text
[Página 2]
[Extração: OCR]
Texto reconhecido na página digitalizada.
```

Isso permite trabalhar também com PDFs mistos:

```text
Página 1 → texto nativo
Página 2 → OCR
Página 3 → texto nativo
Página 4 → OCR
```

O número de página permanece associado ao conteúdo extraído.

Quando os marcadores de página são confiáveis, as citações podem informar:

```text
Página 3
```

ou:

```text
Páginas 3-4
```

## TXT, DOCX, imagens e Google Docs exportado

TXT, DOCX e Google Docs exportados não recebem paginação inventada.

A localização pode ser apresentada como:

```text
Sem paginação neste formato.
```

Imagens também não possuem paginação própria.

O conteúdo reconhecido é armazenado como texto extraído.

# OCR local

A camada de OCR está implementada em:

```text
ocr.py
```

O objetivo é permitir que o assistente trabalhe também com arquivos cujo texto não pode ser obtido diretamente.

O OCR é executado localmente no computador.

A implementação utiliza:

```text
RapidOCR;
ONNX Runtime;
PyMuPDF.
```

## Formatos de imagem aceitos

```text
PNG
JPG
JPEG
BMP
TIF
TIFF
WEBP
```

## PDF digitalizado

Para PDFs, a aplicação tenta primeiro a extração textual normal.

Fluxo:

```text
Página do PDF
      ↓
Existe texto extraível?
   ↙             ↘
 Sim             Não
  ↓               ↓
Usa texto       Renderiza página
nativo            ↓
                  OCR
                   ↓
             Texto reconhecido
```

Assim, o OCR não é executado desnecessariamente em todas as páginas.

## PDFs mistos

Um mesmo PDF pode conter páginas normais e páginas digitalizadas.

Exemplo:

```text
[Página 1]
Texto extraído normalmente.

[Página 2]
[Extração: OCR]
Texto reconhecido pelo OCR.

[Página 3]
Texto extraído normalmente.
```

## Imagens

Imagens são processadas diretamente pelo OCR:

```text
Imagem
   ↓
RapidOCR
   ↓
Texto reconhecido
   ↓
Prévia para revisão
   ↓
Confirmação
   ↓
Cópia TXT na base
```

O conteúdo recebe a indicação:

```text
[Extração: OCR]
```

## Revisão obrigatória

OCR não é considerado uma transcrição perfeita.

Ele pode interpretar incorretamente:

```text
letras;
números;
datas;
pontuação;
acentos;
nomes;
palavras;
valores.
```

A aplicação não faz correção automática do conteúdo reconhecido.

Isso evita transformar uma leitura incerta em texto aparentemente correto.

No painel de importação, o usuário recebe um aviso para conferir o resultado com o documento original antes de adicioná-lo à base.

## Confiança do OCR

O módulo também consegue calcular uma confiança média quando o mecanismo fornece scores válidos.

Essa informação é auxiliar.

Ela não significa que o texto esteja correto e não substitui revisão humana.

## Limites de OCR

Para páginas de PDF:

```text
DPI padrão: 200
DPI permitido: 72 a 300
Limite interno: 25.000.000 de pixels por página renderizada
```

Páginas que excedam os limites são recusadas.

PDFs protegidos por senha continuam sendo recusados.

# Modos de busca

A aplicação possui três estratégias de recuperação de documentos.

```text
Por palavras
Por significado (local)
Híbrida (palavras + significado)
```

As três devolvem o mesmo contrato interno:

```text
documento;
texto original;
lista de TrechoCandidato.
```

Isso permite que citações, Gemini e interfaces funcionem da mesma forma independentemente da busca utilizada.

# Busca por palavras

Implementada em:

```text
busca.py
```

A busca extrai palavras da pergunta, remove alguns termos comuns e ordena os documentos pela quantidade de palavras distintas em comum.

Exemplo:

```text
Pergunta:
Como solicitar material?

Documento A:
Material disponível.

Documento B:
Para solicitar material, informe o setor.

Resultado:
Documento B
Documento A
```

A comparação desconsidera:

```text
maiúsculas;
minúsculas;
acentos.
```

Sinônimos e flexões não são reconhecidos automaticamente.

A busca lexical é especialmente útil quando a pergunta contém:

```text
nomes exatos;
siglas;
códigos;
termos técnicos;
números;
expressões presentes literalmente no documento.
```

Os parágrafos recuperados preservam, quando possível, sua posição no texto original.

# Busca por significado

Implementada em:

```text
busca_semantica.py
```

Utiliza Sentence Transformers com o modelo:

```text
intfloat/multilingual-e5-small
```

A pergunta e os trechos são transformados em embeddings.

Fluxo simplificado:

```text
Pergunta
   ↓
Embedding da pergunta

Documentos
   ↓
Recortes
   ↓
Embeddings dos trechos

      ↓
Comparação vetorial
      ↓
Ranking semântico
```

A busca semântica permite localizar candidatos mesmo quando a pergunta não utiliza exatamente as mesmas palavras do documento.

Ela localiza candidatos, mas não escreve a resposta.

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

O número interno do recorte não é apresentado como número de página.

O modelo é preparado em:

```text
.cache_modelos
```

As pesquisas utilizam a cópia local.

O índice fica na memória do processo.

Ainda não existe banco vetorial persistente.

A similaridade calculada não representa probabilidade de acerto.

# Busca híbrida

Implementada em:

```text
busca_hibrida.py
```

A busca híbrida combina:

```text
busca por palavras
+
busca semântica
```

O objetivo é aproveitar os pontos fortes das duas estratégias.

Fluxo:

```text
                Pergunta
                   ↓
          ┌────────┴────────┐
          ↓                 ↓
 Busca por palavras   Busca semântica
          ↓                 ↓
 Ranking lexical      Ranking vetorial
          └────────┬────────┘
                   ↓
        Reciprocal Rank Fusion
                   ↓
        Ranking híbrido final
                   ↓
             Trechos candidatos
```

## Reciprocal Rank Fusion

A fusão utiliza Reciprocal Rank Fusion, ou RRF.

A implementação não tenta comparar diretamente:

```text
quantidade de palavras encontradas
```

com:

```text
similaridade vetorial.
```

Esses valores possuem significados e escalas diferentes.

Em vez disso, o RRF utiliza a posição do documento em cada ranking.

A contribuição segue a ideia:

```text
peso / (K + posição)
```

Na implementação atual:

```text
RRF_K = 60
PESO_PALAVRAS = 1.0
PESO_SEMANTICA = 1.0
```

Isso significa que os dois mecanismos possuem inicialmente o mesmo peso.

## Documento encontrado pelos dois métodos

Um documento recuperado pelas duas estratégias acumula contribuição dos dois rankings.

Exemplo:

```text
Busca por palavras:
1. documento_A
2. documento_B

Busca semântica:
1. documento_B
2. documento_C
```

O documento B recebe contribuição das duas buscas e pode subir no ranking final.

## Documento encontrado por apenas um método

Ele não é automaticamente descartado.

Um documento pode continuar no resultado quando aparece somente:

```text
na busca lexical;
ou
na busca semântica.
```

Isso evita perder documentos que sejam fortes em apenas uma estratégia.

## Deduplicação

Trechos recuperados pelos dois métodos não são enviados duas vezes.

Quando existem posições confiáveis, a deduplicação considera:

```text
posição inicial;
posição final;
texto.
```

Quando as posições não estão disponíveis, utiliza o texto normalizado somente quanto a espaços.

Não existe correspondência aproximada para deduplicação.

## Prioridade dos trechos

Dentro de cada documento:

```text
trechos encontrados pelos dois métodos aparecem primeiro;
depois entram trechos da busca por palavras;
depois entram trechos da busca semântica;
duplicações são descartadas.
```

## Limites da busca híbrida

Configuração atual:

| Item | Limite |
| --- | --- |
| Documentos finais | Até 3 |
| Trechos por documento | Até 4 |
| Peso lexical | 1.0 |
| Peso semântico | 1.0 |
| Constante RRF | 60 |

Esses parâmetros são regras da demonstração atual.

Eles ainda não foram calibrados com uma base de avaliação de relevância.

## O que a busca híbrida não significa

A posição no ranking híbrido não representa:

```text
probabilidade de resposta correta;
percentual de confiança;
certeza de relevância;
aprovação do conteúdo;
qualidade da interpretação da IA.
```

Por isso as interfaces informam explicitamente:

```text
A busca híbrida combina rankings e não representa
probabilidade de acerto.
```

# Interfaces

## Consulta individual — `interface.py`

A consulta individual permite escolher entre:

```text
Por palavras
Por significado (local)
Híbrida (palavras + significado)
```

O fluxo é:

```text
Escolher o modo
       ↓
Digitar pergunta
       ↓
Pesquisar
       ↓
Conferir documentos e trechos
       ↓
Conferir conteúdo para envio
       ↓
Autorizar o envio
       ↓
Gerar resposta
       ↓
Validar referências
       ↓
Exibir resposta e fontes
```

O modo utilizado é armazenado junto à pesquisa ativa.

Uma nova pesquisa limpa:

```text
resposta anterior;
autorização anterior.
```

A geração continua utilizando o mesmo mecanismo de citações verificáveis.

A busca híbrida altera apenas a recuperação dos candidatos.

Ela não altera as regras de validação da resposta.

## Conversa — `chat.py`

O chat também oferece:

```text
Por palavras
Por significado (local)
Híbrida (palavras + significado)
```

O modo é escolhido antes da conversa.

Depois que existe:

```text
histórico;
ou pergunta pendente;
```

o modo permanece bloqueado.

Para trocar:

```text
Nova conversa
```

Isso evita misturar estratégias diferentes dentro do mesmo contexto sem indicação clara.

## Histórico do modo

A pergunta pendente registra:

```text
modo_busca
```

O turno concluído também preserva:

```text
modo_busca
```

Assim a sessão mantém informação sobre qual estratégia recuperou os candidatos daquela consulta.

## Autorização

Nenhum modo de busca envia conteúdo ao Gemini por conta própria.

```text
buscar documentos ≠ enviar para IA
```

O envio continua dependendo da autorização explícita do usuário.

# Memória da conversa

A preparação utiliza:

```text
a pergunta atual;
a primeira pergunta da conversa;
a pergunta respondida mais recente.
```

As respostas anteriores da IA não são reenviadas como fontes.

Essa memória é limitada.

Referências como:

```text
explique o segundo item da sua resposta
```

podem não funcionar adequadamente.

O histórico fica na sessão do navegador, sem banco de dados persistente, e a versão atual permite até 10 respostas por conversa.

Cada turno concluído armazena uma cópia serializável das fontes citadas.

Isso permite reexibir:

```text
documento;
trecho;
localização;
passagens citadas.
```

sem consultar novamente a versão atual dos arquivos.

# Importação manual de documentos

Disponível no painel lateral do chat.

Fluxo:

```text
Selecionar arquivo
        ↓
Extrair conteúdo
        ↓
OCR quando necessário
        ↓
Revisar texto
        ↓
Confirmar inclusão
        ↓
Salvar cópia TXT local
```

## Formatos aceitos

```text
TXT em UTF-8
PDF
DOCX
PNG
JPG
JPEG
BMP
TIF
TIFF
WEBP
```

## Comportamento por formato

| Formato | Processamento |
| --- | --- |
| TXT | Leitura UTF-8 |
| DOCX | Extração de parágrafos e tabelas |
| PDF com texto | Extração normal |
| PDF digitalizado | OCR nas páginas sem texto |
| PDF misto | Extração normal + OCR seletivo |
| Imagem | OCR local |

## Limites da conversão

| Item | Regra |
| --- | --- |
| Arquivo processado | Até 5 MiB |
| PDF | Até 30 páginas |
| Texto extraído | Até 100.000 caracteres |
| PDF protegido | Recusado |
| Página sem texto | OCR é tentado |
| Página sem texto reconhecível após OCR | Importação é recusada |
| DOCX expandido | Limite interno de 20 MiB |
| DOC antigo | Não aceito |
| Página renderizada para OCR | Até 25 milhões de pixels |

As cópias manuais utilizam o padrão:

```text
documentos/importado_nome_identificador.txt
```

Conteúdos diferentes podem gerar cópias diferentes.

Não há substituição automática de versões nesse modo manual.

# Sincronização com Google Drive

A integração utiliza uma conta de serviço com acesso de leitura a uma pasta exclusiva de demonstração.

## Formatos sincronizados

```text
TXT
PDF
DOCX
Google Docs exportado como texto
PNG
JPG/JPEG
BMP
TIFF
WEBP
```

Imagens compatíveis são baixadas e processadas por OCR local.

PDFs sincronizados também podem utilizar OCR em páginas digitalizadas.

## Fluxo

```text
Google Drive
    ↓
Listagem
    ↓
Seleção dos tipos compatíveis
    ↓
Download
    ↓
Extração / OCR
    ↓
Validação
    ↓
Preparação de todas as cópias
    ↓
Aplicação da base
```

Se um documento compatível falhar antes da aplicação, a sincronização não aplica uma base parcialmente nova.

## Regras da atualização

| Situação | Comportamento |
| --- | --- |
| Arquivo novo | Cria uma cópia local |
| Mesmo ID alterado | Atualiza a cópia correspondente |
| Mesmo conteúdo | Mantém sem duplicação |
| Arquivo deixa a pasta | Retira da base ativa e preserva backup |
| Documento não pode ser lido | Interrompe antes da aplicação |
| OCR falha | Interrompe antes da aplicação |
| Cópia local gerenciada foi editada | Interrompe |
| Arquivo local não gerenciado | Preservado |
| Pasta configurada muda | Interrompe |

## Estado e backups

```text
documentos/drive_identificador.txt
.estado_drive/manifesto.json
.estado_drive/historico/
```

A sincronização não altera arquivos no Google Drive.

# Integração com Gemini

O módulo:

```text
consulta_ia.py
```

prepara os trechos e realiza a chamada ao modelo gerador.

| Item | Limite |
| --- | --- |
| Pergunta digitada | 500 caracteres |
| Documentos enviados | Até três candidatos |
| Contexto | 12.000 caracteres |
| Saída | JSON estruturado |
| Tentativas automáticas extras | Nenhuma |

A recuperação de documentos acontece antes da chamada ao Gemini.

```text
Busca por palavras
Busca semântica
Busca híbrida
        ↓
Trechos candidatos
        ↓
Revisão
        ↓
Autorização
        ↓
Gemini
```

O Gemini não escolhe quais documentos entram inicialmente na busca local.

A resposta retornada também não é confiada diretamente.

Antes da apresentação, `citacoes.py` confere as referências contra o registro local.

# Organização do projeto

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
├── requirements-ocr.txt
├── app.py
├── busca.py
├── busca_semantica.py
├── busca_hibrida.py
├── citacoes.py
├── consulta_ia.py
├── conversa.py
├── importacao.py
├── ocr.py
├── painel_documentos.py
├── interface.py
├── chat.py
├── verificar_drive.py
├── sincronizar_drive.py
├── test_app.py
├── test_busca.py
├── test_busca_semantica.py
├── test_busca_hibrida.py
├── test_citacoes.py
├── test_consulta_ia.py
├── test_conversa.py
├── test_importacao.py
├── test_ocr.py
├── test_painel_documentos.py
├── test_interface.py
├── test_chat.py
├── test_verificar_drive.py
└── test_sincronizar_drive.py
```

Credenciais, modelos, documentos privados e backups não devem ser publicados.

# Instalação no Windows

## Clonar e preparar

```powershell
git clone https://github.com/limaavls/assistente-procedimentos-python.git
cd assistente-procedimentos-python
python -m venv venv
```

## Dependências básicas

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Busca semântica e híbrida

A busca híbrida depende da busca semântica.

Instale:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements-semantica.txt
```

Prepare o modelo:

```powershell
.\venv\Scripts\python.exe busca_semantica.py
```

A busca híbrida reutiliza o mesmo modelo local.

Não existe um segundo modelo específico para ela.

## OCR

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements-ocr.txt
```

Dependências principais:

```text
rapidocr
onnxruntime
PyMuPDF
```

## Google Drive

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements-drive.txt
```

# Configuração local

## Gemini

Crie `.env`:

```env
GEMINI_API_KEY=COLE_SUA_CHAVE_AQUI
```

Opcional:

```env
GEMINI_MODEL=SEU_MODELO
```

## Google Drive

```env
DRIVE_FOLDER_ID=ID_DA_PASTA
DRIVE_CREDENTIALS_FILE=.secrets/google-drive.json
```

# Executar

## Chat

```powershell
.\venv\Scripts\python.exe -m streamlit run chat.py --server.address=127.0.0.1 --browser.gatherUsageStats=false
```

## Consulta individual

```powershell
.\venv\Scripts\python.exe -m streamlit run interface.py --server.address=127.0.0.1 --browser.gatherUsageStats=false
```

## Busca literal pelo terminal

```powershell
.\venv\Scripts\python.exe app.py
```

## Consulta com Gemini pelo terminal

```powershell
.\venv\Scripts\python.exe consulta_ia.py
```

## Sincronização do Drive

```powershell
.\venv\Scripts\python.exe sincronizar_drive.py
```

Modo periódico:

```powershell
.\venv\Scripts\python.exe sincronizar_drive.py --intervalo 300
```

# Testes automatizados

Execute toda a suíte:

```powershell
python -m unittest discover -v
```

A suíte completa foi executada localmente com sucesso após a implementação da busca híbrida.

O número exato de testes deve ser considerado o valor apresentado pela execução atual.

## Testes da busca híbrida

Arquivo:

```text
test_busca_hibrida.py
```

Os cenários incluem:

```text
fusão de documentos presentes nas duas buscas;
documentos recuperados por apenas um mecanismo;
deduplicação de trechos;
preservação de posições;
preservação do índice semântico;
limite de documentos;
limite de trechos;
desempate determinístico;
entrada vazia;
ausência de resultados;
alteração da base durante a fusão;
contratos incompatíveis;
limites inválidos.
```

## Testes de integração

A busca híbrida também é coberta em:

```text
test_chat.py
test_interface.py
```

Esses testes verificam:

```text
presença do terceiro modo;
seleção da busca híbrida;
preservação do modo utilizado;
preparação das citações;
autorização antes da IA;
compatibilidade com respostas validadas;
avisos sobre o limite da fusão.
```

## Testes individuais

Busca híbrida:

```powershell
python -m unittest -v test_busca_hibrida
```

Busca por palavras:

```powershell
python -m unittest -v test_busca
```

Busca semântica:

```powershell
python -m unittest -v test_busca_semantica
```

Chat:

```powershell
python -m unittest -v test_chat
```

Interface:

```powershell
python -m unittest -v test_interface
```

Citações:

```powershell
python -m unittest -v test_citacoes
```

OCR:

```powershell
python -m unittest -v test_ocr
```

Importação:

```powershell
python -m unittest -v test_importacao
```

Painel:

```powershell
python -m unittest -v test_painel_documentos
```

Sincronização:

```powershell
python -m unittest -v test_sincronizar_drive
```

# GitHub Actions

O workflow executa:

```bash
python -m unittest discover -v
```

A suíte deve funcionar sem:

```text
credenciais reais;
acesso real ao Google Drive;
chamadas reais ao Gemini;
documentos privados.
```

Os testes semânticos e híbridos automatizados utilizam simulações quando necessário.

Uma execução verde indica que os cenários configurados passaram.

Isso não significa que toda a aplicação esteja livre de erros.

# Privacidade e limitações

Importação, OCR e buscas são locais.

A sincronização lê os documentos da pasta aprovada e grava suas cópias no computador.

Somente a geração de respostas envia conteúdo ao Gemini.

O usuário pode revisar os trechos antes do envio e precisa autorizar cada consulta.

## A busca híbrida não garante relevância

Mesmo combinando dois métodos, um documento incorreto ainda pode ser selecionado.

O RRF melhora a forma de combinar rankings, mas não prova que:

```text
o primeiro documento é correto;
o trecho é suficiente;
a resposta será correta;
a IA interpretará corretamente o conteúdo.
```

## A busca híbrida ainda não possui avaliação quantitativa

Ainda não existem métricas documentadas como:

```text
Precision@K;
Recall@K;
MRR;
nDCG;
taxa de respostas corretas;
comparação estatística entre os três modos.
```

Esse tipo de avaliação faz parte da evolução planejada do projeto.

## OCR

OCR também não garante transcrição perfeita.

O texto reconhecido precisa ser revisado.

## Citações

Citações verificáveis confirmam a existência da passagem, não a qualidade da interpretação.

## Recursos ainda não existentes

O projeto ainda não possui:

```text
autenticação de usuários;
banco persistente de conversas;
controle institucional de versões;
controle automático de vigência;
banco vetorial persistente;
avaliação automática da qualidade das respostas;
dashboard de métricas;
deploy em Docker;
garantia de resposta correta.
```

# Ciclo de melhorias

| Melhoria | Situação |
| --- | --- |
| Conversa com contexto | Concluída |
| Importação de TXT, PDF e DOCX | Concluída |
| Busca semântica local | Concluída |
| Sincronização de pasta aprovada no Google Drive | Concluída |
| Citações verificáveis | Concluída |
| OCR para PDFs digitalizados e imagens | Concluída |
| Busca híbrida | Concluída |

# Próximas melhorias planejadas

| Ordem | Melhoria | Situação |
| --- | --- | --- |
| 1 | Citações verificáveis | Concluída |
| 2 | OCR para PDFs digitalizados e imagens | Concluída |
| 3 | Busca híbrida | Concluída |
| 4 | Avaliação automática da qualidade da IA | Próxima etapa |
| 5 | Integração com n8n e automações | Planejada |
| 6 | Dashboard de métricas | Planejada |
| 7 | Docker e demonstração online | Planejada |

A próxima etapa será especialmente importante porque permitirá medir, em vez de apenas assumir, a qualidade de:

```text
recuperação de documentos;
citações;
respostas;
comparação entre palavras, semântica e híbrida.
```

# Referências

- Google Gemini API
- Google Drive API
- Sentence Transformers
- `intfloat/multilingual-e5-small`
- RapidOCR
- ONNX Runtime
- PyMuPDF
- Reciprocal Rank Fusion
- Streamlit
- Python `unittest`

# Autor

Desenvolvido por Victor Lima Silva como projeto de aprendizado em Python, inteligência artificial, automação e aplicação de tecnologia à rotina administrativa.

GitHub:

```text
https://github.com/limaavls
```