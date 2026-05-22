import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
from io import BytesIO

# =========================================
# CONFIGURAÇÃO
# =========================================

st.set_page_config(
    page_title="Pedidos Em Aberto",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Pedidos Em Aberto - Visualização")

# =========================================
# CARREGAR PLANILHA
# =========================================

if not os.path.exists("dados.xlsx"):

    st.warning("⚠️ Nenhuma planilha foi enviada ainda.")
    st.stop()

try:

    df = pd.read_excel(
        "dados.xlsx",
        sheet_name=0
    )

    # LIMPA NOMES DAS COLUNAS
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

except Exception as e:

    st.error(f"Erro ao abrir planilha: {e}")
    st.stop()

# =========================================
# APLICAR FILTROS SALVOS
# =========================================

if os.path.exists("filtros.json"):

    try:

        with open("filtros.json", "r") as f:

            filtros = json.load(f)[0]

        # =====================================
        # FILTRO ROTA
        # =====================================

        if (
            "rotas" in filtros
            and
            "Rota" in df.columns
        ):

            df = df[
                df["Rota"]
                .astype(str)
                .isin(filtros["rotas"])
            ]

        # =====================================
        # FILTRO DATA
        # =====================================

        if (
            "start_date" in filtros
            and
            "end_date" in filtros
            and
            "Previsão" in df.columns
        ):

            df["Previsão"] = pd.to_datetime(
                df["Previsão"],
                errors="coerce",
                dayfirst=True
            )

            df = df.dropna(
                subset=["Previsão"]
            )

            start_date = pd.to_datetime(
                filtros["start_date"]
            ).date()

            end_date = pd.to_datetime(
                filtros["end_date"]
            ).date()

            df = df[
                (
                    df["Previsão"].dt.date
                    >= start_date
                )
                &
                (
                    df["Previsão"].dt.date
                    <= end_date
                )
            ]

    except Exception as e:

        st.warning(
            f"Erro ao aplicar filtros: {e}"
        )

# =========================================
# SEM DADOS
# =========================================

if df.empty:

    st.warning(
        "⚠️ Nenhum dado encontrado."
    )

    st.stop()

# =========================================
# INDICADORES
# =========================================

st.subheader("📌 Indicadores")

# PEDIDOS
if "Pedido" in df.columns:

    total_pedidos = df["Pedido"].nunique()

else:

    total_pedidos = len(df)

# PEÇAS
total_pecas = len(df)

# M2
if "M2 Vendido" in df.columns:

    total_m2 = pd.to_numeric(
        df["M2 Vendido"],
        errors="coerce"
    ).sum()

else:

    total_m2 = 0

# PESO
if "Peso" in df.columns:

    total_peso = pd.to_numeric(
        df["Peso"],
        errors="coerce"
    ).sum()

else:

    total_peso = 0

# ROTAS
if "Rota" in df.columns:

    total_rotas = df["Rota"].nunique()

else:

    total_rotas = 0

# CARDS
c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    "Pedidos",
    total_pedidos
)

c2.metric(
    "Peças",
    total_pecas
)

c3.metric(
    "Total M²",
    round(total_m2, 2)
)

c4.metric(
    "Peso Total",
    round(total_peso, 2)
)

c5.metric(
    "Rotas",
    total_rotas
)

# =========================================
# TABELA RESUMO
# =========================================

st.subheader("📋 Resumo por Rota")

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

    tabela = tabela.sort_values(
        by="M2 Vendido",
        ascending=False
    )

    st.dataframe(
        tabela,
        use_container_width=True,
        height=400
    )

# =========================================
# GRÁFICO ROTA
# =========================================

st.subheader("📊 Produção por Rota")

if (
    "Rota" in df.columns
    and
    "M2 Vendido" in df.columns
):

    grafico_rota = (
        df.groupby("Rota")["M2 Vendido"]
        .sum()
        .reset_index()
        .sort_values(
            by="M2 Vendido",
            ascending=True
        )
    )

    fig_rota = px.bar(
        grafico_rota,
        x="M2 Vendido",
        y="Rota",
        orientation="h",
        text="M2 Vendido"
    )

    fig_rota.update_traces(
        texttemplate="%{text:.2f}",
        textposition="outside"
    )

    fig_rota.update_layout(
        height=600
    )

    st.plotly_chart(
        fig_rota,
        use_container_width=True
    )

# =========================================
# GRÁFICO PRODUTO / PEÇA
# =========================================

coluna_produto = None

if "Produto" in df.columns:

    coluna_produto = "Produto"

elif "Peça" in df.columns:

    coluna_produto = "Peça"

if (
    coluna_produto
    and
    "M2 Vendido" in df.columns
):

    st.subheader(
        f"📦 Produção por {coluna_produto}"
    )

    grafico_produto = (
        df.groupby(coluna_produto)["M2 Vendido"]
        .sum()
        .reset_index()
        .sort_values(
            by="M2 Vendido",
            ascending=True
        )
    )

    fig_produto = px.bar(
        grafico_produto,
        x="M2 Vendido",
        y=coluna_produto,
        orientation="h",
        text="M2 Vendido"
    )

    fig_produto.update_traces(
        texttemplate="%{text:.2f}",
        textposition="outside"
    )

    fig_produto.update_layout(
        height=700
    )

    st.plotly_chart(
        fig_produto,
        use_container_width=True
    )

# =========================================
# BASE COMPLETA
# =========================================

st.subheader("🗂️ Base Completa")

st.dataframe(
    df,
    use_container_width=True,
    height=500
)

# =========================================
# DOWNLOAD
# =========================================

st.subheader("📥 Exportar Dados")

def to_excel(df):

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Dados"
        )

    return output.getvalue()

excel_file = to_excel(df)

st.download_button(
    label="Baixar planilha filtrada",
    data=excel_file,
    file_name="dados_filtrados.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
