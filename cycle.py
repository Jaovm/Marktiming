"""
Módulo para identificação de ciclo econômico e market timing.

Este módulo contém funções para detectar a fase atual do ciclo econômico,
gerar scores de market timing e criar alertas visuais baseados no ciclo.
"""

import os
import sys
import json
import datetime
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple

# Adicionar caminho para importar módulos do projeto
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATA_DIR, CACHE_DIR, CICLO_ECONOMICO
from data.macro_data import (
    get_pib_data, get_inflacao_data, get_juros_data, get_curva_juros_data,
    get_trabalho_data, get_risco_data
)
from data.market_data import get_fed_model_data
from analysis.valuation import calcular_premio_risco, calcular_indicadores_valuation_mercado

def calcular_inclinacao_curva_juros(use_cache: bool = True) -> Dict[str, float]:
    """
    Calcula a inclinação da curva de juros brasileira.
    
    Args:
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        Dict[str, float]: Dicionário com métricas de inclinação da curva de juros.
    """
    # Obtém dados da curva de juros
    curva_juros = get_curva_juros_data(use_cache=use_cache)
    
    # Cria dicionário para as métricas
    metricas = {}
    
    if not curva_juros.empty:
        # Obtém os dados mais recentes
        ultimo_dia = curva_juros.iloc[-1]
        
        # Calcula inclinações
        if 'di_30d' in ultimo_dia and 'di_360d' in ultimo_dia:
            metricas['inclinacao_1y_1m'] = ultimo_dia['di_360d'] - ultimo_dia['di_30d']
        
        if 'di_360d' in ultimo_dia and 'di_1080d' in ultimo_dia:
            metricas['inclinacao_3y_1y'] = ultimo_dia['di_1080d'] - ultimo_dia['di_360d']
        
        if 'di_30d' in ultimo_dia and 'di_1080d' in ultimo_dia:
            metricas['inclinacao_3y_1m'] = ultimo_dia['di_1080d'] - ultimo_dia['di_30d']
        
        # Determina se a curva está normal ou invertida
        if 'inclinacao_3y_1m' in metricas:
            if metricas['inclinacao_3y_1m'] > 0.5:
                metricas['status_curva'] = 'Normal'
            elif metricas['inclinacao_3y_1m'] > -0.5:
                metricas['status_curva'] = 'Achatada'
            else:
                metricas['status_curva'] = 'Invertida'
    
    return metricas

def analisar_tendencia_inflacao(use_cache: bool = True) -> Dict[str, str]:
    """
    Analisa a tendência da inflação brasileira.
    
    Args:
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        Dict[str, str]: Dicionário com análise da tendência da inflação.
    """
    # Obtém dados de inflação
    inflacao = get_inflacao_data(use_cache=use_cache)
    
    # Cria dicionário para a análise
    analise = {}
    
    if not inflacao.empty and 'ipca_acumulado_12m' in inflacao.columns:
        # Obtém os últimos 12 meses de dados
        ipca_12m = inflacao['ipca_acumulado_12m'].dropna()
        ultimos_12_meses = ipca_12m[-12:] if len(ipca_12m) >= 12 else ipca_12m
        
        # Calcula a tendência
        if len(ultimos_12_meses) >= 3:
            # Calcula a média móvel de 3 meses
            mm3 = ultimos_12_meses.rolling(window=3).mean()
            
            # Compara o valor atual com a média móvel de 3 meses de 3 meses atrás
            valor_atual = mm3.iloc[-1]
            valor_3_meses_atras = mm3.iloc[-4] if len(mm3) >= 4 else mm3.iloc[0]
            
            if valor_atual < valor_3_meses_atras * 0.95:  # Queda de mais de 5%
                analise['tendencia_ipca'] = 'Desacelerando'
            elif valor_atual > valor_3_meses_atras * 1.05:  # Aumento de mais de 5%
                analise['tendencia_ipca'] = 'Acelerando'
            else:
                analise['tendencia_ipca'] = 'Estável'
        
        # Classifica o nível atual
        ultimo_valor = ultimos_12_meses.iloc[-1]
        
        if ultimo_valor < 3.0:
            analise['nivel_ipca'] = 'Baixo'
        elif ultimo_valor < 5.0:
            analise['nivel_ipca'] = 'Moderado'
        elif ultimo_valor < 8.0:
            analise['nivel_ipca'] = 'Alto'
        else:
            analise['nivel_ipca'] = 'Muito Alto'
    
    return analise

