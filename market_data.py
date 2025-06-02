"""
Módulo para coleta e processamento de dados de mercado e ações da B3.

Este módulo contém funções para acessar APIs e fontes de dados que fornecem
informações sobre ações brasileiras, índices, setores da B3, múltiplos de valuation
e outros dados relevantes para análise de mercado.
"""

import os
import sys
import json
import time
import datetime
import pandas as pd
import numpy as np
import requests
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple

# Adicionar caminho para importar módulos do projeto
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATA_DIR, CACHE_DIR, CACHE_EXPIRY, API_RETRY_ATTEMPTS, API_TIMEOUT, SETORES_B3, CARTEIRA_BASE

# Configuração para Yahoo Finance
try:
    import yfinance as yf
except ImportError:
    print("Biblioteca yfinance não encontrada. Instalando...")
    os.system("pip install yfinance")
    import yfinance as yf

# Configuração para Investpy (dados da Investing.com)
try:
    import investpy
except ImportError:
    print("Biblioteca investpy não encontrada. Instalando...")
    os.system("pip install investpy")
    import investpy

# Mapeamento de tickers para adicionar sufixo .SA quando necessário
def format_ticker_for_yf(ticker: str) -> str:
    """
    Formata o ticker para uso com a API do Yahoo Finance.
    
    Args:
        ticker: Ticker da ação brasileira (ex: PETR4, VALE3).
        
    Returns:
        str: Ticker formatado para Yahoo Finance (ex: PETR4.SA, VALE3.SA).
    """
    # Se já tiver o sufixo .SA, retorna como está
    if ticker.endswith('.SA'):
        return ticker
    
    # Adiciona o sufixo .SA para ações brasileiras
    return f"{ticker}.SA"

# Mapeamento de setores da B3 para tickers representativos
SETORES_TICKERS = {
    "Financeiro": ["ITUB4.SA", "BBDC4.SA", "B3SA3.SA", "BBAS3.SA", "SANB11.SA"],
    "Energia": ["PETR4.SA", "PETR3.SA", "PRIO3.SA", "CSAN3.SA", "UGPA3.SA"],
    "Materiais Básicos": ["VALE3.SA", "SUZB3.SA", "KLBN11.SA", "GGBR4.SA", "CSNA3.SA"],
    "Bens Industriais": ["WEGE3.SA", "RAIL3.SA", "EMBR3.SA", "RENT3.SA", "MOVI3.SA"],
    "Consumo Cíclico": ["LREN3.SA", "MGLU3.SA", "VVAR3.SA", "AMER3.SA", "LWSA3.SA"],
    "Consumo Não Cíclico": ["ABEV3.SA", "NTCO3.SA", "JBSS3.SA", "MRFG3.SA", "BRFS3.SA"],
    "Saúde": ["RDOR3.SA", "HAPV3.SA", "FLRY3.SA", "GNDI3.SA", "PARD3.SA"],
    "Tecnologia da Informação": ["TOTS3.SA", "LWSA3.SA", "CASH3.SA", "IFCM3.SA", "SQIA3.SA"],
    "Telecomunicações": ["VIVT3.SA", "TIMS3.SA", "OIBR3.SA", "TELB4.SA", "TELB3.SA"],
    "Utilidade Pública": ["SBSP3.SA", "CMIG4.SA", "ELET3.SA", "ELET6.SA", "ENGI11.SA"],
    "Imobiliário": ["BRML3.SA", "MULT3.SA", "IGTI11.SA", "ALSO3.SA", "CYRE3.SA"]
}

# Índices brasileiros importantes
INDICES_BRASIL = {
    "Ibovespa": "^BVSP",
    "IBrX-100": "^IBX",
    "IDIV": "^IDIV",
    "SMLL": "^SMLL",
    "IFIX": "^IFIX"
}

def get_cache_path(data_type: str) -> Path:
    """
    Retorna o caminho para o arquivo de cache de um determinado tipo de dado.
    
    Args:
        data_type: Tipo de dado para o qual se deseja o caminho de cache.
        
    Returns:
        Path: Caminho para o arquivo de cache.
    """
    return CACHE_DIR / f"{data_type}.parquet"

