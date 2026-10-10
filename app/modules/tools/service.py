from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date

FGTS_RATE = 0.08

RESCISAO_TYPES: dict[str, dict] = {
    "sem_justa_causa": {
        "label": "Sem justa causa (iniciativa do empregador)",
        "multa": 0.40,
        "aviso_proporcao": 1.0,
        "saca_fgts": True,
    },
    "acordo": {
        "label": "Acordo entre as partes",
        "multa": 0.20,
        "aviso_proporcao": 0.5,
        "saca_fgts": True,
    },
    "pedido_demissao": {
        "label": "Pedido de demissão (iniciativa do empregado)",
        "multa": 0.0,
        "aviso_proporcao": 0.0,
        "saca_fgts": False,
    },
    "justa_causa": {
        "label": "Justa causa",
        "multa": 0.0,
        "aviso_proporcao": 0.0,
        "saca_fgts": True,
    },
}

AVISO_PREVIO_OPTIONS: dict[str, str] = {
    "indenizado": "Indenizado (sem cumprimento)",
    "trabalhado": "Trabalhado (cumprido normalmente)",
}

INSS_TETO = 908.85
INSS_BANDS = (
    (0.0, 1_518.00, 0.075),
    (1_518.00, 2_793.88, 0.090),
    (2_793.88, 4_190.83, 0.120),
    (4_190.83, float("inf"), 0.140),
)

INSS_TETO_2026 = 988.09
INSS_BANDS_2026 = (
    (0.0, 1_621.00, 0.075),
    (1_621.00, 2_902.84, 0.090),
    (2_902.84, 4_354.27, 0.120),
    (4_354.27, float("inf"), 0.140),
)

DEPENDENTE_MENSAL = 189.59
DESCONTO_SIMPLIFICADO_MENSAL = 607.20
IRRF_MENSAL_2026 = (
    (0.0, 2_428.80, 0.0, 0.0),
    (2_428.80, 2_826.65, 0.075, 182.16),
    (2_826.65, 3_751.05, 0.150, 394.16),
    (3_751.05, 4_664.68, 0.225, 675.49),
    (4_664.68, float("inf"), 0.275, 908.73),
)
REDUCAO_MENSAL_LIMITE = 5_000.00
REDUCAO_MENSAL_TETO = 7_350.00
REDUCAO_MENSAL_A = 978.62
REDUCAO_MENSAL_B = 0.133145
REDUCAO_MENSAL_ZERO = 312.89

DEPENDENTE_ANUAL = 2_275.08
INSTRUCAO_LIMITE = 3_561.50
DESCONTO_SIMPLIFICADO_ANUAL = 17_640.00
IRRF_ANUAL_2026 = (
    (0.0, 29_145.60, 0.0, 0.0),
    (29_145.60, 33_919.80, 0.075, 2_185.92),
    (33_919.80, 45_012.60, 0.150, 4_729.91),
    (45_012.60, 55_976.16, 0.225, 8_105.85),
    (55_976.16, float("inf"), 0.275, 10_904.66),
)
REDUCAO_ANUAL_LIMITE = 60_000.00
REDUCAO_ANUAL_TETO = 88_200.00
REDUCAO_ANUAL_A = 8_429.73
REDUCAO_ANUAL_B = 0.095575
REDUCAO_ANUAL_ZERO = 2_694.15


def brl(value: float) -> str:
    number = round(value, 2)
    sign = "-" if number < 0 else ""
    number = abs(number)
    whole, cents = f"{number:.2f}".split(".")
    whole = f"{int(whole):,}".replace(",", ".")
    return f"{sign}R$ {whole},{cents}"


def _worked_days(start: date, end: date, year: int, month: int) -> int:
    first = date(year, month, 1)
    last = date(year, month, calendar.monthrange(year, month)[1])
    return max(0, (min(end, last) - max(start, first)).days + 1)


def _full_years(start: date, end: date) -> int:
    years = end.year - start.year
    if (end.month, end.day) < (start.month, start.day):
        years -= 1
    return max(years, 0)


def _months_worked(start: date, end: date) -> int:
    count = 0
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        if _worked_days(start, end, year, month) > 14:
            count += 1
        month += 1
        if month == 13:
            year += 1
            month = 1
    return count


def _months_in_year(start: date, end: date) -> int:
    total = 0
    for month in range(1, end.month + 1):
        if _worked_days(start, end, end.year, month) >= 15:
            total += 1
    return total


@dataclass(frozen=True)
class LineItem:
    label: str
    hint: str
    value: float
    accent: bool = False

    @property
    def value_text(self) -> str:
        return brl(self.value)


