import streamlit as st
import requests
import base64
import pandas as pd
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

link_logo = "https://github.com/ArthurModesto1/fre-itens/raw/main/logo.png"
link_logo_curta = "https://github.com/ArthurModesto1/fre-itens/raw/main/logo_curta.png"

st.set_page_config(
   page_title="Visualizador FRE - CVM",
   page_icon=link_logo_curta,
   layout="wide"
)

st.logo(link_logo, icon_image=link_logo_curta)

# -------- CSS PARA CUSTOMIZAR RADIO E TABELAS -------- #
st.markdown("""
<style>
    /* Customização do Radio Button */
    [data-testid="stRadio"] [role="radiogroup"] label {
        background-color: transparent !important;
    }
    [data-testid="stRadio"] div[data-baseweb="radio"] > div:first-child {
        background-color: white !important;
        border: 1px solid white !important;
    }

    /* Estilização das Tabelas HTML */
    .minha-tabela {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        border-radius: 1rem;
        font-size: 0.9rem;
        background-color: #0b2859; 
        overflow: hidden;
        border: 1px solid #10408d;
        margin-bottom: 20px;
    }
    .minha-tabela th {
        background-color: #10408d; 
        text-align: center !important;
        padding: 10px;
        color: white;
        border: none;
    }
    .minha-tabela td {
        padding: 8px;
        text-align: center;
        color: white;
        border-top: 1px solid #10408d;
    }
    .minha-tabela tr:first-child td {
        border-top: none;
    }
    .minha-tabela a {
        color: #4fb3ff !important;
        text-decoration: none;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ---------------- #
st.markdown("""
# 📄 Visualizador de Documentos FRE - CVM
 Ferramenta para consulta rápida de documentos FRE de companhias abertas.
""")
st.markdown("---")

# URLs dos arquivos
CSV_URL = "https://github.com/ArthurModesto1/fre-itens/raw/main/fre_cia_aberta_2025.csv"
PLANOS_URL = "https://github.com/ArthurModesto1/fre-itens/raw/main/tabela_consolidada_cvm_otimizado.xlsx"

# Dicionário com as URLs dos arquivos específicos para download
DOWNLOAD_FILES = {
   "8.2": "https://github.com/ArthurModesto1/fre-itens/raw/main/fre_cia_aberta_remuneracao_total_orgao_2025.csv",
   "8.3": "https://github.com/ArthurModesto1/fre-itens/raw/main/fre_cia_aberta_remuneracao_variavel_2025.csv",
   "8.5": "https://github.com/ArthurModesto1/fre-itens/raw/main/fre_cia_aberta_remuneracao_acao_2025.csv",
   "8.11": "https://github.com/ArthurModesto1/fre-itens/raw/main/fre_cia_aberta_acao_entregue_2025.csv"
}

# ---------------- LOAD DATA ---------------- #
@st.cache_data
def load_data():
   df_fre = pd.read_csv(CSV_URL, sep=';', dtype=str, encoding="latin-1")
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


df, df_planos = load_data()
df = df.sort_values(by=["DENOM_CIA", "VERSAO"], ascending=[True, False])

# Criar conjunto de empresas únicas
empresas_csv = set(df["DENOM_CIA"].dropna())
empresas_excel = set(df_planos["Empresa"].dropna())
empresas_unicas = sorted(empresas_csv | empresas_excel)

# ---------------- SIDEBAR (FILTROS) ---------------- #
with st.sidebar:
   st.header("🔎 Filtros")

   selected_company = st.selectbox(
       "Selecione a empresa",
       empresas_unicas
   )

   lista_itens = ["8.1","8.2","8.3","8.4","8.5","8.6","8.7","8.8","8.9","8.10","8.11","8.12"]

   selected_item = st.radio(
       "Selecione o item do FRE",
       lista_itens
   )

# ---------------- RESULTADOS ---------------- #
df_filtered = df[df["DENOM_CIA"] == selected_company]

st.subheader(f"🏢 Empresa selecionada: {selected_company}")

col1, col2 = st.columns([3,1])

with col1:
   st.write(f"Item selecionado: **{selected_item}**")

# --- LÓGICA DE DOWNLOAD FILTRADO ---
if selected_item in DOWNLOAD_FILES:
   st.info(f"📥 O item {selected_item} permite o download dos dados filtrados.")

   try:
       df_download = pd.read_csv(DOWNLOAD_FILES[selected_item], sep=';', encoding="latin-1", dtype=str)
       col_name = "Nome_Companhia"
       df_download[col_name] = df_download[col_name].str.upper().str.strip()
       df_filtered_dl = df_download[df_download[col_name].str.contains(selected_company, na=False)]

       if not df_filtered_dl.empty:
           csv_bytes = df_filtered_dl.to_csv(index=False, sep=';', encoding="latin-1").encode("latin-1")

           col1_dl, col2_dl = st.columns([1,3])

           with col1_dl:
               st.download_button(
                   label="💾 Baixar CSV",
                   data=csv_bytes,
                   file_name=f"item_{selected_item}_{selected_company}.csv",
                   mime="text/csv"
               )

           st.markdown("### 📊 Prévia dos dados")
           
           html_previa = df_filtered_dl.head(5).to_html(index=False, classes='minha-tabela', escape=False)
           
           st.write(html_previa, unsafe_allow_html=True)

       else:
           st.warning("Nenhum dado encontrado.")

   except Exception as e:
       st.error(f"Erro ao processar download: {e}")

# ---------------- DOCUMENT VIEW ---------------- #
else:
   document_url = df_filtered.iloc[0]["LINK_DOC"] if not df_filtered.empty else None

   def extract_document_number(url):
       if pd.isna(url):
           return None
       parsed_url = urlparse(url)
       query_params = parse_qs(parsed_url.query)
       return query_params.get("NumeroSequencialDocumento", [None])[0]

   def generate_fre_url(doc_number, item):
       mapeamento_quadros = {
           "8.1":"8030",
           "8.4":"8120",
           "8.6":"8180",
           "8.7":"8210",
           "8.8":"8240",
           "8.9":"8270",
           "8.10":"8300",
           "8.12":"8360"
       }
       codigo_quadro = mapeamento_quadros.get(item,"8030")
       return f"https://www.rad.cvm.gov.br/ENET/frmExibirArquivoFRE.aspx?NumeroSequencialDocumento={doc_number}&CodigoGrupo=8000&CodigoQuadro={codigo_quadro}"

   if document_url:
       document_number = extract_document_number(document_url)
       if document_number:
           fre_url = generate_fre_url(document_number, selected_item)
           st.markdown("### 📄 Documento FRE")
           st.link_button(
               "🔗 Abrir documento na CVM",
               fre_url
           )
       else:
           st.warning("Documento não encontrado.")

# ---------------- PLANOS ---------------- #
planos_empresa = df_planos[df_planos["Empresa"] == selected_company]

st.markdown("---")
st.subheader("📋 Planos de Remuneração")

if not planos_empresa.empty:
   planos_empresa["Link"] = planos_empresa["Link"].apply(
       lambda x: f'<a href="{x}" target="_blank">Abrir Documento</a>'
   )

   st.write(
       planos_empresa.to_html(
           escape=False,
           index=False,
           justify="center",
           classes='minha-tabela'
       ),
       unsafe_allow_html=True
   )
else:
   st.info("Nenhum plano encontrado para esta empresa.")

# ---------------- FOOTER ---------------- #
st.markdown("---")
st.caption(
"""
Sistema de consulta de documentos FRE da CVM  
Desenvolvido para análise de remuneração executiva
"""
)
