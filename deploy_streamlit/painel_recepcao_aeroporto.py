import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import os

st.set_page_config(page_title="Gestão Recepção Aeroporto", layout="wide", page_icon="✈️")

# Título
st.title("✈️ Análise de Recepção no Aeroporto - Clientes sem Guia")
st.markdown("---")

@st.cache_data
def carregar_dados(uploaded_file=None):
    """Carrega e processa os dados da planilha"""
    # Tentar carregar de diferentes formas
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    elif os.path.exists('planilha_dados.csv'):
        df = pd.read_csv('planilha_dados.csv')
    elif os.path.exists('../planilha_dados.csv'):
        df = pd.read_csv('../planilha_dados.csv')
    elif os.path.exists('./deploy_streamlit/planilha_dados.csv'):
        df = pd.read_csv('./deploy_streamlit/planilha_dados.csv')
    else:
        raise FileNotFoundError("Arquivo planilha_dados.csv não encontrado")
    
    # Converter Data para datetime
    df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
    
    # Filtrar apenas IN (chegadas) e sem guia
    # Excluir IN - Tripulacao
    df_sem_guia = df[
        (df['Tipo do Serviço'] == 'IN') & 
        (df['Guia'] == 'Sem Guia') &
        (df['Serviço'] != 'IN - Tripulacao')
    ].copy()
    
    # Converter Adt e Chd para numérico
    df_sem_guia['Adt'] = pd.to_numeric(df_sem_guia['Adt'], errors='coerce').fillna(0).astype(int)
    df_sem_guia['Chd'] = pd.to_numeric(df_sem_guia['Chd'], errors='coerce').fillna(0).astype(int)
    
    # Calcular total de passageiros
    df_sem_guia['Total_Pax'] = df_sem_guia['Adt'] + df_sem_guia['Chd']
    
    # Extrair informações de data/hora
    df_sem_guia['Dia_Semana'] = df_sem_guia['Data'].dt.day_name()
    df_sem_guia['Dia_Semana_Num'] = df_sem_guia['Data'].dt.dayofweek
    df_sem_guia['Mes'] = df_sem_guia['Data'].dt.month
    df_sem_guia['Ano'] = df_sem_guia['Data'].dt.year
    
    # Traduzir dias da semana
    dias_pt = {
        'Monday': 'Segunda-feira',
        'Tuesday': 'Terça-feira',
        'Wednesday': 'Quarta-feira',
        'Thursday': 'Quinta-feira',
        'Friday': 'Sexta-feira',
        'Saturday': 'Sábado',
        'Sunday': 'Domingo'
    }
    df_sem_guia['Dia_Semana_PT'] = df_sem_guia['Dia_Semana'].map(dias_pt)
    
    # Processar horário de voo
    df_sem_guia['Horario_Voo_Limpo'] = df_sem_guia['Horário de Voo'].astype(str).str.strip()
    
    # Extrair hora do horário de voo (formato HH:MM)
    def extrair_hora(horario):
        try:
            if pd.isna(horario) or horario == '' or horario == '-':
                return None
            # Tentar extrair hora (primeiros 2 dígitos ou primeiros caracteres antes de :)
            if ':' in str(horario):
                hora = int(str(horario).split(':')[0])
                return hora
            elif len(str(horario)) >= 2:
                hora = int(str(horario)[:2])
                return hora
            return None
        except:
            return None
    
    df_sem_guia['Hora_Voo'] = df_sem_guia['Horario_Voo_Limpo'].apply(extrair_hora)
    
    # Filtrar apenas registros com hora válida e >= 8h
    df_sem_guia = df_sem_guia[
        (df_sem_guia['Hora_Voo'].notna()) & 
        (df_sem_guia['Hora_Voo'] >= 8)
    ].copy()
    
    # Criar faixa horária
    def criar_faixa_horaria(hora):
        if pd.isna(hora):
            return None
        return f"{int(hora):02d}:00 - {int(hora):02d}:59"
    
    df_sem_guia['Faixa_Horaria'] = df_sem_guia['Hora_Voo'].apply(criar_faixa_horaria)
    
    return df_sem_guia

