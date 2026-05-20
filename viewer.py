import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Pedidos Em Aberto - Viewer", page_icon="📊", layout="wide")
st.title("📊 Pedidos Em Aberto - Visualização")

# Lê direto do arquivo salvo pelo app principal
try:
    df = pd.read_excel("dados.xlsx", sheet_name="Base")
except FileNotFoundError:
    st.error("⚠️ Nenhum arquivo foi carregado ainda no app principal.")
    st.stop()

df.columns = df.columns.astype(str)

# ===================================
# FILTROS
# ===================================

if "Cliente" in df.columns:
    clientes = sorted(df["Cliente"].dropna().astype(str).unique())
    cliente = st.sidebar.multiselect("Cliente", clientes)
    if cliente:
        df = df[df["Cliente"].astype(str).isin(cliente)]

if "Rota" in df.columns:
    rotas = sorted(df["Rota"].dropna().astype(str).unique())
    rota = st.sidebar.multiselect("Rota", rotas)
    if rota:
        df = df[df["Rota"].astype(str).isin(rota)]

if "Produto" in df.columns:
    produtos = sorted(df["Produto"].dropna().astype(str).unique())
    produto = st.sidebar.multiselect("Produto", produtos)
    if produto:
        df = df[df["Produto"].astype(str).isin(produto)]

if "Previsão" in df.columns:
    df["Previsão"] = pd.to_datetime(df["Previsão"], errors="coerce", dayfirst=True)
    df = df.dropna(subset=["Previsão"])
    if not df.empty:
        min_date = df["Previsão"].min().
