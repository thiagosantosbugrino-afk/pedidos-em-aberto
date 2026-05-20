import streamlit as st
import pandas as pd

st.set_page_config(page_title="Pedidos Em Aberto - Edição", page_icon="🔑", layout="wide")
st.title("🔑 Página de Edição")

# Campo de senha
senha = st.text_input("Digite a senha para acessar:", type="password")

if senha == "1911":  # troque pela sua senha
    # Inicializa flag de sessão
    if "planilha_carregada" not in st.session_state:
        st.session_state["planilha_carregada"] = False

    # Upload da planilha
    arquivo = st.file_uploader("Importar planilha", type=["xlsx"])

    # Se o usuário fizer upload e ainda não tiver carregado
    if arquivo and not st.session_state["planilha_carregada"]:
        try:
            df = pd.read_excel(arquivo, sheet_name="Base")  # garante aba Base
            df.to_excel("dados.xlsx", index=False)          # salva para o Viewer
            st.session_state["planilha_carregada"] = True
            st.success("✅ Planilha carregada e salva!")
        except Exception as e:
            st.error(f"Erro ao ler a planilha: {e}")

    # Se já foi carregada, mostra os dados direto
    if st.session_state["planilha_carregada"]:
        try:
            df = pd.read_excel("dados.xlsx", sheet_name="Base")
            st.dataframe(df)
        except Exception as e:
            st.error(f"Erro ao abrir dados salvos: {e}")
else:
    st.warning("⚠️ Acesso restrito. Digite a senha correta.")
