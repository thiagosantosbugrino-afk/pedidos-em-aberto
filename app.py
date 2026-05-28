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
# CSS
# ===================================

st.markdown("""
<style>
table {
    width: 100% !important;
    border-collapse: collapse !important;
    text-align: center !important;
    font-size: 14px !important;
}
thead tr th {
    text-align: center !important;
    font-weight: bold !important;
    background-color: #f0f2f6 !important;
    padding: 8px !important;
}
tbody tr td {
    text-align: center !important;
    padding: 6px !important;
}
tbody tr:last-child {
    font-weight: bold !important;
    background-color: #f8f9fa !important;
}
</style>
""", unsafe_allow_html=True)

# ===================================
# LEITURA PLANILHA
# ===================================

try:
    df_original = pd.read_excel("dados.xlsx", sheet_name=0)

except FileNotFoundError:

    st.error("⚠️ Nenhum arquivo carregado.")
    st.stop()

except Exception as e:

    st.error(f"Erro ao abrir planilha: {e}")
    st.stop()

# ===================================
# LIMPEZA
# ===================================

df_original.columns = (
    df_original.columns
    .astype(str)
    .str.strip()
)

# PEDIDO

if "Pedido" in df_original.columns:

    df_original["Pedido"] = (
        df_original["Pedido"]
        .astype(str)
        .str.replace(".0", "", regex=False)
        .str.strip()
    )

# PC

if "PC" in df_original.columns:

    df_original["PC"] = (
        df_original["PC"]
        .astype(str)
        .str.replace(".0", "", regex=False)
        .str.strip()
    )

# ROTA

if "Rota" in df_original.columns:

    df_original["Rota"] = (
        df_original["Rota"]
        .astype(str)
        .str.strip()
        .replace(
            ["", "nan", "None"],
            "RETIRA"
        )
    )

# DATA

if "Previsão" in df_original.columns:

    df_original["Previsão"] = pd.to_datetime(
        df_original["Previsão"],
        errors="coerce",
        dayfirst=True
    )

# ===================================
# ÚLTIMA ATUALIZAÇÃO
# ===================================

try:

    with open("ultima_atualizacao.json", "r") as f:

        dados_update = json.load(f)

    data_update = datetime.strptime(
        dados_update["ultima_atualizacao"],
        "%Y-%m-%d %H:%M:%S"
    )

    data_update = data_update - timedelta(hours=3)

    data_formatada = data_update.strftime(
        "%d/%m/%Y %H:%M:%S"
    )

    st.info(
        f"🕒 Última atualização: {data_formatada}"
    )

except:

    pass

# ===================================
# FILTROS SALVOS
# ===================================

try:

    with open("filtros.json", "r") as f:

        filtros = json.load(f)[0]

except:

    filtros = {}

# ===================================
# SIDEBAR
# ===================================

st.sidebar.title("Filtros")

df = df_original.copy()

# ===================================
# DATA
# ===================================