def is_cache_valid(data_type: str) -> bool:
    """
    Verifica se o cache para um determinado tipo de dado é válido.
    
    Args:
        data_type: Tipo de dado para verificar a validade do cache.
        
    Returns:
        bool: True se o cache for válido, False caso contrário.
    """
    cache_path = get_cache_path(data_type)
    
    # Se o arquivo não existe, o cache não é válido
    if not cache_path.exists():
        return False
    
    # Verifica a data de modificação do arquivo
    mtime = cache_path.stat().st_mtime
    last_modified = datetime.datetime.fromtimestamp(mtime)
    now = datetime.datetime.now()
    
    # Determina o tempo de expiração com base no tipo de dado
    if data_type in CACHE_EXPIRY:
        expiry_hours = CACHE_EXPIRY[data_type]
    else:
        expiry_hours = 24  # Padrão: 24 horas
    
    # Verifica se o cache expirou
    return (now - last_modified).total_seconds() < expiry_hours * 3600

def save_to_cache(data: pd.DataFrame, data_type: str) -> None:
    """
    Salva dados em cache.
    
    Args:
        data: DataFrame com os dados a serem salvos.
        data_type: Tipo de dado sendo salvo.
    """
    cache_path = get_cache_path(data_type)
    data.to_parquet(cache_path)

def load_from_cache(data_type: str) -> pd.DataFrame:
    """
    Carrega dados do cache.
    
    Args:
        data_type: Tipo de dado a ser carregado.
        
    Returns:
        pd.DataFrame: DataFrame com os dados carregados do cache.
    """
    cache_path = get_cache_path(data_type)
    return pd.read_parquet(cache_path)

def get_stock_data(tickers: List[str], period: str = "5y", interval: str = "1d", 
                  use_cache: bool = True) -> pd.DataFrame:
    """
    Obtém dados históricos de ações.
    
    Args:
        tickers: Lista de tickers das ações.
        period: Período de dados a serem obtidos (ex: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max).
        interval: Intervalo dos dados (ex: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo).
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        pd.DataFrame: DataFrame com os dados históricos das ações.
    """
    data_type = f"stocks_{period}_{interval}"
    
    # Verifica se pode usar cache
    if use_cache and is_cache_valid(data_type):
        return load_from_cache(data_type)
    
    # Formata os tickers para o Yahoo Finance
    formatted_tickers = [format_ticker_for_yf(ticker) for ticker in tickers]
    
    try:
        # Obtém os dados do Yahoo Finance
        data = yf.download(
            tickers=formatted_tickers,
            period=period,
            interval=interval,
            group_by='ticker',
            auto_adjust=True,
            prepost=False,
            threads=True
        )
        
        # Se apenas um ticker foi solicitado, reorganiza o DataFrame
        if len(formatted_tickers) == 1:
            ticker = formatted_tickers[0]
            data.columns = pd.MultiIndex.from_product([[ticker], data.columns])
        
        # Salva em cache
        if not data.empty:
            save_to_cache(data, data_type)
        
        return data
    
    except Exception as e:
        print(f"Erro ao obter dados de ações: {e}")
        return pd.DataFrame()

def get_index_data(indices: List[str] = None, period: str = "5y", interval: str = "1d", 
                  use_cache: bool = True) -> pd.DataFrame:
    """
    Obtém dados históricos de índices.
    
    Args:
        indices: Lista de índices. Se None, usa os índices brasileiros padrão.
        period: Período de dados a serem obtidos.
        interval: Intervalo dos dados.
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        pd.DataFrame: DataFrame com os dados históricos dos índices.
    """
    data_type = f"indices_{period}_{interval}"
    
    # Verifica se pode usar cache
    if use_cache and is_cache_valid(data_type):
        return load_from_cache(data_type)
    
    # Se não foram especificados índices, usa os índices brasileiros padrão
    if indices is None:
        indices = list(INDICES_BRASIL.values())
    
    try:
        # Obtém os dados do Yahoo Finance
        data = yf.download(
            tickers=indices,
            period=period,
            interval=interval,
            group_by='ticker',
            auto_adjust=True,
            prepost=False,
            threads=True
        )
        
        # Se apenas um índice foi solicitado, reorganiza o DataFrame
        if len(indices) == 1:
            index = indices[0]
            data.columns = pd.MultiIndex.from_product([[index], data.columns])
        
        # Salva em cache
        if not data.empty:
            save_to_cache(data, data_type)
        
        return data
    
    except Exception as e:
        print(f"Erro ao obter dados de índices: {e}")
        return pd.DataFrame()

