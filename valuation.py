"""
Módulo para análise de valuation e múltiplos de mercado.

Este módulo contém funções para calcular e analisar múltiplos de valuation,
comparar com médias históricas, implementar modelos de avaliação relativos
e realizar análises setoriais.
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

from config import DATA_DIR, CACHE_DIR, PERIODOS_HISTORICOS, SETORES_B3, CARTEIRA_BASE
from data.market_data import (
    get_valuation_data, get_sector_valuation, get_historical_valuation,
    get_historical_sector_valuation, get_fed_model_data, get_portfolio_valuation
)
from data.macro_data import get_juros_data, get_inflacao_data

def calcular_premio_risco(use_cache: bool = True) -> pd.DataFrame:
    """
    Calcula o prêmio de risco do mercado brasileiro usando o modelo Fed adaptado.
    
    O prêmio de risco é calculado como a diferença entre o Earnings Yield (E/P)
    do Ibovespa e a taxa de juros de longo prazo (Swap Pré-DI de 3 anos).
    
    Args:
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        pd.DataFrame: DataFrame com o prêmio de risco e componentes.
    """
    # Obtém dados do Fed Model
    fed_model = get_fed_model_data(use_cache=use_cache)
    
    # Adiciona interpretação do prêmio de risco
    if not fed_model.empty and 'Prêmio de Risco (%)' in fed_model.columns:
        premio = fed_model['Prêmio de Risco (%)'].iloc[0]
        
        if premio > 3:
            fed_model['Interpretação'] = 'Ações potencialmente subvalorizadas'
            fed_model['Sinal'] = 'Compra'
        elif premio > 0:
            fed_model['Interpretação'] = 'Ações com valuation neutro'
            fed_model['Sinal'] = 'Neutro'
        elif premio > -3:
            fed_model['Interpretação'] = 'Ações potencialmente caras'
            fed_model['Sinal'] = 'Cautela'
        else:
            fed_model['Interpretação'] = 'Ações significativamente caras'
            fed_model['Sinal'] = 'Venda'
    
    return fed_model

def comparar_valuation_historico(tickers: List[str] = None, periodos: List[int] = None,
                               use_cache: bool = True) -> pd.DataFrame:
    """
    Compara múltiplos de valuation atuais com médias históricas.
    
    Args:
        tickers: Lista de tickers das ações. Se None, usa a carteira base.
        periodos: Lista de períodos (em anos) para comparação. Se None, usa os períodos padrão.
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        pd.DataFrame: DataFrame com a comparação de múltiplos atuais e históricos.
    """
    # Se não foram especificados tickers, usa a carteira base
    if tickers is None:
        tickers = CARTEIRA_BASE
    
    # Se não foram especificados períodos, usa os períodos padrão
    if periodos is None:
        periodos = PERIODOS_HISTORICOS
    
    # Obtém dados de valuation atual
    valuation_atual = get_valuation_data(tickers, use_cache=use_cache)
    
    # Cria DataFrame para a comparação
    comparacao = pd.DataFrame(index=tickers)
    
    # Adiciona múltiplos atuais
    for col in ['P/L', 'P/VP', 'EV/EBITDA', 'Dividend Yield']:
        if col in valuation_atual.columns:
            comparacao[f'{col} (Atual)'] = valuation_atual[col]
    
    # Para cada período histórico
    for periodo in periodos:
        # Obtém dados históricos de valuation
        historico = get_historical_valuation(tickers, years=periodo, use_cache=use_cache)
        
        # Para cada ticker
        for ticker in tickers:
            formatted_ticker = ticker
            if not ticker.endswith('.SA'):
                formatted_ticker = f"{ticker}.SA"
            
            if formatted_ticker in historico:
                ticker_historico = historico[formatted_ticker]
                
                # Calcula médias históricas
                for col in ['P/L', 'P/VP']:
                    if col in ticker_historico.columns:
                        media = ticker_historico[col].mean()
                        comparacao.loc[ticker, f'{col} (Média {periodo}a)'] = media
                        
                        # Calcula percentual em relação à média histórica
                        if pd.notna(media) and media != 0 and pd.notna(comparacao.loc[ticker, f'{col} (Atual)']):
                            atual = comparacao.loc[ticker, f'{col} (Atual)']
                            comparacao.loc[ticker, f'{col} (% vs Média {periodo}a)'] = ((atual / media) - 1) * 100
    
    return comparacao

def comparar_setores_historico(periodos: List[int] = None, use_cache: bool = True) -> pd.DataFrame:
    """
    Compara múltiplos de valuation setoriais atuais com médias históricas.
    
    Args:
        periodos: Lista de períodos (em anos) para comparação. Se None, usa os períodos padrão.
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        pd.DataFrame: DataFrame com a comparação de múltiplos setoriais atuais e históricos.
    """
    # Se não foram especificados períodos, usa os períodos padrão
    if periodos is None:
        periodos = PERIODOS_HISTORICOS
    
    # Obtém dados de valuation setorial atual
    valuation_atual = get_sector_valuation(use_cache=use_cache)
    
    # Cria DataFrame para a comparação
    comparacao = pd.DataFrame(index=SETORES_B3)
    
    # Adiciona múltiplos atuais
    for col in ['P/L', 'P/VP', 'EV/EBITDA', 'Dividend Yield']:
        if col in valuation_atual.columns:
            comparacao[f'{col} (Atual)'] = valuation_atual[col]
    
    # Para cada período histórico
    for periodo in periodos:
        # Obtém dados históricos de valuation setorial
        historico = get_historical_sector_valuation(years=periodo, use_cache=use_cache)
        
        # Para cada setor
        for setor in SETORES_B3:
            if setor in historico:
                setor_historico = historico[setor]
                
                # Calcula médias históricas
                for col in ['P/L', 'P/VP']:
                    if col in setor_historico.columns:
                        media = setor_historico[col].mean()
                        comparacao.loc[setor, f'{col} (Média {periodo}a)'] = media
                        
                        # Calcula percentual em relação à média histórica
                        if pd.notna(media) and media != 0 and pd.notna(comparacao.loc[setor, f'{col} (Atual)']):
                            atual = comparacao.loc[setor, f'{col} (Atual)']
                            comparacao.loc[setor, f'{col} (% vs Média {periodo}a)'] = ((atual / media) - 1) * 100
    
    return comparacao

def classificar_valuation_setorial(use_cache: bool = True) -> pd.DataFrame:
    """
    Classifica os setores da B3 com base em seu valuation atual vs. histórico.
    
    Args:
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        pd.DataFrame: DataFrame com a classificação dos setores.
    """
    # Obtém comparação de valuation setorial
    comparacao = comparar_setores_historico(use_cache=use_cache)
    
    # Cria DataFrame para a classificação
    classificacao = pd.DataFrame(index=SETORES_B3)
    
    # Adiciona métricas de valuation
    for setor in SETORES_B3:
        # P/L vs. média histórica de 5 anos
        if f'P/L (% vs Média 5a)' in comparacao.columns:
            pl_vs_media = comparacao.loc[setor, f'P/L (% vs Média 5a)']
            
            if pd.notna(pl_vs_media):
                if pl_vs_media < -20:
                    classificacao.loc[setor, 'P/L vs. Histórico'] = 'Muito Barato'
                    classificacao.loc[setor, 'Score P/L'] = 2
                elif pl_vs_media < -5:
                    classificacao.loc[setor, 'P/L vs. Histórico'] = 'Barato'
                    classificacao.loc[setor, 'Score P/L'] = 1
                elif pl_vs_media < 5:
                    classificacao.loc[setor, 'P/L vs. Histórico'] = 'Neutro'
                    classificacao.loc[setor, 'Score P/L'] = 0
                elif pl_vs_media < 20:
                    classificacao.loc[setor, 'P/L vs. Histórico'] = 'Caro'
                    classificacao.loc[setor, 'Score P/L'] = -1
                else:
                    classificacao.loc[setor, 'P/L vs. Histórico'] = 'Muito Caro'
                    classificacao.loc[setor, 'Score P/L'] = -2
        
        # P/VP vs. média histórica de 5 anos
        if f'P/VP (% vs Média 5a)' in comparacao.columns:
            pvp_vs_media = comparacao.loc[setor, f'P/VP (% vs Média 5a)']
            
            if pd.notna(pvp_vs_media):
                if pvp_vs_media < -20:
                    classificacao.loc[setor, 'P/VP vs. Histórico'] = 'Muito Barato'
                    classificacao.loc[setor, 'Score P/VP'] = 2
                elif pvp_vs_media < -5:
                    classificacao.loc[setor, 'P/VP vs. Histórico'] = 'Barato'
                    classificacao.loc[setor, 'Score P/VP'] = 1
                elif pvp_vs_media < 5:
                    classificacao.loc[setor, 'P/VP vs. Histórico'] = 'Neutro'
                    classificacao.loc[setor, 'Score P/VP'] = 0
                elif pvp_vs_media < 20:
                    classificacao.loc[setor, 'P/VP vs. Histórico'] = 'Caro'
                    classificacao.loc[setor, 'Score P/VP'] = -1
                else:
                    classificacao.loc[setor, 'P/VP vs. Histórico'] = 'Muito Caro'
                    classificacao.loc[setor, 'Score P/VP'] = -2
        
        # Dividend Yield atual
        if 'Dividend Yield (Atual)' in comparacao.columns:
            dy = comparacao.loc[setor, 'Dividend Yield (Atual)']
            
            if pd.notna(dy):
                if dy > 7:
                    classificacao.loc[setor, 'Dividend Yield'] = 'Muito Alto'
                    classificacao.loc[setor, 'Score DY'] = 2
                elif dy > 5:
                    classificacao.loc[setor, 'Dividend Yield'] = 'Alto'
                    classificacao.loc[setor, 'Score DY'] = 1
                elif dy > 3:
                    classificacao.loc[setor, 'Dividend Yield'] = 'Médio'
                    classificacao.loc[setor, 'Score DY'] = 0
                elif dy > 1:
                    classificacao.loc[setor, 'Dividend Yield'] = 'Baixo'
                    classificacao.loc[setor, 'Score DY'] = -1
                else:
                    classificacao.loc[setor, 'Dividend Yield'] = 'Muito Baixo'
                    classificacao.loc[setor, 'Score DY'] = -2
    
    # Calcula score total de valuation
    score_cols = [col for col in classificacao.columns if col.startswith('Score')]
    if score_cols:
        classificacao['Score Total'] = classificacao[score_cols].sum(axis=1)
        
        # Classifica com base no score total
        classificacao['Classificação'] = classificacao['Score Total'].apply(
            lambda x: 'Muito Barato' if x >= 4 else
                     'Barato' if x >= 2 else
                     'Neutro' if x >= -1 else
                     'Caro' if x >= -3 else
                     'Muito Caro'
        )
    
    return classificacao

def analisar_carteira(tickers: List[str] = None, use_cache: bool = True) -> pd.DataFrame:
    """
    Analisa a carteira de ações com base em valuation e outros indicadores.
    
    Args:
        tickers: Lista de tickers das ações. Se None, usa a carteira base.
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        pd.DataFrame: DataFrame com a análise da carteira.
    """
    # Se não foram especificados tickers, usa a carteira base
    if tickers is None:
        tickers = CARTEIRA_BASE
    
    # Obtém dados de valuation da carteira
    valuation = get_portfolio_valuation(tickers, use_cache=use_cache)
    
    # Obtém comparação com médias históricas
    comparacao = comparar_valuation_historico(tickers, use_cache=use_cache)
    
    # Cria DataFrame para a análise
    analise = pd.DataFrame(index=tickers)
    
    # Adiciona métricas de valuation
    for ticker in tickers:
        # P/L atual
        if 'P/L' in valuation.columns:
            pl = valuation.loc[ticker, 'P/L']
            
            if pd.notna(pl):
                analise.loc[ticker, 'P/L'] = pl
                
                if pl < 0:
                    analise.loc[ticker, 'P/L Classificação'] = 'Prejuízo'
                elif pl < 10:
                    analise.loc[ticker, 'P/L Classificação'] = 'Muito Barato'
                elif pl < 15:
                    analise.loc[ticker, 'P/L Classificação'] = 'Barato'
                elif pl < 20:
                    analise.loc[ticker, 'P/L Classificação'] = 'Neutro'
                elif pl < 30:
                    analise.loc[ticker, 'P/L Classificação'] = 'Caro'
                else:
                    analise.loc[ticker, 'P/L Classificação'] = 'Muito Caro'
        
        # P/VP atual
        if 'P/VP' in valuation.columns:
            pvp = valuation.loc[ticker, 'P/VP']
            
            if pd.notna(pvp):
                analise.loc[ticker, 'P/VP'] = pvp
                
                if pvp < 1:
                    analise.loc[ticker, 'P/VP Classificação'] = 'Muito Barato'
                elif pvp < 1.5:
                    analise.loc[ticker, 'P/VP Classificação'] = 'Barato'
                elif pvp < 2:
                    analise.loc[ticker, 'P/VP Classificação'] = 'Neutro'
                elif pvp < 3:
                    analise.loc[ticker, 'P/VP Classificação'] = 'Caro'
                else:
                    analise.loc[ticker, 'P/VP Classificação'] = 'Muito Caro'
        
        # Dividend Yield atual
        if 'Dividend Yield' in valuation.columns:
            dy = valuation.loc[ticker, 'Dividend Yield']
            
            if pd.notna(dy):
                analise.loc[ticker, 'Dividend Yield'] = dy
                
                if dy > 7:
                    analise.loc[ticker, 'DY Classificação'] = 'Muito Alto'
                elif dy > 5:
                    analise.loc[ticker, 'DY Classificação'] = 'Alto'
                elif dy > 3:
                    analise.loc[ticker, 'DY Classificação'] = 'Médio'
                elif dy > 1:
                    analise.loc[ticker, 'DY Classificação'] = 'Baixo'
                else:
                    analise.loc[ticker, 'DY Classificação'] = 'Muito Baixo'
        
        # P/L vs. média histórica de 5 anos
        if f'P/L (% vs Média 5a)' in comparacao.columns:
            pl_vs_media = comparacao.loc[ticker, f'P/L (% vs Média 5a)']
            
            if pd.notna(pl_vs_media):
                analise.loc[ticker, 'P/L vs. Média 5a (%)'] = pl_vs_media
                
                if pl_vs_media < -20:
                    analise.loc[ticker, 'P/L vs. Histórico'] = 'Muito Barato'
                elif pl_vs_media < -5:
                    analise.loc[ticker, 'P/L vs. Histórico'] = 'Barato'
                elif pl_vs_media < 5:
                    analise.loc[ticker, 'P/L vs. Histórico'] = 'Neutro'
                elif pl_vs_media < 20:
                    analise.loc[ticker, 'P/L vs. Histórico'] = 'Caro'
                else:
                    analise.loc[ticker, 'P/L vs. Histórico'] = 'Muito Caro'
        
        # Setor
        if 'Setor' in valuation.columns:
            analise.loc[ticker, 'Setor'] = valuation.loc[ticker, 'Setor']
    
    return analise

def calcular_indicadores_valuation_mercado(use_cache: bool = True) -> Dict[str, float]:
    """
    Calcula indicadores gerais de valuation do mercado brasileiro.
    
    Args:
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        Dict[str, float]: Dicionário com indicadores de valuation do mercado.
    """
    # Obtém dados de valuation setorial
    valuation_setorial = get_sector_valuation(use_cache=use_cache)
    
    # Obtém dados do Fed Model
    fed_model = get_fed_model_data(use_cache=use_cache)
    
    # Obtém dados de juros
    juros = get_juros_data(use_cache=use_cache)
    
    # Cria dicionário para os indicadores
    indicadores = {}
    
    # Calcula médias ponderadas dos múltiplos setoriais
    if not valuation_setorial.empty:
        indicadores['P/L Médio Mercado'] = valuation_setorial['P/L'].mean()
        indicadores['P/VP Médio Mercado'] = valuation_setorial['P/VP'].mean()
        indicadores['EV/EBITDA Médio Mercado'] = valuation_setorial['EV/EBITDA'].mean()
        indicadores['Dividend Yield Médio Mercado'] = valuation_setorial['Dividend Yield'].mean()
    
    # Adiciona prêmio de risco do Fed Model
    if not fed_model.empty and 'Prêmio de Risco (%)' in fed_model.columns:
        indicadores['Prêmio de Risco (%)'] = fed_model['Prêmio de Risco (%)'].iloc[0]
    
    # Adiciona taxa Selic atual
    if not juros.empty and 'selic_meta' in juros.columns:
        indicadores['Taxa Selic (%)'] = juros['selic_meta'].iloc[-1]
    
    # Calcula indicadores derivados
    if 'P/L Médio Mercado' in indicadores and indicadores['P/L Médio Mercado'] > 0:
        indicadores['Earnings Yield (%)'] = 100 / indicadores['P/L Médio Mercado']
    
    if 'Earnings Yield (%)' in indicadores and 'Taxa Selic (%)' in indicadores:
        indicadores['EY - Selic (%)'] = indicadores['Earnings Yield (%)'] - indicadores['Taxa Selic (%)']
    
    return indicadores

if __name__ == "__main__":
    # Teste das funções
    print("Testando funções de análise de valuation...")
    
    # Calcula prêmio de risco
    premio_risco = calcular_premio_risco(use_cache=False)
    print("\nPrêmio de Risco (Fed Model):")
    print(premio_risco)
    
    # Compara valuation setorial com médias históricas
    comparacao_setorial = comparar_setores_historico(use_cache=False)
    print("\nComparação de Valuation Setorial:")
    print(comparacao_setorial)
    
    # Classifica setores por valuation
    classificacao = classificar_valuation_setorial(use_cache=False)
    print("\nClassificação de Valuation Setorial:")
    print(classificacao)
