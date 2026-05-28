import streamlit as st
import pandas as pd
from io import BytesIO
import json
from datetime import datetime

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
# FUNÇÃO ENCONTRAR BASE
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
# UPLOAD
# =========================================

arquivo = st.file_uploader(
    "Importar planilha",
    type=["xlsx", "xlsm"]
)

# =========================================
# SE ENVIAR NOVA PLANILHA
# =========================================

if arquivo is not None:

    try:

        df, aba_encontrada, linha_encontrada = encontrar_base_excel(arquivo)

        if df is None:

            st.error(
                "❌ Não foi possível encontrar automaticamente a base."
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
        # AJUSTE PEDIDO
        # =========================================

        if "Pedido" in df.columns:

            df["Pedido"] = (
                df["Pedido"]
                .astype(str)
                .str.replace(".0", "", regex=False)
                .str.strip()
            )

        # =========================================
        # AJUSTE PC
        # =========================================

        if "PC" in df.columns:

            df["PC"] = (
                df["PC"]
                .astype(str)
                .str.replace(".0", "", regex=False)
                .str.strip()
            )
# =========================================
# TRATAR ROTA EM BRANCO (RETIRA)
# =========================================

if "Rota" in df.columns:

    df["Rota"] = (
        df["Rota"]
        .astype(str)
        .str.strip()
        .replace(["", "nan", "None"], "RETIRA")
    )

        # =========================================
        # SALVAR BASE
        # =========================================
     
        df.to_excel(
            "dados.xlsx",
            index=False,
            engine="openpyxl"
        )

        # =========================================
        # SALVAR DATA UPDATE
        # =========================================

        with open("ultima_atualizacao.json", "w") as f:

            json.dump(
                {
                    "ultima_atualizacao":
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                },
                f
            )

        st.success(
            f"✅ Base encontrada automaticamente | Aba: {aba_encontrada} | Cabeçalho linha: {linha_encontrada + 1}"
        )

        st.success("✅ Planilha carregada e salva!")

    except Exception as e:

        st.error(f"Erro ao ler planilha: {e}")

# =========================================
# CARREGAR BASE SALVA
# =========================================

try:

    df = pd.read_excel(
        "dados.xlsx"
    )

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    # =========================================
    # AJUSTE PEDIDO
    # =========================================

    if "Pedido" in df.columns:

        df["Pedido"] = (
            df["Pedido"]
            .astype(str)
            .str.replace(".0", "", regex=False)
            .str.strip()
        )

    # =========================================
    # AJUSTE PC
    # =========================================

    if "PC" in df.columns:

        df["PC"] = (
            df["PC"]
            .astype(str)
            .str.replace(".0", "", regex=False)
            .str.strip()
        )

except:

    st.warning(
        "⚠️ Nenhuma base carregada ainda."
    )

    st.stop()

# =========================================
# CONVERTE DATA
# =========================================

if "Previsão" in df.columns:

    df["Previsão"] = pd.to_datetime(
        df["Previsão"],
        errors="coerce",
        dayfirst=True
    )

# =========================================
# CARREGAR FILTROS SALVOS
# =========================================

try:

    with open("filtros.json", "r", encoding="utf-8") as f:

        filtros_salvos = json.load(f)[0]

except:

    filtros_salvos = {}

# =========================================
# FILTROS
# =========================================

filtros = {}

st.markdown("---")
st.subheader("🎯 Configuração de Filtros")

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

    rotas_padrao = [
        r for r in filtros_salvos.get("rotas", [])
        if r in rotas
    ]

    rotas_selecionadas = st.multiselect(
        "Selecione as rotas prioritárias:",
        rotas,
        default=rotas_padrao
    )

    filtros["rotas"] = rotas_selecionadas

# =========================================
# FILTRO PRODUTO
# =========================================

if "Produto" in df.columns:

    produtos = sorted(
        df["Produto"]
        .dropna()
        .astype(str)
        .unique()
    )

    produtos_padrao = [
        p for p in filtros_salvos.get("produtos", [])
        if p in produtos
    ]

    produtos_selecionados = st.multiselect(
        "Selecione os produtos:",
        produtos,
        default=produtos_padrao
    )

    filtros["produtos"] = produtos_selecionados

# =========================================
# FILTRO DATA
# =========================================

if "Previsão" in df.columns:

    df_data = df.dropna(
        subset=["Previsão"]
    )

    if not df_data.empty:

        min_date = (
            df_data["Previsão"]
            .min()
            .date()
        )

        max_date = (
            df_data["Previsão"]
            .max()
            .date()
        )

        start_padrao = pd.to_datetime(
            filtros_salvos.get(
                "start_date",
                min_date
            )
        ).date()

        end_padrao = pd.to_datetime(
            filtros_salvos.get(
                "end_date",
                max_date
            )
        ).date()

        col1, col2 = st.columns(2)

        with col1:

            start_date = st.date_input(
                "Data inicial",
                value=start_padrao,
                min_value=min_date,
                max_value=max_date,
                format="DD/MM/YYYY"
            )

        with col2:

            end_date = st.date_input(
                "Data final",
                value=end_padrao,
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

    # GARANTE FORMATO CORRETO
    df["PC"] = (
        df["PC"]
        .astype(str)
        .str.replace(".0", "", regex=False)
        .str.strip()
    )

    pcs = sorted(
        [
            str(p).strip()
            for p in df["PC"]
            .dropna()
            .unique()
        ]
    )

    # FILTROS SALVOS
    pcs_salvos = filtros_salvos.get("pcs", [])

    pcs_salvos = [
        str(p).replace(".0", "").strip()
        for p in pcs_salvos
    ]

    # GARANTE EXISTÊNCIA
    pcs_padrao = [
        p for p in pcs_salvos
        if p in pcs
    ]

    pcs_selecionados = st.multiselect(
        "Programação de carga:",
        pcs,
        default=pcs_padrao
    )

    filtros["pcs"] = [
        str(p).replace(".0", "").strip()
        for p in pcs_selecionados
    ]
# =========================================
# FILTRO ROTA MANUAL (NOVO)
# =========================================

if "Rota" in df.columns:

    # garante padrão
    df["Rota"] = (
        df["Rota"]
        .astype(str)
        .str.strip()
    )

    rotas = sorted(
        df["Rota"]
        .dropna()
        .unique()
    )

    # carrega salvos
    rotas_salvas = filtros_salvos.get("rotas_manuais", [])

    rotas_salvas = [
        str(r).strip()
        for r in rotas_salvas
    ]

    rotas_padrao = [
        r for r in rotas_salvas
        if r in rotas
    ]

    rotas_manuais = st.multiselect(
        "🚚 Rotas manuais (independente da PC):",
        rotas,
        default=rotas_padrao
    )

    filtros["rotas_manuais"] = [
        str(r).strip()
        for r in rotas_manuais
    ]
# =========================================
# PEDIDOS MANUAIS
# =========================================

st.markdown("---")

st.subheader("🔎 Pedidos manuais")

# GARANTE FORMATO
df["Pedido"] = (
    df["Pedido"]
    .astype(str)
    .str.replace(".0", "", regex=False)
    .str.strip()
)

# LISTA PEDIDOS
lista_pedidos = sorted(
    df["Pedido"]
    .dropna()
    .unique()
)

# PEDIDOS SALVOS
pedidos_salvos = filtros_salvos.get(
    "pedidos_manuais",
    []
)

pedidos_salvos = [
    str(p).strip()
    for p in pedidos_salvos
]

# BUSCA
busca_pedido = st.text_input(
    "🔍 Buscar pedido"
)

# FILTRA BUSCA
if busca_pedido:

    pedidos_filtrados = [
        p for p in lista_pedidos
        if busca_pedido.lower() in p.lower()
    ]

else:

    pedidos_filtrados = lista_pedidos

# SELECT
pedidos_manuais = st.multiselect(
    "Selecionar pedidos manuais:",
    pedidos_filtrados,
    default=[
        p for p in pedidos_salvos
        if p in pedidos_filtrados
    ]
)

# SALVA
filtros["pedidos_manuais"] = pedidos_manuais

# MOSTRA 
if pedidos_manuais:

    st.success(
        f"✅ {len(pedidos_manuais)} pedido(s) manual(is) selecionado(s)"
    )

    st.markdown("### 📌 Pedidos selecionados")

    for p in pedidos_manuais:
        st.markdown(
            f"""
            <div style="
                background-color:#f4f6f8;
                padding:6px 10px;
                border-radius:6px;
                margin-bottom:5px;
                font-size:14px;
                border-left:4px solid #4CAF50;
            ">
                🧾 Pedido <b>{p}</b>
            </div>
            """,
            unsafe_allow_html=True
        )
    
# =========================================
# SALVAR FILTROS
# =========================================

if st.button("💾 Salvar filtros"):

    try:

        with open(
            "filtros.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                [filtros],
                f,
                ensure_ascii=False,
                indent=4
            )

        st.success("✅ Filtros salvos com sucesso!")

    except Exception as e:

        st.error(f"Erro ao salvar filtros: {e}")

# =========================================
# MOSTRAR BASE
# =========================================

st.markdown("---")

mostrar_base = st.checkbox(
    "📋 Mostrar Base Atual",
    value=True
)

if mostrar_base:

    st.subheader("📋 Base Atual")

    df_exibir = df.copy()

    if "Previsão" in df_exibir.columns:

        df_exibir["Previsão"] = (
            pd.to_datetime(
                df_exibir["Previsão"],
                errors="coerce"
            )
            .dt.strftime("%d/%m/%Y")
        )

    st.dataframe(
        df_exibir,
        use_container_width=True,
        height=500
    )

# =========================================
# DOWNLOAD
# =========================================

st.markdown("---")

st.subheader("📥 Exportar base")

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

excel_file = to_excel(df)

st.download_button(
    label="Baixar planilha",
    data=excel_file,
    file_name="dados.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
