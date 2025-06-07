"""
Módulo para análise de valuation de ações e setores.

Este módulo contém funções para calcular e analisar métricas de valuation
para ações, setores e o mercado como um todo.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
import datetime

# Importa as configurações e dados
from config import SETORES_B3, CARTEIRA_BASE
from market_data import get_sector_valuation, get_fed_model_data, get_stock_info

def calcular_premio_risco() -> pd.DataFrame:
    """
    Calcula o prêmio de risco do mercado brasileiro usando o Fed Model adaptado.
    
    Returns:
        pd.DataFrame: DataFrame com os dados do prêmio de risco.
    """
    # Obtém os dados do Fed Model
    fed_model = get_fed_model_data()
    
    return fed_model

def classificar_valuation_setorial() -> pd.DataFrame:
    """
    Classifica os setores da B3 com base em múltiplos de valuation.
    
    Returns:
        pd.DataFrame: DataFrame com a classificação dos setores.
    """
    # Obtém os múltiplos de valuation por setor
    valuation_setorial = get_sector_valuation()
    
    if valuation_setorial.empty:
        return pd.DataFrame()
    
    # Cria um DataFrame para a classificação
    classificacao = pd.DataFrame(index=valuation_setorial.index)
    
    # Calcula scores para cada múltiplo (quanto menor, melhor)
    if 'P/L' in valuation_setorial.columns:
        pl_norm = (valuation_setorial['P/L'] - valuation_setorial['P/L'].min()) / (valuation_setorial['P/L'].max() - valuation_setorial['P/L'].min())
        classificacao['Score P/L'] = 1 - pl_norm
    
    if 'P/VP' in valuation_setorial.columns:
        pvp_norm = (valuation_setorial['P/VP'] - valuation_setorial['P/VP'].min()) / (valuation_setorial['P/VP'].max() - valuation_setorial['P/VP'].min())
        classificacao['Score P/VP'] = 1 - pvp_norm
    
    if 'EV/EBITDA' in valuation_setorial.columns:
        ev_ebitda_norm = (valuation_setorial['EV/EBITDA'] - valuation_setorial['EV/EBITDA'].min()) / (valuation_setorial['EV/EBITDA'].max() - valuation_setorial['EV/EBITDA'].min())
        classificacao['Score EV/EBITDA'] = 1 - ev_ebitda_norm
    
    # Para Dividend Yield, quanto maior, melhor
    if 'Dividend Yield (%)' in valuation_setorial.columns:
        dy_norm = (valuation_setorial['Dividend Yield (%)'] - valuation_setorial['Dividend Yield (%)'].min()) / (valuation_setorial['Dividend Yield (%)'].max() - valuation_setorial['Dividend Yield (%)'].min())
        classificacao['Score DY'] = dy_norm
    
    # Calcula o score total (média dos scores individuais)
    score_columns = [col for col in classificacao.columns if col.startswith('Score')]
    classificacao['Score Total'] = classificacao[score_columns].mean(axis=1)
    
    # Classifica os setores com base no score total
    classificacao['Classificação'] = pd.cut(
        classificacao['Score Total'],
        bins=[-float('inf'), 0.2, 0.4, 0.6, 0.8, float('inf')],
        labels=['Muito Caro', 'Caro', 'Neutro', 'Barato', 'Muito Barato']
    )
    
    return classificacao

def comparar_setores_historico() -> pd.DataFrame:
    """
    Compara os múltiplos atuais dos setores com suas médias históricas.
    
    Returns:
        pd.DataFrame: DataFrame com a comparação dos múltiplos.
    """
    # Obtém os múltiplos de valuation por setor
    valuation_setorial = get_sector_valuation()
    
    if valuation_setorial.empty:
        return pd.DataFrame()
    
    # Cria um DataFrame para a comparação
    comparacao = pd.DataFrame(index=valuation_setorial.index)
    
    # Simula médias históricas (em um sistema real, seriam obtidas de um banco de dados)
    # Aqui, estamos usando valores simulados para demonstração
    for setor in valuation_setorial.index:
        if 'P/L' in valuation_setorial.columns:
            pl_atual = valuation_setorial.loc[setor, 'P/L']
            # Simula uma média histórica de 5 anos (±20% do valor atual)
            pl_medio_5a = pl_atual * (1 + np.random.uniform(-0.2, 0.2))
            comparacao.loc[setor, 'P/L (Atual)'] = pl_atual
            comparacao.loc[setor, 'P/L (Média 5a)'] = pl_medio_5a
            comparacao.loc[setor, 'P/L (% vs Média)'] = ((pl_atual / pl_medio_5a) - 1) * 100
        
        if 'P/VP' in valuation_setorial.columns:
            pvp_atual = valuation_setorial.loc[setor, 'P/VP']
            # Simula uma média histórica de 5 anos (±20% do valor atual)
            pvp_medio_5a = pvp_atual * (1 + np.random.uniform(-0.2, 0.2))
            comparacao.loc[setor, 'P/VP (Atual)'] = pvp_atual
            comparacao.loc[setor, 'P/VP (Média 5a)'] = pvp_medio_5a
            comparacao.loc[setor, 'P/VP (% vs Média)'] = ((pvp_atual / pvp_medio_5a) - 1) * 100
    
    return comparacao

def analisar_carteira(carteira: Dict[str, float]) -> pd.DataFrame:
    """
    Analisa os múltiplos de valuation de uma carteira de ações.
    
    Args:
        carteira: Dicionário com tickers e pesos da carteira.
        
    Returns:
        pd.DataFrame: DataFrame com a análise da carteira.
    """
    # Cria um DataFrame para a análise
    analise = pd.DataFrame(index=carteira.keys())
    
    # Para cada ação da carteira
    for ticker in carteira.keys():
        try:
            # Obtém as informações da ação
            info = get_stock_info(ticker)
            
            # Extrai os múltiplos
            if 'trailingPE' in info and info['trailingPE'] is not None:
                analise.loc[ticker, 'P/L'] = info['trailingPE']
            
            if 'priceToBook' in info and info['priceToBook'] is not None:
                analise.loc[ticker, 'P/VP'] = info['priceToBook']
            
            if 'enterpriseToEbitda' in info and info['enterpriseToEbitda'] is not None:
                analise.loc[ticker, 'EV/EBITDA'] = info['enterpriseToEbitda']
            
            if 'dividendYield' in info and info['dividendYield'] is not None:
                analise.loc[ticker, 'Dividend Yield (%)'] = info['dividendYield'] * 100  # Converte para percentual
            
            # Adiciona o peso na carteira
            analise.loc[ticker, 'Peso (%)'] = carteira[ticker]
            
            # Adiciona o setor
            for setor, tickers in SETORES_B3.items():
                if ticker in tickers:
                    analise.loc[ticker, 'Setor'] = setor
                    break
        except Exception as e:
            print(f"Erro ao analisar a ação {ticker}: {e}")
    
    # Calcula os múltiplos médios da carteira (ponderados pelo peso)
    for col in ['P/L', 'P/VP', 'EV/EBITDA', 'Dividend Yield (%)']:
        if col in analise.columns:
            analise.loc['MÉDIA CARTEIRA', col] = np.average(
                analise[col].dropna(),
                weights=analise.loc[analise[col].dropna().index, 'Peso (%)']
            )
    
    # Adiciona o peso total da carteira
    analise.loc['MÉDIA CARTEIRA', 'Peso (%)'] = analise['Peso (%)'].sum()
    
    return analise
