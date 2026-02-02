import streamlit as st
import requests
import pandas as pd
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

st.set_page_config(layout="wide")
st.title("📄 Visualizador de Documentos FRE – CVM")

CSV_URL = "https://github.com/tovarich86/FRE-8.1/raw/main/fre_cia_aberta_2025.csv"
PLANOS_URL = "https://github.com/tovarich86/FRE-8.1/raw/main/tabela_consolidada_cvm_otimizado.xlsx"

@st.cache_data
def load_data():
    df_fre = pd.read_csv(CSV_URL, sep=";", dtype=str, encoding="latin-1")
    df_planos = pd.read_excel(PLANOS_URL, dtype=str)

    def normalize_company_name(name):
        if pd.isna(name):
            return None
        name = name.upper().strip()
        name = re.sub(r"\s+(S\.?A\.?|S/A|SA)$", " S.A.", name)
        return name

    df_fre["DENOM_CIA"] = df_fre["DENOM_CIA"].apply(normalize_company_name)
    df_planos["Empresa"] = df_planos["Empresa"].apply(normalize_company_name)

    return df_fre, df_planos

@st.cache_data
def extract_document_number(url):
    if pd.isna(url):
        return None
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    return params.get("NumeroSequencialDocumento", [None])[0]

@st.cache_data
def get_fre_items(numero_documento):
    """
    Busca no índice do FRE quais itens existem
    e seus respectivos CodigoQuadro reais
    """
    url = (
        "https://www.rad.cvm.gov.br/ENET/frmConsultaFRE.aspx"
        f"?NumeroSequencialDocumento={numero_documento}"
    )

    response = requests.get(url, timeout=15)
    soup = BeautifulSoup(response.text, "html.parser")

    itens = {}

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if "frmExibirArquivoFRE.aspx" in href:
            parsed = urlparse(href)
            params = parse_qs(parsed.query)

            codigo_quadro = params.get("CodigoQuadro", [None])[0]
            texto = a.get_text(strip=True)

            # Captura apenas itens do capítulo 8
            match = re.match(r"(8\.\d+)", texto)
            if match and codigo_quadro:
                item = match.group(1)
                itens[item] = codigo_quadro

    return itens

def generate_fre_url(numero_documento, codigo_quadro):
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

with st.spinner("Consultando itens reais do FRE na CVM..."):
    itens_fre = get_fre_items(numero_doc)

if not itens_fre:
    st.warning("Nenhum item do capítulo 8 encontrado.")
    st.stop()

item_selecionado = st.selectbox(
    "📑 Selecione o item FRE (capítulo 8)",
    sorted(itens_fre.keys(), key=lambda x: float(x.replace(".", "")))
)

codigo_quadro = itens_fre[item_selecionado]
fre_url = generate_fre_url(numero_doc, codigo_quadro)

st.success(f"Item {item_selecionado} encontrado no FRE")
st.write(f"[🔗 Abrir documento FRE – Item {item_selecionado}]({fre_url})")

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
