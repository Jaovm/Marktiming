"""
Módulo para visualização de dados de mercado.

Este módulo contém funções para criar gráficos e visualizações
dos indicadores de mercado, como índices, setores e múltiplos de valuation.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Union

def criar_dashboard_mercado(dados_mercado: Dict) -> Dict[str, go.Figure]:
    """
    Cria um dashboard com gráficos dos principais indicadores de mercado.
    
    Args:
        dados_mercado: Dicionário com dados de mercado.
        
    Returns:
        Dict[str, go.Figure]: Dicionário com os gráficos do dashboard.
    """
    # Inicializa o dicionário de gráficos
    graficos = {}
    
    # Gráfico dos índices
    if 'indices' in dados_mercado and not dados_mercado['indices'].empty:
        fig_indices = go.Figure()
        
        # Para cada índice
        for ticker, nome in {
            "^BVSP": "Ibovespa",
            "^IBX": "IBrX",
            "^IDIV": "IDIV",
            "^SMLL": "Small Caps",
            "^IFIX": "IFIX"
        }.items():
            if ticker in dados_mercado['indices'].columns.levels[0]:
                # Normaliza os preços para base 100
                precos = dados_mercado['indices'][ticker]['Close']
                precos_norm = (precos / precos.iloc[0]) * 100
                
                # Adiciona a série ao gráfico
                fig_indices.add_trace(
                    go.Scatter(
                        x=precos.index,
                        y=precos_norm,
                        name=nome,
                        mode='lines'
                    )
                )
        
        # Configura os eixos
        fig_indices.update_layout(
            title="Evolução dos Principais Índices (Base 100)",
            xaxis_title="Data",
            yaxis_title="Índice (Base 100)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        # Adiciona o gráfico ao dicionário
        graficos['indices'] = fig_indices
    
    # Gráfico dos setores
    if 'setores' in dados_mercado:
        # Cria um DataFrame para armazenar o desempenho dos setores
        df_setores = pd.DataFrame(columns=['Setor', 'Retorno 1M (%)', 'Retorno 3M (%)', 'Retorno 6M (%)', 'Retorno 1A (%)'])
        
        # Para cada setor
        for setor, dados in dados_mercado['setores'].items():
            if not dados.empty:
                # Calcula o retorno médio das ações do setor
                retornos = {}
                
                for ticker in dados.columns.levels[0]:
                    if 'Close' in dados[ticker].columns:
                        precos = dados[ticker]['Close']
                        
                        # Calcula os retornos
                        if len(precos) > 21:  # 1 mês (21 dias úteis)
                            retornos[ticker] = {
                                '1M': ((precos.iloc[-1] / precos.iloc[-21]) - 1) * 100
                            }
                        
                        if len(precos) > 63:  # 3 meses (63 dias úteis)
                            retornos[ticker]['3M'] = ((precos.iloc[-1] / precos.iloc[-63]) - 1) * 100
                        
                        if len(precos) > 126:  # 6 meses (126 dias úteis)
                            retornos[ticker]['6M'] = ((precos.iloc[-1] / precos.iloc[-126]) - 1) * 100
                        
                        if len(precos) > 252:  # 1 ano (252 dias úteis)
                            retornos[ticker]['1A'] = ((precos.iloc[-1] / precos.iloc[-252]) - 1) * 100
                
                # Calcula a média dos retornos do setor
                if retornos:
                    retorno_1m = np.mean([r.get('1M', np.nan) for r in retornos.values() if '1M' in r])
                    retorno_3m = np.mean([r.get('3M', np.nan) for r in retornos.values() if '3M' in r])
                    retorno_6m = np.mean([r.get('6M', np.nan) for r in retornos.values() if '6M' in r])
                    retorno_1a = np.mean([r.get('1A', np.nan) for r in retornos.values() if '1A' in r])
                    
                    # Adiciona ao DataFrame
                    df_setores.loc[len(df_setores)] = [setor, retorno_1m, retorno_3m, retorno_6m, retorno_1a]
        
        # Cria o gráfico de barras dos retornos setoriais
        if not df_setores.empty:
            # Gráfico de retorno de 1 mês
            fig_setores_1m = px.bar(
                df_setores.sort_values('Retorno 1M (%)'),
                x='Setor',
                y='Retorno 1M (%)',
                color='Retorno 1M (%)',
                color_continuous_scale=['#F44336', '#FFFFFF', '#4CAF50'],
                color_continuous_midpoint=0,
                title="Retorno Setorial - 1 Mês"
            )
            
            # Gráfico de retorno de 1 ano
            fig_setores_1a = px.bar(
                df_setores.sort_values('Retorno 1A (%)'),
                x='Setor',
                y='Retorno 1A (%)',
                color='Retorno 1A (%)',
                color_continuous_scale=['#F44336', '#FFFFFF', '#4CAF50'],
                color_continuous_midpoint=0,
                title="Retorno Setorial - 1 Ano"
            )
            
            # Combina os gráficos
            fig_setores = make_subplots(rows=2, cols=1, subplot_titles=("Retorno Setorial - 1 Mês", "Retorno Setorial - 1 Ano"))
            
            # Adiciona os traces do primeiro gráfico
            for trace in fig_setores_1m.data:
                fig_setores.add_trace(trace, row=1, col=1)
            
            # Adiciona os traces do segundo gráfico
            for trace in fig_setores_1a.data:
                fig_setores.add_trace(trace, row=2, col=1)
            
            # Configura o layout
            fig_setores.update_layout(
                height=800,
                showlegend=False
            )
            
            # Adiciona o gráfico ao dicionário
            graficos['setores'] = fig_setores
    
    # Gráfico de valuation setorial
    if 'valuation_setorial' in dados_mercado and not dados_mercado['valuation_setorial'].empty:
        # Cria um gráfico para cada múltiplo
        fig_valuation = make_subplots(
            rows=2, cols=2,
            subplot_titles=("P/L por Setor", "P/VP por Setor", "EV/EBITDA por Setor", "Dividend Yield por Setor"),
            vertical_spacing=0.1
        )
        
        # P/L
        if 'P/L' in dados_mercado['valuation_setorial'].columns:
            df_pl = dados_mercado['valuation_setorial'].sort_values('P/L')
            fig_valuation.add_trace(
                go.Bar(
                    x=df_pl.index,
                    y=df_pl['P/L'],
                    name="P/L",
                    marker_color="#1E88E5"
                ),
                row=1, col=1
            )
        
        # P/VP
        if 'P/VP' in dados_mercado['valuation_setorial'].columns:
            df_pvp = dados_mercado['valuation_setorial'].sort_values('P/VP')
            fig_valuation.add_trace(
                go.Bar(
                    x=df_pvp.index,
                    y=df_pvp['P/VP'],
                    name="P/VP",
                    marker_color="#4CAF50"
                ),
                row=1, col=2
            )
        
        # EV/EBITDA
        if 'EV/EBITDA' in dados_mercado['valuation_setorial'].columns:
            df_ev_ebitda = dados_mercado['valuation_setorial'].sort_values('EV/EBITDA')
            fig_valuation.add_trace(
                go.Bar(
                    x=df_ev_ebitda.index,
                    y=df_ev_ebitda['EV/EBITDA'],
                    name="EV/EBITDA",
                    marker_color="#FFC107"
                ),
                row=2, col=1
            )
        
        # Dividend Yield
        if 'Dividend Yield (%)' in dados_mercado['valuation_setorial'].columns:
            df_dy = dados_mercado['valuation_setorial'].sort_values('Dividend Yield (%)', ascending=False)
            fig_valuation.add_trace(
                go.Bar(
                    x=df_dy.index,
                    y=df_dy['Dividend Yield (%)'],
                    name="Dividend Yield (%)",
                    marker_color="#F44336"
                ),
                row=2, col=2
            )
        
        # Configura o layout
        fig_valuation.update_layout(
            height=800,
            showlegend=False,
            title_text="Múltiplos de Valuation por Setor"
        )
        
        # Adiciona o gráfico ao dicionário
        graficos['valuation_setorial'] = fig_valuation
    
    # Gráfico de comparação com médias históricas
    if 'comparacao_valuation' in dados_mercado and not dados_mercado['comparacao_valuation'].empty:
        # Cria um gráfico para cada múltiplo
        fig_comparacao = make_subplots(
            rows=1, cols=2,
            subplot_titles=("P/L vs Média Histórica", "P/VP vs Média Histórica"),
            specs=[[{"type": "bar"}, {"type": "bar"}]]
        )
        
        # P/L
        if 'P/L (Atual)' in dados_mercado['comparacao_valuation'].columns and 'P/L (Média 5a)' in dados_mercado['comparacao_valuation'].columns:
            df_pl = dados_mercado['comparacao_valuation'].sort_values('P/L (% vs Média)')
            
            fig_comparacao.add_trace(
                go.Bar(
                    x=df_pl.index,
                    y=df_pl['P/L (Atual)'],
                    name="P/L Atual",
                    marker_color="#1E88E5"
                ),
                row=1, col=1
            )
            
            fig_comparacao.add_trace(
                go.Bar(
                    x=df_pl.index,
                    y=df_pl['P/L (Média 5a)'],
                    name="P/L Média 5 anos",
                    marker_color="#90CAF9"
                ),
                row=1, col=1
            )
        
        # P/VP
        if 'P/VP (Atual)' in dados_mercado['comparacao_valuation'].columns and 'P/VP (Média 5a)' in dados_mercado['comparacao_valuation'].columns:
            df_pvp = dados_mercado['comparacao_valuation'].sort_values('P/VP (% vs Média)')
            
            fig_comparacao.add_trace(
                go.Bar(
                    x=df_pvp.index,
                    y=df_pvp['P/VP (Atual)'],
                    name="P/VP Atual",
                    marker_color="#4CAF50"
                ),
                row=1, col=2
            )
            
            fig_comparacao.add_trace(
                go.Bar(
                    x=df_pvp.index,
                    y=df_pvp['P/VP (Média 5a)'],
                    name="P/VP Média 5 anos",
                    marker_color="#A5D6A7"
                ),
                row=1, col=2
            )
        
        # Configura o layout
        fig_comparacao.update_layout(
            height=500,
            barmode='group',
            title_text="Comparação com Médias Históricas"
        )
        
        # Adiciona o gráfico ao dicionário
        graficos['comparacao_valuation'] = fig_comparacao
    
    # Gráfico do Fed Model
    if 'premio_risco' in dados_mercado and not dados_mercado['premio_risco'].empty:
        fig_fed_model = go.Figure()
        
        # Adiciona o Earnings Yield
        if 'Earnings Yield (%)' in dados_mercado['premio_risco'].columns:
            fig_fed_model.add_trace(
                go.Bar(
                    x=["Earnings Yield"],
                    y=[dados_mercado['premio_risco']['Earnings Yield (%)'].iloc[0]],
                    name="Earnings Yield (%)",
                    marker_color="#4CAF50"
                )
            )
        
        # Adiciona a Taxa de Juros de Longo Prazo
        if 'Taxa de Juros Longo Prazo (%)' in dados_mercado['premio_risco'].columns:
            fig_fed_model.add_trace(
                go.Bar(
                    x=["Taxa de Juros LP"],
                    y=[dados_mercado['premio_risco']['Taxa de Juros Longo Prazo (%)'].iloc[0]],
                    name="Taxa de Juros Longo Prazo (%)",
                    marker_color="#F44336"
                )
            )
        
        # Adiciona o Prêmio de Risco
        if 'Prêmio de Risco (%)' in dados_mercado['premio_risco'].columns:
            premio = dados_mercado['premio_risco']['Prêmio de Risco (%)'].iloc[0]
            cor = "#4CAF50" if premio > 0 else "#F44336"
            
            fig_fed_model.add_trace(
                go.Bar(
                    x=["Prêmio de Risco"],
                    y=[premio],
                    name="Prêmio de Risco (%)",
                    marker_color=cor
                )
            )
        
        # Adiciona a interpretação
        if 'Interpretação' in dados_mercado['premio_risco'].columns:
            interpretacao = dados_mercado['premio_risco']['Interpretação'].iloc[0]
            
            fig_fed_model.add_annotation(
                x=0.5,
                y=1.15,
                xref="paper",
                yref="paper",
                text=f"Interpretação: {interpretacao}",
                showarrow=False,
                font=dict(size=14)
            )
        
        # Configura o layout
        fig_fed_model.update_layout(
            title="Fed Model Adaptado para Brasil",
            xaxis_title="",
            yaxis_title="Percentual (%)"
        )
        
        # Adiciona o gráfico ao dicionário
        graficos['premio_risco'] = fig_fed_model
    
    # Gráfico de classificação setorial
    if 'classificacao_setorial' in dados_mercado and not dados_mercado['classificacao_setorial'].empty:
        # Cria um DataFrame para o gráfico
        df_class = dados_mercado['classificacao_setorial'].copy()
        
        # Mapeia as classificações para valores numéricos
        mapa_class = {
            'Muito Caro': 1,
            'Caro': 2,
            'Neutro': 3,
            'Barato': 4,
            'Muito Barato': 5
        }
        
        # Mapeia as classificações para cores
        mapa_cores = {
            'Muito Caro': '#F44336',
            'Caro': '#FF9800',
            'Neutro': '#FFC107',
            'Barato': '#8BC34A',
            'Muito Barato': '#4CAF50'
        }
        
        if 'Classificação' in df_class.columns:
            # Cria o gráfico
            fig_class = go.Figure()
            
            # Adiciona as barras
            for i, (setor, row) in enumerate(df_class.iterrows()):
                if 'Score Total' in row and 'Classificação' in row:
                    fig_class.add_trace(
                        go.Bar(
                            x=[setor],
                            y=[row['Score Total']],
                            name=setor,
                            marker_color=mapa_cores.get(row['Classificação'], '#CCCCCC')
                        )
                    )
            
            # Configura o layout
            fig_class.update_layout(
                title="Classificação de Valuation dos Setores",
                xaxis_title="",
                yaxis_title="Score de Valuation",
                showlegend=False
            )
            
            # Adiciona o gráfico ao dicionário
            graficos['classificacao_setorial'] = fig_class
    
    # Gráfico da carteira
    if 'carteira' in dados_mercado and not dados_mercado['carteira'].empty:
        # Cria um gráfico para a evolução da carteira
        fig_carteira = go.Figure()
        
        # Para cada ação da carteira
        for ticker in dados_mercado['carteira'].columns.levels[0]:
            if 'Close' in dados_mercado['carteira'][ticker].columns:
                # Normaliza os preços para base 100
                precos = dados_mercado['carteira'][ticker]['Close']
                precos_norm = (precos / precos.iloc[0]) * 100
                
                # Adiciona a série ao gráfico
                fig_carteira.add_trace(
                    go.Scatter(
                        x=precos.index,
                        y=precos_norm,
                        name=ticker,
                        mode='lines'
                    )
                )
        
        # Adiciona o Ibovespa como referência
        if 'indices' in dados_mercado and not dados_mercado['indices'].empty and '^BVSP' in dados_mercado['indices'].columns.levels[0]:
            precos_ibov = dados_mercado['indices']['^BVSP']['Close']
            precos_ibov_norm = (precos_ibov / precos_ibov.iloc[0]) * 100
            
            fig_carteira.add_trace(
                go.Scatter(
                    x=precos_ibov.index,
                    y=precos_ibov_norm,
                    name="Ibovespa",
                    mode='lines',
                    line=dict(color='black', width=3, dash='dash')
                )
            )
        
        # Configura os eixos
        fig_carteira.update_layout(
            title="Evolução da Carteira vs Ibovespa (Base 100)",
            xaxis_title="Data",
            yaxis_title="Índice (Base 100)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        # Adiciona o gráfico ao dicionário
        graficos['carteira'] = fig_carteira
    
    # Gráfico de análise da carteira
    if 'analise_carteira' in dados_mercado and not dados_mercado['analise_carteira'].empty:
        # Cria um gráfico para os múltiplos da carteira
        fig_analise = go.Figure()
        
        # Filtra apenas as ações (remove a média da carteira)
        df_analise = dados_mercado['analise_carteira'].copy()
        df_analise = df_analise.drop('MÉDIA CARTEIRA', errors='ignore')
        
        # Adiciona o P/L
        if 'P/L' in df_analise.columns:
            fig_analise.add_trace(
                go.Bar(
                    x=df_analise.index,
                    y=df_analise['P/L'],
                    name="P/L",
                    marker_color="#1E88E5"
                )
            )
        
        # Configura os eixos
        fig_analise.update_layout(
            title="P/L das Ações da Carteira",
            xaxis_title="Ação",
            yaxis_title="P/L",
            showlegend=False
        )
        
        # Adiciona o gráfico ao dicionário
        graficos['analise_carteira'] = fig_analise
    
    return graficos

def criar_tabela_resumo_mercado(resumo_mercado: pd.DataFrame) -> go.Figure:
    """
    Cria uma tabela com o resumo dos principais indicadores de mercado.
    
    Args:
        resumo_mercado: DataFrame com o resumo dos indicadores.
        
    Returns:
        go.Figure: Figura com a tabela de resumo.
    """
    # Cria a tabela
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=['Indicador', 'Valor', 'Data'],
            fill_color='#1E88E5',
            align='left',
            font=dict(color='white', size=12)
        ),
        cells=dict(
            values=[
                resumo_mercado.index,
                resumo_mercado['Valor'].apply(lambda x: f"{x:.2f}" if isinstance(x, (int, float)) else x),
                resumo_mercado['Data']
            ],
            fill_color='lavender',
            align='left'
        )
    )])
    
    # Configura o layout
    fig.update_layout(
        title="Resumo dos Indicadores de Mercado",
        height=400
    )
    
    return fig
