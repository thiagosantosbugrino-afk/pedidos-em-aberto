import streamlit as st
import pandas as pd
import plotly.express as px

# CONFIG
st.set_page_config(
    page_title="Pedidos Em Aberto",
    page_icon="📊",
    layout="wide"
)

# TÍTULO
st.title("📊 Pedidos Em Aberto - Controle de Produção")

# SIDEBAR
st.sidebar.title("Filtros")

# UPLOAD
arquivo = st.file_uploader(
    "Importar planilha",
    type=["xlsx"]
)

if arquivo:

    # LEITURA EXCEL
    df = pd.read_excel(
        arquivo,
        sheet_name="Base"
    )

    # LIMPEZA
    df.columns = df.columns.astype(str)

    # ===================================
    # FILTROS
    # ===================================

    # CLIENTE
    if "Cliente" in df.columns:
        clientes = sorted(df["Cliente"].dropna().astype(str).unique())
        cliente = st.sidebar.multiselect("Cliente", clientes)
        if cliente:
            df = df[df["Cliente"].astype(str).isin(cliente)]

    # ROTA
    if "Rota" in df.columns:
        rotas = sorted(df["Rota"].dropna().astype(str).unique())
        rota = st.sidebar.multiselect("Rota", rotas)
        if rota:
            df = df[df["Rota"].astype(str).isin(rota)]

    # PRODUTO
    if "Produto" in df.columns:
        produtos = sorted(df["Produto"].dropna().astype(str).unique())
        produto = st.sidebar.multiselect("Produto", produtos)
        if produto:
            df = df[df["Produto"].astype(str).isin(produto)]

    # ===================================
    # INDICADORES
    # ===================================

    st.subheader("Indicadores")

    total_pedidos = len(df)
    total_m2 = 0
    total_peso = 0

    if "M2 Vendido" in df.columns:
        total_m2 = pd.to_numeric(df["M2 Vendido"], errors="coerce").sum()

    if "Peso" in df.columns:
        total_peso = pd.to_numeric(df["Peso"], errors="coerce").sum()

    total_rotas = 0
    if "Rota" in df.columns:
        total_rotas = df["Rota"].nunique()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pedidos", total_pedidos)
    c2.metric("Total M²", round(total_m2, 2))
    c3.metric("Peso Total", round(total_peso, 2))
    c4.metric("Rotas", total_rotas)

    # ===================================
    # TABELA Pedidos Em Aberto
    # ===================================

    st.subheader("Pedidos Em Aberto")

    if "Rota" in df.columns and "M2 Vendido" in df.columns:
        tabela = pd.pivot_table(
            df,
            values="M2 Vendido",
            index="Rota",
            aggfunc="sum",
            fill_value=0,
            margins=True,
            margins_name="TOTAL GERAL"
        )
        st.dataframe(tabela, use_container_width=True, height=500)

    # ===================================
    # GRÁFICO
    # ===================================

    st.subheader("Produção por Rota")

    if "Rota" in df.columns and "M2 Vendido" in df.columns:
        grafico = df.groupby("Rota")["M2 Vendido"].sum().reset_index()
        fig = px.bar(
            grafico,
            x="M2 Vendido",
            y="Rota",
            orientation="h",
            title="Produção por Rota"
        )
        st.plotly_chart(fig, use_container_width=True)

    # ===================================
    # BASE COMPLETA
    # ===================================

    st.subheader("Base Completa")
    st.dataframe(df, use_container_width=True, height=400)

else:
    st.info("Importe sua planilha Excel.")
