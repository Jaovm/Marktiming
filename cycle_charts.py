"""
Módulo para visualização de dados do ciclo econômico e market timing.

Este módulo contém funções para criar gráficos e visualizações
relacionados ao ciclo econômico e market timing.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Union

def criar_dashboard_ciclo(ciclo: Dict, timing: Dict, alertas: List[Dict]) -> Dict[str, go.Figure]:
    """
    Cria um dashboard com gráficos do ciclo econômico e market timing.
    
    Args:
        ciclo: Dicionário com informações sobre a fase do ciclo econômico.
        timing: Dicionário com informações sobre o score de market timing.
        alertas: Lista de alertas de market timing.
        
    Returns:
        Dict[str, go.Figure]: Dicionário com os gráficos do dashboard.
    """
    # Inicializa o dicionário de gráficos
    graficos = {}
    
    # Gráfico do ciclo econômico
    fig_ciclo = go.Figure()
    
    # Cria um gráfico circular para representar o ciclo econômico
    fases = ['EXPANSAO', 'PICO', 'CONTRACAO', 'RECUPERACAO']
    cores = ['#4CAF50', '#FFC107', '#F44336', '#2196F3']
    
    # Adiciona um setor para cada fase do ciclo
    for i, fase in enumerate(fases):
        # Destaca a fase atual
        opacidade = 1.0 if fase == ciclo['fase'] else 0.3
        
        fig_ciclo.add_trace(
            go.Pie(
                labels=[fase],
                values=[1],
                name=fase,
                marker=dict(colors=[cores[i]]),
                opacity=opacidade,
                textinfo='label',
                textposition='inside',
                textfont=dict(size=14, color='white'),
                hoverinfo='label+text',
                text=[fase],
                hole=0.3
            )
        )
    
    # Adiciona um texto no centro do gráfico
    fig_ciclo.update_layout(
        title="Fase Atual do Ciclo Econômico",
        annotations=[dict(
            text=ciclo['fase'],
            x=0.5,
            y=0.5,
            font=dict(size=20, color=ciclo['cor_alerta']),
            showarrow=False
        )],
        showlegend=False
    )
    
    # Adiciona o gráfico ao dicionário
    graficos['ciclo'] = fig_ciclo
    
    # Gráfico dos componentes do ciclo
    if 'scores' in ciclo:
        fig_componentes = go.Figure()
        
        # Adiciona uma barra para cada fase
        for fase, score in ciclo['scores'].items():
            cor = {
                'EXPANSAO': '#4CAF50',
                'PICO': '#FFC107',
                'CONTRACAO': '#F44336',
                'RECUPERACAO': '#2196F3'
            }.get(fase, '#CCCCCC')
            
            fig_componentes.add_trace(
                go.Bar(
                    x=[fase],
                    y=[score],
                    name=fase,
                    marker_color=cor
                )
            )
        
        # Configura o layout
        fig_componentes.update_layout(
            title="Pontuação de Cada Fase do Ciclo",
            xaxis_title="Fase",
            yaxis_title="Pontuação",
            showlegend=False
        )
        
        # Adiciona o gráfico ao dicionário
        graficos['componentes'] = fig_componentes
    
    # Gráfico do score de market timing
    fig_timing = go.Figure()
    
    # Cria um gráfico de gauge para o score de market timing
    fig_timing.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=timing['score'],
            title={"text": f"Market Timing: {timing['recomendacao']}"},
            gauge={
                'axis': {'range': [-100, 100]},
                'bar': {'color': timing['cor']},
                'steps': [
                    {'range': [-100, -70], 'color': '#F44336'},
                    {'range': [-70, -30], 'color': '#FF9800'},
                    {'range': [-30, 30], 'color': '#FFC107'},
                    {'range': [30, 70], 'color': '#8BC34A'},
                    {'range': [70, 100], 'color': '#4CAF50'}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': timing['score']
                }
            }
        )
    )
    
    # Configura o layout
    fig_timing.update_layout(
        title="Score de Market Timing",
        height=400
    )
    
    # Adiciona o gráfico ao dicionário
    graficos['timing'] = fig_timing
    
    # Gráfico dos alertas
    fig_alertas = go.Figure()
    
    # Cria uma tabela com os alertas
    if alertas:
        # Extrai os dados dos alertas
        tipos = [alerta['tipo'] for alerta in alertas]
        mensagens = [alerta['mensagem'] for alerta in alertas]
        cores = [alerta['cor'] for alerta in alertas]
        
        # Cria células coloridas para os tipos de alerta
        cell_colors = []
        for i in range(len(alertas)):
            cell_colors.append([cores[i], 'white'])
        
        # Cria a tabela
        fig_alertas = go.Figure(data=[go.Table(
            header=dict(
                values=['Tipo', 'Mensagem'],
                fill_color='#1E88E5',
                align='left',
                font=dict(color='white', size=12)
            ),
            cells=dict(
                values=[tipos, mensagens],
                fill_color=cell_colors,
                align='left'
            )
        )])
    
    # Configura o layout
    fig_alertas.update_layout(
        title="Alertas de Market Timing",
        height=400
    )
    
    # Adiciona o gráfico ao dicionário
    graficos['alertas'] = fig_alertas
    
    # Gráfico da inclinação da curva de juros
    if 'detalhes' in ciclo and 'curva_juros' in ciclo['detalhes']:
        curva_juros = ciclo['detalhes']['curva_juros']
        
        if 'inclinacao_1y_1m' in curva_juros and 'inclinacao_3y_1y' in curva_juros:
            fig_inclinacao = go.Figure()
            
            # Adiciona barras para as inclinações
            fig_inclinacao.add_trace(
                go.Bar(
                    x=['1 ano - 1 mês'],
                    y=[curva_juros['inclinacao_1y_1m']],
                    name='1 ano - 1 mês',
                    marker_color='#1E88E5'
                )
            )
            
            fig_inclinacao.add_trace(
                go.Bar(
                    x=['3 anos - 1 ano'],
                    y=[curva_juros['inclinacao_3y_1y']],
                    name='3 anos - 1 ano',
                    marker_color='#4CAF50'
                )
            )
            
            fig_inclinacao.add_trace(
                go.Bar(
                    x=['3 anos - 1 mês'],
                    y=[curva_juros['inclinacao_3y_1m']],
                    name='3 anos - 1 mês',
                    marker_color='#FFC107'
                )
            )
            
            # Adiciona uma linha horizontal em zero
            fig_inclinacao.add_shape(
                type='line',
                x0=-0.5,
                y0=0,
                x1=2.5,
                y1=0,
                line=dict(color='red', width=2, dash='dash')
            )
            
            # Configura o layout
            fig_inclinacao.update_layout(
                title="Inclinação da Curva de Juros (pontos percentuais)",
                xaxis_title="",
                yaxis_title="Inclinação (p.p.)",
                showlegend=False
            )
            
            # Adiciona o gráfico ao dicionário
            graficos['inclinacao_curva'] = fig_inclinacao
    
    return graficos
