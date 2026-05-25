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

st.success("✅ Acesso liberado.")

# =========================================
# FUNÇÃO INTELIGENTE
# =========================================

def encontrar_base_excel(arquivo):

    excel = pd.ExcelFile(arquivo)

    palavras_chave = [
        "pedido",
        "rota",
        "produto",
        "cliente",
        "previs",
        "pc"
    ]

    for aba in excel.sheet_names:

        try:

            for linha in range(15):

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
                    teste.columns
                    .astype(str)
                    .str.lower()
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
# MOSTRAR BASE ATUAL
# =========================================

df_existente = None

try:

    df_existente = pd.read_excel(
        "dados.xlsx",
        sheet_name="Base"
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

        df, aba, linha = encontrar_base_excel(arquivo)

        if df is None:

            st.error(
                "❌ Não foi possível localizar a base automaticamente."
            )

            st.stop()

        # =========================================
        # LIMPEZA
        # =========================================

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

        # =========================================
        # MOSTRA INFORMAÇÕES
        # =========================================

        st.success(
            f"✅ Base encontrada | Aba: {aba} | Linha do cabeçalho: {linha + 1}"
        )

        st.write("Quantidade de linhas:", len(df))
        st.write("Quantidade de colunas:", len(df.columns))

        st.write("Colunas encontradas:")
        st.write(df.columns.tolist())

        # =========================================
        # SALVAR BASE
        # =========================================

        with pd.ExcelWriter(
            "dados.xlsx",
            engine="openpyxl"
        ) as writer:

            df.to_excel(
                writer,
                index=False,
                sheet_name="Base"
            )

        # =========================================
        # SALVAR DATA ATUALIZAÇÃO
        # =========================================

        horario_brasilia = datetime.now(
            ZoneInfo("America/Sao_Paulo")
        ).strftime("%d/%m/%Y %H:%M:%S")

        with open(
            "ultima_atualizacao.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                {
                    "horario": horario_brasilia
                },
                f,
                ensure_ascii=False
            )

        st.success("✅ Planilha carregada com sucesso!")

        df_existente = df

    except Exception as e:

        st.error(f"Erro ao processar planilha: {e}")

# =========================================
# EXIBIR BASE
# =========================================

if df_existente is not None:

    st.subheader("📋 Base Atual")

    st.dataframe(
        df_existente,
        use_container_width=True,
        height=500
    )

    # =========================================
    # DOWNLOAD
    # =========================================

    st.subheader("📥 Exportar Base")

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
        label="Baixar dados.xlsx",
        data=excel_file,
        file_name="dados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
