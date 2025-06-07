"""
Módulo para recomendação de alocação setorial com base no ciclo econômico.

Este módulo contém funções para recomendar alocação setorial, analisar
alinhamento da carteira atual e sugerir ajustes de risco.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
import datetime

# Importa as configurações e dados
from config import ALOCACAO_PARAMS, SETORES_B3, CARTEIRA_BASE
from cycle import identificar_fase_ciclo, calcular_market_timing_score
from valuation import classificar_valuation_setorial

def recomendar_alocacao_setorial() -> Dict[str, Union[str, Dict, List]]:
    """
    Recomenda alocação setorial com base na fase atual do ciclo econômico.
    
    Returns:
        Dict: Dicionário com recomendações de alocação setorial.
    """
    # Obtém a fase atual do ciclo econômico
    ciclo = identificar_fase_ciclo()
    fase = ciclo['fase']
    
    # Obtém o score de market timing
    timing = calcular_market_timing_score()
    score = timing['score']
    
    # Obtém a alocação recomendada para a fase atual
    alocacao_recomendada = ALOCACAO_PARAMS[fase]
    
    # Descrições das fases do ciclo
    descricoes = {
        'EXPANSAO': "Fase de crescimento econômico sustentado, com aumento da produção, emprego e consumo. Inflação tende a acelerar e o Banco Central geralmente eleva os juros para conter pressões inflacionárias.",
        'PICO': "Fase de maturidade do ciclo, com economia operando próxima ao pleno emprego. Inflação elevada, juros altos e sinais de desaceleração começam a aparecer.",
        'CONTRACAO': "Fase de desaceleração econômica, com queda na produção, aumento do desemprego e redução do consumo. Banco Central geralmente inicia ciclo de corte de juros.",
        'RECUPERACAO': "Fase inicial de retomada econômica após período de contração. Desemprego ainda elevado mas em queda, inflação controlada e juros baixos para estimular a economia."
    }
    
    # Determina o nível de risco recomendado com base na fase do ciclo e no score de market timing
    if fase == 'EXPANSAO':
        if score > 50:
            nivel_risco = "Moderado para Alto"
            justificativa = [
                "Economia em crescimento sustentado",
                "Indicadores de market timing favoráveis",
                "Potencial de valorização em setores cíclicos"
            ]
        elif score > 0:
            nivel_risco = "Moderado"
            justificativa = [
                "Economia em crescimento",
                "Indicadores de market timing neutros a positivos",
                "Balanceamento entre setores cíclicos e defensivos"
            ]
        else:
            nivel_risco = "Moderado para Baixo"
            justificativa = [
                "Economia em crescimento, mas indicadores de market timing negativos",
                "Possível desaceleração à frente",
                "Preferência por setores menos sensíveis ao ciclo"
            ]
    elif fase == 'PICO':
        if score > 0:
            nivel_risco = "Moderado"
            justificativa = [
                "Economia próxima ao pico do ciclo",
                "Indicadores de market timing ainda positivos",
                "Rotação para setores mais defensivos recomendada"
            ]
        else:
            nivel_risco = "Baixo"
            justificativa = [
                "Economia no pico do ciclo com sinais de desaceleração",
                "Indicadores de market timing negativos",
                "Preferência por setores defensivos e proteção de capital"
            ]
    elif fase == 'CONTRACAO':
        if score > 0:
            nivel_risco = "Baixo para Moderado"
            justificativa = [
                "Economia em contração",
                "Indicadores de market timing surpreendentemente positivos",
                "Oportunidades seletivas em setores de valor"
            ]
        else:
            nivel_risco = "Muito Baixo"
            justificativa = [
                "Economia em contração significativa",
                "Indicadores de market timing negativos",
                "Foco em preservação de capital e setores defensivos"
            ]
    else:  # RECUPERACAO
        if score > 50:
            nivel_risco = "Alto"
            justificativa = [
                "Economia em recuperação consistente",
                "Indicadores de market timing muito positivos",
                "Momento favorável para setores cíclicos e de valor"
            ]
        elif score > 0:
            nivel_risco = "Moderado para Alto"
            justificativa = [
                "Economia em recuperação",
                "Indicadores de market timing positivos",
                "Aumento gradual da exposição a setores cíclicos"
            ]
        else:
            nivel_risco = "Moderado"
            justificativa = [
                "Economia em recuperação inicial",
                "Indicadores de market timing ainda não confirmados",
                "Abordagem cautelosa com foco em qualidade"
            ]
    
    # Retorna as recomendações
    return {
        'fase_ciclo': fase,
        'descricao_fase': descricoes[fase],
        'alocacao_recomendada': alocacao_recomendada,
        'nivel_risco': nivel_risco,
        'justificativa': justificativa,
        'score_timing': score
    }

def analisar_alinhamento_carteira(carteira: Dict[str, float]) -> Dict[str, Union[float, List]]:
    """
    Analisa o alinhamento da carteira atual com a fase do ciclo econômico.
    
    Args:
        carteira: Dicionário com tickers e pesos da carteira.
        
    Returns:
        Dict: Dicionário com análise de alinhamento da carteira.
    """
    # Obtém a recomendação de alocação setorial
    recomendacao = recomendar_alocacao_setorial()
    fase = recomendacao['fase_ciclo']
    alocacao_recomendada = recomendacao['alocacao_recomendada']
    
    # Inicializa a alocação atual por setor
    alocacao_atual = {setor: 0 for setor in SETORES_B3.keys()}
    
    # Mapeia os tickers da carteira para seus respectivos setores
    mapeamento_setor = {}
    for setor, tickers in SETORES_B3.items():
        for ticker in tickers:
            mapeamento_setor[ticker] = setor
    
    # Calcula a alocação atual por setor
    for ticker, peso in carteira.items():
        if ticker in mapeamento_setor:
            setor = mapeamento_setor[ticker]
            alocacao_atual[setor] += peso
    
    # Calcula o alinhamento da carteira
    alinhamento_score = 0
    max_diferenca = 0
    
    for setor, peso_recomendado in alocacao_recomendada.items():
        peso_atual = alocacao_atual.get(setor, 0)
        diferenca = abs(peso_atual - peso_recomendado)
        max_diferenca += max(peso_atual, peso_recomendado)
        alinhamento_score += min(peso_atual, peso_recomendado)
    
    # Normaliza o score de alinhamento (0-100%)
    alinhamento_score = (alinhamento_score / 100) * 100 if max_diferenca > 0 else 0
    
    # Identifica ações alinhadas e desalinhadas
    acoes_alinhadas = []
    acoes_desalinhadas = []
    
    for ticker, peso in carteira.items():
        if ticker in mapeamento_setor:
            setor = mapeamento_setor[ticker]
            peso_recomendado_setor = alocacao_recomendada.get(setor, 0)
            
            # Verifica se o setor está alinhado com a recomendação
            if peso_recomendado_setor >= 10:  # Setores com peso recomendado significativo
                acoes_alinhadas.append({
                    'ticker': ticker,
                    'setor': setor,
                    'peso': peso,
                    'alinhamento': 'Alto'
                })
            elif peso_recomendado_setor <= 5:  # Setores com peso recomendado baixo
                acoes_desalinhadas.append({
                    'ticker': ticker,
                    'setor': setor,
                    'peso': peso,
                    'alinhamento': 'Baixo'
                })
            else:
                acoes_alinhadas.append({
                    'ticker': ticker,
                    'setor': setor,
                    'peso': peso,
                    'alinhamento': 'Médio'
                })
    
    # Ordena as ações por peso
    acoes_alinhadas = sorted(acoes_alinhadas, key=lambda x: x['peso'], reverse=True)
    acoes_desalinhadas = sorted(acoes_desalinhadas, key=lambda x: x['peso'], reverse=True)
    
    # Retorna a análise
    return {
        'alinhamento_score': alinhamento_score,
        'alocacao_atual': alocacao_atual,
        'alocacao_recomendada': alocacao_recomendada,
        'acoes_alinhadas': acoes_alinhadas,
        'acoes_desalinhadas': acoes_desalinhadas
    }

def sugerir_ajuste_risco_carteira() -> Dict[str, Union[str, List]]:
    """
    Sugere ajustes de risco para a carteira com base no ciclo econômico e market timing.
    
    Returns:
        Dict: Dicionário com sugestões de ajuste de risco.
    """
    # Obtém a recomendação de alocação setorial
    recomendacao = recomendar_alocacao_setorial()
    fase = recomendacao['fase_ciclo']
    nivel_risco = recomendacao['nivel_risco']
    score_timing = recomendacao['score_timing']
    
    # Inicializa as sugestões
    sugestoes = []
    
    # Sugere ajustes com base na fase do ciclo e no score de market timing
    if fase == 'EXPANSAO':
        if score_timing > 50:
            sugestoes.append("Aumentar exposição a setores cíclicos (Financeiro, Consumo, Tecnologia)")
            sugestoes.append("Reduzir posições em setores defensivos (Utilities, Saúde)")
            sugestoes.append("Considerar aumento da alavancagem em posições de maior convicção")
        elif score_timing > 0:
            sugestoes.append("Manter exposição balanceada entre setores cíclicos e defensivos")
            sugestoes.append("Priorizar empresas de qualidade com crescimento consistente")
            sugestoes.append("Evitar alavancagem excessiva")
        else:
            sugestoes.append("Reduzir gradualmente exposição a setores mais sensíveis ao ciclo")
            sugestoes.append("Aumentar posições em empresas de qualidade e dividendos")
            sugestoes.append("Manter reserva de caixa para oportunidades futuras")
    elif fase == 'PICO':
        if score_timing > 0:
            sugestoes.append("Iniciar rotação para setores mais defensivos (Utilities, Saúde, Consumo Básico)")
            sugestoes.append("Reduzir exposição a setores cíclicos de forma gradual")
            sugestoes.append("Aumentar qualidade da carteira, priorizando empresas com baixo endividamento")
        else:
            sugestoes.append("Reduzir significativamente exposição a setores cíclicos")
            sugestoes.append("Aumentar posições em setores defensivos e empresas de dividendos")
            sugestoes.append("Elevar reserva de caixa para aproveitar oportunidades na fase de contração")
    elif fase == 'CONTRACAO':
        if score_timing > 0:
            sugestoes.append("Manter posições defensivas, mas iniciar alocação seletiva em setores de valor")
            sugestoes.append("Buscar empresas com balanços sólidos e vantagens competitivas")
            sugestoes.append("Manter reserva de caixa para oportunidades")
        else:
            sugestoes.append("Maximizar exposição a setores defensivos (Utilities, Saúde)")
            sugestoes.append("Priorizar preservação de capital e empresas com dividendos consistentes")
            sugestoes.append("Manter reserva de caixa significativa para aproveitar o ponto de inflexão")
    else:  # RECUPERACAO
        if score_timing > 50:
            sugestoes.append("Aumentar significativamente exposição a setores cíclicos e de valor")
            sugestoes.append("Reduzir posições em setores defensivos")
            sugestoes.append("Considerar empresas de menor capitalização com potencial de recuperação")
        elif score_timing > 0:
            sugestoes.append("Aumentar gradualmente exposição a setores cíclicos")
            sugestoes.append("Manter algumas posições defensivas para equilíbrio")
            sugestoes.append("Focar em empresas de qualidade com potencial de crescimento")
        else:
            sugestoes.append("Manter abordagem cautelosa, com exposição balanceada")
            sugestoes.append("Priorizar empresas de qualidade em setores menos sensíveis ao ciclo")
            sugestoes.append("Aguardar confirmação dos indicadores antes de aumentar risco")
    
    # Sugere ajustes específicos com base no valuation setorial
    classificacao = classificar_valuation_setorial()
    if not classificacao.empty:
        setores_baratos = classificacao[classificacao['Classificação'].isin(['Barato', 'Muito Barato'])].index.tolist()
        setores_caros = classificacao[classificacao['Classificação'].isin(['Caro', 'Muito Caro'])].index.tolist()
        
        if setores_baratos:
            # Filtra setores baratos que estão alinhados com a fase do ciclo
            setores_baratos_alinhados = [setor for setor in setores_baratos if recomendacao['alocacao_recomendada'].get(setor, 0) >= 10]
            if setores_baratos_alinhados:
                sugestoes.append(f"Priorizar alocação nos setores com valuation atrativo e alinhados ao ciclo: {', '.join(setores_baratos_alinhados)}")
        
        if setores_caros:
            # Filtra setores caros que não estão alinhados com a fase do ciclo
            setores_caros_desalinhados = [setor for setor in setores_caros if recomendacao['alocacao_recomendada'].get(setor, 0) <= 5]
            if setores_caros_desalinhados:
                sugestoes.append(f"Reduzir exposição aos setores com valuation elevado e desalinhados do ciclo: {', '.join(setores_caros_desalinhados)}")
    
    # Retorna as sugestões
    return {
        'nivel_risco_recomendado': nivel_risco,
        'fase_ciclo': fase,
        'sugestoes': sugestoes
    }
