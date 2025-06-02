# Painel Inteligente de Market Timing e Análise Macroeconômica

Este projeto implementa um dashboard interativo em Streamlit focado no mercado brasileiro, integrando análise macroeconômica, valuation de setores da B3, sinais de market timing e recomendações de alocação setorial baseadas no ciclo econômico atual.

## Estrutura do Projeto

```
market_timing_dashboard/
├── data/                  # Dados armazenados localmente
├── src/                   # Código-fonte do projeto
│   ├── analysis/          # Módulos de análise
│   │   ├── allocation.py  # Recomendação de alocação setorial
│   │   ├── cycle.py       # Identificação do ciclo econômico
│   │   └── valuation.py   # Análise de valuation
│   ├── data/              # Módulos de coleta de dados
│   │   ├── macro_data.py  # Dados macroeconômicos
│   │   └── market_data.py # Dados de mercado
│   ├── visualization/     # Módulos de visualização
│   │   ├── allocation_charts.py  # Gráficos de alocação
│   │   ├── cycle_charts.py       # Gráficos de ciclo econômico
│   │   ├── macro_charts.py       # Gráficos macroeconômicos
│   │   └── market_charts.py      # Gráficos de mercado
│   ├── app.py             # Aplicativo Streamlit principal
│   └── config.py          # Configurações globais
├── requirements.txt       # Dependências do projeto
└── README.md              # Documentação
```

## Requisitos

- Python 3.8+
- Bibliotecas listadas em `requirements.txt`

## Instalação

1. Clone o repositório ou extraia os arquivos do projeto:

```bash
git clone <url-do-repositorio>
cd market_timing_dashboard
```

2. Crie um ambiente virtual e instale as dependências:

```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Execução

Para iniciar o dashboard:

```bash
cd market_timing_dashboard
source venv/bin/activate  # No Windows: venv\Scripts\activate
streamlit run src/app.py
```

O aplicativo será aberto automaticamente no seu navegador padrão. Se não abrir, acesse `http://localhost:8501`.

## Funcionalidades

### 1. Análise do Cenário Macroeconômico do Brasil

- PIB: Crescimento trimestral e anual
- Inflação: IPCA, IGP-M (12 meses + tendência)
- Juros: Selic, curva de juros brasileira (DI futuro)
- Mercado de Trabalho: Taxa de desemprego e geração de empregos
- Liquidez: Agregados monetários (M1, M2) e política monetária
- Risco: CDS Brasil (risco país), IFIX (risco do mercado imobiliário)

### 2. Valuation da Bolsa Brasileira e Setores da B3

- Múltiplos de valuation (P/L, P/VP, EV/EBITDA, Dividend Yield)
- Comparação com médias históricas
- Prêmio de risco (Fed Model adaptado)
- Classificação setorial (barato/caro)

### 3. Sinais de Market Timing e Ciclo Econômico

- Identificação da fase atual do ciclo econômico
- Score de market timing
- Alertas visuais
- Análise da curva de juros

### 4. Recomendação de Alocação Setorial

- Alocação recomendada por setor com base no ciclo econômico
- Análise de alinhamento da carteira atual
- Recomendações de ajuste
- Sugestões de ajuste de risco

## Fontes de Dados

- Banco Central do Brasil (via API do SGS)
- Yahoo Finance (via yfinance)
- Dados simulados para demonstração

## Observações Importantes

1. **Atualização de Dados**: O dashboard atualiza os dados automaticamente a cada hora. Para forçar uma atualização, reinicie o aplicativo.

2. **Limitações de API**: Algumas APIs podem ter limites de requisições. Em caso de erro, aguarde alguns minutos e tente novamente.

3. **Finalidade Educacional**: Este dashboard foi desenvolvido para fins educacionais e não constitui recomendação de investimento.

4. **Personalização**: Para personalizar a carteira base, edite o arquivo `src/config.py`.

## Solução de Problemas

- **Erro de conexão com APIs**: Verifique sua conexão com a internet e se as APIs estão disponíveis.
- **Erro de instalação de dependências**: Certifique-se de estar usando Python 3.8+ e tente reinstalar as dependências.
- **Erro ao iniciar o Streamlit**: Verifique se todas as dependências foram instaladas corretamente.

## Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

## Licença

Este projeto está licenciado sob a licença MIT.
