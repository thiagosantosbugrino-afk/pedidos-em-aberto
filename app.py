import io
import re
import json
import streamlit as st
import pandas as pd
import plotly.express as px

from io import BytesIO
from datetime import datetime, timedelta


# ===================================
# FUNÇÕES
# ===================================

def codigo_material(texto):

    if pd.isna(texto):
        return None

    texto = str(texto).upper().strip()

    texto = texto.replace("ESI", "ESP")

    resultado = re.match(
        r"(LAMINC\d{2})",
        texto
    )

    if resultado:
        return resultado.group(1)

    resultado = re.match(
        r"([A-Z]{3}\d{2})",
        texto
    )

    if resultado:
        return resultado.group(1)

    return texto


def descricao_material(texto):

    if pd.isna(texto):
        return ""

    texto = str(texto).upper().strip()

    texto = texto.replace(
        "CHAPARIA",
        ""
    )

    texto = re.sub(
        r"\d{4}\s*[Xx]\s*\d{4}",
        "",
        texto
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    ).strip()

    texto = re.sub(
        r"\b0(\d)\s*MM\b",
        r"\1 mm",
        texto
    )

    return texto.upper()


def formatar_numero(valor):

    if pd.isna(valor):
        return ""

    return (
        f"{float(valor):,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


# ===================================
# CONFIGURAÇÃO
# ===================================

st.set_page_config(
    page_title="Pedidos Em Aberto - Visualização",
    page_icon="📊",
    layout="wide"
)

st.title(
    "📊 Pedidos Em Aberto - Visualização"
)


# ===================================
# CSS
# ===================================

st.markdown(
    """
<style>

.tabela-centralizada {
    width: 100% !important;
    border-collapse: collapse !important;
    font-size: 14px !important;
}

.tabela-centralizada th {
    text-align: center !important;
    vertical-align: middle !important;
    font-weight: bold !important;
    background-color: #f0f2f6 !important;
    padding: 8px !important;
    white-space: nowrap !important;
}

.tabela-centralizada td {
    text-align: center !important;
    vertical-align: middle !important;
    padding: 7px !important;
}

.tabela-centralizada tr:last-child td {
    font-weight: bold !important;
}

</style>
    """,
    unsafe_allow_html=True
)


# ===================================
# LEITURA
# ===================================

df = pd.read_excel(
    "dados.xlsx",
    sheet_name=0
)

df_base = pd.read_excel(
    "dados.xlsx"
)

df.columns = (
    df.columns
    .astype(str)
    .str.strip()
)

df_base.columns = (
    df_base.columns
    .astype(str)
    .str.strip()
)


# ===================================
# CONSOLIDADOR
# ===================================

try:

    df_consolidador = pd.read_excel(
        "consolidador.xlsx"
    )

    df_consolidador.columns = (
        df_consolidador.columns
        .astype(str)
        .str.strip()
    )

    consolidador_carregado = True

except:

    df_consolidador = pd.DataFrame()

    consolidador_carregado = False


# ===================================
# LIMPEZA
# ===================================

for base in [df, df_base]:

    if "Pedido" in base.columns:

        base["Pedido"] = (
            pd.to_numeric(
                base["Pedido"],
                errors="coerce"
            )
            .astype("Int64")
            .astype(str)
        )

    if "PC" in base.columns:

        base["PC"] = (
            base["PC"]
            .astype(str)
            .str.replace(
                ".0",
                "",
                regex=False
            )
        )

    if "Previsão" in base.columns:

        base["Previsão"] = (
            pd.to_datetime(
                base["Previsão"],
                errors="coerce",
                dayfirst=True
            )
        )


# ===================================
# ÚLTIMA ATUALIZAÇÃO
# ===================================

try:

    with open(
        "ultima_atualizacao.json",
        "r"
    ) as arquivo:

        dados_update = json.load(
            arquivo
        )

    data_update = datetime.strptime(
        dados_update[
            "ultima_atualizacao"
        ],
        "%Y-%m-%d %H:%M:%S"
    )

    data_update = (
        data_update
        -
        timedelta(hours=3)
    )

    st.info(
        "🕒 Última atualização: "
        +
        data_update.strftime(
            "%d/%m/%Y %H:%M:%S"
        )
    )

except:

    pass


# ===================================
# FILTROS SALVOS
# ===================================

try:

    with open(
        "filtros.json",
        "r"
    ) as arquivo:

        filtros = json.load(
            arquivo
        )[0]

except:

    filtros = {}


# ===================================
# FILTROS
# ===================================

st.sidebar.title(
    "Filtros"
)


# DATA

if (
    "Previsão" in df.columns
    and
    not df.empty
):

    min_data = (
        df["Previsão"]
        .min()
        .date()
    )

    max_data = (
        df["Previsão"]
        .max()
        .date()
    )

    start_default = (
        pd.to_datetime(
            filtros.get(
                "start_date",
                min_data
            )
        )
        .date()
    )

    end_default = (
        pd.to_datetime(
            filtros.get(
                "end_date",
                max_data
            )
        )
        .date()
    )

    start_date = (
        st.sidebar.date_input(
            "Data inicial",
            value=start_default,
            format="DD/MM/YYYY"
        )
    )

    end_date = (
        st.sidebar.date_input(
            "Data final",
            value=end_default,
            format="DD/MM/YYYY"
        )
    )

    df = df[
        (
            df["Previsão"]
            .dt.date
            >=
            start_date
        )
        &
        (
            df["Previsão"]
            .dt.date
            <=
            end_date
        )
    ]

else:

    start_date = None

    end_date = None


# ROTA

if "Rota" in df.columns:

    rotas = sorted(
        df["Rota"]
        .dropna()
        .astype(str)
        .unique()
    )

    rotas_sel = (
        st.sidebar.multiselect(
            "Rotas",
            rotas,
            default=[
                r
                for r
                in filtros.get(
                    "rotas",
                    []
                )
                if r in rotas
            ]
        )
    )

    if rotas_sel:

        df = df[
            df["Rota"]
            .astype(str)
            .isin(
                rotas_sel
            )
        ]


# PRODUTO

if "Produto" in df.columns:

    produtos = sorted(
        df["Produto"]
        .dropna()
        .astype(str)
        .unique()
    )

    produtos_sel = (
        st.sidebar.multiselect(
            "Produtos",
            produtos,
            default=[
                p
                for p
                in filtros.get(
                    "produtos",
                    []
                )
                if p in produtos
            ]
        )
    )

    if produtos_sel:

        df = df[
            df["Produto"]
            .astype(str)
            .isin(
                produtos_sel
            )
        ]


# PC

if "PC" in df.columns:

    pcs = sorted(
        df["PC"]
        .dropna()
        .astype(str)
        .unique()
    )

    pcs_sel = (
        st.sidebar.multiselect(
            "Programação de carga",
            pcs,
            default=[
                p
                for p
                in filtros.get(
                    "pcs",
                    []
                )
                if p in pcs
            ]
        )
    )

    if pcs_sel:

        df = df[
            df["PC"]
            .astype(str)
            .isin(
                pcs_sel
            )
        ]


# ===================================
# PEDIDOS MANUAIS
# ===================================

st.sidebar.markdown(
    "---"
)

st.sidebar.subheader(
    "📌 Pedidos manuais"
)

lista_pedidos = (
    sorted(
        df_base["Pedido"]
        .dropna()
        .astype(str)
        .unique()
    )
    if "Pedido" in df_base.columns
    else []
)

pedidos_manuais = (
    st.sidebar.multiselect(
        "Selecionar pedidos manuais",
        lista_pedidos,
        default=[
            p
            for p
            in filtros.get(
                "pedidos_manuais",
                []
            )
            if p in lista_pedidos
        ]
    )
)


# ===================================
# ROTAS MANUAIS
# ===================================

st.sidebar.markdown(
    "---"
)

st.sidebar.subheader(
    "🚚 Rotas manuais"
)

lista_rotas = (
    sorted(
        df_base["Rota"]
        .dropna()
        .astype(str)
        .unique()
    )
    if "Rota" in df_base.columns
    else []
)

rotas_manuais = (
    st.sidebar.multiselect(
        "Selecionar rotas manuais",
        lista_rotas,
        default=[
            r
            for r
            in filtros.get(
                "rotas_manuais",
                []
            )
            if r in lista_rotas
        ]
    )
)


# ===================================
# APLICAÇÃO
# ===================================

df_filtrado = df.copy()

df_base_filtrada = (
    df_base.copy()
)

if (
    start_date
    and
    end_date
    and
    "Previsão"
    in df_base_filtrada.columns
):

    df_base_filtrada = (
        df_base_filtrada[
            (
                df_base_filtrada[
                    "Previsão"
                ]
                .dt.date
                >=
                start_date
            )
            &
            (
                df_base_filtrada[
                    "Previsão"
                ]
                .dt.date
                <=
                end_date
            )
        ]
    )

df_final = (
    df_filtrado.copy()
)

if (
    pedidos_manuais
    and
    "Pedido"
    in df_base_filtrada.columns
):

    df_extra = (
        df_base_filtrada[
            df_base_filtrada[
                "Pedido"
            ]
            .astype(str)
            .isin(
                pedidos_manuais
            )
        ]
    )

    df_final = (
        pd.concat(
            [
                df_final,
                df_extra
            ],
            ignore_index=True
        )
    )

if (
    rotas_manuais
    and
    "Rota"
    in df_base_filtrada.columns
):

    df_extra = (
        df_base_filtrada[
            df_base_filtrada[
                "Rota"
            ]
            .astype(str)
            .isin(
                rotas_manuais
            )
        ]
    )

    df_final = (
        pd.concat(
            [
                df_final,
                df_extra
            ],
            ignore_index=True
        )
    )

df_final = (
    df_final
    .drop_duplicates()
)


# ===================================
# MATÉRIA-PRIMA
# ===================================

st.markdown(
    "---"
)

mostrar_mp = st.checkbox(
    "🪵 Mostrar Matéria-Prima",
    value=False
)

if mostrar_mp:

    if not consolidador_carregado:

        st.warning(
            "⚠️ Nenhum Consolidador foi enviado."
        )

    else:

        st.subheader(
            "📦 Estoque de Matéria-Prima"
        )

        estoque = (
            df_consolidador
            .iloc[:, [1, 2, 18]]
            .copy()
        )

        estoque.columns = [
            "Codigo",
            "Descricao",
            "Estoque"
        ]

        estoque["Codigo"] = (
            estoque["Codigo"]
            .apply(
                codigo_material
            )
        )

        estoque["Descricao"] = (
            estoque["Descricao"]
            .apply(
                descricao_material
            )
        )

        estoque["Estoque"] = (
            pd.to_numeric(
                estoque["Estoque"],
                errors="coerce"
            )
            .fillna(0)
        )

        estoque = (
            estoque
            .groupby(
                [
                    "Codigo",
                    "Descricao"
                ],
                as_index=False
            )["Estoque"]
            .sum()
        )

        consumo = (
            df_final[
                [
                    "Produto",
                    "M2 Vendido"
                ]
            ]
            .copy()
        )

        consumo["Codigo"] = (
            consumo["Produto"]
            .apply(
                codigo_material
            )
        )

        consumo["Consumo"] = (
            pd.to_numeric(
                consumo[
                    "M2 Vendido"
                ],
                errors="coerce"
            )
            .fillna(0)
        )

        consumo = (
            consumo
            .groupby(
                "Codigo",
                as_index=False
            )["Consumo"]
            .sum()
        )

        consumo_data = (
            df_final[
                [
                    "Previsão",
                    "Produto",
                    "Pedido",
                    "Cliente",
                    "PC",
                    "Rota",
                    "M2 Vendido"
                ]
            ]
            .copy()
        )

        consumo_data["Codigo"] = (
            consumo_data[
                "Produto"
            ]
            .apply(
                codigo_material
            )
        )

        consumo_data[
            "Consumo Dia"
        ] = (
            pd.to_numeric(
                consumo_data[
                    "M2 Vendido"
                ],
                errors="coerce"
            )
            .fillna(0)
        )

        consumo_data = (
            consumo_data
            .sort_values(
                [
                    "Codigo",
                    "Previsão"
                ]
            )
        )

        resumo = pd.merge(
            consumo,
            estoque,
            on="Codigo",
            how="left"
        )

        resumo["Descricao"] = (
            resumo[
                "Descricao"
            ]
            .fillna(
                resumo[
                    "Codigo"
                ]
            )
        )

        resumo["Estoque"] = (
            resumo[
                "Estoque"
            ]
            .fillna(0)
        )

        resumo["Saldo"] = (
            resumo[
                "Estoque"
            ]
            -
            resumo[
                "Consumo"
            ]
        )

        resumo = (
            resumo[
                resumo[
                    "Consumo"
                ]
                > 0
            ]
            .copy()
        )

        resumo = (
            resumo[
                ~resumo[
                    "Codigo"
                ]
                .astype(str)
                .str.contains(
                    "CODIG|CÓDIG",
                    case=False,
                    na=False
                )
            ]
        )

        resumo = (
            resumo[
                ~resumo[
                    "Descricao"
                ]
                .astype(str)
                .str.contains(
                    "DESCRI",
                    case=False,
                    na=False
                )
            ]
        )

        produz_ate = []

        primeira_falta = []

        for _, linha in (
            resumo.iterrows()
        ):

            saldo = (
                linha[
                    "Estoque"
                ]
            )

            tabela = (
                consumo_data[
                    consumo_data[
                        "Codigo"
                    ]
                    ==
                    linha[
                        "Codigo"
                    ]
                ]
                .sort_values(
                    "Previsão"
                )
            )

            ultima = pd.NaT

            falta = pd.NaT

            for _, item in (
                tabela.iterrows()
            ):

                if (
                    saldo
                    >=
                    item[
                        "Consumo Dia"
                    ]
                ):

                    saldo -= (
                        item[
                            "Consumo Dia"
                        ]
                    )

                    ultima = (
                        item[
                            "Previsão"
                        ]
                    )

                else:

                    falta = (
                        item[
                            "Previsão"
                        ]
                    )

                    break

            produz_ate.append(
                ultima
            )

            primeira_falta.append(
                falta
            )

        resumo[
            "Produz até"
        ] = produz_ate

        resumo[
            "Primeira Falta"
        ] = primeira_falta

        resumo[
            "Compra Necessária"
        ] = (
            resumo[
                "Saldo"
            ]
            .clip(
                upper=0
            )
            .abs()
        )

        resumo[
            "Status"
        ] = (
            resumo[
                "Saldo"
            ]
            .apply(
                lambda x:
                "🟢 OK"
                if x >= 0
                else "🔴 Comprar"
            )
        )

        for coluna in [
            "Estoque",
            "Consumo",
            "Saldo",
            "Compra Necessária"
        ]:

            resumo[
                coluna
            ] = (
                pd.to_numeric(
                    resumo[
                        coluna
                    ],
                    errors="coerce"
                )
                .round(2)
            )

        for coluna in [
            "Produz até",
            "Primeira Falta"
        ]:

            resumo[
                coluna
            ] = (
                pd.to_datetime(
                    resumo[
                        coluna
                    ],
                    errors="coerce"
                )
                .dt.strftime(
                    "%d/%m/%Y"
                )
                .fillna("")
            )

        col1, col2, col3, col4, col5 = (
            st.columns(5)
        )

        col1.metric(
            "📦 Materiais",
            len(resumo)
        )

        col2.metric(
            "🔴 Comprar",
            (
                resumo[
                    "Saldo"
                ]
                < 0
            ).sum()
        )

        col3.metric(
            "📐 Total Comprar (m²)",
            formatar_numero(
                resumo[
                    "Compra Necessária"
                ].sum()
            )
        )

        col4.metric(
            "⚠️ Falta Material",
            (
                resumo[
                    "Primeira Falta"
                ]
                != ""
            ).sum()
        )

        col5.metric(
            "🟢 OK",
            (
                resumo[
                    "Saldo"
                ]
                >= 0
            ).sum()
        )

        resumo = (
            resumo[
                [
                    "Codigo",
                    "Descricao",
                    "Estoque",
                    "Consumo",
                    "Saldo",
                    "Produz até",
                    "Primeira Falta",
                    "Compra Necessária",
                    "Status"
                ]
            ]
        )

        resumo = (
            resumo
            .sort_values(
                [
                    "Compra Necessária",
                    "Primeira Falta"
                ],
                ascending=[
                    False,
                    True
                ]
            )
        )

        # Oculta linhas sem valores

        colunas_numericas = [
            "Estoque",
            "Consumo",
            "Saldo",
            "Compra Necessária"
        ]

        resumo = (
            resumo[
                resumo[
                    colunas_numericas
                ]
                .fillna(0)
                .ne(0)
                .any(axis=1)
            ]
            .copy()
        )

        # Tabela centralizada

        tabela_resumo = (
            resumo.copy()
        )

        for coluna in (
            colunas_numericas
        ):

            tabela_resumo[
                coluna
            ] = (
                tabela_resumo[
                    coluna
                ]
                .apply(
                    formatar_numero
                )
            )

        html_resumo = (
            tabela_resumo
            .to_html(
                index=False,
                border=0,
                classes=(
                    "tabela-centralizada"
                ),
                escape=False
            )
        )

        st.markdown(
            html_resumo,
            unsafe_allow_html=True
        )

        # DETALHAR MATERIAL

        st.markdown(
            "---"
        )

        st.subheader(
            "🔍 Detalhar Material"
        )

        if not resumo.empty:

            materiais = (
                resumo[
                    "Codigo"
                ]
                +
                " - "
                +
                resumo[
                    "Descricao"
                ]
            ).tolist()

            material = (
                st.selectbox(
                    "Selecione o material",
                    sorted(
                        materiais
                    )
                )
            )

            codigo = (
                material
                .split(
                    " - "
                )[0]
            )

            detalhe = (
                consumo_data[
                    consumo_data[
                        "Codigo"
                    ]
                    ==
                    codigo
                ]
                .copy()
                .sort_values(
                    "Previsão"
                )
            )

            detalhe[
                "Consumo Dia"
            ] = (
                detalhe[
                    "Consumo Dia"
                ]
                .round(2)
            )

            detalhe[
                "Previsão"
            ] = (
                detalhe[
                    "Previsão"
                ]
                .dt.strftime(
                    "%d/%m/%Y"
                )
            )

            st.dataframe(
                detalhe[
                    [
                        "Previsão",
                        "Pedido",
                        "Cliente",
                        "PC",
                        "Rota",
                        "Consumo Dia"
                    ]
                ],
                use_container_width=True,
                hide_index=True,
                height=350
            )

        else:

            st.info(
                "Nenhum material foi "
                "encontrado nos filtros."
            )

        excel_mp = (
            io.BytesIO()
        )

        with pd.ExcelWriter(
            excel_mp,
            engine="openpyxl"
        ) as writer:

            resumo.to_excel(
                writer,
                sheet_name=(
                    "Matéria-Prima"
                ),
                index=False
            )

        st.download_button(
            "📥 Baixar Matéria-Prima",
            excel_mp.getvalue(),
            "Materia_Prima.xlsx",
            mime=(
                "application/"
                "vnd.openxmlformats-"
                "officedocument."
                "spreadsheetml.sheet"
            )
        )


# ===================================
# INDICADORES
# ===================================

st.subheader(
    "Indicadores"
)

total_pedidos = (
    df_final[
        "Pedido"
    ]
    .nunique()
    if "Pedido"
    in df_final.columns
    else 0
)

total_pecas = len(
    df_final
)

total_m2 = (
    pd.to_numeric(
        df_final[
            "M2 Vendido"
        ],
        errors="coerce"
    )
    .sum()
    if "M2 Vendido"
    in df_final.columns
    else 0
)

total_peso = (
    pd.to_numeric(
        df_final[
            "Peso"
        ],
        errors="coerce"
    )
    .sum()
    if "Peso"
    in df_final.columns
    else 0
)

total_rotas = (
    df_final[
        "Rota"
    ]
    .nunique()
    if "Rota"
    in df_final.columns
    else 0
)

c1, c2, c3, c4, c5 = (
    st.columns(5)
)

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
    formatar_numero(
        total_m2
    )
)

