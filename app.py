# ===================================
# DETALHAMENTO
# ===================================

if mostrar_detalhamento:

    st.subheader("🔎 Detalhamento")

    df_detalhe = df.copy()

    # ===================================
    # FILTRO DATA
    # ===================================

    if "Previsão" in df_detalhe.columns:

        min_det = df_detalhe["Previsão"].min().date()
        max_det = df_detalhe["Previsão"].max().date()

        col1, col2 = st.columns(2)

        with col1:

            detalhe_inicio = st.date_input(
                "Detalhamento - Data Inicial",
                value=min_det,
                key="det_inicio"
            )

        with col2:

            detalhe_fim = st.date_input(
                "Detalhamento - Data Final",
                value=max_det,
                key="det_fim"
            )

        df_detalhe = df_detalhe[
            (
                df_detalhe["Previsão"].dt.date >= detalhe_inicio
            )
            &
            (
                df_detalhe["Previsão"].dt.date <= detalhe_fim
            )
        ]

    # ===================================
    # FILTRO PRODUTO
    # ===================================

    if "Produto" in df_detalhe.columns:

        produtos_det = sorted(
            df_detalhe["Produto"]
            .dropna()
            .astype(str)
            .unique()
        )

        produto_det = st.multiselect(
            "Filtrar Produto",
            produtos_det,
            key="produto_det"
        )

        if produto_det:

            df_detalhe = df_detalhe[
                df_detalhe["Produto"]
                .astype(str)
                .isin(produto_det)
            ]

    # ===================================
    # FILTRO ROTA
    # ===================================

    if "Rota" in df_detalhe.columns:

        rotas_det = sorted(
            df_detalhe["Rota"]
            .dropna()
            .astype(str)
            .unique()
        )

        rota_det = st.multiselect(
            "Filtrar Rota",
            rotas_det,
            key="rota_det"
        )

        if rota_det:

            df_detalhe = df_detalhe[
                df_detalhe["Rota"]
                .astype(str)
                .isin(rota_det)
            ]

    # ===================================
    # FILTRO CARREGAMENTO / PC
    # ===================================

    if "PC" in df_detalhe.columns:

        pcs_det = sorted(
            df_detalhe["PC"]
            .dropna()
            .astype(str)
            .unique()
        )

        pc_det = st.multiselect(
            "Filtrar Carregamento",
            pcs_det,
            key="pc_det"
        )

        if pc_det:

            df_detalhe = df_detalhe[
                df_detalhe["PC"]
                .astype(str)
                .isin(pc_det)
            ]

    # ===================================
    # FILTRO PEDIDO
    # ===================================

    if "Pedido" in df_detalhe.columns:

        pedidos = sorted(
            df_detalhe["Pedido"]
            .dropna()
            .astype(str)
            .unique()
        )

        pedido_sel = st.selectbox(
            "Selecione o Pedido",
            ["Todos"] + pedidos
        )

        if pedido_sel != "Todos":

            df_detalhe = df_detalhe[
                df_detalhe["Pedido"]
                .astype(str) == pedido_sel
            ]

    # ===================================
    # TABELA
    # ===================================

    st.dataframe(
        df_detalhe,
        use_container_width=True,
        height=400
    )
