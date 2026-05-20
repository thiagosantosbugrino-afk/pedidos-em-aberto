import streamlit as st
import pandas as pd
import plotly.express as px
import json

st.set_page_config(page_title="Pedidos Em Aberto - Visualização", page_icon="📊", layout="wide")
st.title("📊 Pedidos Em Aberto - Visualização")

# Lê planilha
try:
    df = pd.read_excel("dados.xlsx", sheet_name=0)
except FileNotFoundError:
    st.error("⚠️ Nenhum arquivo foi carregado ainda na página de edição.")
    st.stop()
except Exception as e:
    st.error(f"Erro ao abrir a planilha: {e}")
    st.stop()

df.columns = df.columns.astype(str)

# Aplica filtros salvos
try:
    with open("filtros.json", "r") as f:
        filtros = json.load(f)[0]

    # Filtro de rotas
    if "rotas" in filtros and "Rota" in df.columns:
        df = df[df["Rota"].astype(str).isin(filtros["rotas"])]

    # Filtro de datas
    if "start_date" in filtros and "end_date" in filtros and "Previsão" in df.columns:
        df["Previsão"] = pd.to_datetime(df["Previsão"], errors="coerce", dayfirst=True)
        df = df.dropna(subset=["Previsão"])
        start_date = pd.to_datetime(filtros["start_date"]).date()
        end_date = pd.to_datetime(filtros["end_date"]).date()
        df = df[(df["Previsão"].dt.date >= start_date) & (df["Previsão"].dt.date <= end_date)]
except FileNotFoundError:
    pass

# ... (resto do código igual: indicadores, tabela, gráficos por rota e produto, base completa)
