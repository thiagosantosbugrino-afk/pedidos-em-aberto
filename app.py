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
# ÚLTIMA ATUALIZAÇÃO
# ===================================

try:

    data_modificacao = datetime.fromtimestamp(
        __import__("os").path.getmtime("dados.xlsx")
    )

    # Ajuste Brasília
    data_modificacao = data_modificacao - timedelta(hours=3)

    data_formatada = data_modificacao.strftime("%d/%m/%Y %H:%M:%S")

    st.info(f"🕒 Última atualização: {data_formatada}")

except:
    pass

# ===================================
# LEITURA DA PLANILHA
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

    st.error(f"Erro ao abrir a planilha: {e}")
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
# APLICA FILTROS SALVOS
# ===================================

try:

    with open("filtros.json", "r") as f:

        filtros = json.load(f)[0]

    # ROTA

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

    # DATA

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
                df["Previsão"].dt.date >= start_date
            )
            &
            (
                df["Previsão"].dt.date <= end_date
            )
        ]

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

    pcs_padrao = []

    try:

        with open("filtros.json", "r") as f:

            filtros_salvos = json.load(f)[0]

            if "pcs" in filtros_salvos:

                pcs_padrao = filtros_salvos["pcs"]

    except:
        pass

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
# TABELA POR ROTA
# ===================================

mostrar_tabela_rota = st.checkbox(
    "Mostrar Tabela por Rota",
    value=True
)

if mostrar_tabela_rota:

    st.subheader("📊 Tabela por Rota")

    if (
        "Rota" in df.columns
        and
        "M2 Vendido" in df.columns
        and
        "Previsão" in df.columns
    ):

        df_rota = df.copy()

        df_rota["Previsão"] = pd.to_datetime(
            df_rota["Previsão"],
            errors="coerce",
            dayfirst=True
        )

        df_rota = df_rota.dropna(subset=["Previsão"])

        df_rota["Data"] = df_rota["Previsão"].dt.strftime("%d/%m/%Y")

        tabela_rota = pd.pivot_table(
            df_rota,
            values="M2 Vendido",
            index="Rota",
            columns="Data",
            aggfunc="sum",
            fill_value=0
        )

        tabela_rota = tabela_rota.replace(0, "")

        st.dataframe(
            tabela_rota,
            use_container_width=True,
            height=500
        )

# ===================================
# TABELA POR PRODUTO
# ===================================

mostrar_tabela_produto = st.checkbox(
    "Mostrar Tabela por Produto",
    value=True
)

if mostrar_tabela_produto:

    st.subheader("📦 Tabela por Produto")

    if (
        "Produto" in df.columns
        and
        "M2 Vendido" in df.columns
        and
        "Previsão" in df.columns
    ):

        df_produto = df.copy()

        df_produto["Previsão"] = pd.to_datetime(
            df_produto["Previsão"],
            errors="coerce",
            dayfirst=True
        )

        df_produto = df_produto.dropna(subset=["Previsão"])

        produtos = sorted(
            df_produto["Produto"]
            .dropna()
            .astype(str)
            .unique()
        )

        produto_filtro = st.multiselect(
            "Filtrar Produto",
            produtos
        )

        if produto_filtro:

            df_produto = df_produto[
                df_produto["Produto"]
                .astype(str)
                .isin(produto_filtro)
            ]

        data_inicial = st.date_input(
            "Data Inicial Produto",
            value=df_produto["Previsão"].min().date(),
            format="DD/MM/YYYY"
        )

        data_final = st.date_input(
            "Data Final Produto",
            value=df_produto["Previsão"].max().date(),
            format="DD/MM/YYYY"
        )

        df_produto = df_produto[
            (
                df_produto["Previsão"].dt.date >= data_inicial
            )
            &
            (
                df_produto["Previsão"].dt.date <= data_final
            )
        ]

        df_produto["Data"] = (
            df_produto["Previsão"]
            .dt.strftime("%d/%m/%Y")
        )

        tabela_produto = pd.pivot_table(
            df_produto,
            values="M2 Vendido",
            index="Produto",
            columns="Data",
            aggfunc="sum",
            fill_value=0
        )

        tabela_produto = tabela_produto.replace(0, "")

        st.dataframe(
            tabela_produto,
            use_container_width=True,
            height=500
        )

# ===================================
# GRÁFICO ROTA
# ===================================

st.subheader("📈 Produção por Rota")

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

    st.plotly_chart(
        fig_rota,
        use_container_width=True
    )

# ===================================
# GRÁFICO PRODUTO
# ===================================

st.subheader("📈 Produção por Produto")

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

    st.plotly_chart(
        fig_produto,
        use_container_width=True
    )

# ===================================
# DETALHAMENTO
# ===================================

st.subheader("🔍 Detalhamento")

if "Previsão" in df.columns:

    df["Previsão"] = pd.to_datetime(
        df["Previsão"],
        errors="coerce",
        dayfirst=True
    )

    data_inicio = st.date_input(
        "Detalhamento - Data Inicial",
        value=df["Previsão"].min().date(),
        format="DD/MM/YYYY"
    )

    data_fim = st.date_input(
        "Detalhamento - Data Final",
        value=df["Previsão"].max().date(),
        format="DD/MM/YYYY"
    )

    detalhe = df[
        (
            df["Previsão"].dt.date >= data_inicio
        )
        &
        (
            df["Previsão"].dt.date <= data_fim
        )
    ]

    st.dataframe(
        detalhe,
        use_container_width=True,
        height=400
    )

# ===================================
# BASE COMPLETA
# ===================================

mostrar_base = st.checkbox(
    "Mostrar Base Completa",
    value=False
)

if mostrar_base:

    st.subheader("📋 Base Completa")

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
    label="Baixar planilha filtrada (Excel)",
    data=excel_file,
    file_name="dados_filtrados.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
