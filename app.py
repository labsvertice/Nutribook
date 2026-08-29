import base64
import os
import pandas as pd
import requests
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# URL DO SEU APP WEB DO GOOGLE APPS SCRIPT
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbz7Pnyk2eCsURm-9-WKlluYJAFK_jj_Zd2FqM3KAJVe5zdNrAoI5ak8nmf_XOC2qxY/exec"

# CONFIGURAÇÕES DA EVOLUTION API (ORACLE CLOUD)
# As credenciais ficam protegidas no Secrets do Streamlit Cloud.
EVOLUTION_API_URL = st.secrets["evolution"]["api_url"]
API_KEY = st.secrets["evolution"]["api_key"]
INSTANCE_NAME = st.secrets["evolution"].get("instance", "nutribook")

# =================================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E CSS
# =================================================================================
st.set_page_config(
    page_title="Nutribook — Portal do Consultório",
    page_icon="🍎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =================================================================================
# 0. AUTENTICAÇÃO E IDENTIFICAÇÃO DA NUTRICIONISTA
# =================================================================================


def tela_login():
    """Exibe a tela de login quando não existe uma sessão autenticada."""

    col_esq, col_login, col_dir = st.columns([1, 1.1, 1])

    with col_login:

        # ============================================================
        # CABEÇALHO NUTRIBOOK
        # ============================================================

        if os.path.exists("cabecalho.png"):
            st.image(
                "cabecalho.png",
                width=850
            )

        # ============================================================
        # TÍTULO
        # ============================================================

        st.markdown(
            """
            <div style="
                text-align: center;
                margin-top: 28px;
                margin-bottom: 10px;
            ">
                <h2 style="
                    color: #112214;
                    margin: 0;
                    font-size: 30px;
                ">
                    🔐 Acesso ao Nutribook
                </h2>
            </div>
            """,
            unsafe_allow_html=True
        )

        # ============================================================
        # TEXTO
        # ============================================================

        st.markdown(
            """
            <div style="
                text-align: center;
                color: #334033;
                font-size: 16px;
                margin-bottom: 22px;
            ">
                Entre com sua conta Google para acessar o portal do consultório.
            </div>
            """,
            unsafe_allow_html=True
        )

        # ============================================================
        # BOTÃO GOOGLE
        # ============================================================

        _, col_btn, _ = st.columns([1, 1.2, 1])

        with col_btn:
            st.button(
                "Entrar com Google",
                on_click=st.login,
                use_container_width=True
            )

        # ============================================================
        # ESPAÇO
        # ============================================================

        st.markdown(
            "<div style='height: 35px;'></div>",
            unsafe_allow_html=True
        )
        # ============================================================
        # RODAPÉ
        # ============================================================
        
        st.markdown(
            "<div style='height: 40px;'></div>",
            unsafe_allow_html=True
        )
        
        if os.path.exists("rodape.png"):
            st.image(
                "rodape.png",
                width=650
            )
            

def obter_email_usuario_logado():
    """Retorna o e-mail autenticado pelo Google, normalizado."""
    return str(getattr(st.user, "email", "") or "").strip().lower()


if not st.user.is_logged_in:
    tela_login()
    st.stop()

EMAIL_NUTRICIONISTA_LOGADA = obter_email_usuario_logado()
NOME_NUTRICIONISTA_LOGADA = str(
    getattr(st.user, "name", "") or "Nutricionista"
).strip()

if not EMAIL_NUTRICIONISTA_LOGADA:
    st.error("Não foi possível identificar o e-mail da conta Google autenticada.")
    st.stop()

st.markdown(
    """
    <style>
    .stApp { background-color: #E2E8E2 !important; }
    
    header[data-testid="stHeader"], [data-testid="stHeader"], header {
        display: none !important;
        height: 0px !important;
    }
    
    .main .block-container, [data-testid="stMainBlockContainer"] {
        padding-top: 2rem !important;
        margin-top: -1.5rem !important;
        padding-bottom: 2rem !important;
    }
    
    [data-testid="stSidebarContent"] {
        padding-top: 2rem !important;
    }

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

    h1, h2, h3 { color: #112214 !important; font-weight: 700 !important; }
    [data-testid="stSidebar"] { background-color: #D3DDD3 !important; border-right: 1px solid #C1CDC1; }
    </style>
""",
    unsafe_allow_html=True,
)

# Conexão GSheets para leitura do Painel
conn = st.connection("gsheets", type=GSheetsConnection)


def normalizar_colunas(df):
    if df is not None and not df.empty:
        df = df.copy()
        df.columns = df.columns.astype(str).str.strip()
    return df


def carregar_dados_planilha():
    try:
        df = conn.read(ttl=0)
        return normalizar_colunas(df)
    except Exception:
        return None


def carregar_clientes():
    """Lê exclusivamente a aba Clientes para validar a conta autenticada."""
    try:
        df = conn.read(worksheet="Clientes", ttl=0)
        return normalizar_colunas(df)
    except Exception:
        return None


def localizar_coluna(df, candidatos):
    """Encontra uma coluna por correspondência de nome, ignorando maiúsculas/minúsculas."""
    if df is None or df.empty:
        return None

    mapa = {str(c).strip().lower(): c for c in df.columns}
    for candidato in candidatos:
        chave = str(candidato).strip().lower()
        if chave in mapa:
            return mapa[chave]
    return None


def obter_cliente_logada():
    """Valida o usuário Google contra a aba Clientes."""
    df = carregar_clientes()

    if df is None or df.empty:
        st.error("Não foi possível carregar o cadastro de profissionais.")
        st.stop()

    c_email = localizar_coluna(df, ["E-mail", "Email", "E-mail Nutricionista"])
    c_nome = localizar_coluna(df, ["Nome"])
    c_ativo = localizar_coluna(df, ["Ativo"])
    c_limite = localizar_coluna(df, ["Limite mensal"])
    c_consumo = localizar_coluna(df, ["Nutribooks no mês"])
    c_whatsapp = localizar_coluna(df, ["WhatsApp"])

    if not c_email:
        st.error("A aba Clientes não possui a coluna de e-mail necessária para o login.")
        st.stop()

    df["__email_login"] = (
        df[c_email]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    encontrados = df[df["__email_login"] == EMAIL_NUTRICIONISTA_LOGADA]

    if encontrados.empty:
        st.error(
            f"A conta **{EMAIL_NUTRICIONISTA_LOGADA}** não está cadastrada no Nutribook."
        )
        st.info("Entre em contato com o suporte para cadastrar ou liberar seu acesso.")
        st.stop()

    registro = encontrados.iloc[0]
    ativo = str(registro[c_ativo]).strip().lower() if c_ativo else "sim"

    if ativo not in {"sim", "true", "1", "ativo", "yes"}:
        st.error("Seu cadastro está inativo no Nutribook.")
        st.stop()

    return {
        "nome": str(registro[c_nome]).strip() if c_nome else NOME_NUTRICIONISTA_LOGADA,
        "email": EMAIL_NUTRICIONISTA_LOGADA,
        "ativo": True,
        "limite": registro[c_limite] if c_limite else "",
        "consumo": registro[c_consumo] if c_consumo else "",
        "whatsapp": registro[c_whatsapp] if c_whatsapp else "",
    }


CLIENTE_LOGADA = obter_cliente_logada()


@st.cache_data(ttl=15)
def checar_status_whatsapp_rapido():
    """Consulta o status da Evolution API com cache curto de 15s para não travar a interface."""
    try:
        url_state = (
            f"{EVOLUTION_API_URL}/instance/connectionState/{INSTANCE_NAME}"
        )
        headers = {"apikey": API_KEY}
        res = requests.get(url_state, headers=headers, timeout=3)
        if res.status_code == 200:
            state = res.json().get("instance", {}).get("state", "disconnected")
            return state == "open"
    except Exception:
        pass
    return False


# =================================================================================
# 2. SIDEBAR / NAV
# =================================================================================
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=160)
    else:
        st.title("🍎 Nutribook")

    st.markdown(f"#### Olá, **{CLIENTE_LOGADA['nome']}**! 👋")
    st.caption("Vamos iniciar o próximo Nutribook?")

    col_usuario, col_saida = st.columns([3, 1])
    with col_usuario:
        st.caption(EMAIL_NUTRICIONISTA_LOGADA)
    with col_saida:
        if st.button("↪️", help="Sair"):
            st.logout()

    st.divider()

    menu = st.radio(
        "Navegação do Consultório:",
        ["➕ Novo Nutribook", "📋 Painel Nutribook", "📱 Conectar WhatsApp"],
        index=0,
    )

# =================================================================================
# 3. CONTEÚDO PRINCIPAL
# =================================================================================

if menu == "➕ Novo Nutribook":
    st.title("🍎 Novo Nutribook")
    st.write(
        "Preencha as informações do paciente e anexe o plano em PDF para"
        " disparar a geração."
    )

    wa_conectado = checar_status_whatsapp_rapido()
    badge_wa = "🟢 Conectado" if wa_conectado else "🔴 Desconectado"

    with st.form("form_nutribook", clear_on_submit=True):
        st.subheader("Dados do Paciente")
        col_nome, col_email, col_whatsapp = st.columns(3)
        with col_nome:
            nome_paciente = st.text_input("Nome do Paciente *")
        with col_email:
            email_paciente = st.text_input("E-mail do Paciente")
        with col_whatsapp:
            whatsapp_paciente = st.text_input(
                f"WhatsApp do Paciente (com DDD) * — {badge_wa}",
                placeholder="Ex: 5548999999999",
            )

        st.subheader("Perfis / Protocolos do Paciente")
        lista_protocolos = [
            "Fertilidade Feminina",
            "Emagrecimento & Definição",
            "Hipertrofia & Ganho de Massa",
            "Reeducação Alimentar & Saúde Geral",
            "Saúde Intestinal (Disbiose / FODMAPs)",
            "Saúde da Mulher (SOP / Endometriose)",
            "Controle Metabólico (Diabetes / Colesterol)",
            "Performance Esportiva",
            "Alimentação Plant-Based (Veg/Vegano)",
            "Gestante & Lactante",
            "Longevidade & Saúde Sênior",
            "Guia Prático & Orientações Gerais",
        ]

        protocolos_selecionados = []
        col_proto1, col_proto2 = st.columns(2)
        metade = (len(lista_protocolos) + 1) // 2

        with col_proto1:
            for p in lista_protocolos[:metade]:
                if st.checkbox(p, key=p):
                    protocolos_selecionados.append(p)

        with col_proto2:
            for p in lista_protocolos[metade:]:
                if st.checkbox(p, key=p):
                    protocolos_selecionados.append(p)

        st.subheader("Plano Alimentar Base")
        pdf_file = st.file_uploader(
            "Upload do Plano Alimentar Base (PDF):", type=["pdf"]
        )

        submitted = st.form_submit_button("CRIAR NUTRIBOOK")

        if submitted:
            if nome_paciente and whatsapp_paciente and pdf_file:
                if WEBAPP_URL == "SUA_URL_DO_WEB_APP_AQUI" or not WEBAPP_URL:
                    st.error(
                        "Por favor, configure a URL do seu Apps Script Web App"
                        " no código."
                    )
                else:
                    with st.spinner(
                        "Enviando arquivo e registrando pedido..."
                    ):
                        try:
                            file_bytes = base64.b64encode(
                                pdf_file.getvalue()
                            ).decode("utf-8")
                            protocolos_str = (
                                ", ".join(protocolos_selecionados)
                                if protocolos_selecionados
                                else "Padrão"
                            )

                            mensagem_whatsapp = (
                                f"Olá, *{nome_paciente}*! 🍎✨\n\n"
                                f"Aqui está o seu *Nutribook*, preparado com muito carinho e 100% personalizado para a sua rotina e seus objetivos! 🥗💪\n\n"
                                f"Dê uma olhada no documento em anexo com calma. Qualquer dúvida que tiver, estou por aqui para te ajudar.\n\n"
                                f"Bora caprichar na alimentação e focar nos resultados! 🚀💚"
                            )

                            payload = {
                                "nome": nome_paciente,
                                "email": email_paciente,
                                "whatsapp": whatsapp_paciente,
                                "protocolos": protocolos_str,
                                "fileName": pdf_file.name,
                                "fileBytes": file_bytes,
                                "mensagem": mensagem_whatsapp,
                                "instancia": INSTANCE_NAME,
                                "emailNutricionista": EMAIL_NUTRICIONISTA_LOGADA,
                            }

                            response = requests.post(WEBAPP_URL, json=payload, timeout=30)

                            if (
                                response.status_code == 200
                                and response.json().get("status") == "success"
                            ):
                                st.success(
                                    f"✅ Nutribook para **{nome_paciente}**"
                                    " registrado com sucesso!"
                                )
                            else:
                                st.error(f"Erro ao registrar: {response.text}")
                        except Exception as e:
                            st.error(f"Falha na comunicação com o Apps Script: {e}")
            else:
                st.error(
                    "Por favor, preencha o Nome, WhatsApp do Paciente e"
                    " selecione um arquivo PDF."
                )

elif menu == "📋 Painel Nutribook":
    st.title("📄 Painel Nutribook")
    st.write(
        "Acompanhe os indicadores de geração, faturamento e histórico"
        " completo."
    )
    st.divider()

    df_dados = carregar_dados_planilha()

    if df_dados is not None and not df_dados.empty:
        df_dados = df_dados.copy()

        # Segurança: o painel mostra somente os registros da nutricionista logada.
        col_nutri = next(
            (
                c
                for c in df_dados.columns
                if str(c).strip().lower()
                in {"e-mail nutricionista", "email nutricionista", "e-mail da nutricionista"}
            ),
            None,
        )

        if col_nutri:
            df_dados = df_dados[
                df_dados[col_nutri].fillna("").astype(str).str.strip().str.lower()
                == EMAIL_NUTRICIONISTA_LOGADA
            ].copy()

        col_status = (
            "Status" if "Status" in df_dados.columns else df_dados.columns[-1]
        )
        col_data = (
            "Carimbo de data/hora"
            if "Carimbo de data/hora" in df_dados.columns
            else df_dados.columns[0]
        )

        df_dados["Data_Parsed"] = pd.to_datetime(
            df_dados[col_data], dayfirst=True, errors="coerce"
        )
        
        status_clean = df_dados[col_status].astype(str).str.strip().str.lower()
        df_concluidos = df_dados[status_clean.isin(["concluído", "concluido"])]

        VALOR_NUTRIBOOK = 5.00
        total_historico = len(df_concluidos)
        agora = pd.Timestamp.now()

        df_mes_atual = df_concluidos[
            (df_concluidos["Data_Parsed"].dt.month == agora.month)
            & (df_concluidos["Data_Parsed"].dt.year == agora.year)
        ]
        total_mes = len(df_mes_atual)

        faturamento_mes = total_mes * VALOR_NUTRIBOOK
        faturamento_total = total_historico * VALOR_NUTRIBOOK

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        with kpi1:
            st.metric("Total Concluídos (Geral)", f"{total_historico}")
        with kpi2:
            st.metric("Concluídos no Mês", f"{total_mes}")
        with kpi3:
            st.metric(
                "Faturamento Mês Atual",
                f"R$ {faturamento_mes:,.2f}"
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", "."),
            )
        with kpi4:
            st.metric(
                "Faturamento Acumulado",
                f"R$ {faturamento_total:,.2f}"
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", "."),
            )

        st.markdown("---")
        st.subheader("📈 Evolução Mensal (Nutribooks Concluídos)")

        # O gráfico mensal usa exclusivamente a aba Historico_Nutribooks,
        # filtrada pela nutricionista autenticada.
        try:
            df_historico = conn.read(
                worksheet="Historico_Nutribooks",
                ttl=0
            )
            df_historico = normalizar_colunas(df_historico)
        except Exception:
            df_historico = None

        if df_historico is not None and not df_historico.empty:
            c_mes_hist = localizar_coluna(
                df_historico,
                ["Mês", "Mes"]
            )
            c_email_hist = localizar_coluna(
                df_historico,
                ["E-mail Nutricionista", "E-mail", "Email"]
            )
            c_nutribooks_hist = localizar_coluna(
                df_historico,
                ["Nutribooks", "Nutribooks no mês", "Quantidade"]
            )

            if c_mes_hist and c_email_hist and c_nutribooks_hist:
                df_historico = df_historico[
                    df_historico[c_email_hist]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                    .str.lower()
                    == EMAIL_NUTRICIONISTA_LOGADA
                ].copy()

                if not df_historico.empty:
                    # Aceita tanto 2026-08 em texto quanto uma data real do Sheets.
                    df_historico["Mes_Parsed"] = pd.to_datetime(
                        df_historico[c_mes_hist],
                        errors="coerce"
                    )

                    df_historico["Quantidade"] = pd.to_numeric(
                        df_historico[c_nutribooks_hist],
                        errors="coerce"
                    ).fillna(0)

                    df_grafico = (
                        df_historico
                        .dropna(subset=["Mes_Parsed"])
                        .sort_values("Mes_Parsed")
                        [["Mes_Parsed", "Quantidade"]]
                        .drop_duplicates(
                            subset=["Mes_Parsed"],
                            keep="last"
                        )
                        .copy()
                    )

                    if not df_grafico.empty:
                        df_grafico["Mês/Ano"] = (
                            df_grafico["Mes_Parsed"]
                            .dt.strftime("%m/%Y")
                        )

                        st.bar_chart(
                            df_grafico.set_index("Mês/Ano")[["Quantidade"]],
                            height=260
                        )
                    else:
                        st.info(
                            "Nenhum histórico mensal válido encontrado "
                            "para exibição do gráfico."
                        )
                else:
                    st.info(
                        "Nenhum histórico mensal encontrado para "
                        "a nutricionista logada."
                    )
            else:
                st.error(
                    "A aba Historico_Nutribooks não possui as colunas "
                    "esperadas para montar o gráfico."
                )
        else:
            st.info(
                "Nenhum histórico mensal encontrado para exibição do gráfico."
            )

        st.markdown("---")
        st.subheader("📋 Histórico de Pedidos")

        status_unicos = list(df_dados[col_status].dropna().unique())
        status_filtro = st.selectbox(
            "Filtrar por Status:", ["Todos"] + status_unicos
        )

        df_exibicao = df_dados.copy()
        if status_filtro != "Todos":
            df_exibicao = df_exibicao[df_exibicao[col_status] == status_filtro]

        c_data = next(
            (
                c
                for c in df_exibicao.columns
                if "carimbo" in c.lower() or "data" in c.lower()
            ),
            None,
        )
        c_nome = next(
            (c for c in df_exibicao.columns if "nome" in c.lower()), None
        )
        c_email = next(
            (
                c
                for c in df_exibicao.columns
                if "email" in c.lower() or "e-mail" in c.lower()
            ),
            None,
        )
        c_whatsapp = next(
            (
                c
                for c in df_exibicao.columns
                if "whatsapp" in c.lower()
                or "celular" in c.lower()
                or "telefone" in c.lower()
            ),
            None,
        )
        c_perfil = next(
            (
                c
                for c in df_exibicao.columns
                if "perfil" in c.lower() or "protocolo" in c.lower()
            ),
            None,
        )
        c_link = next(
            (c for c in df_exibicao.columns if "link" in c.lower()), None
        )
        if not c_link:
            c_link = next(
                (c for c in df_exibicao.columns if "upload" in c.lower()), None
            )
        c_status = next(
            (c for c in df_exibicao.columns if "status" in c.lower()), None
        )

        mapa_colunas = {}
        if c_data:
            mapa_colunas[c_data] = "Carimbo de data/hora"
        if c_nome:
            mapa_colunas[c_nome] = "Nome do Paciente"
        if c_email:
            mapa_colunas[c_email] = "E-mail do Paciente"
        if c_whatsapp:
            mapa_colunas[c_whatsapp] = "WhatsApp do Paciente"
        if c_perfil:
            mapa_colunas[c_perfil] = "Perfil / Protocolo"
        if c_link:
            mapa_colunas[c_link] = "Link Nutribook"
        if c_status:
            mapa_colunas[c_status] = "Status"

        cols_origem = list(mapa_colunas.keys())
        if cols_origem:
            df_final = df_exibicao[cols_origem].rename(columns=mapa_colunas)
        else:
            df_final = df_exibicao.copy()

        # Limpeza rigorosa de strings e remoção do sufixo .0 de floats
        for col in df_final.columns:
            if col != "Link Nutribook":
                df_final[col] = (
                    df_final[col]
                    .fillna("")
                    .astype(str)
                    .replace({"None": "", "nan": "", "<NA>": ""})
                    .str.replace(r"\.0$", "", regex=True)
                    .str.strip()
                )

        config_colunas = {}
        if "Link Nutribook" in df_final.columns:
            config_colunas["Link Nutribook"] = st.column_config.LinkColumn(
                "Link Nutribook", display_text="🔗"
            )

        st.dataframe(
            df_final,
            use_container_width=True,
            hide_index=True,
            column_config=config_colunas,
        )
    else:
        st.info("Nenhum dado encontrado na planilha do Google Sheets.")

elif menu == "📱 Conectar WhatsApp":
    st.title("📱 Status da Conexão WhatsApp")
    st.write(
        "Gerencie a conexão da Evolution API para disparos automáticos de"
        " mensagens."
    )
    st.divider()

    col_btn, col_status = st.columns([1, 2])

    with col_btn:
        verificar = st.button("🔄 Verificar Status / Gerar QR Code")

    try:
        url_state = (
            f"{EVOLUTION_API_URL}/instance/connectionState/{INSTANCE_NAME}"
        )
        headers = {"apikey": API_KEY}
        res_state = requests.get(url_state, headers=headers, timeout=5)

        if res_state.status_code == 200:
            state_data = res_state.json()
            status_atual = state_data.get("instance", {}).get(
                "state", "disconnected"
            )

            if status_atual == "open":
                st.success("🟢 **WhatsApp Conectado e Operacional!**")
                st.info(
                    "Sua instância está pronta para enviar o Nutribook"
                    " automaticamente aos pacientes."
                )
            else:
                st.error("🔴 **WhatsApp Desconectado**")
                st.warning(
                    "Abra o WhatsApp no seu celular, vá em 'Aparelhos"
                    " Conectados' e escaneie o QR Code abaixo:"
                )

                url_qr = f"{EVOLUTION_API_URL}/instance/connect/{INSTANCE_NAME}"
                res_qr = requests.get(url_qr, headers=headers, timeout=5)
                if res_qr.status_code == 200:
                    qr_data = res_qr.json()
                    base64_qr = qr_data.get("base64") or qr_data.get("code")

                    if base64_qr:
                        if "," in base64_qr:
                            base64_qr = base64_qr.split(",")[1]
                        st.image(base64.b64decode(base64_qr), width=280)
                    else:
                        st.info("Aguardando geração do QR Code...")
        else:
            st.error(
                "Erro ao consultar a Evolution API. Status Code:"
                f" {res_state.status_code}"
            )

    except Exception as e:
        st.error(f"Falha de conexão com o servidor da Evolution API: {e}")
