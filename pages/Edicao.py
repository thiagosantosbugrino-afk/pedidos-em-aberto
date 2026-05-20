import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Pedidos Em Aberto - Edição", page_icon="🔑", layout="wide")
st.title("🔑 Página de Edição")

senha = st.text_input("Digite a senha para acessar:", type="password")

if senha == "Thiago2026!":  # 🔹 sua senha
    arquivo = st.file_uploader("Importar planilha", type=["xlsx"])

    if arquivo:
        try:
            df = pd.read_excel(arquivo, sheet_name=0)
            df.to_excel("dados.xlsx", index=False)
            st.success("✅ Planilha carregada e salva!")

            filtros = {}

            # Selecionar rotas prioritárias
            if "Rota" in df.columns:
                rotas = sorted(df["Rota"].dropna().astype(str).unique())
                rotas_selecionadas = st.multiselect("Selecione as rotas prioritárias:", rotas)
                if rotas_selecionadas:
                    filtros["rotas"] = rotas_selecionadas

            # Selecionar período de datas
            if "Previsão" in df.columns:
                df["Previsão"] = pd.to_datetime(df["Previsão"], errors="coerce", dayfirst=True)
                df = df.dropna(subset=["Previsão"])
                if not df.empty:
                    min_date = df["Previsão"].min().date()
                    max_date = df["Previsão"].max().date()
                    start_date = st.date_input("Data inicial", value=min_date, min_value=min_date, max_value=max_date, format="DD/MM/YYYY")
                    end_date = st.date_input("Data final", value=max_date, min_value=min_date, max_value=max_date, format="DD/MM/YYYY")
                    filtros["start_date"] = str(start_date)
                    filtros["end_date"] = str(end_date)

            # Salva filtros escolhidos
            if filtros:
                pd.DataFrame([filtros]).to_json("filtros.json", orient="records")
                st.success("✅ Filtros salvos (rotas e datas)!")

            # ===================================
            # DOWNLOAD DA PLANILHA FILTRADA
            # ===================================
            st.subheader("📥 Exportar dados filtrados")

            def to_excel(df):
                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="Base Filtrada")
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

    # Mostra dados já salvos
    try:
        df = pd.read_excel("dados.xlsx", sheet_name=0)
        st.dataframe(df)
    except Exception:
        st.info("Nenhuma planilha carregada ainda.")
else:
    st.warning("⚠️ Acesso restrito. Digite a senha correta.")
