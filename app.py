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

    # PREVISÃO (Coluna Previsão com duas caixas de data)
    if "Previsão" in df.columns:
        df["Previsão"] = pd.to_datetime(df["Previsão"], errors="coerce", dayfirst=True)
        df = df.dropna(subset=["Previsão"])

        if not df.empty:
            min_date = df["Previsão"].min().date()
            max_date = df["Previsão"].max().date()

            # Duas caixas separadas
            start_date = st.sidebar.date_input(
                "Data inicial",
                value=min_date,
                min_value=min_date,
                max_value=max_date,
                format="DD/MM/YYYY"
            )

            end_date = st.sidebar.date_input(
                "Data final",
                value=max_date,
                min_value=min_date,
                max_value=max_date,
                format="DD/MM/YYYY"
            )

            # Filtrar pelo intervalo
            df = df[(df["Previsão"].dt.date >= start_date) & (df["Previsão"].dt.date <= end_date)]

    # ===================================
    # INDICADORES
    # ===================================

    st.subheader("Indicadores")

    total_pedidos = len(df)
    total_m2 = 0
    total_peso = 0

    if "M2 Vendido" in df.columns:
        total_m2 = pd.to_numeric(df["M2 Vendido"], errors="coerce").sum()

