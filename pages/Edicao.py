import streamlit as st
import pandas as pd
from io import BytesIO
import json
from datetime import datetime
from zoneinfo import ZoneInfo

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
# ACESSO
# =========================================

st.success("✅ Acesso liberado.")

# =========================================
# MOSTRAR BASE ATUAL
# =========================================

df_existente = None

try:

    df_existente = pd.read_excel(
        "dados.xlsx",
        sheet_name=0
    )

    st.success("✅ Base atual carregada.")

except:

    pass

# =========================================
# UPLOAD
# =========================================

arquivo = st.file_uploader(
    "Importar planilha",
    type=["xlsx", "xlsm"]
)

# =========================================
# PROCESSAMENTO
# =========================================

if arquivo:

    try:

        df = pd.read_excel(
            arquivo,
            sheet_name=0
        )

        df.columns = (
            df.columns
            .astype(str)
            .str.strip()
        )

        df = df.loc[
            :,
            ~df.columns.str.contains(
                "^Unnamed",
                case=False
            )
        ]

        df = df.dropna(
            how="all"
        )

        df.to_excel(
            "dados.xlsx",
            index=False,
            engine="openpyxl"
        )

        horario_brasilia = datetime.now(
            ZoneInfo("America/Sao_Paulo")
        ).strftime("%d/%m/%Y %H:%M:%S")

        with open("ultima_atualizacao.json", "w") as f:

            json.dump(
                {
                    "horario": horario_brasilia
                },
                f
            )

        st.success("✅ Planilha carregada!")

        df_existente = df

    except Exception as e:

        st.error(f"Erro ao ler planilha: {e}")

# =========================================
# FILTROS
# =========================================

if df_existente is not None:

    filtros = {}

    if "Rota" in df_existente.columns:

        rotas = sorted(
            df_existente["Rota"]
            .dropna()
            .astype(str)
            .unique()
        )

        rotas_selecionadas = st.multiselect(
            "Rotas prioritárias",
            rotas
        )

        if rotas_selecionadas:

            filtros["rotas"] = rotas_selecionadas

    if "Previsão" in df_existente.columns:

        df_existente["Previsão"] = pd.to_datetime(
            df_existente["Previsão"],
            errors="coerce",
            dayfirst=True
        )

        df_existente = df_existente.dropna(
            subset=["Previsão"]
        )

        if not df_existente.empty:

            min_date = df_existente["Previsão"].min().date()
            max_date = df_existente["Previsão"].max().date()

            start_date = st.date_input(
                "Data inicial",
                value=min_date,
                format="DD/MM/YYYY"
            )

            end_date = st.date_input(
                "Data final",
                value=max_date,
                format="DD/MM/YYYY"
            )

            filtros["start_date"] = str(start_date)
            filtros["end_date"] = str(end_date)

    if "PC" in df_existente.columns:

        pcs = sorted(
            df_existente["PC"]
            .dropna()
            .astype(str)
            .unique()
        )

        pcs_selecionados = st.multiselect(
            "Programação de carga",
            pcs
        )

        if pcs_selecionados:

            filtros["pcs"] = pcs_selecionados

    if st.button("💾 Salvar filtros"):

        with open("filtros.json", "w") as f:

            json.dump(
                [filtros],
                f
            )

        st.success("✅ Filtros salvos!")

    st.subheader("📋 Base Atual")

    st.dataframe(
        df_existente,
        use_container_width=True,
        height=400
    )

    st.subheader("📥 Exportar dados")

    def to_excel(df):

        output = BytesIO()

        with pd.ExcelWriter(
            output,
            engine="openpyxl"
        ) as writer:

            df.to_excel(
                writer,
                index=False,
                sheet_name="Base"
            )

        return output.getvalue()

    excel_file = to_excel(df_existente)

    st.download_button(
        label="Baixar Excel",
        data=excel_file,
        file_name="dados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