def analisar_tendencia_juros(use_cache: bool = True) -> Dict[str, str]:
    """
    Analisa a tendência da taxa de juros brasileira.
    
    Args:
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        Dict[str, str]: Dicionário com análise da tendência dos juros.
    """
    # Obtém dados de juros
    juros = get_juros_data(use_cache=use_cache)
    
    # Cria dicionário para a análise
    analise = {}
    
    if not juros.empty and 'selic_meta' in juros.columns:
        # Obtém os últimos 12 meses de dados
        selic = juros['selic_meta'].dropna()
        ultimos_12_meses = selic[-12:] if len(selic) >= 12 else selic
        
        # Determina a tendência com base nas últimas decisões do Copom
        if len(ultimos_12_meses) >= 3:
            ultimas_3_decisoes = ultimos_12_meses[-3:]
            
            if ultimas_3_decisoes.iloc[-1] > ultimas_3_decisoes.iloc[-3]:
                analise['tendencia_selic'] = 'Subindo'
            elif ultimas_3_decisoes.iloc[-1] < ultimas_3_decisoes.iloc[-3]:
                analise['tendencia_selic'] = 'Caindo'
            else:
                analise['tendencia_selic'] = 'Estável'
        
        # Classifica o nível atual
        ultimo_valor = ultimos_12_meses.iloc[-1]
        
        if ultimo_valor < 6.0:
            analise['nivel_selic'] = 'Baixo'
        elif ultimo_valor < 9.0:
            analise['nivel_selic'] = 'Moderado'
        elif ultimo_valor < 12.0:
            analise['nivel_selic'] = 'Alto'
        else:
            analise['nivel_selic'] = 'Muito Alto'
    
    return analise

def analisar_indicadores_risco(use_cache: bool = True) -> Dict[str, str]:
    """
    Analisa indicadores de risco do mercado brasileiro.
    
    Args:
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        Dict[str, str]: Dicionário com análise dos indicadores de risco.
    """
    # Obtém dados de risco
    risco = get_risco_data(use_cache=use_cache)
    
    # Cria dicionário para a análise
    analise = {}
    
    if not risco.empty:
        # Analisa CDS Brasil (se disponível)
        if 'GAP12_CRDSCBR5Y' in risco.columns:
            cds = risco['GAP12_CRDSCBR5Y'].dropna()
            
            if not cds.empty:
                ultimo_valor = cds.iloc[-1]
                
                if ultimo_valor < 150:
                    analise['nivel_cds'] = 'Baixo'
                elif ultimo_valor < 250:
                    analise['nivel_cds'] = 'Moderado'
                elif ultimo_valor < 350:
                    analise['nivel_cds'] = 'Alto'
                else:
                    analise['nivel_cds'] = 'Muito Alto'
                
                # Analisa tendência do CDS
                if len(cds) >= 30:
                    media_30d = cds[-30:].mean()
                    
                    if ultimo_valor < media_30d * 0.9:  # Queda de mais de 10%
                        analise['tendencia_cds'] = 'Melhorando'
                    elif ultimo_valor > media_30d * 1.1:  # Aumento de mais de 10%
                        analise['tendencia_cds'] = 'Piorando'
                    else:
                        analise['tendencia_cds'] = 'Estável'
        
        # Analisa EMBI+ Brasil (se disponível)
        if 'embi' in risco.columns:
            embi = risco['embi'].dropna()
            
            if not embi.empty:
                ultimo_valor = embi.iloc[-1]
                
                if ultimo_valor < 200:
                    analise['nivel_embi'] = 'Baixo'
                elif ultimo_valor < 300:
                    analise['nivel_embi'] = 'Moderado'
                elif ultimo_valor < 400:
                    analise['nivel_embi'] = 'Alto'
                else:
                    analise['nivel_embi'] = 'Muito Alto'
        
        # Analisa IFIX (se disponível)
        if 'BMF12_IFIX12' in risco.columns:
            ifix = risco['BMF12_IFIX12'].dropna()
            
            if not ifix.empty and len(ifix) >= 30:
                ultimo_valor = ifix.iloc[-1]
                media_30d = ifix[-30:].mean()
                
                if ultimo_valor < media_30d * 0.95:  # Queda de mais de 5%
                    analise['tendencia_ifix'] = 'Queda'
                elif ultimo_valor > media_30d * 1.05:  # Aumento de mais de 5%
                    analise['tendencia_ifix'] = 'Alta'
                else:
                    analise['tendencia_ifix'] = 'Estável'
    
    return analise