@dataclass(frozen=True)
class RescisaoResult:
    tipo_label: str
    items: tuple[LineItem, ...]
    total_bruto: float
    fgts_estimado: float
    notas: tuple[str, ...]

    @property
    def total_text(self) -> str:
        return brl(self.total_bruto)

    @property
    def fgts_text(self) -> str:
        return brl(self.fgts_estimado)


def _aviso_hint(aviso_previo: str, dia_aviso: int, multa_pct: int, tipo_key: str) -> str:
    if aviso_previo != "indenizado" or tipo_key in {"pedido_demissao", "justa_causa"}:
        return "Aviso trabalhado ou não devido neste tipo de rescisão"
    if tipo_key == "acordo":
        return f"{dia_aviso} dia(s) — metade do aviso no acordo entre as partes"
    return f"{dia_aviso} dia(s) — 30 dias + 3 por ano de serviço (limite de 90)"


def _rescisao_notas(tipo_key: str, fgts_estimado: float) -> tuple[str, ...]:
    notas = [
        "Valores brutos estimados — não incluem descontos de INSS, IRRF nem deduções de aviso prévio trabalhado.",
        "O cálculo considera um vínculo contínuo e não avalia acordos coletivos, adicionais, horas extras ou comissões.",
        f"Depósitos de FGTS estimados no período: {brl(fgts_estimado)} — ficam na conta do FGTS, fora da rescisão.",
    ]
    if tipo_key == "sem_justa_causa":
        notas.append("Sem justa causa: você pode sacar o saldo do FGTS e recebe a multa de 40% paga pelo empregador.")
    elif tipo_key == "acordo":
        notas.append("No acordo: a multa é de 20% e o saque do FGTS fica limitado a 80% do saldo.")
    elif tipo_key == "pedido_demissao":
        notas.append("No pedido de demissão não há multa sobre o FGTS e, em regra, o saldo não pode ser sacado.")
    else:
        notas.append("Na justa causa não há aviso prévio nem multa de 40%; o saldo do FGTS pode ser sacado.")
    notas.append("Simulação educativa — não substitui a orientação de um contador ou profissional de RH.")
    return tuple(notas)


def compute_rescisao(
    *,
    salario_bruto: float,
    data_admissao: date,
    data_demissao: date,
    tipo_rescisao: str,
    aviso_previo: str,
    dias_ferias_vencidas: int,
) -> RescisaoResult:
    tipo = RESCISAO_TYPES[tipo_rescisao]
    salario_dia = salario_bruto / 30.0

    saldo_salario = salario_dia * data_demissao.day

    anos = _full_years(data_admissao, data_demissao)
    aviso_dias = min(30 + 3 * anos, 90)
    if aviso_previo == "indenizado":
        aviso_dias_efetivos = round(aviso_dias * tipo["aviso_proporcao"])
        aviso_valor = salario_dia * aviso_dias_efetivos
    else:
        aviso_dias_efetivos = 0
        aviso_valor = 0.0

    meses_13 = _months_in_year(data_admissao, data_demissao)
    decimo_13 = (salario_bruto / 12.0) * meses_13

    meses_totais = _months_worked(data_admissao, data_demissao)
    meses_periodo = meses_totais % 12

    ferias_vencidas = salario_dia * dias_ferias_vencidas
    terco_vencidas = ferias_vencidas / 3.0

    dias_prop = meses_periodo * (30.0 / 12.0)
    ferias_proporcionais = salario_dia * dias_prop
    terco_proporcionais = ferias_proporcionais / 3.0

    base_fgts = (
        salario_bruto * meses_totais
        + saldo_salario
        + aviso_valor
        + decimo_13
        + ferias_vencidas
        + ferias_proporcionais
    )
    fgts_estimado = FGTS_RATE * base_fgts
    multa_fgts = fgts_estimado * tipo["multa"]
    pct = round(tipo["multa"] * 100)

    items = (
        LineItem("Saldo de salário", f"{data_demissao.day} dia(s) trabalhado(s) no mês em que o contrato terminou", saldo_salario),
        LineItem("Aviso prévio", _aviso_hint(aviso_previo, aviso_dias_efetivos, pct, tipo_rescisao), aviso_valor),
        LineItem("13º salário proporcional", f"{meses_13}/12 avos trabalhados no ano da demissão", decimo_13),
        LineItem("Férias vencidas", f"{dias_ferias_vencidas} dia(s), se ainda não foram gozadas", ferias_vencidas),
        LineItem("1/3 constitucional sobre férias vencidas", "Súmula 328 do TST", terco_vencidas),
        LineItem("Férias proporcionais", f"{meses_periodo} mês(es) do período aquisitivo atual ({dias_prop:g} dia(s))", ferias_proporcionais),
        LineItem("1/3 constitucional sobre férias proporcionais", "Súmula 328 do TST", terco_proporcionais),
        LineItem(f"Multa de {pct}% sobre o FGTS", "Percentual conforme o tipo de rescisão", multa_fgts),
    )

    return RescisaoResult(
        tipo_label=tipo["label"],
        items=items,
        total_bruto=round(sum(item.value for item in items), 2),
        fgts_estimado=round(fgts_estimado, 2),
        notas=_rescisao_notas(tipo_rescisao, fgts_estimado),
    )


