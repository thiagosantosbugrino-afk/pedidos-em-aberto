import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import json

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
# LIMPEZA
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

        ultima = json.load(f)

        horario = ultima["horario"]

        st.info(f"🕒 Última atualização: {horario}")

except:

    pass

# ===================================
# SIDEBAR
# ===================================

st.sidebar.title("Filtros")

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

    rota_selecionada = st.sidebar.multiselect(
        "Rota",
        rotas
    )

    if rota_selecionada:

        df = df[
            df["Rota"]
            .astype(str)
            .isin(rota_selecionada)
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

    produto_selecionado = st.sidebar.multiselect(
        "Produto",
        produtos
    )

    if produto_selecionado:

        df = df[
            df["Produto"]
            .astype(str)
            .isin(produto_selecionado)
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

    pc_selecionado = st.sidebar.multiselect(
        "Programação de carga",
        pcs
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
# EXIBIR VISÕES
# ===================================

st.sidebar.title("Visualizações")

mostrar_rota = st.sidebar.checkbox(
    "Tabela previsão por rota",
    value=True
)

mostrar_produto = st.sidebar.checkbox(
    "Tabela previsão por produto",
    value=True
)

# ===================================
# CRIAR COLUNA DATA FORMATADA
# ===================================

if "Previsão" in df.columns:

    meses_pt = {
        "Jan": "jan",
        "Feb": "fev",
        "Mar": "mar",
        "Apr": "abr",
        "May": "mai",
        "Jun": "jun",
        "Jul": "jul",
        "Aug": "ago",
        "Sep": "set",
        "Oct": "out",
        "Nov": "nov",
        "Dec": "dez"
    }

    df["DATA_FORMATADA"] = (
        df["Previsão"]
        .dt.strftime("%d/%b")
        .replace(meses_pt, regex=True)
    )

# ===================================
# TABELA PREVISÃO POR ROTA
# ===================================

if mostrar_rota:

    st.subheader("📅 Previsão por Rota")

    try:

        tabela_rota = pd.pivot_table(
            df,
            values="M2 Vendido",
            index="Rota",
            columns="DATA_FORMATADA",
            aggfunc="sum",
            fill_value=0
        )

        tabela_rota.loc["Total Geral"] = tabela_rota.sum()

        tabela_rota["Total Geral"] = tabela_rota.sum(axis=1)

        tabela_rota = tabela_rota.replace(0, "")

        st.dataframe(
            tabela_rota,
            use_container_width=True,
            height=500
        )

    except Exception as e:

        st.error(f"Erro na tabela por rota: {e}")

# ===================================
# TABELA PREVISÃO POR PRODUTO
# ===================================

if mostrar_produto:

    st.subheader("📅 Previsão por Produto")

    try:

        tabela_produto = pd.pivot_table(
            df,
            values="M2 Vendido",
            index="Produto",
            columns="DATA_FORMATADA",
            aggfunc="sum",
            fill_value=0
        )

        tabela_produto.loc["Total Geral"] = tabela_produto.sum()

        tabela_produto["Total Geral"] = tabela_produto.sum(axis=1)

        tabela_produto = tabela_produto.replace(0, "")

        st.dataframe(
            tabela_produto,
            use_container_width=True,
            height=500
        )

    except Exception as e:

        st.error(f"Erro na tabela por produto: {e}")

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
