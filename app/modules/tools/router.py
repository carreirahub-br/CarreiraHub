from fastapi import APIRouter, Request
from pydantic import ValidationError

from app.core.templating import templates
from app.modules.home.service import ToolCard
from app.modules.tools.schemas import (
    FeriasInput,
    InssInput,
    IrrfInput,
    RescisaoInput,
    RestituicaoInput,
)
from app.modules.tools.service import (
    AVISO_PREVIO_OPTIONS,
    RESCISAO_TYPES,
    compute_ferias,
    compute_inss,
    compute_irrf,
    compute_rescisao,
    compute_restituicao,
    tabela_inss,
    tabela_irrf_anual,
    tabela_irrf_mensal,
)

router = APIRouter()

ACTIVE_TOOLS = (
    ToolCard(
        slug="ferias",
        name="Calculadora de férias",
        description="Calcule dias de descanso, 1/3 constitucional, abono pecuniário e o valor líquido estimado.",
        icon="calendar",
        available=True,
        path="/ferramentas/ferias",
        cta="Calcular férias",
    ),
    ToolCard(
        slug="rescisao",
        name="Simulador de rescisão",
        description="Estime saldo de salário, aviso prévio, 13º e férias proporcionais e a multa do FGTS.",
        icon="scale",
        available=True,
        path="/ferramentas/rescisao",
        cta="Simular rescisão",
    ),
    ToolCard(
        slug="inss",
        name="Calculadora de INSS",
        description="Calcule a contribuição mensal do INSS com a tabela progressiva de 2026 e o salário líquido estimado.",
        icon="wallet",
        available=True,
        path="/ferramentas/inss",
        cta="Calcular INSS",
    ),
    ToolCard(
        slug="imposto-de-renda",
        name="Calculadora de imposto de renda",
        description="Veja quanto de IRRF você vai pagar no mês com a tabela de 2026 e a redução da Lei 15.270/2025.",
        icon="calculator",
        available=True,
        path="/ferramentas/imposto-de-renda",
        cta="Calcular IRRF",
    ),
    ToolCard(
        slug="restituicao-ir",
        name="Simulador de restituição do IR",
        description="Descubra se você recebe restituição ou fica devendo imposto de renda na declaração anual de 2026.",
        icon="file",
        available=True,
        path="/ferramentas/restituicao-ir",
        cta="Simular restituição",
    ),
)

UPCOMING_TOOLS = (
    ("Criador de currículo", "Currículo profissional com exportação em PDF."),
    ("Analisador de currículo ATS", "Sugestões de estrutura e palavras-chave."),
    ("Calculadora de salário líquido", "Descontos e valor líquido a partir do bruto."),
    ("Preparação para entrevistas", "Roteiros e perguntas frequentes."),
)

META = {
    "ferramentas": {
        "title": "Ferramentas de carreira",
        "description": "Calculadoras gratuitas de férias e de rescisão trabalhista, com valores estimados para o trabalhador.",
    },
    "rescisao": {
        "title": "Simulador de rescisão",
        "description": "Estime saldo de salário, aviso prévio, 13º e férias proporcionais e a multa do FGTS numa rescisão de contrato CLT.",
    },
    "ferias": {
        "title": "Calculadora de férias",
        "description": "Calcule férias, 1/3 constitucional, abono pecuniário e o valor líquido estimado das suas férias.",
    },
    "inss": {
        "title": "Calculadora de INSS",
        "description": "Calcule a contribuição do INSS com a tabela progressiva de 2026 e estime o seu salário líquido.",
    },
    "imposto-de-renda": {
        "title": "Calculadora de imposto de renda",
        "description": "Calcule o IRRF do mês com a tabela de 2026 e a redução da Lei 15.270/2025 para salários até R$ 7.350.",
    },
    "restituicao-ir": {
        "title": "Simulador de restituição do imposto de renda",
        "description": "Descubra se você vai receber restituição ou pagar imposto de renda na declaração anual.",
    },
}

MSG_MAP = {
    "Input should be a valid number": "Informe um valor numérico válido (use ponto para os centavos).",
    "Input should be a valid date": "As datas devem ser válidas, no formato aaaa-mm-dd.",
    "Input should be a valid integer": "Informe números inteiros válidos.",
    "Input should be a value able to be converted to a float": "Informe um valor numérico válido (use ponto para os centavos).",
}


def _clean_number(raw) -> str:
    if raw is None:
        return ""
    text = str(raw).strip().replace("R$", "").replace(" ", "")
    if not text:
        return ""
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    return text