if "Previsão" in df.columns:

    min_data = df["Previsão"].min().date()
    max_data = df["Previsão"].max().date()

    start_default = pd.to_datetime(
        filtros.get("start_date", min_data)
    ).date()

    end_default = pd.to_datetime(
        filtros.get("end_date", max_data)
    ).date()

    start_date = st.sidebar.date_input(
        "Data inicial",
        value=start_default,
        format="DD/MM/YYYY"
    )

    end_date = st.sidebar.date_input(
        "Data final",
        value=end_default,
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
# FILTROS
# ===================================

rotas_sel = filtros.get("rotas", [])
produtos_sel = filtros.get("produtos", [])
pcs_sel = filtros.get("pcs", [])
rotas_manuais = filtros.get("rotas_manuais", [])
pedidos_manuais = filtros.get("pedidos_manuais", [])

# ===================================
# MOSTRAR FILTROS SALVOS
# ===================================

with st.sidebar.expander("📌 Filtros salvos", expanded=True):

    st.write("🚚 Rotas:", rotas_sel if rotas_sel else "Todos")
    st.write("🪟 Produtos:", produtos_sel if produtos_sel else "Todos")
    st.write("📦 PCs:", pcs_sel if pcs_sel else "Todos")
    st.write("🚛 Rotas manuais:", rotas_manuais if rotas_manuais else "Nenhuma")
    st.write("🧾 Pedidos manuais:", pedidos_manuais if pedidos_manuais else "Nenhum")

# ===================================
# FILTRO COMBINADO
# ===================================

dfs_filtrados = []

# PCs

if pcs_sel and "PC" in df.columns:

    df_pc = df[
        df["PC"]
        .astype(str)
        .isin(pcs_sel)
    ]

    dfs_filtrados.append(df_pc)

# ROTAS

if rotas_sel and "Rota" in df.columns:

    df_rota = df[
        df["Rota"]
        .astype(str)
        .isin(rotas_sel)
    ]

    dfs_filtrados.append(df_rota)

# PRODUTOS

if produtos_sel and "Produto" in df.columns:

    df_produto = df[
        df["Produto"]
        .astype(str)
        .isin(produtos_sel)
    ]

    dfs_filtrados.append(df_produto)

# ROTAS MANUAIS

if rotas_manuais and "Rota" in df.columns:

    df_rota_manual = df[
        df["Rota"]
        .astype(str)
        .isin(rotas_manuais)
    ]

    dfs_filtrados.append(df_rota_manual)

# PEDIDOS MANUAIS

if pedidos_manuais and "Pedido" in df.columns:

    pedidos_manuais = [
        str(p).strip()
        for p in pedidos_manuais
    ]

    df_manual = df[
        df["Pedido"]
        .astype(str)
        .isin(pedidos_manuais)
    ]

    dfs_filtrados.append(df_manual)

# ===================================
# UNIR TODOS FILTROS
# ===================================

if dfs_filtrados:

    df = pd.concat(
        dfs_filtrados,
        ignore_index=True
    )

    df = df.drop_duplicates()

# ===================================
# SEM DADOS
# ===================================

if df.empty:

    st.warning("⚠️ Nenhum dado encontrado.")
    st.stop()

# ===================================
# PEDIDOS MANUAIS VISUAL
# ===================================

if pedidos_manuais:

    st.markdown("---")

    st.subheader("📌 Pedidos adicionados manualmente")

    for pedido in pedidos_manuais:

        st.markdown(
            f"""
            <div style="
                background-color:#f4f6f8;
                padding:8px;
                border-radius:6px;
                margin-bottom:5px;
                border-left:4px solid #4CAF50;
            ">
                🧾 Pedido <b>{pedido}</b>
            </div>
            """,
            unsafe_allow_html=True
        )

# ===================================
# INDICADORES
# ===================================

st.subheader("Indicadores")

total_pedidos = (
    df["Pedido"].nunique()
    if "Pedido" in df.columns
    else 0
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

pedidos_atrasados = 0
m2_atrasados = 0

if "Previsão" in df.columns:

    limite = (
        datetime.now() + timedelta(days=2)
    ).date()

    df_atrasados = df[
        df["Previsão"].dt.date < limite
    ]

    pedidos_atrasados = len(df_atrasados)

    if "M2 Vendido" in df_atrasados.columns:

        m2_atrasados = pd.to_numeric(
            df_atrasados["M2 Vendido"],
            errors="coerce"
        ).sum()

c1, c2, c3, c4, c5, c6, c7 = st.columns(7)

c1.metric("Pedidos", total_pedidos)
c2.metric("Peças", total_pecas)
c3.metric("Total M²", round(total_m2, 2))
c4.metric("Peso Total", round(total_peso, 2))
c5.metric("Rotas", total_rotas)
c6.metric("⚠️ Peças Atrasadas", pedidos_atrasados)
c7.metric("⚠️ M² Atrasado", round(m2_atrasados, 2))

# ===================================
# TABELA POR ROTA
# ===================================

st.markdown("---")

mostrar_rota = st.checkbox(
    "📊 Mostrar Tabela por Rota",
    value=True
)

if mostrar_rota:

    st.subheader("📊 Tabela por Rota")

    df_rota = df.copy()

    df_rota["Previsão"] = (
        df_rota["Previsão"]
        .dt.strftime("%d/%m/%Y")
    )

    ordem_datas = sorted(
        df_rota["Previsão"].dropna().unique()
    )

    ordem_datas = [
        pd.to_datetime(d).strftime("%d/%m/%Y")
        for d in ordem_datas
    ]

    tabela_rota = pd.pivot_table(
        df_rota,
        values="M2 Vendido",
        index="Rota",
        columns="Previsão",
        aggfunc="sum",
        fill_value=0,
        margins=True,
        margins_name="TOTAL GERAL"
    )

    colunas = [
        c for c in ordem_datas
        if c in tabela_rota.columns
    ]

    if "TOTAL GERAL" in tabela_rota.columns:

        colunas.append("TOTAL GERAL")

    tabela_rota = tabela_rota[colunas]

    tabela_rota = tabela_rota.round(2)

    tabela_rota = tabela_rota.replace(0, "")

    html_rota = tabela_rota.to_html(
        classes="tabela-centralizada",
        border=0
    )

    st.markdown(
        html_rota,
        unsafe_allow_html=True
    )

# ===================================
# TABELA PRODUTO
# ===================================

st.markdown("---")

mostrar_produto = st.checkbox(
    "🪟 Mostrar Tabela por Produto",
    value=True
)

if mostrar_produto:

    st.subheader("🪟 Tabela por Produto")

    df_produto = df.copy()

    df_produto["Previsão"] = (
        df_produto["Previsão"]
        .dt.strftime("%d/%m/%Y")
    )

    ordem_datas = sorted(
        df_produto["Previsão"].dropna().unique()
    )

    ordem_datas = [
        pd.to_datetime(d).strftime("%d/%m/%Y")
        for d in ordem_datas
    ]

    tabela_produto = pd.pivot_table(
        df_produto,
        values="M2 Vendido",
        index="Produto",
        columns="Previsão",
        aggfunc="sum",
        fill_value=0,
        margins=True,
        margins_name="TOTAL GERAL"
    )

    colunas = [
        c for c in ordem_datas
        if c in tabela_produto.columns
    ]

    if "TOTAL GERAL" in tabela_produto.columns:

        colunas.append("TOTAL GERAL")

    tabela_produto = tabela_produto[colunas]

    tabela_produto = tabela_produto.round(2)

    tabela_produto = tabela_produto.replace(0, "")

    html_produto = tabela_produto.to_html(
        classes="tabela-centralizada",
        border=0
    )

    st.markdown(
        html_produto,
        unsafe_allow_html=True
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
