import streamlit as st
import pandas as pd
import io
from streamlit_gsheets import GSheetsConnection
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# ID da pasta de entrada para upload dos PDFs base
PASTA_ENTRADAS_ID = '1_Bffls1oLxmaIUeQGsPGL0xVTL6CTLqj'

# VALOR UNITÁRIO PARA CÁLCULO DE FATURAMENTO (Ajuste conforme o preço comercializado)
VALOR_NUTRIBOOK = 35.00  

# =================================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E CSS (MARGEM SUPERIOR AJUSTADA)
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

    /* Redução da margem do topo */
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
    """Envia o arquivo PDF para a pasta do Google Drive."""
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
        st.error(f"Erro no upload para o Google Drive: {e}")
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
                    drive_url = upload_pdf_para_google_drive(pdf_file, PASTA_ENTRADAS_ID)
                    
                    if drive_url:
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
                        
                        df_atual = conn.read()
                        if df_atual is not None and not df_atual.empty:
                            df_atualizado = pd.concat([df_atual, novo_registro], ignore_index=True)
                        else:
                            df_atualizado = novo_registro
                        
                        conn.update(data=df_atualizado)
                        st.success(f"✅ Nutribook para **{nome_paciente}** registrado com sucesso!")
            else:
                st.error("Por favor, preencha o Nome do Paciente e selecione um arquivo PDF.")

# --- ABA 2: PAINEL NUTRIBOOK ---
elif menu == "📋 Painel Nutribook":
    st.title("🍎 Painel Nutribook")
    st.write("Acompanhe os indicadores de geração, faturamento e histórico completo.")
    
    st.divider()
    
    df_dados = carregar_dados_planilha()
    
    if df_dados is not None and not df_dados.empty:
        # Mapeamento dinâmico de colunas
        col_status = "Status" if "Status" in df_dados.columns else df_dados.columns[-1]
        col_data = "Carimbo de data/hora" if "Carimbo de data/hora" in df_dados.columns else df_dados.columns[0]
        
        # Tratamento das datas para análise temporal
        df_dados['Data_Parsed'] = pd.to_datetime(df_dados[col_data], dayfirst=True, errors='coerce')
        
        # FILTRO EXCLUSIVO: Apenas registros com status "Concluído"
        df_concluidos = df_dados[df_dados[col_status].astype(str).str.strip().str.lower() == 'concluído']
        
        # Cálculos de Métricas
        total_historico = len(df_concluidos)
        
        agora = pd.Timestamp.now()
        df_mes_atual = df_concluidos[
            (df_concluidos['Data_Parsed'].dt.month == agora.month) & 
            (df_concluidos['Data_Parsed'].dt.year == agora.year)
        ]
        total_mes = len(df_mes_atual)
        
        faturamento_mes = total_mes * VALOR_NUTRIBOOK
        faturamento_total = total_historico * VALOR_NUTRIBOOK

        # Exibição dos KPIs em Cards
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        with kpi1:
            st.metric(label="Total Concluídos (Geral)", value=f"{total_historico}")
        with kpi2:
            st.metric(label="Concluídos no Mês", value=f"{total_mes}")
        with kpi3:
            st.metric(label="Faturamento Mês Atual", value=f"R$ {faturamento_mes:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        with kpi4:
            st.metric(label="Faturamento Acumulado", value=f"R$ {faturamento_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        st.markdown("---")

        # Gráfico Mês a Mês
        st.subheader("📈 Evolução Mensal (Nutribooks Concluídos)")
        if not df_concluidos.empty and df_concluidos['Data_Parsed'].notna().any():
            df_grafico = (
                df_concluidos.dropna(subset=['Data_Parsed'])
                .groupby(df_concluidos['Data_Parsed'].dt.to_period('M'))
                .size()
                .reset_index(name='Quantidade')
            )
            df_grafico['Mês/Ano'] = df_grafico['Data_Parsed'].astype(str)
            df_grafico = df_grafico.set_index('Mês/Ano')[['Quantidade']]
            
            st.bar_chart(df_grafico, height=260)
        else:
            st.caption("Aguardando mais registros concluídos para exibição do gráfico.")

        st.markdown("---")

        # Tabela Detalhada do Histórico
        st.subheader("📋 Histórico de Pedidos")
        
        status_unicos = list(df_dados[col_status].dropna().unique())
        status_filtro = st.selectbox("Filtrar por Status na Tabela:", ["Todos"] + status_unicos)
        
        df_exibicao = df_dados.copy()
        if status_filtro != "Todos":
            df_exibicao = df_exibicao[df_exibicao[col_status] == status_filtro]

        # Oculta colunas auxiliares no painel
        if 'Data_Parsed' in df_exibicao.columns:
            df_exibicao = df_exibicao.drop(columns=['Data_Parsed'])

        st.dataframe(
            df_exibicao,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Link Nutribook": st.column_config.LinkColumn("Link Nutribook", display_text="🔗 Abrir PDF"),
                "Upload do Plano Alimentar Base": st.column_config.LinkColumn("Plano Base", display_text="📄 Ver Base")
            }
        )
    else:
        st.info("Nenhum dado encontrado na planilha do Google Sheets.")