def get_sector_data(period: str = "5y", interval: str = "1d", use_cache: bool = True) -> Dict[str, pd.DataFrame]:
    """
    Obtém dados históricos por setor da B3.
    
    Args:
        period: Período de dados a serem obtidos.
        interval: Intervalo dos dados.
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        Dict[str, pd.DataFrame]: Dicionário com os dados históricos por setor.
    """
    data_type = f"sectors_{period}_{interval}"
    
    # Verifica se pode usar cache
    if use_cache and is_cache_valid(data_type):
        return load_from_cache(data_type)
    
    result = {}
    
    for setor, tickers in SETORES_TICKERS.items():
        try:
            # Obtém os dados do setor
            data = get_stock_data(tickers, period, interval, use_cache=False)
            
            if not data.empty:
                result[setor] = data
        
        except Exception as e:
            print(f"Erro ao obter dados do setor {setor}: {e}")
    
    # Salva em cache
    if result:
        save_to_cache(pd.DataFrame({'setores': list(result.keys())}), data_type)
    
    return result

def get_stock_info(tickers: List[str], use_cache: bool = True) -> Dict[str, Dict]:
    """
    Obtém informações detalhadas sobre ações.
    
    Args:
        tickers: Lista de tickers das ações.
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        Dict[str, Dict]: Dicionário com informações detalhadas sobre as ações.
    """
    data_type = "stock_info"
    
    # Verifica se pode usar cache
    if use_cache and is_cache_valid(data_type):
        return load_from_cache(data_type)
    
    # Formata os tickers para o Yahoo Finance
    formatted_tickers = [format_ticker_for_yf(ticker) for ticker in tickers]
    
    result = {}
    
    for ticker in formatted_tickers:
        try:
            # Obtém informações da ação
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if info:
                result[ticker] = info
        
        except Exception as e:
            print(f"Erro ao obter informações da ação {ticker}: {e}")
    
    # Salva em cache
    if result:
        # Converte para DataFrame para salvar em cache
        df = pd.DataFrame({'ticker': list(result.keys())})
        df['info'] = df['ticker'].apply(lambda x: json.dumps(result[x]))
        save_to_cache(df, data_type)
    
    return result

def get_valuation_data(tickers: List[str], use_cache: bool = True) -> pd.DataFrame:
    """
    Obtém dados de valuation de ações.
    
    Args:
        tickers: Lista de tickers das ações.
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        pd.DataFrame: DataFrame com dados de valuation das ações.
    """
    data_type = "valuation"
    
    # Verifica se pode usar cache
    if use_cache and is_cache_valid(data_type):
        return load_from_cache(data_type)
    
    # Obtém informações detalhadas das ações
    info = get_stock_info(tickers, use_cache=False)
    
    # Cria DataFrame para os dados de valuation
    valuation = pd.DataFrame(index=tickers)
    
    for ticker in tickers:
        formatted_ticker = format_ticker_for_yf(ticker)
        
        if formatted_ticker in info:
            stock_info = info[formatted_ticker]
            
            # Extrai métricas de valuation
            valuation.loc[ticker, 'P/L'] = stock_info.get('trailingPE', np.nan)
            valuation.loc[ticker, 'P/VP'] = stock_info.get('priceToBook', np.nan)
            valuation.loc[ticker, 'EV/EBITDA'] = stock_info.get('enterpriseToEbitda', np.nan)
            valuation.loc[ticker, 'Dividend Yield'] = stock_info.get('dividendYield', np.nan)
            if valuation.loc[ticker, 'Dividend Yield'] is not None:
                valuation.loc[ticker, 'Dividend Yield'] *= 100  # Converte para percentual
            
            # Adiciona outras métricas úteis
            valuation.loc[ticker, 'Market Cap'] = stock_info.get('marketCap', np.nan)
            valuation.loc[ticker, 'Setor'] = stock_info.get('sector', '')
            valuation.loc[ticker, 'Indústria'] = stock_info.get('industry', '')
    
    # Salva em cache
    if not valuation.empty:
        save_to_cache(valuation, data_type)
    
    return valuation

