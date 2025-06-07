"""
Módulo para visualização de dados de alocação setorial.

Este módulo contém funções para criar gráficos e visualizações
relacionados à recomendação de alocação setorial e análise de carteira.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Union

def criar_dashboard_alocacao(recomendacao: Dict, alinhamento: Dict, ajuste_risco: Dict) -> Dict[str, go.Figure]:
    """
    Cria um dashboard com gráficos de recomendação de alocação setorial.
    
    Args:
        recomendacao: Dicionário com recomendações de alocação setorial.
        alinhamento: Dicionário com análise de alinhamento da carteira.
        ajuste_risco: Dicionário com sugestões de ajuste de risco.
        
    Returns:
        Dict[str, go.Figure]: Dicionário com os gráficos do dashboard.
    """
    # Inicializa o dicionário de gráficos
    graficos = {}
    
    # Gráfico da alocação recomendada
    if 'alocacao_recomendada' in recomendacao:
        # Cria um DataFrame com a alocação recomendada
        df_alocacao = pd.DataFrame({
            'Setor': list(recomendacao['alocacao_recomendada'].keys()),
            'Alocação (%)': list(recomendacao['alocacao_recomendada'].values())
        }).sort_values(by='Alocação (%)', ascending=False)
        
        # Cria o gráfico de pizza
        fig_alocacao = px.pie(
            df_alocacao,
            values='Alocação (%)',
            names='Setor',
            title=f"Alocação Setorial Recomendada - Fase: {recomendacao['fase_ciclo'].capitalize()}",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        # Configura o layout
        fig_alocacao.update_traces(textposition='inside', textinfo='percent+label')
        fig_alocacao.update_layout(
            uniformtext_minsize=12,
            uniformtext_mode='hide'
        )
        
        # Adiciona o gráfico ao dicionário
        graficos['alocacao_recomendada'] = fig_alocacao
    
    # Gráfico do ajuste de risco
    if 'nivel_risco_recomendado' in ajuste_risco and 'sugestoes' in ajuste_risco:
        # Cria um gráfico de gauge para o nível de risco
        nivel_risco = ajuste_risco['nivel_risco_recomendado']
        
        # Mapeia o nível de risco para um valor numérico
        mapa_risco = {
            'Muito Baixo': 10,
            'Baixo': 30,
            'Baixo para Moderado': 45,
            'Moderado': 60,
            'Moderado para Alto': 75,
            'Alto': 90
        }
        
        valor_risco = mapa_risco.get(nivel_risco, 50)
        
        fig_risco = go.Figure()
        
        fig_risco.add_trace(
            go.Indicator(
                mode="gauge+number+delta",
                value=valor_risco,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': f"Nível de Risco: {nivel_risco}"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#1E88E5"},
                    'steps': [
                        {'range': [0, 20], 'color': "#4CAF50"},
                        {'range': [20, 40], 'color': "#8BC34A"},
                        {'range': [40, 60], 'color': "#FFC107"},
                        {'range': [60, 80], 'color': "#FF9800"},
                        {'range': [80, 100], 'color': "#F44336"}
                    ],
                    'threshold': {
                        'line': {'color': "black", 'width': 4},
                        'thickness': 0.75,
                        'value': valor_risco
                    }
                }
            )
        )
        
        # Configura o layout
        fig_risco.update_layout(
            title="Nível de Risco Recomendado",
            height=400
        )
        
        # Adiciona o gráfico ao dicionário
        graficos['ajuste_risco'] = fig_risco
        
        # Cria uma tabela com as sugestões de ajuste
        fig_ajustes = go.Figure(data=[go.Table(
            header=dict(
                values=['Sugestões de Ajuste'],
                fill_color='#1E88E5',
                align='left',
                font=dict(color='white', size=12)
            ),
            cells=dict(
                values=[ajuste_risco['sugestoes']],
                fill_color='lavender',
                align='left'
            )
        )])
        
        # Configura o layout
        fig_ajustes.update_layout(
            title="Sugestões de Ajuste de Risco",
            height=400
        )
        
        # Adiciona o gráfico ao dicionário
        graficos['ajustes_especificos'] = fig_ajustes
    
    # Gráfico do alinhamento da carteira
    if 'alinhamento_score' in alinhamento and 'alocacao_atual' in alinhamento and 'alocacao_recomendada' in alinhamento:
        # Cria um gráfico de gauge para o alinhamento
        fig_alinhamento = go.Figure()
        
        fig_alinhamento.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=alinhamento['alinhamento_score'],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Alinhamento da Carteira ao Ciclo"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#1E88E5"},
                    'steps': [
                        {'range': [0, 30], 'color': "#F44336"},
                        {'range': [30, 70], 'color': "#FFC107"},
                        {'range': [70, 100], 'color': "#4CAF50"}
                    ],
                    'threshold': {
                        'line': {'color': "black", 'width': 4},
                        'thickness': 0.75,
                        'value': alinhamento['alinhamento_score']
                    }
                }
            )
        )
        
        # Configura o layout
        fig_alinhamento.update_layout(
            title="Score de Alinhamento da Carteira (%)",
            height=400
        )
        
        # Adiciona o gráfico ao dicionário
        graficos['alinhamento_carteira'] = fig_alinhamento
        
        # Cria um gráfico de barras comparando a alocação atual com a recomendada
        setores = list(set(list(alinhamento['alocacao_atual'].keys()) + list(alinhamento['alocacao_recomendada'].keys())))
        alocacao_atual = [alinhamento['alocacao_atual'].get(setor, 0) for setor in setores]
        alocacao_recomendada = [alinhamento['alocacao_recomendada'].get(setor, 0) for setor in setores]
        
        fig_comparativo = go.Figure()
        
        fig_comparativo.add_trace(
            go.Bar(
                x=setores,
                y=alocacao_atual,
                name='Alocação Atual',
                marker_color='#1E88E5'
            )
        )
        
        fig_comparativo.add_trace(
            go.Bar(
                x=setores,
                y=alocacao_recomendada,
                name='Alocação Recomendada',
                marker_color='#4CAF50'
            )
        )
        
        # Configura o layout
        fig_comparativo.update_layout(
            title="Comparativo: Alocação Atual vs. Recomendada",
            xaxis_title="Setor",
            yaxis_title="Alocação (%)",
            barmode='group',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        # Adiciona o gráfico ao dicionário
        graficos['comparativo_alocacao'] = fig_comparativo
    
    # Gráfico das ações alinhadas e desalinhadas
    if 'acoes_alinhadas' in alinhamento and 'acoes_desalinhadas' in alinhamento:
        # Cria um gráfico para as ações alinhadas
        if alinhamento['acoes_alinhadas']:
            # Extrai os dados
            tickers = [acao['ticker'] for acao in alinhamento['acoes_alinhadas']]
            pesos = [acao['peso'] for acao in alinhamento['acoes_alinhadas']]
            setores = [acao['setor'] for acao in alinhamento['acoes_alinhadas']]
            
            # Cria o gráfico
            fig_alinhadas = px.bar(
                x=tickers,
                y=pesos,
                color=setores,
                title="Ações Alinhadas ao Ciclo",
                labels={'x': 'Ação', 'y': 'Peso na Carteira (%)'}
            )
            
            # Configura o layout
            fig_alinhadas.update_layout(
                showlegend=True,
                xaxis_tickangle=-45
            )
            
            # Adiciona o gráfico ao dicionário
            graficos['acoes_alinhadas'] = fig_alinhadas
        
        # Cria um gráfico para as ações desalinhadas
        if alinhamento['acoes_desalinhadas']:
            # Extrai os dados
            tickers = [acao['ticker'] for acao in alinhamento['acoes_desalinhadas']]
            pesos = [acao['peso'] for acao in alinhamento['acoes_desalinhadas']]
            setores = [acao['setor'] for acao in alinhamento['acoes_desalinhadas']]
            
            # Cria o gráfico
            fig_desalinhadas = px.bar(
                x=tickers,
                y=pesos,
                color=setores,
                title="Ações Desalinhadas do Ciclo",
                labels={'x': 'Ação', 'y': 'Peso na Carteira (%)'}
            )
            
            # Configura o layout
            fig_desalinhadas.update_layout(
                showlegend=True,
                xaxis_tickangle=-45
            )
            
            # Adiciona o gráfico ao dicionário
            graficos['acoes_desalinhadas'] = fig_desalinhadas
    
    # Gráfico de recomendações de ajuste
    if 'acoes_alinhadas' in alinhamento and 'acoes_desalinhadas' in alinhamento:
        # Cria uma lista de recomendações
        recomendacoes = []
        
        # Recomendações para ações desalinhadas
        for acao in alinhamento['acoes_desalinhadas']:
            recomendacoes.append({
                'Ação': acao['ticker'],
                'Recomendação': 'Reduzir',
                'Justificativa': f"Setor {acao['setor']} desalinhado com a fase atual do ciclo"
            })
        
        # Recomendações para ações alinhadas
        for acao in alinhamento['acoes_alinhadas'][:3]:  # Limita a 3 recomendações
            recomendacoes.append({
                'Ação': acao['ticker'],
                'Recomendação': 'Aumentar',
                'Justificativa': f"Setor {acao['setor']} alinhado com a fase atual do ciclo"
            })
        
        # Cria uma tabela com as recomendações
        if recomendacoes:
            fig_recomendacoes = go.Figure(data=[go.Table(
                header=dict(
                    values=['Ação', 'Recomendação', 'Justificativa'],
                    fill_color='#1E88E5',
                    align='left',
                    font=dict(color='white', size=12)
                ),
                cells=dict(
                    values=[
                        [r['Ação'] for r in recomendacoes],
                        [r['Recomendação'] for r in recomendacoes],
                        [r['Justificativa'] for r in recomendacoes]
                    ],
                    fill_color=[
                        'white',
                        ['#F44336' if r['Recomendação'] == 'Reduzir' else '#4CAF50' for r in recomendacoes],
                        'white'
                    ],
                    align='left',
                    font=dict(color=['black', 'white', 'black'])
                )
            )])
            
            # Configura o layout
            fig_recomendacoes.update_layout(
                title="Recomendações de Ajuste da Carteira",
                height=400
            )
            
            # Adiciona o gráfico ao dicionário
            graficos['recomendacoes_ajuste'] = fig_recomendacoes
    
    return graficos
