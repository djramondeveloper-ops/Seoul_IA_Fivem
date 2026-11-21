from __future__ import annotations

from core.models import Project, ResourceInspection


def project_header(project: Project) -> str:
    return (
        f"Projeto: {project.name}. "
        f"Framework: {project.framework}. "
        f"Banco: {project.database}. "
        f"Prefixo custom do usuário: {project.custom_prefix}. "
        f"Observações do projeto: {project.notes or 'nenhuma'}"
    )


def reference_header(project: Project) -> str:
    if project.reference_mode == "none":
        return "Referência de framework: desativada."
    details = [f"Referência de framework: modo {project.reference_mode}."]
    if project.reference_repo_url:
        details.append(f"URL de referência: {project.reference_repo_url}.")
    if project.reference_local_path:
        details.append(f"Clone local de referência informado pelo usuário: {project.reference_local_path}.")
    details.append("A referência é somente apoio de padrão e nunca substitui o código real do projeto atual.")
    return " ".join(details)


def common_guardrails(project: Project) -> str:
    return (
        f"Considere que scripts com prefixo {project.custom_prefix} são scripts custom do usuário. "
        "Ignore qb-*, standalone, PolyZone, npwd, builds e dependências padrão quando a tarefa falar de scripts custom, "
        "a menos que a própria tarefa peça comparação com framework. "
        "Não peça para adicionar arquivos ao chat. "
        "Se o contexto estiver insuficiente, explique isso em texto simples. "
        "Não invente estruturas padrão de FiveM/QBCore sem evidência concreta. "
        "Não altere arquivos sem pedido explícito."
    )


def build_project_analysis_prompt(project: Project) -> str:
    return (
        project_header(project) + " " + reference_header(project) + " " + common_guardrails(project) + " "
        "Analise apenas a estrutura da pasta resources deste projeto. Explique os grupos principais de resources, "
        "os núcleos do framework, as áreas customizadas e os riscos de acoplamento em alto nível. "
        "Não abra arquivos individuais e não altere nada."
    )


def build_custom_resources_prompt(project: Project, custom_resources: list[str]) -> str:
    catalog = "\n".join(f"- {item}" for item in custom_resources) if custom_resources else "- nenhum resource custom encontrado"
    return (
        project_header(project)
        + " "
        + reference_header(project)
        + " "
        + common_guardrails(project)
        + "\n\n"
        + f"Resources customizados detectados com prefixo {project.custom_prefix}:\n{catalog}\n\n"
        + "Analise apenas esses resources listados acima. "
        + "Agrupe por área funcional, diga quais parecem centrais e quais parecem depender de outros. "
        + "Use somente análise estrutural por nomes de resources/pastas listados acima. Não altere nada."
    )


def resource_context_block(inspection: ResourceInspection) -> str:
    bits = [
        f"Resource alvo: {inspection.name}",
        f"Escopo real encontrado: {inspection.rel_path}",
        "Árvore real encontrada:",
        inspection.tree,
    ]
    if inspection.manifest_path:
        bits.append(f"Manifesto detectado no escopo: {inspection.manifest_path}")
    if inspection.manifest_text:
        bits.append("Trecho do manifesto:\n```lua\n" + inspection.manifest_text + "\n```")
    if inspection.structure_summary:
        bits.append("Resumo estrutural automático:\n" + inspection.structure_summary)
    if inspection.scope_strategy:
        bits.append("Estratégia de escopo usada:\n" + inspection.scope_strategy)
    if inspection.context_estimate:
        estimate = inspection.context_estimate
        lines = [
            "Contexto estimado:",
            f"- Tokens estimados: {estimate.get('estimated_tokens', 'n/a')}",
            f"- Orçamento máximo: {estimate.get('max_tokens', 'n/a')}",
            f"- Uso estimado: {estimate.get('usage_percent', 'n/a')}%",
            f"- Status: {inspection.context_status or 'n/a'}",
        ]
        removed = estimate.get("removed_files") or []
        if removed:
            lines.append("Arquivos removidos para proteger contexto:\n- " + "\n- ".join(str(item) for item in removed))
        bits.append("\n".join(lines))
    if inspection.file_summaries_text:
        bits.append("Resumos por arquivo do primeiro passe:\n" + inspection.file_summaries_text)
    if inspection.key_files:
        bits.append("Arquivos-chave confirmados neste escopo:\n" + "\n".join(f"- {item}" for item in inspection.key_files))
    if inspection.context_files:
        bits.append("Arquivos do primeiro passe para leitura profunda:\n" + "\n".join(f"- {item}" for item in inspection.context_files))
    if inspection.warnings:
        bits.append("Observações de escopo:\n" + "\n".join(f"- {item}" for item in inspection.warnings))
    return "\n\n".join(bits)


