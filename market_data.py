"""
Módulo para coleta e processamento de dados de mercado.

Este módulo contém funções para obter dados de mercado, como índices,
ações, setores e múltiplos de valuation.
"""

import pandas as pd
import numpy as np
import yfinance as yf
import datetime
from typing import Dict, List, Optional, Union
import sys
import os
from pathlib import Path

# Importa as configurações
from config import INDICES, SETORES_B3, CARTEIRA_BASE, API_CONFIG

def get_index_data(period: str = "1y") -> pd.DataFrame:
    """
    Obtém dados dos principais índices brasileiros.
    
    Args:
        period: Período de dados a serem obtidos (ex: "1d", "1mo", "1y").
        
    Returns:
        pd.DataFrame: DataFrame com os dados dos índices.
    """
    # Lista de tickers dos índices
    tickers = list(INDICES.values())
    
    try:
        # Obtém os dados dos índices
        dados = yf.download(
            tickers=tickers,
            period=period,
            interval=API_CONFIG['yahoo']['interval'],
            group_by='ticker',
            auto_adjust=True
        )
        
        return dados
    except Exception as e:
        print(f"Erro ao obter dados dos índices: {e}")
        # Retorna DataFrame vazio em caso de erro
        return pd.DataFrame()

def get_sector_data(period: str = "1y") -> Dict[str, pd.DataFrame]:
    """
    Obtém dados das ações por setor.
    
    Args:
        period: Período de dados a serem obtidos (ex: "1d", "1mo", "1y").
        
    Returns:
        Dict[str, pd.DataFrame]: Dicionário com DataFrames para cada setor.
    """
    # Dicionário para armazenar os dados por setor
    dados_setores = {}
    
    # Para cada setor
    for setor, tickers in SETORES_B3.items():
        try:
            # Adiciona ".SA" aos tickers para o Yahoo Finance
            tickers_sa = [f"{ticker}.SA" for ticker in tickers]
            
            # Obtém os dados das ações do setor
            dados = yf.download(
                tickers=tickers_sa,
                period=period,
                interval=API_CONFIG['yahoo']['interval'],
                group_by='ticker',
                auto_adjust=True
            )
            
            # Armazena os dados do setor
            dados_setores[setor] = dados
        except Exception as e:
            print(f"Erro ao obter dados do setor {setor}: {e}")
            # Armazena DataFrame vazio em caso de erro
            dados_setores[setor] = pd.DataFrame()
    
    return dados_setores

def get_stock_data(tickers: List[str], period: str = "1y") -> pd.DataFrame:
    """
    Obtém dados de ações específicas.
    
    Args:
        tickers: Lista de tickers das ações.
        period: Período de dados a serem obtidos (ex: "1d", "1mo", "1y").
        
    Returns:
        pd.DataFrame: DataFrame com os dados das ações.
    """
    try:
        # Adiciona ".SA" aos tickers para o Yahoo Finance
        tickers_sa = [f"{ticker}.SA" for ticker in tickers]
        
        # Obtém os dados das ações
        dados = yf.download(
            tickers=tickers_sa,
            period=period,
            interval=API_CONFIG['yahoo']['interval'],
            group_by='ticker',
            auto_adjust=True
        )
        
        return dados
    except Exception as e:
        print(f"Erro ao obter dados das ações: {e}")
        # Retorna DataFrame vazio em caso de erro
        return pd.DataFrame()

def get_stock_info(ticker: str) -> Dict:
    """
    Obtém informações detalhadas de uma ação.
    
    Args:
        ticker: Ticker da ação.
        
    Returns:
        Dict: Dicionário com informações da ação.
    """
    try:
        # Adiciona ".SA" ao ticker para o Yahoo Finance
        ticker_sa = f"{ticker}.SA"
        
        # Obtém as informações da ação
        acao = yf.Ticker(ticker_sa)
        info = acao.info
        
        return info
    except Exception as e:
        print(f"Erro ao obter informações da ação {ticker}: {e}")
        # Retorna dicionário vazio em caso de erro
        return {}

