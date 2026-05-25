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
# CARREGAR BASE JÁ EXISTENTE
# =========================================

df = None

try:

    df = pd.read_excel(
        "dados.xlsx",
        sheet_name=0
    )

    st.success("✅ Base já carregada encontrada.")

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
# PROCESSAMENTO DO UPLOAD
# =========================================

if arquivo:

    try:

        # =========================================
        # LEITURA AUTOMÁTICA
        # =========================================

        novo_df, aba_encontrada, linha_encontrada = encontrar_base_excel(arquivo)

        if novo_df is None:

            st.error(
                "❌ Não foi possível encontrar automaticamente a base da planilha."
            )

            st.stop()

        # =========================================
        # LIMPEZA COLUNAS
        # =========================================

        novo_df.columns = (
            novo_df.columns
            .astype(str)
            .str.strip()
        )

        # REMOVE COLUNAS UNNAMED
        novo_df = novo_df.loc[
            :,
            ~novo_df.columns.str.contains(
                "^Unnamed",
                case=False
            )
        ]

        # REMOVE LINHAS TOTALMENTE VAZIAS
        novo_df = novo_df.dropna(
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

        novo_df.to_excel(
            "dados.xlsx",
            index=False,
            engine="openpyxl"
        )

        st.success("✅ Planilha carregada e salva!")

        # Atualiza df principal
        df = novo_df

    except Exception as e:

        st.error(f"Erro ao ler a planilha: {e}")

# =========================================
# VERIFICA SE TEM BASE
# =========================================

if df is None:

    st.warning("⚠️ Nenhuma base carregada ainda.")
    st.stop()

# =========================================
# CARREGAR FILTROS SALVOS
# =========================================

filtros = {}

try:

    with open("filtros.json", "r") as f:

        filtros = json.load(f)[0]

except:

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
        rotas,
        default=filtros.get("rotas", [])
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
            value=pd.to_datetime(
                filtros.get("start_date", min_date)
            ).date(),
            min_value=min_date,
            max_value=max_date,
            format="DD/MM/YYYY"
        )

        end_date = st.date_input(
            "Data final",
            value=pd.to_datetime(
                filtros.get("end_date", max_date)
            ).date(),
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
        pcs,
        default=filtros.get("pcs", [])
    )

    if pcs_selecionados:

        filtros["pcs"] = pcs_selecionados

# =========================================
# BOTÃO SALVAR FILTROS
# =========================================

if st.button("💾 Salvar filtros"):

    with open("filtros.json", "w") as f:

        json.dump(
            [filtros],
            f
        )

    st.success("✅ Filtros salvos com sucesso!")

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

# =========================================
# MOSTRAR BASE ATUAL
# =========================================

st.subheader("📋 Base Atual")

st.dataframe(
    df,
    use_container_width=True,
    height=400
)
