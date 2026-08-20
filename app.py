import streamlit as st
import pandas as pd
import io
from streamlit_gsheets import GSheetsConnection
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# ID da pasta de entrada para upload dos PDFs base (mesmo ID definido no seu Apps Script)
PASTA_ENTRADAS_ID = '11Pv3PC3X6LpCj4Lg4W1-M7x6KEYERIjBiTSbUyZbxnkvFWHF4nk8Q5KWiOpX7c9NibA2pssC'

# =================================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E CSS (REMOCIONAL DE ESPAÇO NO TOPO)
# =================================================================================
st.set_page_config(
    page_title="Nutribook — Portal do Consultório",
    page_icon="🍎",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* Cor de fundo principal */
    .stApp {
        background-color: #E2E8E2 !important;
    }

    /* Remove o espaço em branco gigante do topo */
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 1.5rem !important;
    }
    
    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }

    [data-testid="stSidebarContent"] {
        padding-top: 1rem !important;
    }

    /* Botão Principal */
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

    /* Títulos e Tipografia */
    h1, h2, h3 {
        color: #112214 !important;
        font-weight: 700 !important;
    }

    /* Barra Lateral */
    [data-testid="stSidebar"] {
        background-color: #D3DDD3 !important;
        border-right: 1px solid #C1CDC1;
    }
    </style>
""", unsafe_allow_html=True)

# =================================================================================
# 2. FUNÇÕES DE INTEGRAÇÃO (GOOGLE DRIVE & SHEETS)
# =================================================================================

def upload_pdf_para_google_drive(uploaded_file, folder_id):
    """Envia o arquivo PDF diretamente para a pasta do Google Drive."""
    try:
        creds_dict = dict(st.secrets["connections"]["gsheets"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        scopes = ["https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        service = build('drive', 'v3', credentials=creds)

        file_metadata = {
            'name': uploaded_file.name,
            'parents': [folder_id]
        }
        
        media = MediaIoBaseUpload(
            io.BytesIO(uploaded_file.getvalue()),
            mimetype='application/pdf',
            resumable=True
        )
        
        arquivo_drive = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        return arquivo_drive.get('webViewLink')
    except Exception as e:
        st.error(f"Erro ao fazer upload do arquivo para o Google Drive: {e}")
        return None

# Conexão com o Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados_planilha():
    try:
        return conn.read(ttl=0)
    except Exception:
        return None

# =================================================================================
# 3. SIDEBAR / NAV
# =================================================================================
with st.sidebar:
    st.image("logo.png", width=160)
    
    nome_nutri = "Jean Victor"
    st.markdown(f"#### Olá, **{nome_nutri}**! 👋")
    st.caption("Vamos iniciar o próximo Nutribook?")
    
    st.divider()
    
    menu = st.radio(
        "Navegação do Consultório:",
        ["➕ Novo Nutribook", "📋 Painel Nutribook"],
        index=0
    )

# =================================================================================
# 4. CONTEÚDO PRINCIPAL
# =================================================================================

# --- ABA 1: NOVO NUTRIBOOK ---
if menu == "➕ Novo Nutribook":
    st.title("📄 Novo Nutribook")
    st.write("Preencha as informações do paciente e anexe o plano em PDF para disparar a geração.")
    
    with st.form("form_nutribook", clear_on_submit=True):
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
                with st.spinner("Enviando arquivo e registrando pedido..."):
                    # 1. Faz upload do PDF para o Google Drive
                    drive_url = upload_pdf_para_google_drive(pdf_file, PASTA_ENTRADAS_ID)
                    
                    if drive_url:
                        # 2. Prepara os dados para a planilha
                        data_registro = pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")
                        protocolos_str = ", ".join(protocolos_selecionados) if protocolos_selecionados else "Padrão"
                        
                        novo_registro = pd.DataFrame([{
                            "Carimbo de data/hora": data_registro,
                            "Nome do Paciente": nome_paciente,
                            "E-mail do Paciente": email_paciente,
                            "Perfis / Protocolos": protocolos_str,
                            "Upload do Plano Alimentar Base": drive_url,
                            "Conduta": "",
                            "Link Nutribook": "",
                            "Status": "Pendente"
                        }])
                        
                        # 3. Lê o histórico e concatena a nova linha
                        df_atual = conn.read()
                        if df_atual is not None and not df_atual.empty:
                            df_atualizado = pd.concat([df_atual, novo_registro], ignore_index=True)
                        else:
                            df_atualizado = novo_registro
                        
                        # 4. Atualiza a planilha
                        conn.update(data=df_atualizado)
                        
                        st.success(f"✅ Nutribook para **{nome_paciente}** registrado com sucesso! O robô processará e enviará por e-mail em instantes.")
            else:
                st.error("Por favor, preencha o Nome do Paciente e selecione um arquivo PDF.")

# --- ABA 2: PAINEL NUTRIBOOK ---
elif menu == "📋 Painel Nutribook":
    st.title("🍎 Painel Nutribook")
    st.write("Acompanhe o status de geração dos PDFs e acesse os links entregues aos pacientes.")
    
    st.divider()
    
    df_dados = carregar_dados_planilha()
    
    if df_dados is not None and not df_dados.empty:
        col1, col2 = st.columns(2)
        with col1:
            total_concluidos = len(df_dados[df_dados['Status'] == 'Concluído']) if 'Status' in df_dados.columns else 0
            st.metric(label="Nutribooks Concluídos", value=total_concluidos)
        
        st.write("### **Histórico de Pedidos**")
        st.dataframe(df_dados, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum dado encontrado ou aguardando conexão com o Google Sheets.")
