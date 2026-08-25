import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Usa o otimizador.py que já existe no seu projeto.
try:
    from otimizador import Peca, otimizar_lista
except ImportError:
    Peca = None
    otimizar_lista = None

st.set_page_config(
    page_title="Pedidos Em Aberto - Viewer",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Pedidos Em Aberto - Visualização")

# ==========================================================
# LEITURA DA BASE
# ==========================================================

try:
    df = pd.read_excel("dados.xlsx", sheet_name="Base")
except FileNotFoundError:
    st.error("⚠️ Nenhum arquivo foi carregado ainda no app principal.")
    st.stop()

df.columns = df.columns.astype(str)

# ==========================================================
# FILTROS
# ==========================================================

if "Cliente" in df.columns:
    clientes = sorted(df["Cliente"].dropna().astype(str).unique())
    cliente = st.sidebar.multiselect("Cliente", clientes)
    if cliente:
        df = df[df["Cliente"].astype(str).isin(cliente)]

if "Rota" in df.columns:
    rotas = sorted(df["Rota"].dropna().astype(str).unique())
    rota = st.sidebar.multiselect("Rota", rotas)
    if rota:
        df = df[df["Rota"].astype(str).isin(rota)]

if "Produto" in df.columns:
    produtos = sorted(df["Produto"].dropna().astype(str).unique())
    produto = st.sidebar.multiselect("Produto", produtos)
    if produto:
        df = df[df["Produto"].astype(str).isin(produto)]

if "Previsão" in df.columns:
    df["Previsão"] = pd.to_datetime(
        df["Previsão"],
        errors="coerce",
        dayfirst=True
    )
    df = df.dropna(subset=["Previsão"])

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
                & (df["Previsão"].dt.date <= end_date)
            ]

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
    pd.to_numeric(df["M2 Vendido"], errors="coerce").sum()
    if "M2 Vendido" in df.columns
    else 0
)