# Verificar se o arquivo existe, senão solicitar upload
uploaded_file = None
arquivo_existe = os.path.exists('planilha_dados.csv') or os.path.exists('../planilha_dados.csv')

if not arquivo_existe:
    st.warning("⚠️ Arquivo 'planilha_dados.csv' não encontrado no repositório!")
    st.info("""
    **Por favor, faça upload do arquivo CSV com os dados:**
    
    O arquivo deve conter as seguintes colunas:
    - Data, Tipo do Serviço, Guia, Serviço, Voo, Horário de Voo, Adt, Chd, Código
    """)
    
    uploaded_file = st.file_uploader("Escolha o arquivo planilha_dados.csv", type=['csv'])
    
    if uploaded_file is None:
        st.error("❌ Por favor, faça upload do arquivo para continuar.")
        st.stop()

# Carregar dados
try:
    with st.spinner('Carregando dados...'):
        df = carregar_dados(uploaded_file)
except FileNotFoundError as e:
    st.error(f"❌ Erro: {str(e)}")
    st.info("""
    **Solução:**
    1. Certifique-se de que o arquivo 'planilha_dados.csv' está no repositório GitHub
    2. Ou faça upload do arquivo usando o botão acima
    3. Verifique se o arquivo está na mesma pasta que o painel_recepcao_aeroporto.py
    """)
    st.stop()
except Exception as e:
    st.error(f"❌ Erro ao carregar dados: {str(e)}")
    st.stop()

# Filtros na sidebar
st.sidebar.header("📊 Filtros")

# Filtro de período
anos_disponiveis = sorted(df['Ano'].dropna().unique())
ano_selecionado = st.sidebar.selectbox("Ano", anos_disponiveis, index=len(anos_disponiveis)-1 if anos_disponiveis else 0)

meses_disponiveis = sorted(df[df['Ano'] == ano_selecionado]['Mes'].dropna().unique())
mes_selecionado = st.sidebar.selectbox(
    "Mês", 
    meses_disponiveis,
    format_func=lambda x: {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }.get(x, str(x))
)

# Filtrar dados
df_filtrado = df[(df['Ano'] == ano_selecionado) & (df['Mes'] == mes_selecionado)].copy()

# Métricas principais
st.markdown("### 📊 Resumo Geral")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    total_voos = df_filtrado['Voo'].nunique()
    st.metric("🛬 Total de Voos", f"{total_voos:,}")

with col2:
    total_pax = df_filtrado['Total_Pax'].sum()
    st.metric("👥 Total de Passageiros", f"{total_pax:,}")

with col3:
    media_pax_dia = df_filtrado.groupby('Data')['Total_Pax'].sum().mean()
    st.metric("📈 Média Pax/Dia", f"{media_pax_dia:.1f}")

with col4:
    total_servicos_unicos = df_filtrado['Serviço'].nunique()
    st.metric("🎯 Tipos de Serviço", f"{total_servicos_unicos}")

with col5:
    total_registros = len(df_filtrado)
    st.metric("📋 Total de Registros", f"{total_registros:,}")

# Cards com principais serviços
st.markdown("### 🎯 Top 3 Serviços do Período")
servicos_top = df_filtrado.groupby('Serviço')['Total_Pax'].sum().sort_values(ascending=False).head(3)

col1, col2, col3 = st.columns(3)
cols = [col1, col2, col3]

for idx, (servico, total) in enumerate(servicos_top.items()):
    with cols[idx]:
        qtd_voos = df_filtrado[df_filtrado['Serviço'] == servico]['Voo'].nunique()
        st.metric(
            label=f"🏆 {servico}",
            value=f"{int(total)} pax",
            delta=f"{qtd_voos} voos"
        )

st.markdown("---")

# Análise por Serviços
st.subheader("🎯 Serviços sem Guia - Visão Geral")

# Agrupar por serviço
servicos_resumo = df_filtrado.groupby('Serviço').agg({
    'Total_Pax': 'sum',
    'Código': 'count',
    'Voo': 'nunique'
}).reset_index()
servicos_resumo.columns = ['Serviço', 'Total_Passageiros', 'Qtd_Servicos', 'Qtd_Voos']
servicos_resumo = servicos_resumo.sort_values('Total_Passageiros', ascending=False)

