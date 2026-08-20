import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. Configuração Inicial da Página
st.set_page_config(
    page_title="Nutribook — Portal do Consultório",
    page_icon="🍎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Estilização CSS Personalizada (Tom Verde Sálvia Aconchegante)
st.markdown("""
    <style>
    /* Cor de fundo geral */
    .stApp {
        background-color: #E2E8E2 !important;
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

    /* Títulos principais em tom verde escuro */
    h1, h2, h3 {
        color: #112214 !important;
        font-weight: 700 !important;
    }

    /* Estilo da barra lateral */
    [data-testid="stSidebar"] {
        background-color: #D3DDD3 !important;
        border-right: 1px solid #C1CDC1;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Sidebar / Menu Lateral
with st.sidebar:
    st.image("logo.png", width=160)
    
    # Mensagem de Boas-vindas Personalizada
    nome_nutri = "Jean Victor"  # Pode vir de uma autenticação/parâmetro no futuro
    st.markdown(f"#### Olá, **{nome_nutri}**! 👋")
    st.caption("Vamos iniciar o próximo Nutribook?")
    
    st.divider()
    
    menu = st.radio(
        "Navegação do Consultório:",
        ["➕ Novo Nutribook", "📋 Painel Nutribook"],
        index=0
    )

# 4. Conexão com o Google Sheets
def carregar_dados():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        return conn.read()
    except Exception as e:
        return None

df_dados = carregar_dados()

# --- ABA 1: NOVO NUTRIBOOK ---
if menu == "➕ Novo Nutribook":
    st.title("📄 Novo Nutribook")
    st.write("Preencha as informações do paciente e anexe o plano em PDF para disparar a geração.")
    
    with st.form("form_nutribook"):
        st.subheader("Dados do Paciente")
        col_nome, col_email = st.columns(2)
        with col_nome:
            nome_paciente = st.text_input("Nome do Paciente *")
        with col_email:
            email_paciente = st.text_input("E-mail do Paciente")
        
        st.subheader("Perfis / Protocolos do Paciente")
        st.caption("Marque as opções aplicáveis:")
        
        lista_protocolos = [
            "Fertilidade Feminina",
            "Fertilidade Masculina",
            "FODMAPs Orientações Gerais",
            "FODMAPs Guia e Fases",
            "FODMAPs Tabela Completa",
            "Gestação",
            "Gestação - Diabetes Gestacional",
            "Histamina - Tabela",
            "Lactante",
            "Niquel",
            "Referência Geral"
        ]
        
        protocolos_selecionados = []
        for protocolo in lista_protocolos:
            if st.checkbox(protocolo, key=protocolo):
                protocolos_selecionados.append(protocolo)
        
        st.subheader("Plano Alimentar Base")
        pdf_file = st.file_uploader("Upload do Plano Alimentar Base (PDF):", type=["pdf"])
        
        submitted = st.form_submit_button("CRIAR NUTRIBOOK")
        
        if submitted:
            if nome_paciente and pdf_file:
                st.success(f"Solicitação criada com sucesso para **{nome_paciente}**! Protocolos selecionados: {len(protocolos_selecionados)}.")
            else:
                st.error("Por favor, preencha o Nome do Paciente e faça o upload do arquivo PDF.")

# --- ABA 2: PAINEL NUTRIBOOK ---
elif menu == "📋 Painel Nutribook":
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
