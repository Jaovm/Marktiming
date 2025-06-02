"""
Módulo para visualização de dados macroeconômicos.

Este módulo contém funções para criar gráficos e visualizações dos indicadores
macroeconômicos brasileiros, como PIB, inflação, juros, desemprego, liquidez e risco.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple

def criar_grafico_pib(dados_pib: pd.DataFrame) -> go.Figure:
    """
    Cria um gráfico com a evolução do PIB brasileiro.
    
    Args:
        dados_pib: DataFrame com os dados do PIB.
        
    Returns:
        go.Figure: Figura do Plotly com o gráfico do PIB.
    """
    if dados_pib.empty:
        # Retorna um gráfico vazio se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Dados do PIB não disponíveis",
            xaxis_title="Data",
            yaxis_title="Valor"
        )
        return fig
    
    # Cria um gráfico com duas métricas: valor e variação
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Adiciona o valor do PIB
    if 'pib_valor' in dados_pib.columns:
        fig.add_trace(
            go.Scatter(
                x=dados_pib.index,
                y=dados_pib['pib_valor'],
                name="PIB (R$ milhões)",
                line=dict(color="#1E88E5", width=2)
            ),
            secondary_y=False
        )
    
    # Adiciona a variação do PIB
    if 'pib_variacao' in dados_pib.columns:
        fig.add_trace(
            go.Bar(
                x=dados_pib.index,
                y=dados_pib['pib_variacao'],
                name="Variação Anual (%)",
                marker_color="#FFC107"
            ),
            secondary_y=True
        )
    
    # Configura os eixos
    fig.update_layout(
        title="Evolução do PIB Brasileiro",
        xaxis_title="Data",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        template="plotly_white",
        height=500
    )
    
    fig.update_yaxes(
        title_text="PIB (R$ milhões)",
        secondary_y=False
    )
    
    fig.update_yaxes(
        title_text="Variação Anual (%)",
        secondary_y=True
    )
    
    return fig

def criar_grafico_inflacao(dados_inflacao: pd.DataFrame) -> go.Figure:
    """
    Cria um gráfico com a evolução da inflação brasileira.
    
    Args:
        dados_inflacao: DataFrame com os dados de inflação.
        
    Returns:
        go.Figure: Figura do Plotly com o gráfico de inflação.
    """
    if dados_inflacao.empty:
        # Retorna um gráfico vazio se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Dados de inflação não disponíveis",
            xaxis_title="Data",
            yaxis_title="Valor"
        )
        return fig
    
    # Cria um gráfico com IPCA e IGP-M acumulados em 12 meses
    fig = go.Figure()
    
    # Adiciona o IPCA acumulado em 12 meses
    if 'ipca_acumulado_12m' in dados_inflacao.columns:
        fig.add_trace(
            go.Scatter(
                x=dados_inflacao.index,
                y=dados_inflacao['ipca_acumulado_12m'],
                name="IPCA (12 meses)",
                line=dict(color="#1E88E5", width=2)
            )
        )
    
    # Adiciona o IGP-M acumulado em 12 meses
    if 'igpm_acumulado_12m' in dados_inflacao.columns:
        fig.add_trace(
            go.Scatter(
                x=dados_inflacao.index,
                y=dados_inflacao['igpm_acumulado_12m'],
                name="IGP-M (12 meses)",
                line=dict(color="#F44336", width=2)
            )
        )
    
    # Adiciona linha horizontal na meta de inflação (3.5%)
    fig.add_shape(
        type="line",
        x0=dados_inflacao.index.min(),
        y0=3.5,
        x1=dados_inflacao.index.max(),
        y1=3.5,
        line=dict(
            color="#4CAF50",
            width=2,
            dash="dash",
        )
    )
    
    # Adiciona anotação para a meta de inflação
    fig.add_annotation(
        x=dados_inflacao.index.max(),
        y=3.5,
        text="Meta de Inflação",
        showarrow=False,
        yshift=10,
        font=dict(
            color="#4CAF50"
        )
    )
    
    # Configura o layout
    fig.update_layout(
        title="Evolução da Inflação Brasileira",
        xaxis_title="Data",
        yaxis_title="Variação Acumulada 12 meses (%)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        template="plotly_white",
        height=500
    )
    
    return fig

def criar_grafico_juros(dados_juros: pd.DataFrame) -> go.Figure:
    """
    Cria um gráfico com a evolução da taxa de juros brasileira.
    
    Args:
        dados_juros: DataFrame com os dados de juros.
        
    Returns:
        go.Figure: Figura do Plotly com o gráfico de juros.
    """
    if dados_juros.empty:
        # Retorna um gráfico vazio se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Dados de juros não disponíveis",
            xaxis_title="Data",
            yaxis_title="Taxa (%)"
        )
        return fig
    
    # Cria um gráfico com a taxa Selic
    fig = go.Figure()
    
    # Adiciona a taxa Selic meta
    if 'selic_meta' in dados_juros.columns:
        fig.add_trace(
            go.Scatter(
                x=dados_juros.index,
                y=dados_juros['selic_meta'],
                name="Taxa Selic Meta",
                line=dict(color="#1E88E5", width=2)
            )
        )
    
    # Adiciona a taxa Selic diária
    if 'selic_diaria' in dados_juros.columns:
        fig.add_trace(
            go.Scatter(
                x=dados_juros.index,
                y=dados_juros['selic_diaria'],
                name="Taxa Selic Diária",
                line=dict(color="#F44336", width=1, dash="dot")
            )
        )
    
    # Configura o layout
    fig.update_layout(
        title="Evolução da Taxa Selic",
        xaxis_title="Data",
        yaxis_title="Taxa (%)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        template="plotly_white",
        height=500
    )
    
    return fig

def criar_grafico_curva_juros(dados_curva_juros: pd.DataFrame) -> go.Figure:
    """
    Cria um gráfico com a curva de juros brasileira.
    
    Args:
        dados_curva_juros: DataFrame com os dados da curva de juros.
        
    Returns:
        go.Figure: Figura do Plotly com o gráfico da curva de juros.
    """
    if dados_curva_juros.empty:
        # Retorna um gráfico vazio se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Dados da curva de juros não disponíveis",
            xaxis_title="Prazo",
            yaxis_title="Taxa (%)"
        )
        return fig
    
    # Obtém os dados mais recentes
    ultimo_dia = dados_curva_juros.iloc[-1]
    
    # Prazos em dias
    prazos = [30, 90, 180, 360, 720, 1080]
    
    # Taxas correspondentes
    taxas = []
    for prazo in [30, 90, 180, 360, 720, 1080]:
        coluna = f'di_{prazo}d'
        if coluna in ultimo_dia.index:
            taxas.append(ultimo_dia[coluna])
        else:
            taxas.append(None)
    
    # Cria o gráfico da curva de juros atual
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
            x=prazos,
            y=taxas,
            mode='lines+markers',
            name="Curva Atual",
            line=dict(color="#1E88E5", width=2),
            marker=dict(size=8)
        )
    )
    
    # Se houver dados de 30 dias atrás, adiciona para comparação
    if len(dados_curva_juros) > 30:
        dia_anterior = dados_curva_juros.iloc[-30]
        
        taxas_anterior = []
        for prazo in [30, 90, 180, 360, 720, 1080]:
            coluna = f'di_{prazo}d'
            if coluna in dia_anterior.index:
                taxas_anterior.append(dia_anterior[coluna])
            else:
                taxas_anterior.append(None)
        
        fig.add_trace(
            go.Scatter(
                x=prazos,
                y=taxas_anterior,
                mode='lines+markers',
                name="Curva 30 dias atrás",
                line=dict(color="#F44336", width=2, dash="dash"),
                marker=dict(size=6)
            )
        )
    
    # Configura o layout
    fig.update_layout(
        title="Curva de Juros Brasileira",
        xaxis_title="Prazo (dias)",
        yaxis_title="Taxa (%)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        template="plotly_white",
        height=500
    )
    
    # Configura o eixo X para mostrar os prazos em meses/anos
    fig.update_xaxes(
        tickvals=prazos,
        ticktext=["1 mês", "3 meses", "6 meses", "1 ano", "2 anos", "3 anos"]
    )
    
    return fig

def criar_grafico_trabalho(dados_trabalho: pd.DataFrame) -> go.Figure:
    """
    Cria um gráfico com os dados do mercado de trabalho brasileiro.
    
    Args:
        dados_trabalho: DataFrame com os dados do mercado de trabalho.
        
    Returns:
        go.Figure: Figura do Plotly com o gráfico do mercado de trabalho.
    """
    if dados_trabalho.empty:
        # Retorna um gráfico vazio se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Dados do mercado de trabalho não disponíveis",
            xaxis_title="Data",
            yaxis_title="Valor"
        )
        return fig
    
    # Cria um gráfico com duas métricas: desemprego e saldo do CAGED
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Adiciona a taxa de desemprego
    if 'desemprego' in dados_trabalho.columns:
        fig.add_trace(
            go.Scatter(
                x=dados_trabalho.index,
                y=dados_trabalho['desemprego'],
                name="Taxa de Desemprego (%)",
                line=dict(color="#1E88E5", width=2)
            ),
            secondary_y=False
        )
    
    # Adiciona o saldo do CAGED
    if 'caged_saldo' in dados_trabalho.columns:
        fig.add_trace(
            go.Bar(
                x=dados_trabalho.index,
                y=dados_trabalho['caged_saldo'],
                name="Saldo de Empregos (CAGED)",
                marker_color="#4CAF50"
            ),
            secondary_y=True
        )
    
    # Configura os eixos
    fig.update_layout(
        title="Mercado de Trabalho Brasileiro",
        xaxis_title="Data",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        template="plotly_white",
        height=500
    )
    
    fig.update_yaxes(
        title_text="Taxa de Desemprego (%)",
        secondary_y=False
    )
    
    fig.update_yaxes(
        title_text="Saldo de Empregos",
        secondary_y=True
    )
    
    return fig

def criar_grafico_liquidez(dados_liquidez: pd.DataFrame) -> go.Figure:
    """
    Cria um gráfico com os dados de liquidez e agregados monetários brasileiros.
    
    Args:
        dados_liquidez: DataFrame com os dados de liquidez.
        
    Returns:
        go.Figure: Figura do Plotly com o gráfico de liquidez.
    """
    if dados_liquidez.empty:
        # Retorna um gráfico vazio se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Dados de liquidez não disponíveis",
            xaxis_title="Data",
            yaxis_title="Valor"
        )
        return fig
    
    # Cria um gráfico com os agregados monetários
    fig = go.Figure()
    
    # Adiciona M1
    if 'm1' in dados_liquidez.columns:
        fig.add_trace(
            go.Scatter(
                x=dados_liquidez.index,
                y=dados_liquidez['m1'] / 1e9,  # Converte para bilhões
                name="M1",
                line=dict(color="#1E88E5", width=2)
            )
        )
    
    # Adiciona M2
    if 'm2' in dados_liquidez.columns:
        fig.add_trace(
            go.Scatter(
                x=dados_liquidez.index,
                y=dados_liquidez['m2'] / 1e9,  # Converte para bilhões
                name="M2",
                line=dict(color="#F44336", width=2)
            )
        )
    
    # Adiciona M3
    if 'm3' in dados_liquidez.columns:
        fig.add_trace(
            go.Scatter(
                x=dados_liquidez.index,
                y=dados_liquidez['m3'] / 1e9,  # Converte para bilhões
                name="M3",
                line=dict(color="#4CAF50", width=2)
            )
        )
    
    # Adiciona M4
    if 'm4' in dados_liquidez.columns:
        fig.add_trace(
            go.Scatter(
                x=dados_liquidez.index,
                y=dados_liquidez['m4'] / 1e9,  # Converte para bilhões
                name="M4",
                line=dict(color="#FFC107", width=2)
            )
        )
    
    # Configura o layout
    fig.update_layout(
        title="Agregados Monetários Brasileiros",
        xaxis_title="Data",
        yaxis_title="Valor (R$ bilhões)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        template="plotly_white",
        height=500
    )
    
    return fig

def criar_grafico_risco(dados_risco: pd.DataFrame) -> go.Figure:
    """
    Cria um gráfico com os indicadores de risco do Brasil.
    
    Args:
        dados_risco: DataFrame com os dados de risco.
        
    Returns:
        go.Figure: Figura do Plotly com o gráfico de risco.
    """
    if dados_risco.empty:
        # Retorna um gráfico vazio se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Dados de risco não disponíveis",
            xaxis_title="Data",
            yaxis_title="Valor"
        )
        return fig
    
    # Cria um gráfico com duas métricas: EMBI+ e CDS
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Adiciona o EMBI+
    if 'embi' in dados_risco.columns:
        fig.add_trace(
            go.Scatter(
                x=dados_risco.index,
                y=dados_risco['embi'],
                name="EMBI+ Brasil",
                line=dict(color="#1E88E5", width=2)
            ),
            secondary_y=False
        )
    
    # Adiciona o CDS
    if 'GAP12_CRDSCBR5Y' in dados_risco.columns:
        fig.add_trace(
            go.Scatter(
                x=dados_risco.index,
                y=dados_risco['GAP12_CRDSCBR5Y'],
                name="CDS Brasil 5 anos",
                line=dict(color="#F44336", width=2)
            ),
            secondary_y=True
        )
    
    # Configura os eixos
    fig.update_layout(
        title="Indicadores de Risco do Brasil",
        xaxis_title="Data",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        template="plotly_white",
        height=500
    )
    
    fig.update_yaxes(
        title_text="EMBI+ Brasil (pontos)",
        secondary_y=False
    )
    
    fig.update_yaxes(
        title_text="CDS Brasil 5 anos (pontos)",
        secondary_y=True
    )
    
    return fig

def criar_dashboard_macro(dados_macro: Dict[str, pd.DataFrame]) -> Dict[str, go.Figure]:
    """
    Cria um dashboard completo com todos os indicadores macroeconômicos.
    
    Args:
        dados_macro: Dicionário com DataFrames de dados macroeconômicos.
        
    Returns:
        Dict[str, go.Figure]: Dicionário com figuras do Plotly para cada indicador.
    """
    dashboard = {}
    
    # Cria gráfico do PIB
    if 'pib' in dados_macro:
        dashboard['pib'] = criar_grafico_pib(dados_macro['pib'])
    
    # Cria gráfico de inflação
    if 'inflacao' in dados_macro:
        dashboard['inflacao'] = criar_grafico_inflacao(dados_macro['inflacao'])
    
    # Cria gráfico de juros
    if 'juros' in dados_macro:
        dashboard['juros'] = criar_grafico_juros(dados_macro['juros'])
    
    # Cria gráfico da curva de juros
    if 'curva_juros' in dados_macro:
        dashboard['curva_juros'] = criar_grafico_curva_juros(dados_macro['curva_juros'])
    
    # Cria gráfico do mercado de trabalho
    if 'trabalho' in dados_macro:
        dashboard['trabalho'] = criar_grafico_trabalho(dados_macro['trabalho'])
    
    # Cria gráfico de liquidez
    if 'liquidez' in dados_macro:
        dashboard['liquidez'] = criar_grafico_liquidez(dados_macro['liquidez'])
    
    # Cria gráfico de risco
    if 'risco' in dados_macro:
        dashboard['risco'] = criar_grafico_risco(dados_macro['risco'])
    
    return dashboard

def criar_tabela_resumo_macro(resumo_macro: pd.DataFrame) -> go.Figure:
    """
    Cria uma tabela com o resumo dos indicadores macroeconômicos.
    
    Args:
        resumo_macro: DataFrame com o resumo dos indicadores macroeconômicos.
        
    Returns:
        go.Figure: Figura do Plotly com a tabela de resumo.
    """
    if resumo_macro.empty:
        # Retorna uma tabela vazia se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Resumo dos indicadores macroeconômicos não disponível"
        )
        return fig
    
    # Formata os valores para exibição
    resumo_formatado = resumo_macro.copy()
    
    for idx in resumo_formatado.index:
        if 'IPCA' in idx or 'IGP-M' in idx or 'Taxa' in idx or 'Desemprego' in idx:
            # Formata percentuais
            resumo_formatado.loc[idx, 'Valor'] = f"{resumo_formatado.loc[idx, 'Valor']:.2f}%"
        elif 'EMBI' in idx or 'CDS' in idx:
            # Formata pontos
            resumo_formatado.loc[idx, 'Valor'] = f"{resumo_formatado.loc[idx, 'Valor']:.0f} pts"
    
    # Cria a tabela
    fig = go.Figure(data=[
        go.Table(
            header=dict(
                values=["Indicador", "Valor", "Data"],
                fill_color="#1E88E5",
                align="left",
                font=dict(color="white", size=14)
            ),
            cells=dict(
                values=[
                    resumo_formatado.index,
                    resumo_formatado["Valor"],
                    resumo_formatado["Data"]
                ],
                fill_color="#F5F5F5",
                align="left",
                font=dict(size=12)
            )
        )
    ])
    
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
        dados_macro: Dicionário com DataFrames de dados macroeconômicos.
        
    Returns:
        go.Figure: Figura do Plotly com o heatmap de correlação.
    """
    # Cria um DataFrame combinado com os principais indicadores
    df_combinado = pd.DataFrame()
    
    # Adiciona IPCA
    if 'inflacao' in dados_macro and 'ipca_acumulado_12m' in dados_macro['inflacao'].columns:
        df_combinado['IPCA'] = dados_macro['inflacao']['ipca_acumulado_12m']
    
    # Adiciona Selic
    if 'juros' in dados_macro and 'selic_meta' in dados_macro['juros'].columns:
        df_combinado['Selic'] = dados_macro['juros']['selic_meta']
    
    # Adiciona Desemprego
    if 'trabalho' in dados_macro and 'desemprego' in dados_macro['trabalho'].columns:
        df_combinado['Desemprego'] = dados_macro['trabalho']['desemprego']
    
    # Adiciona EMBI+
    if 'risco' in dados_macro and 'embi' in dados_macro['risco'].columns:
        df_combinado['EMBI'] = dados_macro['risco']['embi']
    
    # Adiciona CDS
    if 'risco' in dados_macro and 'GAP12_CRDSCBR5Y' in dados_macro['risco'].columns:
        df_combinado['CDS'] = dados_macro['risco']['GAP12_CRDSCBR5Y']
    
    # Se não houver dados suficientes, retorna um gráfico vazio
    if df_combinado.empty or df_combinado.shape[1] < 2:
        fig = go.Figure()
        fig.update_layout(
            title="Dados insuficientes para criar heatmap de correlação"
        )
        return fig
    
    # Calcula a matriz de correlação
    corr_matrix = df_combinado.corr()
    
    # Cria o heatmap
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.index,
        colorscale='RdBu_r',
        zmin=-1,
        zmax=1,
        text=np.round(corr_matrix.values, 2),
        texttemplate="%{text:.2f}",
        textfont={"size": 12},
        hoverongaps=False
    ))
    
    # Configura o layout
    fig.update_layout(
        title="Correlação entre Indicadores Macroeconômicos",
        height=500,
        template="plotly_white"
    )
    
    return fig
