import io
import re
import json
import math

import streamlit as st
import pandas as pd
import plotly.express as px

from io import BytesIO
from datetime import datetime, timedelta

from equivalencias import EQUIVALENCIAS

from st_aggrid import AgGrid, GridOptionsBuilder

from otimizador import (
    Peca,
    otimizar_lista,
    resumo_otimizacao
)

# ===================================
# FUNÇÕES
# ===================================

def codigo_material(texto):
    """
    Retorna o código padronizado do material
    utilizando a tabela de equivalências.
    """

    if pd.isna(texto):
        return None

    texto = str(texto).upper().strip()

    # Busca a equivalência cadastrada
    return EQUIVALENCIAS.get(texto, texto)


def descricao_material(texto):
    """
    Converte a descrição do consolidador
    em um nome mais amigável.
    """

    if pd.isna(texto):
        return ""

    texto = str(texto).upper().strip()

    # Remove CHAPARIA
    texto = texto.replace("CHAPARIA", "")

    # Remove medidas
    texto = re.sub(
        r"\d{4}\s*[Xx]\s*\d{4}",
        "",
        texto
    )

    # Remove espaços extras
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


def formatar_numero_br(valor):
    """
    Formata números no padrão brasileiro.
    Exemplo:
    1234.50 -> 1.234,50
    """

    if pd.isna(valor):
        return ""

    return (
        f"{float(valor):,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


# ===================================
# CONFIGURAÇÃO DAS CHAPAS
# ===================================

LARGURA_CHAPA = 3.210
ALTURA_CHAPA = 2.400

AREA_CHAPA = LARGURA_CHAPA * ALTURA_CHAPA


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

try:

    df = pd.read_excel(
        "dados.xlsx",
        sheet_name=0
    )

    df_base = pd.read_excel(
        "dados.xlsx",
        sheet_name=0
    )

except Exception as erro:

    st.error(
        f"❌ Erro ao abrir dados.xlsx: {erro}"
    )

    st.stop()


# ===================================
# LIMPEZA DAS COLUNAS
# ===================================

for base in [df, df_base]:

    base.columns = (
        base.columns
        .astype(str)
        .str.strip()
    )

    # Pedido
    if "Pedido" in base.columns:

        base["Pedido"] = (
            pd.to_numeric(
                base["Pedido"],
                errors="coerce"
            )
            .astype("Int64")
            .astype(str)
        )

        base["Pedido"] = (
            base["Pedido"]
            .replace("<NA>", "")
        )

    # PC
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

        base["PC"] = (
            base["PC"]
            .replace("nan", "")
        )

    # Data
    if "Previsão" in base.columns:

        base["Previsão"] = (
            pd.to_datetime(
                base["Previsão"],
                errors="coerce",
                dayfirst=True
            )
        )

    # M²
    if "M2 Vendido" in base.columns:

        base["M2 Vendido"] = (
            pd.to_numeric(
                base["M2 Vendido"],
                errors="coerce"
            )
            .fillna(0)
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

except Exception:

    df_consolidador = pd.DataFrame()

    consolidador_carregado = False


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
        dados_update["ultima_atualizacao"],
        "%Y-%m-%d %H:%M:%S"
    )

    data_update = (
        data_update
        - timedelta(hours=3)
    )

    data_formatada = (
        data_update
        .strftime("%d/%m/%Y %H:%M:%S")
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

st.sidebar.title("Filtros")


# ===================================
# FILTRO DE DATA
# ===================================

start_date = None
end_date = None

if "Previsão" in df.columns:

    # Remove datas inválidas
    datas_validas = pd.to_datetime(
        df["Previsão"],
        errors="coerce"
    ).dropna()

    if not datas_validas.empty:

        min_data = datas_validas.min().date()
        max_data = datas_validas.max().date()

        try:
            start_default = pd.to_datetime(
                filtros.get("start_date", min_data)
            ).date()
        except Exception:
            start_default = min_data

        try:
            end_default = pd.to_datetime(
                filtros.get("end_date", max_data)
            ).date()
        except Exception:
            end_default = max_data

        # Garante que as datas estejam dentro do intervalo permitido
        if start_default < min_data or start_default > max_data:
            start_default = min_data

        if end_default < min_data or end_default > max_data:
            end_default = max_data

        start_date = st.sidebar.date_input(
            "Data inicial",
            value=start_default,
            min_value=min_data,
            max_value=max_data,
            format="DD/MM/YYYY"
        )

        end_date = st.sidebar.date_input(
            "Data final",
            value=end_default,
            min_value=min_data,
            max_value=max_data,
            format="DD/MM/YYYY"
        )

        if start_date > end_date:
            st.sidebar.error(
                "A data inicial não pode ser maior que a data final."
            )
            st.stop()

        df = df[
            (df["Previsão"].dt.date >= start_date)
            &
            (df["Previsão"].dt.date <= end_date)
        ]

    else:

        st.warning("Nenhuma data válida encontrada na coluna Previsão.")
        st.stop()

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

    rotas_sel = st.sidebar.multiselect(
        "Rotas",
        options=rotas,
        default=rotas_default
    )

    if rotas_sel:

        df = df[
            df["Rota"]
            .astype(str)
            .isin(rotas_sel)
        ]


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

    produtos_sel = st.sidebar.multiselect(
        "Produtos",
        options=produtos,
        default=produtos_default
    )

    if produtos_sel:

        df = df[
            df["Produto"]
            .astype(str)
            .isin(produtos_sel)
        ]


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

    pcs_sel = st.sidebar.multiselect(
        "Programação de carga",
        options=pcs,
        default=pcs_default
    )

    if pcs_sel:

        df = df[
            df["PC"]
            .astype(str)
            .isin(pcs_sel)
        ]


# ===================================
# BASE FILTRADA
# ===================================

df_filtrado = df.copy()

df_final = df_filtrado.copy()


# ===================================
# PEDIDOS MANUAIS
# ===================================

st.sidebar.markdown("---")

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
        options=lista_pedidos,
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

st.sidebar.markdown("---")

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
        options=lista_rotas,
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
    and "Previsão" in df_base_filtrada.columns
):

    df_base_filtrada = (
        df_base_filtrada[
            (
                df_base_filtrada[
                    "Previsão"
                ].dt.date
                >= start_date
            )
            &
            (
                df_base_filtrada[
                    "Previsão"
                ].dt.date
                <= end_date
            )
        ]
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

st.markdown("---")

mostrar_mp = st.checkbox(
    "🪵 Mostrar Matéria-Prima",
    value=False
)


if mostrar_mp:

    if not consolidador_carregado:

        st.warning(
            "⚠️ Nenhum arquivo "
            "consolidador.xlsx foi encontrado."
        )

    elif len(
        df_consolidador.columns
    ) < 19:

        st.error(
            "❌ O consolidador não possui "
            "as colunas necessárias."
        )

    elif df_final.empty:

        st.info(
            "Nenhum pedido foi encontrado "
            "nos filtros selecionados."
        )

    else:

        st.subheader(
            "📦 Estoque de Matéria-Prima"
        )

        # =====================================
        # ESTOQUE
        # =====================================

        estoque = (
            df_consolidador
            .iloc[:, [1, 2, 16]]
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
            estoque[
                estoque["Codigo"]
                .notna()
            ]
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

        # =====================================
        # CONSUMO DOS FILTROS
        # =====================================

        if (
            "Produto"
            not in df_final.columns
            or
            "M2 Vendido"
            not in df_final.columns
        ):

            st.error(
                "❌ As colunas Produto "
                "ou M2 Vendido não foram "
                "encontradas."
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
                consumo[
                    consumo["Codigo"]
                    .notna()
                ]
            )

            consumo = (
                consumo
                .groupby(
                    "Codigo",
                    as_index=False
                )["Consumo"]
                .sum()
            )

            # =================================
            # CONSUMO POR DATA
            # =================================

            colunas_detalhe = [

                "Previsão",

                "Produto",

                "Pedido",

                "Cliente",

                "PC",

                "Rota",

                "M2 Vendido"

            ]

            colunas_existentes = [

                coluna

                for coluna
                in colunas_detalhe

                if coluna
                in df_final.columns

            ]

            consumo_data = (
                df_final[
                    colunas_existentes
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

            if (
                "Previsão"
                in consumo_data.columns
            ):

                consumo_data = (
                    consumo_data
                    .sort_values(
                        [
                            "Codigo",
                            "Previsão"
                        ]
                    )
                )
            # =================================
            # PEÇAS PARA OTIMIZAÇÃO
            # =================================

            colunas_pecas = [

                "Produto",

                "Pedido",

                "Cliente",

                "PC",

                "Rota",

                "Largura",

                "Altura"

            ]

            colunas_pecas = [

                c

                for c in colunas_pecas

                if c in df_final.columns

            ]

            pecas = (

                df_final[
                    colunas_pecas
                ]

                .copy()

            )

            pecas["Codigo"] = (

                pecas["Produto"]

                .apply(

                    codigo_material

                )

            )

            pecas["Largura"] = (

                pd.to_numeric(

                    pecas["Largura"],

                    errors="coerce"

                )

            )

            pecas["Altura"] = (

                pd.to_numeric(

                    pecas["Altura"],

                    errors="coerce"

                )

            )

            pecas = (

                pecas

                .dropna(

                    subset=[

                        "Largura",

                        "Altura"

                    ]

                )

            )
                        # =================================
            # PREPARAÇÃO PARA O CORTE
            # =================================

            # Acrescenta 4 mm para lapidação
            pecas["Largura Corte"] = pecas["Largura"] + 4
            pecas["Altura Corte"] = pecas["Altura"] + 4

            # Área da peça em m²
            pecas["Área"] = (
                pecas["Largura Corte"]
                *
                pecas["Altura Corte"]
            ) / 1000000


            # =================================
            # DISTÂNCIA MÍNIMA
            # =================================

            def distancia_minima(codigo):

                codigo = str(codigo).upper()

                if codigo.startswith("LM"):
                    return 30

                numeros = re.findall(
                    r"\d+",
                    codigo
                )

                if numeros:

                    espessura = int(
                        numeros[0]
                    )

                    if espessura in [3, 4]:
                        return 12

                    elif espessura in [6, 8]:
                        return 20

                    elif espessura >= 10:
                        return 30

                return 12


            pecas["Distância"] = (
                pecas["Codigo"]
                .apply(
                    distancia_minima
                )
            )


            # =================================
            # TAMANHO UTILIZADO NO ENCAIXE
            # =================================

            pecas["Largura Encaixe"] = (
                pecas["Largura Corte"]
                +
                pecas["Distância"]
            )

            pecas["Altura Encaixe"] = (
                pecas["Altura Corte"]
                +
                pecas["Distância"]
            )


            # =====================================
            # MONTA LISTA PARA OTIMIZAÇÃO
            # =====================================

            lista_otimizacao = []

            for _, linha in pecas.iterrows():

                largura = float(
                    linha["Largura Encaixe"]
                )

                altura = float(
                    linha["Altura Encaixe"]
                )

                if altura > largura:

                    largura, altura = altura, largura

                lista_otimizacao.append(

                    Peca(

                        codigo=str(
                            linha["Codigo"]
                        ),

                        largura=largura,

                        altura=altura,

                        pedido=str(
                            linha.get(
                                "Pedido",
                                ""
                            )
                        ),

                        cliente=str(
                            linha.get(
                                "Cliente",
                                ""
                            )
                        ),

                        pc=str(
                            linha.get(
                                "PC",
                                ""
                            )
                        ),

                        rota=str(
                            linha.get(
                                "Rota",
                                ""
                            )
                        )

                    )

                )

            # =====================================
            # EXECUTA A OTIMIZAÇÃO
            # =====================================

            resultado_otimizacao = (
                otimizar_lista(
                    lista_otimizacao
                )
            )

            resumo_otimizado = pd.DataFrame(
                resumo_otimizacao(
                    resultado_otimizacao
                )
            )

            colunas = [

                "Codigo",

                "Qtd Chapas",

                "Área Total",

                "Área Utilizada",

                "Desperdício Total",

                "Aproveitamento (%)"

            ]

            for coluna in colunas:

                if coluna not in resumo_otimizado.columns:

                    resumo_otimizado[coluna] = 0

            resumo_otimizado["Qtd Chapas"] = (
                resumo_otimizado["Qtd Chapas"]
                .fillna(0)
                .astype(int)
            )

            resumo_otimizado["Área Total"] = (
                resumo_otimizado["Área Total"]
                .fillna(0)
                .round(2)
            )

            resumo_otimizado["Área Utilizada"] = (
                resumo_otimizado["Área Utilizada"]
                .fillna(0)
                .round(2)
            )

            resumo_otimizado["Desperdício Total"] = (
                resumo_otimizado["Desperdício Total"]
                .fillna(0)
                .round(2)
            )

            resumo_otimizado["Aproveitamento (%)"] = (
                resumo_otimizado["Aproveitamento (%)"]
                .fillna(0)
                .round(2)
            )


            # =================================
            # TESTE DAS PEÇAS
            # =================================

            with st.expander(
                "🧪 Teste das Peças"
            ):

                st.dataframe(
                    pecas,
                    use_container_width=True,
                    hide_index=True,
                    height=300
                )


            # =================================
            # AGRUPA PEÇAS POR MATERIAL
            # =================================
            

            materiais_otimizacao = {}

            for codigo in sorted(
                pecas["Codigo"].unique()
            ):

                tabela = (
                    pecas[
                        pecas["Codigo"] == codigo
                    ]
                    .copy()
                )

                tabela = (
                    tabela
                    .sort_values(
                        [
                            "Largura Encaixe",
                            "Altura Encaixe"
                        ],
                        ascending=False
                    )
                )

                materiais_otimizacao[codigo] = tabela


            # =================================
            # RESUMO DOS MATERIAIS
            # =================================

            resumo_otimizacao = []

            for codigo, tabela in materiais_otimizacao.items():

                resumo_otimizacao.append(
                    {
                        "Material": codigo,
                        "Peças": len(tabela),
                        "Área Total": round(
                            tabela["Área"].sum(),
                            2
                        )
                    }
                )


            resumo_otimizacao = pd.DataFrame(
                resumo_otimizacao
            )


            with st.expander(
                "📋 Resumo da Otimização"
            ):

                st.dataframe(
                    resumo_otimizacao,
                    use_container_width=True,
                    hide_index=True
                )
                      
                       

            # =================================
            # RESUMO
            # =================================

            # O merge começa pelo consumo.
            # Portanto, aparecem somente os
            # materiais usados pelos filtros.

            resumo = pd.merge(

                consumo,

                estoque,

                on="Codigo",

                how="left"

            )

            resumo["Descricao"] = (

                resumo["Descricao"]

                .fillna(

                    resumo["Codigo"]

                )

            )

            resumo["Estoque"] = (

                resumo["Estoque"]

                .fillna(0)

            )

            resumo["Consumo"] = (

                resumo["Consumo"]

                .fillna(0)

            )

            resumo["Saldo"] = (

                resumo["Estoque"]

                -

                resumo["Consumo"]

            )

            # Mostra somente materiais
            # utilizados pelos filtros.

            resumo = (

                resumo[

                    resumo["Consumo"]

                    > 0

                ]

                .copy()

            )

            # Remove possíveis cabeçalhos

            resumo = (

                resumo[

                    ~resumo["Codigo"]

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

                    ~resumo["Descricao"]

                    .astype(str)

                    .str.contains(

                        "DESCRI",

                        case=False,

                        na=False

                    )

                ]

            )
            # =================================
            # COBERTURA
            # =================================

            produz_ate = []

            primeira_falta = []

            for _, linha in resumo.iterrows():

                codigo_atual = linha["Codigo"]

                saldo_atual = linha["Estoque"]

                tabela_material = (
                    consumo_data[
                        consumo_data["Codigo"] == codigo_atual
                    ]
                    .copy()
                )

                if "Previsão" in tabela_material.columns:

                    tabela_material = (
                        tabela_material
                        .sort_values("Previsão")
                    )

                ultima_data_ok = pd.NaT

                primeira_data_sem = pd.NaT

                for _, item in tabela_material.iterrows():

                    consumo_dia = item["Consumo Dia"]

                    if saldo_atual >= consumo_dia:

                        saldo_atual -= consumo_dia

                        if "Previsão" in item.index:

                            ultima_data_ok = item["Previsão"]

                    else:

                        if "Previsão" in item.index:

                            primeira_data_sem = item["Previsão"]

                        break

                produz_ate.append(
                    ultima_data_ok
                )

                primeira_falta.append(
                    primeira_data_sem
                )

            resumo["Produz até"] = produz_ate

            resumo["Primeira Falta"] = primeira_falta

            # =================================
            # COMPRA NECESSÁRIA
            # =================================

            resumo[
                "Compra Necessária"
            ] = (

                resumo["Saldo"]

                .clip(
                    upper=0
                )

                .abs()

            )

            # =================================
            # COMPRA COM PERDA
            # =================================

            def calcular_compra_perda(linha):

                compra = linha[
                    "Compra Necessária"
                ]

                codigo = str(
                    linha["Codigo"]
                ).upper()

                if codigo.startswith("LM"):

                    return compra * 1.20

                return compra * 1.10

            resumo[
                "Compra c/ Perda"
            ] = (

                resumo.apply(

                    calcular_compra_perda,

                    axis=1

                )

            )

            # =================================
            # STATUS
            # =================================

            resumo["Status"] = (

                resumo["Saldo"]

                .apply(

                    lambda valor:

                    "🟢 OK"

                    if valor >= 0

                    else "🔴 Comprar"

                )

            )

            # =================================
            # ARREDONDAMENTO
            # =================================

            for coluna in [

                "Estoque",

                "Consumo",

                "Saldo",

                "Compra Necessária",

                "Compra c/ Perda"

            ]:

                resumo[coluna] = (

                    resumo[coluna]

                    .round(2)

                )
            # =================================
            # FORMATAÇÃO DAS DATAS
            # =================================

            for coluna in [

                "Produz até",

                "Primeira Falta"

            ]:

                resumo[coluna] = (

                    pd.to_datetime(

                        resumo[coluna],

                        errors="coerce"

                    )

                    .dt.strftime(

                        "%d/%m/%Y"

                    )

                    .fillna("")

                )

            # =================================
            # INDICADORES DA MP
            # =================================

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

                    ).sum()

                )

            )

            total_compra = (

                resumo[

                    "Compra Necessária"

                ].sum()

            )

            col3.metric(

                "📐 Total Comprar (m²)",

                formatar_numero_br(

                    total_compra

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

                    ).sum()

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

                    ).sum()

                )

            )
                        # =====================================
            # JUNTA RESULTADO DA OTIMIZAÇÃO
            # =====================================

            st.write("Resumo otimizado:")
            st.write(resumo_otimizado)

            st.write("Colunas resumo_otimizado:")
            st.write(resumo_otimizado.columns.tolist())

            st.write("Colunas resumo antes do merge:")
            st.write(resumo.columns.tolist())

            if not resumo_otimizado.empty:

                resumo = resumo.merge(

                    resumo_otimizado[
                        [
                            "Codigo",
                            "Qtd Chapas",
                            "Área Total",
                            "Área Utilizada",
                            "Desperdício Total",
                            "Aproveitamento (%)"
                        ]
                    ],

                    on="Codigo",

                    how="left"

                )

                st.write("Colunas após o merge:")
                st.write(resumo.columns.tolist())

                resumo["Qtd Chapas"] = (

                    resumo["Qtd Chapas"]

                    .fillna(0)

                    .astype(int)

                )

                resumo["Área Total"] = (

                    resumo["Área Total"]

                    .fillna(0)

                    .round(2)

                )

                resumo["Área Utilizada"] = (

                    resumo["Área Utilizada"]

                    .fillna(0)

                    .round(2)

                )

                resumo["Desperdício Total"] = (

                    resumo["Desperdício Total"]

                    .fillna(0)

                    .round(2)

                )

                resumo["Aproveitamento (%)"] = (

                    resumo["Aproveitamento (%)"]

                    .fillna(0)

                    .round(2)

                )

            else:

                st.warning("Resumo otimizado vazio.")

                resumo["Qtd Chapas"] = 0
                resumo["Área Total"] = 0
                resumo["Área Utilizada"] = 0
                resumo["Desperdício Total"] = 0
                resumo["Aproveitamento (%)"] = 0

            # =================================
            # COLUNAS DA TABELA
            # =================================
           
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

                        "Compra c/ Perda",

                        "Qtd Chapas",

                        "Área Total",

                        "Área Utilizada",

                        "Desperdício Total",

                        "Aproveitamento (%)",

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


            
                       # =================================
            # TABELA
            # =================================

            # Remove linhas totalmente vazias
            resumo = resumo.dropna(how="all")

            # Remove materiais sem estoque, sem consumo e sem saldo
            resumo = resumo[
                (resumo["Estoque"] != 0)
                |
                (resumo["Consumo"] != 0)
                |
                (resumo["Saldo"] != 0)
            ]

            gb = GridOptionsBuilder.from_dataframe(resumo)

            gb.configure_default_column(
                editable=False,
                sortable=True,
                filter=True,
                resizable=True,
                cellStyle={
                    "textAlign": "center"
                },
                headerClass="ag-center-header"
            )

            for coluna in resumo.columns:
                gb.configure_column(
                    coluna,
                    cellStyle={"textAlign": "center"},
                    headerClass="ag-center-header"
                )

            gridOptions = gb.build()

            AgGrid(
                resumo,
                gridOptions=gridOptions,
                fit_columns_on_grid_load=True,
                height=650,
                theme="streamlit",
                allow_unsafe_jscode=True,
            )
            # =================================
            # DETALHAR MATERIAL
            # =================================

            st.markdown("---")

            st.subheader(
                "🔍 Detalhar Material"
            )

            if not resumo.empty:

                materiais = (

                    resumo["Codigo"]

                    +

                    " - "

                    +

                    resumo["Descricao"]

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

                )

                if (
                    "Previsão"
                    in detalhe.columns
                ):

                    detalhe = (

                        detalhe

                        .sort_values(

                            "Previsão"

                        )

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

                detalhe[

                    "Consumo Dia"

                ] = (

                    detalhe[

                        "Consumo Dia"

                    ]

                    .round(2)

                )

                colunas_exibir = [

                    coluna

                    for coluna in [

                        "Previsão",

                        "Pedido",

                        "Cliente",

                        "PC",

                        "Rota",

                        "Consumo Dia"

                    ]

                    if coluna

                    in detalhe.columns

                ]

                st.dataframe(

                    detalhe[

                        colunas_exibir

                    ],

                    use_container_width=True,

                    hide_index=True,

                    height=350

                )

            else:

                st.info(

                    "Nenhum material foi "

                    "encontrado nos filtros "

                    "selecionados."

                )

            # =================================
            # EXPORTAÇÃO DA MP
            # =================================

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

                    "application/"

                    "vnd.openxmlformats-"

                    "officedocument."

                    "spreadsheetml.sheet"

                )

            )


