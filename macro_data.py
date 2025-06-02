"""
Módulo para coleta e processamento de dados macroeconômicos do Brasil.

Este módulo contém funções para acessar APIs e fontes de dados que fornecem
indicadores macroeconômicos brasileiros, como PIB, inflação, juros, desemprego,
liquidez e indicadores de risco.
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

from config import DATA_DIR, CACHE_DIR, CACHE_EXPIRY, API_RETRY_ATTEMPTS, API_TIMEOUT

# Configuração para API do Banco Central do Brasil (BCB)
try:
    import bcb
except ImportError:
    print("Biblioteca BCB não encontrada. Instalando...")
    os.system("pip install bcb")
    import bcb

# Configuração para API do IPEA
IPEA_BASE_URL = "http://www.ipeadata.gov.br/api/odata4"

# Mapeamento de séries do Banco Central do Brasil (SGS)
BCB_SERIES = {
    # PIB
    "pib_trimestral": 4380,  # PIB Trimestral - Valores correntes
    "pib_variacao_anual": 1207,  # PIB - Variação real anual
    
    # Inflação
    "ipca_mensal": 433,  # IPCA - Mensal
    "ipca_acumulado_12_meses": 13522,  # IPCA - Acumulado 12 meses
    "igpm_mensal": 189,  # IGP-M - Mensal
    "igpm_acumulado_12_meses": 13599,  # IGP-M - Acumulado 12 meses
    
    # Juros
    "selic_meta": 432,  # Meta Selic definida pelo Copom
    "selic_diaria": 11,  # Taxa Selic diária
    "selic_acumulada_mes": 4189,  # Taxa Selic acumulada no mês
    
    # Curva de Juros
    "swap_pre_di_30": 7805,  # Swap Pré-DI de 30 dias
    "swap_pre_di_90": 7806,  # Swap Pré-DI de 90 dias
    "swap_pre_di_180": 7807,  # Swap Pré-DI de 180 dias
    "swap_pre_di_360": 7808,  # Swap Pré-DI de 360 dias
    "swap_pre_di_720": 7809,  # Swap Pré-DI de 720 dias (2 anos)
    "swap_pre_di_1080": 7810,  # Swap Pré-DI de 1080 dias (3 anos)
    
    # Mercado de Trabalho
    "taxa_desemprego": 24369,  # Taxa de desemprego - PNADC
    "caged_saldo": 28763,  # Saldo de empregos formais - CAGED
    
    # Liquidez
    "m1": 27841,  # M1 - Base monetária
    "m2": 27842,  # M2 - M1 + depósitos de poupança e títulos privados
    "m3": 27843,  # M3 - M2 + quotas de fundos e títulos públicos
    "m4": 27844,  # M4 - M3 + títulos públicos em poder do público
    
    # Risco
    "embi_brasil": 3543,  # EMBI+ Brasil (Risco-país)
}

# Mapeamento de séries do IPEA
IPEA_SERIES = {
    "cds_brasil_5y": "GAP12_CRDSCBR5Y",  # Credit Default Swap - Brasil 5 anos
    "ifix": "BMF12_IFIX12",  # Índice de Fundos Imobiliários
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

def get_bcb_series(series_id: int, start_date: Optional[str] = None, 
                  end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Obtém série temporal do Sistema Gerenciador de Séries Temporais (SGS) do Banco Central do Brasil.
    
    Args:
        series_id: Código da série no SGS.
        start_date: Data de início no formato 'YYYY-MM-DD'. Se None, obtém desde o início da série.
        end_date: Data de fim no formato 'YYYY-MM-DD'. Se None, obtém até a data atual.
        
    Returns:
        pd.DataFrame: DataFrame com a série temporal.
    """
    try:
        # Tenta obter a série do BCB
        for attempt in range(API_RETRY_ATTEMPTS):
            try:
                if start_date and end_date:
                    df = bcb.sgs.get(series_id, start=start_date, end=end_date)
                else:
                    df = bcb.sgs.get(series_id)
                
                # Renomeia a coluna para o código da série
                df.columns = [str(series_id)]
                return df
            
            except Exception as e:
                if attempt < API_RETRY_ATTEMPTS - 1:
                    time.sleep(2)  # Espera 2 segundos antes de tentar novamente
                else:
                    raise e
    
    except Exception as e:
        print(f"Erro ao obter série {series_id} do BCB: {e}")
        return pd.DataFrame()