col1, col2 = st.columns(2)

with col1:
    # Top 10 serviços
    top_servicos = servicos_resumo.head(10)
    fig_servicos = px.bar(
        top_servicos,
        x='Total_Passageiros',
        y='Serviço',
        orientation='h',
        title='Top 10 Serviços sem Guia (Total de Passageiros)',
        labels={'Serviço': 'Serviço', 'Total_Passageiros': 'Total de Passageiros'},
        color='Total_Passageiros',
        color_continuous_scale='Reds',
        text='Total_Passageiros'
    )
    fig_servicos.update_traces(texttemplate='%{text}', textposition='outside')
    fig_servicos.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_servicos, use_container_width=True)

with col2:
    # Pizza dos principais serviços
    top5_servicos = servicos_resumo.head(5)
    outros = servicos_resumo.iloc[5:]['Total_Passageiros'].sum()
    
    if outros > 0:
        pie_data = pd.concat([
            top5_servicos[['Serviço', 'Total_Passageiros']],
            pd.DataFrame({'Serviço': ['Outros'], 'Total_Passageiros': [outros]})
        ])
    else:
        pie_data = top5_servicos[['Serviço', 'Total_Passageiros']]
    
    fig_pie = px.pie(
        pie_data,
        values='Total_Passageiros',
        names='Serviço',
        title='Distribuição de Passageiros por Serviço',
        color_discrete_sequence=px.colors.sequential.RdBu
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# Tabela com todos os serviços
with st.expander("📊 Ver todos os serviços"):
    st.dataframe(
        servicos_resumo,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Serviço": st.column_config.TextColumn("🎯 Serviço", width="large"),
            "Total_Passageiros": st.column_config.NumberColumn("👥 Total Pax", format="%d"),
            "Qtd_Servicos": st.column_config.NumberColumn("📋 Qtd Serviços", format="%d"),
            "Qtd_Voos": st.column_config.NumberColumn("✈️ Qtd Voos", format="%d")
        }
    )

st.markdown("---")

# Análise por dia da semana
st.subheader("📅 Concentração por Dia da Semana")

# Criar ordem dos dias da semana
ordem_dias = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']

# Agrupar por dia da semana
concentracao_dia = df_filtrado.groupby('Dia_Semana_PT').agg({
    'Total_Pax': 'sum',
    'Código': 'count',
    'Voo': 'nunique'
}).reset_index()
concentracao_dia.columns = ['Dia_Semana', 'Total_Passageiros', 'Qtd_Servicos', 'Qtd_Voos']

# Ordenar por dia da semana
concentracao_dia['Ordem'] = concentracao_dia['Dia_Semana'].map({dia: i for i, dia in enumerate(ordem_dias)})
concentracao_dia = concentracao_dia.sort_values('Ordem')

col1, col2 = st.columns(2)

with col1:
    fig_dia_pax = px.bar(
        concentracao_dia,
        x='Dia_Semana',
        y='Total_Passageiros',
        title='Total de Passageiros por Dia da Semana',
        labels={'Dia_Semana': 'Dia da Semana', 'Total_Passageiros': 'Passageiros'},
        color='Total_Passageiros',
        color_continuous_scale='Blues',
        text='Total_Passageiros'
    )
    fig_dia_pax.update_traces(texttemplate='%{text}', textposition='outside')
    fig_dia_pax.update_layout(showlegend=False, xaxis_tickangle=-45)
    st.plotly_chart(fig_dia_pax, use_container_width=True)

with col2:
    fig_dia_voos = px.bar(
        concentracao_dia,
        x='Dia_Semana',
        y='Qtd_Voos',
        title='Quantidade de Voos por Dia da Semana',
        labels={'Dia_Semana': 'Dia da Semana', 'Qtd_Voos': 'Voos'},
        color='Qtd_Voos',
        color_continuous_scale='Greens',
        text='Qtd_Voos'
    )
    fig_dia_voos.update_traces(texttemplate='%{text}', textposition='outside')
    fig_dia_voos.update_layout(showlegend=False, xaxis_tickangle=-45)
    st.plotly_chart(fig_dia_voos, use_container_width=True)