def get_sector_valuation() -> pd.DataFrame:
    """
    Obtém múltiplos de valuation por setor.
    
    Returns:
        pd.DataFrame: DataFrame com os múltiplos de valuation por setor.
    """
    # Dicionário para armazenar os múltiplos por setor
    multiplos_setores = {}
    
    # Para cada setor
    for setor, tickers in SETORES_B3.items():
        # Listas para armazenar os múltiplos das ações do setor
        pl_list = []
        pvp_list = []
        ev_ebitda_list = []
        dy_list = []
        
        # Para cada ação do setor
        for ticker in tickers:
            try:
                # Obtém as informações da ação
                info = get_stock_info(ticker)
                
                # Extrai os múltiplos
                if 'trailingPE' in info and info['trailingPE'] is not None and info['trailingPE'] > 0:
                    pl_list.append(info['trailingPE'])
                
                if 'priceToBook' in info and info['priceToBook'] is not None and info['priceToBook'] > 0:
                    pvp_list.append(info['priceToBook'])
                
                if 'enterpriseToEbitda' in info and info['enterpriseToEbitda'] is not None and info['enterpriseToEbitda'] > 0:
                    ev_ebitda_list.append(info['enterpriseToEbitda'])
                
                if 'dividendYield' in info and info['dividendYield'] is not None and info['dividendYield'] > 0:
                    dy_list.append(info['dividendYield'] * 100)  # Converte para percentual
            except Exception as e:
                print(f"Erro ao obter múltiplos da ação {ticker}: {e}")
        
        # Calcula as médias dos múltiplos do setor
        pl_medio = np.mean(pl_list) if pl_list else np.nan
        pvp_medio = np.mean(pvp_list) if pvp_list else np.nan
        ev_ebitda_medio = np.mean(ev_ebitda_list) if ev_ebitda_list else np.nan
        dy_medio = np.mean(dy_list) if dy_list else np.nan
        
        # Armazena os múltiplos do setor
        multiplos_setores[setor] = {
            'P/L': pl_medio,
            'P/VP': pvp_medio,
            'EV/EBITDA': ev_ebitda_medio,
            'Dividend Yield (%)': dy_medio
        }
    
    # Converte o dicionário para DataFrame
    df_valuation = pd.DataFrame.from_dict(multiplos_setores, orient='index')
    
    return df_valuation

def get_fed_model_data() -> pd.DataFrame:
    """
    Obtém dados para o Fed Model adaptado para o Brasil.
    
    Returns:
        pd.DataFrame: DataFrame com os dados do Fed Model.
    """
    # Obtém os dados do Ibovespa
    ibov = yf.Ticker("^BVSP")
    
    try:
        # Obtém o P/L do Ibovespa
        pl_ibov = ibov.info.get('trailingPE', np.nan)
        
        # Calcula o Earnings Yield (E/P)
        earnings_yield = (1 / pl_ibov) * 100 if pl_ibov and pl_ibov > 0 else np.nan
        
        # Obtém a taxa de juros de longo prazo (DI de 3 anos)
        from macro_data import get_bcb_data
        from config import BCB_SERIES
        
        di_3y = get_bcb_data(BCB_SERIES['di_3y'])
        taxa_juros_longo_prazo = di_3y.iloc[-1, 0] if not di_3y.empty else np.nan
        
        # Calcula o prêmio de risco
        premio_risco = earnings_yield - taxa_juros_longo_prazo if not np.isnan(earnings_yield) and not np.isnan(taxa_juros_longo_prazo) else np.nan
        
        # Determina a interpretação do prêmio de risco
        if premio_risco > 3:
            interpretacao = "Ações subvalorizadas"
        elif premio_risco > 0:
            interpretacao = "Ações levemente subvalorizadas"
        elif premio_risco > -3:
            interpretacao = "Ações levemente sobrevalorizadas"
        else:
            interpretacao = "Ações sobrevalorizadas"
        
        # Cria o DataFrame com os resultados
        fed_model = pd.DataFrame({
            'Earnings Yield (%)': [earnings_yield],
            'Taxa de Juros Longo Prazo (%)': [taxa_juros_longo_prazo],
            'Prêmio de Risco (%)': [premio_risco],
            'Interpretação': [interpretacao]
        })
        
        return fed_model
    except Exception as e:
        print(f"Erro ao calcular o Fed Model: {e}")
        # Retorna DataFrame vazio em caso de erro
        return pd.DataFrame()