def get_multiple_bcb_series(series_ids: List[int], start_date: Optional[str] = None, 
                           end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Obtém múltiplas séries temporais do BCB e as combina em um único DataFrame.
    
    Args:
        series_ids: Lista de códigos das séries no SGS.
        start_date: Data de início no formato 'YYYY-MM-DD'. Se None, obtém desde o início da série.
        end_date: Data de fim no formato 'YYYY-MM-DD'. Se None, obtém até a data atual.
        
    Returns:
        pd.DataFrame: DataFrame com as séries temporais combinadas.
    """
    result = pd.DataFrame()
    
    for series_id in series_ids:
        df = get_bcb_series(series_id, start_date, end_date)
        
        if not df.empty:
            if result.empty:
                result = df
            else:
                result = result.join(df, how='outer')
    
    return result

def get_ipea_series(series_code: str, start_date: Optional[str] = None, 
                   end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Obtém série temporal da API do IPEA.
    
    Args:
        series_code: Código da série no IPEA.
        start_date: Data de início no formato 'YYYY-MM-DD'. Se None, obtém desde o início da série.
        end_date: Data de fim no formato 'YYYY-MM-DD'. Se None, obtém até a data atual.
        
    Returns:
        pd.DataFrame: DataFrame com a série temporal.
    """
    url = f"{IPEA_BASE_URL}/ValoresSerie(SERCODIGO='{series_code}')"
    
    if start_date:
        start_date_obj = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        start_date_str = start_date_obj.strftime('%Y-%m-%d')
        url += f"?$filter=VALDATA ge {start_date_str}"
        
        if end_date:
            end_date_obj = datetime.datetime.strptime(end_date, '%Y-%m-%d')
            end_date_str = end_date_obj.strftime('%Y-%m-%d')
            url += f" and VALDATA le {end_date_str}"
    
    try:
        for attempt in range(API_RETRY_ATTEMPTS):
            try:
                response = requests.get(url, timeout=API_TIMEOUT)
                response.raise_for_status()
                
                data = response.json()
                values = data.get('value', [])
                
                if not values:
                    return pd.DataFrame()
                
                # Cria DataFrame com os dados
                df = pd.DataFrame(values)
                
                # Converte a coluna de data
                df['VALDATA'] = pd.to_datetime(df['VALDATA'])
                
                # Renomeia e seleciona colunas
                df = df.rename(columns={'VALDATA': 'date', 'VALVALOR': series_code})
                df = df[['date', series_code]].set_index('date')
                
                return df
            
            except Exception as e:
                if attempt < API_RETRY_ATTEMPTS - 1:
                    time.sleep(2)  # Espera 2 segundos antes de tentar novamente
                else:
                    raise e
    
    except Exception as e:
        print(f"Erro ao obter série {series_code} do IPEA: {e}")
        return pd.DataFrame()

def get_pib_data(use_cache: bool = True) -> pd.DataFrame:
    """
    Obtém dados do PIB brasileiro.
    
    Args:
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        pd.DataFrame: DataFrame com os dados do PIB.
    """
    data_type = "pib"
    
    # Verifica se pode usar cache
    if use_cache and is_cache_valid(data_type):
        return load_from_cache(data_type)
    
    # Séries do PIB a serem obtidas
    series_ids = [
        BCB_SERIES["pib_trimestral"],
        BCB_SERIES["pib_variacao_anual"]
    ]
    
    # Obtém os dados
    df = get_multiple_bcb_series(series_ids)
    
    if not df.empty:
        # Renomeia as colunas
        df = df.rename(columns={
            str(BCB_SERIES["pib_trimestral"]): "pib_valor",
            str(BCB_SERIES["pib_variacao_anual"]): "pib_variacao"
        })
        
        # Salva em cache
        save_to_cache(df, data_type)
    
    return df

def get_inflacao_data(use_cache: bool = True) -> pd.DataFrame:
    """
    Obtém dados de inflação brasileira (IPCA e IGP-M).
    
    Args:
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        pd.DataFrame: DataFrame com os dados de inflação.
    """
    data_type = "inflacao"
    
    # Verifica se pode usar cache
    if use_cache and is_cache_valid(data_type):
        return load_from_cache(data_type)
    
    # Séries de inflação a serem obtidas
    series_ids = [
        BCB_SERIES["ipca_mensal"],
        BCB_SERIES["ipca_acumulado_12_meses"],
        BCB_SERIES["igpm_mensal"],
        BCB_SERIES["igpm_acumulado_12_meses"]
    ]
    
    # Obtém os dados
    df = get_multiple_bcb_series(series_ids)
    
    if not df.empty:
        # Renomeia as colunas
        df = df.rename(columns={
            str(BCB_SERIES["ipca_mensal"]): "ipca_mensal",
            str(BCB_SERIES["ipca_acumulado_12_meses"]): "ipca_acumulado_12m",
            str(BCB_SERIES["igpm_mensal"]): "igpm_mensal",
            str(BCB_SERIES["igpm_acumulado_12_meses"]): "igpm_acumulado_12m"
        })
        
        # Salva em cache
        save_to_cache(df, data_type)
    
    return df

def get_juros_data(use_cache: bool = True) -> pd.DataFrame:
    """
    Obtém dados de juros brasileiros (Selic).
    
    Args:
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        pd.DataFrame: DataFrame com os dados de juros.
    """
    data_type = "juros"
    
    # Verifica se pode usar cache
    if use_cache and is_cache_valid(data_type):
        return load_from_cache(data_type)
    
    # Séries de juros a serem obtidas
    series_ids = [
        BCB_SERIES["selic_meta"],
        BCB_SERIES["selic_diaria"],
        BCB_SERIES["selic_acumulada_mes"]
    ]
    
    # Obtém os dados
    df = get_multiple_bcb_series(series_ids)
    
    if not df.empty:
        # Renomeia as colunas
        df = df.rename(columns={
            str(BCB_SERIES["selic_meta"]): "selic_meta",
            str(BCB_SERIES["selic_diaria"]): "selic_diaria",
            str(BCB_SERIES["selic_acumulada_mes"]): "selic_acumulada_mes"
        })
        
        # Salva em cache
        save_to_cache(df, data_type)
    
    return df

def get_curva_juros_data(use_cache: bool = True) -> pd.DataFrame:
    """
    Obtém dados da curva de juros brasileira (Swaps DI-Pré).
    
    Args:
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        pd.DataFrame: DataFrame com os dados da curva de juros.
    """
    data_type = "curva_juros"
    
    # Verifica se pode usar cache
    if use_cache and is_cache_valid(data_type):
        return load_from_cache(data_type)
    
    # Séries da curva de juros a serem obtidas
    series_ids = [
        BCB_SERIES["swap_pre_di_30"],
        BCB_SERIES["swap_pre_di_90"],
        BCB_SERIES["swap_pre_di_180"],
        BCB_SERIES["swap_pre_di_360"],
        BCB_SERIES["swap_pre_di_720"],
        BCB_SERIES["swap_pre_di_1080"]
    ]
    
    # Obtém os dados
    df = get_multiple_bcb_series(series_ids)
    
    if not df.empty:
        # Renomeia as colunas
        df = df.rename(columns={
            str(BCB_SERIES["swap_pre_di_30"]): "di_30d",
            str(BCB_SERIES["swap_pre_di_90"]): "di_90d",
            str(BCB_SERIES["swap_pre_di_180"]): "di_180d",
            str(BCB_SERIES["swap_pre_di_360"]): "di_360d",
            str(BCB_SERIES["swap_pre_di_720"]): "di_720d",
            str(BCB_SERIES["swap_pre_di_1080"]): "di_1080d"
        })
        
        # Salva em cache
        save_to_cache(df, data_type)
    
    return df

def get_trabalho_data(use_cache: bool = True) -> pd.DataFrame:
    """
    Obtém dados do mercado de trabalho brasileiro.
    
    Args:
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        pd.DataFrame: DataFrame com os dados do mercado de trabalho.
    """
    data_type = "trabalho"
    
    # Verifica se pode usar cache
    if use_cache and is_cache_valid(data_type):
        return load_from_cache(data_type)
    
    # Séries do mercado de trabalho a serem obtidas
    series_ids = [
        BCB_SERIES["taxa_desemprego"],
        BCB_SERIES["caged_saldo"]
    ]
    
    # Obtém os dados
    df = get_multiple_bcb_series(series_ids)
    
    if not df.empty:
        # Renomeia as colunas
        df = df.rename(columns={
            str(BCB_SERIES["taxa_desemprego"]): "desemprego",
            str(BCB_SERIES["caged_saldo"]): "caged_saldo"
        })
        
        # Salva em cache
        save_to_cache(df, data_type)
    
    return df

def get_liquidez_data(use_cache: bool = True) -> pd.DataFrame:
    """
    Obtém dados de liquidez e agregados monetários brasileiros.
    
    Args:
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        pd.DataFrame: DataFrame com os dados de liquidez.
    """
    data_type = "liquidez"
    
    # Verifica se pode usar cache
    if use_cache and is_cache_valid(data_type):
        return load_from_cache(data_type)
    
    # Séries de liquidez a serem obtidas
    series_ids = [
        BCB_SERIES["m1"],
        BCB_SERIES["m2"],
        BCB_SERIES["m3"],
        BCB_SERIES["m4"]
    ]
    
    # Obtém os dados
    df = get_multiple_bcb_series(series_ids)
    
    if not df.empty:
        # Renomeia as colunas
        df = df.rename(columns={
            str(BCB_SERIES["m1"]): "m1",
            str(BCB_SERIES["m2"]): "m2",
            str(BCB_SERIES["m3"]): "m3",
            str(BCB_SERIES["m4"]): "m4"
        })
        
        # Salva em cache
        save_to_cache(df, data_type)
    
    return df

def get_risco_data(use_cache: bool = True) -> pd.DataFrame:
    """
    Obtém dados de risco do Brasil (EMBI+, CDS, IFIX).
    
    Args:
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        pd.DataFrame: DataFrame com os dados de risco.
    """
    data_type = "risco"
    
    # Verifica se pode usar cache
    if use_cache and is_cache_valid(data_type):
        return load_from_cache(data_type)
    
    # Obtém EMBI+ do BCB
    embi_df = get_bcb_series(BCB_SERIES["embi_brasil"])
    
    # Obtém CDS do IPEA
    cds_df = get_ipea_series(IPEA_SERIES["cds_brasil_5y"])
    
    # Obtém IFIX do IPEA
    ifix_df = get_ipea_series(IPEA_SERIES["ifix"])
    
    # Combina os DataFrames
    df = pd.DataFrame()
    
    if not embi_df.empty:
        embi_df = embi_df.rename(columns={str(BCB_SERIES["embi_brasil"]): "embi"})
        df = embi_df
    
    if not cds_df.empty:
        if df.empty:
            df = cds_df
        else:
            df = df.join(cds_df, how='outer')
    
    if not ifix_df.empty:
        if df.empty:
            df = ifix_df
        else:
            df = df.join(ifix_df, how='outer')
    
    if not df.empty:
        # Salva em cache
        save_to_cache(df, data_type)
    
    return df

def get_all_macro_data(use_cache: bool = True) -> Dict[str, pd.DataFrame]:
    """
    Obtém todos os dados macroeconômicos.
    
    Args:
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        Dict[str, pd.DataFrame]: Dicionário com todos os dados macroeconômicos.
    """
    return {
        "pib": get_pib_data(use_cache),
        "inflacao": get_inflacao_data(use_cache),
        "juros": get_juros_data(use_cache),
        "curva_juros": get_curva_juros_data(use_cache),
        "trabalho": get_trabalho_data(use_cache),
        "liquidez": get_liquidez_data(use_cache),
        "risco": get_risco_data(use_cache)
    }

def get_macro_summary(use_cache: bool = True) -> pd.DataFrame:
    """
    Obtém um resumo dos principais indicadores macroeconômicos.
    
    Args:
        use_cache: Se True, usa dados em cache se disponíveis e válidos.
        
    Returns:
        pd.DataFrame: DataFrame com o resumo dos indicadores macroeconômicos.
    """
    # Obtém os dados
    inflacao = get_inflacao_data(use_cache)
    juros = get_juros_data(use_cache)
    trabalho = get_trabalho_data(use_cache)
    risco = get_risco_data(use_cache)
    
    # Cria um DataFrame vazio para o resumo
    summary = pd.DataFrame()
    
    # Adiciona IPCA
    if not inflacao.empty and 'ipca_acumulado_12m' in inflacao.columns:
        ipca = inflacao['ipca_acumulado_12m'].dropna().iloc[-1]
        summary.loc['IPCA (12 meses)', 'Valor'] = ipca
        summary.loc['IPCA (12 meses)', 'Data'] = inflacao.index[-1].strftime('%d/%m/%Y')
    
    # Adiciona IGP-M
    if not inflacao.empty and 'igpm_acumulado_12m' in inflacao.columns:
        igpm = inflacao['igpm_acumulado_12m'].dropna().iloc[-1]
        summary.loc['IGP-M (12 meses)', 'Valor'] = igpm
        summary.loc['IGP-M (12 meses)', 'Data'] = inflacao.index[-1].strftime('%d/%m/%Y')
    
    # Adiciona Selic
    if not juros.empty and 'selic_meta' in juros.columns:
        selic = juros['selic_meta'].dropna().iloc[-1]
        summary.loc['Taxa Selic', 'Valor'] = selic
        summary.loc['Taxa Selic', 'Data'] = juros.index[-1].strftime('%d/%m/%Y')
    
    # Adiciona Desemprego
    if not trabalho.empty and 'desemprego' in trabalho.columns:
        desemprego = trabalho['desemprego'].dropna().iloc[-1]
        summary.loc['Taxa de Desemprego', 'Valor'] = desemprego
        summary.loc['Taxa de Desemprego', 'Data'] = trabalho.index[-1].strftime('%d/%m/%Y')
    
    # Adiciona EMBI+
    if not risco.empty and 'embi' in risco.columns:
        embi = risco['embi'].dropna().iloc[-1]
        summary.loc['EMBI+ Brasil', 'Valor'] = embi
        summary.loc['EMBI+ Brasil', 'Data'] = risco.index[-1].strftime('%d/%m/%Y')
    
    # Adiciona CDS
    if not risco.empty and IPEA_SERIES["cds_brasil_5y"] in risco.columns:
        cds = risco[IPEA_SERIES["cds_brasil_5y"]].dropna().iloc[-1]
        summary.loc['CDS Brasil 5 anos', 'Valor'] = cds
        summary.loc['CDS Brasil 5 anos', 'Data'] = risco.index[-1].strftime('%d/%m/%Y')
    
    return summary

if __name__ == "__main__":
    # Teste das funções
    print("Testando funções de coleta de dados macroeconômicos...")
    
    # Obtém resumo dos indicadores
    summary = get_macro_summary(use_cache=False)
    print("\nResumo dos Indicadores Macroeconômicos:")
    print(summary)
