"""
Módulo para recomendação de alocação setorial com base no ciclo econômico.

Este módulo contém funções para gerar recomendações de alocação em setores da B3,
ajustar o nível de risco da carteira e analisar o alinhamento da carteira atual
com o ciclo econômico identificado.
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

from config import DATA_DIR, CACHE_DIR, CICLO_ECONOMICO, SETORES_B3, CARTEIRA_BASE
from data.market_data import get_valuation_data, get_sector_valuation, get_stock_info
from analysis.cycle import identificar_fase_ciclo, calcular_market_timing_score
from analysis.valuation import classificar_valuation_setorial, analisar_carteira

def recomendar_alocacao_setorial(use_cache: bool = True) -> Dict[str, Union[str, Dict, List]]:
    """
    Recomenda alocação setorial com base na fase atual do ciclo econômico.
    
    Args:
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        Dict[str, Union[str, Dict, List]]: Dicionário com recomendações de alocação.
    """
    # Identifica a fase atual do ciclo econômico
    ciclo = identificar_fase_ciclo(use_cache=use_cache)
    fase_atual = ciclo['fase']
    
    # Obtém o score de market timing
    timing = calcular_market_timing_score(use_cache=use_cache)
    
    # Obtém classificação de valuation setorial
    valuation_setorial = classificar_valuation_setorial(use_cache=use_cache)
    
    # Setores favorecidos na fase atual do ciclo
    setores_favorecidos = CICLO_ECONOMICO[fase_atual]['setores_favorecidos']
    
    # Cria dicionário para as recomendações
    recomendacoes = {
        'fase_ciclo': fase_atual,
        'descricao_fase': CICLO_ECONOMICO[fase_atual]['descricao'],
        'market_timing_score': timing['score'],
        'market_timing_recomendacao': timing['recomendacao'],
        'setores_favorecidos': setores_favorecidos,
        'alocacao_recomendada': {},
        'nivel_risco': '',
        'justificativa': []
    }
    
    # Define o nível de risco recomendado com base no score de market timing
    if timing['score'] >= 70:
        recomendacoes['nivel_risco'] = 'Agressivo'
        recomendacoes['justificativa'].append('Score de market timing muito positivo, favorecendo maior exposição a risco.')
    elif timing['score'] >= 30:
        recomendacoes['nivel_risco'] = 'Moderado para Agressivo'
        recomendacoes['justificativa'].append('Score de market timing positivo, favorecendo exposição moderada a risco.')
    elif timing['score'] >= -30:
        recomendacoes['nivel_risco'] = 'Neutro'
        recomendacoes['justificativa'].append('Score de market timing neutro, sugerindo manutenção de alocação balanceada.')
    elif timing['score'] >= -70:
        recomendacoes['nivel_risco'] = 'Moderado para Defensivo'
        recomendacoes['justificativa'].append('Score de market timing negativo, sugerindo redução da exposição a risco.')
    else:
        recomendacoes['nivel_risco'] = 'Defensivo'
        recomendacoes['justificativa'].append('Score de market timing muito negativo, indicando postura defensiva.')
    
    # Recomendações de alocação por fase do ciclo
    if fase_atual == 'EXPANSAO':
        # Na fase de expansão, favorece setores cíclicos e de crescimento
        recomendacoes['alocacao_recomendada'] = {
            'Consumo Cíclico': 20,
            'Tecnologia da Informação': 15,
            'Bens Industriais': 15,
            'Financeiro': 15,
            'Materiais Básicos': 10,
            'Saúde': 5,
            'Energia': 5,
            'Consumo Não Cíclico': 5,
            'Utilidade Pública': 5,
            'Telecomunicações': 3,
            'Imobiliário': 2
        }
        recomendacoes['justificativa'].append('Fase de expansão favorece setores cíclicos e de crescimento.')
        
    elif fase_atual == 'PICO':
        # Na fase de pico, favorece setores com poder de precificação e commodities
        recomendacoes['alocacao_recomendada'] = {
            'Financeiro': 20,
            'Materiais Básicos': 15,
            'Energia': 15,
            'Utilidade Pública': 10,
            'Consumo Não Cíclico': 10,
            'Saúde': 10,
            'Tecnologia da Informação': 5,
            'Telecomunicações': 5,
            'Bens Industriais': 5,
            'Consumo Cíclico': 3,
            'Imobiliário': 2
        }
        recomendacoes['justificativa'].append('Fase de pico favorece setores com poder de precificação e commodities.')
        
    elif fase_atual == 'CONTRACAO':
        # Na fase de contração, favorece setores defensivos
        recomendacoes['alocacao_recomendada'] = {
            'Utilidade Pública': 20,
            'Consumo Não Cíclico': 20,
            'Saúde': 15,
            'Telecomunicações': 10,
            'Financeiro': 10,
            'Energia': 10,
            'Tecnologia da Informação': 5,
            'Materiais Básicos': 5,
            'Bens Industriais': 3,
            'Consumo Cíclico': 2,
            'Imobiliário': 0
        }
        recomendacoes['justificativa'].append('Fase de contração favorece setores defensivos e de dividendos.')
        
    elif fase_atual == 'RECUPERACAO':
        # Na fase de recuperação, favorece setores cíclicos e financeiros
        recomendacoes['alocacao_recomendada'] = {
            'Imobiliário': 15,
            'Financeiro': 15,
            'Consumo Cíclico': 15,
            'Bens Industriais': 10,
            'Tecnologia da Informação': 10,
            'Materiais Básicos': 10,
            'Energia': 10,
            'Saúde': 5,
            'Consumo Não Cíclico': 5,
            'Utilidade Pública': 3,
            'Telecomunicações': 2
        }
        recomendacoes['justificativa'].append('Fase de recuperação favorece setores cíclicos e financeiros.')
    
    # Ajusta a alocação com base no valuation setorial
    if not valuation_setorial.empty and 'Classificação' in valuation_setorial.columns:
        for setor in SETORES_B3:
            if setor in valuation_setorial.index and setor in recomendacoes['alocacao_recomendada']:
                classificacao = valuation_setorial.loc[setor, 'Classificação']
                
                # Ajusta a alocação com base no valuation
                if classificacao == 'Muito Barato':
                    # Aumenta a alocação em setores muito baratos
                    recomendacoes['alocacao_recomendada'][setor] += 5
                    recomendacoes['justificativa'].append(f'Aumento em {setor} devido a valuation muito atrativo.')
                elif classificacao == 'Muito Caro':
                    # Reduz a alocação em setores muito caros
                    recomendacoes['alocacao_recomendada'][setor] = max(0, recomendacoes['alocacao_recomendada'][setor] - 5)
                    recomendacoes['justificativa'].append(f'Redução em {setor} devido a valuation muito elevado.')
        
        # Normaliza as alocações para somar 100%
        total = sum(recomendacoes['alocacao_recomendada'].values())
        if total > 0:
            for setor in recomendacoes['alocacao_recomendada']:
                recomendacoes['alocacao_recomendada'][setor] = round(recomendacoes['alocacao_recomendada'][setor] / total * 100, 1)
    
    # Adiciona recomendação de caixa/renda fixa com base no market timing
    if timing['score'] < -50:
        recomendacoes['caixa_renda_fixa'] = 30
        recomendacoes['justificativa'].append('Elevada alocação em caixa/renda fixa devido ao cenário de alto risco.')
    elif timing['score'] < -20:
        recomendacoes['caixa_renda_fixa'] = 20
        recomendacoes['justificativa'].append('Alocação moderada em caixa/renda fixa para reduzir exposição a risco.')
    elif timing['score'] < 20:
        recomendacoes['caixa_renda_fixa'] = 10
        recomendacoes['justificativa'].append('Alocação neutra em caixa/renda fixa.')
    elif timing['score'] < 50:
        recomendacoes['caixa_renda_fixa'] = 5
        recomendacoes['justificativa'].append('Baixa alocação em caixa/renda fixa para aumentar exposição a renda variável.')
    else:
        recomendacoes['caixa_renda_fixa'] = 0
        recomendacoes['justificativa'].append('Mínima alocação em caixa/renda fixa devido ao cenário muito favorável para renda variável.')
    
    return recomendacoes

def analisar_alinhamento_carteira(tickers: List[str] = None, use_cache: bool = True) -> Dict[str, Union[float, Dict, List]]:
    """
    Analisa o alinhamento da carteira atual com o ciclo econômico.
    
    Args:
        tickers: Lista de tickers das ações. Se None, usa a carteira base.
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        Dict[str, Union[float, Dict, List]]: Dicionário com análise de alinhamento da carteira.
    """
    # Se não foram especificados tickers, usa a carteira base
    if tickers is None:
        tickers = CARTEIRA_BASE
    
    # Obtém informações das ações
    info = get_stock_info(tickers, use_cache=use_cache)
    
    # Obtém recomendação de alocação setorial
    recomendacao = recomendar_alocacao_setorial(use_cache=use_cache)
    
    # Cria dicionário para a análise
    analise = {
        'alinhamento_score': 0,
        'setores_carteira': {},
        'setores_recomendados': recomendacao['alocacao_recomendada'],
        'acoes_alinhadas': [],
        'acoes_desalinhadas': [],
        'recomendacoes': []
    }
    
    # Mapeia os setores da carteira
    for ticker in tickers:
        formatted_ticker = ticker
        if not ticker.endswith('.SA'):
            formatted_ticker = f"{ticker}.SA"
        
        if formatted_ticker in info:
            setor = info[formatted_ticker].get('sector', 'Não classificado')
            
            # Mapeia o setor do Yahoo Finance para o setor da B3
            setor_b3 = mapear_setor_yahoo_para_b3(setor)
            
            if setor_b3 in analise['setores_carteira']:
                analise['setores_carteira'][setor_b3] += 1
            else:
                analise['setores_carteira'][setor_b3] = 1
    
    # Normaliza a contagem de setores para percentuais
    total_acoes = len(tickers)
    if total_acoes > 0:
        for setor in analise['setores_carteira']:
            analise['setores_carteira'][setor] = round(analise['setores_carteira'][setor] / total_acoes * 100, 1)
    
    # Calcula o alinhamento da carteira
    alinhamento_total = 0
    max_alinhamento = 0
    
    for setor in SETORES_B3:
        peso_carteira = analise['setores_carteira'].get(setor, 0)
        peso_recomendado = analise['setores_recomendados'].get(setor, 0)
        
        # Quanto menor a diferença, melhor o alinhamento
        diferenca = abs(peso_carteira - peso_recomendado)
        alinhamento_setor = 100 - diferenca
        
        alinhamento_total += alinhamento_setor
        max_alinhamento += 100
    
    # Normaliza o score de alinhamento para 0-100
    if max_alinhamento > 0:
        analise['alinhamento_score'] = round(alinhamento_total / max_alinhamento * 100, 1)
    
    # Identifica ações alinhadas e desalinhadas
    fase_atual = recomendacao['fase_ciclo']
    setores_favorecidos = CICLO_ECONOMICO[fase_atual]['setores_favorecidos']
    
    for ticker in tickers:
        formatted_ticker = ticker
        if not ticker.endswith('.SA'):
            formatted_ticker = f"{ticker}.SA"
        
        if formatted_ticker in info:
            setor = info[formatted_ticker].get('sector', 'Não classificado')
            setor_b3 = mapear_setor_yahoo_para_b3(setor)
            
            if setor_b3 in setores_favorecidos:
                analise['acoes_alinhadas'].append({
                    'ticker': ticker,
                    'setor': setor_b3,
                    'justificativa': f'Setor favorecido na fase de {fase_atual.lower()}'
                })
            else:
                analise['acoes_desalinhadas'].append({
                    'ticker': ticker,
                    'setor': setor_b3,
                    'justificativa': f'Setor não favorecido na fase de {fase_atual.lower()}'
                })
    
    # Gera recomendações para melhorar o alinhamento
    for setor in SETORES_B3:
        peso_carteira = analise['setores_carteira'].get(setor, 0)
        peso_recomendado = analise['setores_recomendados'].get(setor, 0)
        
        if peso_carteira < peso_recomendado - 5:
            analise['recomendacoes'].append({
                'tipo': 'Aumentar',
                'setor': setor,
                'atual': peso_carteira,
                'recomendado': peso_recomendado,
                'diferenca': peso_recomendado - peso_carteira,
                'justificativa': f'Aumentar exposição ao setor {setor}, favorecido na fase atual'
            })
        elif peso_carteira > peso_recomendado + 5:
            analise['recomendacoes'].append({
                'tipo': 'Reduzir',
                'setor': setor,
                'atual': peso_carteira,
                'recomendado': peso_recomendado,
                'diferenca': peso_carteira - peso_recomendado,
                'justificativa': f'Reduzir exposição ao setor {setor}, menos favorecido na fase atual'
            })
    
    # Ordena as recomendações por diferença (maior para menor)
    analise['recomendacoes'] = sorted(
        analise['recomendacoes'],
        key=lambda x: x['diferenca'],
        reverse=True
    )
    
    return analise

def sugerir_ajuste_risco_carteira(use_cache: bool = True) -> Dict[str, Union[str, float, List]]:
    """
    Sugere ajustes no nível de risco da carteira com base no ciclo econômico.
    
    Args:
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        Dict[str, Union[str, float, List]]: Dicionário com sugestões de ajuste de risco.
    """
    # Obtém o score de market timing
    timing = calcular_market_timing_score(use_cache=use_cache)
    
    # Obtém a fase do ciclo econômico
    ciclo = identificar_fase_ciclo(use_cache=use_cache)
    fase_atual = ciclo['fase']
    
    # Cria dicionário para as sugestões
    sugestoes = {
        'nivel_risco_recomendado': '',
        'score_market_timing': timing['score'],
        'fase_ciclo': fase_atual,
        'ajustes_recomendados': [],
        'justificativa': []
    }
    
    # Define o nível de risco recomendado com base no score de market timing
    if timing['score'] >= 70:
        sugestoes['nivel_risco_recomendado'] = 'Agressivo'
        sugestoes['justificativa'].append('Score de market timing muito positivo, favorecendo maior exposição a risco.')
    elif timing['score'] >= 30:
        sugestoes['nivel_risco_recomendado'] = 'Moderado para Agressivo'
        sugestoes['justificativa'].append('Score de market timing positivo, favorecendo exposição moderada a risco.')
    elif timing['score'] >= -30:
        sugestoes['nivel_risco_recomendado'] = 'Neutro'
        sugestoes['justificativa'].append('Score de market timing neutro, sugerindo manutenção de alocação balanceada.')
    elif timing['score'] >= -70:
        sugestoes['nivel_risco_recomendado'] = 'Moderado para Defensivo'
        sugestoes['justificativa'].append('Score de market timing negativo, sugerindo redução da exposição a risco.')
    else:
        sugestoes['nivel_risco_recomendado'] = 'Defensivo'
        sugestoes['justificativa'].append('Score de market timing muito negativo, indicando postura defensiva.')
    
    # Sugere ajustes específicos com base no nível de risco
    if sugestoes['nivel_risco_recomendado'] == 'Agressivo':
        sugestoes['ajustes_recomendados'] = [
            {
                'tipo': 'Aumentar',
                'categoria': 'Renda Variável',
                'percentual': 80,
                'justificativa': 'Cenário muito favorável para ativos de risco'
            },
            {
                'tipo': 'Reduzir',
                'categoria': 'Renda Fixa',
                'percentual': 15,
                'justificativa': 'Manter apenas para liquidez e oportunidades'
            },
            {
                'tipo': 'Manter',
                'categoria': 'Caixa',
                'percentual': 5,
                'justificativa': 'Mínimo para liquidez imediata'
            }
        ]
    elif sugestoes['nivel_risco_recomendado'] == 'Moderado para Agressivo':
        sugestoes['ajustes_recomendados'] = [
            {
                'tipo': 'Aumentar',
                'categoria': 'Renda Variável',
                'percentual': 70,
                'justificativa': 'Cenário favorável para ativos de risco'
            },
            {
                'tipo': 'Reduzir',
                'categoria': 'Renda Fixa',
                'percentual': 25,
                'justificativa': 'Manter para equilíbrio e oportunidades'
            },
            {
                'tipo': 'Manter',
                'categoria': 'Caixa',
                'percentual': 5,
                'justificativa': 'Mínimo para liquidez imediata'
            }
        ]
    elif sugestoes['nivel_risco_recomendado'] == 'Neutro':
        sugestoes['ajustes_recomendados'] = [
            {
                'tipo': 'Equilibrar',
                'categoria': 'Renda Variável',
                'percentual': 60,
                'justificativa': 'Manter exposição balanceada'
            },
            {
                'tipo': 'Equilibrar',
                'categoria': 'Renda Fixa',
                'percentual': 30,
                'justificativa': 'Manter para equilíbrio e proteção'
            },
            {
                'tipo': 'Manter',
                'categoria': 'Caixa',
                'percentual': 10,
                'justificativa': 'Liquidez para oportunidades'
            }
        ]
    elif sugestoes['nivel_risco_recomendado'] == 'Moderado para Defensivo':
        sugestoes['ajustes_recomendados'] = [
            {
                'tipo': 'Reduzir',
                'categoria': 'Renda Variável',
                'percentual': 40,
                'justificativa': 'Reduzir exposição a ativos de risco'
            },
            {
                'tipo': 'Aumentar',
                'categoria': 'Renda Fixa',
                'percentual': 45,
                'justificativa': 'Aumentar proteção e estabilidade'
            },
            {
                'tipo': 'Aumentar',
                'categoria': 'Caixa',
                'percentual': 15,
                'justificativa': 'Manter liquidez para oportunidades'
            }
        ]
    else:  # Defensivo
        sugestoes['ajustes_recomendados'] = [
            {
                'tipo': 'Reduzir',
                'categoria': 'Renda Variável',
                'percentual': 30,
                'justificativa': 'Manter apenas posições estratégicas'
            },
            {
                'tipo': 'Aumentar',
                'categoria': 'Renda Fixa',
                'percentual': 50,
                'justificativa': 'Priorizar proteção e estabilidade'
            },
            {
                'tipo': 'Aumentar',
                'categoria': 'Caixa',
                'percentual': 20,
                'justificativa': 'Manter liquidez elevada para oportunidades futuras'
            }
        ]
    
    # Adiciona ajustes específicos com base na fase do ciclo
    if fase_atual == 'EXPANSAO':
        sugestoes['ajustes_recomendados'].append({
            'tipo': 'Priorizar',
            'categoria': 'Setores Cíclicos',
            'justificativa': 'Fase de expansão favorece setores cíclicos e de crescimento'
        })
    elif fase_atual == 'PICO':
        sugestoes['ajustes_recomendados'].append({
            'tipo': 'Priorizar',
            'categoria': 'Setores com Poder de Precificação',
            'justificativa': 'Fase de pico favorece setores com poder de precificação e commodities'
        })
    elif fase_atual == 'CONTRACAO':
        sugestoes['ajustes_recomendados'].append({
            'tipo': 'Priorizar',
            'categoria': 'Setores Defensivos',
            'justificativa': 'Fase de contração favorece setores defensivos e de dividendos'
        })
    elif fase_atual == 'RECUPERACAO':
        sugestoes['ajustes_recomendados'].append({
            'tipo': 'Priorizar',
            'categoria': 'Setores Financeiros e Cíclicos',
            'justificativa': 'Fase de recuperação favorece setores financeiros e cíclicos'
        })
    
    return sugestoes

def mapear_setor_yahoo_para_b3(setor_yahoo: str) -> str:
    """
    Mapeia o setor do Yahoo Finance para o setor da B3.
    
    Args:
        setor_yahoo: Setor conforme classificação do Yahoo Finance.
        
    Returns:
        str: Setor correspondente na classificação da B3.
    """
    # Mapeamento de setores do Yahoo Finance para setores da B3
    mapeamento = {
        'Financial Services': 'Financeiro',
        'Financial': 'Financeiro',
        'Banks': 'Financeiro',
        'Insurance': 'Financeiro',
        
        'Energy': 'Energia',
        'Oil & Gas': 'Energia',
        'Oil & Gas E&P': 'Energia',
        'Oil & Gas Integrated': 'Energia',
        'Oil & Gas Midstream': 'Energia',
        'Oil & Gas Refining & Marketing': 'Energia',
        
        'Basic Materials': 'Materiais Básicos',
        'Materials': 'Materiais Básicos',
        'Chemicals': 'Materiais Básicos',
        'Steel': 'Materiais Básicos',
        'Paper & Forest Products': 'Materiais Básicos',
        'Mining': 'Materiais Básicos',
        
        'Industrials': 'Bens Industriais',
        'Industrial Products': 'Bens Industriais',
        'Aerospace & Defense': 'Bens Industriais',
        'Building Products': 'Bens Industriais',
        'Electrical Equipment': 'Bens Industriais',
        'Machinery': 'Bens Industriais',
        'Transportation': 'Bens Industriais',
        
        'Consumer Cyclical': 'Consumo Cíclico',
        'Consumer Discretionary': 'Consumo Cíclico',
        'Retail': 'Consumo Cíclico',
        'Apparel Retail': 'Consumo Cíclico',
        'Department Stores': 'Consumo Cíclico',
        'Specialty Retail': 'Consumo Cíclico',
        'Auto Manufacturers': 'Consumo Cíclico',
        'Auto Parts': 'Consumo Cíclico',
        'Entertainment': 'Consumo Cíclico',
        'Hotels, Restaurants & Leisure': 'Consumo Cíclico',
        
        'Consumer Defensive': 'Consumo Não Cíclico',
        'Consumer Staples': 'Consumo Não Cíclico',
        'Food & Beverage': 'Consumo Não Cíclico',
        'Beverages—Brewers': 'Consumo Não Cíclico',
        'Beverages—Non-Alcoholic': 'Consumo Não Cíclico',
        'Beverages—Wineries & Distilleries': 'Consumo Não Cíclico',
        'Farm Products': 'Consumo Não Cíclico',
        'Food Distribution': 'Consumo Não Cíclico',
        'Grocery Stores': 'Consumo Não Cíclico',
        'Household Products': 'Consumo Não Cíclico',
        'Packaged Foods': 'Consumo Não Cíclico',
        'Tobacco': 'Consumo Não Cíclico',
        
        'Healthcare': 'Saúde',
        'Health Care': 'Saúde',
        'Biotechnology': 'Saúde',
        'Drug Manufacturers': 'Saúde',
        'Health Care Plans': 'Saúde',
        'Health Care Providers': 'Saúde',
        'Medical Devices': 'Saúde',
        'Medical Instruments & Supplies': 'Saúde',
        'Pharmaceutical Retailers': 'Saúde',
        
        'Technology': 'Tecnologia da Informação',
        'Information Technology': 'Tecnologia da Informação',
        'Software': 'Tecnologia da Informação',
        'Software—Application': 'Tecnologia da Informação',
        'Software—Infrastructure': 'Tecnologia da Informação',
        'Communication Equipment': 'Tecnologia da Informação',
        'Computer Hardware': 'Tecnologia da Informação',
        'Consumer Electronics': 'Tecnologia da Informação',
        'Electronic Components': 'Tecnologia da Informação',
        'Electronics & Computer Distribution': 'Tecnologia da Informação',
        'Information Technology Services': 'Tecnologia da Informação',
        'Scientific & Technical Instruments': 'Tecnologia da Informação',
        'Semiconductor Equipment & Materials': 'Tecnologia da Informação',
        'Semiconductors': 'Tecnologia da Informação',
        
        'Communication Services': 'Telecomunicações',
        'Telecom Services': 'Telecomunicações',
        'Telecom': 'Telecomunicações',
        'Telecom Services': 'Telecomunicações',
        'Wireless Telecom': 'Telecomunicações',
        
        'Utilities': 'Utilidade Pública',
        'Utilities—Regulated': 'Utilidade Pública',
        'Utilities—Regulated Electric': 'Utilidade Pública',
        'Utilities—Regulated Gas': 'Utilidade Pública',
        'Utilities—Regulated Water': 'Utilidade Pública',
        'Utilities—Independent Power Producers': 'Utilidade Pública',
        'Utilities—Renewable': 'Utilidade Pública',
        
        'Real Estate': 'Imobiliário',
        'REIT': 'Imobiliário',
        'REIT—Diversified': 'Imobiliário',
        'REIT—Healthcare Facilities': 'Imobiliário',
        'REIT—Hotel & Motel': 'Imobiliário',
        'REIT—Industrial': 'Imobiliário',
        'REIT—Office': 'Imobiliário',
        'REIT—Residential': 'Imobiliário',
        'REIT—Retail': 'Imobiliário',
        'REIT—Specialty': 'Imobiliário',
        'Real Estate Services': 'Imobiliário',
        'Real Estate—Development': 'Imobiliário',
        'Real Estate—Diversified': 'Imobiliário'
    }
    
    # Retorna o setor mapeado ou "Não classificado" se não encontrar
    return mapeamento.get(setor_yahoo, 'Não classificado')

def recomendar_acoes_por_setor(setores: List[str], use_cache: bool = True) -> Dict[str, List[Dict]]:
    """
    Recomenda ações específicas para cada setor recomendado.
    
    Args:
        setores: Lista de setores para os quais recomendar ações.
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        Dict[str, List[Dict]]: Dicionário com recomendações de ações por setor.
    """
    # Obtém classificação de valuation setorial
    valuation_setorial = classificar_valuation_setorial(use_cache=use_cache)
    
    # Cria dicionário para as recomendações
    recomendacoes = {}
    
    # Para cada setor
    for setor in setores:
        # Obtém tickers representativos do setor
        tickers_setor = []
        for ticker_yahoo, tickers_lista in SETORES_TICKERS.items():
            setor_b3 = mapear_setor_yahoo_para_b3(ticker_yahoo)
            if setor_b3 == setor:
                tickers_setor.extend([t.replace('.SA', '') for t in tickers_lista])
        
        if not tickers_setor:
            continue
        
        # Obtém dados de valuation das ações do setor
        valuation = get_valuation_data(tickers_setor, use_cache=use_cache)
        
        # Filtra ações com valuation atrativo
        acoes_recomendadas = []
        
        for ticker in tickers_setor:
            if ticker not in valuation.index:
                continue
            
            # Critérios de valuation
            pl = valuation.loc[ticker, 'P/L'] if 'P/L' in valuation.columns else None
            pvp = valuation.loc[ticker, 'P/VP'] if 'P/VP' in valuation.columns else None
            dy = valuation.loc[ticker, 'Dividend Yield'] if 'Dividend Yield' in valuation.columns else None
            
            # Pontuação de valuation
            score = 0
            justificativa = []
            
            if pl is not None and pd.notna(pl):
                if pl > 0 and pl < 10:
                    score += 2
                    justificativa.append(f'P/L atrativo: {pl:.2f}')
                elif pl > 0 and pl < 15:
                    score += 1
                    justificativa.append(f'P/L razoável: {pl:.2f}')
            
            if pvp is not None and pd.notna(pvp):
                if pvp < 1:
                    score += 2
                    justificativa.append(f'P/VP muito atrativo: {pvp:.2f}')
                elif pvp < 1.5:
                    score += 1
                    justificativa.append(f'P/VP atrativo: {pvp:.2f}')
            
            if dy is not None and pd.notna(dy):
                if dy > 7:
                    score += 2
                    justificativa.append(f'Dividend Yield alto: {dy:.2f}%')
                elif dy > 5:
                    score += 1
                    justificativa.append(f'Dividend Yield bom: {dy:.2f}%')
            
            # Adiciona à lista se tiver pontuação mínima
            if score >= 1:
                acoes_recomendadas.append({
                    'ticker': ticker,
                    'score': score,
                    'justificativa': ', '.join(justificativa)
                })
        
        # Ordena por score (maior para menor)
        acoes_recomendadas = sorted(acoes_recomendadas, key=lambda x: x['score'], reverse=True)
        
        # Limita a 5 recomendações por setor
        recomendacoes[setor] = acoes_recomendadas[:5]
    
    return recomendacoes

if __name__ == "__main__":
    # Teste das funções
    print("Testando funções de recomendação de alocação setorial...")
    
    # Recomenda alocação setorial
    recomendacao = recomendar_alocacao_setorial(use_cache=False)
    print("\nRecomendação de Alocação Setorial:")
    print(f"Fase do Ciclo: {recomendacao['fase_ciclo']}")
    print(f"Descrição: {recomendacao['descricao_fase']}")
    print(f"Nível de Risco: {recomendacao['nivel_risco']}")
    print("\nAlocação Recomendada:")
    for setor, peso in recomendacao['alocacao_recomendada'].items():
        print(f"{setor}: {peso}%")
    
    # Analisa alinhamento da carteira
    alinhamento = analisar_alinhamento_carteira(use_cache=False)
    print("\nAlinhamento da Carteira:")
    print(f"Score de Alinhamento: {alinhamento['alinhamento_score']}%")
    print("\nAções Alinhadas:")
    for acao in alinhamento['acoes_alinhadas']:
        print(f"{acao['ticker']} ({acao['setor']}): {acao['justificativa']}")
    
    # Sugere ajuste de risco
    ajuste = sugerir_ajuste_risco_carteira(use_cache=False)
    print("\nAjuste de Risco Recomendado:")
    print(f"Nível de Risco: {ajuste['nivel_risco_recomendado']}")
    for rec in ajuste['ajustes_recomendados']:
        if 'percentual' in rec:
            print(f"{rec['tipo']} {rec['categoria']}: {rec['percentual']}% - {rec['justificativa']}")
        else:
            print(f"{rec['tipo']} {rec['categoria']}: {rec['justificativa']}")
