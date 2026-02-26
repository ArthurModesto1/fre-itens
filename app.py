import streamlit as st
import requests
import base64
import pandas as pd
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

st.title("📄 Visualizador de Documentos FRE - CVM")

# URLs dos arquivos CSV e Excel (versões otimizadas no GitHub)
CSV_URL = "https://github.com/ArthurModesto1/fre-itens/raw/main/fre_cia_aberta_2025.csv"
PLANOS_URL = "https://github.com/ArthurModesto1/fre-itens/raw/main/tabela_consolidada_cvm_otimizado.xlsx"

# Dicionário com as URLs dos arquivos específicos para download
DOWNLOAD_FILES = {
    "8.3": "https://github.com/ArthurModesto1/fre-itens/raw/main/fre_cia_aberta_remuneracao_variavel_2025.csv",
    "8.5": "https://github.com/ArthurModesto1/fre-itens/raw/main/fre_cia_aberta_remuneracao_acao_2025.csv",
    "8.11": "https://github.com/ArthurModesto1/fre-itens/raw/main/fre_cia_aberta_acao_entregue_2025.csv"
}

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

    lista_itens = ["8.1", "8.3", "8.4", "8.5", "8.6", "8.7", "8.8", "8.9", "8.10", "8.11", "8.12"]
    selected_item = st.radio("📑 Selecione o item", lista_itens, horizontal=True)

    # --- LÓGICA DE DOWNLOAD FILTRADO (8.3, 8.5, 8.11) ---
    if selected_item in DOWNLOAD_FILES:
        st.info(f"📥 O item {selected_item} permite o download dos dados brutos filtrados.")
        
        try:
            # Carrega o CSV específico do item
            df_download = pd.read_csv(DOWNLOAD_FILES[selected_item], sep=';', encoding="latin-1",