@dataclass(frozen=True)
class FeriasResult:
    items: tuple[LineItem, ...]
    subtotal_bruto: float
    inss: float
    valor_liquido: float
    notas: tuple[str, ...]

    @property
    def subtotal_text(self) -> str:
        return brl(self.subtotal_bruto)

    @property
    def inss_text(self) -> str:
        return brl(self.inss)

    @property
    def liquido_text(self) -> str:
        return brl(self.valor_liquido)


def inss_2025(value: float) -> float:
    total = 0.0
    for low, high, rate in INSS_BANDS:
        if value > low:
            total += (min(value, high) - low) * rate
    return min(total, INSS_TETO)


def compute_ferias(
    *,
    salario_bruto: float,
    media_adicionais: float,
    dias_gozados: int,
    vender_abono: bool,
    dias_abono: int,
) -> FeriasResult:
    base_mensal = salario_bruto + media_adicionais
    diaria = base_mensal / 30.0

    gozo = diaria * dias_gozados
    abono = diaria * dias_abono if vender_abono else 0.0
    terco = base_mensal / 3.0

    subtotal = gozo + abono + terco
    inss = inss_2025(subtotal)
    liquido = subtotal - inss

    items = (
        LineItem("Férias (dias de descanso)", f"{dias_gozados} dia(s) × diária calculada", gozo),
        LineItem("Abono pecuniário", f"{dias_abono} dia(s) vendido(s), se solicitado", abono),
        LineItem("1/3 constitucional", "Sobre a base de 30 dias (Súmula 328 do TST)", terco),
        LineItem("INSS (estimativa)", "Tabela progressiva de 2025", -inss),
    )
    notas = (
        "Valores estimados para um caso simples. Convenções coletivas, adicionais acima da média informada e IRRF não estão considerados.",
        "O terço constitucional incide sobre os 30 dias de férias, mesmo quando parte é convertida em abono pecuniário.",
        "Simulação educativa — não substitui a consulta a um contador ou profissional de RH.",
    )

    return FeriasResult(
        items=items,
        subtotal_bruto=round(subtotal, 2),
        inss=round(inss, 2),
        valor_liquido=round(liquido, 2),
        notas=notas,
    )


def inss_2026(value: float) -> float:
    total = 0.0
    for low, high, rate in INSS_BANDS_2026:
        if value > low:
            total += (min(value, high) - low) * rate
    return min(total, INSS_TETO_2026)


def _ir_progressivo(value: float, bands: tuple) -> float:
    if value <= 0:
        return 0.0
    for low, high, rate, parcela in bands:
        if low < value <= high:
            return max(value * rate - parcela, 0.0)
    return 0.0


def _reducao_mensal(rendimento: float, imposto: float) -> float:
    if rendimento <= REDUCAO_MENSAL_LIMITE:
        return min(imposto, REDUCAO_MENSAL_ZERO)
    if rendimento <= REDUCAO_MENSAL_TETO:
        return min(imposto, REDUCAO_MENSAL_A - REDUCAO_MENSAL_B * rendimento)
    return 0.0


def _reducao_anual(rendimento: float, imposto: float) -> float:
    if rendimento <= REDUCAO_ANUAL_LIMITE:
        return min(imposto, REDUCAO_ANUAL_ZERO)
    if rendimento <= REDUCAO_ANUAL_TETO:
        return min(imposto, REDUCAO_ANUAL_A - REDUCAO_ANUAL_B * rendimento)
    return 0.0


def _tabela_rows(columns: tuple[str, ...], rows: tuple[tuple[str, ...], ...], title: str, source: str) -> dict:
    return {"columns": columns, "rows": rows, "title": title, "source": source}


