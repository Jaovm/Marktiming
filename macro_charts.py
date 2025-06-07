"""
Módulo para visualização de dados macroeconômicos.

Este módulo contém funções para criar gráficos e visualizações
dos indicadores macroeconômicos do Brasil.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Union

def criar_dashboard_macro(dados_macro: Dict[str, pd.DataFrame]) -> Dict[str, go.Figure]:
    """
    Cria um dashboard com gráficos dos principais indicadores macroeconômicos.
    
    Args:
        dados_macro: Dicionário com DataFrames dos dados macroeconômicos.
        
    Returns:
        Dict[str, go.Figure]: Dicionário com os gráficos do dashboard.
    """
    # Inicializa o dicionário de gráficos
    graficos = {}
    
    # Gráfico do PIB
    if 'pib' in dados_macro and not dados_macro['pib'].empty:
        fig_pib = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Adiciona o valor do PIB
        if 'pib_valor' in dados_macro['pib'].columns:
            fig_pib.add_trace(
                go.Scatter(
                    x=dados_macro['pib'].index,
                    y=dados_macro['pib']['pib_valor'],
                    name="PIB (R$ milhões)",
                    line=dict(color="#1E88E5", width=2)
                ),
                secondary_y=False
            )
        
        # Adiciona a variação do PIB
        if 'pib_variacao' in dados_macro['pib'].columns:
            fig_pib.add_trace(
                go.Scatter(
                    x=dados_macro['pib'].index,
                    y=dados_macro['pib']['pib_variacao'],
                    name="Variação Anual (%)",
                    line=dict(color="#4CAF50", width=2, dash='dash')
                ),
                secondary_y=True
            )
        
        # Configura os eixos
        fig_pib.update_layout(
            title="PIB - Produto Interno Bruto",
            xaxis_title="Data",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig_pib.update_yaxes(title_text="PIB (R$ milhões)", secondary_y=False)
        fig_pib.update_yaxes(title_text="Variação Anual (%)", secondary_y=True)
        
        # Adiciona o gráfico ao dicionário
        graficos['pib'] = fig_pib
    
    # Gráfico da inflação
    if 'inflacao' in dados_macro and not dados_macro['inflacao'].empty:
        fig_inflacao = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Adiciona o IPCA acumulado em 12 meses
        if 'ipca_acumulado_12m' in dados_macro['inflacao'].columns:
            fig_inflacao.add_trace(
                go.Scatter(
                    x=dados_macro['inflacao'].index,
                    y=dados_macro['inflacao']['ipca_acumulado_12m'],
                    name="IPCA (12 meses)",
                    line=dict(color="#1E88E5", width=2)
                ),
                secondary_y=False
            )
        
        # Adiciona o IGP-M acumulado em 12 meses
        if 'igpm_acumulado_12m' in dados_macro['inflacao'].columns:
            fig_inflacao.add_trace(
                go.Scatter(
                    x=dados_macro['inflacao'].index,
                    y=dados_macro['inflacao']['igpm_acumulado_12m'],
                    name="IGP-M (12 meses)",
                    line=dict(color="#F44336", width=2)
                ),
                secondary_y=False
            )
        
        # Adiciona o IPCA mensal
        if 'ipca_mensal' in dados_macro['inflacao'].columns:
            fig_inflacao.add_trace(
                go.Bar(
                    x=dados_macro['inflacao'].index,
                    y=dados_macro['inflacao']['ipca_mensal'],
                    name="IPCA Mensal",
                    marker_color="#2196F3",
                    opacity=0.5
                ),
                secondary_y=True
            )
        
        # Configura os eixos
        fig_inflacao.update_layout(
            title="Inflação - IPCA e IGP-M",
            xaxis_title="Data",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig_inflacao.update_yaxes(title_text="Acumulado 12 meses (%)", secondary_y=False)
        fig_inflacao.update_yaxes(title_text="Mensal (%)", secondary_y=True)
        
        # Adiciona o gráfico ao dicionário
        graficos['inflacao'] = fig_inflacao
    
    # Gráfico da taxa de juros
    if 'juros' in dados_macro and not dados_macro['juros'].empty:
        fig_juros = go.Figure()
        
        # Adiciona a Selic meta
        if 'selic_meta' in dados_macro['juros'].columns:
            fig_juros.add_trace(
                go.Scatter(
                    x=dados_macro['juros'].index,
                    y=dados_macro['juros']['selic_meta'],
                    name="Selic Meta",
                    line=dict(color="#1E88E5", width=2)
                )
            )
        
        # Adiciona a Selic diária
        if 'selic_diaria' in dados_macro['juros'].columns:
            fig_juros.add_trace(
                go.Scatter(
                    x=dados_macro['juros'].index,
                    y=dados_macro['juros']['selic_diaria'],
                    name="Selic Diária",
                    line=dict(color="#4CAF50", width=1, dash='dot')
                )
            )
        
        # Configura os eixos
        fig_juros.update_layout(
            title="Taxa de Juros - Selic",
            xaxis_title="Data",
            yaxis_title="Taxa (% a.a.)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        # Adiciona o gráfico ao dicionário
        graficos['juros'] = fig_juros
    
    # Gráfico da curva de juros
    if 'curva_juros' in dados_macro and not dados_macro['curva_juros'].empty:
        # Obtém a data mais recente
        data_recente = dados_macro['curva_juros'].index.max()
        
        # Obtém os dados da curva de juros mais recente
        curva_recente = dados_macro['curva_juros'].loc[data_recente]
        
        # Cria um DataFrame com os prazos e taxas
        prazos = {
            'di_30d': 1,
            'di_90d': 3,
            'di_180d': 6,
            'di_360d': 12,
            'di_720d': 24,
            'di_1080d': 36
        }
        
        df_curva = pd.DataFrame(columns=['Prazo (meses)', 'Taxa (% a.a.)'])
        
        for coluna, prazo in prazos.items():
            if coluna in dados_macro['curva_juros'].columns:
                df_curva = pd.concat([df_curva, pd.DataFrame({
                    'Prazo (meses)': [prazo],
                    'Taxa (% a.a.)': [curva_recente[coluna]]
                })])
        
        # Ordena o DataFrame pelo prazo
        df_curva = df_curva.sort_values('Prazo (meses)')
        
        # Cria o gráfico da curva de juros
        fig_curva = go.Figure()
        
        fig_curva.add_trace(
            go.Scatter(
                x=df_curva['Prazo (meses)'],
                y=df_curva['Taxa (% a.a.)'],
                mode='lines+markers',
                name="Curva de Juros",
                line=dict(color="#1E88E5", width=2),
                marker=dict(size=8)
            )
        )
        
        # Configura os eixos
        fig_curva.update_layout(
            title=f"Curva de Juros - {data_recente.strftime('%d/%m/%Y')}",
            xaxis_title="Prazo (meses)",
            yaxis_title="Taxa (% a.a.)",
            xaxis=dict(
                tickmode='array',
                tickvals=list(prazos.values())
            )
        )
        
        # Adiciona o gráfico ao dicionário
        graficos['curva_juros'] = fig_curva
    
    # Gráfico do mercado de trabalho
    if 'trabalho' in dados_macro and not dados_macro['trabalho'].empty:
        fig_trabalho = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Adiciona a taxa de desemprego
        if 'desemprego' in dados_macro['trabalho'].columns:
            fig_trabalho.add_trace(
                go.Scatter(
                    x=dados_macro['trabalho'].index,
                    y=dados_macro['trabalho']['desemprego'],
                    name="Taxa de Desemprego",
                    line=dict(color="#F44336", width=2)
                ),
                secondary_y=False
            )
        
        # Adiciona o saldo do CAGED
        if 'caged_saldo' in dados_macro['trabalho'].columns:
            fig_trabalho.add_trace(
                go.Bar(
                    x=dados_macro['trabalho'].index,
                    y=dados_macro['trabalho']['caged_saldo'],
                    name="Saldo de Empregos (CAGED)",
                    marker_color="#4CAF50"
                ),
                secondary_y=True
            )
        
        # Configura os eixos
        fig_trabalho.update_layout(
            title="Mercado de Trabalho",
            xaxis_title="Data",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig_trabalho.update_yaxes(title_text="Taxa de Desemprego (%)", secondary_y=False)
        fig_trabalho.update_yaxes(title_text="Saldo de Empregos", secondary_y=True)
        
        # Adiciona o gráfico ao dicionário
        graficos['trabalho'] = fig_trabalho
    
    # Gráfico de liquidez
    if 'liquidez' in dados_macro and not dados_macro['liquidez'].empty:
        fig_liquidez = go.Figure()
        
        # Adiciona os agregados monetários
        for coluna, nome, cor in [
            ('m1', 'M1', "#1E88E5"),
            ('m2', 'M2', "#4CAF50"),
            ('m3', 'M3', "#FFC107"),
            ('m4', 'M4', "#F44336")
        ]:
            if coluna in dados_macro['liquidez'].columns:
                fig_liquidez.add_trace(
                    go.Scatter(
                        x=dados_macro['liquidez'].index,
                        y=dados_macro['liquidez'][coluna],
                        name=nome,
                        line=dict(color=cor, width=2)
                    )
                )
        
        # Configura os eixos
        fig_liquidez.update_layout(
            title="Agregados Monetários",
            xaxis_title="Data",
            yaxis_title="Valor (R$ milhões)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        # Adiciona o gráfico ao dicionário
        graficos['liquidez'] = fig_liquidez
    
    # Gráfico de risco
    if 'risco' in dados_macro and not dados_macro['risco'].empty:
        fig_risco = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Adiciona o EMBI+
        if 'embi' in dados_macro['risco'].columns:
            fig_risco.add_trace(
                go.Scatter(
                    x=dados_macro['risco'].index,
                    y=dados_macro['risco']['embi'],
                    name="EMBI+ Brasil",
                    line=dict(color="#F44336", width=2)
                ),
                secondary_y=False
            )
        
        # Adiciona o CDS de 5 anos
        if 'GAP12_CRDSCBR5Y' in dados_macro['risco'].columns:
            fig_risco.add_trace(
                go.Scatter(
                    x=dados_macro['risco'].index,
                    y=dados_macro['risco']['GAP12_CRDSCBR5Y'],
                    name="CDS Brasil 5 anos",
                    line=dict(color="#1E88E5", width=2)
                ),
                secondary_y=False
            )
        
        # Adiciona o IFIX
        if 'ifix' in dados_macro['risco'].columns:
            fig_risco.add_trace(
                go.Scatter(
                    x=dados_macro['risco'].index,
                    y=dados_macro['risco']['ifix'],
                    name="IFIX",
                    line=dict(color="#4CAF50", width=2)
                ),
                secondary_y=True
            )
        
        # Configura os eixos
        fig_risco.update_layout(
            title="Indicadores de Risco",
            xaxis_title="Data",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig_risco.update_yaxes(title_text="Pontos (EMBI+ e CDS)", secondary_y=False)
        fig_risco.update_yaxes(title_text="Pontos (IFIX)", secondary_y=True)
        
        # Adiciona o gráfico ao dicionário
        graficos['risco'] = fig_risco
    
    return graficos

def criar_tabela_resumo_macro(resumo_macro: pd.DataFrame) -> go.Figure:
    """
    Cria uma tabela com o resumo dos principais indicadores macroeconômicos.
    
    Args:
        resumo_macro: DataFrame com o resumo dos indicadores.
        
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
                resumo_macro.index,
                resumo_macro['Valor'].apply(lambda x: f"{x:.2f}%" if isinstance(x, (int, float)) else x),
                resumo_macro['Data']
            ],
            fill_color='lavender',
            align='left'
        )
    )])
    
    # Configura o layout
    fig.update_layout(
        title="Resumo dos Indicadores Macroeconômicos",
        height=400
    )
    
    return fig

