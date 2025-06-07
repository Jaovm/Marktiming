"""
Configurações globais do painel de Market Timing e Análise Macroeconômica.

Este módulo contém constantes, configurações e parâmetros utilizados em todo o projeto.
"""

# Tema visual do dashboard
THEME = {
    "primary": "#1E88E5",    # Azul
    "secondary": "#4CAF50",  # Verde
    "background": "#F5F5F5", # Cinza claro
    "text": "#212121",       # Preto
    "positive": "#4CAF50",   # Verde
    "negative": "#F44336",   # Vermelho
    "neutral": "#FFC107"     # Amarelo
}

# Setores da B3
SETORES_B3 = {
    "Financeiro": ["ITUB4", "BBDC4", "BBAS3", "SANB11", "B3SA3"],
    "Energia": ["PETR4", "PETR3", "CSAN3", "UGPA3", "BRDT3"],
    "Mineração": ["VALE3", "CSNA3", "GGBR4", "GOAU4", "USIM5"],
    "Consumo": ["ABEV3", "LREN3", "MGLU3", "VVAR3", "BTOW3"],
    "Imobiliário": ["CYRE3", "MRVE3", "EZTC3", "EVEN3", "DIRR3"],
    "Utilities": ["SBSP3", "CMIG4", "ELET3", "ELET6", "CPFE3"],
    "Saúde": ["RADL3", "HAPV3", "GNDI3", "FLRY3", "PARD3"],
    "Tecnologia": ["TOTS3", "LWSA3", "POSI3", "LINX3", "TIMS3"],
    "Transporte": ["AZUL4", "GOLL4", "RAIL3", "ECOR3", "CCRO3"],
    "Agronegócio": ["SLCE3", "JBSS3", "MRFG3", "BEEF3", "SMTO3"]
}

# Carteira base para análise
CARTEIRA_BASE = {
    "PETR4": 15,  # % da carteira
    "VALE3": 15,
    "ITUB4": 10,
    "BBDC4": 10,
    "ABEV3": 10,
    "MGLU3": 5,
    "WEGE3": 5,
    "RADL3": 5,
    "RENT3": 5,
    "B3SA3": 5,
    "BBAS3": 5,
    "EGIE3": 5,
    "FLRY3": 5
}

# Configurações de APIs
API_CONFIG = {
    "bcb": {
        "base_url": "https://api.bcb.gov.br/dados/serie/bcdata.sgs.",
        "format": "/dados?formato=json"
    },
    "yahoo": {
        "interval": "1d",
        "period": "1y"
    }
}

# Códigos de séries do Banco Central
BCB_SERIES = {
    # PIB
    "pib_mensal": 4380,        # PIB Mensal - Valores correntes (R$ milhões)
    "pib_var_anual": 7326,     # PIB - Variação real anual
    
    # Inflação
    "ipca_mensal": 433,        # IPCA - Var. % mensal
    "ipca_acum_12m": 13522,    # IPCA - Acumulado 12 meses (% a.a.)
    "igpm_mensal": 189,        # IGP-M - Var. % mensal
    "igpm_acum_12m": 13599,    # IGP-M - Acumulado 12 meses (% a.a.)
    
    # Juros
    "selic_meta": 432,         # Taxa Selic Meta (% a.a.)
    "selic_diaria": 11,        # Taxa Selic diária (% a.a.)
    "di_1m": 12,               # DI - 30 dias
    "di_3m": 14,               # DI - 90 dias
    "di_6m": 16,               # DI - 180 dias
    "di_1y": 18,               # DI - 360 dias
    "di_2y": 20,               # DI - 720 dias
    "di_3y": 22,               # DI - 1080 dias
    
    # Mercado de Trabalho
    "desemprego": 24369,       # Taxa de desocupação - PNAD Contínua (%)
    "caged_saldo": 28763,      # CAGED - Saldo de empregos formais
    
    # Liquidez
    "m1": 27841,               # M1 - Base monetária restrita
    "m2": 27842,               # M2 - M1 + depósitos de poupança + títulos privados
    "m3": 27843,               # M3 - M2 + quotas de fundos de renda fixa
    "m4": 27844,               # M4 - M3 + títulos públicos
    
    # Risco
    "embi": 3543,              # EMBI+ Brasil (pontos)
    "cds_5y": 41216,           # CDS Brasil 5 anos (pontos)
    "ifix": 29568              # Índice de Fundos Imobiliários (IFIX)
}

# Índices de mercado
INDICES = {
    "Ibovespa": "^BVSP",
    "IBrX": "^IBX",
    "IDIV": "^IDIV",
    "Small Caps": "^SMLL",
    "IFIX": "^IFIX"
}

# Parâmetros para análise de ciclo econômico
CICLO_PARAMS = {
    "pesos_indicadores": {
        "curva_juros": 0.25,
        "inflacao": 0.20,
        "juros": 0.20,
        "atividade": 0.15,
        "risco": 0.10,
        "mercado": 0.10
    },
    "limites_inclinacao": {
        "invertida": -0.5,
        "achatada": 0.5,
        "normal": 1.5,
        "acentuada": 999
    }
}

# Parâmetros para market timing
TIMING_PARAMS = {
    "pesos_indicadores": {
        "ciclo": 0.30,
        "valuation": 0.25,
        "momentum": 0.20,
        "risco": 0.15,
        "liquidez": 0.10
    },
    "limites_score": {
        "muito_negativo": -70,
        "negativo": -30,
        "neutro": 30,
        "positivo": 70,
        "muito_positivo": 100
    }
}

# Parâmetros para recomendação de alocação
ALOCACAO_PARAMS = {
    "EXPANSAO": {
        "Financeiro": 20,
        "Consumo": 15,
        "Tecnologia": 15,
        "Mineração": 10,
        "Energia": 10,
        "Saúde": 10,
        "Transporte": 10,
        "Utilities": 5,
        "Imobiliário": 5,
        "Agronegócio": 0
    },
    "PICO": {
        "Utilities": 20,
        "Saúde": 15,
        "Consumo": 15,
        "Financeiro": 10,
        "Energia": 10,
        "Agronegócio": 10,
        "Tecnologia": 10,
        "Mineração": 5,
        "Imobiliário": 5,
        "Transporte": 0
    },
    "CONTRACAO": {
        "Utilities": 25,
        "Saúde": 20,
        "Consumo": 15,
        "Agronegócio": 15,
        "Financeiro": 10,
        "Energia": 10,
        "Tecnologia": 5,
        "Mineração": 0,
        "Imobiliário": 0,
        "Transporte": 0
    },
    "RECUPERACAO": {
        "Mineração": 20,
        "Energia": 15,
        "Financeiro": 15,
        "Imobiliário": 15,
        "Tecnologia": 10,
        "Transporte": 10,
        "Consumo": 5,
        "Saúde": 5,
        "Utilities": 5,
        "Agronegócio": 0
    }
}
