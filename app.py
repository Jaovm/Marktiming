"""
Módulo principal do aplicativo Streamlit para o Painel Inteligente de Market Timing e Análise Macroeconômica.

Este módulo contém a configuração principal do Streamlit e a estrutura de navegação
entre as diferentes páginas do dashboard.
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
from datetime import datetime

# Adiciona o diretório raiz ao path para importar os módulos do projeto
sys.path.insert(0, str(Path(__file__).parent.parent))

# Importa os módulos do projeto
from config import THEME, SETORES_B3, CARTEIRA_BASE
from data.macro_data import get_all_macro_data, get_macro_summary
from data.market_data import (
    get_index_data, get_sector_data, get_sector_valuation,
    get_fed_model_data, get_market_summary, get_portfolio_data
)
from analysis.valuation import (
    calcular_premio_risco, classificar_valuation_setorial,
    comparar_setores_historico, analisar_carteira
)
from analysis.cycle import (
    identificar_fase_ciclo, calcular_market_timing_score,
    gerar_alertas_market_timing
)
from analysis.allocation import (
    recomendar_alocacao_setorial, analisar_alinhamento_carteira,
    sugerir_ajuste_risco_carteira
)
from visualization.macro_charts import criar_dashboard_macro, criar_tabela_resumo_macro
from visualization.market_charts import criar_dashboard_mercado, criar_tabela_resumo_mercado
from visualization.cycle_charts import criar_dashboard_ciclo
from visualization.allocation_charts import criar_dashboard_alocacao

# Configuração da página
st.set_page_config(
    page_title="Painel de Market Timing e Análise Macroeconômica",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Função para aplicar o tema personalizado
def aplicar_tema():
    """
    Aplica o tema personalizado ao Streamlit usando CSS.
    """
    st.markdown(
        f"""
        <style>
        :root {{
            --primary-color: {THEME['primary']};
            --secondary-color: {THEME['secondary']};
            --background-color: {THEME['background']};
            --text-color: {THEME['text']};
            --positive-color: {THEME['positive']};
            --negative-color: {THEME['negative']};
            --neutral-color: {THEME['neutral']};
        }}
        
        .stApp {{
            background-color: var(--background-color);
            color: var(--text-color);
        }}
        
        .stButton>button {{
            background-color: var(--primary-color);
            color: white;
        }}
        
        .positive {{
            color: var(--positive-color);
        }}
        
        .negative {{
            color: var(--negative-color);
        }}
        
        .neutral {{
            color: var(--neutral-color);
        }}
        
        .card {{
            background-color: white;
            border-radius: 5px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }}
        
        .header {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 20px;
            color: var(--primary-color);
        }}
        
        .subheader {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
            color: var(--secondary-color);
        }}
        
        .tooltip {{
            position: relative;
            display: inline-block;
            border-bottom: 1px dotted black;
            cursor: help;
        }}
        
        .tooltip .tooltiptext {{
            visibility: hidden;
            width: 200px;
            background-color: #555;
            color: #fff;
            text-align: center;
            border-radius: 6px;
            padding: 5px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            margin-left: -100px;
            opacity: 0;
            transition: opacity 0.3s;
        }}
        
        .tooltip:hover .tooltiptext {{
            visibility: visible;
            opacity: 1;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Função para criar um card
def criar_card(titulo, conteudo):
    """
    Cria um card com título e conteúdo.
    
    Args:
        titulo: Título do card.
        conteudo: Conteúdo do card (HTML).
    """
    st.markdown(
        f"""
        <div class="card">
            <div class="header">{titulo}</div>
            {conteudo}
        </div>
        """,
        unsafe_allow_html=True
    )

# Função para criar um tooltip
def criar_tooltip(texto, explicacao):
    """
    Cria um tooltip com explicação.
    
    Args:
        texto: Texto a ser exibido.
        explicacao: Explicação a ser mostrada no tooltip.
    """
    return f"""
    <div class="tooltip">{texto}
        <span class="tooltiptext">{explicacao}</span>
    </div>
    """

# Função para formatar valores
def formatar_valor(valor, tipo="numero", precisao=2):
    """
    Formata um valor para exibição.
    
    Args:
        valor: Valor a ser formatado.
        tipo: Tipo de formatação ("numero", "percentual", "moeda").
        precisao: Número de casas decimais.
        
    Returns:
        str: Valor formatado.
    """
    if pd.isna(valor):
        return "N/A"
    
    if tipo == "percentual":
        return f"{valor:.{precisao}f}%"
    elif tipo == "moeda":
        return f"R$ {valor:,.{precisao}f}"
    else:
        return f"{valor:,.{precisao}f}"

# Função para exibir indicador com seta
def exibir_indicador(valor, titulo, formato="numero", precisao=2, delta=None):
    """
    Exibe um indicador com seta de tendência.
    
    Args:
        valor: Valor a ser exibido.
        titulo: Título do indicador.
        formato: Formato do valor ("numero", "percentual", "moeda").
        precisao: Número de casas decimais.
        delta: Variação para determinar a direção da seta.
    """
    # Formata o valor
    valor_formatado = formatar_valor(valor, formato, precisao)
    
    # Determina a direção da seta
    if delta is not None:
        if delta > 0:
            delta_color = "positive"
            delta_icon = "↑"
        elif delta < 0:
            delta_color = "negative"
            delta_icon = "↓"
        else:
            delta_color = "neutral"
            delta_icon = "→"
        
        delta_formatado = formatar_valor(abs(delta), formato, precisao)
        delta_html = f'<span class="{delta_color}">{delta_icon} {delta_formatado}</span>'
    else:
        delta_html = ""
    
    # Cria o HTML do indicador
    html = f"""
    <div style="text-align: center;">
        <div style="font-size: 14px; color: gray;">{titulo}</div>
        <div style="font-size: 24px; font-weight: bold;">{valor_formatado} {delta_html}</div>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)

# Função para carregar dados
@st.cache_data(ttl=3600)  # Cache por 1 hora
def carregar_dados():
    """
    Carrega todos os dados necessários para o dashboard.
    
    Returns:
        dict: Dicionário com todos os dados.
    """
    # Dados macroeconômicos
    dados_macro = get_all_macro_data()
    resumo_macro = get_macro_summary()
    
    # Dados de mercado
    dados_indices = get_index_data()
    dados_setores = get_sector_data()
    valuation_setorial = get_sector_valuation()
    premio_risco = calcular_premio_risco()
    resumo_mercado = get_market_summary()
    
    # Análises
    classificacao_setorial = classificar_valuation_setorial()
    comparacao_setorial = comparar_setores_historico()
    
    # Carteira
    dados_carteira = get_portfolio_data(CARTEIRA_BASE)
    analise_carteira = analisar_carteira(CARTEIRA_BASE)
    
    # Ciclo econômico
    ciclo = identificar_fase_ciclo()
    timing = calcular_market_timing_score()
    alertas = gerar_alertas_market_timing()
    
    # Alocação
    recomendacao = recomendar_alocacao_setorial()
    alinhamento = analisar_alinhamento_carteira(CARTEIRA_BASE)
    ajuste_risco = sugerir_ajuste_risco_carteira()
    
    return {
        "macro": {
            "dados": dados_macro,
            "resumo": resumo_macro
        },
        "mercado": {
            "indices": dados_indices,
            "setores": dados_setores,
            "valuation_setorial": valuation_setorial,
            "premio_risco": premio_risco,
            "resumo": resumo_mercado,
            "classificacao_setorial": classificacao_setorial,
            "comparacao_setorial": comparacao_setorial
        },
        "carteira": {
            "dados": dados_carteira,
            "analise": analise_carteira
        },
        "ciclo": {
            "fase": ciclo,
            "timing": timing,
            "alertas": alertas
        },
        "alocacao": {
            "recomendacao": recomendacao,
            "alinhamento": alinhamento,
            "ajuste_risco": ajuste_risco
        }
    }

# Função para a página inicial
def pagina_inicial():
    """
    Exibe a página inicial do dashboard.
    """
    st.title("📊 Painel Inteligente de Market Timing e Análise Macroeconômica")
    
    # Carrega os dados
    dados = carregar_dados()
    
    # Exibe a data de atualização
    st.markdown(f"*Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}*")
    
    # Resumo do ciclo econômico e market timing
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚥 Ciclo Econômico e Market Timing")
        
        # Fase do ciclo
        fase = dados["ciclo"]["fase"]["fase"]
        descricao = dados["ciclo"]["fase"]["descricao"]
        cor = dados["ciclo"]["fase"]["cor_alerta"]
        
        st.markdown(f"""
        <div style="background-color: {cor}; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
            <h3 style="color: white; margin: 0;">Fase Atual: {fase.capitalize()}</h3>
        </div>
        <p>{descricao}</p>
        """, unsafe_allow_html=True)
        
        # Score de market timing
        timing = dados["ciclo"]["timing"]
        st.markdown(f"""
        <div style="background-color: {timing['cor']}; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
            <h3 style="color: white; margin: 0;">Market Timing: {timing['recomendacao']}</h3>
        </div>
        <p>Score: {timing['score']:.1f}</p>
        """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("⚠️ Alertas Principais")
        
        # Exibe os alertas
        alertas = dados["ciclo"]["alertas"]
        for alerta in alertas[:3]:  # Exibe apenas os 3 primeiros alertas
            st.markdown(f"""
            <div style="background-color: {alerta['cor']}; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                <h4 style="color: white; margin: 0;">{alerta['tipo']}</h4>
                <p style="color: white; margin: 0;">{alerta['mensagem']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Resumo dos indicadores macroeconômicos e de mercado
    st.subheader("📈 Resumo dos Indicadores")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Indicadores Macroeconômicos")
        
        # Cria uma tabela com os principais indicadores macroeconômicos
        resumo_macro = dados["macro"]["resumo"]
        if not resumo_macro.empty:
            df_display = resumo_macro.copy()
            df_display["Valor"] = df_display["Valor"].apply(lambda x: f"{x:.2f}%" if isinstance(x, (int, float)) else x)
            st.dataframe(df_display, hide_index=False)
    
    with col2:
        st.markdown("### Indicadores de Mercado")
        
        # Cria uma tabela com os principais indicadores de mercado
        resumo_mercado = dados["mercado"]["resumo"]
        if not resumo_mercado.empty:
            df_display = resumo_mercado.copy()
            df_display["Valor"] = df_display["Valor"].apply(lambda x: f"{x:.2f}" if isinstance(x, (int, float)) else x)
            st.dataframe(df_display, hide_index=False)
    
    # Recomendação de alocação
    st.subheader("🧠 Recomendação de Alocação")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Exibe a alocação recomendada
        recomendacao = dados["alocacao"]["recomendacao"]
        
        st.markdown(f"### Fase do Ciclo: {recomendacao['fase_ciclo'].capitalize()}")
        st.markdown(f"**Nível de Risco Recomendado:** {recomendacao['nivel_risco']}")
        
        # Cria um gráfico de pizza com a alocação recomendada
        alocacao = recomendacao["alocacao_recomendada"]
        
        # Converte para DataFrame para exibição
        df_alocacao = pd.DataFrame({
            "Setor": list(alocacao.keys()),
            "Alocação (%)": list(alocacao.values())
        }).sort_values(by="Alocação (%)", ascending=False)
        
        st.dataframe(df_alocacao, hide_index=True)
    
    with col2:
        # Exibe o alinhamento da carteira atual
        alinhamento = dados["alocacao"]["alinhamento"]
        
        st.markdown(f"### Alinhamento da Carteira: {alinhamento['alinhamento_score']:.1f}%")
        
        # Exibe as ações alinhadas e desalinhadas
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.markdown("**Ações Alinhadas:**")
            for acao in alinhamento["acoes_alinhadas"][:5]:  # Exibe apenas as 5 primeiras
                st.markdown(f"- {acao['ticker']}")
        
        with col_b:
            st.markdown("**Ações Desalinhadas:**")
            for acao in alinhamento["acoes_desalinhadas"][:5]:  # Exibe apenas as 5 primeiras
                st.markdown(f"- {acao['ticker']}")
    
    # Navegação para outras páginas
    st.subheader("📑 Navegação")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🏦 Análise Macroeconômica", use_container_width=True):
            st.session_state.pagina = "macro"
            st.rerun()
    
    with col2:
        if st.button("📊 Valuation e Mercado", use_container_width=True):
            st.session_state.pagina = "valuation"
            st.rerun()
    
    with col3:
        if st.button("🚥 Ciclo Econômico", use_container_width=True):
            st.session_state.pagina = "ciclo"
            st.rerun()
    
    with col4:
        if st.button("🧠 Recomendação de Alocação", use_container_width=True):
            st.session_state.pagina = "alocacao"
            st.rerun()

# Função para a página de análise macroeconômica
def pagina_macro():
    """
    Exibe a página de análise macroeconômica.
    """
    st.title("🏦 Análise do Cenário Macroeconômico do Brasil")
    
    # Carrega os dados
    dados = carregar_dados()
    dados_macro = dados["macro"]["dados"]
    
    # Cria os gráficos
    dashboard_macro = criar_dashboard_macro(dados_macro)
    
    # Exibe o resumo dos indicadores
    st.subheader("Resumo dos Indicadores Macroeconômicos")
    
    # Cria uma tabela com os principais indicadores
    tabela_resumo = criar_tabela_resumo_macro(dados["macro"]["resumo"])
    st.plotly_chart(tabela_resumo, use_container_width=True)
    
    # Filtro de período
    periodo = st.selectbox(
        "Selecione o período de análise:",
        ["1 ano", "2 anos", "5 anos", "10 anos", "Máximo"],
        index=0
    )
    
    # PIB
    st.subheader("PIB - Produto Interno Bruto")
    st.markdown("""
    O Produto Interno Bruto (PIB) é a soma de todos os bens e serviços produzidos no país, 
    sendo um dos principais indicadores da atividade econômica.
    """)
    
    if "pib" in dashboard_macro:
        st.plotly_chart(dashboard_macro["pib"], use_container_width=True)
    
    # Inflação
    st.subheader("Inflação - IPCA e IGP-M")
    st.markdown("""
    A inflação mede o aumento generalizado dos preços de bens e serviços. O IPCA é o índice oficial 
    de inflação do Brasil, enquanto o IGP-M é mais sensível a variações cambiais e commodities.
    """)
    
    if "inflacao" in dashboard_macro:
        st.plotly_chart(dashboard_macro["inflacao"], use_container_width=True)
    
    # Juros
    st.subheader("Taxa de Juros - Selic")
    st.markdown("""
    A taxa Selic é a taxa básica de juros da economia brasileira, definida pelo Banco Central. 
    Ela influencia todas as demais taxas de juros do país.
    """)
    
    if "juros" in dashboard_macro:
        st.plotly_chart(dashboard_macro["juros"], use_container_width=True)
    
    # Curva de Juros
    st.subheader("Curva de Juros")
    st.markdown("""
    A curva de juros mostra as taxas de juros para diferentes prazos. Uma curva normal (crescente) 
    indica expectativa de crescimento econômico, enquanto uma curva invertida pode sinalizar recessão.
    """)
    
    if "curva_juros" in dashboard_macro:
        st.plotly_chart(dashboard_macro["curva_juros"], use_container_width=True)
    
    # Mercado de Trabalho
    st.subheader("Mercado de Trabalho")
    st.markdown("""
    O mercado de trabalho é um importante termômetro da economia. A taxa de desemprego e o saldo 
    de empregos formais (CAGED) são indicadores-chave da saúde econômica.
    """)
    
    if "trabalho" in dashboard_macro:
        st.plotly_chart(dashboard_macro["trabalho"], use_container_width=True)
    
    # Liquidez
    st.subheader("Liquidez e Agregados Monetários")
    st.markdown("""
    Os agregados monetários (M1, M2, M3, M4) medem a quantidade de moeda em circulação na economia. 
    São importantes indicadores da política monetária e da liquidez do sistema financeiro.
    """)
    
    if "liquidez" in dashboard_macro:
        st.plotly_chart(dashboard_macro["liquidez"], use_container_width=True)
    
    # Risco
    st.subheader("Indicadores de Risco")
    st.markdown("""
    O EMBI+ (Emerging Markets Bond Index Plus) e o CDS (Credit Default Swap) são indicadores 
    do risco-país, refletindo a percepção dos investidores sobre a economia brasileira.
    """)
    
    if "risco" in dashboard_macro:
        st.plotly_chart(dashboard_macro["risco"], use_container_width=True)
    
    # Correlação entre indicadores
    st.subheader("Correlação entre Indicadores Macroeconômicos")
    
    # Cria um heatmap de correlação
    heatmap_correlacao = criar_heatmap_correlacao_macro(dados_macro)
    st.plotly_chart(heatmap_correlacao, use_container_width=True)
    
    # Botão para voltar à página inicial
    if st.button("← Voltar à Página Inicial"):
        st.session_state.pagina = "inicial"
        st.rerun()

# Função para a página de valuation e mercado
def pagina_valuation():
    """
    Exibe a página de valuation e mercado.
    """
    st.title("📊 Valuation da Bolsa Brasileira e Setores da B3")
    
    # Carrega os dados
    dados = carregar_dados()
    dados_mercado = {
        "indices": dados["mercado"]["indices"],
        "setores": dados["mercado"]["setores"],
        "valuation_setorial": dados["mercado"]["valuation_setorial"],
        "comparacao_valuation": dados["mercado"]["comparacao_setorial"],
        "premio_risco": dados["mercado"]["premio_risco"],
        "classificacao_setorial": dados["mercado"]["classificacao_setorial"],
        "carteira": dados["carteira"]["dados"],
        "analise_carteira": dados["carteira"]["analise"],
        "resumo_mercado": dados["mercado"]["resumo"]
    }
    
    # Cria os gráficos
    dashboard_mercado = criar_dashboard_mercado(dados_mercado)
    
    # Exibe o resumo dos indicadores
    st.subheader("Resumo dos Indicadores de Mercado")
    
    # Cria uma tabela com os principais indicadores
    tabela_resumo = criar_tabela_resumo_mercado(dados["mercado"]["resumo"])
    st.plotly_chart(tabela_resumo, use_container_width=True)
    
    # Filtro de período
    periodo = st.selectbox(
        "Selecione o período de análise:",
        ["1 mês", "3 meses", "6 meses", "1 ano", "2 anos", "5 anos"],
        index=3
    )
    
    # Índices
    st.subheader("Evolução dos Principais Índices")
    st.markdown("""
    Os índices da bolsa são indicadores do desempenho médio das ações. O Ibovespa é o principal 
    índice da B3, enquanto outros índices representam segmentos específicos do mercado.
    """)
    
    if "indices" in dashboard_mercado:
        st.plotly_chart(dashboard_mercado["indices"], use_container_width=True)
    
    # Setores
    st.subheader("Evolução dos Setores da B3")
    st.markdown("""
    A análise setorial permite identificar quais segmentos da economia estão se destacando 
    ou enfrentando dificuldades, ajudando na alocação estratégica de investimentos.
    """)
    
    if "setores" in dashboard_mercado:
        st.plotly_chart(dashboard_mercado["setores"], use_container_width=True)
    
    # Valuation Setorial
    st.subheader("Múltiplos de Valuation por Setor")
    st.markdown("""
    Os múltiplos de valuation (P/L, P/VP, EV/EBITDA) ajudam a identificar se um setor 
    está caro ou barato em relação aos seus fundamentos.
    """)
    
    if "valuation_setorial" in dashboard_mercado:
        st.plotly_chart(dashboard_mercado["valuation_setorial"], use_container_width=True)
    
    # Comparativo de Valuation
    st.subheader("Comparação com Médias Históricas")
    st.markdown("""
    Comparar os múltiplos atuais com suas médias históricas ajuda a identificar 
    oportunidades de investimento e possíveis distorções de preço.
    """)
    
    if "comparacao_valuation" in dashboard_mercado:
        st.plotly_chart(dashboard_mercado["comparacao_valuation"], use_container_width=True)
    
    # Prêmio de Risco
    st.subheader("Fed Model Adaptado para Brasil")
    st.markdown("""
    O Fed Model compara o Earnings Yield (E/P) do mercado de ações com a taxa de juros de longo prazo. 
    Um prêmio de risco positivo indica que as ações podem estar subvalorizadas em relação aos títulos.
    """)
    
    if "premio_risco" in dashboard_mercado:
        st.plotly_chart(dashboard_mercado["premio_risco"], use_container_width=True)
    
    # Classificação Setorial
    st.subheader("Classificação de Valuation dos Setores")
    st.markdown("""
    Esta classificação combina diferentes métricas de valuation para identificar 
    quais setores estão mais atrativos para investimento.
    """)
    
    if "classificacao_setorial" in dashboard_mercado:
        st.plotly_chart(dashboard_mercado["classificacao_setorial"], use_container_width=True)
    
    # Carteira
    st.subheader("Análise da Carteira Base")
    st.markdown("""
    A análise da carteira base mostra o desempenho e os múltiplos de valuation 
    dos ativos selecionados, permitindo comparações com índices e setores.
    """)
    
    if "carteira" in dashboard_mercado:
        st.plotly_chart(dashboard_mercado["carteira"], use_container_width=True)
    
    if "analise_carteira" in dashboard_mercado:
        st.plotly_chart(dashboard_mercado["analise_carteira"], use_container_width=True)
    
    # Botão para voltar à página inicial
    if st.button("← Voltar à Página Inicial"):
        st.session_state.pagina = "inicial"
        st.rerun()

# Função para a página de ciclo econômico
def pagina_ciclo():
    """
    Exibe a página de ciclo econômico e market timing.
    """
    st.title("🚥 Sinais de Market Timing e Ciclo Econômico")
    
    # Carrega os dados
    dados = carregar_dados()
    ciclo = dados["ciclo"]["fase"]
    timing = dados["ciclo"]["timing"]
    alertas = dados["ciclo"]["alertas"]
    
    # Cria os gráficos
    dashboard_ciclo = criar_dashboard_ciclo(ciclo, timing, alertas)
    
    # Exibe a fase do ciclo econômico
    st.subheader("Fase Atual do Ciclo Econômico")
    st.markdown(f"""
    <div style="background-color: {ciclo['cor_alerta']}; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
        <h3 style="color: white; margin: 0;">Fase Atual: {ciclo['fase'].capitalize()}</h3>
    </div>
    <p>{ciclo['descricao']}</p>
    """, unsafe_allow_html=True)
    
    # Exibe o gráfico do ciclo econômico
    if "ciclo" in dashboard_ciclo:
        st.plotly_chart(dashboard_ciclo["ciclo"], use_container_width=True)
    
    # Exibe os componentes do ciclo
    if "componentes" in dashboard_ciclo:
        st.subheader("Análise dos Componentes do Ciclo")
        st.markdown("""
        Este gráfico mostra a pontuação de cada fase do ciclo econômico com base nos 
        indicadores analisados. A fase com maior pontuação é considerada a fase atual.
        """)
        st.plotly_chart(dashboard_ciclo["componentes"], use_container_width=True)
    
    # Exibe o score de market timing
    st.subheader("Score de Market Timing")
    st.markdown(f"""
    <div style="background-color: {timing['cor']}; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
        <h3 style="color: white; margin: 0;">Recomendação: {timing['recomendacao']}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    if "timing" in dashboard_ciclo:
        st.plotly_chart(dashboard_ciclo["timing"], use_container_width=True)
    
    # Exibe os alertas
    st.subheader("Alertas de Market Timing")
    st.markdown("""
    Os alertas abaixo são gerados com base na análise do ciclo econômico e dos 
    indicadores de mercado, destacando pontos de atenção para os investidores.
    """)
    
    if "alertas" in dashboard_ciclo:
        st.plotly_chart(dashboard_ciclo["alertas"], use_container_width=True)
    
    # Exibe a inclinação da curva de juros
    if "inclinacao_curva" in dashboard_ciclo:
        st.subheader("Inclinação da Curva de Juros")
        st.markdown("""
        A inclinação da curva de juros é um importante indicador do ciclo econômico. 
        Uma curva normal indica expectativa de crescimento, enquanto uma curva invertida 
        pode sinalizar desaceleração ou recessão.
        """)
        st.plotly_chart(dashboard_ciclo["inclinacao_curva"], use_container_width=True)
    
    # Exibe detalhes adicionais
    st.subheader("Detalhes dos Indicadores")
    
    # Cria abas para os diferentes grupos de indicadores
    tab1, tab2, tab3, tab4 = st.tabs(["Curva de Juros", "Inflação", "Taxa de Juros", "Risco"])
    
    with tab1:
        if "detalhes" in ciclo and "curva_juros" in ciclo["detalhes"]:
            curva_juros = ciclo["detalhes"]["curva_juros"]
            st.markdown(f"""
            **Status da Curva:** {curva_juros.get('status_curva', 'N/A')}
            
            **Inclinações:**
            - 1 ano - 1 mês: {curva_juros.get('inclinacao_1y_1m', 'N/A'):.2f} p.p.
            - 3 anos - 1 ano: {curva_juros.get('inclinacao_3y_1y', 'N/A'):.2f} p.p.
            - 3 anos - 1 mês: {curva_juros.get('inclinacao_3y_1m', 'N/A'):.2f} p.p.
            """)
    
    with tab2:
        if "detalhes" in ciclo and "inflacao" in ciclo["detalhes"]:
            inflacao = ciclo["detalhes"]["inflacao"]
            st.markdown(f"""
            **Tendência do IPCA:** {inflacao.get('tendencia_ipca', 'N/A')}
            
            **Nível do IPCA:** {inflacao.get('nivel_ipca', 'N/A')}
            """)
    
    with tab3:
        if "detalhes" in ciclo and "juros" in ciclo["detalhes"]:
            juros = ciclo["detalhes"]["juros"]
            st.markdown(f"""
            **Tendência da Selic:** {juros.get('tendencia_selic', 'N/A')}
            
            **Nível da Selic:** {juros.get('nivel_selic', 'N/A')}
            """)
    
    with tab4:
        if "detalhes" in ciclo and "risco" in ciclo["detalhes"]:
            risco = ciclo["detalhes"]["risco"]
            st.markdown(f"""
            **Nível do CDS:** {risco.get('nivel_cds', 'N/A')}
            
            **Tendência do CDS:** {risco.get('tendencia_cds', 'N/A')}
            
            **Nível do EMBI+:** {risco.get('nivel_embi', 'N/A')}
            
            **Tendência do IFIX:** {risco.get('tendencia_ifix', 'N/A')}
            """)
    
    # Botão para voltar à página inicial
    if st.button("← Voltar à Página Inicial"):
        st.session_state.pagina = "inicial"
        st.rerun()

# Função para a página de recomendação de alocação
def pagina_alocacao():
    """
    Exibe a página de recomendação de alocação setorial.
    """
    st.title("🧠 Recomendação de Alocação por Fase do Ciclo Econômico")
    
    # Carrega os dados
    dados = carregar_dados()
    recomendacao = dados["alocacao"]["recomendacao"]
    alinhamento = dados["alocacao"]["alinhamento"]
    ajuste_risco = dados["alocacao"]["ajuste_risco"]
    
    # Cria os gráficos
    dashboard_alocacao = criar_dashboard_alocacao(recomendacao, alinhamento, ajuste_risco)
    
    # Exibe a fase do ciclo econômico
    st.subheader(f"Fase Atual do Ciclo: {recomendacao['fase_ciclo'].capitalize()}")
    st.markdown(f"*{recomendacao['descricao_fase']}*")
    
    # Exibe o score de market timing
    st.markdown(f"""
    <div style="background-color: {dados['ciclo']['timing']['cor']}; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
        <h3 style="color: white; margin: 0;">Market Timing: {dados['ciclo']['timing']['recomendacao']}</h3>
        <p style="color: white; margin: 0;">Score: {dados['ciclo']['timing']['score']:.1f}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Exibe a alocação recomendada
    st.subheader("Alocação Setorial Recomendada")
    st.markdown(f"""
    Com base na fase atual do ciclo econômico ({recomendacao['fase_ciclo'].capitalize()}) e no score de market timing ({dados['ciclo']['timing']['score']:.1f}), 
    recomendamos a seguinte alocação setorial:
    """)
    
    if "alocacao_recomendada" in dashboard_alocacao:
        st.plotly_chart(dashboard_alocacao["alocacao_recomendada"], use_container_width=True)
    
    # Exibe o nível de risco recomendado
    st.subheader("Nível de Risco Recomendado")
    st.markdown(f"""
    **Nível de Risco:** {recomendacao['nivel_risco']}
    
    **Justificativa:**
    """)
    
    for justificativa in recomendacao['justificativa']:
        st.markdown(f"- {justificativa}")
    
    # Exibe o ajuste de risco recomendado
    st.subheader("Ajuste de Risco Recomendado")
    
    if "ajuste_risco" in dashboard_alocacao:
        st.plotly_chart(dashboard_alocacao["ajuste_risco"], use_container_width=True)
    
    # Exibe os ajustes específicos
    if "ajustes_especificos" in dashboard_alocacao:
        st.plotly_chart(dashboard_alocacao["ajustes_especificos"], use_container_width=True)
    
    # Exibe o alinhamento da carteira atual
    st.subheader("Alinhamento da Carteira Atual")
    st.markdown(f"""
    A carteira atual tem um alinhamento de **{alinhamento['alinhamento_score']:.1f}%** com a fase atual do ciclo econômico.
    """)
    
    if "alinhamento_carteira" in dashboard_alocacao:
        st.plotly_chart(dashboard_alocacao["alinhamento_carteira"], use_container_width=True)
    
    # Exibe o comparativo de alocação
    st.subheader("Comparativo: Alocação Atual vs. Recomendada")
    
    if "comparativo_alocacao" in dashboard_alocacao:
        st.plotly_chart(dashboard_alocacao["comparativo_alocacao"], use_container_width=True)
    
    # Exibe as ações alinhadas e desalinhadas
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Ações Alinhadas ao Ciclo")
        
        if "acoes_alinhadas" in dashboard_alocacao:
            st.plotly_chart(dashboard_alocacao["acoes_alinhadas"], use_container_width=True)
    
    with col2:
        st.subheader("Ações Desalinhadas do Ciclo")
        
        if "acoes_desalinhadas" in dashboard_alocacao:
            st.plotly_chart(dashboard_alocacao["acoes_desalinhadas"], use_container_width=True)
    
    # Exibe as recomendações de ajuste
    st.subheader("Recomendações de Ajuste da Carteira")
    
    if "recomendacoes_ajuste" in dashboard_alocacao:
        st.plotly_chart(dashboard_alocacao["recomendacoes_ajuste"], use_container_width=True)
    
    # Botão para voltar à página inicial
    if st.button("← Voltar à Página Inicial"):
        st.session_state.pagina = "inicial"
        st.rerun()

# Função principal
def main():
    """
    Função principal do aplicativo.
    """
    # Aplica o tema personalizado
    aplicar_tema()
    
    # Inicializa o estado da sessão
    if "pagina" not in st.session_state:
        st.session_state.pagina = "inicial"
    
    # Exibe a página correspondente
    if st.session_state.pagina == "inicial":
        pagina_inicial()
    elif st.session_state.pagina == "macro":
        pagina_macro()
    elif st.session_state.pagina == "valuation":
        pagina_valuation()
    elif st.session_state.pagina == "ciclo":
        pagina_ciclo()
    elif st.session_state.pagina == "alocacao":
        pagina_alocacao()

# Executa o aplicativo
if __name__ == "__main__":
    main()
