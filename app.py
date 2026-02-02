import streamlit as st
import pandas as pd
import re
from urllib.parse import urlparse, parse_qs

st.set_page_config(layout="wide")
st.title("📄 Visualizador de Documentos FRE – CVM")

# =========================
# FONTES DE DADOS
# =========================

CSV_URL = "https://github.com/tovarich86/FRE-8.1/raw/main/fre_cia_aberta_2025.csv"
PLANOS_URL = "https://github.com/tovarich86/FRE-8.1/raw/main/tabela_consolidada_cvm_otimizado.xlsx"

# =========================
# CÓDIGOS OFICIAIS FRE 2025
# =========================

FRE_ITEMS = {
    "8.1": "8030",
    "8.2": "8040",
    "8.3": "8050",
    "8.4": "8120",
    "8.5": "8060",
    "8.6": "8070",
    "8.7": "8080",
    "8.8": "8090",
    "8.9": "8100",
    "8.10": "8110",
    "8.11": "8210",
    "8.12": "8220",
}

# =========================
# FUNÇÕES
# =========================

@st.cache_data
def load_data():
    df_fre = pd.read_csv(CSV_URL, sep=";", dtype=str, encoding="latin-1")
    df_planos = pd.read_excel(PLANOS_URL, dtype=str)

    def normalize_company_name(name):
        if pd.isna(name):
            return None
        name = name.upper().strip()
        return re.sub(r"\s+(S\.?A\.?|S/A|SA)$", " S.A.", name)

    df_fre["DENOM_CIA"] = df_fre["DENOM_CIA"].apply(normalize_company_name)
    df_planos["Empresa"] = df_planos["Empresa"].apply(normalize_company_name)

    return df_fre, df_planos


def extract_document_number(url):
    if pd.isna(url):
        return None
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    return params.get("NumeroSequencialDocumento", [None])[0]


def generate_fre_url(numero_documento, item):
    codigo_quadro = FRE_ITEMS.get(item)
    if not codigo_quadro:
        return None

    return (
        "https://www.rad.cvm.gov.br/ENET/frmExibirArquivoFRE.aspx"
        f"?NumeroSequencialDocumento={numero_documento}"
        f"&CodigoGrupo=8000"
        f"&CodigoQuadro={codigo_quadro}"
    )

# =========================
# EXECUÇÃO PRINCIPAL
# =========================

df, df_planos = load_data()
df = df.sort_values(by=["DENOM_CIA", "VERSAO"], ascending=[True, False])

empresas = sorted(
    set(df["DENOM_CIA"].dropna()) | set(df_planos["Empresa"].dropna())
)

if not empresas:
    st.warning("Nenhuma empresa encontrada.")
    st.stop()

empresa = st.selectbox("🏢 Selecione a empresa", empresas)
df_empresa = df[df["DENOM_CIA"] == empresa]

if df_empresa.empty:
    st.warning("Empresa sem FRE disponível.")
    st.stop()

link_doc = df_empresa.iloc[0]["LINK_DOC"]
numero_doc = extract_document_number(link_doc)

if not numero_doc:
    st.warning("Não foi possível extrair o número do documento.")
    st.stop()

item = st.radio(
    "📑 Selecione o item do FRE (Capítulo 8)",
    list(FRE_ITEMS.keys()),
    horizontal=True
)

fre_url = generate_fre_url(numero_doc, item)

st.success(f"Documento FRE – Item {item}")
st.write(f"[🔗 Abrir documento em nova aba]({fre_url})")

# =========================
# PLANOS DE REMUNERAÇÃO
# =========================

planos_empresa = df_planos[df_planos["Empresa"] == empresa]

if not planos_empresa.empty:
    st.write("---")
    st.subheader("📋 Planos de Remuneração")

    planos_empresa = planos_empresa.copy()
    planos_empresa["Link"] = planos_empresa["Link"].apply(
        lambda x: f'<a href="{x}" target="_blank">Abrir Documento</a>'
    )

    st.write(planos_empresa.to_html(escape=False, index=False), unsafe_allow_html=True)
else:
    st.info("Nenhum plano de remuneração encontrado para esta empresa.")
