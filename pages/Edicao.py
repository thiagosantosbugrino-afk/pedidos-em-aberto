import streamlit as st
import pandas as pd

st.set_page_config(page_title="Pedidos Em Aberto - Edição", page_icon="🔑", layout="wide")
st.title("🔑 Página de Edição")

# Campo de senha
senha = st.text_input("Digite a senha para acessar:", type="password")

if senha == "Thiago2026!":  # 🔹 aqui você define sua senha
    arquivo = st.file_uploader("Importar planilha", type=["xlsx"])

    if arquivo:
        try:
            df = pd.read_excel(arquivo, sheet_name=0)  # lê sempre a primeira aba
            df.to_excel("dados.xlsx", index=False)     # sobrescreve sempre
            st.success("✅ Planilha carregada e salva!")

            # 🔹 Selecionar rotas prioritárias
            if "Rota" in df.columns:
                rotas = sorted(df["Rota"].dropna().astype(str).unique())
                rotas_selecionadas = st.multiselect("Selecione as rotas prioritárias:", rotas)

                if rotas_selecionadas:
                    pd.Series(rotas_selecionadas).to_csv("rotas_prioritarias.csv", index=False)
                    st.success("✅ Rotas prioritárias salvas!")
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
