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

                    return teste

        except:

            pass

    return None

# =========================================
# PROCESSAMENTO NOVO UPLOAD
# =========================================

if arquivo:

    try:

        df_novo = encontrar_base_excel(arquivo)

        if df_novo is None:

            st.error("❌ Não foi possível localizar a base.")
            st.stop()

        df_novo.columns = (
            df_novo.columns
            .astype(str)
            .str.strip()
        )

        df_novo = df_novo.loc[
            :,
            ~df_novo.columns.str.contains("^Unnamed")
        ]

        df_novo = df_novo.dropna(how="all")

        df_novo.to_excel(
            "dados.xlsx",
            index=False,
            engine="openpyxl"
        )

        st.success("✅ Nova planilha salva!")

    except Exception as e:

        st.error(f"Erro ao processar planilha: {e}")

# =========================================
# LER BASE ATUAL
# =========================================

try:

    df = pd.read_excel(
        "dados.xlsx",
        sheet_name=0
    )

except:

    st.warning("⚠️ Nenhuma planilha salva ainda.")
    st.stop()

# =========================================
# CARREGAR FILTROS EXISTENTES
# =========================================

filtros_salvos = {}

try:

    with open("filtros.json", "r") as f:

        filtros_salvos = json.load(f)[0]

except:

    pass

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

    rotas_padrao = filtros_salvos.get("rotas", [])

    rotas_sel = st.multiselect(
        "Rotas prioritárias",
        rotas,
        default=rotas_padrao
    )

    if rotas_sel:

        filtros["rotas"] = rotas_sel

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

    pcs_padrao = filtros_salvos.get("pcs", [])

    pcs_sel = st.multiselect(
        "Programação de carga",
        pcs,
        default=pcs_padrao
    )

    if pcs_sel:

        filtros["pcs"] = pcs_sel

# =========================================
# FILTRO DATA
# =========================================

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

        data_inicial_padrao = min_date
        data_final_padrao = max_date

        if "start_date" in filtros_salvos:

            data_inicial_padrao = pd.to_datetime(
                filtros_salvos["start_date"]
            ).date()

        if "end_date" in filtros_salvos:

            data_final_padrao = pd.to_datetime(
                filtros_salvos["end_date"]
            ).date()

        start_date = st.date_input(
            "Data inicial",
            value=data_inicial_padrao
        )

        end_date = st.date_input(
            "Data final",
            value=data_final_padrao
        )

        filtros["start_date"] = str(start_date)
        filtros["end_date"] = str(end_date)

# =========================================
# SALVAR FILTROS
# =========================================

if st.button("💾 Salvar filtros"):

    with open("filtros.json", "w") as f:

        json.dump(
            [filtros],
            f
        )

    st.success("✅ Filtros salvos!")

# =========================================
# BASE ATUAL
# =========================================

st.subheader("📋 Base Atual")

st.dataframe(
    df,
    use_container_width=True,
    height=400
)