total_peso = (
    pd.to_numeric(df["Peso"], errors="coerce").sum()
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

if "Rota" in df.columns and "M2 Vendido" in df.columns:
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

if "Rota" in df.columns and "M2 Vendido" in df.columns:
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
# VISUALIZAÇÃO DA OTIMIZAÇÃO
# ==========================================================

st.divider()
st.subheader("🧩 Visualização da Otimização")

visualizar = st.checkbox(
    "👁️ Visualizar desenho da otimização",
    value=False
)

if visualizar:

    if Peca is None or otimizar_lista is None:
        st.error(
            "❌ Não foi possível importar o otimizador.py. "
            "Deixe o arquivo otimizador.py na mesma pasta deste viewer."
        )
    elif df.empty:
        st.info("Não existem peças no filtro atual.")
    else:
        st.caption(
            "O desenho abaixo usa as posições calculadas pelo "
            "otimizador.py. O algoritmo de nesting não é alterado."
        )

        # --------------------------------------------------
        # Escolha das colunas
        # --------------------------------------------------

        colunas = list(df.columns)

        def encontrar_coluna(nomes):
            for nome in nomes:
                if nome in colunas:
                    return nome
            return colunas[0] if colunas else None

        def indice_coluna(nomes):
            valor = encontrar_coluna(nomes)
            return colunas.index(valor) if valor in colunas else 0

        st.markdown("#### ⚙️ Configuração das peças")

        a, b, c = st.columns(3)

        with a:
            material_col = st.selectbox(
                "Material / Código",
                colunas,
                index=indice_coluna([
                    "Código",
                    "Codigo",
                    "Material",
                    "Produto",
                    "Vidro"
                ]),
                key="opt_material_col"
            )

        with b:
            largura_col = st.selectbox(
                "Largura (mm)",
                colunas,
                index=indice_coluna([
                    "Largura",
                    "Largura (mm)",
                    "Largura Corte",
                    "Base"
                ]),
                key="opt_largura_col"
            )

        with c:
            altura_col = st.selectbox(
                "Altura (mm)",
                colunas,
                index=indice_coluna([
                    "Altura",
                    "Altura (mm)",
                    "Altura Corte",
                    "Altura peça"
                ]),
                key="opt_altura_col"
            )

        d, e, f = st.columns(3)

        with d:
            pedido_col = st.selectbox(
                "Pedido",
                colunas,
                index=indice_coluna(["Pedido", "Nº Pedido", "Numero Pedido"]),
                key="opt_pedido_col"
            )

        with e:
            cliente_col = st.selectbox(
                "Cliente",
                ["(não usar)"] + colunas,
                index=(
                    1 + indice_coluna(["Cliente"])
                    if "Cliente" in colunas
                    else 0
                ),
                key="opt_cliente_col"
            )

        with f:
            pc_col = st.selectbox(
                "PC",
                ["(não usar)"] + colunas,
                index=(
                    1 + indice_coluna(["PC", "Pc"])
                    if ("PC" in colunas or "Pc" in colunas)
                    else 0
                ),
                key="opt_pc_col"
            )

        rota_opcoes = ["(não usar)"] + colunas
        rota_default = (
            1 + indice_coluna(["Rota"])
            if "Rota" in colunas
            else 0
        )

        rota_col = st.selectbox(
            "Rota",
            rota_opcoes,
            index=rota_default,
            key="opt_rota_col"
        )

        # --------------------------------------------------
        # Montagem das peças
        # --------------------------------------------------

        try:
            largura_num = pd.to_numeric(
                df[largura_col],
                errors="coerce"
            )

            altura_num = pd.to_numeric(
                df[altura_col],
                errors="coerce"
            )

            base_opt = df.copy()
            base_opt["_LARGURA_OPT"] = largura_num
            base_opt["_ALTURA_OPT"] = altura_num

            invalidas = base_opt[
                base_opt["_LARGURA_OPT"].isna()
                | base_opt["_ALTURA_OPT"].isna()
                | (base_opt["_LARGURA_OPT"] <= 0)
                | (base_opt["_ALTURA_OPT"] <= 0)
            ]

            base_opt = base_opt[
                ~base_opt.index.isin(invalidas.index)
            ].copy()

            if not invalidas.empty:
                st.warning(
                    f"⚠️ {len(invalidas)} linha(s) não possuem "
                    "largura/altura válidas e foram ignoradas."
                )

            lista_pecas = []

            for _, row in base_opt.iterrows():

                cliente_val = ""
                if cliente_col != "(não usar)":
                    cliente_val = str(row[cliente_col])

                pc_val = ""
                if pc_col != "(não usar)":
                    pc_val = str(row[pc_col])

                rota_val = ""
                if rota_col != "(não usar)":
                    rota_val = str(row[rota_col])

                lista_pecas.append(
                    Peca(
                        codigo=str(row[material_col]),
                        largura=float(row["_LARGURA_OPT"]),
                        altura=float(row["_ALTURA_OPT"]),
                        pedido=str(row[pedido_col]),
                        cliente=cliente_val,
                        pc=pc_val,
                        rota=rota_val
                    )
                )

            if not lista_pecas:
                st.warning(
                    "Não foi possível montar nenhuma peça "
                    "com as colunas selecionadas."
                )
            else:
                # --------------------------------------------------
                # Executa a otimização somente quando solicitado.
                # --------------------------------------------------

                executar = st.button(
                    "▶️ Gerar / atualizar otimização",
                    type="primary",
                    key="executar_visualizacao"
                )

                if executar:
                    with st.spinner(
                        "Calculando otimização das chapas..."
                    ):
                        resultado_otimizacao = otimizar_lista(
                            lista_pecas
                        )

                    st.session_state["resultado_visualizacao"] = (
                        resultado_otimizacao
                    )

                resultado_otimizacao = st.session_state.get(
                    "resultado_visualizacao"
                )

                if resultado_otimizacao:

                    materiais = sorted(
                        [
                            str(codigo)
                            for codigo, chapas
                            in resultado_otimizacao.items()
                            if chapas
                        ]
                    )

                    if materiais:

                        material = st.selectbox(
                            "Selecione o material",
                            materiais,
                            key="material_desenho"
                        )

                        chapas = resultado_otimizacao[material]

                        chapa_labels = [
                            f"Chapa {i + 1} de {len(chapas)}"
                            for i in range(len(chapas))
                        ]

                        chapa_label = st.selectbox(
                            "Selecione a chapa",
                            chapa_labels,
                            key=f"chapa_desenho_{material}"
                        )

                        indice = chapa_labels.index(chapa_label)
                        chapa = chapas[indice]

                        # --------------------------------------------------
                        # Indicadores da chapa
                        # --------------------------------------------------

                        area_total = chapa.area_total
                        area_utilizada = chapa.area_utilizada
                        desperdicio = chapa.desperdicio
                        aproveitamento = chapa.aproveitamento

                        m1, m2, m3, m4 = st.columns(4)

                        m1.metric(
                            "Dimensão da chapa",
                            f"{chapa.largura:.0f} × "
                            f"{chapa.altura:.0f} mm"
                        )

                        m2.metric(
                            "Peças",
                            len(chapa.pecas)
                        )

                        m3.metric(
                            "Aproveitamento",
                            f"{aproveitamento:.2f}%"
                        )

                        m4.metric(
                            "Perda",
                            f"{desperdicio / 1_000_000:.3f} m²"
                        )

                        # --------------------------------------------------
                        # DESENHO
                        # --------------------------------------------------

                        fig_chapa = go.Figure()

                        # Contorno da chapa
                        fig_chapa.add_shape(
                            type="rect",
                            x0=0,
                            y0=0,
                            x1=chapa.largura,
                            y1=chapa.altura,
                            line=dict(width=3),
                            fillcolor="rgba(220,220,220,0.30)"
                        )

                        hover_x = []
                        hover_y = []
                        hover_text = []

                        for numero, pos in enumerate(
                            chapa.pecas,
                            start=1
                        ):
                            peca = pos.peca

                            # Posicionamento já calculado pelo MaxRects.
                            largura = pos.largura
                            altura = pos.altura

                            x0 = pos.x
                            y0 = pos.y
                            x1 = x0 + largura
                            y1 = y0 + altura

                            fig_chapa.add_shape(
                                type="rect",
                                x0=x0,
                                y0=y0,
                                x1=x1,
                                y1=y1,
                                line=dict(width=1),
                                fillcolor="rgba(100,149,237,0.35)"
                            )

                            pedido = str(
                                peca.pedido
                            ).strip()

                            if not pedido or pedido.lower() == "nan":
                                pedido = f"Peça {numero}"

                            orientacao = (
                                "90° - girada"
                                if pos.girada
                                else "0°"
                            )

                            # Texto visível dentro da peça.
                            fig_chapa.add_annotation(
                                x=x0 + largura / 2,
                                y=y0 + altura / 2,
                                text=(
                                    f"<b>{pedido}</b><br>"
                                    f"{largura:.0f} × "
                                    f"{altura:.0f} mm"
                                ),
                                showarrow=False,
                                font=dict(size=10),
                                align="center"
                            )

                            hover_x.append(
                                x0 + largura / 2
                            )
                            hover_y.append(
                                y0 + altura / 2
                            )

                            hover_text.append(
                                f"<b>Pedido:</b> {pedido}"
                                f"<br><b>Material:</b> {material}"
                                f"<br><b>Dimensão:</b> "
                                f"{largura:.0f} × {altura:.0f} mm"
                                f"<br><b>Orientação:</b> {orientacao}"
                                f"<br><b>Cliente:</b> "
                                f"{peca.cliente}"
                                f"<br><b>PC:</b> {peca.pc}"
                                f"<br><b>Rota:</b> {peca.rota}"
                                f"<br><b>Posição:</b> "
                                f"X {x0:.0f} / Y {y0:.0f} mm"
                            )

                        if hover_x:
                            fig_chapa.add_trace(
                                go.Scatter(
                                    x=hover_x,
                                    y=hover_y,
                                    mode="markers",
                                    marker=dict(
                                        size=18,
                                        opacity=0
                                    ),
                                    text=hover_text,
                                    hovertemplate=(
                                        "%{text}<extra></extra>"
                                    ),
                                    showlegend=False
                                )
                            )

                        fig_chapa.update_xaxes(
                            range=[0, chapa.largura],
                            title="Largura (mm)",
                            showgrid=True,
                            dtick=500
                        )

                        # Inverte o Y para a origem ficar no topo,
                        # como normalmente se espera em um desenho de corte.
                        fig_chapa.update_yaxes(
                            range=[chapa.altura, 0],
                            title="Altura (mm)",
                            showgrid=True,
                            dtick=500,
                            scaleanchor="x",
                            scaleratio=1
                        )

                        fig_chapa.update_layout(
                            height=700,
                            margin=dict(
                                l=30,
                                r=30,
                                t=30,
                                b=30
                            ),
                            showlegend=False
                        )

                        st.plotly_chart(
                            fig_chapa,
                            use_container_width=True
                        )

                        st.caption(
                            f"Área utilizada: "
                            f"{area_utilizada / 1_000_000:.3f} m²"
                            f"  |  Área da chapa: "
                            f"{area_total / 1_000_000:.3f} m²"
                            f"  |  Perda: "
                            f"{desperdicio / 1_000_000:.3f} m²"
                        )

                    else:
                        st.info(
                            "Não foram encontradas chapas "
                            "otimizadas."
                        )

        except Exception as erro:
            st.error(
                "❌ Não foi possível preparar a otimização."
            )
            st.exception(erro)

# ==========================================================
# BASE COMPLETA
# ==========================================================

st.divider()
st.subheader("Base Completa")
st.dataframe(
    df,
    use_container_width=True,
    height=400
)
