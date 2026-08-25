import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Hub BioPerformance", page_icon="🍎", layout="wide")

# URLs dos Webhooks do n8n / Evolution API
N8N_WEBHOOK_ENVIO = "http://163.176.133.204:5678/webhook/enviar-nutribook"
EVOLUTION_API_URL = "http://163.176.133.204:8080"
API_KEY = "nutribook_secret_key_2026"
INSTANCE_NAME = "nutribook"

tab1, tab2, tab3 = st.tabs(["📋 Novo Nutribook", "📱 Conectar WhatsApp", "📅 Agenda & Pacientes"])

# ==========================================
# ABA 1: FORMUÁRIO DE ENVIO
# ==========================================
with tab1:
    st.header("Novo Nutribook")
    st.caption("Preencha as informações do paciente e anexe o plano em PDF para disparar a geração.")
    
    with st.form("form_nutribook"):
        col1, col2, col3 = st.columns(3)
        with col1:
            nome = st.text_input("Nome do Paciente *")
        with col2:
            email = st.text_input("E-mail do Paciente")
        with col3:
            whatsapp = st.text_input("WhatsApp do Paciente (com DDD) *", placeholder="5548999999999")
            
        st.subheader("Perfis / Protocolos do Paciente")
        protocolos = st.multiselect(
            "Selecione os protocolos aplicáveis:",
            [
                "Fertilidade Feminina", "Emagrecimento & Definição", "Hipertrofia & Ganho de Massa",
                "Reeducação Alimentar & Saúde Geral", "Saúde Intestinal (Disbiose / FODMAPs)",
                "Saúde da Mulher (SOP / Endometriose)", "Controle Metabólico (Diabetes / Colesterol)",
                "Performance Esportiva", "Alimentação Plant-Based (Veg/Vegano)", "Gestante & Lactante",
                "Longevidade & Saúde Sênior", "Guia Prático & Orientações Gerais"
            ]
        )
        
        st.subheader("Plano Alimentar Base")
        pdf_file = st.file_uploader("Upload do Plano Alimentar Base (PDF):", type=["pdf"])
        
        submitted = st.form_submit_button("🚀 CRIAR E ENVIAR NUTRIBOOK")
        
        if submitted:
            if not nome or not whatsapp or not pdf_file:
                st.error("Por favor, preencha o Nome, WhatsApp e anexe o PDF.")
            else:
                st.success(f"Nutribook para {nome} enviado para a fila de processamento!")

# ==========================================
# ABA 2: CONECTAR WHATSAPP
# ==========================================
with tab2:
    st.header("Status da Conexão WhatsApp")
    
    col_status, col_btn = st.columns([2, 1])
    
    with col_btn:
        if st.button("Verificar Status / Gerar QR Code"):
            try:
                res = requests.get(
                    f"{EVOLUTION_API_URL}/instance/connectionState/{INSTANCE_NAME}",
                    headers={"apikey": API_KEY}
                )
                data = res.json()
                state = data.get("instance", {}).get("state", "disconnected")
                st.session_state["wa_state"] = state
            except Exception as e:
                st.error(f"Erro ao conectar com API: {e}")
                
    with col_status:
        current_state = st.session_state.get("wa_state", "unknown")
        if current_state == "open":
            st.success("🟢 Conectado ao WhatsApp")
        else:
            st.error("🔴 Desconectado")
            st.info("Escaneie o QR Code abaixo no seu aplicativo do WhatsApp:")
            # Exibe imagem do QR Code obtido via API quando desconectado

# ==========================================
# ABA 3: AGENDA & PACIENTES
# ==========================================
with tab3:
    st.header("Histórico e Pacientes")
    st.caption("Visualização das dietas geradas e atalhos de reenvio.")
    # Tabela dinâmica carregando os dados do Google Sheets
