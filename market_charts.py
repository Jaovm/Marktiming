"""
Módulo para visualização de dados de mercado e setores.

Este módulo contém funções para criar gráficos e visualizações dos dados de mercado,
incluindo ações, índices, setores da B3 e múltiplos de valuation.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple

def criar_grafico_indices(dados_indices: pd.DataFrame, periodo: str = "1y") -> go.Figure:
    """
    Cria um gráfico com a evolução dos principais índices brasileiros.
    
    Args:
        dados_indices: DataFrame com os dados dos índices.
        periodo: Período a ser exibido no gráfico.
        
    Returns:
        go.Figure: Figura do Plotly com o gráfico dos índices.
    """
    if dados_indices.empty:
        # Retorna um gráfico vazio se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Dados de índices não disponíveis",
            xaxis_title="Data",
            yaxis_title="Valor"
        )
        return fig
    
    # Cria um gráfico com os principais índices
    fig = go.Figure()
    
    # Lista de índices a serem exibidos
    indices = ['^BVSP', '^IBX', '^IDIV', '^SMLL', '^IFIX']
    cores = ['#1E88E5', '#F44336', '#4CAF50', '#FFC107', '#9C27B0']
    
    # Adiciona cada índice ao gráfico
    for i, indice in enumerate(indices):
        if indice in dados_indices.columns.levels[0]:
            # Normaliza os valores para base 100
            valores = dados_indices[indice]['Close']
            valores_norm = (valores / valores.iloc[0]) * 100
            
            fig.add_trace(
                go.Scatter(
                    x=valores.index,
                    y=valores_norm,
                    name=indice.replace('^', ''),
                    line=dict(color=cores[i % len(cores)], width=2)
                )
            )
    
    # Configura o layout
    fig.update_layout(
        title=f"Evolução dos Principais Índices Brasileiros (Base 100 - {periodo})",
        xaxis_title="Data",
        yaxis_title="Valor (Base 100)",
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

def criar_grafico_setores(dados_setores: Dict[str, pd.DataFrame], periodo: str = "1y") -> go.Figure:
    """
    Cria um gráfico com a evolução dos principais setores da B3.
    
    Args:
        dados_setores: Dicionário com DataFrames dos dados por setor.
        periodo: Período a ser exibido no gráfico.
        
    Returns:
        go.Figure: Figura do Plotly com o gráfico dos setores.
    """
    if not dados_setores:
        # Retorna um gráfico vazio se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Dados de setores não disponíveis",
            xaxis_title="Data",
            yaxis_title="Valor"
        )
        return fig
    
    # Cria um gráfico com os principais setores
    fig = go.Figure()
    
    # Cores para os setores
    cores = ['#1E88E5', '#F44336', '#4CAF50', '#FFC107', '#9C27B0', '#FF5722', '#607D8B', '#795548', '#00BCD4', '#8BC34A', '#3F51B5']
    
    # Para cada setor, calcula a média dos preços normalizados
    for i, (setor, dados) in enumerate(dados_setores.items()):
        # Obtém os tickers do setor
        tickers = list(dados.columns.levels[0])
        
        # Se não houver tickers, pula o setor
        if not tickers:
            continue
        
        # Inicializa DataFrame para armazenar preços normalizados
        precos_norm = pd.DataFrame(index=dados.index)
        
        # Para cada ticker, normaliza os preços
        for ticker in tickers:
            if 'Close' in dados[ticker].columns:
                valores = dados[ticker]['Close']
                precos_norm[ticker] = (valores / valores.iloc[0]) * 100
        
        # Calcula a média dos preços normalizados
        media_setor = precos_norm.mean(axis=1)
        
        # Adiciona ao gráfico
        fig.add_trace(
            go.Scatter(
                x=media_setor.index,
                y=media_setor.values,
                name=setor,
                line=dict(color=cores[i % len(cores)], width=2)
            )
        )
    
    # Configura o layout
    fig.update_layout(
        title=f"Evolução dos Setores da B3 (Base 100 - {periodo})",
        xaxis_title="Data",
        yaxis_title="Valor (Base 100)",
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

def criar_grafico_valuation_setorial(valuation_setorial: pd.DataFrame) -> go.Figure:
    """
    Cria um gráfico com os múltiplos de valuation por setor da B3.
    
    Args:
        valuation_setorial: DataFrame com os dados de valuation por setor.
        
    Returns:
        go.Figure: Figura do Plotly com o gráfico de valuation setorial.
    """
    if valuation_setorial.empty:
        # Retorna um gráfico vazio se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Dados de valuation setorial não disponíveis",
            xaxis_title="Setor",
            yaxis_title="Valor"
        )
        return fig
    
    # Cria um gráfico de barras com os múltiplos P/L e P/VP
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Adiciona P/L
    if 'P/L' in valuation_setorial.columns:
        fig.add_trace(
            go.Bar(
                x=valuation_setorial.index,
                y=valuation_setorial['P/L'],
                name="P/L",
                marker_color="#1E88E5"
            ),
            secondary_y=False
        )
    
    # Adiciona P/VP
    if 'P/VP' in valuation_setorial.columns:
        fig.add_trace(
            go.Bar(
                x=valuation_setorial.index,
                y=valuation_setorial['P/VP'],
                name="P/VP",
                marker_color="#F44336"
            ),
            secondary_y=True
        )
    
    # Configura os eixos
    fig.update_layout(
        title="Múltiplos de Valuation por Setor",
        xaxis_title="Setor",
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
        title_text="P/L",
        secondary_y=False
    )
    
    fig.update_yaxes(
        title_text="P/VP",
        secondary_y=True
    )
    
    # Rotaciona os rótulos do eixo X para melhor visualização
    fig.update_xaxes(
        tickangle=45
    )
    
    return fig

def criar_grafico_comparativo_valuation(comparacao_valuation: pd.DataFrame) -> go.Figure:
    """
    Cria um gráfico comparando múltiplos atuais com médias históricas.
    
    Args:
        comparacao_valuation: DataFrame com a comparação de múltiplos.
        
    Returns:
        go.Figure: Figura do Plotly com o gráfico comparativo.
    """
    if comparacao_valuation.empty:
        # Retorna um gráfico vazio se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Dados de comparação de valuation não disponíveis",
            xaxis_title="Setor",
            yaxis_title="Valor"
        )
        return fig
    
    # Cria um gráfico de barras agrupadas para comparar P/L atual com médias históricas
    fig = go.Figure()
    
    # Adiciona P/L atual
    if 'P/L (Atual)' in comparacao_valuation.columns:
        fig.add_trace(
            go.Bar(
                x=comparacao_valuation.index,
                y=comparacao_valuation['P/L (Atual)'],
                name="P/L Atual",
                marker_color="#1E88E5"
            )
        )
    
    # Adiciona P/L médio de 5 anos
    if 'P/L (Média 5a)' in comparacao_valuation.columns:
        fig.add_trace(
            go.Bar(
                x=comparacao_valuation.index,
                y=comparacao_valuation['P/L (Média 5a)'],
                name="P/L Média 5 anos",
                marker_color="#F44336"
            )
        )
    
    # Configura o layout
    fig.update_layout(
        title="Comparação de P/L Atual vs. Média Histórica",
        xaxis_title="Setor",
        yaxis_title="P/L",
        barmode='group',
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
    
    # Rotaciona os rótulos do eixo X para melhor visualização
    fig.update_xaxes(
        tickangle=45
    )
    
    return fig

def criar_grafico_premio_risco(premio_risco: pd.DataFrame) -> go.Figure:
    """
    Cria um gráfico com o prêmio de risco do mercado brasileiro.
    
    Args:
        premio_risco: DataFrame com os dados do prêmio de risco.
        
    Returns:
        go.Figure: Figura do Plotly com o gráfico do prêmio de risco.
    """
    if premio_risco.empty:
        # Retorna um gráfico vazio se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Dados de prêmio de risco não disponíveis",
            xaxis_title="Data",
            yaxis_title="Valor"
        )
        return fig
    
    # Cria um gráfico de barras com o prêmio de risco
    fig = go.Figure()
    
    # Obtém os valores
    earnings_yield = premio_risco['Earnings Yield (%)'].iloc[0] if 'Earnings Yield (%)' in premio_risco.columns else 0
    taxa_juros = premio_risco['Taxa de Juros Longo Prazo (%)'].iloc[0] if 'Taxa de Juros Longo Prazo (%)' in premio_risco.columns else 0
    premio = premio_risco['Prêmio de Risco (%)'].iloc[0] if 'Prêmio de Risco (%)' in premio_risco.columns else 0
    
    # Adiciona barras para cada componente
    fig.add_trace(
        go.Bar(
            x=['Earnings Yield', 'Taxa de Juros', 'Prêmio de Risco'],
            y=[earnings_yield, taxa_juros, premio],
            marker_color=['#4CAF50', '#F44336', '#1E88E5']
        )
    )
    
    # Adiciona linha horizontal em zero
    fig.add_shape(
        type="line",
        x0=-0.5,
        y0=0,
        x1=2.5,
        y1=0,
        line=dict(
            color="black",
            width=1,
            dash="dash",
        )
    )
    
    # Configura o layout
    fig.update_layout(
        title="Fed Model Adaptado para Brasil",
        xaxis_title="Componente",
        yaxis_title="Valor (%)",
        template="plotly_white",
        height=400
    )
    
    # Adiciona anotação com a interpretação
    if 'Interpretação' in premio_risco.columns:
        interpretacao = premio_risco['Interpretação'].iloc[0]
        fig.add_annotation(
            x=2,
            y=premio,
            text=interpretacao,
            showarrow=True,
            arrowhead=1,
            ax=0,
            ay=-40
        )
    
    return fig

def criar_grafico_classificacao_setorial(classificacao_setorial: pd.DataFrame) -> go.Figure:
    """
    Cria um gráfico com a classificação de valuation dos setores da B3.
    
    Args:
        classificacao_setorial: DataFrame com a classificação dos setores.
        
    Returns:
        go.Figure: Figura do Plotly com o gráfico de classificação setorial.
    """
    if classificacao_setorial.empty or 'Score Total' not in classificacao_setorial.columns:
        # Retorna um gráfico vazio se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Dados de classificação setorial não disponíveis",
            xaxis_title="Setor",
            yaxis_title="Score"
        )
        return fig
    
    # Ordena os setores pelo score total
    df_ordenado = classificacao_setorial.sort_values('Score Total', ascending=False)
    
    # Define cores com base na classificação
    cores = []
    for setor in df_ordenado.index:
        if 'Classificação' in df_ordenado.columns:
            classificacao = df_ordenado.loc[setor, 'Classificação']
            if classificacao == 'Muito Barato':
                cores.append('#4CAF50')  # Verde
            elif classificacao == 'Barato':
                cores.append('#8BC34A')  # Verde claro
            elif classificacao == 'Neutro':
                cores.append('#FFC107')  # Amarelo
            elif classificacao == 'Caro':
                cores.append('#FF9800')  # Laranja
            elif classificacao == 'Muito Caro':
                cores.append('#F44336')  # Vermelho
            else:
                cores.append('#9E9E9E')  # Cinza
        else:
            cores.append('#9E9E9E')  # Cinza
    
    # Cria um gráfico de barras com o score total
    fig = go.Figure()
    
    fig.add_trace(
        go.Bar(
            x=df_ordenado.index,
            y=df_ordenado['Score Total'],
            marker_color=cores
        )
    )
    
    # Configura o layout
    fig.update_layout(
        title="Classificação de Valuation dos Setores da B3",
        xaxis_title="Setor",
        yaxis_title="Score Total",
        template="plotly_white",
        height=500
    )
    
    # Rotaciona os rótulos do eixo X para melhor visualização
    fig.update_xaxes(
        tickangle=45
    )
    
    # Adiciona linha horizontal em zero
    fig.add_shape(
        type="line",
        x0=-0.5,
        y0=0,
        x1=len(df_ordenado.index) - 0.5,
        y1=0,
        line=dict(
            color="black",
            width=1,
            dash="dash",
        )
    )
    
    return fig

def criar_grafico_carteira(dados_carteira: pd.DataFrame, periodo: str = "1y") -> go.Figure:
    """
    Cria um gráfico com a evolução da carteira de ações.
    
    Args:
        dados_carteira: DataFrame com os dados da carteira.
        periodo: Período a ser exibido no gráfico.
        
    Returns:
        go.Figure: Figura do Plotly com o gráfico da carteira.
    """
    if dados_carteira.empty:
        # Retorna um gráfico vazio se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Dados da carteira não disponíveis",
            xaxis_title="Data",
            yaxis_title="Valor"
        )
        return fig
    
    # Cria um gráfico com a evolução da carteira
    fig = go.Figure()
    
    # Lista de tickers na carteira
    tickers = list(dados_carteira.columns.levels[0])
    
    # Adiciona cada ticker ao gráfico
    for ticker in tickers:
        if 'Close' in dados_carteira[ticker].columns:
            # Normaliza os valores para base 100
            valores = dados_carteira[ticker]['Close']
            valores_norm = (valores / valores.iloc[0]) * 100
            
            fig.add_trace(
                go.Scatter(
                    x=valores.index,
                    y=valores_norm,
                    name=ticker,
                    line=dict(width=1)
                )
            )
    
    # Calcula a média da carteira
    carteira_norm = pd.DataFrame(index=dados_carteira.index)
    for ticker in tickers:
        if 'Close' in dados_carteira[ticker].columns:
            valores = dados_carteira[ticker]['Close']
            carteira_norm[ticker] = (valores / valores.iloc[0]) * 100
    
    media_carteira = carteira_norm.mean(axis=1)
    
    # Adiciona a média da carteira com linha mais grossa
    fig.add_trace(
        go.Scatter(
            x=media_carteira.index,
            y=media_carteira.values,
            name="Média da Carteira",
            line=dict(color="#1E88E5", width=3)
        )
    )
    
    # Configura o layout
    fig.update_layout(
        title=f"Evolução da Carteira (Base 100 - {periodo})",
        xaxis_title="Data",
        yaxis_title="Valor (Base 100)",
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

def criar_grafico_analise_carteira(analise_carteira: pd.DataFrame) -> go.Figure:
    """
    Cria um gráfico com a análise da carteira de ações.
    
    Args:
        analise_carteira: DataFrame com a análise da carteira.
        
    Returns:
        go.Figure: Figura do Plotly com o gráfico de análise da carteira.
    """
    if analise_carteira.empty:
        # Retorna um gráfico vazio se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Dados de análise da carteira não disponíveis",
            xaxis_title="Ticker",
            yaxis_title="Valor"
        )
        return fig
    
    # Cria um gráfico de barras com os múltiplos P/L e P/VP da carteira
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Adiciona P/L
    if 'P/L' in analise_carteira.columns:
        fig.add_trace(
            go.Bar(
                x=analise_carteira.index,
                y=analise_carteira['P/L'],
                name="P/L",
                marker_color="#1E88E5"
            ),
            secondary_y=False
        )
    
    # Adiciona P/VP
    if 'P/VP' in analise_carteira.columns:
        fig.add_trace(
            go.Bar(
                x=analise_carteira.index,
                y=analise_carteira['P/VP'],
                name="P/VP",
                marker_color="#F44336"
            ),
            secondary_y=True
        )
    
    # Configura os eixos
    fig.update_layout(
        title="Múltiplos de Valuation da Carteira",
        xaxis_title="Ticker",
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
        title_text="P/L",
        secondary_y=False
    )
    
    fig.update_yaxes(
        title_text="P/VP",
        secondary_y=True
    )
    
    return fig

def criar_tabela_resumo_mercado(resumo_mercado: pd.DataFrame) -> go.Figure:
    """
    Cria uma tabela com o resumo dos indicadores de mercado.
    
    Args:
        resumo_mercado: DataFrame com o resumo dos indicadores de mercado.
        
    Returns:
        go.Figure: Figura do Plotly com a tabela de resumo.
    """
    if resumo_mercado.empty:
        # Retorna uma tabela vazia se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Resumo dos indicadores de mercado não disponível"
        )
        return fig
    
    # Formata os valores para exibição
    resumo_formatado = resumo_mercado.copy()
    
    for idx in resumo_formatado.index:
        if 'Variação' in idx:
            # Formata percentuais
            resumo_formatado.loc[idx, 'Valor'] = f"{resumo_formatado.loc[idx, 'Valor']:.2f}%"
        elif 'P/L' in idx or 'P/VP' in idx or 'EV/EBITDA' in idx:
            # Formata múltiplos
            resumo_formatado.loc[idx, 'Valor'] = f"{resumo_formatado.loc[idx, 'Valor']:.2f}x"
        elif 'Dividend Yield' in idx or 'Prêmio de Risco' in idx:
            # Formata percentuais
            resumo_formatado.loc[idx, 'Valor'] = f"{resumo_formatado.loc[idx, 'Valor']:.2f}%"
    
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
                    resumo_formatado.get("Data", [""] * len(resumo_formatado))
                ],
                fill_color="#F5F5F5",
                align="left",
                font=dict(size=12)
            )
        )
    ])
    
    # Configura o layout
    fig.update_layout(
        title="Resumo dos Indicadores de Mercado",
        height=400
    )
    
    return fig

def criar_dashboard_mercado(dados_mercado: Dict[str, Union[pd.DataFrame, Dict]]) -> Dict[str, go.Figure]:
    """
    Cria um dashboard completo com todos os indicadores de mercado.
    
    Args:
        dados_mercado: Dicionário com DataFrames e outros dados de mercado.
        
    Returns:
        Dict[str, go.Figure]: Dicionário com figuras do Plotly para cada indicador.
    """
    dashboard = {}
    
    # Cria gráfico dos índices
    if 'indices' in dados_mercado:
        dashboard['indices'] = criar_grafico_indices(dados_mercado['indices'])
    
    # Cria gráfico dos setores
    if 'setores' in dados_mercado:
        dashboard['setores'] = criar_grafico_setores(dados_mercado['setores'])
    
    # Cria gráfico de valuation setorial
    if 'valuation_setorial' in dados_mercado:
        dashboard['valuation_setorial'] = criar_grafico_valuation_setorial(dados_mercado['valuation_setorial'])
    
    # Cria gráfico comparativo de valuation
    if 'comparacao_valuation' in dados_mercado:
        dashboard['comparacao_valuation'] = criar_grafico_comparativo_valuation(dados_mercado['comparacao_valuation'])
    
    # Cria gráfico do prêmio de risco
    if 'premio_risco' in dados_mercado:
        dashboard['premio_risco'] = criar_grafico_premio_risco(dados_mercado['premio_risco'])
    
    # Cria gráfico de classificação setorial
    if 'classificacao_setorial' in dados_mercado:
        dashboard['classificacao_setorial'] = criar_grafico_classificacao_setorial(dados_mercado['classificacao_setorial'])
    
    # Cria gráfico da carteira
    if 'carteira' in dados_mercado:
        dashboard['carteira'] = criar_grafico_carteira(dados_mercado['carteira'])
    
    # Cria gráfico de análise da carteira
    if 'analise_carteira' in dados_mercado:
        dashboard['analise_carteira'] = criar_grafico_analise_carteira(dados_mercado['analise_carteira'])
    
    # Cria tabela de resumo do mercado
    if 'resumo_mercado' in dados_mercado:
        dashboard['resumo_mercado'] = criar_tabela_resumo_mercado(dados_mercado['resumo_mercado'])
    
    return dashboard