# Serviços por dia da semana
st.markdown("##### 📋 Serviços por Dia da Semana")
servicos_por_dia = df_filtrado.groupby(['Dia_Semana_PT', 'Serviço'])['Total_Pax'].sum().reset_index()
servicos_por_dia.columns = ['Dia_Semana', 'Serviço', 'Total_Passageiros']

# Pegar top 5 serviços
top_servicos_list = servicos_resumo.head(5)['Serviço'].tolist()
servicos_por_dia_filtrado = servicos_por_dia[servicos_por_dia['Serviço'].isin(top_servicos_list)]

# Ordenar por dia da semana
servicos_por_dia_filtrado['Ordem'] = servicos_por_dia_filtrado['Dia_Semana'].map({dia: i for i, dia in enumerate(ordem_dias)})
servicos_por_dia_filtrado = servicos_por_dia_filtrado.sort_values('Ordem')

fig_servicos_dia = px.bar(
    servicos_por_dia_filtrado,
    x='Dia_Semana',
    y='Total_Passageiros',
    color='Serviço',
    title='Top 5 Serviços - Passageiros por Dia da Semana',
    labels={'Dia_Semana': 'Dia da Semana', 'Total_Passageiros': 'Passageiros'},
    barmode='group',
    color_discrete_sequence=px.colors.qualitative.Set2
)
fig_servicos_dia.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig_servicos_dia, use_container_width=True)

st.markdown("---")

# Análise por horário
st.subheader("🕐 Concentração por Horário")

# Agrupar por horário
concentracao_hora = df_filtrado.groupby('Hora_Voo').agg({
    'Total_Pax': 'sum',
    'Código': 'count',
    'Voo': 'nunique'
}).reset_index()
concentracao_hora.columns = ['Hora', 'Total_Passageiros', 'Qtd_Servicos', 'Qtd_Voos']
concentracao_hora = concentracao_hora.sort_values('Hora')

col1, col2 = st.columns(2)

with col1:
    fig_hora_pax = px.line(
        concentracao_hora,
        x='Hora',
        y='Total_Passageiros',
        title='Passageiros por Horário',
        labels={'Hora': 'Horário', 'Total_Passageiros': 'Passageiros'},
        markers=True
    )
    fig_hora_pax.add_bar(x=concentracao_hora['Hora'], y=concentracao_hora['Total_Passageiros'], name='Passageiros')
    fig_hora_pax.update_layout(showlegend=False)
    st.plotly_chart(fig_hora_pax, use_container_width=True)

with col2:
    fig_hora_voos = px.bar(
        concentracao_hora,
        x='Hora',
        y='Qtd_Voos',
        title='Voos por Horário',
        labels={'Hora': 'Horário', 'Qtd_Voos': 'Voos'},
        color='Qtd_Voos',
        color_continuous_scale='Oranges'
    )
    fig_hora_voos.update_layout(showlegend=False)
    st.plotly_chart(fig_hora_voos, use_container_width=True)

st.markdown("---")

# Mapa de calor: Dia da Semana vs Horário
st.subheader("🔥 Mapa de Calor: Concentração por Dia e Horário")

# Criar pivot table
heatmap_data = df_filtrado.groupby(['Dia_Semana_PT', 'Hora_Voo'])['Total_Pax'].sum().reset_index()
heatmap_pivot = heatmap_data.pivot(index='Dia_Semana_PT', columns='Hora_Voo', values='Total_Pax').fillna(0)

# Reordenar dias da semana
heatmap_pivot = heatmap_pivot.reindex(ordem_dias)

fig_heatmap = px.imshow(
    heatmap_pivot,
    labels=dict(x="Horário", y="Dia da Semana", color="Passageiros"),
    title="Concentração de Passageiros por Dia e Horário",
    color_continuous_scale='Reds',
    aspect='auto'
)
fig_heatmap.update_xaxes(side="bottom")
st.plotly_chart(fig_heatmap, use_container_width=True)

st.markdown("---")

# Tabela detalhada por dia da semana e horário
st.subheader("📋 Detalhamento por Dia da Semana e Horário")