def get_historical_valuation(tickers: List[str], years: int = 5, 
                            use_cache: bool = True) -> Dict[str, pd.DataFrame]:
    """
    Obtém dados históricos de valuation de ações.
    
    Args:
        tickers: Lista de tickers das ações.
        years: Número de anos de histórico.
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        Dict[str, pd.DataFrame]: Dicionário com dados históricos de valuation por ação.
    """
    data_type = f"historical_valuation_{years}y"
    
    # Verifica se pode usar cache
    if use_cache and is_cache_valid(data_type):
        return load_from_cache(data_type)
    
    # Obtém dados históricos de preços
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=365 * years)
    
    # Formata os tickers para o Yahoo Finance
    formatted_tickers = [format_ticker_for_yf(ticker) for ticker in tickers]
    
    result = {}
    
    for ticker in formatted_tickers:
        try:
            # Obtém dados históricos da ação
            stock = yf.Ticker(ticker)
            
            # Obtém dados financeiros trimestrais
            financials = stock.quarterly_financials
            balance_sheet = stock.quarterly_balance_sheet
            
            if financials.empty or balance_sheet.empty:
                continue
            
            # Calcula métricas de valuation históricas
            valuation = pd.DataFrame(index=financials.columns)
            
            # Obtém preços históricos
            prices = stock.history(start=start_date, end=end_date)
            
            # Para cada data de relatório financeiro
            for date in financials.columns:
                # Encontra o preço mais próximo da data do relatório
                closest_date = min(prices.index, key=lambda x: abs(x - date))
                price = prices.loc[closest_date, 'Close']
                
                # Calcula métricas de valuation
                net_income = financials.loc['Net Income', date]
                total_assets = balance_sheet.loc['Total Assets', date]
                total_liabilities = balance_sheet.loc['Total Liabilities Net Minority Interest', date]
                
                if pd.notna(net_income) and net_income != 0:
                    valuation.loc[date, 'P/L'] = price / (net_income / stock.info.get('sharesOutstanding', 1))
                
                book_value = total_assets - total_liabilities
                if pd.notna(book_value) and book_value != 0:
                    valuation.loc[date, 'P/VP'] = price / (book_value / stock.info.get('sharesOutstanding', 1))
            
            result[ticker] = valuation
        
        except Exception as e:
            print(f"Erro ao obter valuation histórico da ação {ticker}: {e}")
    
    # Salva em cache
    if result:
        # Converte para DataFrame para salvar em cache
        df = pd.DataFrame({'ticker': list(result.keys())})
        save_to_cache(df, data_type)
    
    return result

def get_sector_valuation(use_cache: bool = True) -> pd.DataFrame:
    """
    Obtém dados de valuation por setor da B3.
    
    Args:
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        pd.DataFrame: DataFrame com dados de valuation por setor.
    """
    data_type = "sector_valuation"
    
    # Verifica se pode usar cache
    if use_cache and is_cache_valid(data_type):
        return load_from_cache(data_type)
    
    # Cria DataFrame para os dados de valuation setorial
    sector_valuation = pd.DataFrame(index=SETORES_B3)
    
    for setor, tickers in SETORES_TICKERS.items():
        try:
            # Obtém dados de valuation das ações do setor
            valuation = get_valuation_data(tickers, use_cache=False)
            
            if not valuation.empty:
                # Calcula médias do setor
                sector_valuation.loc[setor, 'P/L'] = valuation['P/L'].mean()
                sector_valuation.loc[setor, 'P/VP'] = valuation['P/VP'].mean()
                sector_valuation.loc[setor, 'EV/EBITDA'] = valuation['EV/EBITDA'].mean()
                sector_valuation.loc[setor, 'Dividend Yield'] = valuation['Dividend Yield'].mean()
                sector_valuation.loc[setor, 'Market Cap Total'] = valuation['Market Cap'].sum()
        
        except Exception as e:
            print(f"Erro ao obter valuation do setor {setor}: {e}")
    
    # Salva em cache
    if not sector_valuation.empty:
        save_to_cache(sector_valuation, data_type)
    
    return sector_valuation

