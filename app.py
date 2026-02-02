import streamlit as st
import requests
import base64
import pandas as pd
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

st.title("📄 Visualizador de Documentos FRE - CVM")

# URLs dos arquivos CSV e Excel (versões otimizadas no GitHub)
CSV_URL = "https://github.com/tovarich86/FRE-8.1/raw/main/fre_cia_aberta_2025.csv"
PLANOS_URL = "https://github.com/tovarich86/FRE-8.1/raw/main/tabela_consolidada_cvm_otimizado.xlsx"

@st.cache_data
def load_data():
    """Carrega os dados otimizados do CSV e do Excel"""
    df_fre = pd.read_csv(CSV_URL, sep=';', dtype=str, encoding="latin-1")
    df_planos = pd.read_excel(PLANOS_URL, dtype=str)
    
    # Função para padronizar nomes de empresas
    def normalize_company_name(name):
        if pd.isna(name):
            return None
        name = name.upper().strip()
        # Padronizar todas as variações de S.A., S.A, S/A, SA para "S.A."
        name = re.sub(r"\s+(S\.?A\.?|S/A|SA)$", " S.A.", name)
        return name
    
    df_fre["DENOM_CIA"] = df_fre["DENOM_CIA"].apply(normalize_company_name)
    df_planos["Empresa"] = df_planos["Empresa"].apply(normalize_company_name)
    
    return df_fre, df_planos

df, df_planos = load_data()
df = df.sort_values(by=["DENOM_CIA", "VERSAO"], ascending=[True, False])

# Criar conjunto de empresas únicas
empresas_csv = set(df["DENOM_CIA"].dropna())
empresas_excel = set(df_planos["Empresa"].dropna())
empresas_unicas = sorted(empresas_csv | empresas_excel)

if empresas_unicas:
    selected_company = st.selectbox("🏢 Selecione a empresa", empresas_unicas)
    df_filtered = df[df["DENOM_CIA"] == selected_company]

    lista_itens = ["8.1", "8.2", "8.4", "8.5", "8.6", "8.7", "8.8", "8.9", "8.10", "8.11", "8.12"]
    selected_item = st.radio("📑 Selecione o item", lista_itens, horizontal=True)
    
    document_url = df_filtered.iloc[0]["LINK_DOC"] if not df_filtered.empty else None
    
    def extract_document_number(url):
        """Extrai o número sequencial do documento da URL"""
        if pd.isna(url):
            return None
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        return query_params.get("NumeroSequencialDocumento", [None])[0]
    
    def generate_fre_url(doc_number, item):
        """Gera a URL do documento FRE com mapeamento de quadros"""
        mapeamento_quadros = {
            "8.1": "8030",
            "8.2": "8040",
            "8.4": "8120",
            "8.5": "8130",
            "8.6": "8140",
            "8.7": "8150",
            "8.8": "8160",
            "8.9": "8170",
            "8.10": "8180",
            "8.11": "8190",
            "8.12": "8200"
        }
        codigo_quadro = mapeamento_quadros.get(item, "8030")
        return f"https://www.rad.cvm.gov.br/ENET/frmExibirArquivoFRE.aspx?NumeroSequencialDocumento={doc_number}&CodigoGrupo=8000&CodigoQuadro={codigo_quadro}"
    
    if document_url:
        document_number = extract_document_number(document_url)
        if document_number:
            fre_url = generate_fre_url(document_number, selected_item)
            
            st.write(f"### 📄 Documento FRE da {selected_company} - Item {selected_item}")
            st.write(f"[🔗 Abrir documento em uma nova aba]({fre_url})")
        else:
            st.warning("⚠️ Documento não encontrado para esta empresa.")
    
    # Verificar se a empresa possui planos e exibir ao final
    planos_empresa = df_planos[df_planos["Empresa"] == selected_company]
    if not planos_empresa.empty:
        st.write("---")
        st.write("📋 **Planos de Remuneração encontrados:**")
        
        # Transformar o link em hyperlink
        planos_empresa["Link"] = planos_empresa["Link"].apply(lambda x: f'<a href="{x}" target="_blank">Abrir Documento</a>')
        
        st.write(planos_empresa.to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        st.write("❌ Nenhum plano de remuneração encontrado para esta empresa.")