def identificar_fase_ciclo(use_cache: bool = True) -> Dict[str, Union[str, float, Dict]]:
    """
    Identifica a fase atual do ciclo econômico brasileiro.
    
    Args:
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        Dict[str, Union[str, float, Dict]]: Dicionário com a fase do ciclo e detalhes.
    """
    # Obtém análises dos diferentes indicadores
    inclinacao_curva = calcular_inclinacao_curva_juros(use_cache=use_cache)
    tendencia_inflacao = analisar_tendencia_inflacao(use_cache=use_cache)
    tendencia_juros = analisar_tendencia_juros(use_cache=use_cache)
    indicadores_risco = analisar_indicadores_risco(use_cache=use_cache)
    premio_risco = calcular_premio_risco(use_cache=use_cache)
    
    # Inicializa scores para cada fase do ciclo
    scores = {
        'EXPANSAO': 0,
        'PICO': 0,
        'CONTRACAO': 0,
        'RECUPERACAO': 0
    }
    
    # Analisa inclinação da curva de juros
    if 'status_curva' in inclinacao_curva:
        if inclinacao_curva['status_curva'] == 'Normal':
            scores['EXPANSAO'] += 2
            scores['RECUPERACAO'] += 1
        elif inclinacao_curva['status_curva'] == 'Achatada':
            scores['PICO'] += 1
            scores['RECUPERACAO'] += 1
        elif inclinacao_curva['status_curva'] == 'Invertida':
            scores['PICO'] += 2
            scores['CONTRACAO'] += 2
    
    # Analisa tendência da inflação
    if 'tendencia_ipca' in tendencia_inflacao:
        if tendencia_inflacao['tendencia_ipca'] == 'Acelerando':
            scores['EXPANSAO'] += 1
            scores['PICO'] += 2
        elif tendencia_inflacao['tendencia_ipca'] == 'Estável':
            scores['EXPANSAO'] += 1
            scores['CONTRACAO'] += 1
        elif tendencia_inflacao['tendencia_ipca'] == 'Desacelerando':
            scores['CONTRACAO'] += 1
            scores['RECUPERACAO'] += 2
    
    # Analisa nível da inflação
    if 'nivel_ipca' in tendencia_inflacao:
        if tendencia_inflacao['nivel_ipca'] == 'Baixo':
            scores['RECUPERACAO'] += 2
        elif tendencia_inflacao['nivel_ipca'] == 'Moderado':
            scores['EXPANSAO'] += 1
        elif tendencia_inflacao['nivel_ipca'] == 'Alto':
            scores['PICO'] += 1
        elif tendencia_inflacao['nivel_ipca'] == 'Muito Alto':
            scores['PICO'] += 2
    
    # Analisa tendência dos juros
    if 'tendencia_selic' in tendencia_juros:
        if tendencia_juros['tendencia_selic'] == 'Subindo':
            scores['PICO'] += 2
            scores['EXPANSAO'] += 1
        elif tendencia_juros['tendencia_selic'] == 'Estável':
            scores['EXPANSAO'] += 1
            scores['CONTRACAO'] += 1
        elif tendencia_juros['tendencia_selic'] == 'Caindo':
            scores['CONTRACAO'] += 1
            scores['RECUPERACAO'] += 2
    
    # Analisa nível dos juros
    if 'nivel_selic' in tendencia_juros:
        if tendencia_juros['nivel_selic'] == 'Baixo':
            scores['RECUPERACAO'] += 2
            scores['EXPANSAO'] += 1
        elif tendencia_juros['nivel_selic'] == 'Moderado':
            scores['EXPANSAO'] += 1
        elif tendencia_juros['nivel_selic'] == 'Alto':
            scores['PICO'] += 1
            scores['CONTRACAO'] += 1
        elif tendencia_juros['nivel_selic'] == 'Muito Alto':
            scores['CONTRACAO'] += 2
    
    # Analisa indicadores de risco
    if 'nivel_cds' in indicadores_risco:
        if indicadores_risco['nivel_cds'] == 'Baixo':
            scores['EXPANSAO'] += 1
            scores['RECUPERACAO'] += 1
        elif indicadores_risco['nivel_cds'] == 'Alto' or indicadores_risco['nivel_cds'] == 'Muito Alto':
            scores['PICO'] += 1
            scores['CONTRACAO'] += 1
    
    if 'tendencia_cds' in indicadores_risco:
        if indicadores_risco['tendencia_cds'] == 'Melhorando':
            scores['RECUPERACAO'] += 1
        elif indicadores_risco['tendencia_cds'] == 'Piorando':
            scores['PICO'] += 1
    
    # Analisa prêmio de risco
    if not premio_risco.empty and 'Prêmio de Risco (%)' in premio_risco.columns:
        premio = premio_risco['Prêmio de Risco (%)'].iloc[0]
        
        if premio > 3:
            scores['CONTRACAO'] += 1
            scores['RECUPERACAO'] += 2
        elif premio > 0:
            scores['EXPANSAO'] += 1
        elif premio > -3:
            scores['PICO'] += 1
        else:
            scores['PICO'] += 2
    
    # Determina a fase do ciclo com base nos scores
    fase_atual = max(scores.items(), key=lambda x: x[1])[0]
    
    # Calcula o score de confiança (normalizado para 0-100%)
    total_score = sum(scores.values())
    confianca = (scores[fase_atual] / total_score * 100) if total_score > 0 else 0
    
    # Determina a cor do alerta com base na fase
    if fase_atual == 'EXPANSAO':
        cor_alerta = CICLO_ECONOMICO['EXPANSAO']['cor']
    elif fase_atual == 'PICO':
        cor_alerta = CICLO_ECONOMICO['PICO']['cor']
    elif fase_atual == 'CONTRACAO':
        cor_alerta = CICLO_ECONOMICO['CONTRACAO']['cor']
    else:  # RECUPERACAO
        cor_alerta = CICLO_ECONOMICO['RECUPERACAO']['cor']
    
    # Cria o resultado
    resultado = {
        'fase': fase_atual,
        'descricao': CICLO_ECONOMICO[fase_atual]['descricao'],
        'confianca': confianca,
        'scores': scores,
        'cor_alerta': cor_alerta,
        'detalhes': {
            'curva_juros': inclinacao_curva,
            'inflacao': tendencia_inflacao,
            'juros': tendencia_juros,
            'risco': indicadores_risco
        }
    }
    
    return resultado

