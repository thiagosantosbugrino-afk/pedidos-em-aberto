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
# LIMPEZA DAS COLUNAS
# ===================================

df.columns = (
    df.columns
    .astype(str)
    .str.strip()
)

# ===================================
# ÚLTIMA ATUALIZAÇÃO
# ===================================

try:

    with open("ultima_atualizacao.json", "r") as f:

        dados_update = json.load(f)

        data_update = dados_update["ultima_atualizacao"]

        data_update = datetime.strptime(
            data_update,
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
# CONVERTE DATA
# ===================================

if "Previsão" in df.columns:

    df["Previsão"] = pd.to_datetime(
        df["Previsão"],
        errors="coerce",
        dayfirst=True
    )

# ===================================
# FILTROS SALVOS
# ===================================

try:

    with open("filtros.json", "r") as f:

        filtros = json.load(f)[0]

except:

    filtros = {}

# ===================================
# FILTRO SIDEBAR
# ===================================

st.sidebar.title("Filtros")

# DATA

if "Previsão" in df.columns:

    min_data = df["Previsão"].min().date()
    max_data = df["Previsão"].max().date()

    start_date = st.sidebar.date_input(
        "Data inicial",
        value=min_data
    )

    end_date = st.sidebar.date_input(
        "Data final",
        value=max_data
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

# ROTA

if "Rota" in df.columns:

    rotas = sorted(
        df["Rota"]
        .dropna()
        .astype(str)
        .unique()
    )

    rotas_default = filtros.get("rotas", [])

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

# PRODUTO

if "Produto" in df.columns:

    produtos = sorted(
        df["Produto"]
        .dropna()
        .astype(str)
        .unique()
    )

    produtos_selecionados = st.sidebar.multiselect(
        "Produtos",
        produtos
    )

    if produtos_selecionados:

        df = df[
            df["Produto"]
            .astype(str)
            .isin(produtos_selecionados)
        ]

# PC

if "PC" in df.columns:

    pcs = sorted(
        df["PC"]
        .dropna()
        .astype(str)
        .unique()
    )

    pcs_default = filtros.get("pcs", [])

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

    st.warning(
        "⚠️ Nenhum dado encontrado."
    )

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
# MOSTRAR / OCULTAR
# ===================================

mostrar_rota = st.checkbox(
    "📊 Mostrar Tabela por Rota",
    value=True
)

mostrar_produto = st.checkbox(
    "🪟 Mostrar Tabela por Produto",
    value=True
)

mostrar_base = st.checkbox(
    "📋 Mostrar Base Completa",
    value=False
)

mostrar_detalhamento = st.checkbox(
    "🔎 Mostrar Detalhamento",
    value=False
)

# ===================================
# TABELA POR ROTA
# ===================================

if mostrar_rota:

    st.subheader("📊 Tabela por Rota")

    if (
        "Rota" in df.columns
        and
        "Previsão" in df.columns
        and
        "M2 Vendido" in df.columns
    ):

        df_rota = df.copy()

        df_rota["Previsão Texto"] = (
            df_rota["Previsão"]
            .dt.strftime("%d/%m/%Y")
        )

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

        tabela_rota = tabela_rota.replace(
            0,
            ""
        )

        st.dataframe(
            tabela_rota,
            use_container_width=True,
            height=400
        )

# ===================================
# TABELA POR PRODUTO
# ===================================

if mostrar_produto:

    st.subheader("🪟 Tabela por Produto")

    if (
        "Produto" in df.columns
        and
        "Previsão" in df.columns
        and
        "M2 Vendido" in df.columns
    ):

        df_produto = df.copy()

        df_produto["Previsão Texto"] = (
            df_produto["Previsão"]
            .dt.strftime("%d/%m/%Y")
        )

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

        tabela_produto = tabela_produto.replace(
            0,
            ""
        )

        st.dataframe(
            tabela_produto,
            use_container_width=True,
            height=400
        )

# ===================================
# GRÁFICO POR ROTA
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

    fig_rota.update_traces(
        texttemplate='%{text:.2f}',
        textposition='outside'
    )

    st.plotly_chart(
        fig_rota,
        use_container_width=True
    )

# ===================================
# GRÁFICO POR PRODUTO
# ===================================

st.subheader("🪟 Produção por Produto")

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
# DETALHAMENTO
# ===================================

if mostrar_detalhamento:

    st.subheader("🔎 Detalhamento")

    df_detalhe = df.copy()

    if "Previsão" in df_detalhe.columns:

        min_det = df_detalhe["Previsão"].min().date()
        max_det = df_detalhe["Previsão"].max().date()

        col1, col2 = st.columns(2)

        with col1:

            detalhe_inicio = st.date_input(
                "Detalhamento - Data Inicial",
                value=min_det,
                key="det_inicio"
            )

        with col2:

            detalhe_fim = st.date_input(
                "Detalhamento - Data Final",
                value=max_det,
                key="det_fim"
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

    if "Pedido" in df_detalhe.columns:

        pedidos = sorted(
            df_detalhe["Pedido"]
            .dropna()
            .astype(str)
            .unique()
        )

        pedido_sel = st.selectbox(
            "Selecione o Pedido",
            ["Todos"] + pedidos
        )

        if pedido_sel != "Todos":

            df_detalhe = df_detalhe[
                df_detalhe["Pedido"]
                .astype(str) == pedido_sel
            ]

    st.dataframe(
        df_detalhe,
        use_container_width=True,
        height=400
    )

# ===================================
# BASE COMPLETA
# ===================================

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
