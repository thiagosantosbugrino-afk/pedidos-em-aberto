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

    df = pd.read_excel(
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

df.columns = (
    df.columns
    .astype(str)
    .str.strip()
)

# PEDIDO

if "Pedido" in df.columns:

    df["Pedido"] = (
        df["Pedido"]
        .astype(str)
        .str.replace(".0", "", regex=False)
    )

# PC

if "PC" in df.columns:

    df["PC"] = (
        df["PC"]
        .astype(str)
        .str.replace(".0", "", regex=False)
    )

# DATA

if "Previsão" in df.columns:

    df["Previsão"] = pd.to_datetime(
        df["Previsão"],
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

    if rotas_sel:

        df = df[
            df["Rota"]
            .astype(str)
            .isin(rotas_sel)
        ]

# ===================================
# PRODUTO
# ===================================

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

    if produtos_sel:

        df = df[
            df["Produto"]
            .astype(str)
            .isin(produtos_sel)
        ]

# ===================================
# PC
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

    if pcs_sel:

        df = df[
            df["PC"]
            .astype(str)
            .isin(pcs_sel)
        ]

# ===================================
# BASE COMPLETA
# ===================================

df_base = pd.read_excel("dados.xlsx")
df_base.columns = df_base.columns.astype(str).str.strip()

# aplica filtros normais em df_filtrado
df_filtrado = df.copy()

# ===================================
# PEDIDOS MANUAIS
# ===================================

df_final = df_filtrado.copy()

# Se NÃO houver programação de carga selecionada,
# restringe apenas aos pedidos/rotas manuais escolhidos
if not pcs_sel:
    df_final = pd.DataFrame()  # começa vazio

    if pedidos_manuais and "Pedido" in df_base.columns:
        df_final = pd.concat([df_final, df_base[df_base["Pedido"].isin(pedidos_manuais)]],
                             ignore_index=True).drop_duplicates()
else:
    # Se houver programação de carga, acrescenta os manuais ao filtrado
    if pedidos_manuais and "Pedido" in df_base.columns:
        df_extra = df_base[df_base["Pedido"].isin(pedidos_manuais)]
        df_final = pd.concat([df_final, df_extra], ignore_index=True).drop_duplicates()


# ===================================
# ROTAS MANUAIS
# ===================================

if not pcs_sel:
    if rotas_manuais and "Rota" in df_base.columns:
        df_final = pd.concat([df_final, df_base[df_base["Rota"].isin(rotas_manuais)]],
                             ignore_index=True).drop_duplicates()
else:
    if rotas_manuais and "Rota" in df_base.columns:
        df_extra_rotas = df_base[df_base["Rota"].isin(rotas_manuais)]
        df_final = pd.concat([df_final, df_extra_rotas], ignore_index=True).drop_duplicates()

# ===================================
# SIDEBAR - PEDIDOS MANUAIS
# ===================================

st.sidebar.markdown("---")
st.sidebar.subheader("📌 Pedidos manuais")

lista_pedidos = sorted(
    df_base["Pedido"].dropna().astype(str).unique()
) if "Pedido" in df_base.columns else []

pedidos_manuais = st.sidebar.multiselect(
    "Selecionar pedidos manuais",
    lista_pedidos,
    default=filtros.get("pedidos_manuais", [])
)

if pedidos_manuais:
    df_extra = df_base[df_base["Pedido"].isin(pedidos_manuais)]
    df_final = pd.concat([df_final, df_extra], ignore_index=True).drop_duplicates()

# ===================================
# SIDEBAR - ROTAS MANUAIS
# ===================================

st.sidebar.markdown("---")
st.sidebar.subheader("🚚 Rotas manuais")

lista_rotas = sorted(
    df_base["Rota"].dropna().astype(str).unique()
) if "Rota" in df_base.columns else []

rotas_manuais = st.sidebar.multiselect(
    "Selecionar rotas manuais",
    lista_rotas,
    default=filtros.get("rotas_manuais", [])
)

if rotas_manuais:
    df_extra_rotas = df_base[df_base["Rota"].isin(rotas_manuais)]
    df_final = pd.concat([df_final, df_extra_rotas], ignore_index=True).drop_duplicates()

# ===================================
# INDICADORES
# ===================================

st.subheader("Indicadores")

total_pedidos = (
    df_final["Pedido"].nunique()
    if "Pedido" in df_final.columns
    else 0
)

total_pecas = len(df_final)

total_m2 = (
    pd.to_numeric(
        df_final["M2 Vendido"],
        errors="coerce"
    ).sum()
    if "M2 Vendido" in df_final.columns
    else 0
)

total_peso = (
    pd.to_numeric(
        df_final["Peso"],
        errors="coerce"
    ).sum()
    if "Peso" in df_final.columns
    else 0
)

total_rotas = (
    df_final["Rota"].nunique()
    if "Rota" in df_final.columns
    else 0
)

# ATRASADOS

pedidos_atrasados = 0
m2_atrasados = 0

if "Previsão" in df_final.columns:

    limite = (
        datetime.now() + timedelta(days=2)
    ).date()

    df_atrasados = df_final[
        df_final["Previsão"].dt.date < limite
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

    df_rota = df_final.copy()

    df_rota["Previsão"] = (
        df_rota["Previsão"]
        .dt.strftime("%d/%m/%Y")
    )

    ordem_datas = sorted(
        pd.to_datetime(
            df_rota["Previsão"],
            format="%d/%m/%Y",
            errors="coerce"
        ).dropna().unique()
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
    tabela_rota = tabela_rota.loc[(tabela_rota != 0).any(axis=1)]
    tabela_rota = tabela_rota.loc[:, (tabela_rota != 0).any(axis=0)]
    tabela_rota = tabela_rota.replace(0, "")
    tabela_rota = tabela_rota.astype(str)

    html_rota = tabela_rota.to_html(
        classes="tabela-centralizada",
        border=0
    )

    st.markdown(html_rota, unsafe_allow_html=True)

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

    df_produto = df_final.copy()

    df_produto["Previsão"] = (
        df_produto["Previsão"]
        .dt.strftime("%d/%m/%Y")
    )

    ordem_datas = sorted(
        pd.to_datetime(
            df_produto["Previsão"],
            format="%d/%m/%Y",
            errors="coerce"
        ).dropna().unique()
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
    tabela_produto = tabela_produto.loc[(tabela_produto != 0).any(axis=1)]
    tabela_produto = tabela_produto.loc[:, (tabela_produto != 0).any(axis=0)]
    tabela_produto = tabela_produto.replace(0, "")
    tabela_produto = tabela_produto.astype(str)

    html_produto = tabela_produto.to_html(
        classes="tabela-centralizada",
        border=0
    )

    st.markdown(html_produto, unsafe_allow_html=True)

# ===================================
# TABELA ROTA X PRODUTO
# ===================================

st.markdown("---")

mostrar_rota_produto = st.checkbox(
    "📊 Mostrar Rota X Produto",
    value=False
)

if mostrar_rota_produto:

    st.subheader("📊 Rota X Produto")

    if (
        "Rota" in df_final.columns
        and "Produto" in df_final.columns
        and "M2 Vendido" in df_final.columns
    ):

        df_rota_produto = df_final.copy()

        tabela_rota_produto = pd.pivot_table(
            df_rota_produto,
            values="M2 Vendido",
            index="Rota",
            columns="Produto",
            aggfunc="sum",
            fill_value=0,
            margins=True,
            margins_name="TOTAL GERAL"
        )

        tabela_rota_produto = tabela_rota_produto.round(2)
        tabela_rota_produto = tabela_rota_produto.loc[(tabela_rota_produto != 0).any(axis=1)]
        tabela_rota_produto = tabela_rota_produto.loc[:, (tabela_rota_produto != 0).any(axis=0)]
        tabela_rota_produto = tabela_rota_produto.replace(0, "")
        tabela_rota_produto = tabela_rota_produto.astype(object)

        for coluna in tabela_rota_produto.columns:
            tabela_rota_produto[coluna] = tabela_rota_produto[coluna].apply(
                lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                if isinstance(x, (int, float)) else x
            )

        html_rota_produto = tabela_rota_produto.to_html(
            classes="tabela-centralizada",
            border=0
        )

        st.markdown(html_rota_produto, unsafe_allow_html=True)

# ===================================
# GRÁFICO ROTA
# ===================================

st.subheader("📈 Produção por Rota")

grafico_rota = (
    df_final.groupby("Rota")["M2 Vendido"]
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

st.plotly_chart(fig_rota, use_container_width=True)

# ===================================
# GRÁFICO PRODUTO
# ===================================

st.subheader("🪟 Produção por Produto")

grafico_produto = (
    df_final.groupby("Produto")["M2 Vendido"]
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
st.plotly_chart(fig_produto, use_container_width=True)

# ===================================
# DETALHAMENTO
# ===================================

st.markdown("---")

mostrar_detalhamento = st.checkbox(
    "🔎 Mostrar Detalhamento",
    value=False
)

if mostrar_detalhamento:

    st.subheader("🔎 Detalhamento")

    df_detalhe = df_final.copy()

    min_det = df_detalhe["Previsão"].min().date()
    max_det = df_detalhe["Previsão"].max().date()

    col1, col2 = st.columns(2)

    with col1:
        detalhe_inicio = st.date_input(
            "Detalhamento - Data Inicial",
            value=min_det,
            key="det_inicio",
            format="DD/MM/YYYY"
        )

    with col2:
        detalhe_fim = st.date_input(
            "Detalhamento - Data Final",
            value=max_det,
            key="det_fim",
            format="DD/MM/YYYY"
        )

    df_detalhe = df_detalhe[
        (df_detalhe["Previsão"].dt.date >= detalhe_inicio)
        &
        (df_detalhe["Previsão"].dt.date <= detalhe_fim)
    ]

    if "Previsão" in df_detalhe.columns:
        df_detalhe["Previsão"] = (
            df_detalhe["Previsão"].dt.strftime("%d/%m/%Y")
        )

    st.dataframe(
        df_detalhe,
        use_container_width=True,
        height=500
    )

# ===================================
# BASE COMPLETA
# ===================================

st.markdown("---")

mostrar_base = st.checkbox(
    "📋 Mostrar Base Completa",
    value=False
)

if mostrar_base:
    st.subheader("📋 Base Completa")
    st.dataframe(
        df_final,
        use_container_width=True,
        height=500
    )

# ===================================
# DOWNLOAD
# ===================================

st.subheader("📥 Exportar dados filtrados")

def to_excel(df_final):

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        df_final.to_excel(
            writer,
            index=False,
            sheet_name="Base Filtrada"
        )

    return output.getvalue()

excel_file = to_excel(df_final)

st.download_button(
    label="Baixar planilha filtrada (Excel)",
    data=excel_file,
    file_name="dados_filtrados.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