c4.metric(
    "Peso Total",
    formatar_numero(
        total_peso
    )
)

c5.metric(
    "Rotas",
    total_rotas
)


# ===================================
# GRÁFICO ROTA
# ===================================

if (
    not df_final.empty
    and
    "Rota"
    in df_final.columns
    and
    "M2 Vendido"
    in df_final.columns
):

    st.subheader(
        "📈 Produção por Rota"
    )

    grafico_rota = (
        df_final
        .groupby(
            "Rota"
        )[
            "M2 Vendido"
        ]
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
        texttemplate=(
            "%{text:.2f}"
        ),
        textposition=(
            "outside"
        )
    )

    st.plotly_chart(
        fig_rota,
        use_container_width=True
    )


# ===================================
# GRÁFICO PRODUTO
# ===================================

if (
    not df_final.empty
    and
    "Produto"
    in df_final.columns
    and
    "M2 Vendido"
    in df_final.columns
):

    st.subheader(
        "🪟 Produção por Produto"
    )

    grafico_produto = (
        df_final
        .groupby(
            "Produto"
        )[
            "M2 Vendido"
        ]
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
        texttemplate=(
            "%{text:.2f}"
        ),
        textposition=(
            "outside"
        )
    )

    st.plotly_chart(
        fig_produto,
        use_container_width=True
    )


# ===================================
# BASE COMPLETA
# ===================================

st.markdown(
    "---"
)

mostrar_base = st.checkbox(
    "📋 Mostrar Base Completa",
    value=False
)

if mostrar_base:

    st.subheader(
        "📋 Base Completa"
    )

    st.dataframe(
        df_final,
        use_container_width=True,
        height=500
    )


# ===================================
# DOWNLOAD
# ===================================

st.subheader(
    "📥 Exportar dados filtrados"
)


def to_excel(dados):

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        dados.to_excel(
            writer,
            index=False,
            sheet_name=(
                "Base Filtrada"
            )
        )

    return (
        output.getvalue()
    )


excel_file = (
    to_excel(
        df_final
    )
)

st.download_button(
    "Baixar planilha filtrada (Excel)",
    excel_file,
    "dados_filtrados.xlsx",
    mime=(
        "application/"
        "vnd.openxmlformats-"
        "officedocument."
        "spreadsheetml.sheet"
    )
)
