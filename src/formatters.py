from decimal import Decimal, InvalidOperation


def parse_brl(value):
    """Converte entradas brasileiras e números da API sem alterar os centavos."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float, Decimal)):
        return float(value)
    text = str(value).strip().replace("R$", "").replace(" ", "")
    if not text:
        return None
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        return float(Decimal(text))
    except (InvalidOperation, ValueError):
        return None


def format_brl(value) -> str:
    number = float(value or 0)
    return f"R$ {number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