# ===================================
# INDICADORES GERAIS
# ===================================

st.markdown("---")

st.subheader("Indicadores")


total_pedidos = (

    df_final["Pedido"]

    .replace(

        "",

        pd.NA

    )

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

    df_final["Rota"]

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

        + timedelta(days=2)

    ).date()

    df_atrasados = (

        df_final[

            df_final[

                "Previsão"

            ].dt.date

            < limite

        ]

    )

    pecas_atrasadas = len(

        df_atrasados

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
    formatar_numero_br(
        total_m2
    )
)

c4.metric(
    "Peso Total",
    formatar_numero_br(
        total_peso
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
    formatar_numero_br(
        m2_atrasados
    )
)


# ===================================
# TABELA POR ROTA
# ===================================

st.markdown("---")

mostrar_rota = st.checkbox(

    "📊 Mostrar Tabela por Rota",

    value=True

)


if mostrar_rota:

    st.subheader(
        "📊 Tabela por Rota"
    )

    if (

        not df_final.empty

        and

        "Rota"

        in df_final.columns

        and

        "Previsão"

        in df_final.columns

        and

        "M2 Vendido"

        in df_final.columns

    ):

        df_rota = (

            df_final.copy()

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

        ordem_datas = (

            sorted(

                pd.to_datetime(

                    df_rota[

                        "Previsão"

                    ],

                    format=(

                        "%d/%m/%Y"

                    ),

                    errors="coerce"

                )

                .dropna()

                .unique()

            )

        )

        ordem_datas = [

            pd.to_datetime(

                data

            ).strftime(

                "%d/%m/%Y"

            )

            for data

            in ordem_datas

        ]

        tabela_rota = (

            pd.pivot_table(

                df_rota,

                values=(

                    "M2 Vendido"

                ),

                index="Rota",

                columns=(

                    "Previsão"

                ),

                aggfunc="sum",

                fill_value=0,

                margins=True,

                margins_name=(

                    "TOTAL GERAL"

                )

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

        )

        tabela_rota = (

            tabela_rota

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

    else:

        st.info(

            "Não há dados suficientes "

            "para montar a tabela."

        )


# ===================================
# TABELA POR PRODUTO
# ===================================

st.markdown("---")

mostrar_produto = st.checkbox(

    "🪟 Mostrar Tabela por Produto",

    value=True

)


if mostrar_produto:

    st.subheader(
        "🪟 Tabela por Produto"
    )

    if (

        not df_final.empty

        and

        "Produto"

        in df_final.columns

        and

        "Previsão"

        in df_final.columns

        and

        "M2 Vendido"

        in df_final.columns

    ):

        df_produto = (

            df_final.copy()

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

        ordem_datas = (

            sorted(

                pd.to_datetime(

                    df_produto[

                        "Previsão"

                    ],

                    format=(

                        "%d/%m/%Y"

                    ),

                    errors="coerce"

                )

                .dropna()

                .unique()

            )

        )

        ordem_datas = [

            pd.to_datetime(

                data

            ).strftime(

                "%d/%m/%Y"

            )

            for data

            in ordem_datas

        ]

        tabela_produto = (

            pd.pivot_table(

                df_produto,

                values=(

                    "M2 Vendido"

                ),

                index="Produto",

                columns=(

                    "Previsão"

                ),

                aggfunc="sum",

                fill_value=0,

                margins=True,

                margins_name=(

                    "TOTAL GERAL"

                )

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

        )

        tabela_produto = (

            tabela_produto

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

    else:

        st.info(

            "Não há dados suficientes "

            "para montar a tabela."

        )


# ===================================
# TABELA ROTA X PRODUTO
# ===================================

st.markdown("---")

mostrar_rota_produto = (
    st.checkbox(
        "📊 Mostrar Rota X Produto",
        value=False
    )
)


if mostrar_rota_produto:

    st.subheader(
        "📊 Rota X Produto"
    )

    if (

        not df_final.empty

        and

        "Rota"

        in df_final.columns

        and

        "Produto"

        in df_final.columns

        and

        "M2 Vendido"

        in df_final.columns

    ):

        tabela_rota_produto = (

            pd.pivot_table(

                df_final,

                values=(

                    "M2 Vendido"

                ),

                index="Rota",

                columns="Produto",

                aggfunc="sum",

                fill_value=0,

                margins=True,

                margins_name=(

                    "TOTAL GERAL"

                )

            )

        )

        tabela_rota_produto = (

            tabela_rota_produto

            .round(2)

        )

        tabela_rota_produto = (

            tabela_rota_produto

            .loc[

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

            tabela_rota_produto

            .loc[

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

                    formatar_numero_br(

                        valor

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

    else:

        st.info(

            "Não há dados suficientes "

            "para montar a tabela."

        )


# ===================================
# GRÁFICO POR ROTA
# ===================================

st.markdown("---")

st.subheader(
    "📈 Produção por Rota"
)


if (

    not df_final.empty

    and

    "Rota"

    in df_final.columns

    and

    "M2 Vendido"

    in df_final.columns

):

    grafico_rota = (

        df_final

        .groupby(

            "Rota",

            as_index=False

        )[

            "M2 Vendido"

        ]

        .sum()

        .sort_values(

            "M2 Vendido"

        )

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

else:

    st.info(

        "Não há dados para o gráfico."

    )


# ===================================
# GRÁFICO POR PRODUTO
# ===================================

st.markdown("---")

st.subheader(
    "🪟 Produção por Produto"
)


if (

    not df_final.empty

    and

    "Produto"

    in df_final.columns

    and

    "M2 Vendido"

    in df_final.columns

):

    grafico_produto = (

        df_final

        .groupby(

            "Produto",

            as_index=False

        )[

            "M2 Vendido"

        ]

        .sum()

        .sort_values(

            "M2 Vendido"

        )

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

else:

    st.info(

        "Não há dados para o gráfico."

    )


# ===================================
# DETALHAMENTO
# ===================================

st.markdown("---")

mostrar_detalhamento = (
    st.checkbox(
        "🔎 Mostrar Detalhamento",
        value=False
    )
)


if mostrar_detalhamento:

    st.subheader(
        "🔎 Detalhamento"
    )

    df_detalhe = (
        df_final.copy()
    )

    if (

        not df_detalhe.empty

        and

        "Previsão"

        in df_detalhe.columns

        and

        df_detalhe[

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

                    ].dt.date

                    >= detalhe_inicio

                )

                &

                (

                    df_detalhe[

                        "Previsão"

                    ].dt.date

                    <= detalhe_fim

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

            hide_index=True,

            height=500

        )

    else:

        st.info(

            "Nenhum dado disponível "

            "para detalhamento."

        )


# ===================================
# BASE COMPLETA
# ===================================

st.markdown("---")

mostrar_base = (
    st.checkbox(
        "📋 Mostrar Base Completa",
        value=False
    )
)


if mostrar_base:

    st.subheader(
        "📋 Base Completa"
    )

    st.dataframe(

        df_final,

        use_container_width=True,

        hide_index=True,

        height=500

    )


# ===================================
# DOWNLOAD
# ===================================

st.markdown("---")

st.subheader(
    "📥 Exportar dados filtrados"
)


def to_excel(
    dataframe
):

    output = BytesIO()

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

        "📥 Baixar planilha "

        "filtrada (Excel)"

    ),

    data=excel_file,

    file_name=(

        "dados_filtrados.xlsx"

    ),

    mime=(

        "application/"

        "vnd.openxmlformats-"

        "officedocument."

        "spreadsheetml.sheet"

    )

)