def calcular_market_timing_score(use_cache: bool = True) -> Dict[str, Union[float, str, Dict]]:
    """
    Calcula o score de market timing para o mercado brasileiro.
    
    Args:
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        Dict[str, Union[float, str, Dict]]: Dicionário com o score de market timing e detalhes.
    """
    # Obtém a fase do ciclo econômico
    ciclo = identificar_fase_ciclo(use_cache=use_cache)
    
    # Obtém indicadores de valuation
    indicadores_valuation = calcular_indicadores_valuation_mercado(use_cache=use_cache)
    
    # Inicializa o score de market timing
    score = 0
    max_score = 10
    detalhes = {}
    
    # Avalia com base na fase do ciclo
    if ciclo['fase'] == 'EXPANSAO':
        score += 2
        detalhes['ciclo'] = 'Fase de expansão (+2)'
    elif ciclo['fase'] == 'RECUPERACAO':
        score += 3
        detalhes['ciclo'] = 'Fase de recuperação (+3)'
    elif ciclo['fase'] == 'PICO':
        score -= 2
        detalhes['ciclo'] = 'Fase de pico (-2)'
    elif ciclo['fase'] == 'CONTRACAO':
        score -= 3
        detalhes['ciclo'] = 'Fase de contração (-3)'
    
    # Avalia com base no prêmio de risco
    if 'Prêmio de Risco (%)' in indicadores_valuation:
        premio = indicadores_valuation['Prêmio de Risco (%)']
        
        if premio > 5:
            score += 3
            detalhes['premio_risco'] = f'Prêmio de risco muito alto: {premio:.2f}% (+3)'
        elif premio > 3:
            score += 2
            detalhes['premio_risco'] = f'Prêmio de risco alto: {premio:.2f}% (+2)'
        elif premio > 1:
            score += 1
            detalhes['premio_risco'] = f'Prêmio de risco positivo: {premio:.2f}% (+1)'
        elif premio > -1:
            score += 0
            detalhes['premio_risco'] = f'Prêmio de risco neutro: {premio:.2f}% (0)'
        elif premio > -3:
            score -= 1
            detalhes['premio_risco'] = f'Prêmio de risco negativo: {premio:.2f}% (-1)'
        elif premio > -5:
            score -= 2
            detalhes['premio_risco'] = f'Prêmio de risco muito negativo: {premio:.2f}% (-2)'
        else:
            score -= 3
            detalhes['premio_risco'] = f'Prêmio de risco extremamente negativo: {premio:.2f}% (-3)'
    
    # Avalia com base na inclinação da curva de juros
    if 'curva_juros' in ciclo['detalhes'] and 'status_curva' in ciclo['detalhes']['curva_juros']:
        status_curva = ciclo['detalhes']['curva_juros']['status_curva']
        
        if status_curva == 'Normal':
            score += 1
            detalhes['curva_juros'] = 'Curva de juros normal (+1)'
        elif status_curva == 'Achatada':
            score += 0
            detalhes['curva_juros'] = 'Curva de juros achatada (0)'
        elif status_curva == 'Invertida':
            score -= 2
            detalhes['curva_juros'] = 'Curva de juros invertida (-2)'
    
    # Avalia com base no P/L médio do mercado
    if 'P/L Médio Mercado' in indicadores_valuation:
        pl_medio = indicadores_valuation['P/L Médio Mercado']
        
        if pl_medio < 8:
            score += 2
            detalhes['pl_medio'] = f'P/L médio muito baixo: {pl_medio:.2f} (+2)'
        elif pl_medio < 12:
            score += 1
            detalhes['pl_medio'] = f'P/L médio baixo: {pl_medio:.2f} (+1)'
        elif pl_medio < 16:
            score += 0
            detalhes['pl_medio'] = f'P/L médio neutro: {pl_medio:.2f} (0)'
        elif pl_medio < 20:
            score -= 1
            detalhes['pl_medio'] = f'P/L médio alto: {pl_medio:.2f} (-1)'
        else:
            score -= 2
            detalhes['pl_medio'] = f'P/L médio muito alto: {pl_medio:.2f} (-2)'
    
    # Normaliza o score para o intervalo [-100, 100]
    score_normalizado = (score / max_score) * 100
    
    # Determina a recomendação com base no score
    if score_normalizado >= 70:
        recomendacao = 'COMPRA FORTE'
        cor = '#4CAF50'  # Verde
    elif score_normalizado >= 30:
        recomendacao = 'COMPRA'
        cor = '#8BC34A'  # Verde claro
    elif score_normalizado >= -30:
        recomendacao = 'NEUTRO'
        cor = '#FFC107'  # Amarelo
    elif score_normalizado >= -70:
        recomendacao = 'VENDA'
        cor = '#FF9800'  # Laranja
    else:
        recomendacao = 'VENDA FORTE'
        cor = '#F44336'  # Vermelho
    
    # Cria o resultado
    resultado = {
        'score': score_normalizado,
        'recomendacao': recomendacao,
        'cor': cor,
        'detalhes': detalhes,
        'data': datetime.datetime.now().strftime('%Y-%m-%d')
    }
    
    return resultado

