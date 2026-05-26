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

    if (
        "Rota" in df.columns
        and
        "Previsão" in df.columns
        and
        "M2 Vendido" in df.columns
    ):

        df_rota = df.copy()

        df_rota["Previsão Texto"] = (
            df_rota["Previsão"]
            .dt.strftime("%d/%m/%Y")
        )

        ordem_datas = sorted(
            df_rota["Previsão"].dropna().unique()
        )

        ordem_datas = [
            pd.to_datetime(data).strftime("%d/%m/%Y")
            for data in ordem_datas
        ]

        tabela_rota = pd.pivot_table(
            df_rota,
            values="M2 Vendido",
            index="Rota",
            columns="Previsão Texto",
            aggfunc="sum",
            fill_value=0,
            margins=True,
            margins_name="TOTAL GERAL"
        )

        colunas_ordenadas = [
            c for c in ordem_datas
            if c in tabela_rota.columns
        ]

        if "TOTAL GERAL" in tabela_rota.columns:

            colunas_ordenadas.append("TOTAL GERAL")

        tabela_rota = tabela_rota[
            colunas_ordenadas
        ]

        tabela_rota = tabela_rota.loc[
            (tabela_rota != 0).any(axis=1)
        ]

        tabela_rota = tabela_rota.replace(
            0,
            ""
        )

        tabela_rota = tabela_rota.applymap(
            lambda x: round(x, 2)
            if isinstance(x, (int, float))
            else x
        )

        st.dataframe(
            tabela_rota,
            use_container_width=True,
            height=min(
                45 * (len(tabela_rota) + 1),
                600
            )
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

    st.subheader("🪟 Tabela por Produto")

    if (
        "Produto" in df.columns
        and
        "Previsão" in df.columns
        and
        "M2 Vendido" in df.columns
    ):

        df_produto = df.copy()

        df_produto["Previsão Texto"] = (
            df_produto["Previsão"]
            .dt.strftime("%d/%m/%Y")
        )

        ordem_datas = sorted(
            df_produto["Previsão"].dropna().unique()
        )

        ordem_datas = [
            pd.to_datetime(data).strftime("%d/%m/%Y")
            for data in ordem_datas
        ]

        tabela_produto = pd.pivot_table(
            df_produto,
            values="M2 Vendido",
            index="Produto",
            columns="Previsão Texto",
            aggfunc="sum",
            fill_value=0,
            margins=True,
            margins_name="TOTAL GERAL"
        )

        colunas_ordenadas = [
            c for c in ordem_datas
            if c in tabela_produto.columns
        ]

        if "TOTAL GERAL" in tabela_produto.columns:

            colunas_ordenadas.append("TOTAL GERAL")

        tabela_produto = tabela_produto[
            colunas_ordenadas
        ]

        tabela_produto = tabela_produto.loc[
            (tabela_produto != 0).any(axis=1)
        ]

        tabela_produto = tabela_produto.replace(
            0,
            ""
        )

        tabela_produto = tabela_produto.applymap(
            lambda x: round(x, 2)
            if isinstance(x, (int, float))
            else x
        )

        st.dataframe(
            tabela_produto,
            use_container_width=True,
            height=min(
                45 * (len(tabela_produto) + 1),
                600
            )
        )