def get_historical_sector_valuation(years: int = 5, use_cache: bool = True) -> Dict[str, pd.DataFrame]:
    """
    Obtém dados históricos de valuation por setor da B3.
    
    Args:
        years: Número de anos de histórico.
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        Dict[str, pd.DataFrame]: Dicionário com dados históricos de valuation por setor.
    """
    data_type = f"historical_sector_valuation_{years}y"
    
    # Verifica se pode usar cache
    if use_cache and is_cache_valid(data_type):
        return load_from_cache(data_type)
    
    result = {}
    
    for setor, tickers in SETORES_TICKERS.items():
        try:
            # Obtém dados históricos de valuation das ações do setor
            historical_valuation = get_historical_valuation(tickers, years, use_cache=False)
            
            if historical_valuation:
                # Combina os dados de todas as ações do setor
                sector_data = pd.DataFrame()
                
                for ticker, data in historical_valuation.items():
                    if sector_data.empty:
                        sector_data = data.copy()
                    else:
                        # Combina os dados, calculando médias
                        for col in data.columns:
                            if col in sector_data.columns:
                                sector_data[col] = (sector_data[col] + data[col]) / 2
                            else:
                                sector_data[col] = data[col]
                
                result[setor] = sector_data
        
        except Exception as e:
            print(f"Erro ao obter valuation histórico do setor {setor}: {e}")
    
    # Salva em cache
    if result:
        # Converte para DataFrame para salvar em cache
        df = pd.DataFrame({'setor': list(result.keys())})
        save_to_cache(df, data_type)
    
    return result

def get_portfolio_data(tickers: List[str] = None, period: str = "1y", 
                      interval: str = "1d", use_cache: bool = True) -> pd.DataFrame:
    """
    Obtém dados históricos da carteira de ações.
    
    Args:
        tickers: Lista de tickers das ações. Se None, usa a carteira base.
        period: Período de dados a serem obtidos.
        interval: Intervalo dos dados.
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        pd.DataFrame: DataFrame com os dados históricos da carteira.
    """
    # Se não foram especificados tickers, usa a carteira base
    if tickers is None:
        tickers = CARTEIRA_BASE
    
    data_type = f"portfolio_{period}_{interval}"
    
    # Verifica se pode usar cache
    if use_cache and is_cache_valid(data_type):
        return load_from_cache(data_type)
    
    # Obtém dados históricos das ações
    data = get_stock_data(tickers, period, interval, use_cache=False)
    
    # Salva em cache
    if not data.empty:
        save_to_cache(data, data_type)
    
    return data

def get_portfolio_valuation(tickers: List[str] = None, use_cache: bool = True) -> pd.DataFrame:
    """
    Obtém dados de valuation da carteira de ações.
    
    Args:
        tickers: Lista de tickers das ações. Se None, usa a carteira base.
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        pd.DataFrame: DataFrame com dados de valuation da carteira.
    """
    # Se não foram especificados tickers, usa a carteira base
    if tickers is None:
        tickers = CARTEIRA_BASE
    
    # Obtém dados de valuation das ações
    return get_valuation_data(tickers, use_cache)

