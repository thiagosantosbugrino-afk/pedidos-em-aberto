import json
import os
import re

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from equivalencias import EQUIVALENCIAS
from otimizador import Peca, otimizar_lista


st.set_page_config(
    page_title="Pedidos Em Aberto - Viewer",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Pedidos Em Aberto - Visualização")


# ==========================================================
# FUNÇÕES DE MATERIAL / CHAPAS
# ==========================================================

ARQUIVO_CHAPAS = "chapas_materiais.json"
LARGURA_CHAPA_PADRAO = 3210
ALTURA_CHAPA_PADRAO = 2400


def codigo_material(texto):
    if pd.isna(texto):
        return None

    texto = str(texto).upper().strip()
    texto = re.sub(r"\s+", " ", texto)
    texto = re.sub(r"(\d+)\s*MM\b", r"\1 MM", texto)

    return EQUIVALENCIAS.get(texto, texto)


def carregar_configuracao_chapas():
    padrao = {
        "_PADRAO": {
            "largura": LARGURA_CHAPA_PADRAO,
            "altura": ALTURA_CHAPA_PADRAO,
        }
    }

    try:
        if not os.path.exists(ARQUIVO_CHAPAS):
            return padrao

        with open(ARQUIVO_CHAPAS, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

        if not isinstance(dados, dict):
            return padrao

        dados.setdefault("_PADRAO", padrao["_PADRAO"])
        return dados

    except Exception:
        return padrao


def obter_chapa_material(codigo, configuracao):
    dados = configuracao.get(str(codigo))

    if not isinstance(dados, dict):
        dados = configuracao.get("_PADRAO", {})

    try:
        largura = float(
            dados.get("largura", LARGURA_CHAPA_PADRAO)
        )
        altura = float(
            dados.get("altura", ALTURA_CHAPA_PADRAO)
        )
    except (ValueError, TypeError):
        largura = LARGURA_CHAPA_PADRAO
        altura = ALTURA_CHAPA_PADRAO

    return largura, altura


# ==========================================================
# LEITURA DA BASE
# ==========================================================

try:
    df = pd.read_excel("dados.xlsx", sheet_name="Base")
except FileNotFoundError:
    try:
        df = pd.read_excel("dados.xlsx", sheet_name=0)
    except FileNotFoundError:
        st.error("⚠️ Nenhum arquivo foi carregado ainda no app principal.")
        st.stop()

df.columns = df.columns.astype(str).str.strip()


# ==========================================================
# FILTROS
# ==========================================================

if "Cliente" in df.columns:
    clientes = sorted(
        df["Cliente"].dropna().astype(str).unique()
    )
    cliente = st.sidebar.multiselect("Cliente", clientes)
    if cliente:
        df = df[
            df["Cliente"].astype(str).isin(cliente)
        ].copy()


if "Rota" in df.columns:
    rotas = sorted(
        df["Rota"].dropna().astype(str).unique()
    )
    rota = st.sidebar.multiselect("Rota", rotas)
    if rota:
        df = df[
            df["Rota"].astype(str).isin(rota)
        ].copy()


if "Produto" in df.columns:
    produtos = sorted(
        df["Produto"].dropna().astype(str).unique()
    )
    produto = st.sidebar.multiselect("Produto", produtos)
    if produto:
        df = df[
            df["Produto"].astype(str).isin(produto)
        ].copy()


if "Previsão" in df.columns:
    df["Previsão"] = pd.to_datetime(
        df["Previsão"],
        errors="coerce",
        dayfirst=True
    )

    df = df.dropna(
        subset=["Previsão"]
    ).copy()

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

        if start_date > end_date:
            st.sidebar.error(
                "⚠️ A data inicial não pode ser maior que a data final."
            )
        else:
            df = df[
                (df["Previsão"].dt.date >= start_date)
                &
                (df["Previsão"].dt.date <= end_date)
            ].copy()


# ==========================================================
# INDICADORES
# ==========================================================

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


# ==========================================================
# TABELA
# ==========================================================

st.subheader("Pedidos Em Aberto")

if (
    "Rota" in df.columns
    and "M2 Vendido" in df.columns
):
    tabela = pd.pivot_table(
        df,
        values="M2 Vendido",
        index="Rota",
        aggfunc="sum",
        fill_value=0,
        margins=True,
        margins_name="TOTAL GERAL"
    )

    st.dataframe(
        tabela,
        use_container_width=True,
        height=500
    )


# ==========================================================
# GRÁFICO
# ==========================================================

st.subheader("Produção por Rota")

if (
    "Rota" in df.columns
    and "M2 Vendido" in df.columns
):
    grafico = (
        df.groupby("Rota")["M2 Vendido"]
        .sum()
        .reset_index()
    )

    fig = px.bar(
        grafico,
        x="M2 Vendido",
        y="Rota",
        orientation="h",
        title="Produção por Rota"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ==========================================================
# OTIMIZAÇÃO / DESENHO DA CHAPA
# ==========================================================

st.markdown("---")
st.subheader("🧩 Visualização da Otimização")

st.caption(
    "A visualização abaixo usa o mesmo módulo "
    "`otimizador.py` do aplicativo principal. "
    "A otimização é recalculada somente para os registros "
    "que passaram pelos filtros deste Viewer."
)

visualizar_otimizacao = st.checkbox(
    "☑️ 👁️ Visualizar desenho da otimização",
    value=False
)


if visualizar_otimizacao:

    colunas_obrigatorias = [
        "Produto",
        "Largura",
        "Altura",
    ]

    faltantes = [
        coluna
        for coluna in colunas_obrigatorias
        if coluna not in df.columns
    ]

    if faltantes:
        st.error(
            "❌ Não foi possível executar a otimização. "
            "Faltam as colunas: "
            + ", ".join(faltantes)
        )
    elif df.empty:
        st.info(
            "Nenhum registro encontrado para os filtros selecionados."
        )
    else:

        configuracao_chapas = carregar_configuracao_chapas()

        pecas = df.copy()

        pecas["Codigo"] = (
            pecas["Produto"]
            .apply(codigo_material)
        )

        pecas["Largura"] = pd.to_numeric(
            pecas["Largura"],
            errors="coerce"
        )

        pecas["Altura"] = pd.to_numeric(
            pecas["Altura"],
            errors="coerce"
        )

        pecas = pecas.dropna(
            subset=[
                "Codigo",
                "Largura",
                "Altura"
            ]
        ).copy()

        lista_otimizacao = []

        for _, linha in pecas.iterrows():

            largura = float(linha["Largura"]) + 4
            altura = float(linha["Altura"]) + 4

            # Mantém a mesma normalização usada
            # pelo aplicativo principal antes de chamar
            # o otimizador.
            if altura > largura:
                largura, altura = altura, largura

            lista_otimizacao.append(
                Peca(
                    codigo=str(linha["Codigo"]),
                    largura=largura,
                    altura=altura,
                    pedido=str(
                        linha.get("Pedido", "")
                    ),
                    cliente=str(
                        linha.get("Cliente", "")
                    ),
                    pc=str(
                        linha.get("PC", "")
                    ),
                    rota=str(
                        linha.get("Rota", "")
                    )
                )
            )

        if not lista_otimizacao:
            st.warning(
                "⚠️ Nenhuma peça válida foi encontrada "
                "para a otimização."
            )
        else:

            with st.spinner(
                "Otimizando peças..."
            ):
                resultado_otimizacao = otimizar_lista(
                    lista_otimizacao,
                    configuracao_chapas
                )

            materiais = [
                codigo
                for codigo, chapas
                in sorted(resultado_otimizacao.items())
                if chapas
            ]

            if not materiais:
                st.warning(
                    "Nenhuma chapa foi gerada pela otimização."
                )
            else:

                material_selecionado = st.selectbox(
                    "🪵 Material",
                    materiais,
                    key="viewer_material_otimizacao"
                )

                chapas = resultado_otimizacao[
                    material_selecionado
                ]

                if not chapas:
                    st.info(
                        "Nenhuma chapa encontrada para este material."
                    )
                else:

                    numero_chapa = st.selectbox(
                        "📄 Chapa",
                        options=list(
                            range(1, len(chapas) + 1)
                        ),
                        format_func=lambda numero:
                            f"Chapa {numero} de {len(chapas)}",
                        key="viewer_numero_chapa"
                    )

                    chapa = chapas[
                        numero_chapa - 1
                    ]

                    largura_chapa = chapa.largura
                    altura_chapa = chapa.altura

                    # ------------------------------------------
                    # INDICADORES DA CHAPA
                    # ------------------------------------------

                    area_total = (
                        largura_chapa
                        * altura_chapa
                        / 1_000_000
                    )

                    area_utilizada = (
                        chapa.area_utilizada
                        / 1_000_000
                    )

                    desperdicio = (
                        chapa.desperdicio
                        / 1_000_000
                    )

                    aproveitamento = (
                        chapa.aproveitamento
                    )

                    a, b, c, d = st.columns(4)

                    a.metric(
                        "📐 Chapa",
                        f"{largura_chapa:.0f} × {altura_chapa:.0f} mm"
                    )

                    b.metric(
                        "🧩 Peças",
                        len(chapa.pecas)
                    )

                    c.metric(
                        "📈 Aproveitamento",
                        f"{aproveitamento:.2f}%"
                    )

                    d.metric(
                        "⚠️ Desperdício",
                        f"{desperdicio:.2f} m²"
                    )

                    # ------------------------------------------
                    # DESENHO
                    # ------------------------------------------

                    fig_chapa = go.Figure()

                    # Contorno da chapa.
                    fig_chapa.add_shape(
                        type="rect",
                        x0=0,
                        y0=0,
                        x1=largura_chapa,
                        y1=altura_chapa,
                        line=dict(width=2),
                    )

                    # Cada peça posicionada pelo próprio
                    # resultado do otimizador.
                    for indice, posicionamento in enumerate(
                        chapa.pecas,
                        start=1
                    ):

                        x = posicionamento.x
                        y = posicionamento.y
                        w = posicionamento.largura
                        h = posicionamento.altura

                        peca = posicionamento.peca

                        fig_chapa.add_shape(
                            type="rect",
                            x0=x,
                            y0=y,
                            x1=x + w,
                            y1=y + h,
                            line=dict(width=1),
                            fillcolor="rgba(100, 149, 237, 0.35)",
                        )

                        pedido = str(
                            peca.pedido
                        ).strip()

                        cliente = str(
                            peca.cliente
                        ).strip()

                        pc = str(
                            peca.pc
                        ).strip()

                        rota = str(
                            peca.rota
                        ).strip()

                        identificacao = (
                            f"{indice} | Pedido: {pedido}"
                            if pedido
                            else f"{indice}"
                        )

                        detalhes = []

                        if cliente:
                            detalhes.append(
                                f"Cliente: {cliente}"
                            )

                        if pc:
                            detalhes.append(
                                f"PC: {pc}"
                            )

                        if rota:
                            detalhes.append(
                                f"Rota: {rota}"
                            )

                        detalhes.append(
                            f"{w:.0f} × {h:.0f} mm"
                        )

                        if posicionamento.girada:
                            detalhes.append(
                                "↻ girada"
                            )

                        texto = (
                            identificacao
                            + "<br>"
                            + "<br>".join(detalhes)
                        )

                        fig_chapa.add_annotation(
                            x=x + w / 2,
                            y=y + h / 2,
                            text=texto,
                            showarrow=False,
                            font=dict(size=9),
                            align="center",
                        )

                    fig_chapa.update_xaxes(
                        title="Largura (mm)",
                        range=[0, largura_chapa],
                        constrain="domain",
                    )

                    fig_chapa.update_yaxes(
                        title="Altura (mm)",
                        range=[0, altura_chapa],
                        scaleanchor="x",
                        scaleratio=1,
                    )

                    fig_chapa.update_layout(
                        title=(
                            f"{material_selecionado} — "
                            f"Chapa {numero_chapa}/{len(chapas)}"
                        ),
                        height=700,
                        margin=dict(
                            l=20,
                            r=20,
                            t=60,
                            b=20
                        ),
                        showlegend=False,
                    )

                    st.plotly_chart(
                        fig_chapa,
                        use_container_width=True
                    )

                    # ------------------------------------------
                    # DETALHES DAS PEÇAS DA CHAPA
                    # ------------------------------------------

                    detalhes_chapa = []

                    for indice, posicionamento in enumerate(
                        chapa.pecas,
                        start=1
                    ):

                        peca = posicionamento.peca

                        detalhes_chapa.append(
                            {
                                "Peça": indice,
                                "Material": peca.codigo,
                                "Pedido": peca.pedido,
                                "Cliente": peca.cliente,
                                "PC": peca.pc,
                                "Rota": peca.rota,
                                "X (mm)": round(
                                    posicionamento.x,
                                    1
                                ),
                                "Y (mm)": round(
                                    posicionamento.y,
                                    1
                                ),
                                "Largura (mm)": round(
                                    posicionamento.largura,
                                    1
                                ),
                                "Altura (mm)": round(
                                    posicionamento.altura,
                                    1
                                ),
                                "Girou": (
                                    "SIM"
                                    if posicionamento.girada
                                    else "NÃO"
                                ),
                            }
                        )

                    st.dataframe(
                        pd.DataFrame(detalhes_chapa),
                        use_container_width=True,
                        hide_index=True,
                        height=350
                    )


# ==========================================================
# BASE COMPLETA
# ==========================================================

st.subheader("Base Completa")

st.dataframe(
    df,
    use_container_width=True,
    height=400
)