# Seletor de dia da semana
dia_selecionado = st.selectbox("Selecione o dia da semana", ordem_dias)

# Filtrar dados do dia selecionado
df_dia = df_filtrado[df_filtrado['Dia_Semana_PT'] == dia_selecionado].copy()

if len(df_dia) > 0:
    # Tabs para diferentes visualizações
    tab1, tab2 = st.tabs(["📊 Por Voo e Horário", "🎯 Por Serviço"])
    
    with tab1:
        # Agrupar por horário e voo
        detalhamento = df_dia.groupby(['Hora_Voo', 'Voo', 'Serviço']).agg({
            'Total_Pax': 'sum',
            'Adt': 'sum',
            'Chd': 'sum',
            'Código': 'count'
        }).reset_index()
        detalhamento.columns = ['Hora', 'Voo', 'Serviço', 'Total_Pax', 'Adultos', 'Crianças', 'Qtd_Serviços']
        detalhamento = detalhamento.sort_values(['Hora', 'Voo'])
        
        # Formatar hora
        detalhamento['Horário'] = detalhamento['Hora'].apply(lambda x: f"{int(x):02d}:00")
        
        # Reordenar colunas
        detalhamento = detalhamento[['Horário', 'Voo', 'Serviço', 'Total_Pax', 'Adultos', 'Crianças', 'Qtd_Serviços']]
        
        st.dataframe(
            detalhamento,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Horário": st.column_config.TextColumn("🕐 Horário", width="small"),
                "Voo": st.column_config.TextColumn("✈️ Voo", width="small"),
                "Serviço": st.column_config.TextColumn("🎯 Serviço", width="medium"),
                "Total_Pax": st.column_config.NumberColumn("👥 Total Pax", format="%d"),
                "Adultos": st.column_config.NumberColumn("👤 Adultos", format="%d"),
                "Crianças": st.column_config.NumberColumn("👶 Crianças", format="%d"),
                "Qtd_Serviços": st.column_config.NumberColumn("📋 Serviços", format="%d")
            }
        )
    
    with tab2:
        # Agrupar por serviço
        detalhamento_servico = df_dia.groupby('Serviço').agg({
            'Total_Pax': 'sum',
            'Adt': 'sum',
            'Chd': 'sum',
            'Voo': 'nunique',
            'Código': 'count'
        }).reset_index()
        detalhamento_servico.columns = ['Serviço', 'Total_Pax', 'Adultos', 'Crianças', 'Qtd_Voos', 'Qtd_Serviços']
        detalhamento_servico = detalhamento_servico.sort_values('Total_Pax', ascending=False)
        
        # Criar colunas para cards
        cols = st.columns(min(3, len(detalhamento_servico)))
        for idx, (_, row) in enumerate(detalhamento_servico.head(3).iterrows()):
            with cols[idx]:
                st.metric(
                    label=f"🎯 {row['Serviço']}",
                    value=f"{int(row['Total_Pax'])} pax",
                    delta=f"{int(row['Qtd_Voos'])} voos"
                )
        
        st.dataframe(
            detalhamento_servico,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Serviço": st.column_config.TextColumn("🎯 Serviço", width="large"),
                "Total_Pax": st.column_config.NumberColumn("👥 Total Pax", format="%d"),
                "Adultos": st.column_config.NumberColumn("👤 Adultos", format="%d"),
                "Crianças": st.column_config.NumberColumn("👶 Crianças", format="%d"),
                "Qtd_Voos": st.column_config.NumberColumn("✈️ Voos", format="%d"),
                "Qtd_Serviços": st.column_config.NumberColumn("📋 Serviços", format="%d")
            }
        )
        
        # Gráfico de serviços
        fig_servicos_dia = px.bar(
            detalhamento_servico.head(10),
            x='Total_Pax',
            y='Serviço',
            orientation='h',
            title=f'Serviços sem Guia - {dia_selecionado}',
            labels={'Serviço': 'Serviço', 'Total_Pax': 'Total de Passageiros'},
            color='Total_Pax',
            color_continuous_scale='Viridis',
            text='Total_Pax'
        )
        fig_servicos_dia.update_traces(texttemplate='%{text}', textposition='outside')
        fig_servicos_dia.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_servicos_dia, use_container_width=True)
    
    # Resumo do dia
    st.info(f"""
    **Resumo de {dia_selecionado}:**
    - Total de passageiros: **{df_dia['Total_Pax'].sum():,}**
    - Total de voos: **{df_dia['Voo'].nunique()}**
    - Total de serviços: **{len(df_dia)}**
    - Serviço com mais passageiros: **{detalhamento_servico.iloc[0]['Serviço']}** com **{detalhamento_servico.iloc[0]['Total_Pax']:.0f}** passageiros
    - Horário de pico: **{detalhamento.groupby('Horário')['Total_Pax'].sum().idxmax()}** com **{detalhamento.groupby('Horário')['Total_Pax'].sum().max():.0f}** passageiros
    """)