def tabela_inss() -> dict:
    return _tabela_rows(
        columns=("Base de cálculo", "Alíquota"),
        rows=(
            ("Até R$ 1.621,00", "7,5%"),
            ("De R$ 1.621,01 até R$ 2.902,84", "9%"),
            ("De R$ 2.902,85 até R$ 4.354,27", "12%"),
            ("De R$ 4.354,28 até R$ 8.475,55", "14%"),
        ),
        title="Tabela do INSS (2026)",
        source="Portaria Interministerial MPS/MF nº 13, de 09/01/2026 — competência janeiro de 2026. Alíquota progressiva por faixa.",
    )


def tabela_irrf_mensal() -> dict:
    return _tabela_rows(
        columns=("Base de cálculo", "Alíquota", "Parcela a deduzir"),
        rows=(
            ("Até R$ 2.428,80", "Isento", "—"),
            ("De R$ 2.428,81 até R$ 2.826,65", "7,5%", "R$ 182,16"),
            ("De R$ 2.826,66 até R$ 3.751,05", "15%", "R$ 394,16"),
            ("De R$ 3.751,06 até R$ 4.664,68", "22,5%", "R$ 675,49"),
            ("Acima de R$ 4.664,68", "27,5%", "R$ 908,73"),
        ),
        title="Tabela do IRRF (2026)",
        source="Lei 15.191/2025, vigente a partir de janeiro de 2026. Combinada à Lei 15.270/2025, zera o IR até R$ 5.000 por mês.",
    )


def tabela_irrf_anual() -> dict:
    return _tabela_rows(
        columns=("Base de cálculo", "Alíquota", "Parcela a deduzir"),
        rows=(
            ("Até R$ 29.145,60", "Isento", "—"),
            ("De R$ 29.145,61 até R$ 33.919,80", "7,5%", "R$ 2.185,92"),
            ("De R$ 33.919,81 até R$ 45.012,60", "15%", "R$ 4.729,91"),
            ("De R$ 45.012,61 até R$ 55.976,16", "22,5%", "R$ 8.105,85"),
            ("Acima de R$ 55.976,16", "27,5%", "R$ 10.904,66"),
        ),
        title="Tabela anual do IR (exercício 2027)",
        source="Tributação de 2026 (ano-calendário 2026), divulgada pela Receita Federal. Dedução por dependente: R$ 2.275,08.",
    )


@dataclass(frozen=True)
class InssResult:
    salario_bruto: float
    contribuicao: float
    aliquota_efetiva: float
    salario_liquido: float
    notas: tuple[str, ...]

    @property
    def salario_text(self) -> str:
        return brl(self.salario_bruto)

    @property
    def contribuicao_text(self) -> str:
        return brl(self.contribuicao)

    @property
    def aliquota_text(self) -> str:
        return f"{self.aliquota_efetiva * 100:.1f}%".replace(".", ",")

    @property
    def liquido_text(self) -> str:
        return brl(self.salario_liquido)


def compute_inss(*, salario_bruto: float) -> InssResult:
    contribuicao = inss_2026(salario_bruto)
    aliquota_efetiva = contribuicao / salario_bruto
    liquido = salario_bruto - contribuicao
    notas = (
        "Contribuição estimada com a tabela progressiva de 2026, limitada ao teto de contribuição (R$ 8.475,55).",
        "A alíquota é efetiva: cada faixa tributada em separado, como prevê a tabela do INSS.",
        "Simulação educativa — não inclui contribuições de patrões, MEI, autônomos ou regimes próprios.",
    )
    return InssResult(
        salario_bruto=salario_bruto,
        contribuicao=round(contribuicao, 2),
        aliquota_efetiva=round(aliquota_efetiva, 4),
        salario_liquido=round(liquido, 2),
        notas=notas,
    )


@dataclass(frozen=True)
class IrrfResult:
    items: tuple[LineItem, ...]
    irrf: float
    liquido: float
    usar_simplificado: bool
    notas: tuple[str, ...]

    @property
    def irrf_text(self) -> str:
        return brl(self.irrf)

    @property
    def liquido_text(self) -> str:
        return brl(self.liquido)

    @property
    def desconto_label(self) -> str:
        return "Desconto simplificado" if self.usar_simplificado else "Deduções legais"