def gerar_alertas_market_timing(use_cache: bool = True) -> List[Dict[str, str]]:
    """
    Gera alertas de market timing com base na análise do ciclo econômico.
    
    Args:
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        List[Dict[str, str]]: Lista de alertas de market timing.
    """
    # Obtém a fase do ciclo econômico
    ciclo = identificar_fase_ciclo(use_cache=use_cache)
    
    # Obtém o score de market timing
    timing = calcular_market_timing_score(use_cache=use_cache)
    
    # Lista de alertas
    alertas = []
    
    # Alerta baseado na fase do ciclo
    alertas.append({
        'tipo': 'Ciclo Econômico',
        'mensagem': f"O Brasil está na fase de {ciclo['fase'].lower()} do ciclo econômico.",
        'cor': ciclo['cor_alerta'],
        'importancia': 'Alta'
    })
    
    # Alerta baseado no score de market timing
    alertas.append({
        'tipo': 'Market Timing',
        'mensagem': f"Sinal de market timing: {timing['recomendacao']} (score: {timing['score']:.1f}).",
        'cor': timing['cor'],
        'importancia': 'Alta'
    })
    
    # Alertas baseados em detalhes específicos
    if 'curva_juros' in ciclo['detalhes'] and 'status_curva' in ciclo['detalhes']['curva_juros']:
        if ciclo['detalhes']['curva_juros']['status_curva'] == 'Invertida':
            alertas.append({
                'tipo': 'Curva de Juros',
                'mensagem': "Curva de juros invertida: possível sinal de desaceleração econômica futura.",
                'cor': '#F44336',  # Vermelho
                'importancia': 'Alta'
            })
    
    if 'inflacao' in ciclo['detalhes'] and 'tendencia_ipca' in ciclo['detalhes']['inflacao']:
        if ciclo['detalhes']['inflacao']['tendencia_ipca'] == 'Acelerando':
            alertas.append({
                'tipo': 'Inflação',
                'mensagem': "Inflação em aceleração: possível pressão para aumento de juros.",
                'cor': '#FF9800',  # Laranja
                'importancia': 'Média'
            })
    
    if 'juros' in ciclo['detalhes'] and 'tendencia_selic' in ciclo['detalhes']['juros']:
        if ciclo['detalhes']['juros']['tendencia_selic'] == 'Subindo':
            alertas.append({
                'tipo': 'Juros',
                'mensagem': "Juros em alta: possível pressão sobre ativos de risco.",
                'cor': '#FF9800',  # Laranja
                'importancia': 'Média'
            })
        elif ciclo['detalhes']['juros']['tendencia_selic'] == 'Caindo':
            alertas.append({
                'tipo': 'Juros',
                'mensagem': "Juros em queda: possível suporte para ativos de risco.",
                'cor': '#4CAF50',  # Verde
                'importancia': 'Média'
            })
    
    if 'risco' in ciclo['detalhes'] and 'tendencia_cds' in ciclo['detalhes']['risco']:
        if ciclo['detalhes']['risco']['tendencia_cds'] == 'Piorando':
            alertas.append({
                'tipo': 'Risco País',
                'mensagem': "Risco país em alta: possível pressão sobre ativos brasileiros.",
                'cor': '#F44336',  # Vermelho
                'importancia': 'Média'
            })
    
    return alertas

if __name__ == "__main__":
    # Teste das funções
    print("Testando funções de identificação de ciclo econômico e market timing...")
    
    # Identifica a fase do ciclo econômico
    ciclo = identificar_fase_ciclo(use_cache=False)
    print("\nFase do Ciclo Econômico:")
    print(f"Fase: {ciclo['fase']}")
    print(f"Descrição: {ciclo['descricao']}")
    print(f"Confiança: {ciclo['confianca']:.1f}%")
    
    # Calcula o score de market timing
    timing = calcular_market_timing_score(use_cache=False)
    print("\nScore de Market Timing:")
    print(f"Score: {timing['score']:.1f}")
    print(f"Recomendação: {timing['recomendacao']}")
    
    # Gera alertas de market timing
    alertas = gerar_alertas_market_timing(use_cache=False)
    print("\nAlertas de Market Timing:")
    for alerta in alertas:
        print(f"{alerta['tipo']}: {alerta['mensagem']} ({alerta['importancia']})")