else:
    st.warning(f"Não há dados para {dia_selecionado} no período selecionado.")

st.markdown("---")

# Recomendação de horário
st.subheader("💡 Recomendação de Horário de Trabalho")

# Calcular horários com mais movimento
resumo_horario = df_filtrado.groupby('Hora_Voo')['Total_Pax'].sum().sort_values(ascending=False)

col1, col2 = st.columns(2)

with col1:
    st.success("**Horários com maior movimento:**")
    top_horarios = resumo_horario.head(5)
    for hora, pax in top_horarios.items():
        st.write(f"🕐 **{int(hora):02d}:00** - {int(pax):,} passageiros")

with col2:
    # Calcular horário de início e fim recomendado
    total_pax_geral = df_filtrado['Total_Pax'].sum()
    acumulado = 0
    hora_inicio = None
    hora_fim = None
    
    for hora in sorted(df_filtrado['Hora_Voo'].unique()):
        pax_hora = df_filtrado[df_filtrado['Hora_Voo'] == hora]['Total_Pax'].sum()
        percentual = (pax_hora / total_pax_geral) * 100
        
        if percentual >= 5 and hora_inicio is None:  # Início quando atinge 5% do movimento
            hora_inicio = int(hora)
        
        acumulado += pax_hora
        if (acumulado / total_pax_geral) >= 0.90:  # Até 90% do movimento
            hora_fim = int(hora) + 1
            break
    
    if hora_inicio and hora_fim:
        st.info(f"""
        **Horário recomendado:**
        
        🕐 **Início:** {hora_inicio:02d}:00
        
        🕐 **Fim:** {hora_fim:02d}:00
        
        📊 **Cobertura:** ~90% dos passageiros
        """)

st.markdown("---")

# Exportar dados
st.subheader("📥 Exportar Dados")

col1, col2, col3 = st.columns(3)

with col1:
    # Exportar resumo por dia
    if st.button("📊 Exportar Resumo por Dia"):
        concentracao_dia_export = concentracao_dia[['Dia_Semana', 'Total_Passageiros', 'Qtd_Servicos', 'Qtd_Voos']]
        csv = concentracao_dia_export.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="⬇️ Download CSV",
            data=csv,
            file_name=f"resumo_por_dia_{ano_selecionado}_{mes_selecionado:02d}.csv",
            mime="text/csv"
        )

with col2:
    # Exportar resumo por horário
    if st.button("📊 Exportar Resumo por Horário"):
        csv = concentracao_hora.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="⬇️ Download CSV",
            data=csv,
            file_name=f"resumo_por_horario_{ano_selecionado}_{mes_selecionado:02d}.csv",
            mime="text/csv"
        )

with col3:
    # Exportar dados completos
    if st.button("📊 Exportar Dados Completos"):
        df_export = df_filtrado[['Data', 'Dia_Semana_PT', 'Hora_Voo', 'Voo', 'Código', 'Serviço', 'Cliente', 'Adt', 'Chd', 'Total_Pax']]
        csv = df_export.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="⬇️ Download CSV",
            data=csv,
            file_name=f"dados_completos_{ano_selecionado}_{mes_selecionado:02d}.csv",
            mime="text/csv"
        )

# Rodapé
st.markdown("---")
st.caption(f"📊 Análise gerada em {datetime.now().strftime('%d/%m/%Y %H:%M')} | Total de registros analisados: {len(df_filtrado):,}")