def build_resource_review_prompt(
    project: Project,
    inspection: ResourceInspection,
    objective: str,
    extra_instructions: str = "",
) -> str:
    extra = f"Instruções extras do usuário: {extra_instructions.strip()}\n" if extra_instructions.strip() else ""
    return (
        project_header(project)
        + " "
        + reference_header(project)
        + " "
        + common_guardrails(project)
        + "\n\n"
        + resource_context_block(inspection)
        + "\n\n"
        + f"Objetivo: {objective}.\n"
        + "Use SOMENTE a árvore, o manifesto, o resumo estrutural, os resumos por arquivo e os arquivos recomendados já informados. "
        + "Não solicite anexar arquivos, não amplie o escopo e não invente caminhos. "
        + "Responda neste formato exato:\n"
        + "1. Estrutura confirmada\n"
        + "2. Função provável de cada parte\n"
        + "3. Dependências explícitas confirmadas\n"
        + "4. Riscos e pontos cegos\n"
        + "5. Oportunidades\n"
        + 'Se algo não puder ser confirmado pelo contexto fornecido, diga explicitamente "não confirmado". '
        + "Não altere nada ainda.\n"
        + extra
    )


def build_debug_prompt(
    project: Project,
    error_text: str,
    inspection: ResourceInspection | None = None,
    extra_instructions: str = "",
) -> str:
    extra = f"Instruções extras do usuário: {extra_instructions.strip()}\n" if extra_instructions.strip() else ""
    context_block = ""
    if inspection is not None:
        context_block = resource_context_block(inspection) + "\n\n"
    return (
        project_header(project)
        + " "
        + reference_header(project)
        + " "
        + common_guardrails(project)
        + "\n\n"
        + context_block
        + "Analise o erro abaixo no contexto do projeto. Monte um plano de investigação seguro em etapas, "
        + "diga onde olhar primeiro, quais arquivos têm mais chance de conter a causa e quais testes rápidos validar antes de alterar código. "
        + "Use a árvore, o manifesto, o resumo estrutural, os resumos por arquivo e os arquivos do primeiro passe quando eles existirem. "
        + "Não altere nada ainda.\n\n"
        + f"Erro:\n{error_text.strip()}\n\n"
        + extra
    )


def build_create_resource_prompt(project: Project, resource_name: str, flavor: str, extra_instructions: str = "") -> str:
    extra = f"Instruções extras do usuário: {extra_instructions.strip()}\n" if extra_instructions.strip() else ""
    return (
        project_header(project)
        + " "
        + reference_header(project)
        + " "
        + common_guardrails(project)
        + "\n\n"
        + f"O resource {resource_name} já foi criado no disco com estrutura base do tipo {flavor}. "
        + "Você deve trabalhar SOMENTE nos arquivos já existentes dentro deste resource, sem recriar a estrutura do zero, sem mover a pasta e sem renomear o resource. "
        + "Considere este resource como o único escopo editável da tarefa. "
        + "Não use require estilo Lua comum para carregar config ou animations em FiveM. "
        + "Não adicione dependências desnecessárias como oxmysql se não houver banco real. "
        + "Não duplique comandos no client e no server sem necessidade. "
        + "Primeiro diga quais arquivos existentes você pretende alterar. "
        + "Só crie arquivo novo se for absolutamente necessário para concluir a lógica solicitada. "
        + "Depois implemente a lógica respeitando o padrão modular de FiveM com client/server/shared e NUI apenas quando já existir ou quando for realmente necessário.\n"
        + extra
    )


def build_framework_compare_prompt(
    project: Project,
    inspection: ResourceInspection,
    extra_instructions: str = "",
) -> str:
    extra = f"Instruções extras do usuário: {extra_instructions.strip()}\n" if extra_instructions.strip() else ""
    return (
        project_header(project)
        + " "
        + reference_header(project)
        + " "
        + common_guardrails(project)
        + "\n\n"
        + resource_context_block(inspection)
        + "\n\n"
        + f"Compare o resource {inspection.name} com o padrão esperado do framework {project.framework}. "
        + "A referência oficial/fork serve apenas como apoio de convenções. Em caso de conflito, o projeto atual do usuário vence. "
        + "Explique diferenças, riscos e quando vale manter o custom atual. Não altere nada.\n"
        + extra
    )


def build_advanced_prompt(project: Project, custom_prompt: str) -> str:
    return project_header(project) + " " + reference_header(project) + " " + common_guardrails(project) + "\n\n" + custom_prompt.strip()


def build_followup_prompt(project: Project, previous_prompt: str, previous_output: str, followup: str) -> str:
    return (
        project_header(project)
        + " "
        + reference_header(project)
        + " "
        + common_guardrails(project)
        + "\n\n"
        + "Contexto da tarefa anterior:\n"
        + f"Prompt anterior:\n{previous_prompt.strip()}\n\n"
        + f"Resposta anterior:\n{previous_output.strip()}\n\n"
        + f"Nova solicitação do usuário:\n{followup.strip()}\n\n"
        + "Continue a partir do contexto acima. Não repita análise genérica. Se for alterar algo, diga primeiro quais arquivos seriam afetados."
    )
