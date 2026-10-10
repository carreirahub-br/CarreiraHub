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