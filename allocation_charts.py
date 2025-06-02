"""
Módulo para visualização de recomendações de alocação setorial.

Este módulo contém funções para criar gráficos e visualizações relacionados
às recomendações de alocação setorial com base no ciclo econômico.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple

def criar_grafico_alocacao_recomendada(recomendacao: Dict[str, Union[str, Dict, List]]) -> go.Figure:
    """
    Cria um gráfico com a alocação setorial recomendada.
    
    Args:
        recomendacao: Dicionário com recomendações de alocação.
        
    Returns:
        go.Figure: Figura do Plotly com o gráfico de alocação recomendada.
    """
    if not recomendacao or 'alocacao_recomendada' not in recomendacao:
        # Retorna um gráfico vazio se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Dados de alocação recomendada não disponíveis"
        )
        return fig
    
    # Obtém os dados de alocação
    alocacao = recomendacao['alocacao_recomendada']
    
    # Cria um gráfico de pizza com a alocação recomendada
    labels = list(alocacao.keys())
    values = list(alocacao.values())
    
    # Define cores para os setores
    cores = px.colors.qualitative.Plotly
    
    fig = go.Figure(data=[
        go.Pie(
            labels=labels,
            values=values,
            textinfo='label+percent',
            insidetextorientation='radial',
            marker=dict(colors=cores),
            hole=0.3
        )
    ])
    
    # Configura o layout
    fig.update_layout(
        title=f"Alocação Setorial Recomendada - Fase: {recomendacao['fase_ciclo'].capitalize()}",
        height=600,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )
    
    # Adiciona anotação com o nível de risco
    if 'nivel_risco' in recomendacao:
        fig.add_annotation(
            x=0.5,
            y=0.5,
            text=f"Nível de Risco:\n{recomendacao['nivel_risco']}",
            showarrow=False,
            font=dict(size=14),
            align="center"
        )
    
    return fig

def criar_grafico_alinhamento_carteira(alinhamento: Dict[str, Union[float, Dict, List]]) -> go.Figure:
    """
    Cria um gráfico com o alinhamento da carteira atual ao ciclo econômico.
    
    Args:
        alinhamento: Dicionário com análise de alinhamento da carteira.
        
    Returns:
        go.Figure: Figura do Plotly com o gráfico de alinhamento da carteira.
    """
    if not alinhamento or 'alinhamento_score' not in alinhamento:
        # Retorna um gráfico vazio se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Dados de alinhamento da carteira não disponíveis"
        )
        return fig
    
    # Cria um gráfico de gauge para o score de alinhamento
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=alinhamento['alinhamento_score'],
        domain=dict(x=[0, 1], y=[0, 1]),
        title=dict(text="Score de Alinhamento da Carteira", font=dict(size=16)),
        gauge=dict(
            axis=dict(range=[0, 100]),
            bar=dict(color="#1E88E5"),
            bgcolor="white",
            borderwidth=2,
            bordercolor="gray",
            steps=[
                dict(range=[0, 30], color="#F44336"),   # Vermelho
                dict(range=[30, 60], color="#FFC107"),  # Amarelo
                dict(range=[60, 100], color="#4CAF50")  # Verde
            ],
            threshold=dict(
                line=dict(color="black", width=4),
                thickness=0.75,
                value=alinhamento['alinhamento_score']
            )
        )
    ))
    
    # Configura o layout
    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    # Adiciona interpretação do score
    interpretacao = ""
    if alinhamento['alinhamento_score'] >= 80:
        interpretacao = "Carteira muito bem alinhada ao ciclo atual"
    elif alinhamento['alinhamento_score'] >= 60:
        interpretacao = "Carteira bem alinhada ao ciclo atual"
    elif alinhamento['alinhamento_score'] >= 40:
        interpretacao = "Carteira moderadamente alinhada ao ciclo atual"
    elif alinhamento['alinhamento_score'] >= 20:
        interpretacao = "Carteira pouco alinhada ao ciclo atual"
    else:
        interpretacao = "Carteira desalinhada do ciclo atual"
    
    fig.add_annotation(
        x=0.5,
        y=0.2,
        text=interpretacao,
        showarrow=False,
        font=dict(size=14),
        align="center",
        xref="paper",
        yref="paper"
    )
    
    return fig

def criar_grafico_comparativo_alocacao(alinhamento: Dict[str, Union[float, Dict, List]]) -> go.Figure:
    """
    Cria um gráfico comparando a alocação atual com a recomendada.
    
    Args:
        alinhamento: Dicionário com análise de alinhamento da carteira.
        
    Returns:
        go.Figure: Figura do Plotly com o gráfico comparativo de alocação.
    """
    if not alinhamento or 'setores_carteira' not in alinhamento or 'setores_recomendados' not in alinhamento:
        # Retorna um gráfico vazio se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Dados comparativos de alocação não disponíveis"
        )
        return fig
    
    # Obtém os dados de alocação
    setores_carteira = alinhamento['setores_carteira']
    setores_recomendados = alinhamento['setores_recomendados']
    
    # Combina os setores de ambas as alocações
    todos_setores = sorted(set(list(setores_carteira.keys()) + list(setores_recomendados.keys())))
    
    # Cria listas para o gráfico
    alocacao_atual = [setores_carteira.get(setor, 0) for setor in todos_setores]
    alocacao_recomendada = [setores_recomendados.get(setor, 0) for setor in todos_setores]
    
    # Cria um gráfico de barras agrupadas
    fig = go.Figure()
    
    fig.add_trace(
        go.Bar(
            x=todos_setores,
            y=alocacao_atual,
            name="Alocação Atual",
            marker_color="#1E88E5"
        )
    )
    
    fig.add_trace(
        go.Bar(
            x=todos_setores,
            y=alocacao_recomendada,
            name="Alocação Recomendada",
            marker_color="#4CAF50"
        )
    )
    
    # Configura o layout
    fig.update_layout(
        title="Comparação: Alocação Atual vs. Recomendada",
        xaxis_title="Setor",
        yaxis_title="Alocação (%)",
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

def criar_tabela_acoes_alinhadas(alinhamento: Dict[str, Union[float, Dict, List]]) -> go.Figure:
    """
    Cria uma tabela com as ações alinhadas ao ciclo econômico.
    
    Args:
        alinhamento: Dicionário com análise de alinhamento da carteira.
        
    Returns:
        go.Figure: Figura do Plotly com a tabela de ações alinhadas.
    """
    if not alinhamento or 'acoes_alinhadas' not in alinhamento:
        # Retorna uma tabela vazia se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Dados de ações alinhadas não disponíveis"
        )
        return fig
    
    # Obtém as ações alinhadas
    acoes_alinhadas = alinhamento['acoes_alinhadas']
    
    if not acoes_alinhadas:
        # Retorna uma tabela vazia se não houver ações alinhadas
        fig = go.Figure()
        fig.update_layout(
            title="Não há ações alinhadas ao ciclo atual"
        )
        return fig
    
    # Cria uma tabela com as ações alinhadas
    fig = go.Figure(data=[
        go.Table(
            header=dict(
                values=["Ticker", "Setor", "Justificativa"],
                fill_color="#4CAF50",
                align="left",
                font=dict(color="white", size=14)
            ),
            cells=dict(
                values=[
                    [acao['ticker'] for acao in acoes_alinhadas],
                    [acao['setor'] for acao in acoes_alinhadas],
                    [acao['justificativa'] for acao in acoes_alinhadas]
                ],
                fill_color="#F5F5F5",
                align="left",
                font=dict(size=12)
            )
        )
    ])
    
    # Configura o layout
    fig.update_layout(
        title="Ações Alinhadas ao Ciclo Econômico Atual",
        height=300 + 30 * len(acoes_alinhadas)  # Ajusta a altura com base no número de ações
    )
    
    return fig

def criar_tabela_acoes_desalinhadas(alinhamento: Dict[str, Union[float, Dict, List]]) -> go.Figure:
    """
    Cria uma tabela com as ações desalinhadas do ciclo econômico.
    
    Args:
        alinhamento: Dicionário com análise de alinhamento da carteira.
        
    Returns:
        go.Figure: Figura do Plotly com a tabela de ações desalinhadas.
    """
    if not alinhamento or 'acoes_desalinhadas' not in alinhamento:
        # Retorna uma tabela vazia se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Dados de ações desalinhadas não disponíveis"
        )
        return fig
    
    # Obtém as ações desalinhadas
    acoes_desalinhadas = alinhamento['acoes_desalinhadas']
    
    if not acoes_desalinhadas:
        # Retorna uma tabela vazia se não houver ações desalinhadas
        fig = go.Figure()
        fig.update_layout(
            title="Não há ações desalinhadas do ciclo atual"
        )
        return fig
    
    # Cria uma tabela com as ações desalinhadas
    fig = go.Figure(data=[
        go.Table(
            header=dict(
                values=["Ticker", "Setor", "Justificativa"],
                fill_color="#F44336",
                align="left",
                font=dict(color="white", size=14)
            ),
            cells=dict(
                values=[
                    [acao['ticker'] for acao in acoes_desalinhadas],
                    [acao['setor'] for acao in acoes_desalinhadas],
                    [acao['justificativa'] for acao in acoes_desalinhadas]
                ],
                fill_color="#F5F5F5",
                align="left",
                font=dict(size=12)
            )
        )
    ])
    
    # Configura o layout
    fig.update_layout(
        title="Ações Desalinhadas do Ciclo Econômico Atual",
        height=300 + 30 * len(acoes_desalinhadas)  # Ajusta a altura com base no número de ações
    )
    
    return fig

def criar_tabela_recomendacoes_ajuste(alinhamento: Dict[str, Union[float, Dict, List]]) -> go.Figure:
    """
    Cria uma tabela com as recomendações de ajuste da carteira.
    
    Args:
        alinhamento: Dicionário com análise de alinhamento da carteira.
        
    Returns:
        go.Figure: Figura do Plotly com a tabela de recomendações de ajuste.
    """
    if not alinhamento or 'recomendacoes' not in alinhamento:
        # Retorna uma tabela vazia se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Dados de recomendações de ajuste não disponíveis"
        )
        return fig
    
    # Obtém as recomendações de ajuste
    recomendacoes = alinhamento['recomendacoes']
    
    if not recomendacoes:
        # Retorna uma tabela vazia se não houver recomendações
        fig = go.Figure()
        fig.update_layout(
            title="Não há recomendações de ajuste para a carteira"
        )
        return fig
    
    # Cria uma tabela com as recomendações de ajuste
    fig = go.Figure(data=[
        go.Table(
            header=dict(
                values=["Tipo", "Setor", "Atual (%)", "Recomendado (%)", "Diferença (%)", "Justificativa"],
                fill_color="#1E88E5",
                align="left",
                font=dict(color="white", size=14)
            ),
            cells=dict(
                values=[
                    [rec['tipo'] for rec in recomendacoes],
                    [rec['setor'] for rec in recomendacoes],
                    [rec['atual'] for rec in recomendacoes],
                    [rec['recomendado'] for rec in recomendacoes],
                    [rec['diferenca'] for rec in recomendacoes],
                    [rec['justificativa'] for rec in recomendacoes]
                ],
                fill_color=[
                    ["#F5F5F5"] * len(recomendacoes),
                    ["#F5F5F5"] * len(recomendacoes),
                    ["#F5F5F5"] * len(recomendacoes),
                    ["#F5F5F5"] * len(recomendacoes),
                    [
                        "#4CAF50" if rec['tipo'] == 'Aumentar' else "#F44336" if rec['tipo'] == 'Reduzir' else "#FFC107"
                        for rec in recomendacoes
                    ],
                    ["#F5F5F5"] * len(recomendacoes)
                ],
                align="left",
                font=dict(size=12)
            )
        )
    ])
    
    # Configura o layout
    fig.update_layout(
        title="Recomendações de Ajuste da Carteira",
        height=300 + 30 * len(recomendacoes)  # Ajusta a altura com base no número de recomendações
    )
    
    return fig

def criar_grafico_ajuste_risco(ajuste_risco: Dict[str, Union[str, float, List]]) -> go.Figure:
    """
    Cria um gráfico com as sugestões de ajuste de risco da carteira.
    
    Args:
        ajuste_risco: Dicionário com sugestões de ajuste de risco.
        
    Returns:
        go.Figure: Figura do Plotly com o gráfico de ajuste de risco.
    """
    if not ajuste_risco or 'ajustes_recomendados' not in ajuste_risco:
        # Retorna um gráfico vazio se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Dados de ajuste de risco não disponíveis"
        )
        return fig
    
    # Obtém os ajustes recomendados
    ajustes = ajuste_risco['ajustes_recomendados']
    
    # Filtra apenas os ajustes com percentual
    ajustes_percentual = [ajuste for ajuste in ajustes if 'percentual' in ajuste]
    
    if not ajustes_percentual:
        # Retorna um gráfico vazio se não houver ajustes com percentual
        fig = go.Figure()
        fig.update_layout(
            title="Dados de ajuste de risco não disponíveis"
        )
        return fig
    
    # Cria um gráfico de pizza com a alocação recomendada por categoria de risco
    labels = [ajuste['categoria'] for ajuste in ajustes_percentual]
    values = [ajuste['percentual'] for ajuste in ajustes_percentual]
    
    # Define cores para as categorias
    cores = {
        'Renda Variável': '#1E88E5',
        'Renda Fixa': '#4CAF50',
        'Caixa': '#FFC107'
    }
    
    cores_lista = [cores.get(label, '#9E9E9E') for label in labels]
    
    fig = go.Figure(data=[
        go.Pie(
            labels=labels,
            values=values,
            textinfo='label+percent',
            insidetextorientation='radial',
            marker=dict(colors=cores_lista),
            hole=0.3
        )
    ])
    
    # Configura o layout
    fig.update_layout(
        title=f"Ajuste de Risco Recomendado - Nível: {ajuste_risco['nivel_risco_recomendado']}",
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )
    
    # Adiciona anotação com o score de market timing
    if 'score_market_timing' in ajuste_risco:
        fig.add_annotation(
            x=0.5,
            y=0.5,
            text=f"Market Timing:\n{ajuste_risco['score_market_timing']:.1f}",
            showarrow=False,
            font=dict(size=14),
            align="center"
        )
    
    return fig

def criar_tabela_ajustes_especificos(ajuste_risco: Dict[str, Union[str, float, List]]) -> go.Figure:
    """
    Cria uma tabela com os ajustes específicos recomendados.
    
    Args:
        ajuste_risco: Dicionário com sugestões de ajuste de risco.
        
    Returns:
        go.Figure: Figura do Plotly com a tabela de ajustes específicos.
    """
    if not ajuste_risco or 'ajustes_recomendados' not in ajuste_risco:
        # Retorna uma tabela vazia se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Dados de ajustes específicos não disponíveis"
        )
        return fig
    
    # Obtém os ajustes recomendados
    ajustes = ajuste_risco['ajustes_recomendados']
    
    # Filtra apenas os ajustes sem percentual (específicos)
    ajustes_especificos = [ajuste for ajuste in ajustes if 'percentual' not in ajuste]
    
    if not ajustes_especificos:
        # Retorna uma tabela vazia se não houver ajustes específicos
        fig = go.Figure()
        fig.update_layout(
            title="Não há ajustes específicos recomendados"
        )
        return fig
    
    # Cria uma tabela com os ajustes específicos
    fig = go.Figure(data=[
        go.Table(
            header=dict(
                values=["Tipo", "Categoria", "Justificativa"],
                fill_color="#1E88E5",
                align="left",
                font=dict(color="white", size=14)
            ),
            cells=dict(
                values=[
                    [ajuste['tipo'] for ajuste in ajustes_especificos],
                    [ajuste['categoria'] for ajuste in ajustes_especificos],
                    [ajuste['justificativa'] for ajuste in ajustes_especificos]
                ],
                fill_color="#F5F5F5",
                align="left",
                font=dict(size=12)
            )
        )
    ])
    
    # Configura o layout
    fig.update_layout(
        title="Ajustes Específicos Recomendados",
        height=300 + 30 * len(ajustes_especificos)  # Ajusta a altura com base no número de ajustes
    )
    
    return fig

def criar_dashboard_alocacao(recomendacao: Dict[str, Union[str, Dict, List]],
                           alinhamento: Dict[str, Union[float, Dict, List]],
                           ajuste_risco: Dict[str, Union[str, float, List]]) -> Dict[str, go.Figure]:
    """
    Cria um dashboard completo com informações sobre alocação setorial.
    
    Args:
        recomendacao: Dicionário com recomendações de alocação.
        alinhamento: Dicionário com análise de alinhamento da carteira.
        ajuste_risco: Dicionário com sugestões de ajuste de risco.
        
    Returns:
        Dict[str, go.Figure]: Dicionário com figuras do Plotly para cada componente.
    """
    dashboard = {}
    
    # Cria gráfico de alocação recomendada
    dashboard['alocacao_recomendada'] = criar_grafico_alocacao_recomendada(recomendacao)
    
    # Cria gráfico de alinhamento da carteira
    dashboard['alinhamento_carteira'] = criar_grafico_alinhamento_carteira(alinhamento)
    
    # Cria gráfico comparativo de alocação
    dashboard['comparativo_alocacao'] = criar_grafico_comparativo_alocacao(alinhamento)
    
    # Cria tabela de ações alinhadas
    dashboard['acoes_alinhadas'] = criar_tabela_acoes_alinhadas(alinhamento)
    
    # Cria tabela de ações desalinhadas
    dashboard['acoes_desalinhadas'] = criar_tabela_acoes_desalinhadas(alinhamento)
    
    # Cria tabela de recomendações de ajuste
    dashboard['recomendacoes_ajuste'] = criar_tabela_recomendacoes_ajuste(alinhamento)
    
    # Cria gráfico de ajuste de risco
    dashboard['ajuste_risco'] = criar_grafico_ajuste_risco(ajuste_risco)
    
    # Cria tabela de ajustes específicos
    dashboard['ajustes_especificos'] = criar_tabela_ajustes_especificos(ajuste_risco)
    
    return dashboard
