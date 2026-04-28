"""BCB SGS series configuration.

Series codes can be looked up at https://www3.bcb.gov.br/sgspub/.
"""

# The BCB SGS API rejects daily-series queries that span more than ~10 years
# in a single request. We default to ~8 years of history so every series stays
# within the limit while keeping a meaningful amount of data for analysis.
DEFAULT_START_DATE = "01/01/2018"

SERIES = {
    "selic_meta": {
        "code": 432,
        "name": "Selic meta",
        "unit": "% a.a.",
        "frequency": "daily",
    },
    "selic_over": {
        "code": 11,
        "name": "Selic Over (daily rate)",
        "unit": "% a.d.",
        "frequency": "daily",
    },
    "ipca_monthly": {
        "code": 433,
        "name": "IPCA mensal",
        "unit": "% a.m.",
        "frequency": "monthly",
    },
    "ipca_12m": {
        "code": 13522,
        "name": "IPCA acumulado 12 meses",
        "unit": "% a.a.",
        "frequency": "monthly",
    },
    "usd_brl_ptax": {
        "code": 1,
        "name": "USD/BRL PTAX (compra)",
        "unit": "R$",
        "frequency": "daily",
    },
    "eur_brl_ptax": {
        "code": 21619,
        "name": "EUR/BRL PTAX (compra)",
        "unit": "R$",
        "frequency": "daily",
    },
}
