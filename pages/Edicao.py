import streamlit as st
import pandas as pd

st.set_page_config(page_title="Pedidos Em Aberto - Edição", page_icon="🔑", layout="wide")
st.title("🔑 Página de Edição")

# Campo de senha
senha = st.text_input("Digite a senha para acessar:", type="password")

if senha == "1911":  # troque pela sua senha
    arquivo = st.file_uploader("Importar planilha", type=["xlsx"])
    if arquivo:
        df = pd.read_excel(arquivo, sheet_name="Base")
        df.to_excel("dados.xlsx", index=False)  # salva para o Viewer
        st.success("✅ Planilha carregada e salva!")
        st.dataframe(df)
else:
    st.warning("⚠️ Acesso restrito. Digite a senha correta.")

