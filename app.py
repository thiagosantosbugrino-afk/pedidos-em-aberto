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

    df_original = pd.read_excel(
        "dados.xlsx",
        sheet_name=0
    )

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

# ROTA VAZIA = RETIRA

if "Rota" in df.columns:

    df["Rota"] = (
        df["Rota"]
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
# ROTA
# ===================================

rotas_sel = []

if "Rota" in df.columns:

    rotas = sorted(
        df["Rota"]
        .dropna()
        .astype(str)
        .unique()
    )

    rotas_default = [
        r for r in filtros.get("rotas", [])
        if r in rotas
    ]

    rotas_sel = st.sidebar.multiselect(
        "Rotas",
        rotas,
        default=rotas_default
    )

# ===================================
# PRODUTO
# ===================================

produtos_sel = []

if "Produto" in df.columns:

    produtos = sorted(
        df["Produto"]
        .dropna()
        .astype(str)
        .unique()
    )

    produtos_default = [
        p for p in filtros.get("produtos", [])
        if p in produtos
    ]

    produtos_sel = st.sidebar.multiselect(
        "Produtos",
        produtos,
        default=produtos_default
    )

# ===================================
# PC
# ===================================

pcs_sel = []

if "PC" in df.columns:

    pcs = sorted(
        df["PC"]
        .dropna()
        .astype(str)
        .unique()
    )

    pcs_default = [
        p for p in filtros.get("pcs", [])
        if p in pcs
    ]

    pcs_sel = st.sidebar.multiselect(
        "Programação de carga",
        pcs,
        default=pcs_default
    )

# ===================================
# ROTAS MANUAIS
# ===================================

rotas_manuais = filtros.get(
    "rotas_manuais",
    []
)

rotas_manuais = [
    str(r).strip()
    for r in rotas_manuais
    if r
]

# ===================================
# PEDIDOS MANUAIS
# ===================================

pedidos_manuais = filtros.get(
    "pedidos_manuais",
    []
)

pedidos_manuais = [
    str(p).strip()
    for p in pedidos_manuais
    if p
]

# ===================================
# FILTROS COMBINADOS
# ===================================

lista_dfs = []

# PCS
if pcs_sel:

    df_pc = df[
        df["PC"]
        .astype(str)
        .isin(pcs_sel)
    ]

    lista_dfs.append(df_pc)

# ROTAS MANUAIS
if rotas_manuais:

    df_rotas_manuais = df[
        df["Rota"]
        .astype(str)
        .isin(rotas_manuais)
    ]

    lista_dfs.append(df_rotas_manuais)

# PEDIDOS MANUAIS
if pedidos_manuais:

    df_pedidos_manuais = df[
        df["Pedido"]
        .astype(str)
        .isin(pedidos_manuais)
    ]

    lista_dfs.append(df_pedidos_manuais)

# SELEÇÃO FINAL

if lista_dfs:

    df = pd.concat(
        lista_dfs,
        ignore_index=True
    ).drop_duplicates()

# ===================================
# SIDEBAR FILTROS SALVOS
# ===================================

st.sidebar.markdown("---")

with st.sidebar.expander(
    "📌 Filtros salvos",
    expanded=True
):

    st.markdown(
        f"🚚 Rotas: {rotas_sel if rotas_sel else 'Todas'}"
    )

    st.markdown(
        f"📦 Produtos: {produtos_sel if produtos_sel else 'Todos'}"
    )

    st.markdown(
        f"📋 PCs: {pcs_sel if pcs_sel else 'Todas'}"
    )

    st.markdown(
        f"🚛 Rotas manuais: {rotas_manuais if rotas_manuais else 'Nenhuma'}"
    )

    st.markdown(
        f"🧾 Pedidos manuais: {pedidos_manuais if pedidos_manuais else 'Nenhum'}"
    )
# ===================================
# FILTROS SALVOS
# ===================================

with st.sidebar.expander(
    "📌 Filtros salvos",
    expanded=True
):

    st.markdown(
        f"🚚 Rotas: {rotas_sel if rotas_sel else 'Todas'}"
    )

    st.markdown(
        f"📦 Produtos: {produtos_sel if produtos_sel else 'Todos'}"
    )

    st.markdown(
        f"📋 PCs: {pcs_sel if pcs_sel else 'Todas'}"
    )

    st.markdown(
        f"🚛 Rotas manuais: {rotas_manuais if rotas_manuais else 'Nenhuma'}"
    )

    st.markdown(
        f"🧾 Pedidos manuais: {pedidos_manuais if pedidos_manuais else 'Nenhum'}"
    )

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
# FILTRO PC
# ===================================

if "PC" in df.columns:

    pcs = sorted(
        df["PC"]
        .dropna()
        .astype(str)
        .unique()
    )

    pcs_default = [
        p for p in filtros.get("pcs", [])
        if p in pcs
    ]

    pcs_sel = st.sidebar.multiselect(
        "Programação de carga",
        pcs,
        default=pcs_default
    )

# ===================================
# ROTAS MANUAIS
# ===================================

rotas_manuais = filtros.get(
    "rotas_manuais",
    []
)

rotas_manuais = [
    str(r).strip()
    for r in rotas_manuais
    if r
]

# ===================================
# PEDIDOS MANUAIS
# ===================================

pedidos_manuais = filtros.get(
    "pedidos_manuais",
    []
)

pedidos_manuais = [
    str(p).strip()
    for p in pedidos_manuais
    if p
]

# ===================================
# APLICA FILTROS COMBINADOS
# ===================================

df_base = df.copy()

lista_filtros = []

# PC
if pcs_sel:

    df_pc = df_base[
        df_base["PC"]
        .astype(str)
        .isin(pcs_sel)
    ]

    lista_filtros.append(df_pc)

# ROTA MANUAL
if rotas_manuais:

    df_rota_manual = df_base[
        df_base["Rota"]
        .astype(str)
        .isin(rotas_manuais)
    ]

    lista_filtros.append(df_rota_manual)

# PEDIDOS MANUAIS
if pedidos_manuais:

    df_pedido_manual = df_base[
        df_base["Pedido"]
        .astype(str)
        .isin(pedidos_manuais)
    ]

    lista_filtros.append(df_pedido_manual)

# SE TIVER ALGUM FILTRO ESPECIAL
if lista_filtros:

    df = pd.concat(
        lista_filtros,
        ignore_index=True
    ).drop_duplicates()

else:

    df = df_base.copy()

# ===================================
# SIDEBAR - FILTROS MANUAIS
# ===================================

st.sidebar.markdown("---")

st.sidebar.subheader("📌 Filtros manuais")

# ROTAS
if rotas_manuais:

    st.sidebar.success(
        "🚚 Rotas Manuais"
    )

    st.sidebar.info(
        " | ".join(rotas_manuais)
    )

# PEDIDOS
if pedidos_manuais:

    st.sidebar.success(
        "🧾 Pedidos Manuais"
    )

    st.sidebar.info(
        " | ".join(pedidos_manuais)
    )

if (
    not rotas_manuais
    and
    not pedidos_manuais
):

    st.sidebar.warning(
        "Nenhum filtro manual"
    )

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

# ATRASADOS

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

    tabela_rota = tabela_rota.loc[
        (tabela_rota != 0).any(axis=1)
    ]

    tabela_rota = tabela_rota.loc[
        :,
        (tabela_rota != 0).any(axis=0)
    ]

    tabela_rota = tabela_rota.replace(
        0,
        ""
    )

    tabela_rota = tabela_rota.astype(str)

    html_rota = tabela_rota.to_html(
        classes="tabela-centralizada",
        border=0
    )

    st.markdown(
        html_rota,
        unsafe_allow_html=True
    )
