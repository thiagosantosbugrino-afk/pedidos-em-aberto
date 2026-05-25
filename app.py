import streamlit as st
import pandas as pd
import plotly.express as px
import json
from io import BytesIO
from datetime import datetime
import pytz
import os

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

    fuso_brasil = pytz.timezone("America/Sao_Paulo")

    timestamp = os.path.getmtime("dados.xlsx")

    horario = datetime.fromtimestamp(
        timestamp,
        tz=fuso_brasil
    )

    horario_formatado = horario.strftime("%d/%m/%Y %H:%M:%S")

    st.info(f"🕒 Última atualização: {horario_formatado}")

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
# APLICA FILTROS SALVOS
# ===================================

try:

    with open("filtros.json", "r") as f:

        filtros = json.load(f)[0]

    # ===================================
    # ROTA
    # ===================================

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

    # ===================================
    # DATA
    # ===================================

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
# TABELA DINÂMICA ROTA
# ===================================

st.markdown("---")

mostrar_tabela_rota = st.checkbox(
    "Mostrar visão por Rota",
    value=True
)

if (
    mostrar_tabela_rota
    and "Rota" in df.columns
    and "Previsão" in df.columns
    and "M2 Vendido" in df.columns
):

    st.subheader("📊 Pedidos por Rota e Data")

    df["Previsão"] = pd.to_datetime(
        df["Previsão"],
        errors="coerce",
        dayfirst=True
    )

    meses_pt = {
        1: "jan",
        2: "fev",
        3: "mar",
        4: "abr",
        5: "mai",
        6: "jun",
        7: "jul",
        8: "ago",
        9: "set",
        10: "out",
        11: "nov",
        12: "dez"
    }

    df["Data_Formatada"] = df["Previsão"].apply(
        lambda x: f"{x.day}/{meses_pt[x.month]}"
        if pd.notnull(x)
        else ""
    )

    tabela_rota = pd.pivot_table(
        df,
        values="M2 Vendido",
        index="Rota",
        columns="Data_Formatada",
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
    # DETALHAMENTO
    # ===================================

    st.markdown("---")
    st.subheader("🔎 Detalhamento")

    col1, col2 = st.columns(2)

    with col1:

        rota_detalhe = st.selectbox(
            "Selecione a rota",
            sorted(
                df["Rota"]
                .dropna()
                .astype(str)
                .unique()
            )
        )

    with col2:

        data_detalhe = st.selectbox(
            "Selecione a data",
            sorted(
                df["Data_Formatada"]
                .dropna()
                .astype(str)
                .unique()
            )
        )

    detalhe = df[
        (
            df["Rota"].astype(str)
            == rota_detalhe
        )
        &
        (
            df["Data_Formatada"].astype(str)
            == data_detalhe
        )
    ]

    colunas_exibir = []

    for coluna in [
        "Pedido",
        "Cliente",
        "Produto",
        "PC",
        "M2 Vendido",
        "Peso",
        "Previsão"
    ]:

        if coluna in detalhe.columns:

            colunas_exibir.append(coluna)

    st.dataframe(
        detalhe[colunas_exibir],
        use_container_width=True,
        height=400
    )

# ===================================
# TABELA DINÂMICA PRODUTO
# ===================================

st.markdown("---")

mostrar_tabela_produto = st.checkbox(
    "Mostrar visão por Produto",
    value=True
)

if (
    mostrar_tabela_produto
    and "Produto" in df.columns
    and "Previsão" in df.columns
    and "M2 Vendido" in df.columns
):

    st.subheader("📊 Produção por Produto e Data")

    filtro_produto = st.multiselect(
        "Filtrar produtos",
        sorted(
            df["Produto"]
            .dropna()
            .astype(str)
            .unique()
        )
    )

    if filtro_produto:

        df_produto = df[
            df["Produto"]
            .astype(str)
            .isin(filtro_produto)
        ]

    else:

        df_produto = df.copy()

    tabela_produto = pd.pivot_table(
        df_produto,
        values="M2 Vendido",
        index="Produto",
        columns="Data_Formatada",
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

st.markdown("---")

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
# GRÁFICO PRODUTO
# ===================================

st.markdown("---")

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

st.markdown("---")

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

st.markdown("---")

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
