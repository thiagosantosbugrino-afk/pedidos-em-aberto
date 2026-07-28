import io
import re
import json

import streamlit as st
import pandas as pd
import plotly.express as px

from io import BytesIO
from datetime import datetime, timedelta


# ===================================
# FUNÇÃO IDENTIFICADOR DO MATERIAL
# ===================================

def codigo_material(texto):
    """
    Retorna o código padronizado do material.

    Exemplos:

    INC0832102400      -> INC08
    REF1032102400      -> REF10
    ESP0432102400      -> ESP04
    ESI0432102400      -> ESP04
    LAMINC0632102400   -> LAMINC06
    LAMINC0832102400   -> LAMINC08
    """

    if pd.isna(texto):
        return None

    texto = str(texto).upper().strip()

    # Padroniza códigos equivalentes
    texto = texto.replace("ESI", "ESP")

    # Laminados
    resultado = re.match(
        r"(LAMINC\d{2})",
        texto
    )

    if resultado:
        return resultado.group(1)

    # Materiais comuns
    resultado = re.match(
        r"([A-Z]{3}\d{2})",
        texto
    )

    if resultado:
        return resultado.group(1)

    return texto


# ===================================
# FUNÇÃO DESCRIÇÃO DO MATERIAL
# ===================================

def descricao_material(texto):
    """
    Converte a descrição do consolidador
    em um nome mais amigável.
    """

    if pd.isna(texto):
        return ""

    texto = str(texto).upper().strip()

    # Remove a palavra CHAPARIA
    texto = texto.replace(
        "CHAPARIA",
        ""
    )

    # Remove medidas da chapa
    texto = re.sub(
        r"\d{4}\s*[Xx]\s*\d{4}",
        "",
        texto
    )

    # Remove espaços duplicados
    texto = re.sub(
        r"\s+",
        " ",
        texto
    ).strip()

    # Padroniza espessura
    texto = re.sub(
        r"\b0(\d)\s*MM\b",
        r"\1 mm",
        texto
    )

    return texto.upper()


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
    """,
    unsafe_allow_html=True
)


# ===================================
# LEITURA DA PLANILHA
# ===================================

df = pd.read_excel(
    "dados.xlsx",
    sheet_name=0
)

df_base = pd.read_excel(
    "dados.xlsx",
    sheet_name=0
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
# CARREGA CONSOLIDADOR
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

except Exception:

    df_consolidador = pd.DataFrame()

    consolidador_carregado = False


# ===================================
# PADRONIZA PEDIDOS
# ===================================

for base in [df, df_base]:

    if "Pedido" in base.columns:

        pedido_numerico = pd.to_numeric(
            base["Pedido"],
            errors="coerce"
        )

        base["Pedido"] = (
            pedido_numerico
            .astype("Int64")
            .astype(str)
        )


# ===================================
# PADRONIZA PC
# ===================================

for base in [df, df_base]:

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


# ===================================
# PADRONIZA DATA
# ===================================

for base in [df, df_base]:

    if "Previsão" in base.columns:

        base["Previsão"] = pd.to_datetime(
            base["Previsão"],
            errors="coerce",
            dayfirst=True
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
        - timedelta(hours=3)
    )

    data_formatada = (
        data_update
        .strftime(
            "%d/%m/%Y %H:%M:%S"
        )
    )

    st.info(
        f"🕒 Última atualização: "
        f"{data_formatada}"
    )

except Exception:

    pass


# ===================================
# FILTROS SALVOS
# ===================================

try:

    with open(
        "filtros.json",
        "r"
    ) as arquivo:

        dados_filtros = json.load(
            arquivo
        )

    if isinstance(
        dados_filtros,
        list
    ):

        filtros = (
            dados_filtros[0]
            if dados_filtros
            else {}
        )

    else:

        filtros = dados_filtros

except Exception:

    filtros = {}


# ===================================
# SIDEBAR
# ===================================

st.sidebar.title(
    "Filtros"
)


# ===================================
# FILTRO DE DATA
# ===================================

start_date = None
end_date = None

if (
    "Previsão" in df.columns
    and not df.empty
):

    datas_validas = (
        df["Previsão"]
        .dropna()
    )

    if not datas_validas.empty:

        min_data = (
            datas_validas
            .min()
            .date()
        )

        max_data = (
            datas_validas
            .max()
            .date()
        )

        try:

            start_default = (
                pd.to_datetime(
                    filtros.get(
                        "start_date",
                        min_data
                    )
                )
                .date()
            )

        except Exception:

            start_default = min_data

        try:

            end_default = (
                pd.to_datetime(
                    filtros.get(
                        "end_date",
                        max_data
                    )
                )
                .date()
            )

        except Exception:

            end_default = max_data

        start_date = (
            st.sidebar
            .date_input(
                "Data inicial",
                value=start_default,
                format="DD/MM/YYYY"
            )
        )

        end_date = (
            st.sidebar
            .date_input(
                "Data final",
                value=end_default,
                format="DD/MM/YYYY"
            )
        )

        df = df[
            (
                df["Previsão"]
                .dt.date
                >= start_date
            )
            &
            (
                df["Previsão"]
                .dt.date
                <= end_date
            )
        ]


# ===================================
# FILTRO DE ROTA
# ===================================

if "Rota" in df.columns:

    rotas = sorted(
        df["Rota"]
        .dropna()
        .astype(str)
        .unique()
    )

    rotas_default = [

        rota

        for rota in filtros.get(
            "rotas",
            []
        )

        if rota in rotas

    ]

    rotas_sel = (
        st.sidebar
        .multiselect(
            "Rotas",
            rotas,
            default=rotas_default
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

else:

    rotas_sel = []


# ===================================
# FILTRO DE PRODUTO
# ===================================

if "Produto" in df.columns:

    produtos = sorted(
        df["Produto"]
        .dropna()
        .astype(str)
        .unique()
    )

    produtos_default = [

        produto

        for produto in filtros.get(
            "produtos",
            []
        )

        if produto in produtos

    ]

    produtos_sel = (
        st.sidebar
        .multiselect(
            "Produtos",
            produtos,
            default=produtos_default
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

else:

    produtos_sel = []


# ===================================
# FILTRO DE PC
# ===================================

if "PC" in df.columns:

    pcs = sorted(
        df["PC"]
        .dropna()
        .astype(str)
        .unique()
    )

    pcs_default = [

        pc

        for pc in filtros.get(
            "pcs",
            []
        )

        if pc in pcs

    ]

    pcs_sel = (
        st.sidebar
        .multiselect(
            "Programação de carga",
            pcs,
            default=pcs_default
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

else:

    pcs_sel = []


# ===================================
# BASE FILTRADA
# ===================================

df_filtrado = (
    df.copy()
)

df_final = (
    df_filtrado.copy()
)


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

        df_base[
            "Pedido"
        ]

        .dropna()

        .astype(str)

        .unique()

    )

    if "Pedido" in df_base.columns

    else []

)

pedidos_manuais = (
    st.sidebar
    .multiselect(
        "Selecionar pedidos manuais",
        lista_pedidos,
        default=[

            pedido

            for pedido in filtros.get(
                "pedidos_manuais",
                []
            )

            if pedido in lista_pedidos

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

        df_base[
            "Rota"
        ]

        .dropna()

        .astype(str)

        .unique()

    )

    if "Rota" in df_base.columns

    else []

)

rotas_manuais = (
    st.sidebar
    .multiselect(
        "Selecionar rotas manuais",
        lista_rotas,
        default=[

            rota

            for rota in filtros.get(
                "rotas_manuais",
                []
            )

            if rota in lista_rotas

        ]
    )
)


# ===================================
# APLICAÇÃO DOS FILTROS MANUAIS
# ===================================

df_base_filtrada = (
    df_base.copy()
)

if (
    start_date is not None
    and end_date is not None
    and "Previsão"
    in df_base_filtrada.columns
):

    df_base_filtrada = (
        df_base_filtrada[
            (
                df_base_filtrada[
                    "Previsão"
                ]
                .dt.date
                >= start_date
            )
            &
            (
                df_base_filtrada[
                    "Previsão"
                ]
                .dt.date
                <= end_date
            )
        ]
    )


df_final = (
    df_filtrado.copy()
)


if (
    pedidos_manuais
    and "Pedido"
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

    df_final = pd.concat(
        [
            df_final,
            df_extra
        ],
        ignore_index=True
    )


if (
    rotas_manuais
    and "Rota"
    in df_base_filtrada.columns
):

    df_extra_rotas = (
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

    df_final = pd.concat(
        [
            df_final,
            df_extra_rotas
        ],
        ignore_index=True
    )


df_final = (
    df_final
    .drop_duplicates()
)


# =====================================
# VISÃO MATÉRIA-PRIMA
# =====================================

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
            "⚠️ Nenhum Consolidador "
            "foi enviado."
        )

    else:

        st.subheader(
            "📦 Estoque de Matéria-Prima"
        )

        # =====================================
        # ESTOQUE
        # =====================================

        if (
            df_consolidador.shape[1]
            <= 18
        ):

            st.error(
                "O arquivo Consolidador "
                "não possui as colunas "
                "necessárias."
            )

        else:

            estoque = (
                df_consolidador
                .iloc[
                    :,
                    [1, 2, 18]
                ]
                .copy()
            )

            estoque.columns = [

                "Codigo",

                "Descricao",

                "Estoque"

            ]

            estoque["Codigo"] = (

                estoque[
                    "Codigo"
                ]

                .apply(
                    codigo_material
                )

            )

            estoque["Descricao"] = (

                estoque[
                    "Descricao"
                ]

                .apply(
                    descricao_material
                )

            )

            estoque["Estoque"] = (

                pd.to_numeric(

                    estoque[
                        "Estoque"
                    ],

                    errors="coerce"

                )

                .fillna(0)

            )

            estoque = (

                estoque

                .dropna(
                    subset=[
                        "Codigo"
                    ]
                )

                .groupby(

                    [
                        "Codigo",
                        "Descricao"
                    ],

                    as_index=False

                )[
                    "Estoque"
                ]

                .sum()

            )


            # =====================================
            # CONSUMO
            # =====================================

            colunas_consumo = [

                coluna

                for coluna in [

                    "Produto",

                    "M2 Vendido"

                ]

                if coluna
                in df_final.columns

            ]


            if len(
                colunas_consumo
            ) < 2:

                st.warning(
                    "As colunas "
                    "'Produto' e "
                    "'M2 Vendido' "
                    "não foram encontradas."
                )

            else:

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

                    consumo[
                        "Produto"
                    ]

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

                    .dropna(
                        subset=[
                            "Codigo"
                        ]
                    )

                    .groupby(

                        "Codigo",

                        as_index=False

                    )[
                        "Consumo"
                    ]

                    .sum()

                )


                # =====================================
                # CONSUMO POR DATA
                # =====================================

                colunas_detalhe = [

                    "Previsão",

                    "Produto",

                    "Pedido",

                    "Cliente",

                    "PC",

                    "Rota",

                    "M2 Vendido"

                ]


                for coluna in colunas_detalhe:

                    if (
                        coluna
                        not in df_final.columns
                    ):

                        df_final[
                            coluna
                        ] = ""


                consumo_data = (

                    df_final[

                        colunas_detalhe

                    ]

                    .copy()

                )

                consumo_data[
                    "Codigo"
                ] = (

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

                    .dropna(
                        subset=[
                            "Codigo"
                        ]
                    )

                    .sort_values(

                        [
                            "Codigo",
                            "Previsão"
                        ]

                    )

                )


                # =====================================
                # RESUMO
                # =====================================

                resumo = pd.merge(

                    consumo,

                    estoque,

                    on="Codigo",

                    how="left"

                )


                resumo[
                    "Descricao"
                ] = (

                    resumo[
                        "Descricao"
                    ]

                    .fillna(

                        resumo[
                            "Codigo"
                        ]

                    )

                )


                resumo[
                    "Estoque"
                ] = (

                    resumo[
                        "Estoque"
                    ]

                    .fillna(0)

                )


                resumo[
                    "Consumo"
                ] = (

                    resumo[
                        "Consumo"
                    ]

                    .fillna(0)

                )


                resumo[
                    "Saldo"
                ] = (

                    resumo[
                        "Estoque"
                    ]

                    -

                    resumo[
                        "Consumo"
                    ]

                )


                # Mantém somente os materiais
                # presentes nos filtros.

                resumo = (

                    resumo[

                        resumo[
                            "Consumo"
                        ]
                        > 0

                    ]

                    .copy()

                )


                # Remove possíveis cabeçalhos
                # importados da planilha.

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


                # =====================================
                # COBERTURA DO ESTOQUE
                # =====================================

                produz_ate = []

                primeira_falta = []


                for _, linha in (
                    resumo.iterrows()
                ):

                    codigo_atual = (
                        linha[
                            "Codigo"
                        ]
                    )

                    saldo_atual = (
                        linha[
                            "Estoque"
                        ]
                    )

                    tabela_material = (

                        consumo_data[

                            consumo_data[
                                "Codigo"
                            ]

                            ==

                            codigo_atual

                        ]

                        .sort_values(

                            "Previsão"

                        )

                        .copy()

                    )


                    ultima_data_ok = (
                        pd.NaT
                    )

                    primeira_data_sem = (
                        pd.NaT
                    )


                    for _, item in (
                        tabela_material
                        .iterrows()
                    ):

                        consumo_dia = (

                            item[
                                "Consumo Dia"
                            ]

                        )


                        if (
                            saldo_atual
                            >=
                            consumo_dia
                        ):

                            saldo_atual = (

                                saldo_atual

                                -

                                consumo_dia

                            )

                            ultima_data_ok = (

                                item[
                                    "Previsão"
                                ]

                            )

                        else:

                            primeira_data_sem = (

                                item[
                                    "Previsão"
                                ]

                            )

                            break


                    produz_ate.append(

                        ultima_data_ok

                    )

                    primeira_falta.append(

                        primeira_data_sem

                    )


                resumo[
                    "Produz até"
                ] = produz_ate

                resumo[
                    "Primeira Falta"
                ] = primeira_falta


                # =====================================
                # COMPRA NECESSÁRIA
                # =====================================

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


                # =====================================
                # STATUS
                # =====================================

                resumo[
                    "Status"
                ] = (

                    resumo[
                        "Saldo"
                    ]

                    .apply(

                        lambda valor:

                        "🟢 OK"

                        if valor >= 0

                        else

                        "🔴 Comprar"

                    )

                )


                # =====================================
                # ARREDONDAMENTO
                # =====================================

                for coluna in [

                    "Estoque",

                    "Consumo",

                    "Saldo",

                    "Compra Necessária"

                ]:

                    resumo[
                        coluna
                    ] = (

                        resumo[
                            coluna
                        ]

                        .round(2)

                    )


                # =====================================
                # FORMATAÇÃO DAS DATAS
                # =====================================

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


                # =====================================
                # INDICADORES MATÉRIA-PRIMA
                # =====================================

                col1, col2, col3, col4, col5 = (
                    st.columns(5)
                )


                col1.metric(

                    "📦 Materiais",

                    len(resumo)

                )


                col2.metric(

                    "🔴 Comprar",

                    int(

                        (
                            resumo[
                                "Saldo"
                            ]
                            < 0
                        )
                        .sum()

                    )

                )


                total_compra = (

                    resumo[
                        "Compra Necessária"
                    ]

                    .sum()

                )


                col3.metric(

                    "📐 Total Comprar (m²)",

                    (
                        f"{total_compra:,.2f}"
                        .replace(
                            ",",
                            "X"
                        )
                        .replace(
                            ".",
                            ","
                        )
                        .replace(
                            "X",
                            "."
                        )
                    )

                )


                col4.metric(

                    "⚠️ Falta Material",

                    int(

                        (

                            resumo[
                                "Primeira Falta"
                            ]

                            != ""

                        )

                        .sum()

                    )

                )


                col5.metric(

                    "🟢 OK",

                    int(

                        (

                            resumo[
                                "Saldo"
                            ]

                            >= 0

                        )

                        .sum()

                    )

                )


                # =====================================
                # COLUNAS
                # =====================================

                resumo = resumo[

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

                    .reset_index(

                        drop=True

                    )

                )


                # =====================================
                # TABELA CENTRALIZADA
                # =====================================

                estilo_tabela = (

                    resumo.style

                    # Centraliza o conteúdo
                    # de todas as colunas.

                    .set_properties(

                        **{

                            "text-align":

                            "center"

                        }

                    )

                    # Mantém somente o conteúdo
                    # da descrição à esquerda.

                    .set_properties(

                        subset=[

                            "Descricao"

                        ],

                        **{

                            "text-align":

                            "left"

                        }

                    )

                    # Centraliza todos os títulos.

                    .set_table_styles(

                        [

                            {

                                "selector":

                                "th",

                                "props":

                                [

                                    (

                                        "text-align",

                                        "center !important"

                                    )

                                ]

                            }

                        ]

                    )

                )


                altura_tabela = min(

                    45

                    +

                    (

                        len(resumo)

                        *

                        36

                    ),

                    650

                )


                st.dataframe(

                    estilo_tabela,

                    use_container_width=True,

                    hide_index=True,

                    height=altura_tabela

                )


                # =====================================
                # DETALHAR MATERIAL
                # =====================================

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


                    codigo_selecionado = (

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

                            codigo_selecionado

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

                        pd.to_datetime(

                            detalhe[
                                "Previsão"
                            ],

                            errors="coerce"

                        )

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

                        height=min(

                            45

                            +

                            (

                                len(
                                    detalhe
                                )

                                *

                                36

                            ),

                            350

                        )

                    )


                else:

                    st.info(

                        "Nenhum material foi "

                        "encontrado nos filtros "

                        "selecionados."

                    )


                # =====================================
                # EXPORTAÇÃO MATÉRIA-PRIMA
                # =====================================

                excel_mp = (
                    io.BytesIO()
                )


                with pd.ExcelWriter(

                    excel_mp,

                    engine="openpyxl"

                ) as writer:

                    resumo.to_excel(

                        writer,

                        sheet_name="Matéria-Prima",

                        index=False

                    )


                st.download_button(

                    label=(

                        "📥 Baixar "

                        "Matéria-Prima"

                    ),

                    data=(

                        excel_mp.getvalue()

                    ),

                    file_name=(

                        "Materia_Prima.xlsx"

                    ),

                    mime=(

                        "application/vnd."

                        "openxmlformats-"

                        "officedocument."

                        "spreadsheetml.sheet"

                    )

                )


# ===================================
# INDICADORES GERAIS
# ===================================

st.markdown(
    "---"
)

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


total_pecas = (
    len(df_final)
)


total_m2 = (

    pd.to_numeric(

        df_final[
            "M2 Vendido"
        ],

        errors="coerce"

    )

    .fillna(0)

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

    .fillna(0)

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


# ===================================
# ATRASADOS
# ===================================

pecas_atrasadas = 0

m2_atrasados = 0


if (
    "Previsão"
    in df_final.columns
):

    limite = (

        datetime.now()

        +

        timedelta(
            days=2
        )

    ).date()


    df_atrasados = (

        df_final[

            df_final[
                "Previsão"
            ]

            .dt.date

            <

            limite

        ]

    )


    pecas_atrasadas = (
        len(df_atrasados)
    )


    if (
        "M2 Vendido"
        in df_atrasados.columns
    ):

        m2_atrasados = (

            pd.to_numeric(

                df_atrasados[
                    "M2 Vendido"
                ],

                errors="coerce"

            )

            .fillna(0)

            .sum()

        )


c1, c2, c3, c4, c5, c6, c7 = (
    st.columns(7)
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
    round(
        total_m2,
        2
    )
)

c4.metric(
    "Peso Total",
    round(
        total_peso,
        2
    )
)

c5.metric(
    "Rotas",
    total_rotas
)

c6.metric(
    "⚠️ Peças Atrasadas",
    pecas_atrasadas
)

c7.metric(
    "⚠️ M² Atrasado",
    round(
        m2_atrasados,
        2
    )
)


# ===================================
# TABELA POR ROTA
# ===================================

st.markdown(
    "---"
)

mostrar_rota = st.checkbox(

    "📊 Mostrar Tabela por Rota",

    value=True

)


if (
    mostrar_rota
    and not df_final.empty
    and "Rota"
    in df_final.columns
    and "Previsão"
    in df_final.columns
    and "M2 Vendido"
    in df_final.columns
):

    st.subheader(
        "📊 Tabela por Rota"
    )


    df_rota = (
        df_final.copy()
    )


    df_rota[
        "M2 Vendido"
    ] = (

        pd.to_numeric(

            df_rota[
                "M2 Vendido"
            ],

            errors="coerce"

        )

        .fillna(0)

    )


    df_rota[
        "Previsão"
    ] = (

        pd.to_datetime(

            df_rota[
                "Previsão"
            ],

            errors="coerce"

        )

    )


    ordem_datas = (

        df_rota[
            "Previsão"
        ]

        .dropna()

        .sort_values()

        .dt.strftime(

            "%d/%m/%Y"

        )

        .unique()

        .tolist()

    )


    df_rota[
        "Previsão"
    ] = (

        df_rota[
            "Previsão"
        ]

        .dt.strftime(

            "%d/%m/%Y"

        )

    )


    tabela_rota = (

        pd.pivot_table(

            df_rota,

            values="M2 Vendido",

            index="Rota",

            columns="Previsão",

            aggfunc="sum",

            fill_value=0,

            margins=True,

            margins_name="TOTAL GERAL"

        )

    )


    colunas = [

        coluna

        for coluna
        in ordem_datas

        if coluna
        in tabela_rota.columns

    ]


    if (
        "TOTAL GERAL"
        in tabela_rota.columns
    ):

        colunas.append(
            "TOTAL GERAL"
        )


    tabela_rota = (

        tabela_rota[
            colunas
        ]

        .round(2)

    )


    tabela_rota = (

        tabela_rota.loc[

            (
                tabela_rota
                != 0
            )

            .any(
                axis=1
            )

        ]

    )


    tabela_rota = (

        tabela_rota.loc[

            :,

            (
                tabela_rota
                != 0
            )

            .any(
                axis=0
            )

        ]

    )


    tabela_rota = (

        tabela_rota

        .replace(
            0,
            ""
        )

    )


    html_rota = (

        tabela_rota

        .to_html(

            classes=(
                "tabela-centralizada"
            ),

            border=0

        )

    )


    st.markdown(

        html_rota,

        unsafe_allow_html=True

    )


# ===================================
# TABELA POR PRODUTO
# ===================================

st.markdown(
    "---"
)

mostrar_produto = st.checkbox(

    "🪟 Mostrar Tabela por Produto",

    value=True

)


if (
    mostrar_produto
    and not df_final.empty
    and "Produto"
    in df_final.columns
    and "Previsão"
    in df_final.columns
    and "M2 Vendido"
    in df_final.columns
):

    st.subheader(
        "🪟 Tabela por Produto"
    )


    df_produto = (
        df_final.copy()
    )


    df_produto[
        "M2 Vendido"
    ] = (

        pd.to_numeric(

            df_produto[
                "M2 Vendido"
            ],

            errors="coerce"

        )

        .fillna(0)

    )


    df_produto[
        "Previsão"
    ] = (

        pd.to_datetime(

            df_produto[
                "Previsão"
            ],

            errors="coerce"

        )

    )


    ordem_datas = (

        df_produto[
            "Previsão"
        ]

        .dropna()

        .sort_values()

        .dt.strftime(

            "%d/%m/%Y"

        )

        .unique()

        .tolist()

    )


    df_produto[
        "Previsão"
    ] = (

        df_produto[
            "Previsão"
        ]

        .dt.strftime(

            "%d/%m/%Y"

        )

    )


    tabela_produto = (

        pd.pivot_table(

            df_produto,

            values="M2 Vendido",

            index="Produto",

            columns="Previsão",

            aggfunc="sum",

            fill_value=0,

            margins=True,

            margins_name="TOTAL GERAL"

        )

    )


    colunas = [

        coluna

        for coluna
        in ordem_datas

        if coluna
        in tabela_produto.columns

    ]


    if (
        "TOTAL GERAL"
        in tabela_produto.columns
    ):

        colunas.append(
            "TOTAL GERAL"
        )


    tabela_produto = (

        tabela_produto[
            colunas
        ]

        .round(2)

    )


    tabela_produto = (

        tabela_produto.loc[

            (
                tabela_produto
                != 0
            )

            .any(
                axis=1
            )

        ]

    )


    tabela_produto = (

        tabela_produto.loc[

            :,

            (
                tabela_produto
                != 0
            )

            .any(
                axis=0
            )

        ]

    )


    tabela_produto = (

        tabela_produto

        .replace(
            0,
            ""
        )

    )


    html_produto = (

        tabela_produto

        .to_html(

            classes=(
                "tabela-centralizada"
            ),

            border=0

        )

    )


    st.markdown(

        html_produto,

        unsafe_allow_html=True

    )


# ===================================
# TABELA ROTA X PRODUTO
# ===================================

st.markdown(
    "---"
)

mostrar_rota_produto = st.checkbox(

    "📊 Mostrar Rota X Produto",

    value=False

)


if (
    mostrar_rota_produto
    and not df_final.empty
    and "Rota"
    in df_final.columns
    and "Produto"
    in df_final.columns
    and "M2 Vendido"
    in df_final.columns
):

    st.subheader(
        "📊 Rota X Produto"
    )


    df_rota_produto = (
        df_final.copy()
    )


    df_rota_produto[
        "M2 Vendido"
    ] = (

        pd.to_numeric(

            df_rota_produto[
                "M2 Vendido"
            ],

            errors="coerce"

        )

        .fillna(0)

    )


    tabela_rota_produto = (

        pd.pivot_table(

            df_rota_produto,

            values="M2 Vendido",

            index="Rota",

            columns="Produto",

            aggfunc="sum",

            fill_value=0,

            margins=True,

            margins_name="TOTAL GERAL"

        )

    )


    tabela_rota_produto = (

        tabela_rota_produto

        .round(2)

    )


    tabela_rota_produto = (

        tabela_rota_produto.loc[

            (
                tabela_rota_produto
                != 0
            )

            .any(
                axis=1
            )

        ]

    )


    tabela_rota_produto = (

        tabela_rota_produto.loc[

            :,

            (
                tabela_rota_produto
                != 0
            )

            .any(
                axis=0
            )

        ]

    )


    tabela_rota_produto = (

        tabela_rota_produto

        .replace(
            0,
            ""
        )

        .astype(object)

    )


    for coluna in (
        tabela_rota_produto.columns
    ):

        tabela_rota_produto[
            coluna
        ] = (

            tabela_rota_produto[
                coluna
            ]

            .apply(

                lambda valor:

                (
                    f"{valor:,.2f}"

                    .replace(
                        ",",
                        "X"
                    )

                    .replace(
                        ".",
                        ","
                    )

                    .replace(
                        "X",
                        "."
                    )
                )

                if isinstance(

                    valor,

                    (
                        int,
                        float
                    )

                )

                else valor

            )

        )


    html_rota_produto = (

        tabela_rota_produto

        .to_html(

            classes=(
                "tabela-centralizada"
            ),

            border=0

        )

    )


    st.markdown(

        html_rota_produto,

        unsafe_allow_html=True

    )


# ===================================
# GRÁFICO POR ROTA
# ===================================

if (
    not df_final.empty
    and "Rota"
    in df_final.columns
    and "M2 Vendido"
    in df_final.columns
):

    st.markdown(
        "---"
    )

    st.subheader(
        "📈 Produção por Rota"
    )


    df_grafico_rota = (
        df_final.copy()
    )


    df_grafico_rota[
        "M2 Vendido"
    ] = (

        pd.to_numeric(

            df_grafico_rota[
                "M2 Vendido"
            ],

            errors="coerce"

        )

        .fillna(0)

    )


    grafico_rota = (

        df_grafico_rota

        .groupby(

            "Rota",

            as_index=False

        )[
            "M2 Vendido"
        ]

        .sum()

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
# GRÁFICO POR PRODUTO
# ===================================

if (
    not df_final.empty
    and "Produto"
    in df_final.columns
    and "M2 Vendido"
    in df_final.columns
):

    st.markdown(
        "---"
    )

    st.subheader(
        "🪟 Produção por Produto"
    )


    df_grafico_produto = (
        df_final.copy()
    )


    df_grafico_produto[
        "M2 Vendido"
    ] = (

        pd.to_numeric(

            df_grafico_produto[
                "M2 Vendido"
            ],

            errors="coerce"

        )

        .fillna(0)

    )


    grafico_produto = (

        df_grafico_produto

        .groupby(

            "Produto",

            as_index=False

        )[
            "M2 Vendido"
        ]

        .sum()

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
# DETALHAMENTO
# ===================================

st.markdown(
    "---"
)

mostrar_detalhamento = st.checkbox(

    "🔎 Mostrar Detalhamento",

    value=False

)


if mostrar_detalhamento:

    st.subheader(
        "🔎 Detalhamento"
    )


    df_detalhe = (
        df_final.copy()
    )


    if (
        "Previsão"
        in df_detalhe.columns
        and not df_detalhe.empty
        and df_detalhe[
            "Previsão"
        ]
        .notna()
        .any()
    ):

        min_det = (

            df_detalhe[
                "Previsão"
            ]

            .min()

            .date()

        )


        max_det = (

            df_detalhe[
                "Previsão"
            ]

            .max()

            .date()

        )


        coluna_1, coluna_2 = (
            st.columns(2)
        )


        with coluna_1:

            detalhe_inicio = (

                st.date_input(

                    "Detalhamento - "
                    "Data Inicial",

                    value=min_det,

                    key="det_inicio",

                    format="DD/MM/YYYY"

                )

            )


        with coluna_2:

            detalhe_fim = (

                st.date_input(

                    "Detalhamento - "
                    "Data Final",

                    value=max_det,

                    key="det_fim",

                    format="DD/MM/YYYY"

                )

            )


        df_detalhe = (

            df_detalhe[

                (
                    df_detalhe[
                        "Previsão"
                    ]

                    .dt.date

                    >=

                    detalhe_inicio

                )

                &

                (
                    df_detalhe[
                        "Previsão"
                    ]

                    .dt.date

                    <=

                    detalhe_fim

                )

            ]

            .copy()

        )


        df_detalhe[
            "Previsão"
        ] = (

            df_detalhe[
                "Previsão"
            ]

            .dt.strftime(

                "%d/%m/%Y"

            )

        )


        st.dataframe(

            df_detalhe,

            use_container_width=True,

            height=500,

            hide_index=True

        )


    else:

        st.warning(

            "Nenhuma coluna "

            "'Previsão' disponível "

            "para detalhamento."

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

        height=500,

        hide_index=True

    )


# ===================================
# DOWNLOAD
# ===================================

st.markdown(
    "---"
)

st.subheader(
    "📥 Exportar dados filtrados"
)


def to_excel(
    dataframe
):

    output = (
        BytesIO()
    )


    with pd.ExcelWriter(

        output,

        engine="openpyxl"

    ) as writer:

        dataframe.to_excel(

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

    label=(

        "Baixar planilha "

        "filtrada (Excel)"

    ),

    data=excel_file,

    file_name=(

        "dados_filtrados.xlsx"

    ),

    mime=(

        "application/vnd."

        "openxmlformats-"

        "officedocument."

        "spreadsheetml.sheet"

    )

)