def _friendly(exc: ValidationError) -> str:
    messages = []
    for err in exc.errors():
        msg = err["msg"]
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, "):]
        else:
            msg = MSG_MAP.get(msg, msg)
        messages.append(msg)
    return "\n".join(dict.fromkeys(messages))


def _page_context(key: str, path: str) -> dict:
    meta = META[key]
    return {
        "meta_title": f"{meta['title']} | CarreiraHub",
        "meta_description": meta["description"],
        "canonical_path": path,
        "og_type": "website",
    }


def _rescisao_context(form: dict) -> dict:
    ctx = _page_context("rescisao", "/ferramentas/rescisao")
    ctx["form"] = {
        "salario_bruto": form.get("salario_bruto", ""),
        "data_admissao": form.get("data_admissao", ""),
        "data_demissao": form.get("data_demissao", ""),
        "tipo_rescisao": form.get("tipo_rescisao", "sem_justa_causa"),
        "aviso_previo": form.get("aviso_previo", "indenizado"),
        "dias_ferias_vencidas": form.get("dias_ferias_vencidas", "0"),
    }
    ctx["rescisao_types"] = RESCISAO_TYPES
    ctx["aviso_options"] = AVISO_PREVIO_OPTIONS
    return ctx


def _ferias_context(form: dict) -> dict:
    ctx = _page_context("ferias", "/ferramentas/ferias")
    checked = bool(form.get("vender_abono"))
    ctx["form"] = {
        "salario_bruto": form.get("salario_bruto", ""),
        "media_adicionais": form.get("media_adicionais", ""),
        "dias_gozados": form.get("dias_gozados", "30"),
        "vender_abono": checked,
        "dias_abono": form.get("dias_abono", "10"),
    }
    return ctx


def _inss_context(form: dict) -> dict:
    ctx = _page_context("inss", "/ferramentas/inss")
    ctx["form"] = {"salario_bruto": form.get("salario_bruto", "")}
    ctx["tabela"] = tabela_inss()
    return ctx


def _irrf_context(form: dict) -> dict:
    ctx = _page_context("imposto-de-renda", "/ferramentas/imposto-de-renda")
    ctx["form"] = {
        "salario_bruto": form.get("salario_bruto", ""),
        "dependentes": form.get("dependentes", "0"),
    }
    ctx["tabela"] = tabela_irrf_mensal()
    return ctx


def _restituicao_context(form: dict) -> dict:
    ctx = _page_context("restituicao-ir", "/ferramentas/restituicao-ir")
    ctx["form"] = {
        "rendimentos_anuais": form.get("rendimentos_anuais", ""),
        "dependentes": form.get("dependentes", "0"),
        "despesas_ensino": form.get("despesas_ensino", ""),
        "despesas_medicas": form.get("despesas_medicas", ""),
        "pensao_alimenticia": form.get("pensao_alimenticia", ""),
        "contribuicao_inss": form.get("contribuicao_inss", ""),
        "ir_retido_fonte": form.get("ir_retido_fonte", ""),
    }
    ctx["tabela"] = tabela_irrf_anual()
    return ctx


@router.get("/ferramentas", include_in_schema=False)
def ferramentas_index(request: Request):
    ctx = _page_context("ferramentas", "/ferramentas")
    ctx["tools"] = ACTIVE_TOOLS
    ctx["upcoming"] = UPCOMING_TOOLS
    return templates.TemplateResponse(request, "pages/tools/index.html", ctx)


@router.get("/ferramentas/rescisao", include_in_schema=False)
def rescisao_form(request: Request):
    return templates.TemplateResponse(request, "pages/tools/rescisao.html", _rescisao_context({}))


@router.post("/ferramentas/rescisao", include_in_schema=False)
async def rescisao_calc(request: Request):
    form = dict(await request.form())
    ctx = _rescisao_context(form)
    try:
        payload = RescisaoInput(
            salario_bruto=_clean_number(form.get("salario_bruto")) or None,
            data_admissao=form.get("data_admissao") or None,
            data_demissao=form.get("data_demissao") or None,
            tipo_rescisao=form.get("tipo_rescisao") or "",
            aviso_previo=form.get("aviso_previo") or "",
            dias_ferias_vencidas=form.get("dias_ferias_vencidas") or 0,
        )
        ctx["result"] = compute_rescisao(
            salario_bruto=payload.salario_bruto,
            data_admissao=payload.data_admissao,
            data_demissao=payload.data_demissao,
            tipo_rescisao=payload.tipo_rescisao,
            aviso_previo=payload.aviso_previo,
            dias_ferias_vencidas=payload.dias_ferias_vencidas,
        )
    except ValidationError as exc:
        ctx["error"] = _friendly(exc)
    return templates.TemplateResponse(request, "pages/tools/rescisao.html", ctx)


