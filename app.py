import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os

from io import BytesIO
from datetime import datetime
from zoneinfo import ZoneInfo

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

    ultima_atualizacao = datetime.fromtimestamp(
        os.path.getmtime("dados.xlsx"),
        tz=ZoneInfo("America/Sao_Paulo")
    )

    meses_pt = {
        1: "janeiro",
        2: "fevereiro",
        3: "março",
        4: "abril",
        5: "maio",
        6: "junho",
        7: "julho",
        8: "agosto",
        9: "setembro",
        10: "outubro",
        11: "novembro",
        12: "dezembro"
    }

    data_formatada = (
        f"{ultima_atualizacao.day:02d} de "
        f"{meses_pt[ultima_atualizacao.month]} de "
        f"{ultima_atualizacao.year} às "
        f"{ultima_atualizacao.strftime('%H:%M:%S')}"
    )

    st.caption(f"🕒 Última atualização: {data_formatada}")

# ===================================
# LEITURA DA PLANILHA
# ===================================

try:

    df = pd.read_excel(
        "dados.xlsx",
        sheet_name=0
    )

except FileNotFoundError:

    st.error("⚠️ Nenhum arquivo carregado.")
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
# FILTROS SALVOS
# ===================================

filtros = {}

try:

    with open("filtros.json", "r") as f:

        filtros = json.load(f)[0]

except:

    pass

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

    rotas_padrao = filtros.get("rotas", [])

    rotas_selecionadas = st.sidebar.multiselect(
        "Rota",
        rotas,
        default=rotas_padrao
    )

    if rotas_selecionadas:

        df = df[
            df["Rota"]
            .astype(str)
            .isin(rotas_selecionadas)
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

    df = df.dropna(
        subset=["Previsão"]
    )

    if not df.empty:

        min_date = df["Previsão"].min().date()
        max_date = df["Previsão"].max().date()

        start_padrao = filtros.get(
            "start_date",
            str(min_date)
        )

        end_padrao = filtros.get(
            "end_date",
            str(max_date)
        )

        start_date = st.sidebar.date_input(
            "Data inicial",
            value=pd.to_datetime(start_padrao).date(),
            min_value=min_date,
            max_value=max_date,
            format="DD/MM/YYYY",
            locale="pt_BR"
        )

        end_date = st.sidebar.date_input(
            "Data final",
            value=pd.to_datetime(end_padrao).date(),
            min_value=min_date,
            max_value=max_date,
            format="DD/MM/YYYY",
            locale="pt_BR"
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
# FILTRO PC
# ===================================

if "PC" in df.columns:

    pcs = sorted(
        df["PC"]
        .dropna()
        .astype(str)
        .unique()
    )

    pcs_padrao = filtros.get("pcs", [])

    pcs_selecionados = st.sidebar.multiselect(
        "Programação de carga",
        pcs,
        default=pcs_padrao
    )

    if pcs_selecionados:

        df = df[
            df["PC"]
            .astype(str)
            .isin(pcs_selecionados)
        ]

# ===================================
# SE NÃO SOBRAR DADOS
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

mostrar_tabela_rota = st.checkbox(
    "Mostrar tabela por rota",
    value=True
)

mostrar_tabela_produto = st.checkbox(
    "Mostrar tabela por produto",
    value=True
)

mostrar_base = st.checkbox(
    "Mostrar base completa",
    value=False
)

# ===================================
# TABELA POR ROTA
# ===================================

if (
    mostrar_tabela_rota
    and
    "Rota" in df.columns
    and
    "M2 Vendido" in df.columns
):

    st.subheader("Previsão por Rota")

    tabela_rota = pd.pivot_table(
        df,
        values="M2 Vendido",
        index="Rota",
        columns=df["Previsão"].dt.strftime("%d/%m/%Y"),
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
# DETALHAMENTO POR ROTA
# ===================================

if "Rota" in df.columns:

    st.subheader("Detalhamento por Rota")

    rota_detalhe = st.selectbox(
        "Escolha a rota",
        sorted(df["Rota"].dropna().astype(str).unique())
    )

    filtro_data = st.radio(
        "Filtrar por:",
        ["Uma data", "Período"]
    )

    df_detalhe = df[
        df["Rota"].astype(str) == rota_detalhe
    ]

    if filtro_data == "Uma data":

        data_unica = st.date_input(
            "Escolha a data",
            value=df["Previsão"].min().date(),
            format="DD/MM/YYYY",
            locale="pt_BR"
        )

        df_detalhe = df_detalhe[
            df_detalhe["Previsão"].dt.date == data_unica
        ]

    else:

        data_inicio = st.date_input(
            "Data inicial detalhe",
            value=df["Previsão"].min().date(),
            format="DD/MM/YYYY",
            locale="pt_BR"
        )

        data_fim = st.date_input(
            "Data final detalhe",
            value=df["Previsão"].max().date(),
            format="DD/MM/YYYY",
            locale="pt_BR"
        )

        df_detalhe = df_detalhe[
            (
                df_detalhe["Previsão"].dt.date >= data_inicio
            )
            &
            (
                df_detalhe["Previsão"].dt.date <= data_fim
            )
        ]

    st.dataframe(
        df_detalhe,
        use_container_width=True,
        height=400
    )

# ===================================
# TABELA POR PRODUTO
# ===================================

if (
    mostrar_tabela_produto
    and
    "Produto" in df.columns
    and
    "M2 Vendido" in df.columns
):

    st.subheader("Previsão por Produto")

    produtos = sorted(
        df["Produto"]
        .dropna()
        .astype(str)
        .unique()
    )

    produto_filtro = st.multiselect(
        "Filtrar produtos",
        produtos
    )

    df_produto = df.copy()

    if produto_filtro:

        df_produto = df_produto[
            df_produto["Produto"]
            .astype(str)
            .isin(produto_filtro)
        ]

    tabela_produto = pd.pivot_table(
        df_produto,
        values="M2 Vendido",
        index="Produto",
        columns=df_produto["Previsão"].dt.strftime("%d/%m/%Y"),
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

if (
    "Rota" in df.columns
    and
    "M2 Vendido" in df.columns
):

    st.subheader("Produção por Rota")

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

if (
    "Produto" in df.columns
    and
    "M2 Vendido" in df.columns
):

    st.subheader("Produção por Produto")

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
# BASE COMPLETA
# ===================================

if mostrar_base:

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
    label="Baixar planilha filtrada (Excel)",
    data=excel_file,
    file_name="dados_filtrados.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
