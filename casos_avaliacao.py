from pathlib import Path

from avaliacao import CasoAvaliacao


DOCUMENTOS_AVALIACAO = [
    (
        Path("material.txt"),
        (
            "SOLICITAÇÃO DE MATERIAL\n\n"
            "Para solicitar material, o colaborador deve informar "
            "o setor solicitante, a descrição do item e a quantidade "
            "necessária.\n\n"
            "A solicitação deve ser encaminhada ao setor de Compras."
        ),
    ),
    (
        Path("frequencia.txt"),
        (
            "CORREÇÃO DE FREQUÊNCIA\n\n"
            "Para corrigir uma frequência, informe a data da ocorrência, "
            "o horário correto e a justificativa.\n\n"
            "A solicitação deve ser encaminhada ao RH."
        ),
    ),
    (
        Path("reembolso.txt"),
        (
            "REEMBOLSO DE DESPESAS\n\n"
            "O pedido de reembolso deve conter a nota fiscal, "
            "o comprovante de pagamento e a justificativa da despesa.\n\n"
            "O pedido deve ser encaminhado ao setor Financeiro."
        ),
    ),
    (
        Path("ferias.txt"),
        (
            "SOLICITAÇÃO DE FÉRIAS\n\n"
            "O pedido de férias deve informar o período desejado "
            "e ser encaminhado ao gestor responsável.\n\n"
            "Depois da aprovação do gestor, o RH realiza "
            "o processamento da solicitação."
        ),
    ),
    (
        Path("acesso.txt"),
        (
            "SOLICITAÇÃO DE ACESSO AO SISTEMA\n\n"
            "Para solicitar acesso ao sistema, informe o nome do usuário, "
            "o setor, o perfil de acesso necessário e a justificativa.\n\n"
            "A solicitação deve ser encaminhada à equipe de TI."
        ),
    ),
    (
        Path("equipamento.txt"),
        (
            "EMPRÉSTIMO DE EQUIPAMENTO\n\n"
            "Para retirar um equipamento emprestado, informe "
            "o patrimônio, o responsável pela retirada e a data prevista "
            "para devolução.\n\n"
            "O controle é realizado pelo setor Administrativo."
        ),
    ),
]


CASOS_AVALIACAO = [
    CasoAvaliacao(
        identificador="material_001",
        pergunta=(
            "Como faço para pedir materiais "
            "para o meu setor?"
        ),
        documentos_esperados=(
            "material.txt",
        ),
        termos_obrigatorios=(
            "setor",
            "descrição",
            "quantidade",
            "Compras",
        ),
        termos_proibidos=(
            "prazo de",
            "RH",
        ),
        status_esperado="respondida",
    ),
    CasoAvaliacao(
        identificador="material_002",
        pergunta=(
            "Quais informações preciso fornecer "
            "numa solicitação de material?"
        ),
        documentos_esperados=(
            "material.txt",
        ),
        termos_obrigatorios=(
            "setor",
            "descrição",
            "quantidade",
        ),
        termos_proibidos=(
            "nota fiscal",
        ),
        status_esperado="respondida",
    ),
    CasoAvaliacao(
        identificador="frequencia_001",
        pergunta=(
            "Como corrigir meu registro de horário?"
        ),
        documentos_esperados=(
            "frequencia.txt",
        ),
        termos_obrigatorios=(
            "data",
            "horário",
            "justificativa",
            "RH",
        ),
        termos_proibidos=(
            "Compras",
        ),
        status_esperado="respondida",
    ),
    CasoAvaliacao(
        identificador="frequencia_002",
        pergunta=(
            "Errei o ponto. O que preciso informar?"
        ),
        documentos_esperados=(
            "frequencia.txt",
        ),
        termos_obrigatorios=(
            "data",
            "horário",
            "justificativa",
        ),
        termos_proibidos=(
            "nota fiscal",
        ),
        status_esperado="respondida",
    ),
    CasoAvaliacao(
        identificador="reembolso_001",
        pergunta=(
            "Quais comprovantes preciso apresentar "
            "para receber uma despesa de volta?"
        ),
        documentos_esperados=(
            "reembolso.txt",
        ),
        termos_obrigatorios=(
            "nota fiscal",
            "comprovante de pagamento",
            "justificativa",
        ),
        termos_proibidos=(
            "patrimônio",
        ),
        status_esperado="respondida",
    ),
    CasoAvaliacao(
        identificador="reembolso_002",
        pergunta=(
            "Como pedir reembolso?"
        ),
        documentos_esperados=(
            "reembolso.txt",
        ),
        termos_obrigatorios=(
            "nota fiscal",
            "comprovante de pagamento",
            "Financeiro",
        ),
        termos_proibidos=(
            "RH",
        ),
        status_esperado="respondida",
    ),
    CasoAvaliacao(
        identificador="ferias_001",
        pergunta=(
            "Como solicitar férias?"
        ),
        documentos_esperados=(
            "ferias.txt",
        ),
        termos_obrigatorios=(
            "período",
            "gestor",
        ),
        termos_proibidos=(
            "nota fiscal",
        ),
        status_esperado="respondida",
    ),
    CasoAvaliacao(
        identificador="ferias_002",
        pergunta=(
            "Quero me ausentar por férias. "
            "Quem precisa aprovar?"
        ),
        documentos_esperados=(
            "ferias.txt",
        ),
        termos_obrigatorios=(
            "gestor",
        ),
        termos_proibidos=(
            "TI",
        ),
        status_esperado="respondida",
    ),
    CasoAvaliacao(
        identificador="acesso_001",
        pergunta=(
            "Preciso de permissão para entrar "
            "em um sistema da empresa."
        ),
        documentos_esperados=(
            "acesso.txt",
        ),
        termos_obrigatorios=(
            "usuário",
            "setor",
            "perfil",
            "justificativa",
            "TI",
        ),
        termos_proibidos=(
            "Financeiro",
        ),
        status_esperado="respondida",
    ),
    CasoAvaliacao(
        identificador="acesso_002",
        pergunta=(
            "Quais dados devo informar para conseguir "
            "acesso ao sistema?"
        ),
        documentos_esperados=(
            "acesso.txt",
        ),
        termos_obrigatorios=(
            "nome",
            "setor",
            "perfil",
            "justificativa",
        ),
        termos_proibidos=(
            "patrimônio",
        ),
        status_esperado="respondida",
    ),
    CasoAvaliacao(
        identificador="equipamento_001",
        pergunta=(
            "Como pegar um equipamento emprestado?"
        ),
        documentos_esperados=(
            "equipamento.txt",
        ),
        termos_obrigatorios=(
            "patrimônio",
            "responsável",
            "devolução",
        ),
        termos_proibidos=(
            "nota fiscal",
        ),
        status_esperado="respondida",
    ),
    CasoAvaliacao(
        identificador="equipamento_002",
        pergunta=(
            "Preciso retirar um equipamento da empresa "
            "temporariamente. O que devo registrar?"
        ),
        documentos_esperados=(
            "equipamento.txt",
        ),
        termos_obrigatorios=(
            "patrimônio",
            "responsável",
            "data",
            "devolução",
        ),
        termos_proibidos=(
            "Compras",
        ),
        status_esperado="respondida",
    ),
]