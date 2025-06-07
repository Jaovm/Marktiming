"""
Módulo para identificação do ciclo econômico e market timing.

Este módulo contém funções para identificar a fase atual do ciclo econômico,
calcular o score de market timing e gerar alertas.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
import datetime

# Importa as configurações e dados
from config import CICLO_PARAMS, TIMING_PARAMS
from macro_data import get_all_macro_data
from market_data import get_fed_model_data, get_sector_valuation
from valuation import classificar_valuation_setorial

def identificar_fase_ciclo() -> Dict[str, Union[str, float, Dict]]:
    """
    Identifica a fase atual do ciclo econômico com base em indicadores macroeconômicos.
    
    Returns:
        Dict: Dicionário com informações sobre a fase do ciclo econômico.
    """
    # Obtém os dados macroeconômicos
    dados_macro = get_all_macro_data()
    
    # Inicializa os scores para cada fase do ciclo
    scores = {
        'EXPANSAO': 0,
        'PICO': 0,
        'CONTRACAO': 0,
        'RECUPERACAO': 0
    }
    
    # Analisa a curva de juros
    curva_juros = {}
    if not dados_macro['curva_juros'].empty:
        # Calcula a inclinação da curva de juros (1 ano - 1 mês)
        if 'di_360d' in dados_macro['curva_juros'].columns and 'di_30d' in dados_macro['curva_juros'].columns:
            ultimo_di_1y = dados_macro['curva_juros']['di_360d'].iloc[-1]
            ultimo_di_1m = dados_macro['curva_juros']['di_30d'].iloc[-1]
            inclinacao_1y_1m = ultimo_di_1y - ultimo_di_1m
            curva_juros['inclinacao_1y_1m'] = inclinacao_1y_1m
        
        # Calcula a inclinação da curva de juros (3 anos - 1 ano)
        if 'di_1080d' in dados_macro['curva_juros'].columns and 'di_360d' in dados_macro['curva_juros'].columns:
            ultimo_di_3y = dados_macro['curva_juros']['di_1080d'].iloc[-1]
            ultimo_di_1y = dados_macro['curva_juros']['di_360d'].iloc[-1]
            inclinacao_3y_1y = ultimo_di_3y - ultimo_di_1y
            curva_juros['inclinacao_3y_1y'] = inclinacao_3y_1y
        
        # Calcula a inclinação da curva de juros (3 anos - 1 mês)
        if 'di_1080d' in dados_macro['curva_juros'].columns and 'di_30d' in dados_macro['curva_juros'].columns:
            ultimo_di_3y = dados_macro['curva_juros']['di_1080d'].iloc[-1]
            ultimo_di_1m = dados_macro['curva_juros']['di_30d'].iloc[-1]
            inclinacao_3y_1m = ultimo_di_3y - ultimo_di_1m
            curva_juros['inclinacao_3y_1m'] = inclinacao_3y_1m
        
        # Determina o status da curva de juros
        if 'inclinacao_1y_1m' in curva_juros:
            if curva_juros['inclinacao_1y_1m'] < CICLO_PARAMS['limites_inclinacao']['invertida']:
                curva_juros['status_curva'] = 'Invertida'
                # Curva invertida é típica do final do ciclo (PICO) ou início da contração
                scores['PICO'] += 0.8 * CICLO_PARAMS['pesos_indicadores']['curva_juros']
                scores['CONTRACAO'] += 0.2 * CICLO_PARAMS['pesos_indicadores']['curva_juros']
            elif curva_juros['inclinacao_1y_1m'] < CICLO_PARAMS['limites_inclinacao']['achatada']:
                curva_juros['status_curva'] = 'Achatada'
                # Curva achatada pode indicar transição entre fases
                scores['PICO'] += 0.5 * CICLO_PARAMS['pesos_indicadores']['curva_juros']
                scores['CONTRACAO'] += 0.3 * CICLO_PARAMS['pesos_indicadores']['curva_juros']
                scores['RECUPERACAO'] += 0.2 * CICLO_PARAMS['pesos_indicadores']['curva_juros']
            elif curva_juros['inclinacao_1y_1m'] < CICLO_PARAMS['limites_inclinacao']['normal']:
                curva_juros['status_curva'] = 'Normal'
                # Curva normal é típica da expansão ou recuperação
                scores['EXPANSAO'] += 0.6 * CICLO_PARAMS['pesos_indicadores']['curva_juros']
                scores['RECUPERACAO'] += 0.4 * CICLO_PARAMS['pesos_indicadores']['curva_juros']
            else:
                curva_juros['status_curva'] = 'Acentuada'
                # Curva acentuada é típica do início do ciclo (RECUPERACAO)
                scores['RECUPERACAO'] += 0.8 * CICLO_PARAMS['pesos_indicadores']['curva_juros']
                scores['EXPANSAO'] += 0.2 * CICLO_PARAMS['pesos_indicadores']['curva_juros']
    
    # Analisa a inflação
    inflacao = {}
    if not dados_macro['inflacao'].empty and 'ipca_acumulado_12m' in dados_macro['inflacao'].columns:
        # Obtém o IPCA acumulado em 12 meses
        ultimo_ipca = dados_macro['inflacao']['ipca_acumulado_12m'].iloc[-1]
        
        # Calcula a tendência do IPCA (últimos 3 meses vs 3 meses anteriores)
        if len(dados_macro['inflacao']) >= 6:
            ipca_ultimos_3m = dados_macro['inflacao']['ipca_acumulado_12m'].iloc[-3:].mean()
            ipca_3m_anteriores = dados_macro['inflacao']['ipca_acumulado_12m'].iloc[-6:-3].mean()
            tendencia_ipca = ipca_ultimos_3m - ipca_3m_anteriores
            
            if tendencia_ipca > 0.5:
                inflacao['tendencia_ipca'] = 'Aceleração'
                # Inflação acelerando é típica do PICO ou EXPANSAO
                scores['PICO'] += 0.7 * CICLO_PARAMS['pesos_indicadores']['inflacao']
                scores['EXPANSAO'] += 0.3 * CICLO_PARAMS['pesos_indicadores']['inflacao']
            elif tendencia_ipca > -0.5:
                inflacao['tendencia_ipca'] = 'Estável'
                # Inflação estável pode ocorrer em qualquer fase
                scores['EXPANSAO'] += 0.3 * CICLO_PARAMS['pesos_indicadores']['inflacao']
                scores['PICO'] += 0.3 * CICLO_PARAMS['pesos_indicadores']['inflacao']
                scores['CONTRACAO'] += 0.2 * CICLO_PARAMS['pesos_indicadores']['inflacao']
                scores['RECUPERACAO'] += 0.2 * CICLO_PARAMS['pesos_indicadores']['inflacao']
            else:
                inflacao['tendencia_ipca'] = 'Desaceleração'
                # Inflação desacelerando é típica da CONTRACAO ou RECUPERACAO
                scores['CONTRACAO'] += 0.6 * CICLO_PARAMS['pesos_indicadores']['inflacao']
                scores['RECUPERACAO'] += 0.4 * CICLO_PARAMS['pesos_indicadores']['inflacao']
        
        # Determina o nível do IPCA
        if ultimo_ipca > 8:
            inflacao['nivel_ipca'] = 'Alto'
            # Inflação alta é típica do PICO
            scores['PICO'] += 0.8 * CICLO_PARAMS['pesos_indicadores']['inflacao']
            scores['EXPANSAO'] += 0.2 * CICLO_PARAMS['pesos_indicadores']['inflacao']
        elif ultimo_ipca > 4.5:
            inflacao['nivel_ipca'] = 'Moderado'
            # Inflação moderada pode ocorrer na EXPANSAO ou RECUPERACAO
            scores['EXPANSAO'] += 0.5 * CICLO_PARAMS['pesos_indicadores']['inflacao']
            scores['RECUPERACAO'] += 0.3 * CICLO_PARAMS['pesos_indicadores']['inflacao']
            scores['PICO'] += 0.2 * CICLO_PARAMS['pesos_indicadores']['inflacao']
        else:
            inflacao['nivel_ipca'] = 'Baixo'
            # Inflação baixa é típica da CONTRACAO ou início da RECUPERACAO
            scores['CONTRACAO'] += 0.6 * CICLO_PARAMS['pesos_indicadores']['inflacao']
            scores['RECUPERACAO'] += 0.4 * CICLO_PARAMS['pesos_indicadores']['inflacao']
    
    # Analisa a taxa de juros
    juros = {}
    if not dados_macro['juros'].empty and 'selic_meta' in dados_macro['juros'].columns:
        # Obtém a Selic meta
        ultima_selic = dados_macro['juros']['selic_meta'].iloc[-1]
        
        # Calcula a tendência da Selic (últimos 3 meses)
        if len(dados_macro['juros']) >= 4:
            selic_atual = dados_macro['juros']['selic_meta'].iloc[-1]
            selic_3m_atras = dados_macro['juros']['selic_meta'].iloc[-4]
            tendencia_selic = selic_atual - selic_3m_atras
            
            if tendencia_selic > 0:
                juros['tendencia_selic'] = 'Alta'
                # Juros em alta são típicos da EXPANSAO ou PICO
                scores['EXPANSAO'] += 0.4 * CICLO_PARAMS['pesos_indicadores']['juros']
                scores['PICO'] += 0.6 * CICLO_PARAMS['pesos_indicadores']['juros']
            elif tendencia_selic < 0:
                juros['tendencia_selic'] = 'Queda'
                # Juros em queda são típicos da CONTRACAO ou RECUPERACAO
                scores['CONTRACAO'] += 0.6 * CICLO_PARAMS['pesos_indicadores']['juros']
                scores['RECUPERACAO'] += 0.4 * CICLO_PARAMS['pesos_indicadores']['juros']
            else:
                juros['tendencia_selic'] = 'Estável'
                # Juros estáveis podem ocorrer em qualquer fase
                scores['EXPANSAO'] += 0.3 * CICLO_PARAMS['pesos_indicadores']['juros']
                scores['PICO'] += 0.3 * CICLO_PARAMS['pesos_indicadores']['juros']
                scores['CONTRACAO'] += 0.2 * CICLO_PARAMS['pesos_indicadores']['juros']
                scores['RECUPERACAO'] += 0.2 * CICLO_PARAMS['pesos_indicadores']['juros']
        
        # Determina o nível da Selic
        if ultima_selic > 10:
            juros['nivel_selic'] = 'Alto'
            # Juros altos são típicos do PICO ou início da CONTRACAO
            scores['PICO'] += 0.7 * CICLO_PARAMS['pesos_indicadores']['juros']
            scores['CONTRACAO'] += 0.3 * CICLO_PARAMS['pesos_indicadores']['juros']
        elif ultima_selic > 6:
            juros['nivel_selic'] = 'Moderado'
            # Juros moderados podem ocorrer na EXPANSAO ou RECUPERACAO
            scores['EXPANSAO'] += 0.5 * CICLO_PARAMS['pesos_indicadores']['juros']
            scores['RECUPERACAO'] += 0.3 * CICLO_PARAMS['pesos_indicadores']['juros']
            scores['PICO'] += 0.2 * CICLO_PARAMS['pesos_indicadores']['juros']
        else:
            juros['nivel_selic'] = 'Baixo'
            # Juros baixos são típicos da CONTRACAO ou RECUPERACAO
            scores['CONTRACAO'] += 0.5 * CICLO_PARAMS['pesos_indicadores']['juros']
            scores['RECUPERACAO'] += 0.5 * CICLO_PARAMS['pesos_indicadores']['juros']
    
    # Analisa o mercado de trabalho (atividade econômica)
    atividade = {}
    if not dados_macro['trabalho'].empty and 'desemprego' in dados_macro['trabalho'].columns:
        # Obtém a taxa de desemprego
        ultimo_desemprego = dados_macro['trabalho']['desemprego'].iloc[-1]
        
        # Determina o nível de desemprego
        if ultimo_desemprego > 12:
            atividade['nivel_desemprego'] = 'Alto'
            # Desemprego alto é típico da CONTRACAO
            scores['CONTRACAO'] += 0.8 * CICLO_PARAMS['pesos_indicadores']['atividade']
            scores['RECUPERACAO'] += 0.2 * CICLO_PARAMS['pesos_indicadores']['atividade']
        elif ultimo_desemprego > 8:
            atividade['nivel_desemprego'] = 'Moderado'
            # Desemprego moderado pode ocorrer na RECUPERACAO ou EXPANSAO
            scores['RECUPERACAO'] += 0.5 * CICLO_PARAMS['pesos_indicadores']['atividade']
            scores['EXPANSAO'] += 0.3 * CICLO_PARAMS['pesos_indicadores']['atividade']
            scores['CONTRACAO'] += 0.2 * CICLO_PARAMS['pesos_indicadores']['atividade']
        else:
            atividade['nivel_desemprego'] = 'Baixo'
            # Desemprego baixo é típico da EXPANSAO ou PICO
            scores['EXPANSAO'] += 0.6 * CICLO_PARAMS['pesos_indicadores']['atividade']
            scores['PICO'] += 0.4 * CICLO_PARAMS['pesos_indicadores']['atividade']
    
    # Analisa o risco
    risco = {}
    if not dados_macro['risco'].empty:
        # Analisa o CDS
        if 'GAP12_CRDSCBR5Y' in dados_macro['risco'].columns:
            ultimo_cds = dados_macro['risco']['GAP12_CRDSCBR5Y'].iloc[-1]
            
            # Determina o nível do CDS
            if ultimo_cds > 300:
                risco['nivel_cds'] = 'Alto'
                # Risco alto é típico da CONTRACAO
                scores['CONTRACAO'] += 0.8 * CICLO_PARAMS['pesos_indicadores']['risco']
                scores['PICO'] += 0.2 * CICLO_PARAMS['pesos_indicadores']['risco']
            elif ultimo_cds > 200:
                risco['nivel_cds'] = 'Moderado'
                # Risco moderado pode ocorrer no PICO ou RECUPERACAO
                scores['PICO'] += 0.5 * CICLO_PARAMS['pesos_indicadores']['risco']
                scores['RECUPERACAO'] += 0.3 * CICLO_PARAMS['pesos_indicadores']['risco']
                scores['CONTRACAO'] += 0.2 * CICLO_PARAMS['pesos_indicadores']['risco']
            else:
                risco['nivel_cds'] = 'Baixo'
                # Risco baixo é típico da EXPANSAO ou RECUPERACAO
                scores['EXPANSAO'] += 0.6 * CICLO_PARAMS['pesos_indicadores']['risco']
                scores['RECUPERACAO'] += 0.4 * CICLO_PARAMS['pesos_indicadores']['risco']
            
            # Calcula a tendência do CDS (últimos 3 meses)
            if len(dados_macro['risco']) >= 4:
                cds_atual = dados_macro['risco']['GAP12_CRDSCBR5Y'].iloc[-1]
                cds_3m_atras = dados_macro['risco']['GAP12_CRDSCBR5Y'].iloc[-4]
                tendencia_cds = cds_atual - cds_3m_atras
                
                if tendencia_cds > 20:
                    risco['tendencia_cds'] = 'Alta'
                    # Risco em alta é típico do PICO ou CONTRACAO
                    scores['PICO'] += 0.4 * CICLO_PARAMS['pesos_indicadores']['risco']
                    scores['CONTRACAO'] += 0.6 * CICLO_PARAMS['pesos_indicadores']['risco']
                elif tendencia_cds < -20:
                    risco['tendencia_cds'] = 'Queda'
                    # Risco em queda é típico da RECUPERACAO ou EXPANSAO
                    scores['RECUPERACAO'] += 0.6 * CICLO_PARAMS['pesos_indicadores']['risco']
                    scores['EXPANSAO'] += 0.4 * CICLO_PARAMS['pesos_indicadores']['risco']
                else:
                    risco['tendencia_cds'] = 'Estável'
                    # Risco estável pode ocorrer em qualquer fase
                    scores['EXPANSAO'] += 0.25 * CICLO_PARAMS['pesos_indicadores']['risco']
                    scores['PICO'] += 0.25 * CICLO_PARAMS['pesos_indicadores']['risco']
                    scores['CONTRACAO'] += 0.25 * CICLO_PARAMS['pesos_indicadores']['risco']
                    scores['RECUPERACAO'] += 0.25 * CICLO_PARAMS['pesos_indicadores']['risco']
        
        # Analisa o EMBI+
        if 'embi' in dados_macro['risco'].columns:
            ultimo_embi = dados_macro['risco']['embi'].iloc[-1]
            
            # Determina o nível do EMBI+
            if ultimo_embi > 300:
                risco['nivel_embi'] = 'Alto'
            elif ultimo_embi > 200:
                risco['nivel_embi'] = 'Moderado'
            else:
                risco['nivel_embi'] = 'Baixo'
        
        # Analisa o IFIX
        if 'ifix' in dados_macro['risco'].columns and len(dados_macro['risco']) >= 4:
            ifix_atual = dados_macro['risco']['ifix'].iloc[-1]
            ifix_3m_atras = dados_macro['risco']['ifix'].iloc[-4]
            tendencia_ifix = ((ifix_atual / ifix_3m_atras) - 1) * 100
            
            if tendencia_ifix > 5:
                risco['tendencia_ifix'] = 'Alta'
                # IFIX em alta é típico da RECUPERACAO ou EXPANSAO
                scores['RECUPERACAO'] += 0.6 * CICLO_PARAMS['pesos_indicadores']['risco']
                scores['EXPANSAO'] += 0.4 * CICLO_PARAMS['pesos_indicadores']['risco']
            elif tendencia_ifix < -5:
                risco['tendencia_ifix'] = 'Queda'
                # IFIX em queda é típico do PICO ou CONTRACAO
                scores['PICO'] += 0.4 * CICLO_PARAMS['pesos_indicadores']['risco']
                scores['CONTRACAO'] += 0.6 * CICLO_PARAMS['pesos_indicadores']['risco']
            else:
                risco['tendencia_ifix'] = 'Estável'
    
    # Analisa o mercado de ações
    mercado = {}
    
    # Obtém o prêmio de risco
    fed_model = get_fed_model_data()
    if not fed_model.empty and 'Prêmio de Risco (%)' in fed_model.columns:
        premio_risco = fed_model['Prêmio de Risco (%)'].iloc[0]
        
        if premio_risco > 3:
            mercado['premio_risco'] = 'Alto'
            # Prêmio de risco alto é típico da CONTRACAO ou início da RECUPERACAO
            scores['CONTRACAO'] += 0.6 * CICLO_PARAMS['pesos_indicadores']['mercado']
            scores['RECUPERACAO'] += 0.4 * CICLO_PARAMS['pesos_indicadores']['mercado']
        elif premio_risco > 0:
            mercado['premio_risco'] = 'Moderado'
            # Prêmio de risco moderado pode ocorrer na RECUPERACAO ou EXPANSAO
            scores['RECUPERACAO'] += 0.5 * CICLO_PARAMS['pesos_indicadores']['mercado']
            scores['EXPANSAO'] += 0.3 * CICLO_PARAMS['pesos_indicadores']['mercado']
            scores['CONTRACAO'] += 0.2 * CICLO_PARAMS['pesos_indicadores']['mercado']
        else:
            mercado['premio_risco'] = 'Baixo/Negativo'
            # Prêmio de risco baixo ou negativo é típico da EXPANSAO ou PICO
            scores['EXPANSAO'] += 0.4 * CICLO_PARAMS['pesos_indicadores']['mercado']
            scores['PICO'] += 0.6 * CICLO_PARAMS['pesos_indicadores']['mercado']
    
    # Determina a fase do ciclo com base nos scores
    fase = max(scores, key=scores.get)
    
    # Calcula o nível de confiança
    total_score = sum(scores.values())
    confianca = (scores[fase] / total_score) * 100 if total_score > 0 else 0
    
    # Define a descrição da fase
    descricoes = {
        'EXPANSAO': "Fase de crescimento econômico sustentado, com aumento da produção, emprego e consumo. Inflação tende a acelerar e o Banco Central geralmente eleva os juros para conter pressões inflacionárias.",
        'PICO': "Fase de maturidade do ciclo, com economia operando próxima ao pleno emprego. Inflação elevada, juros altos e sinais de desaceleração começam a aparecer.",
        'CONTRACAO': "Fase de desaceleração econômica, com queda na produção, aumento do desemprego e redução do consumo. Banco Central geralmente inicia ciclo de corte de juros.",
        'RECUPERACAO': "Fase inicial de retomada econômica após período de contração. Desemprego ainda elevado mas em queda, inflação controlada e juros baixos para estimular a economia."
    }
    
    # Define a cor de alerta para cada fase
    cores_alerta = {
        'EXPANSAO': "#4CAF50",  # Verde
        'PICO': "#FFC107",      # Amarelo
        'CONTRACAO': "#F44336", # Vermelho
        'RECUPERACAO': "#2196F3" # Azul
    }
    
    # Retorna o resultado
    return {
        'fase': fase,
        'confianca': confianca,
        'descricao': descricoes[fase],
        'cor_alerta': cores_alerta[fase],
        'scores': scores,
        'detalhes': {
            'curva_juros': curva_juros,
            'inflacao': inflacao,
            'juros': juros,
            'atividade': atividade,
            'risco': risco,
            'mercado': mercado
        }
    }

def calcular_market_timing_score() -> Dict[str, Union[float, str]]:
    """
    Calcula o score de market timing com base em diversos indicadores.
    
    Returns:
        Dict: Dicionário com o score de market timing e recomendação.
    """
    # Inicializa o score
    score = 0
    
    # Obtém a fase do ciclo econômico
    ciclo = identificar_fase_ciclo()
    fase = ciclo['fase']
    
    # Componente do ciclo econômico
    if fase == 'EXPANSAO':
        score += 50 * TIMING_PARAMS['pesos_indicadores']['ciclo']
    elif fase == 'PICO':
        score -= 50 * TIMING_PARAMS['pesos_indicadores']['ciclo']
    elif fase == 'CONTRACAO':
        score -= 100 * TIMING_PARAMS['pesos_indicadores']['ciclo']
    elif fase == 'RECUPERACAO':
        score += 100 * TIMING_PARAMS['pesos_indicadores']['ciclo']
    
    # Componente de valuation
    fed_model = get_fed_model_data()
    if not fed_model.empty and 'Prêmio de Risco (%)' in fed_model.columns:
        premio_risco = fed_model['Prêmio de Risco (%)'].iloc[0]
        
        # Ajusta o score com base no prêmio de risco
        if premio_risco > 5:
            score += 100 * TIMING_PARAMS['pesos_indicadores']['valuation']
        elif premio_risco > 3:
            score += 75 * TIMING_PARAMS['pesos_indicadores']['valuation']
        elif premio_risco > 1:
            score += 50 * TIMING_PARAMS['pesos_indicadores']['valuation']
        elif premio_risco > -1:
            score += 0 * TIMING_PARAMS['pesos_indicadores']['valuation']
        elif premio_risco > -3:
            score -= 50 * TIMING_PARAMS['pesos_indicadores']['valuation']
        else:
            score -= 100 * TIMING_PARAMS['pesos_indicadores']['valuation']
    
    # Componente de momentum
    # Simula um indicador de momentum do mercado
    momentum = np.random.uniform(-100, 100)
    score += momentum * TIMING_PARAMS['pesos_indicadores']['momentum']
    
    # Componente de risco
    dados_macro = get_all_macro_data()
    if not dados_macro['risco'].empty and 'GAP12_CRDSCBR5Y' in dados_macro['risco'].columns:
        ultimo_cds = dados_macro['risco']['GAP12_CRDSCBR5Y'].iloc[-1]
        
        # Ajusta o score com base no CDS
        if ultimo_cds > 300:
            score -= 100 * TIMING_PARAMS['pesos_indicadores']['risco']
        elif ultimo_cds > 250:
            score -= 75 * TIMING_PARAMS['pesos_indicadores']['risco']
        elif ultimo_cds > 200:
            score -= 50 * TIMING_PARAMS['pesos_indicadores']['risco']
        elif ultimo_cds > 150:
            score -= 25 * TIMING_PARAMS['pesos_indicadores']['risco']
        elif ultimo_cds > 100:
            score += 0 * TIMING_PARAMS['pesos_indicadores']['risco']
        else:
            score += 50 * TIMING_PARAMS['pesos_indicadores']['risco']
    
    # Componente de liquidez
    if not dados_macro['juros'].empty and 'selic_meta' in dados_macro['juros'].columns:
        ultima_selic = dados_macro['juros']['selic_meta'].iloc[-1]
        
        # Ajusta o score com base na Selic
        if ultima_selic > 12:
            score -= 100 * TIMING_PARAMS['pesos_indicadores']['liquidez']
        elif ultima_selic > 10:
            score -= 75 * TIMING_PARAMS['pesos_indicadores']['liquidez']
        elif ultima_selic > 8:
            score -= 50 * TIMING_PARAMS['pesos_indicadores']['liquidez']
        elif ultima_selic > 6:
            score -= 25 * TIMING_PARAMS['pesos_indicadores']['liquidez']
        elif ultima_selic > 4:
            score += 0 * TIMING_PARAMS['pesos_indicadores']['liquidez']
        else:
            score += 50 * TIMING_PARAMS['pesos_indicadores']['liquidez']
    
    # Limita o score entre -100 e 100
    score = max(-100, min(100, score))
    
    # Determina a recomendação com base no score
    if score <= TIMING_PARAMS['limites_score']['muito_negativo']:
        recomendacao = "VENDA"
        cor = "#F44336"  # Vermelho
    elif score <= TIMING_PARAMS['limites_score']['negativo']:
        recomendacao = "REDUÇÃO"
        cor = "#FF9800"  # Laranja
    elif score <= TIMING_PARAMS['limites_score']['neutro']:
        recomendacao = "NEUTRO"
        cor = "#FFC107"  # Amarelo
    elif score <= TIMING_PARAMS['limites_score']['positivo']:
        recomendacao = "AUMENTO"
        cor = "#8BC34A"  # Verde claro
    else:
        recomendacao = "COMPRA"
        cor = "#4CAF50"  # Verde
    
    # Retorna o resultado
    return {
        'score': score,
        'recomendacao': recomendacao,
        'cor': cor
    }

def gerar_alertas_market_timing() -> List[Dict[str, str]]:
    """
    Gera alertas de market timing com base na análise do ciclo econômico e indicadores de mercado.
    
    Returns:
        List[Dict]: Lista de alertas de market timing.
    """
    # Inicializa a lista de alertas
    alertas = []
    
    # Obtém a fase do ciclo econômico
    ciclo = identificar_fase_ciclo()
    fase = ciclo['fase']
    
    # Obtém o score de market timing
    timing = calcular_market_timing_score()
    score = timing['score']
    
    # Alerta com base na fase do ciclo
    if fase == 'EXPANSAO':
        alertas.append({
            'tipo': 'Ciclo Econômico',
            'mensagem': 'Economia em fase de expansão. Setores cíclicos tendem a se beneficiar.',
            'importancia': 'Alta',
            'cor': '#4CAF50'  # Verde
        })
    elif fase == 'PICO':
        alertas.append({
            'tipo': 'Ciclo Econômico',
            'mensagem': 'Economia próxima ao pico do ciclo. Considere reduzir exposição a setores cíclicos.',
            'importancia': 'Alta',
            'cor': '#FFC107'  # Amarelo
        })
    elif fase == 'CONTRACAO':
        alertas.append({
            'tipo': 'Ciclo Econômico',
            'mensagem': 'Economia em fase de contração. Setores defensivos tendem a se beneficiar.',
            'importancia': 'Alta',
            'cor': '#F44336'  # Vermelho
        })
    elif fase == 'RECUPERACAO':
        alertas.append({
            'tipo': 'Ciclo Econômico',
            'mensagem': 'Economia em fase de recuperação. Setores cíclicos e de valor tendem a se beneficiar.',
            'importancia': 'Alta',
            'cor': '#2196F3'  # Azul
        })
    
    # Alerta com base no score de market timing
    if score <= TIMING_PARAMS['limites_score']['muito_negativo']:
        alertas.append({
            'tipo': 'Market Timing',
            'mensagem': 'Indicadores sugerem momento muito desfavorável para o mercado.',
            'importancia': 'Alta',
            'cor': '#F44336'  # Vermelho
        })
    elif score <= TIMING_PARAMS['limites_score']['negativo']:
        alertas.append({
            'tipo': 'Market Timing',
            'mensagem': 'Indicadores sugerem momento desfavorável para o mercado.',
            'importancia': 'Média',
            'cor': '#FF9800'  # Laranja
        })
    elif score >= TIMING_PARAMS['limites_score']['muito_positivo']:
        alertas.append({
            'tipo': 'Market Timing',
            'mensagem': 'Indicadores sugerem momento muito favorável para o mercado.',
            'importancia': 'Alta',
            'cor': '#4CAF50'  # Verde
        })
    elif score >= TIMING_PARAMS['limites_score']['positivo']:
        alertas.append({
            'tipo': 'Market Timing',
            'mensagem': 'Indicadores sugerem momento favorável para o mercado.',
            'importancia': 'Média',
            'cor': '#8BC34A'  # Verde claro
        })
    
    # Alerta com base na curva de juros
    if 'detalhes' in ciclo and 'curva_juros' in ciclo['detalhes'] and 'status_curva' in ciclo['detalhes']['curva_juros']:
        status_curva = ciclo['detalhes']['curva_juros']['status_curva']
        
        if status_curva == 'Invertida':
            alertas.append({
                'tipo': 'Curva de Juros',
                'mensagem': 'Curva de juros invertida. Historicamente, sinal de alerta para recessão nos próximos 12-18 meses.',
                'importancia': 'Alta',
                'cor': '#F44336'  # Vermelho
            })
        elif status_curva == 'Achatada':
            alertas.append({
                'tipo': 'Curva de Juros',
                'mensagem': 'Curva de juros achatada. Possível sinal de desaceleração econômica.',
                'importancia': 'Média',
                'cor': '#FFC107'  # Amarelo
            })
    
    # Alerta com base no prêmio de risco
    fed_model = get_fed_model_data()
    if not fed_model.empty and 'Prêmio de Risco (%)' in fed_model.columns:
        premio_risco = fed_model['Prêmio de Risco (%)'].iloc[0]
        
        if premio_risco > 5:
            alertas.append({
                'tipo': 'Valuation',
                'mensagem': f'Prêmio de risco elevado ({premio_risco:.1f}%). Ações podem estar subvalorizadas em relação aos títulos.',
                'importancia': 'Alta',
                'cor': '#4CAF50'  # Verde
            })
        elif premio_risco < -3:
            alertas.append({
                'tipo': 'Valuation',
                'mensagem': f'Prêmio de risco negativo ({premio_risco:.1f}%). Ações podem estar sobrevalorizadas em relação aos títulos.',
                'importancia': 'Alta',
                'cor': '#F44336'  # Vermelho
            })
    
    # Alerta com base na classificação setorial
    classificacao = classificar_valuation_setorial()
    if not classificacao.empty:
        setores_baratos = classificacao[classificacao['Classificação'] == 'Muito Barato'].index.tolist()
        setores_caros = classificacao[classificacao['Classificação'] == 'Muito Caro'].index.tolist()
        
        if setores_baratos:
            alertas.append({
                'tipo': 'Valuation Setorial',
                'mensagem': f'Setores potencialmente subvalorizados: {", ".join(setores_baratos)}.',
                'importancia': 'Média',
                'cor': '#4CAF50'  # Verde
            })
        
        if setores_caros:
            alertas.append({
                'tipo': 'Valuation Setorial',
                'mensagem': f'Setores potencialmente sobrevalorizados: {", ".join(setores_caros)}.',
                'importancia': 'Média',
                'cor': '#F44336'  # Vermelho
            })
    
    # Alerta com base na inflação
    dados_macro = get_all_macro_data()
    if not dados_macro['inflacao'].empty and 'ipca_acumulado_12m' in dados_macro['inflacao'].columns:
        ultimo_ipca = dados_macro['inflacao']['ipca_acumulado_12m'].iloc[-1]
        
        if ultimo_ipca > 8:
            alertas.append({
                'tipo': 'Inflação',
                'mensagem': f'Inflação elevada ({ultimo_ipca:.1f}%). Pode pressionar margens das empresas e levar a aumento de juros.',
                'importancia': 'Alta',
                'cor': '#F44336'  # Vermelho
            })
        elif ultimo_ipca < 3:
            alertas.append({
                'tipo': 'Inflação',
                'mensagem': f'Inflação baixa ({ultimo_ipca:.1f}%). Pode indicar fraqueza na demanda ou abrir espaço para corte de juros.',
                'importancia': 'Média',
                'cor': '#FFC107'  # Amarelo
            })
    
    return alertas
