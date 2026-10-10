from datetime import date

from pydantic import BaseModel, field_validator, model_validator

RESCISAO_ALLOWED = {"sem_justa_causa", "acordo", "pedido_demissao", "justa_causa"}
AVISO_ALLOWED = {"indenizado", "trabalhado"}


class RescisaoInput(BaseModel):
    salario_bruto: float
    data_admissao: date
    data_demissao: date
    tipo_rescisao: str
    aviso_previo: str
    dias_ferias_vencidas: int

    @field_validator("salario_bruto")
    @classmethod
    def validate_salario(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("O salário bruto mensal deve ser maior que zero.")
        if value > 1_000_000:
            raise ValueError("O salário informado está acima do limite considerado.")
        return value

    @field_validator("dias_ferias_vencidas")
    @classmethod
    def validate_dias_vencidas(cls, value: int) -> int:
        if not 0 <= value <= 90:
            raise ValueError("As férias vencidas devem ficar entre 0 e 90 dias.")
        return value

    @field_validator("tipo_rescisao")
    @classmethod
    def validate_tipo(cls, value: str) -> str:
        if value not in RESCISAO_ALLOWED:
            raise ValueError("Selecione um tipo de rescisão válido.")
        return value

    @field_validator("aviso_previo")
    @classmethod
    def validate_aviso(cls, value: str) -> str:
        if value not in AVISO_ALLOWED:
            raise ValueError("Selecione a forma do aviso prévio.")
        return value

    @model_validator(mode="after")
    def check_period(self):
        if self.data_demissao < self.data_admissao:
            raise ValueError("A data de demissão deve ser posterior à data de admissão.")
        return self


class FeriasInput(BaseModel):
    salario_bruto: float
    media_adicionais: float = 0
    dias_gozados: int = 30
    vender_abono: bool = False
    dias_abono: int = 0

    @field_validator("salario_bruto")
    @classmethod
    def validate_salario(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("O salário bruto mensal deve ser maior que zero.")
        if value > 1_000_000:
            raise ValueError("O salário informado está acima do limite considerado.")
        return value

    @field_validator("media_adicionais")
    @classmethod
    def validate_media(cls, value: float) -> float:
        if value < 0:
            raise ValueError("A média de adicionais não pode ser negativa.")
        return value

    @field_validator("dias_gozados")
    @classmethod
    def validate_dias_gozados(cls, value: int) -> int:
        if not 1 <= value <= 30:
            raise ValueError("Os dias de férias devem ficar entre 1 e 30.")
        return value

    @field_validator("dias_abono")
    @classmethod
    def validate_dias_abono(cls, value: int) -> int:
        if not 0 <= value <= 10:
            raise ValueError("O abono é limitado a 1/3 das férias (10 dias).")
        return value

    @model_validator(mode="after")
    def check_abono(self):
        if self.vender_abono and self.dias_abono == 0:
            raise ValueError("Informe quantos dias você quer vender.")
        if self.dias_gozados + self.dias_abono > 30:
            raise ValueError("Descanso + abono não podem ultrapassar 30 dias.")
        return self


class InssInput(BaseModel):
    salario_bruto: float

    @field_validator("salario_bruto")
    @classmethod
    def validate_salario(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("O salário bruto mensal deve ser maior que zero.")
        if value > 1_000_000:
            raise ValueError("O salário informado está acima do limite considerado.")
        return value


def _validate_dependentes(value: int) -> int:
    if not 0 <= value <= 30:
        raise ValueError("O número de dependentes deve ficar entre 0 e 30.")
    return value


def _validate_despesa(value: float) -> float:
    if value < 0:
        raise ValueError("As despesas não podem ser negativas.")
    return value


class IrrfInput(BaseModel):
    salario_bruto: float
    dependentes: int = 0

    @field_validator("salario_bruto")
    @classmethod
    def validate_salario(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("O salário bruto mensal deve ser maior que zero.")
        if value > 1_000_000:
            raise ValueError("O salário informado está acima do limite considerado.")
        return value

    @field_validator("dependentes")
    @classmethod
    def validate_dependentes_irrf(cls, value: int) -> int:
        return _validate_dependentes(value)


class RestituicaoInput(BaseModel):
    rendimentos_anuais: float
    dependentes: int = 0
    despesas_ensino: float = 0
    despesas_medicas: float = 0
    pensao_alimenticia: float = 0
    contribuicao_inss: float = 0
    ir_retido_fonte: float = 0

    @field_validator("rendimentos_anuais")
    @classmethod
    def validate_rendimentos(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("Os rendimentos anuais devem ser maior que zero.")
        if value > 100_000_000:
            raise ValueError("Os rendimentos informados estão acima do limite considerado.")
        return value

    @field_validator("dependentes")
    @classmethod
    def validate_dependentes_rest(cls, value: int) -> int:
        return _validate_dependentes(value)

    @field_validator(
        "despesas_ensino", "despesas_medicas", "pensao_alimenticia", "contribuicao_inss", "ir_retido_fonte"
    )
    @classmethod
    def validate_despesas(cls, value: float) -> float:
        return _validate_despesa(value)