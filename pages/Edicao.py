import streamlit as st
import pandas as pd
from io import BytesIO
import json

# =========================================
# CONFIGURAÇÃO
# =========================================

st.set_page_config(
    page_title="Pedidos Em Aberto - Edição",
    page_icon="🔑",
    layout="wide"
)

st.title("🔑 Página de Edição")

# =========================================
# SENHA
# =========================================

senha = st.text_input(
    "Digite a senha para acessar:",
    type="password"
)

if senha == "":

    st.info("🔒 Digite a senha para acessar.")
    st.stop()

if senha != "Thiago2026!":

    st.error("❌ Senha incorreta.")
    st.stop()

# =========================================
# ACESSO LIBERADO
# =========================================

st.success("✅ Acesso liberado.")

# =========================================
# UPLOAD
# =========================================

arquivo = st.file_uploader(
    "Importar planilha",
    type=["xlsx", "xlsm"]
)

# =========================================
# FUNÇÃO INTELIGENTE
# =========================================

def encontrar_base_excel(arquivo):

    excel = pd.ExcelFile(arquivo)

    palavras_chave = [
        "pedido",
        "rota",
        "previs",
        "produto",
        "cliente",
        "pc"
    ]

    for aba in excel.sheet_names:

        try:

            for linha in range(10):

                teste = pd.read_excel(
                    arquivo,
                    sheet_name=aba,
                    header=linha
                )

                teste.columns = (
                    teste.columns
                    .astype(str)
                    .str.strip()
                )

                nomes = " ".join(
                    teste.columns.astype(str).str.lower()
                )

                encontrou = any(
                    palavra in nomes
                    for palavra in palavras_chave
                )

                if encontrou:

                    return teste, aba, linha

        except:

            pass

    return None, None, None

# =========================================
# PROCESSAMENTO
# =========================================

if arquivo:

    try:

        # =========================================
        # LEITURA AUTOMÁTICA
        # =========================================

        df, aba_encontrada, linha_encontrada = encontrar_base_excel(arquivo)

        if df is None:

            st.error(
                "❌ Não foi possível encontrar automaticamente a base da planilha."
            )

            st.stop()

        # =========================================
        # LIMPEZA COLUNAS
        # =========================================

        df.columns = (
            df.columns
            .astype(str)
            .str.strip()
        )

        # REMOVE COLUNAS UNNAMED
        df = df.loc[
            :,
            ~df.columns.str.contains(
                "^Unnamed",
                case=False
            )
        ]

        # REMOVE LINHAS TOTALMENTE VAZIAS
        df = df.dropna(
            how="all"
        )

        # =========================================
        # INFORMAÇÕES
        # =========================================

        st.success(
            f"✅ Base encontrada automaticamente | Aba: {aba_encontrada} | Cabeçalho linha: {linha_encontrada + 1}"
        )

        # =========================================
        # SALVAR BASE
        # =========================================

        df.to_excel(
            "dados.xlsx",
            index=False,
            engine="openpyxl"
        )

        st.success("✅ Planilha carregada e salva!")

        filtros = {}

        # =========================================
        # FILTRO ROTA
        # =========================================

        if "Rota" in df.columns:

            rotas = sorted(
                df["Rota"]
                .dropna()
                .astype(str)
                .unique()
            )

            rotas_selecionadas = st.multiselect(
                "Selecione as rotas prioritárias:",
                rotas
            )

            if rotas_selecionadas:

                filtros["rotas"] = rotas_selecionadas

        # =========================================
        # FILTRO DATA
        # =========================================

        if "Previsão" in df.columns:

            df["Previsão"] = pd.to_datetime(
                df["Previsão"],
                errors="coerce",
                dayfirst=True
            )

            df = df.dropna(
                subset=["Previsão"]
            )

            if not df.empty:

                min_date = df["Previsão"].min().date()
                max_date = df["Previsão"].max().date()

                start_date = st.date_input(
                    "Data inicial",
                    value=min_date,
                    min_value=min_date,
                    max_value=max_date,
                    format="DD/MM/YYYY"
                )

                end_date = st.date_input(
                    "Data final",
                    value=max_date,
                    min_value=min_date,
                    max_value=max_date,
                    format="DD/MM/YYYY"
                )

                filtros["start_date"] = str(start_date)
                filtros["end_date"] = str(end_date)

        # =========================================
        # FILTRO PC
        # =========================================

        if "PC" in df.columns:

            pcs = sorted(
                df["PC"]
                .dropna()
                .astype(str)
                .unique()
            )

            pcs_selecionados = st.multiselect(
                "Programação de carga:",
                pcs
            )

            if pcs_selecionados:

                filtros["pcs"] = pcs_selecionados

        # =========================================
        # SALVAR FILTROS
        # =========================================

        if filtros:

            with open("filtros.json", "w") as f:

                json.dump(
                    [filtros],
                    f
                )

            st.success("✅ Filtros salvos!")

        # =========================================
        # DOWNLOAD
        # =========================================

        st.subheader("📥 Exportar dados filtrados")

        def to_excel(df):

            output = BytesIO()

            with pd.ExcelWriter(
                output,
                engine="openpyxl"
            ) as writer:

                df.to_excel(
                    writer,
                    index=False,
                    sheet_name="Base Filtrada"
                )

            return output.getvalue()

        excel_file = to_excel(df)

        st.download_button(
            label="Baixar planilha filtrada (Excel)",
            data=excel_file,
            file_name="dados_filtrados.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:

        st.error(f"Erro ao ler a planilha: {e}")

# =========================================
# MOSTRAR BASE ATUAL
# =========================================

st.subheader("📋 Base Atual")

try:

    df_atual = pd.read_excel(
        "dados.xlsx",
        sheet_name=0
    )

    st.dataframe(
        df_atual,
        use_container_width=True,
        height=400
    )

except Exception:

    st.info("Nenhuma planilha carregada ainda.")