def compute_irrf(*, salario_bruto: float, dependentes: int) -> IrrfResult:
    inss = inss_2026(salario_bruto)
    deducao_legal = inss + dependentes * DEPENDENTE_MENSAL
    usar_simplificado = DESCONTO_SIMPLIFICADO_MENSAL > deducao_legal
    deducao = DESCONTO_SIMPLIFICADO_MENSAL if usar_simplificado else deducao_legal
    base = max(0.0, salario_bruto - deducao)
    ir_bruto = _ir_progressivo(base, IRRF_MENSAL_2026)
    reducao = _reducao_mensal(salario_bruto, ir_bruto)
    irrf = max(0.0, ir_bruto - reducao)
    liquido = salario_bruto - inss - irrf

    desconto_hint = (
        "R$ 607,20 por mês, maior que as deduções legais"
        if usar_simplificado
        else "INSS + dependentes: maior que o desconto simplificado"
    )
    items = (
        LineItem("Salário bruto", "Remuneração mensal informada", salario_bruto),
        LineItem("INSS (2026)", "Desconto previdenciário com a tabela progressiva", -inss),
        LineItem("Deduções aplicadas", desconto_hint, -deducao),
        LineItem("Base de cálculo", "Salário bruto − deduções", base),
        LineItem("IRRF pela tabela", "Aplicação da alíquota sobre a base", ir_bruto),
        LineItem("Redução do imposto", "Lei 15.270/2025 — zera o IR até R$ 5.000/mês", -reducao),
        LineItem("IRRF a pagar no mês", "Após a redução legal", -irrf),
    )
    notas = (
        "A redução da Lei 15.270/2025 elimina o IRRF até R$ 5.000 por mês e diminui de forma decrescente até R$ 7.350.",
        "Usado {desconto}".format(desconto="o desconto simplificado (R$ 607,20)" if usar_simplificado else "as deduções legais (INSS + R$ 189,59 por dependente)"),
        "Simulação educativa — não substitui a folha de pagamento nem a orientação de um contador.",
    )
    return IrrfResult(items=items, irrf=round(irrf, 2), liquido=round(liquido, 2), usar_simplificado=usar_simplificado, notas=notas)


@dataclass(frozen=True)
class RestituicaoResult:
    items: tuple[LineItem, ...]
    ir_devido: float
    saldo: float
    notas: tuple[str, ...]

    @property
    def imposto_text(self) -> str:
        return brl(self.ir_devido)

    @property
    def saldo_text(self) -> str:
        return brl(abs(self.saldo))

    @property
    def is_restituicao(self) -> bool:
        return self.saldo >= 0

    @property
    def rotulo(self) -> str:
        return "Restituição a receber" if self.is_restituicao else "Imposto a pagar"


def compute_restituicao(
    *,
    rendimentos_anuais: float,
    contribuicao_inss: float,
    dependentes: int,
    despesas_ensino: float,
    pensao_alimenticia: float,
    despesas_medicas: float,
    ir_retido_fonte: float,
) -> RestituicaoResult:
    ensino_ded = min(despesas_ensino, INSTRUCAO_LIMITE)
    deducao_legal = (
        dependentes * DEPENDENTE_ANUAL
        + contribuicao_inss
        + ensino_ded
        + pensao_alimenticia
        + despesas_medicas
    )
    usar_simplificado = DESCONTO_SIMPLIFICADO_ANUAL > deducao_legal
    deducao = DESCONTO_SIMPLIFICADO_ANUAL if usar_simplificado else deducao_legal
    base = max(0.0, rendimentos_anuais - deducao)
    ir_bruto = _ir_progressivo(base, IRRF_ANUAL_2026)
    reducao = _reducao_anual(rendimentos_anuais, ir_bruto)
    ir_devido = max(0.0, ir_bruto - reducao)
    saldo = ir_retido_fonte - ir_devido

    desconto_hint = (
        "R$ 17.640,00 no ano, maior que as deduções legais"
        if usar_simplificado
        else "Dependentes, INSS, educação, pensão e despesas médicas"
    )
    items = (
        LineItem("Rendimentos tributáveis anuais", "Total recebido no ano-calendário", rendimentos_anuais),
        LineItem("Deduções aplicadas", desconto_hint, -deducao),
        LineItem("Base de cálculo anual", "Rendimentos − deduções", base),
        LineItem("Imposto pela tabela anual", "Tabela progressiva do exercício", ir_bruto),
        LineItem("Redução do imposto", "Lei 15.270/2025 — imposto zero até R$ 60.000/ano", -reducao),
        LineItem("IR retido na fonte no ano", "Soma dos descontos mensais e 13º", -ir_retido_fonte),
    )
    notas = (
        "Restituição ocorre quando o IR retido na fonte supera o imposto anual devido; o contrário gera imposto a pagar.",
        "Despesas médicas não têm limite; educação é limitada a R$ 3.561,50 por ano; pensão alimentícia judicial é integral.",
        "Simulação educativa — não substitui a declaração completa nem a orientação de um contador.",
    )
    return RestituicaoResult(
        items=items,
        ir_devido=round(ir_devido, 2),
        saldo=round(saldo, 2),
        notas=notas,
    )