def get_fed_model_data(use_cache: bool = True) -> pd.DataFrame:
    """
    Obtém dados para o Fed Model adaptado para o Brasil.
    
    O Fed Model compara o Earnings Yield (E/P) do mercado de ações com a taxa de juros de longo prazo.
    
    Args:
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        pd.DataFrame: DataFrame com os dados do Fed Model.
    """
    data_type = "fed_model"
    
    # Verifica se pode usar cache
    if use_cache and is_cache_valid(data_type):
        return load_from_cache(data_type)
    
    try:
        # Obtém dados do Ibovespa
        ibovespa = yf.Ticker("^BVSP")
        ibovespa_info = ibovespa.info
        
        # Obtém dados de juros de longo prazo (Swap Pré-DI de 1080 dias - 3 anos)
        from .macro_data import get_bcb_series, BCB_SERIES
        juros_longo_prazo = get_bcb_series(BCB_SERIES["swap_pre_di_1080"])
        
        # Cria DataFrame para o Fed Model
        fed_model = pd.DataFrame(index=[datetime.datetime.now().strftime('%Y-%m-%d')])
        
        # Calcula o Earnings Yield do Ibovespa (inverso do P/L)
        if 'trailingPE' in ibovespa_info and ibovespa_info['trailingPE'] > 0:
            earnings_yield = 100 / ibovespa_info['trailingPE']  # Em percentual
            fed_model['Earnings Yield (%)'] = earnings_yield
        
        # Obtém a taxa de juros de longo prazo mais recente
        if not juros_longo_prazo.empty:
            taxa_juros = juros_longo_prazo.iloc[-1, 0]
            fed_model['Taxa de Juros Longo Prazo (%)'] = taxa_juros
        
        # Calcula o prêmio de risco (Earnings Yield - Taxa de Juros)
        if 'Earnings Yield (%)' in fed_model.columns and 'Taxa de Juros Longo Prazo (%)' in fed_model.columns:
            fed_model['Prêmio de Risco (%)'] = fed_model['Earnings Yield (%)'] - fed_model['Taxa de Juros Longo Prazo (%)']
        
        # Salva em cache
        if not fed_model.empty:
            save_to_cache(fed_model, data_type)
        
        return fed_model
    
    except Exception as e:
        print(f"Erro ao obter dados do Fed Model: {e}")
        return pd.DataFrame()

def get_market_summary(use_cache: bool = True) -> pd.DataFrame:
    """
    Obtém um resumo dos principais indicadores de mercado.
    
    Args:
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        pd.DataFrame: DataFrame com o resumo dos indicadores de mercado.
    """
    # Obtém dados dos índices
    indices_data = get_index_data(list(INDICES_BRASIL.values()), period="1mo", use_cache=use_cache)
    
    # Obtém dados de valuation setorial
    sector_valuation = get_sector_valuation(use_cache=use_cache)
    
    # Obtém dados do Fed Model
    fed_model = get_fed_model_data(use_cache=use_cache)
    
    # Cria um DataFrame vazio para o resumo
    summary = pd.DataFrame()
    
    # Adiciona dados dos índices
    for nome, ticker in INDICES_BRASIL.items():
        if ticker in indices_data.columns.levels[0]:
            # Calcula a variação percentual do índice no último mês
            first_price = indices_data[ticker]['Close'].iloc[0]
            last_price = indices_data[ticker]['Close'].iloc[-1]
            variacao = ((last_price / first_price) - 1) * 100
            
            summary.loc[nome, 'Valor'] = last_price
            summary.loc[nome, 'Variação 1M (%)'] = variacao
            summary.loc[nome, 'Data'] = indices_data.index[-1].strftime('%d/%m/%Y')
    
    # Adiciona dados de valuation setorial médio
    if not sector_valuation.empty:
        summary.loc['P/L Médio Setorial', 'Valor'] = sector_valuation['P/L'].mean()
        summary.loc['P/VP Médio Setorial', 'Valor'] = sector_valuation['P/VP'].mean()
        summary.loc['EV/EBITDA Médio Setorial', 'Valor'] = sector_valuation['EV/EBITDA'].mean()
        summary.loc['Dividend Yield Médio Setorial (%)', 'Valor'] = sector_valuation['Dividend Yield'].mean()
    
    # Adiciona dados do Fed Model
    if not fed_model.empty and 'Prêmio de Risco (%)' in fed_model.columns:
        summary.loc['Prêmio de Risco - Fed Model (%)', 'Valor'] = fed_model['Prêmio de Risco (%)'].iloc[0]
    
    return summary

if __name__ == "__main__":
    # Teste das funções
    print("Testando funções de coleta de dados de mercado...")
    
    # Obtém resumo dos indicadores de mercado
    summary = get_market_summary(use_cache=False)
    print("\nResumo dos Indicadores de Mercado:")
    print(summary)