def criar_heatmap_correlacao_macro(dados_macro: Dict[str, pd.DataFrame]) -> go.Figure:
    """
    Cria um heatmap de correlação entre os principais indicadores macroeconômicos.
    
    Args:
        dados_macro: Dicionário com DataFrames dos dados macroeconômicos.
        
    Returns:
        go.Figure: Figura com o heatmap de correlação.
    """
    # Cria um DataFrame com os principais indicadores
    df_correlacao = pd.DataFrame()
    
    # Adiciona o PIB
    if 'pib' in dados_macro and not dados_macro['pib'].empty and 'pib_variacao' in dados_macro['pib'].columns:
        df_correlacao['PIB (var. anual)'] = dados_macro['pib']['pib_variacao']
    
    # Adiciona a inflação
    if 'inflacao' in dados_macro and not dados_macro['inflacao'].empty:
        if 'ipca_acumulado_12m' in dados_macro['inflacao'].columns:
            df_correlacao['IPCA (12 meses)'] = dados_macro['inflacao']['ipca_acumulado_12m']
        if 'igpm_acumulado_12m' in dados_macro['inflacao'].columns:
            df_correlacao['IGP-M (12 meses)'] = dados_macro['inflacao']['igpm_acumulado_12m']
    
    # Adiciona a taxa de juros
    if 'juros' in dados_macro and not dados_macro['juros'].empty and 'selic_meta' in dados_macro['juros'].columns:
        df_correlacao['Selic Meta'] = dados_macro['juros']['selic_meta']
    
    # Adiciona a taxa de desemprego
    if 'trabalho' in dados_macro and not dados_macro['trabalho'].empty and 'desemprego' in dados_macro['trabalho'].columns:
        df_correlacao['Desemprego'] = dados_macro['trabalho']['desemprego']
    
    # Adiciona o risco
    if 'risco' in dados_macro and not dados_macro['risco'].empty:
        if 'embi' in dados_macro['risco'].columns:
            df_correlacao['EMBI+'] = dados_macro['risco']['embi']
        if 'GAP12_CRDSCBR5Y' in dados_macro['risco'].columns:
            df_correlacao['CDS 5 anos'] = dados_macro['risco']['GAP12_CRDSCBR5Y']
    
    # Calcula a matriz de correlação
    if not df_correlacao.empty:
        matriz_correlacao = df_correlacao.corr()
        
        # Cria o heatmap
        fig = go.Figure(data=go.Heatmap(
            z=matriz_correlacao.values,
            x=matriz_correlacao.columns,
            y=matriz_correlacao.index,
            colorscale='RdBu_r',
            zmin=-1,
            zmax=1,
            text=matriz_correlacao.round(2).values,
            texttemplate="%{text}",
            textfont={"size": 10}
        ))
        
        # Configura o layout
        fig.update_layout(
            title="Correlação entre Indicadores Macroeconômicos",
            height=500,
            width=700
        )
        
        return fig
    else:
        # Retorna um gráfico vazio se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Correlação entre Indicadores Macroeconômicos",
            annotations=[dict(
                text="Dados insuficientes para calcular correlações",
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=14)
            )]
        )
        return fig
