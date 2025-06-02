"""
Configurações globais do painel de Market Timing e Análise Macroeconômica.
"""
import os
from pathlib import Path

# Diretórios do projeto
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"

# Criar diretórios se não existirem
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# Configurações de cache
CACHE_EXPIRY = {
    "macro_diario": 24,  # horas
    "macro_semanal": 24 * 7,  # horas
    "macro_mensal": 24 * 30,  # horas
    "acoes_diario": 24,  # horas
    "acoes_semanal": 24 * 7,  # horas
}

# Configurações de APIs
API_RETRY_ATTEMPTS = 3
API_TIMEOUT = 30  # segundos

# Configurações de visualização
THEME = {
    "primary": "#1E88E5",
    "secondary": "#FFC107",
    "background": "#FFFFFF",
    "text": "#212121",
    "positive": "#4CAF50",
    "negative": "#F44336",
    "neutral": "#FFC107",
}

# Configurações de análise
PERIODOS_HISTORICOS = [5, 10]  # anos
SETORES_B3 = [
    "Financeiro",
    "Energia",
    "Materiais Básicos",
    "Bens Industriais",
    "Consumo Cíclico",
    "Consumo Não Cíclico",
    "Saúde",
    "Tecnologia da Informação",
    "Telecomunicações",
    "Utilidade Pública",
    "Imobiliário"
]

# Carteira base para análise
CARTEIRA_BASE = [
    "AGRO3", "BBAS3", "BBSE3", "BPAC11", "EGIE3", 
    "ITUB3", "PRIO3", "PSSA3", "SAPR3", "SBSP3", 
    "VIVT3", "WEGE3", "TOTS3", "B3SA3", "TAEE3", "CMIG3"
]

# Configurações de ciclo econômico
CICLO_ECONOMICO = {
    "EXPANSAO": {
        "cor": "#4CAF50",
        "descricao": "Fase de crescimento econômico, inflação controlada e juros estáveis ou em queda.",
        "setores_favorecidos": ["Consumo Cíclico", "Tecnologia da Informação", "Bens Industriais"]
    },
    "PICO": {
        "cor": "#FFC107",
        "descricao": "Fase de crescimento desacelerando, inflação subindo e juros em alta.",
        "setores_favorecidos": ["Financeiro", "Materiais Básicos", "Energia"]
    },
    "CONTRACAO": {
        "cor": "#F44336",
        "descricao": "Fase de crescimento negativo ou baixo, inflação alta e juros elevados.",
        "setores_favorecidos": ["Utilidade Pública", "Consumo Não Cíclico", "Saúde"]
    },
    "RECUPERACAO": {
        "cor": "#FFC107",
        "descricao": "Fase de retomada do crescimento, inflação controlada e juros em queda.",
        "setores_favorecidos": ["Imobiliário", "Financeiro", "Consumo Cíclico"]
    }
}