def get_market_summary() -> pd.DataFrame:
    """
    Obtém um resumo dos principais indicadores de mercado.
    
    Returns:
        pd.DataFrame: DataFrame com o resumo dos indicadores.
    """
    # Cria um DataFrame para o resumo
    resumo = pd.DataFrame(columns=['Valor', 'Data'])
    
    try:
        # Obtém os dados do Ibovespa
        ibov = yf.Ticker("^BVSP")
        ibov_info = ibov.info
        ibov_hist = ibov.history(period="1y")
        
        # Adiciona o valor atual do Ibovespa
        if not ibov_hist.empty:
            ultimo_valor = ibov_hist['Close'].iloc[-1]
            data_valor = ibov_hist.index[-1].strftime('%d/%m/%Y')
            resumo.loc['Ibovespa'] = [ultimo_valor, data_valor]
        
        # Adiciona a variação do Ibovespa em 1 mês
        if not ibov_hist.empty and len(ibov_hist) > 20:
            valor_atual = ibov_hist['Close'].iloc[-1]
            valor_anterior = ibov_hist['Close'].iloc[-21]  # Aproximadamente 1 mês (21 dias úteis)
            variacao_1m = ((valor_atual / valor_anterior) - 1) * 100
            resumo.loc['Ibovespa (var. 1 mês)'] = [variacao_1m, data_valor]
        
        # Adiciona a variação do Ibovespa em 1 ano
        if not ibov_hist.empty and len(ibov_hist) > 250:
            valor_atual = ibov_hist['Close'].iloc[-1]
            valor_anterior = ibov_hist['Close'].iloc[0]
            variacao_1a = ((valor_atual / valor_anterior) - 1) * 100
            resumo.loc['Ibovespa (var. 1 ano)'] = [variacao_1a, data_valor]
        
        # Obtém os múltiplos do Ibovespa
        if 'trailingPE' in ibov_info and ibov_info['trailingPE'] is not None:
            resumo.loc['Ibovespa P/L'] = [ibov_info['trailingPE'], data_valor]
        
        # Obtém os dados do Fed Model
        fed_model = get_fed_model_data()
        if not fed_model.empty and 'Prêmio de Risco (%)' in fed_model.columns:
            premio_risco = fed_model['Prêmio de Risco (%)'].iloc[0]
            resumo.loc['Prêmio de Risco (%)'] = [premio_risco, data_valor]
        
        # Obtém os dados do dólar
        dolar = yf.Ticker("BRL=X")
        dolar_hist = dolar.history(period="1y")
        
        if not dolar_hist.empty:
            ultimo_valor = dolar_hist['Close'].iloc[-1]
            data_valor = dolar_hist.index[-1].strftime('%d/%m/%Y')
            resumo.loc['Dólar (R$)'] = [ultimo_valor, data_valor]
            
            # Adiciona a variação do dólar em 1 mês
            if len(dolar_hist) > 20:
                valor_atual = dolar_hist['Close'].iloc[-1]
                valor_anterior = dolar_hist['Close'].iloc[-21]  # Aproximadamente 1 mês (21 dias úteis)
                variacao_1m = ((valor_atual / valor_anterior) - 1) * 100
                resumo.loc['Dólar (var. 1 mês)'] = [variacao_1m, data_valor]
    except Exception as e:
        print(f"Erro ao obter resumo de mercado: {e}")
    
    return resumo

def get_portfolio_data(portfolio: Dict[str, float], period: str = "1y") -> pd.DataFrame:
    """
    Obtém dados de uma carteira de ações.
    
    Args:
        portfolio: Dicionário com tickers e pesos da carteira.
        period: Período de dados a serem obtidos (ex: "1d", "1mo", "1y").
        
    Returns:
        pd.DataFrame: DataFrame com os dados da carteira.
    """
    # Obtém os tickers da carteira
    tickers = list(portfolio.keys())
    
    # Obtém os dados das ações da carteira
    dados_carteira = get_stock_data(tickers, period)
    
    return dados_carteira
