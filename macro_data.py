"""
Módulo para coleta e processamento de dados macroeconômicos.

Este módulo contém funções para obter dados macroeconômicos do Brasil,
como PIB, inflação, juros, mercado de trabalho, liquidez e risco.
"""

import pandas as pd
import numpy as np
import requests
import datetime
from typing import Dict, List, Optional, Union
import sys
import os
from pathlib import Path

# Importa as configurações
from config import BCB_SERIES, API_CONFIG

def get_bcb_data(codigo: int, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Obtém dados do Sistema Gerenciador de Séries Temporais (SGS) do Banco Central do Brasil.
    
    Args:
        codigo: Código da série temporal no SGS.
        start_date: Data de início no formato 'dd/mm/aaaa' (opcional).
        end_date: Data de fim no formato 'dd/mm/aaaa' (opcional).
        
    Returns:
        pd.DataFrame: DataFrame com os dados da série temporal.
    """
    # Constrói a URL
    url = f"{API_CONFIG['bcb']['base_url']}{codigo}{API_CONFIG['bcb']['format']}"
    
    # Adiciona parâmetros de data, se fornecidos
    params = {}
    if start_date:
        params['dataInicial'] = start_date
    if end_date:
        params['dataFinal'] = end_date
    
    try:
        # Faz a requisição
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        # Converte para DataFrame
        df = pd.DataFrame(response.json())
        
        # Converte a coluna de data para datetime
        df['data'] = pd.to_datetime(df['data'], dayfirst=True)
        
        # Define a data como índice
        df.set_index('data', inplace=True)
        
        return df
    except Exception as e:
        print(f"Erro ao obter dados do BCB (código {codigo}): {e}")
        # Retorna DataFrame vazio em caso de erro
        return pd.DataFrame()

def get_pib_data() -> pd.DataFrame:
    """
    Obtém dados do PIB brasileiro.
    
    Returns:
        pd.DataFrame: DataFrame com os dados do PIB.
    """
    # Obtém os dados do PIB mensal
    pib_mensal = get_bcb_data(BCB_SERIES['pib_mensal'])
    if not pib_mensal.empty:
        pib_mensal.columns = ['pib_valor']
    
    # Obtém os dados da variação anual do PIB
    pib_var_anual = get_bcb_data(BCB_SERIES['pib_var_anual'])
    if not pib_var_anual.empty:
        pib_var_anual.columns = ['pib_variacao']
    
    # Combina os DataFrames
    pib = pd.DataFrame()
    if not pib_mensal.empty:
        pib = pib_mensal
    
    if not pib_var_anual.empty:
        if pib.empty:
            pib = pib_var_anual
        else:
            pib = pib.join(pib_var_anual, how='outer')
    
    return pib

def get_inflacao_data() -> pd.DataFrame:
    """
    Obtém dados de inflação brasileira (IPCA e IGP-M).
    
    Returns:
        pd.DataFrame: DataFrame com os dados de inflação.
    """
    # Obtém os dados do IPCA mensal
    ipca_mensal = get_bcb_data(BCB_SERIES['ipca_mensal'])
    if not ipca_mensal.empty:
        ipca_mensal.columns = ['ipca_mensal']
    
    # Obtém os dados do IPCA acumulado em 12 meses
    ipca_acum_12m = get_bcb_data(BCB_SERIES['ipca_acum_12m'])
    if not ipca_acum_12m.empty:
        ipca_acum_12m.columns = ['ipca_acumulado_12m']
    
    # Obtém os dados do IGP-M mensal
    igpm_mensal = get_bcb_data(BCB_SERIES['igpm_mensal'])
    if not igpm_mensal.empty:
        igpm_mensal.columns = ['igpm_mensal']
    
    # Obtém os dados do IGP-M acumulado em 12 meses
    igpm_acum_12m = get_bcb_data(BCB_SERIES['igpm_acum_12m'])
    if not igpm_acum_12m.empty:
        igpm_acum_12m.columns = ['igpm_acumulado_12m']
    
    # Combina os DataFrames
    inflacao = pd.DataFrame()
    
    for df in [ipca_mensal, ipca_acum_12m, igpm_mensal, igpm_acum_12m]:
        if not df.empty:
            if inflacao.empty:
                inflacao = df
            else:
                inflacao = inflacao.join(df, how='outer')
    
    return inflacao

def get_juros_data() -> pd.DataFrame:
    """
    Obtém dados de juros brasileiros (Selic).
    
    Returns:
        pd.DataFrame: DataFrame com os dados de juros.
    """
    # Obtém os dados da Selic meta
    selic_meta = get_bcb_data(BCB_SERIES['selic_meta'])
    if not selic_meta.empty:
        selic_meta.columns = ['selic_meta']
    
    # Obtém os dados da Selic diária
    selic_diaria = get_bcb_data(BCB_SERIES['selic_diaria'])
    if not selic_diaria.empty:
        selic_diaria.columns = ['selic_diaria']
    
    # Combina os DataFrames
    juros = pd.DataFrame()
    
    for df in [selic_meta, selic_diaria]:
        if not df.empty:
            if juros.empty:
                juros = df
            else:
                juros = juros.join(df, how='outer')
    
    return juros

def get_curva_juros_data() -> pd.DataFrame:
    """
    Obtém dados da curva de juros brasileira (DI futuro).
    
    Returns:
        pd.DataFrame: DataFrame com os dados da curva de juros.
    """
    # Obtém os dados dos diferentes prazos do DI
    di_1m = get_bcb_data(BCB_SERIES['di_1m'])
    if not di_1m.empty:
        di_1m.columns = ['di_30d']
    
    di_3m = get_bcb_data(BCB_SERIES['di_3m'])
    if not di_3m.empty:
        di_3m.columns = ['di_90d']
    
    di_6m = get_bcb_data(BCB_SERIES['di_6m'])
    if not di_6m.empty:
        di_6m.columns = ['di_180d']
    
    di_1y = get_bcb_data(BCB_SERIES['di_1y'])
    if not di_1y.empty:
        di_1y.columns = ['di_360d']
    
    di_2y = get_bcb_data(BCB_SERIES['di_2y'])
    if not di_2y.empty:
        di_2y.columns = ['di_720d']
    
    di_3y = get_bcb_data(BCB_SERIES['di_3y'])
    if not di_3y.empty:
        di_3y.columns = ['di_1080d']
    
    # Combina os DataFrames
    curva_juros = pd.DataFrame()
    
    for df in [di_1m, di_3m, di_6m, di_1y, di_2y, di_3y]:
        if not df.empty:
            if curva_juros.empty:
                curva_juros = df
            else:
                curva_juros = curva_juros.join(df, how='outer')
    
    return curva_juros

def get_trabalho_data() -> pd.DataFrame:
    """
    Obtém dados do mercado de trabalho brasileiro.
    
    Returns:
        pd.DataFrame: DataFrame com os dados do mercado de trabalho.
    """
    # Obtém os dados da taxa de desemprego
    desemprego = get_bcb_data(BCB_SERIES['desemprego'])
    if not desemprego.empty:
        desemprego.columns = ['desemprego']
    
    # Obtém os dados do saldo do CAGED
    caged_saldo = get_bcb_data(BCB_SERIES['caged_saldo'])
    if not caged_saldo.empty:
        caged_saldo.columns = ['caged_saldo']
    
    # Combina os DataFrames
    trabalho = pd.DataFrame()
    
    for df in [desemprego, caged_saldo]:
        if not df.empty:
            if trabalho.empty:
                trabalho = df
            else:
                trabalho = trabalho.join(df, how='outer')
    
    return trabalho

def get_liquidez_data() -> pd.DataFrame:
    """
    Obtém dados de liquidez e agregados monetários brasileiros.
    
    Returns:
        pd.DataFrame: DataFrame com os dados de liquidez.
    """
    # Obtém os dados dos agregados monetários
    m1 = get_bcb_data(BCB_SERIES['m1'])
    if not m1.empty:
        m1.columns = ['m1']
    
    m2 = get_bcb_data(BCB_SERIES['m2'])
    if not m2.empty:
        m2.columns = ['m2']
    
    m3 = get_bcb_data(BCB_SERIES['m3'])
    if not m3.empty:
        m3.columns = ['m3']
    
    m4 = get_bcb_data(BCB_SERIES['m4'])
    if not m4.empty:
        m4.columns = ['m4']
    
    # Combina os DataFrames
    liquidez = pd.DataFrame()
    
    for df in [m1, m2, m3, m4]:
        if not df.empty:
            if liquidez.empty:
                liquidez = df
            else:
                liquidez = liquidez.join(df, how='outer')
    
    return liquidez

def get_risco_data() -> pd.DataFrame:
    """
    Obtém dados de risco do Brasil.
    
    Returns:
        pd.DataFrame: DataFrame com os dados de risco.
    """
    # Obtém os dados do EMBI+
    embi = get_bcb_data(BCB_SERIES['embi'])
    if not embi.empty:
        embi.columns = ['embi']
    
    # Obtém os dados do CDS de 5 anos
    cds_5y = get_bcb_data(BCB_SERIES['cds_5y'])
    if not cds_5y.empty:
        cds_5y.columns = ['GAP12_CRDSCBR5Y']
    
    # Obtém os dados do IFIX
    ifix = get_bcb_data(BCB_SERIES['ifix'])
    if not ifix.empty:
        ifix.columns = ['ifix']
    
    # Combina os DataFrames
    risco = pd.DataFrame()
    
    for df in [embi, cds_5y, ifix]:
        if not df.empty:
            if risco.empty:
                risco = df
            else:
                risco = risco.join(df, how='outer')
    
    return risco

def get_all_macro_data() -> Dict[str, pd.DataFrame]:
    """
    Obtém todos os dados macroeconômicos.
    
    Returns:
        Dict[str, pd.DataFrame]: Dicionário com DataFrames para cada grupo de dados.
    """
    # Obtém os dados de cada grupo
    pib = get_pib_data()
    inflacao = get_inflacao_data()
    juros = get_juros_data()
    curva_juros = get_curva_juros_data()
    trabalho = get_trabalho_data()
    liquidez = get_liquidez_data()
    risco = get_risco_data()
    
    # Retorna um dicionário com todos os dados
    return {
        'pib': pib,
        'inflacao': inflacao,
        'juros': juros,
        'curva_juros': curva_juros,
        'trabalho': trabalho,
        'liquidez': liquidez,
        'risco': risco
    }

def get_macro_summary() -> pd.DataFrame:
    """
    Obtém um resumo dos principais indicadores macroeconômicos.
    
    Returns:
        pd.DataFrame: DataFrame com o resumo dos indicadores.
    """
    # Obtém todos os dados macroeconômicos
    dados = get_all_macro_data()
    
    # Cria um DataFrame para o resumo
    resumo = pd.DataFrame(columns=['Valor', 'Data'])
    
    # Adiciona o PIB
    if not dados['pib'].empty and 'pib_variacao' in dados['pib'].columns:
        ultimo_pib = dados['pib']['pib_variacao'].dropna().iloc[-1]
        data_pib = dados['pib']['pib_variacao'].dropna().index[-1].strftime('%d/%m/%Y')
        resumo.loc['PIB (var. anual)'] = [ultimo_pib, data_pib]
    
    # Adiciona o IPCA
    if not dados['inflacao'].empty and 'ipca_acumulado_12m' in dados['inflacao'].columns:
        ultimo_ipca = dados['inflacao']['ipca_acumulado_12m'].dropna().iloc[-1]
        data_ipca = dados['inflacao']['ipca_acumulado_12m'].dropna().index[-1].strftime('%d/%m/%Y')
        resumo.loc['IPCA (12 meses)'] = [ultimo_ipca, data_ipca]
    
    # Adiciona o IGP-M
    if not dados['inflacao'].empty and 'igpm_acumulado_12m' in dados['inflacao'].columns:
        ultimo_igpm = dados['inflacao']['igpm_acumulado_12m'].dropna().iloc[-1]
        data_igpm = dados['inflacao']['igpm_acumulado_12m'].dropna().index[-1].strftime('%d/%m/%Y')
        resumo.loc['IGP-M (12 meses)'] = [ultimo_igpm, data_igpm]
    
    # Adiciona a Selic
    if not dados['juros'].empty and 'selic_meta' in dados['juros'].columns:
        ultima_selic = dados['juros']['selic_meta'].dropna().iloc[-1]
        data_selic = dados['juros']['selic_meta'].dropna().index[-1].strftime('%d/%m/%Y')
        resumo.loc['Taxa Selic'] = [ultima_selic, data_selic]
    
    # Adiciona a taxa de desemprego
    if not dados['trabalho'].empty and 'desemprego' in dados['trabalho'].columns:
        ultimo_desemprego = dados['trabalho']['desemprego'].dropna().iloc[-1]
        data_desemprego = dados['trabalho']['desemprego'].dropna().index[-1].strftime('%d/%m/%Y')
        resumo.loc['Taxa de Desemprego'] = [ultimo_desemprego, data_desemprego]
    
    # Adiciona o EMBI+
    if not dados['risco'].empty and 'embi' in dados['risco'].columns:
        ultimo_embi = dados['risco']['embi'].dropna().iloc[-1]
        data_embi = dados['risco']['embi'].dropna().index[-1].strftime('%d/%m/%Y')
        resumo.loc['EMBI+ Brasil'] = [ultimo_embi, data_embi]
    
    # Adiciona o CDS de 5 anos
    if not dados['risco'].empty and 'GAP12_CRDSCBR5Y' in dados['risco'].columns:
        ultimo_cds = dados['risco']['GAP12_CRDSCBR5Y'].dropna().iloc[-1]
        data_cds = dados['risco']['GAP12_CRDSCBR5Y'].dropna().index[-1].strftime('%d/%m/%Y')
        resumo.loc['CDS Brasil 5 anos'] = [ultimo_cds, data_cds]
    
    return resumo
