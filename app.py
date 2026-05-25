import streamlit as st
import pandas as pd
import plotly.express as px
import json
from io import BytesIO
import os
from datetime import datetime

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
# ÚLTIMA ATUALIZAÇÃO
# ===================================

if os.path.exists("dados.xlsx"):

    data_modificacao = os.path.getmtime("dados.xlsx")

    ultima_atualizacao = datetime.fromtimestamp(
        data_modificacao
    ).strftime("%d/%m/%Y %H:%M")

    st.info(f"🕒 Última atualização: {ultima_atualizacao}")

# ===================================
# LEITURA PLANILHA
# ===================================

try:

    df = pd.read_excel(
        "dados.xlsx",
        sheet_name=0
    )

except FileNotFoundError:

    st.error("⚠️ Nenhum arquivo carregado ainda.")
    st.stop()

except Exception as e:

    st.error(f"Erro ao abrir planilha: {e}")
    st.stop()

# ===================================
# LIMPEZA
# ===================================

df.columns = (
    df.columns
    .astype(str)
    .str.strip()
)

# ===================================
# CARREGAR FILTROS SALVOS
# ===================================

filtros_salvos = {}

try:

    with open("filtros.json", "r") as f:

        filtros_salvos = json.load(f)[0]

except:

    pass

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

    pcs_padrao = filtros_salvos.get("pcs", [])

    pc_selecionado = st.sidebar.multiselect(
        "Programação de carga",
        pcs,
        default=pcs_padrao
    )

    if pc_selecionado:

        df = df[
            df["PC"]
            .astype(str)
            .isin(pc_selecionado)
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

    rotas_padrao = filtros_salvos.get("rotas", [])

    rota_selecionada = st.sidebar.multiselect(
        "Rotas",
        rotas,
        default=rotas_padrao
    )

    if rota_selecionada:

        df = df[
            df["Rota"]
            .astype(str)
            .isin(rota_selecionada)
        ]

# ===================================
# FILTRO DATA
# ===================================

if "Previsão" in df.columns:

    df["Previsão"] = pd.to_datetime(
        df["Previsão"],
        errors="coerce",
        dayfirst=True
    )

    df = df.dropna(subset=["Previsão"])

    if not df.empty:

        min_date = df["Previsão"].min().date()
        max_date = df["Previsão"].max().date()

        data_inicial_padrao = min_date
        data_final_padrao = max_date

        if "start_date" in filtros_salvos:

            data_inicial_padrao = pd.to_datetime(
                filtros_salvos["start_date"]
            ).date()

        if "end_date" in filtros_salvos:

            data_final_padrao = pd.to_datetime(
                filtros_salvos["end_date"]
            ).date()

        start_date = st.sidebar.date_input(
            "Data inicial",
            value=data_inicial_padrao
        )

        end_date = st.sidebar.date_input(
            "Data final",
            value=data_final_padrao
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

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Pedidos", total_pedidos)
c2.metric("Peças", total_pecas)
c3.metric("Total M²", round(total_m2, 2))
c4.metric("Peso Total", round(total_peso, 2))
c5.metric("Rotas", total_rotas)

# ===================================
# TABELA PRINCIPAL
# ===================================

st.subheader("Pedidos Em Aberto")

if (
    "Rota" in df.columns
    and
    "M2 Vendido" in df.columns
):

    tabela = pd.pivot_table(
        df,
        values="M2 Vendido",
        index="Rota",
        aggfunc="sum",
        fill_value=0,
        margins=True,
        margins_name="TOTAL GERAL"
    )

    st.dataframe(
        tabela,
        use_container_width=True,
        height=400
    )

# ===================================
# VISÃO POR DATA
# ===================================

st.subheader("📅 Produção por Data")

if (
    "Rota" in df.columns
    and
    "Previsão" in df.columns
    and
    "M2 Vendido" in df.columns
):

    df["Data Formatada"] = (
        df["Previsão"]
        .dt.strftime("%d/%b")
    )

    tabela_datas = pd.pivot_table(
        df,
        values="M2 Vendido",
        index="Rota",
        columns="Data Formatada",
        aggfunc="sum",
        fill_value=0,
        margins=True,
        margins_name="Total Geral"
    )

    st.dataframe(
        tabela_datas,
        use_container_width=True,
        height=500
    )

# ===================================
# GRÁFICO ROTA
# ===================================

st.subheader("Produção por Rota")

if (
    "Rota" in df.columns
    and
    "M2 Vendido" in df.columns
):

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

st.subheader("Produção por Produto")

if (
    "Produto" in df.columns
    and
    "M2 Vendido" in df.columns
):

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
# BASE COMPLETA
# ===================================

st.subheader("Base Completa")

st.dataframe(
    df,
    use_container_width=True,
    height=400
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
    label="Baixar planilha filtrada",
    data=excel_file,
    file_name="dados_filtrados.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
