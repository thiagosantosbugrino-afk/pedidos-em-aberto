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

# ===================================
# EXPORTAÇÃO DAS TABELAS + RESUMO DOS FILTROS
# ===================================
# Funcionalidade adicional: preserva o aplicativo atual e acrescenta
# a exportação da base/tabelas e o resumo dos filtros ativos.

def _valor_resumo_filtro_exportacao(valor):
    if isinstance(valor, (list, tuple, set)):
        return ", ".join(str(item) for item in valor) if valor else "Todos / não selecionado"
    if isinstance(valor, dict):
        return ", ".join(f"{k}: {v}" for k, v in valor.items())
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return "Todos / não selecionado"
    return str(valor)


def _montar_resumo_filtros_exportacao():
    palavras_filtro = (
        "filtro", "rota", "produto", "tipo", "status", "previs", "data",
        "pc", "cliente", "pedido", "busca", "selecion", "periodo", "período"
    )
    linhas = []
    for chave, valor in st.session_state.items():
        chave_texto = str(chave)
        chave_lower = chave_texto.lower()
        if not any(palavra in chave_lower for palavra in palavras_filtro):
            continue
        if chave_lower.startswith(("mostrar_", "download_")):
            continue
        if isinstance(valor, bool):
            continue
        linhas.append({
            "Filtro": chave_texto.replace("_", " ").strip().title(),
            "Valor selecionado": _valor_resumo_filtro_exportacao(valor),
        })
    if not linhas:
        linhas.append({
            "Filtro": "Filtros aplicados",
            "Valor selecionado": "A base exportada já considera os filtros ativos na tela.",
        })
    return pd.DataFrame(linhas)


def _montar_excel_tabelas_exportacao():
    saida = BytesIO()
    resumo_filtros = _montar_resumo_filtros_exportacao()
    with pd.ExcelWriter(saida, engine="openpyxl") as writer:
        df_final.to_excel(writer, index=False, sheet_name="Base Filtrada")
        tabelas_exportadas = set()
        # Usa globals() para capturar tabelas DataFrame criadas no escopo do app.
        for nome, objeto in list(globals().items()):
            if not isinstance(objeto, pd.DataFrame):
                continue
            nome_lower = nome.lower()
            if not (nome_lower.startswith("tabela_") or nome_lower.startswith("df_detalhe")):
                continue
            if objeto is df_final or objeto.empty:
                continue
            nome_aba = nome.replace("tabela_", "").replace("df_", "")[:31] or "Tabela"
            nome_aba = "".join(c for c in nome_aba if c not in "[]:*?/\\") or "Tabela"
            nome_original = nome_aba
            contador = 2
            while nome_aba in tabelas_exportadas or nome_aba in {"Base Filtrada", "Resumo dos Filtros"}:
                sufixo = f"_{contador}"
                nome_aba = nome_original[:31-len(sufixo)] + sufixo
                contador += 1
            objeto.to_excel(writer, index=False, sheet_name=nome_aba)
            tabelas_exportadas.add(nome_aba)
        resumo_filtros.to_excel(writer, index=False, sheet_name="Resumo dos Filtros")
    return saida.getvalue(), resumo_filtros


excel_tabelas_exportacao, resumo_filtros_exportacao = _montar_excel_tabelas_exportacao()
st.markdown("---")
st.subheader("📥 Baixar tabelas e resumo dos filtros")
st.download_button(
    label="📥 Baixar tabelas + resumo dos filtros (Excel)",
    data=excel_tabelas_exportacao,
    file_name="tabelas_e_resumo_dos_filtros.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    key="download_tabelas_resumo_filtros",
)
st.subheader("🧾 Resumo dos filtros aplicados na exportação")
st.caption("A planilha inclui a base filtrada, as tabelas de análise disponíveis e uma aba com este resumo.")
st.dataframe(resumo_filtros_exportacao, use_container_width=True, hide_index=True)
