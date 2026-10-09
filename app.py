
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
