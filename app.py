import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. Configuração Inicial da Página
st.set_page_config(
    page_title="Nutribook AI — Portal do Consultório",
    page_icon="🍎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Estilização CSS Personalizada (Verde Nutri + Sálvia)
st.markdown("""
    <style>
    /* Estilo do Fundo e Aplicação Geral */
    .stApp {
        background-color: #F3F6F3 !important;
    }

    /* Botões Principais */
    div.stButton > button, div.stFormSubmitButton > button {
        background-color: #2A5C36 !important;
        color: #FFFFFF !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 10px 24px !important;
        transition: all 0.3s ease !important;
        width: 100%;
    }
    
    div.stButton > button:hover, div.stFormSubmitButton > button:hover {
        background-color: #1E4327 !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(42, 92, 54, 0.25) !important;
    }

    /* Títulos principais em tom escuro botânico */
    h1, h2, h3 {
        color: #16281A !important;
        font-weight: 700 !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #E3EAE2 !important;
        border-right: 1px solid #D2DDD0;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Sidebar / Menu Lateral
with st.sidebar:
    st.image("logo.png", width=160)
    st.markdown("## **Nutribook AI**")
    st.caption("Documento Único • Nutrição de Alta Performance")
    
    st.divider()
    
    menu = st.radio(
        "Navegação do Consultório:",
        ["📋 Painel de Solicitações", "➕ Criar Novo Nutribook"],
        index=0
    )

# 4. Conexão com a Planilha Google (Google Sheets)
def carregar_dados():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        return conn.read()
    except Exception as e:
        return None

df_dados = carregar_dados()

# --- ABA 1: PAINEL DE ACOMPANHAMENTO ---
if menu == "📋 Painel de Solicitações":
    st.title("🍎 Painel Nutribook")
    st.write("Acompanhe o status de geração dos PDFs e acesse os links entregues aos pacientes.")
    
    st.divider()
    
    if df_dados is not None and not df_dados.empty:
        col1, col2 = st.columns(2)
        with col1:
            total_concluidos = len(df_dados[df_dados['Status'] == 'Concluído']) if 'Status' in df_dados.columns else 0
            st.metric(label="Nutribooks Concluídos no Mês", value=total_concluidos)
        
        st.write("### **Histórico de Pedidos**")
        st.dataframe(df_dados, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum dado encontrado ou aguardando conexão com o Google Sheets.")

# --- ABA 2: CRIAR NOVO NUTRIBOOK ---
elif menu == "➕ Criar Novo Nutribook":
    st.title("📄 Registro de Consulta")
    st.write("Preencha as informações do paciente e anexe o plano em PDF para disparar a geração.")
    
    with st.form("form_nutribook"):
        st.subheader("Dados do Paciente")
        nome_paciente = st.text_input("Nome Completo do Paciente:")
        perfil_clinico = st.text_area("Anotações da Sessão / Conduta Clinica:", help="Orientações e perfil do paciente que a IA deve considerar.")
        
        st.subheader("Plano Alimentar")
        pdf_file = st.file_uploader("Upload do Arquivo PDF:", type=["pdf"])
        
        submitted = st.form_submit_button("CRIAR NUTRIBOOK")
        
        if submitted:
            if nome_paciente and pdf_file:
                st.success(f"Solicitação criada com sucesso para **{nome_paciente}**! O Nutribook está sendo processado.")
            else:
                st.error("Por favor, preencha o nome do paciente e faça o upload do arquivo PDF.")
