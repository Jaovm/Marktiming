"""
Módulo para visualização de ciclo econômico e market timing.

Este módulo contém funções para criar gráficos e visualizações relacionados
ao ciclo econômico, market timing e alertas visuais.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple

def criar_grafico_ciclo_economico(ciclo: Dict[str, Union[str, float, Dict]]) -> go.Figure:
    """
    Cria um gráfico indicando a fase atual do ciclo econômico.
    
    Args:
        ciclo: Dicionário com informações sobre a fase do ciclo econômico.
        
    Returns:
        go.Figure: Figura do Plotly com o gráfico do ciclo econômico.
    """
    if not ciclo or 'fase' not in ciclo:
        # Retorna um gráfico vazio se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Dados do ciclo econômico não disponíveis"
        )
        return fig
    
    # Fases do ciclo econômico
    fases = ['EXPANSAO', 'PICO', 'CONTRACAO', 'RECUPERACAO']
    
    # Posições no círculo (ângulos em radianos)
    angulos = [0, np.pi/2, np.pi, 3*np.pi/2]
    
    # Coordenadas x e y no círculo
    x = [np.cos(angulo) for angulo in angulos]
    y = [np.sin(angulo) for angulo in angulos]
    
    # Cores para cada fase
    cores = {
        'EXPANSAO': '#4CAF50',  # Verde
        'PICO': '#FFC107',      # Amarelo
        'CONTRACAO': '#F44336', # Vermelho
        'RECUPERACAO': '#FFC107' # Amarelo
    }
    
    # Cria o gráfico
    fig = go.Figure()
    
    # Adiciona o círculo do ciclo econômico
    for i, fase in enumerate(fases):
        # Determina se é a fase atual
        e_fase_atual = fase == ciclo['fase']
        
        # Define o tamanho e a cor do marcador
        tamanho = 20 if e_fase_atual else 10
        cor = cores[fase]
        
        # Adiciona o ponto da fase
        fig.add_trace(
            go.Scatter(
                x=[x[i]],
                y=[y[i]],
                mode='markers+text',
                name=fase,
                text=[fase.capitalize()],
                textposition="middle center" if e_fase_atual else "top center",
                marker=dict(
                    size=tamanho,
                    color=cor,
                    line=dict(width=2, color='black') if e_fase_atual else dict(width=1, color='black')
                )
            )
        )
    
    # Adiciona linhas conectando as fases
    fig.add_trace(
        go.Scatter(
            x=x + [x[0]],  # Fecha o círculo
            y=y + [y[0]],  # Fecha o círculo
            mode='lines',
            line=dict(color='gray', width=1),
            showlegend=False
        )
    )
    
    # Adiciona seta indicando a direção do ciclo
    for i in range(len(fases)):
        # Pontos médios entre as fases
        x_mid = (x[i] + x[(i+1) % len(fases)]) / 2
        y_mid = (y[i] + y[(i+1) % len(fases)]) / 2
        
        # Normaliza para obter um ponto um pouco mais próximo do centro
        norm = np.sqrt(x_mid**2 + y_mid**2)
        x_arrow = 0.8 * x_mid / norm
        y_arrow = 0.8 * y_mid / norm
        
        # Adiciona a seta
        fig.add_annotation(
            x=x_arrow,
            y=y_arrow,
            ax=x_mid,
            ay=y_mid,
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=1,
            arrowcolor="gray"
        )
    
    # Configura o layout
    fig.update_layout(
        title=f"Ciclo Econômico - Fase Atual: {ciclo['fase'].capitalize()}",
        xaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            range=[-1.2, 1.2]
        ),
        yaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            range=[-1.2, 1.2]
        ),
        template="plotly_white",
        height=500,
        width=500,
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Adiciona anotação com a descrição da fase atual
    if 'descricao' in ciclo:
        fig.add_annotation(
            x=0,
            y=-1.1,
            text=ciclo['descricao'],
            showarrow=False,
            font=dict(size=12),
            align="center"
        )
    
    # Adiciona anotação com o nível de confiança
    if 'confianca' in ciclo:
        fig.add_annotation(
            x=0,
            y=1.1,
            text=f"Confiança: {ciclo['confianca']:.1f}%",
            showarrow=False,
            font=dict(size=12),
            align="center"
        )
    
    return fig

def criar_grafico_market_timing(timing: Dict[str, Union[float, str, Dict]]) -> go.Figure:
    """
    Cria um gráfico com o score de market timing.
    
    Args:
        timing: Dicionário com informações sobre o market timing.
        
    Returns:
        go.Figure: Figura do Plotly com o gráfico de market timing.
    """
    if not timing or 'score' not in timing:
        # Retorna um gráfico vazio se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Dados de market timing não disponíveis"
        )
        return fig
    
    # Cria um gráfico de gauge para o score de market timing
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=timing['score'],
        domain=dict(x=[0, 1], y=[0, 1]),
        title=dict(text="Market Timing Score", font=dict(size=16)),
        delta=dict(reference=0),
        gauge=dict(
            axis=dict(range=[-100, 100]),
            bar=dict(color=timing.get('cor', '#1E88E5')),
            bgcolor="white",
            borderwidth=2,
            bordercolor="gray",
            steps=[
                dict(range=[-100, -70], color="#F44336"),  # Vermelho
                dict(range=[-70, -30], color="#FF9800"),   # Laranja
                dict(range=[-30, 30], color="#FFC107"),    # Amarelo
                dict(range=[30, 70], color="#8BC34A"),     # Verde claro
                dict(range=[70, 100], color="#4CAF50")     # Verde
            ],
            threshold=dict(
                line=dict(color="black", width=4),
                thickness=0.75,
                value=timing['score']
            )
        )
    ))
    
    # Configura o layout
    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    # Adiciona anotação com a recomendação
    if 'recomendacao' in timing:
        fig.add_annotation(
            x=0.5,
            y=0.2,
            text=f"Recomendação: {timing['recomendacao']}",
            showarrow=False,
            font=dict(size=16, color=timing.get('cor', '#1E88E5')),
            align="center",
            xref="paper",
            yref="paper"
        )
    
    return fig

def criar_grafico_alertas(alertas: List[Dict[str, str]]) -> go.Figure:
    """
    Cria um gráfico com os alertas de market timing.
    
    Args:
        alertas: Lista de dicionários com informações sobre os alertas.
        
    Returns:
        go.Figure: Figura do Plotly com o gráfico de alertas.
    """
    if not alertas:
        # Retorna um gráfico vazio se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Alertas não disponíveis"
        )
        return fig
    
    # Cria uma tabela com os alertas
    fig = go.Figure(data=[
        go.Table(
            header=dict(
                values=["Tipo", "Mensagem", "Importância"],
                fill_color="#1E88E5",
                align="left",
                font=dict(color="white", size=14)
            ),
            cells=dict(
                values=[
                    [alerta['tipo'] for alerta in alertas],
                    [alerta['mensagem'] for alerta in alertas],
                    [alerta['importancia'] for alerta in alertas]
                ],
                fill_color=[
                    ["#F5F5F5"] * len(alertas),
                    [alerta['cor'] for alerta in alertas],
                    ["#F5F5F5"] * len(alertas)
                ],
                align="left",
                font=dict(size=12)
            )
        )
    ])
    
    # Configura o layout
    fig.update_layout(
        title="Alertas de Market Timing",
        height=300 + 30 * len(alertas)  # Ajusta a altura com base no número de alertas
    )
    
    return fig

def criar_grafico_inclinacao_curva(inclinacao_curva: Dict[str, float]) -> go.Figure:
    """
    Cria um gráfico com a inclinação da curva de juros.
    
    Args:
        inclinacao_curva: Dicionário com métricas de inclinação da curva de juros.
        
    Returns:
        go.Figure: Figura do Plotly com o gráfico de inclinação da curva.
    """
    if not inclinacao_curva or 'status_curva' not in inclinacao_curva:
        # Retorna um gráfico vazio se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Dados de inclinação da curva não disponíveis"
        )
        return fig
    
    # Cria um gráfico de barras com as inclinações
    fig = go.Figure()
    
    # Adiciona barras para cada métrica de inclinação
    metricas = []
    valores = []
    
    if 'inclinacao_1y_1m' in inclinacao_curva:
        metricas.append("1 ano - 1 mês")
        valores.append(inclinacao_curva['inclinacao_1y_1m'])
    
    if 'inclinacao_3y_1y' in inclinacao_curva:
        metricas.append("3 anos - 1 ano")
        valores.append(inclinacao_curva['inclinacao_3y_1y'])
    
    if 'inclinacao_3y_1m' in inclinacao_curva:
        metricas.append("3 anos - 1 mês")
        valores.append(inclinacao_curva['inclinacao_3y_1m'])
    
    # Define cores com base nos valores
    cores = []
    for valor in valores:
        if valor > 0.5:
            cores.append('#4CAF50')  # Verde
        elif valor > -0.5:
            cores.append('#FFC107')  # Amarelo
        else:
            cores.append('#F44336')  # Vermelho
    
    fig.add_trace(
        go.Bar(
            x=metricas,
            y=valores,
            marker_color=cores
        )
    )
    
    # Adiciona linha horizontal em zero
    fig.add_shape(
        type="line",
        x0=-0.5,
        y0=0,
        x1=len(metricas) - 0.5,
        y1=0,
        line=dict(
            color="black",
            width=1,
            dash="dash",
        )
    )
    
    # Configura o layout
    status = inclinacao_curva['status_curva']
    cor_status = '#4CAF50' if status == 'Normal' else '#FFC107' if status == 'Achatada' else '#F44336'
    
    fig.update_layout(
        title=f"Inclinação da Curva de Juros - Status: {status}",
        xaxis_title="Métrica",
        yaxis_title="Inclinação (p.p.)",
        template="plotly_white",
        height=400
    )
    
    # Adiciona anotação com o status da curva
    fig.add_annotation(
        x=0.5,
        y=1.05,
        text=f"Status da Curva: {status}",
        showarrow=False,
        font=dict(size=14, color=cor_status),
        align="center",
        xref="paper",
        yref="paper"
    )
    
    return fig

def criar_grafico_componentes_ciclo(ciclo: Dict[str, Union[str, float, Dict]]) -> go.Figure:
    """
    Cria um gráfico com os componentes que influenciam o ciclo econômico.
    
    Args:
        ciclo: Dicionário com informações sobre a fase do ciclo econômico.
        
    Returns:
        go.Figure: Figura do Plotly com o gráfico dos componentes do ciclo.
    """
    if not ciclo or 'scores' not in ciclo:
        # Retorna um gráfico vazio se não houver dados
        fig = go.Figure()
        fig.update_layout(
            title="Dados dos componentes do ciclo não disponíveis"
        )
        return fig
    
    # Obtém os scores para cada fase
    scores = ciclo['scores']
    
    # Cria um gráfico de barras com os scores
    fig = go.Figure()
    
    # Adiciona barras para cada fase
    fases = list(scores.keys())
    valores = list(scores.values())
    
    # Define cores para cada fase
    cores = {
        'EXPANSAO': '#4CAF50',  # Verde
        'PICO': '#FFC107',      # Amarelo
        'CONTRACAO': '#F44336', # Vermelho
        'RECUPERACAO': '#FFC107' # Amarelo
    }
    
    cores_barras = [cores[fase] for fase in fases]
    
    fig.add_trace(
        go.Bar(
            x=fases,
            y=valores,
            marker_color=cores_barras
        )
    )
    
    # Configura o layout
    fig.update_layout(
        title="Scores por Fase do Ciclo Econômico",
        xaxis_title="Fase",
        yaxis_title="Score",
        template="plotly_white",
        height=400
    )
    
    # Destaca a fase atual
    fase_atual = ciclo['fase']
    fig.add_annotation(
        x=fase_atual,
        y=scores[fase_atual],
        text="Fase Atual",
        showarrow=True,
        arrowhead=1,
        ax=0,
        ay=-40
    )
    
    return fig

def criar_dashboard_ciclo(ciclo: Dict[str, Union[str, float, Dict]], 
                         timing: Dict[str, Union[float, str, Dict]],
                         alertas: List[Dict[str, str]]) -> Dict[str, go.Figure]:
    """
    Cria um dashboard completo com informações sobre o ciclo econômico e market timing.
    
    Args:
        ciclo: Dicionário com informações sobre a fase do ciclo econômico.
        timing: Dicionário com informações sobre o market timing.
        alertas: Lista de dicionários com informações sobre os alertas.
        
    Returns:
        Dict[str, go.Figure]: Dicionário com figuras do Plotly para cada componente.
    """
    dashboard = {}
    
    # Cria gráfico do ciclo econômico
    dashboard['ciclo'] = criar_grafico_ciclo_economico(ciclo)
    
    # Cria gráfico de market timing
    dashboard['timing'] = criar_grafico_market_timing(timing)
    
    # Cria gráfico de alertas
    dashboard['alertas'] = criar_grafico_alertas(alertas)
    
    # Cria gráfico de inclinação da curva
    if 'detalhes' in ciclo and 'curva_juros' in ciclo['detalhes']:
        dashboard['inclinacao_curva'] = criar_grafico_inclinacao_curva(ciclo['detalhes']['curva_juros'])
    
    # Cria gráfico de componentes do ciclo
    dashboard['componentes'] = criar_grafico_componentes_ciclo(ciclo)
    
    return dashboard
