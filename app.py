import streamlit as st
import pandas as pd
import plotly.express as px
import json
from io import BytesIO
from datetime import datetime, timedelta

# ===================================
# CONFIGURAÇÃO
# ===================================

st.set_page_config(
    page_title="Pedidos Em Aberto - Visualização",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Pedidos Em Aberto - Visualização")

# ===================================
# CSS
# ===================================

st.markdown(
    """
    <style>

    .stDataFrame td {
        text-align: center !important;
    }

    .stDataFrame th {
        text-align: center !important;
        font-weight: bold !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# ===================================
# LEITURA PLANILHA
# ===================================

try:

    df = pd.read_excel(
        "dados.xlsx",
        sheet_name=0
    )

except FileNotFoundError:

    st.error("⚠️ Nenhum arquivo foi carregado ainda.")
    st.stop()

except Exception as e:

    st.error(f"Erro ao abrir planilha: {e}")
    st.stop()

# ===================================
# LIMPEZA COLUNAS
# ===================================

df.columns = (
    df.columns
    .astype(str)
    .str.strip()
)

# ===================================
# AJUSTAR PEDIDO
# ===================================

if "Pedido" in df.columns:

    df["Pedido"] = (
        df["Pedido"]
        .astype(str)
        .str.replace(".0", "", regex=False)
    )

# ===================================
# AJUSTAR PC
# ===================================

if "PC" in df.columns:

    df["PC"] = (
        df["PC"]
        .astype(str)
        .str.replace(".0", "", regex=False)
    )

# ===================================
# CONVERTE DATA
# ===================================

if "Previsão" in df.columns:

    df["Previsão"] = pd.to_datetime(
        df["Previsão"],
        errors="coerce",
        dayfirst=True
    )

# ===================================
# ÚLTIMA ATUALIZAÇÃO
# ===================================

try:

    with open("ultima_atualizacao.json", "r") as f:

        dados_update = json.load(f)

    data_update = datetime.strptime(
        dados_update["ultima_atualizacao"],
        "%Y-%m-%d %H:%M:%S"
    )

    data_update = data_update - timedelta(hours=3)

    data_formatada = data_update.strftime(
        "%d/%m/%Y %H:%M:%S"
    )

    st.info(
        f"🕒 Última atualização da planilha: {data_formatada}"
    )

except:

    pass

# ===================================
# FILTROS SALVOS
# ===================================

try:

    with open("filtros.json", "r") as f:

        filtros = json.load(f)[0]

except:

    filtros = {}

# ===================================
# SIDEBAR
# ===================================

st.sidebar.title("Filtros")

# ===================================
# FILTRO DATA
# ===================================

if "Previsão" in df.columns:

    min_data = df["Previsão"].min().date()
    max_data = df["Previsão"].max().date()

    st.sidebar.markdown("### 📅 Período")

    start_date = st.sidebar.date_input(
        "Data inicial",
        value=min_data,
        format="DD/MM/YYYY"
    )

    end_date = st.sidebar.date_input(
        "Data final",
        value=max_data,
        format="DD/MM/YYYY"
    )

    df = df[
        (
            df["Previsão"].dt.date >= start_date
        )
        &
        (
            df["Previsão"].dt.date <= end_date
        )
    ]

# ===================================
# FILTRO ROTA
# ===================================

if "Rota" in df.columns:

    rotas = sorted(
        df["Rota"]
        .dropna()
        .astype(str)
        .unique()
    )

    rotas_default = [
        r for r in filtros.get("rotas", [])
        if r in rotas
    ]

    rotas_selecionadas = st.sidebar.multiselect(
        "Rotas",
        rotas,
        default=rotas_default
    )

    if rotas_selecionadas:

        df = df[
            df["Rota"]
            .astype(str)
            .isin(rotas_selecionadas)
        ]

# ===================================
# FILTRO PRODUTO
# ===================================

if "Produto" in df.columns:

    produtos = sorted(
        df["Produto"]
        .dropna()
        .astype(str)
        .unique()
    )

    produtos_default = [
        p for p in filtros.get("produtos", [])
        if p in produtos
    ]

    produtos_selecionados = st.sidebar.multiselect(
        "Produtos",
        produtos,
        default=produtos_default
    )

    if produtos_selecionados:

        df = df[
            df["Produto"]
            .astype(str)
            .isin(produtos_selecionados)
        ]

# ===================================
# FILTRO PC
# ===================================

if "PC" in df.columns:

    pcs = sorted(
        df["PC"]
        .dropna()
        .astype(str)
        .unique()
    )

    pcs_default = [
        p for p in filtros.get("pcs", [])
        if p in pcs
    ]

    pcs_selecionados = st.sidebar.multiselect(
        "Programação de carga",
        pcs,
        default=pcs_default
    )

    if pcs_selecionados:

        df = df[
            df["PC"]
            .astype(str)
            .isin(pcs_selecionados)
        ]

# ===================================
# SEM DADOS
# ===================================

if df.empty:

    st.warning("⚠️ Nenhum dado encontrado.")
    st.stop()

# ===================================
# INDICADORES
# ===================================

st.subheader("Indicadores")

total_pedidos = (
    df["Pedido"].nunique()
    if "Pedido" in df.columns
    else len(df)
)

total_pecas = len(df)

total_m2 = (
    pd.to_numeric(
        df["M2 Vendido"],
        errors="coerce"
    ).sum()
    if "M2 Vendido" in df.columns
    else 0
)

total_peso = (
    pd.to_numeric(
        df["Peso"],
        errors="coerce"
    ).sum()
    if "Peso" in df.columns
    else 0
)

total_rotas = (
    df["Rota"].nunique()
    if "Rota" in df.columns
    else 0
)

# ===================================
# ATRASADOS
# ===================================

pedidos_atrasados = 0

if "Previsão" in df.columns:

    limite = (
        datetime.now() + timedelta(days=2)
    ).date()

    pedidos_atrasados = len(
        df[
            df["Previsão"].dt.date < limite
        ]
    )

c1, c2, c3, c4, c5, c6 = st.columns(6)

c1.metric("Pedidos", total_pedidos)
c2.metric("Peças", total_pecas)
c3.metric("Total M²", round(total_m2, 2))
c4.metric("Peso Total", round(total_peso, 2))
c5.metric("Rotas", total_rotas)
c6.metric("⚠️ Atrasados", pedidos_atrasados)

# ===================================
# TABELA ROTA
# ===================================

st.markdown("---")

mostrar_rota = st.checkbox(
    "📊 Mostrar Tabela por Rota",
    value=True
)

if mostrar_rota:

    st.subheader("📊 Tabela por Rota")

    df_rota = df.copy()

    df_rota["Previsão Texto"] = (
        df_rota["Previsão"]
        .dt.strftime("%d/%m/%Y")
    )

    ordem_datas = sorted(
        df_rota["Previsão"].dropna().unique()
    )

    ordem_datas = [
        pd.to_datetime(data).strftime("%d/%m/%Y")
        for data in ordem_datas
    ]

    tabela_rota = pd.pivot_table(
        df_rota,
        values="M2 Vendido",
        index="Rota",
        columns="Previsão Texto",
        aggfunc="sum",
        fill_value=0,
        margins=True,
        margins_name="TOTAL GERAL"
    )

    colunas_ordenadas = [
        c for c in ordem_datas
        if c in tabela_rota.columns
    ]

    if "TOTAL GERAL" in tabela_rota.columns:

        colunas_ordenadas.append(
            "TOTAL GERAL"
        )

    tabela_rota = tabela_rota[
        colunas_ordenadas
    ]

    tabela_rota = tabela_rota.loc[
        (tabela_rota != 0).any(axis=1)
    ]

    tabela_rota = tabela_rota.round(2)

    tabela_rota = tabela_rota.replace(
        0,
        ""
    )

    st.dataframe(
        tabela_rota,
        use_container_width=True,
        height=min(
            45 * (len(tabela_rota) + 1),
            600
        )
    )

# ===================================
# TABELA PRODUTO
# ===================================

st.markdown("---")

mostrar_produto = st.checkbox(
    "🪟 Mostrar Tabela por Produto",
    value=True
)

if mostrar_produto:

    st.subheader("🪟 Tabela por Produto")

    df_produto = df.copy()

    df_produto["Previsão Texto"] = (
        df_produto["Previsão"]
        .dt.strftime("%d/%m/%Y")
    )

    ordem_datas = sorted(
        df_produto["Previsão"].dropna().unique()
    )

    ordem_datas = [
        pd.to_datetime(data).strftime("%d/%m/%Y")
        for data in ordem_datas
    ]

    tabela_produto = pd.pivot_table(
        df_produto,
        values="M2 Vendido",
        index="Produto",
        columns="Previsão Texto",
        aggfunc="sum",
        fill_value=0,
        margins=True,
        margins_name="TOTAL GERAL"
    )

    colunas_ordenadas = [
        c for c in ordem_datas
        if c in tabela_produto.columns
    ]

    if "TOTAL GERAL" in tabela_produto.columns:

        colunas_ordenadas.append(
            "TOTAL GERAL"
        )

    tabela_produto = tabela_produto[
        colunas_ordenadas
    ]

    tabela_produto = tabela_produto.loc[
        (tabela_produto != 0).any(axis=1)
    ]

    tabela_produto = tabela_produto.round(2)

    tabela_produto = tabela_produto.replace(
        0,
        ""
    )

    st.dataframe(
        tabela_produto,
        use_container_width=True,
        height=min(
            45 * (len(tabela_produto) + 1),
            600
        )
    )

# ===================================
# GRÁFICO ROTA
# ===================================

st.subheader("📈 Produção por Rota")

grafico_rota = (
    df.groupby("Rota")["M2 Vendido"]
    .sum()
    .reset_index()
)

fig_rota = px.bar(
    grafico_rota,
    x="M2 Vendido",
    y="Rota",
    orientation="h",
    text="M2 Vendido"
)

fig_rota.update_traces(
    texttemplate='%{text:.2f}',
    textposition='outside'
)

st.plotly_chart(
    fig_rota,
    use_container_width=True
)

# ===================================
# GRÁFICO PRODUTO
# ===================================

st.subheader("🪟 Produção por Produto")

grafico_produto = (
    df.groupby("Produto")["M2 Vendido"]
    .sum()
    .reset_index()
)

fig_produto = px.bar(
    grafico_produto,
    x="M2 Vendido",
    y="Produto",
    orientation="h",
    text="M2 Vendido"
)

fig_produto.update_traces(
    texttemplate='%{text:.2f}',
    textposition='outside'
)

st.plotly_chart(
    fig_produto,
    use_container_width=True
)

# ===================================
# DETALHAMENTO
# ===================================

st.markdown("---")

mostrar_detalhamento = st.checkbox(
    "🔎 Mostrar Detalhamento",
    value=False
)

if mostrar_detalhamento:

    st.subheader("🔎 Detalhamento")

    df_detalhe = df.copy()

    min_det = df_detalhe["Previsão"].min().date()
    max_det = df_detalhe["Previsão"].max().date()

    col1, col2 = st.columns(2)

    with col1:

        detalhe_inicio = st.date_input(
            "Detalhamento - Data Inicial",
            value=min_det,
            key="det_inicio",
            format="DD/MM/YYYY"
        )

    with col2:

        detalhe_fim = st.date_input(
            "Detalhamento - Data Final",
            value=max_det,
            key="det_fim",
            format="DD/MM/YYYY"
        )

    df_detalhe = df_detalhe[
        (
            df_detalhe["Previsão"].dt.date >= detalhe_inicio
        )
        &
        (
            df_detalhe["Previsão"].dt.date <= detalhe_fim
        )
    ]

    if "Previsão" in df_detalhe.columns:

        df_detalhe["Previsão"] = (
            df_detalhe["Previsão"]
            .dt.strftime("%d/%m/%Y")
        )

    st.dataframe(
        df_detalhe,
        use_container_width=True,
        height=500
    )

# ===================================
# BASE COMPLETA
# ===================================

st.markdown("---")

mostrar_base = st.checkbox(
    "📋 Mostrar Base Completa",
    value=False
)

if mostrar_base:

    st.subheader("📋 Base Completa")

    st.dataframe(
        df,
        use_container_width=True,
        height=500
    )

# ===================================
# DOWNLOAD
# ===================================

st.subheader("📥 Exportar dados filtrados")

def to_excel(df):

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Base Filtrada"
        )

    return output.getvalue()

excel_file = to_excel(df)

st.download_button(
    label="Baixar planilha filtrada (Excel)",
    data=excel_file,
    file_name="dados_filtrados.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
