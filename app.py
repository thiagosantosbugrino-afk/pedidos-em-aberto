import io
import re
import json
import math
import os

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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

    # Remove espaços duplicados
    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    # Padroniza MM
    # 4MM  -> 4 MM
    # 04MM -> 04 MM
    # 4 MM -> 4 MM
    texto = re.sub(
        r"(\d+)\s*MM\b",
        r"\1 MM",
        texto
    )

    # Busca a equivalência
    return EQUIVALENCIAS.get(
        texto,
        texto
    )

def descricao_material(texto):
    """
    Converte a descrição do consolidador
    em um nome mais amigável e padronizado.
    """

    if pd.isna(texto):
        return ""

    texto = str(texto).upper().strip()

    # Remove CHAPARIA
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

    # Remove espaços extras
    texto = re.sub(
        r"\s+",
        " ",
        texto
    ).strip()

    # Padroniza MM
    # 4MM  -> 4 MM
    # 04MM -> 04 MM
    # 4 MM -> 4 MM
    texto = re.sub(
        r"(\d+)\s*MM\b",
        r"\1 MM",
        texto
    )

    # 04 MM -> 4 MM
    # 08 MM -> 8 MM
    texto = re.sub(
        r"\b0(\d)\s+MM\b",
        r"\1 MM",
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
# CONFIGURAÇÃO DAS CHAPAS POR MATERIAL
# ===================================

ARQUIVO_CHAPAS = "chapas_materiais.json"

LARGURA_CHAPA_PADRAO = 3210
ALTURA_CHAPA_PADRAO = 2400


def carregar_configuracao_chapas():

    configuracao_padrao = {
        "_PADRAO": {
            "largura": LARGURA_CHAPA_PADRAO,
            "altura": ALTURA_CHAPA_PADRAO
        }
    }

    try:

        if not os.path.exists(
            ARQUIVO_CHAPAS
        ):

            with open(
                ARQUIVO_CHAPAS,
                "w",
                encoding="utf-8"
            ) as arquivo:

                json.dump(
                    configuracao_padrao,
                    arquivo,
                    ensure_ascii=False,
                    indent=4
                )

            return configuracao_padrao

        with open(
            ARQUIVO_CHAPAS,
            "r",
            encoding="utf-8"
        ) as arquivo:

            dados = json.load(
                arquivo
            )

        if not isinstance(
            dados,
            dict
        ):

            return configuracao_padrao

        if "_PADRAO" not in dados:

            dados["_PADRAO"] = (
                configuracao_padrao["_PADRAO"]
            )

        return dados

    except Exception:

        return configuracao_padrao


def salvar_configuracao_chapas(
    configuracao
):

    with open(
        ARQUIVO_CHAPAS,
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            configuracao,
            arquivo,
            ensure_ascii=False,
            indent=4
        )


def obter_chapa_material(
    codigo,
    configuracao
):

    codigo = str(
        codigo
    )

    dados = configuracao.get(
        codigo
    )

    if not isinstance(
        dados,
        dict
    ):

        dados = configuracao.get(
            "_PADRAO",
            {
                "largura": LARGURA_CHAPA_PADRAO,
                "altura": ALTURA_CHAPA_PADRAO
            }
        )

    try:

        largura = float(
            dados.get(
                "largura",
                LARGURA_CHAPA_PADRAO
            )
        )

        altura = float(
            dados.get(
                "altura",
                ALTURA_CHAPA_PADRAO
            )
        )

    except (
        ValueError,
        TypeError
    ):

        largura = (
            LARGURA_CHAPA_PADRAO
        )

        altura = (
            ALTURA_CHAPA_PADRAO
        )

    return (
        largura,
        altura
    )


def desenhar_chapa_otimizacao(
    chapa,
    material,
    numero_chapa,
    total_chapas
):
    """Desenha uma chapa já otimizada, com cache para navegação rápida."""

    cache = st.session_state.setdefault(
        "_cache_figuras_chapas",
        {}
    )

    largura_chapa = float(chapa.largura)
    altura_chapa = float(chapa.altura)

    # Chave estável: se o Streamlit fizer rerun, a mesma chapa
    # continua sendo reconhecida e o gráfico pronto é reutilizado.
    assinatura = [
        str(material),
        str(numero_chapa),
        f"{largura_chapa:.3f}",
        f"{altura_chapa:.3f}",
        str(len(chapa.pecas)),
    ]

    for posicionamento in chapa.pecas:
        peca = posicionamento.peca
        assinatura.extend([
            f"{float(posicionamento.x):.3f}",
            f"{float(posicionamento.y):.3f}",
            f"{float(posicionamento.largura):.3f}",
            f"{float(posicionamento.altura):.3f}",
            "1" if bool(
                getattr(posicionamento, "girada", False)
            ) else "0",
            str(getattr(peca, "pedido", "")),
            str(getattr(peca, "cliente", "")),
            str(getattr(peca, "pc", "")),
            str(getattr(peca, "rota", "")),
        ])

    chave = "|".join(assinatura)

    if chave in cache:
        dados = cache[chave]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📐 Chapa", dados["dimensoes"])
        c2.metric("🧩 Peças", dados["qtd_pecas"])
        c3.metric("📈 Aproveitamento", dados["aproveitamento"])
        c4.metric("⚠️ Desperdício", dados["desperdicio"])

        st.plotly_chart(
            dados["fig"],
            use_container_width=True,
            key=f"fig_chapa_{abs(hash(chave))}",
            config={
                "displaylogo": False,
                "scrollZoom": True,
                "responsive": True
            }
        )

        if dados["detalhes"]:
            with st.expander(
                "📋 Detalhes das peças desta chapa"
            ):
                st.dataframe(
                    pd.DataFrame(dados["detalhes"]),
                    use_container_width=True,
                    hide_index=True,
                    height=350
                )
        return

    desperdicio = (
        float(chapa.desperdicio) / 1_000_000
    )
    aproveitamento = float(chapa.aproveitamento)

    # Monta a figura somente na primeira vez.
    fig = go.Figure()

    fig.add_shape(
        type="rect",
        x0=0,
        y0=0,
        x1=largura_chapa,
        y1=altura_chapa,
        line=dict(width=2)
    )

    detalhes_pecas = []

    for indice, posicionamento in enumerate(
        chapa.pecas,
        start=1
    ):
        x = float(posicionamento.x)
        y = float(posicionamento.y)
        w = float(posicionamento.largura)
        h = float(posicionamento.altura)

        peca = posicionamento.peca

        pedido = str(
            getattr(peca, "pedido", "")
        ).strip()
        cliente = str(
            getattr(peca, "cliente", "")
        ).strip()
        pc = str(
            getattr(peca, "pc", "")
        ).strip()
        rota = str(
            getattr(peca, "rota", "")
        ).strip()

        girada = bool(
            getattr(posicionamento, "girada", False)
        )

        detalhes = [f"Peça {indice}"]

        if pedido:
            detalhes.append(f"Pedido: {pedido}")
        if cliente:
            detalhes.append(f"Cliente: {cliente}")
        if pc:
            detalhes.append(f"PC: {pc}")
        if rota:
            detalhes.append(f"Rota: {rota}")

        detalhes.append(f"{w:.0f} × {h:.0f} mm")

        if girada:
            detalhes.append("↻ Girada")

        # Shape da peça.
        fig.add_shape(
            type="rect",
            x0=x,
            y0=y,
            x1=x + w,
            y1=y + h,
            line=dict(width=1),
            fillcolor="rgba(100, 149, 237, 0.35)"
        )

        # Mantém o texto visual dentro das peças, como antes.
        fig.add_annotation(
            x=x + w / 2,
            y=y + h / 2,
            text="<br>".join(detalhes),
            showarrow=False,
            font=dict(size=9),
            align="center"
        )

        detalhes_pecas.append(
            {
                "Peça": indice,
                "Pedido": pedido,
                "Cliente": cliente,
                "PC": pc,
                "Rota": rota,
                "X (mm)": round(x, 1),
                "Y (mm)": round(y, 1),
                "Largura (mm)": round(w, 1),
                "Altura (mm)": round(h, 1),
                "Girou": "SIM" if girada else "NÃO"
            }
        )

    fig.update_xaxes(
        title="Largura (mm)",
        range=[0, largura_chapa]
    )
    fig.update_yaxes(
        title="Altura (mm)",
        range=[0, altura_chapa],
        scaleanchor="x",
        scaleratio=1
    )

    fig.update_layout(
        title=(
            f"{material} — Chapa "
            f"{numero_chapa}/{total_chapas}"
        ),
        height=700,
        margin=dict(l=20, r=20, t=60, b=20),
        showlegend=False
    )

    cache[chave] = {
        "fig": fig,
        "detalhes": detalhes_pecas,
        "dimensoes": (
            f"{largura_chapa:.0f} × "
            f"{altura_chapa:.0f} mm"
        ),
        "qtd_pecas": len(chapa.pecas),
        "aproveitamento": f"{aproveitamento:.2f}%",
        "desperdicio": f"{desperdicio:.2f} m²"
    }

    st.plotly_chart(
        fig,
        use_container_width=True,
        key=f"fig_chapa_{abs(hash(chave))}",
        config={
            "displaylogo": False,
            "scrollZoom": True,
            "responsive": True
        }
    )

    if detalhes_pecas:
        with st.expander(
            "📋 Detalhes das peças desta chapa"
        ):
            st.dataframe(
                pd.DataFrame(detalhes_pecas),
                use_container_width=True,
                hide_index=True,
                height=350
            )



# =====================================
# CONFIGURAÇÃO DE CHAPAS POR MATERIAL
# =====================================

configuracao_chapas = carregar_configuracao_chapas()

st.markdown("---")

st.subheader(
    "📐 Configuração de Chapas por Material"
)

st.caption(
    "Selecione um material para consultar ou alterar "
    "a medida da chapa utilizada na otimização."
)


# =====================================
# IDENTIFICA OS MATERIAIS DA PLANILHA
# =====================================

if (
    not df_final.empty
    and "Produto" in df_final.columns
):

    materiais_disponiveis = (
        df_final["Produto"]
        .dropna()
        .astype(str)
        .apply(codigo_material)
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    materiais_disponiveis = sorted(
        materiais_disponiveis
    )

else:

    materiais_disponiveis = []


# =====================================
# SELEÇÃO DO MATERIAL
# =====================================

if materiais_disponiveis:

    material_selecionado = st.selectbox(
        "🪵 Selecione o material",
        options=materiais_disponiveis,
        key="material_chapa_selecionado"
    )


    # =================================
    # BUSCA A MEDIDA ATUAL
    # =================================

    largura_atual, altura_atual = (
        obter_chapa_material(
            material_selecionado,
            configuracao_chapas
        )
    )


    # =================================
    # MOSTRA A DESCRIÇÃO DO MATERIAL
    # =================================

    descricao_atual = ""

    try:

        produtos_material = (
            df_final[
                df_final["Produto"]
                .astype(str)
                .apply(codigo_material)
                == material_selecionado
            ]["Produto"]
            .dropna()
            .astype(str)
            .unique()
        )

        if len(produtos_material) > 0:

            descricao_atual = (
                produtos_material[0]
            )

    except Exception:

        descricao_atual = ""


    if descricao_atual:

        st.info(
            f"Material selecionado: "
            f"**{material_selecionado}** — "
            f"{descricao_atual}"
        )

    else:

        st.info(
            f"Material selecionado: "
            f"**{material_selecionado}**"
        )
        # =================================
    # =================================
    # MEDIDAS DA CHAPA
    # =================================

    col1, col2 = st.columns(2)

    with col1:

        nova_largura = st.number_input(
            "📏 Largura da chapa (mm)",
            min_value=100,
            max_value=10000,
            value=int(largura_atual),
            step=1,
            format="%d",
            key=(
                f"largura_chapa_"
                f"{material_selecionado}"
            )
        )

    with col2:

        nova_altura = st.number_input(
            "📐 Altura da chapa (mm)",
            min_value=100,
            max_value=10000,
            value=int(altura_atual),
            step=1,
            format="%d",
            key=(
                f"altura_chapa_"
                f"{material_selecionado}"
            )
        )

    # =================================
    # MOSTRA A MEDIDA ATUAL
    # =================================

    st.write(
        f"**Medida configurada:** "
        f"{nova_largura} × "
        f"{nova_altura} mm"
    )

    # =================================
    # SALVAR
    # =================================

    if st.button(
        "💾 Salvar medida deste material",
        type="primary",
        key="salvar_medida_material"
    ):

        configuracao_chapas[
            material_selecionado
        ] = {
            "largura": int(
                nova_largura
            ),
            "altura": int(
                nova_altura
            )
        }

        salvar_configuracao_chapas(
            configuracao_chapas
        )

        st.success(
            f"✅ Medida salva para o material "
            f"**{material_selecionado}**: "
            f"{nova_largura} × "
            f"{nova_altura} mm"
        )

else:

    st.info(
        "Nenhum material foi encontrado "
        "nas planilhas carregadas."
    )


# =====================================
# VISÃO MATÉRIA-PRIMA
# =====================================

st.markdown("---")

mostrar_mp = st.checkbox(
    "🪵 Mostrar Matéria-Prima",
    value=False,
    key="mostrar_materia_prima"
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
            "Produto" not in df_final.columns
            or "M2 Vendido" not in df_final.columns
        ):

            st.error(
                "❌ As colunas Produto "
                "ou M2 Vendido não foram "
                "encontradas."
            )
            st.stop()

        else:

            consumo = (
                df_final[["Produto", "M2 Vendido"]]
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
                    consumo["M2 Vendido"],
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

            # ✅ Consolida materiais iguais (ex: INC10)
            consumo = (
                consumo
                .groupby(
                    "Codigo",
                    as_index=False
                )["Consumo"]
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

        colunas_existentes = [
            coluna
            for coluna in colunas_detalhe
            if coluna in df_final.columns
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

        consumo_data["Consumo Dia"] = (
            pd.to_numeric(
                consumo_data[
                    "M2 Vendido"
                ],
                errors="coerce"
            )
            .fillna(0)
        )

        if "Previsão" in consumo_data.columns:

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
            coluna
            for coluna in colunas_pecas
            if coluna in df_final.columns
        ]

        colunas_pecas_obrigatorias = [
            "Produto",
            "Largura",
            "Altura"
        ]

        colunas_pecas_faltantes = [
            coluna
            for coluna in colunas_pecas_obrigatorias
            if coluna not in colunas_pecas
        ]

        if colunas_pecas_faltantes:
            st.error(
                "❌ Não foi possível executar a otimização. "
                "Faltam as colunas: "
                + ", ".join(colunas_pecas_faltantes)
            )
            st.stop()

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

        pecas["Largura Corte"] = (
            pecas["Largura"] + 4
        )

        pecas["Altura Corte"] = (
            pecas["Altura"] + 4
        )

        # Área da peça em m²

        pecas["Área"] = (
            pecas["Largura Corte"]
            *
            pecas["Altura Corte"]
        ) / 1000000


        # =================================
        # TAMANHO UTILIZADO NO ENCAIXE
        # =================================

        # O cálculo da distância mínima
        # é feito somente no otimizador.py.

        pecas["Largura Encaixe"] = (
            pecas["Largura Corte"]
        )

        pecas["Altura Encaixe"] = (
            pecas["Altura Corte"]
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

                largura, altura = (
                    altura,
                    largura
                )

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


        # =================================
        # EXECUTA A OTIMIZAÇÃO
        # =================================

        resultado_otimizacao = otimizar_lista(
            lista_otimizacao,
            configuracao_chapas
        )

        resumo_otimizado = pd.DataFrame(
            resumo_otimizacao(
                resultado_otimizacao
            )
        )


        # =================================
        # GARANTE AS COLUNAS DO RESUMO
        # =================================

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
        # EXIBE RESUMO OTIMIZADO
        # =================================

        with st.expander(
            "📋 Resumo da Otimização"
        ):

            colunas_visiveis = [
                "Codigo",
                "Qtd Chapas",
                "Área Total",
                "Área Utilizada",
                "Desperdício Total",
                "Aproveitamento (%)"
            ]

            st.dataframe(
                resumo_otimizado[
                    colunas_visiveis
                ],
                use_container_width=True,
                hide_index=True
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

            materiais_otimizacao[codigo] = (
                tabela
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

        resumo = resumo[
            resumo["Consumo"] > 0
        ].copy()


        # Remove possíveis cabeçalhos.

        resumo = resumo[
            ~resumo["Codigo"]
            .astype(str)
            .str.contains(
                "CODIG|CÓDIG",
                case=False,
                na=False
            )
        ]

        resumo = resumo[
            ~resumo["Descricao"]
            .astype(str)
            .str.contains(
                "DESCRI",
                case=False,
                na=False
            )
        ]


        # =================================
        # COBERTURA
        # =================================

        produz_ate = []
        primeira_falta = []

        for _, linha in resumo.iterrows():

            codigo_atual = (
                linha["Codigo"]
            )

            saldo_atual = (
                linha["Estoque"]
            )

            tabela_material = (
                consumo_data[
                    consumo_data["Codigo"]
                    == codigo_atual
                ]
                .copy()
            )

            if (
                "Previsão"
                in tabela_material.columns
            ):

                tabela_material = (
                    tabela_material
                    .sort_values(
                        "Previsão"
                    )
                )

            ultima_data_ok = pd.NaT
            primeira_data_sem = pd.NaT


            for _, item in (
                tabela_material.iterrows()
            ):

                consumo_dia = (
                    item["Consumo Dia"]
                )

                if (
                    saldo_atual
                    >=
                    consumo_dia
                ):

                    saldo_atual -= (
                        consumo_dia
                    )

                    if (
                        "Previsão"
                        in item.index
                    ):

                        ultima_data_ok = (
                            item["Previsão"]
                        )

                else:

                    if (
                        "Previsão"
                        in item.index
                    ):

                        primeira_data_sem = (
                            item["Previsão"]
                        )

                    break


            produz_ate.append(
                ultima_data_ok
            )

            primeira_falta.append(
                primeira_data_sem
            )


        resumo["Produz até"] = (
            produz_ate
        )

        resumo["Primeira Falta"] = (
            primeira_falta
        )


        # =====================================
        # JUNTA RESULTADO DA OTIMIZAÇÃO
        # =====================================

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

            resumo["Qtd Chapas"] = 0
            resumo["Área Total"] = 0
            resumo["Área Utilizada"] = 0
            resumo["Desperdício Total"] = 0
            resumo["Aproveitamento (%)"] = 0


        # =================================
        # MEDIDA DA CHAPA POR MATERIAL
        # =================================

        larguras_chapa = []
        alturas_chapa = []
        areas_chapa = []


        for _, linha in resumo.iterrows():

            codigo_atual = str(
                linha["Codigo"]
            )

            largura_atual, altura_atual = (
                obter_chapa_material(
                    codigo_atual,
                    configuracao_chapas
                )
            )

            area_atual = (
                largura_atual
                *
                altura_atual
            ) / 1_000_000

            larguras_chapa.append(
                largura_atual
            )

            alturas_chapa.append(
                altura_atual
            )

            areas_chapa.append(
                area_atual
            )


        resumo["Largura Chapa"] = (
            larguras_chapa
        )

        resumo["Altura Chapa"] = (
            alturas_chapa
        )

        resumo["Área Chapa"] = (
            areas_chapa
        )
                # =================================
        # CHAPAS OTIMIZADAS
        # =================================

        # Quantidade de chapas realmente
        # utilizadas pelo resultado da otimização.

        resumo["Chapas Otimizadas"] = (
            resumo["Qtd Chapas"]
        )


        # =================================
        # CHAPAS EM ESTOQUE
        # =================================

        # Converte o estoque existente em
        # quantidade equivalente de chapas.

        resumo["Chapas Estoque"] = (
            resumo["Estoque"]
            /
            resumo["Área Chapa"]
        )


        # =================================
        # QTD CHAPAS A COMPRAR
        # =================================

        # Desconta do resultado da otimização
        # a quantidade equivalente existente
        # no estoque.
        #
        # Como a compra é feita em chapas inteiras,
        # arredonda sempre para cima.

        resumo["Qtd Chapas a Comprar"] = (
            resumo["Chapas Otimizadas"]
            -
            resumo["Chapas Estoque"]
        ).clip(
            lower=0
        ).apply(
            lambda valor: int(
                math.ceil(valor)
            )
        )


        # =================================
        # COMPRA NECESSÁRIA
        # =================================

        # Mantida para cálculo interno.
        # Esta coluna será ocultada na tabela.

        resumo["Compra Necessária"] = (
            resumo["Qtd Chapas a Comprar"]
            *
            resumo["Área Chapa"]
        ).round(2)


        # =================================
        # COMPRA COM PERDA
        # =================================

        # Área total necessária considerando
        # o resultado da otimização e o estoque.

        resumo["Compra c/ Perda"] = (
            (
                resumo["Área Total"]
                -
                resumo["Estoque"]
            )
            .clip(
                lower=0
            )
            .round(2)
        )


        # =================================
        # PERCENTUAL DE PERDA
        # =================================

        # Percentual de desperdício gerado
        # pela otimização.

        resumo["% Perda"] = (
            (
                resumo["Desperdício Total"]
                /
                resumo["Área Total"]
            )
            .replace(
                [math.inf, -math.inf],
                0
            )
            .fillna(0)
            .mul(100)
            .round(2)
        )


        # =================================
        # STATUS
        # =================================

        resumo["Status"] = resumo.apply(
            lambda linha:
                "🟢 OK"
                if linha["Qtd Chapas a Comprar"] == 0
                else "🔴 Comprar",
            axis=1
        )


        # =================================
        # ARREDONDAMENTO
        # =================================

        for coluna in [
            "Estoque",
            "Consumo",
            "Saldo",
            "Chapas Estoque",
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
        


        
        # =====================================
        # INDICADORES DA MP
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
                    resumo["Status"]
                    ==
                    "🔴 Comprar"
                ).sum()
            )
        )

        total_compra = int(
            resumo["Qtd Chapas a Comprar"].sum()
        )

        col3.metric(
            "🧱 Total Chapas",
            total_compra
        )

        col4.metric(
            "⚠️ Falta Material",
            int(
                (
                    resumo["Primeira Falta"]
                    !=
                    ""
                ).sum()
            )
        )

        col5.metric(
            "🟢 OK",
            int(
                (
                    resumo["Status"]
                    ==
                    "🟢 OK"
                ).sum()
            )
        )
                    

        # =====================================
        # COLUNAS DA TABELA
        # =====================================

        colunas_tabela = [
            "Codigo",
            "Descricao",
            "Estoque",
            "Consumo",
            "Saldo",
            "Produz até",
            "Primeira Falta",
            "Qtd Chapas Otimizadas",
            "Compra c/ Perda",
            "Qtd Chapas a Comprar",
            "Compra Necessária",
            "% Perda",
            "Status"
        ]

        # =====================================
        # QTD CHAPAS OTIMIZADAS
        # =====================================

        resumo["Qtd Chapas Otimizadas"] = (
            resumo["Chapas Otimizadas"]
        )


        # =====================================
        # COLUNAS OCULTAS
        # =====================================

        colunas_ocultas = [
            "Codigo",
            "Compra Necessária"
        ]


        # =====================================
        # COLUNAS QUE SERÃO EXIBIDAS
        # =====================================

        colunas_exibir = [
            coluna
            for coluna in colunas_tabela
            if coluna not in colunas_ocultas
        ]

        # =====================================
        # PREPARA TABELA
        # =====================================

        tabela = resumo.copy()

        tabela = (
            tabela
            .dropna(
                how="all"
            )
        )

        tabela = tabela[
            (tabela["Estoque"] != 0)
            |
            (tabela["Consumo"] != 0)
            |
            (tabela["Saldo"] != 0)
        ]


        # Mantém somente as colunas
        # escolhidas para visualização.

        tabela = tabela[
            colunas_exibir
        ].copy()

        # Código oculto usado para ligar a linha
        # selecionada ao resultado_otimizacao.
        tabela["_CodigoVisualizacao"] = (
            resumo.loc[
                tabela.index,
                "Codigo"
            ].astype(str).values
        )


        # =====================================
        # CONFIGURAÇÃO DO AGGRID
        # =====================================

        gb = (
            GridOptionsBuilder
            .from_dataframe(
                tabela
            )
        )

        gb.configure_default_column(
            editable=False,
            sortable=True,
            filter=True,
            resizable=True,
            cellStyle={
                "textAlign": "center"
            },
            headerClass=(
                "ag-center-header"
            )
        )


        for coluna in tabela.columns:

            gb.configure_column(
                coluna,
                cellStyle={
                    "textAlign": "center"
                },
                headerClass=(
                    "ag-center-header"
                )
            )

        # Código técnico fica invisível.
        gb.configure_column(
            "_CodigoVisualizacao",
            hide=True
        )


        gridOptions = gb.build()


        # =====================================
        # EXIBE A TABELA DE MATÉRIA-PRIMA
        # =====================================

        st.caption(
            "A tabela de matéria-prima é apenas informativa. "
            "A visualização da chapa fica separada abaixo."
        )

        retorno_grid = AgGrid(
            tabela,
            gridOptions=gridOptions,
            fit_columns_on_grid_load=True,
            height=650,
            theme="streamlit",
            allow_unsafe_jscode=True,
            update_on=[]
        )

        # =====================================
        # VISUALIZAÇÃO DA OTIMIZAÇÃO
        # =====================================

        st.markdown("---")
        st.subheader("🧩 Visualização da Otimização")

        visualizar_desenho = st.checkbox(
            "👁️ Visualizar desenho da otimização",
            value=st.session_state.get(
                "visualizar_desenho_otimizacao",
                False
            ),
            key="visualizar_desenho_otimizacao"
        )

        if visualizar_desenho:

            # Materiais que realmente possuem resultado de otimização.
            materiais_visualizacao = sorted(
                materiais_otimizacao.keys()
            )

            if materiais_visualizacao:

                codigo_visualizacao = st.selectbox(
                    "🪵 Selecione o material",
                    options=materiais_visualizacao,
                    format_func=lambda codigo: str(codigo),
                    key="material_visualizacao_otimizacao"
                )

                chapas_desenho = (
                    resultado_otimizacao.get(
                        codigo_visualizacao,
                        []
                    )
                    if isinstance(
                        resultado_otimizacao,
                        dict
                    )
                    else []
                )

                if chapas_desenho:

                    total_chapas = len(chapas_desenho)

                    # Guarda a posição atual por material.
                    chave_indice = (
                        "indice_chapa_visualizacao_"
                        + str(codigo_visualizacao)
                    )

                    if chave_indice not in st.session_state:
                        st.session_state[chave_indice] = 0

                    indice_chapa = int(
                        st.session_state[chave_indice]
                    )

                    indice_chapa = max(
                        0,
                        min(
                            indice_chapa,
                            total_chapas - 1
                        )
                    )

                    # ---------------------------------
                    # NAVEGAÇÃO
                    # ---------------------------------

                    nav1, nav2, nav3 = st.columns(
                        [1, 2, 1]
                    )

                    with nav1:
                        if st.button(
                            "◀ Anterior",
                            disabled=indice_chapa <= 0,
                            use_container_width=True,
                            key=(
                                "chapa_anterior_"
                                + str(codigo_visualizacao)
                            )
                        ):
                            st.session_state[
                                chave_indice
                            ] = max(
                                0,
                                indice_chapa - 1
                            )
                            st.rerun()

                    with nav2:
                        st.markdown(
                            f"""
                            <div style="
                                text-align:center;
                                font-size:20px;
                                font-weight:600;
                                padding-top:5px;
                            ">
                                Chapa {indice_chapa + 1}
                                de {total_chapas}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    with nav3:
                        if st.button(
                            "Próxima ▶",
                            disabled=(
                                indice_chapa
                                >= total_chapas - 1
                            ),
                            use_container_width=True,
                            key=(
                                "chapa_proxima_"
                                + str(codigo_visualizacao)
                            )
                        ):
                            st.session_state[
                                chave_indice
                            ] = min(
                                total_chapas - 1,
                                indice_chapa + 1
                            )
                            st.rerun()

                    # ---------------------------------
                    # DESENHO
                    # ---------------------------------

                    desenhar_chapa_otimizacao(
                        chapas_desenho[indice_chapa],
                        codigo_visualizacao,
                        indice_chapa + 1,
                        total_chapas
                    )

                else:
                    st.info(
                        "Não existem chapas para este material."
                    )

            else:
                st.info(
                    "Nenhum material possui chapas "
                    "otimizadas para os filtros atuais."
                )

        # =====================================
        # DETALHAR MATERIAL

        # =====================================

        st.markdown("---")
        st.subheader(
            "🔍 Detalhar Material"
        )

        if not resumo.empty:

            materiais = (
                resumo["Codigo"].astype(str)
                + " - "
                + resumo["Descricao"].astype(str)
            ).tolist()

            material_detalhado = st.selectbox(
                "Selecione o material",
                sorted(materiais),
                key="select_material_detalhamento_mp"
            )

            codigo_selecionado = (
                material_detalhado
                .split(" - ", 1)[0]
            )

            detalhe = (
                consumo_data[
                    consumo_data["Codigo"].astype(str)
                    == str(codigo_selecionado)
                ]
                .copy()
            )

            if "Previsão" in detalhe.columns:
                detalhe = (
                    detalhe
                    .sort_values("Previsão")
                    .copy()
                )

                detalhe["Previsão"] = (
                    pd.to_datetime(
                        detalhe["Previsão"],
                        errors="coerce"
                    )
                    .dt.strftime("%d/%m/%Y")
                    .fillna("")
                )

            if "Consumo Dia" in detalhe.columns:
                detalhe["Consumo Dia"] = (
                    pd.to_numeric(
                        detalhe["Consumo Dia"],
                        errors="coerce"
                    )
                    .fillna(0)
                    .round(2)
                )

            colunas_detalhe_exibir = [
                coluna
                for coluna in [
                    "Previsão",
                    "Pedido",
                    "Cliente",
                    "PC",
                    "Rota",
                    "Consumo Dia"
                ]
                if coluna in detalhe.columns
            ]

            if not detalhe.empty and colunas_detalhe_exibir:
                st.dataframe(
                    detalhe[colunas_detalhe_exibir],
                    use_container_width=True,
                    hide_index=True,
                    height=350
                )
            else:
                st.info(
                    "Nenhum registro encontrado "
                    "para o material selecionado."
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
            key="download_materia_prima",
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

    value=True,
    key="mostrar_tabela_rota"

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

    value=True,
    key="mostrar_tabela_produto"

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
        value=False,
        key="mostrar_rota_x_produto"
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
        value=False,
        key="mostrar_detalhamento"
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
        value=False,
        key="mostrar_base_completa"
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

    key="download_planilha_filtrada",

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