@router.get("/ferramentas/ferias", include_in_schema=False)
def ferias_form(request: Request):
    return templates.TemplateResponse(request, "pages/tools/ferias.html", _ferias_context({}))


@router.post("/ferramentas/ferias", include_in_schema=False)
async def ferias_calc(request: Request):
    form = dict(await request.form())
    ctx = _ferias_context(form)
    try:
        payload = FeriasInput(
            salario_bruto=_clean_number(form.get("salario_bruto")) or None,
            media_adicionais=_clean_number(form.get("media_adicionais")) or 0,
            dias_gozados=form.get("dias_gozados") or 30,
            vender_abono=bool(form.get("vender_abono")),
            dias_abono=form.get("dias_abono") or 0,
        )
        ctx["result"] = compute_ferias(
            salario_bruto=payload.salario_bruto,
            media_adicionais=payload.media_adicionais,
            dias_gozados=payload.dias_gozados,
            vender_abono=payload.vender_abono,
            dias_abono=payload.dias_abono,
        )
    except ValidationError as exc:
        ctx["error"] = _friendly(exc)
    return templates.TemplateResponse(request, "pages/tools/ferias.html", ctx)


@router.get("/ferramentas/inss", include_in_schema=False)
def inss_form(request: Request):
    return templates.TemplateResponse(request, "pages/tools/inss.html", _inss_context({}))


@router.post("/ferramentas/inss", include_in_schema=False)
async def inss_calc(request: Request):
    form = dict(await request.form())
    ctx = _inss_context(form)
    try:
        payload = InssInput(salario_bruto=_clean_number(form.get("salario_bruto")) or None)
        ctx["result"] = compute_inss(salario_bruto=payload.salario_bruto)
    except ValidationError as exc:
        ctx["error"] = _friendly(exc)
    return templates.TemplateResponse(request, "pages/tools/inss.html", ctx)


@router.get("/ferramentas/imposto-de-renda", include_in_schema=False)
def imposto_de_renda_form(request: Request):
    return templates.TemplateResponse(request, "pages/tools/imposto-de-renda.html", _irrf_context({}))


@router.post("/ferramentas/imposto-de-renda", include_in_schema=False)
async def imposto_de_renda_calc(request: Request):
    form = dict(await request.form())
    ctx = _irrf_context(form)
    try:
        payload = IrrfInput(
            salario_bruto=_clean_number(form.get("salario_bruto")) or None,
            dependentes=form.get("dependentes") or 0,
        )
        ctx["result"] = compute_irrf(
            salario_bruto=payload.salario_bruto,
            dependentes=payload.dependentes,
        )
    except ValidationError as exc:
        ctx["error"] = _friendly(exc)
    return templates.TemplateResponse(request, "pages/tools/imposto-de-renda.html", ctx)


@router.get("/ferramentas/restituicao-ir", include_in_schema=False)
def restituicao_ir_form(request: Request):
    return templates.TemplateResponse(request, "pages/tools/restituicao-ir.html", _restituicao_context({}))


@router.post("/ferramentas/restituicao-ir", include_in_schema=False)
async def restituicao_ir_calc(request: Request):
    form = dict(await request.form())
    ctx = _restituicao_context(form)
    try:
        payload = RestituicaoInput(
            rendimentos_anuais=_clean_number(form.get("rendimentos_anuais")) or None,
            dependentes=form.get("dependentes") or 0,
            despesas_ensino=_clean_number(form.get("despesas_ensino")) or 0,
            despesas_medicas=_clean_number(form.get("despesas_medicas")) or 0,
            pensao_alimenticia=_clean_number(form.get("pensao_alimenticia")) or 0,
            contribuicao_inss=_clean_number(form.get("contribuicao_inss")) or 0,
            ir_retido_fonte=_clean_number(form.get("ir_retido_fonte")) or 0,
        )
        ctx["result"] = compute_restituicao(
            rendimentos_anuais=payload.rendimentos_anuais,
            dependentes=payload.dependentes,
            despesas_ensino=payload.despesas_ensino,
            despesas_medicas=payload.despesas_medicas,
            pensao_alimenticia=payload.pensao_alimenticia,
            contribuicao_inss=payload.contribuicao_inss,
            ir_retido_fonte=payload.ir_retido_fonte,
        )
    except ValidationError as exc:
        ctx["error"] = _friendly(exc)
    return templates.TemplateResponse(request, "pages/tools/restituicao-ir.html", ctx)