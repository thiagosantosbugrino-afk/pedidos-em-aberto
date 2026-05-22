import streamlit as st
import pandas as pd
import plotly.express as px
import json
from io import BytesIO

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

# ===================================
# APLICA FILTROS SALVOS
# ===================================
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

# Se após filtros não sobrou nada
if df.empty:
    st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados. Verifique as rotas e datas na página de edição.")
    st.stop()

# ===================================
# FILTROS ADICIONAIS NA BARRA LATERAL
# ===================================

if "Cliente" in df.columns:
    clientes = sorted(df["Cliente"].dropna().astype(str).unique())
    cliente = st.sidebar.multiselect("Cliente", clientes)
    if cliente:
        df = df[df["Cliente"].astype(str).isin(cliente)]

if "Produto" in df.columns:
    produtos = sorted(df["Produto"].dropna().astype(str).unique())
    produto = st.sidebar.multiselect("Produto", produtos)
    if produto:
        df = df[df["Produto"].astype(str).isin(produto)]

# 🔹 Novo filtro Programação de Carga (PC)
if "PC" in df.columns:
    pcs = sorted(df["PC"].dropna().astype(str).unique())
    pc_selecionado = st.sidebar.multiselect("Programação de carga", pcs)
    if pc_selecionado:
        df = df[df["PC"].astype(str).isin(pc_selecionado)]

# ===================================
# INDICADORES
# ===================================
st.subheader("Indicadores")

total_pedidos = df["Pedido"].nunique() if "Pedido" in df.columns else len(df)
total_pecas = len(df)
total_m2 = pd.to_numeric(df["M2 Vendido"], errors="coerce").sum() if "M2 Vendido" in df.columns else 0
total_peso = pd.to_numeric(df["Peso"], errors="coerce").sum() if "Peso" in df.columns else 0
total_rotas = df["Rota"].nunique() if "Rota" in df.columns else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Pedidos", total_pedidos)
c2.metric("Peças", total_pecas)
c3.metric("Total M²", round(total_m2, 2))
c4.metric("Peso Total", round(total_peso, 2))
c5.metric("Rotas", total_rotas)

# ===================================
# TABELA
# ===================================
st.subheader("Pedidos Em Aberto")
if "Rota" in df.columns and "M2 Vendido" in df.columns:
    tabela = pd.pivot_table(df, values="M2 Vendido", index="Rota", aggfunc="sum", fill_value=0, margins=True, margins_name="TOTAL GERAL")
    st.dataframe(tabela, use_container_width=True, height=500)

# ===================================
# GRÁFICO POR ROTA
# ===================================
st.subheader("Produção por Rota")
if "Rota" in df.columns and "M2 Vendido" in df.columns:
    grafico_rota = df.groupby("Rota")["M2 Vendido"].sum().reset_index()
    fig_rota = px.bar(grafico_rota, x="M2 Vendido", y="Rota", orientation="h", title="Produção por Rota", text="M2 Vendido")
    fig_rota.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    st.plotly_chart(fig_rota, use_container_width=True)

# ===================================
# GRÁFICO POR PRODUTO
# ===================================
st.subheader("Produção por Produto")
if "Produto" in df.columns and "M2 Vendido" in df.columns:
    grafico_produto = df.groupby("Produto")["M2 Vendido"].sum().reset_index()
    fig_produto = px.bar(grafico_produto, x="M2 Vendido", y="Produto", orientation="h", title="Produção por Produto", text="M2 Vendido")
    fig_produto.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    st.plotly_chart(fig_produto, use_container_width=True)

# ===================================
# BASE COMPLETA
# ===================================
st.subheader("Base Completa")
st.dataframe(df, use_container_width=True, height=400)

# ===================================
# DOWNLOAD DA PLANILHA FILTRADA
# ===================================
st.subheader("📥 Exportar dados filtrados")

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Base Filtrada")
    return output.getvalue()

excel_file = to_excel(df)

st.download_button(
    label="Baixar planilha filtrada (Excel)",
    data=excel_file,
    file_name="dados_filtrados.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
