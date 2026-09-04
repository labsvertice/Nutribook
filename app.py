import base64
import os
import re

import pandas as pd
import requests
import streamlit as st
from streamlit_gsheets import GSheetsConnection


# =================================================================================
# CONFIGURAÇÕES GERAIS
# =================================================================================

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbz7Pnyk2eCsURm-9-WKlluYJAFK_jj_Zd2FqM3KAJVe5zdNrAoI5ak8nmf_XOC2qxY/exec"

# Evolution API: somente URL e chave ficam nos Secrets.
# A instância é definida por nutricionista via cadastro/identificação.
try:
    EVOLUTION_API_URL = st.secrets["evolution"]["api_url"]
    API_KEY = st.secrets["evolution"]["api_key"]
except Exception:
    EVOLUTION_API_URL = ""
    API_KEY = ""

SPREADSHEET_ID = "1X-9ZrJhSrVSpjDJCw3I-1Ry14oAgk2iJ8fckMxMDR9w"

st.set_page_config(
    page_title="Nutribook — Portal do Consultório",
    page_icon="🍎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =================================================================================
# CSS — mantém visual Nutribook e preserva controles nativos da sidebar
# =================================================================================
st.markdown(
    """
    <style>
    :root {
        --brand-bg: #E2E8E2;
        --brand-panel: #FAFAFA;
        --brand-line: #C1CDC1;
        --brand-text: #112214;
        --brand-muted: #5E6D64;
        --brand-green: #2A5C36;
        --brand-green-dark: #1E4327;
    }

    .stApp {
        background-color: var(--brand-bg) !important;
    }

    /* Mantém o cabeçalho nativo para preservar abrir/fechar a sidebar,
       inclusive em telas pequenas. */
    header[data-testid="stHeader"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    header[data-testid="stHeader"] [data-testid="stDecoration"] {
        display: none !important;
    }

    .main .block-container,
    [data-testid="stMainBlockContainer"] {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
    }

    [data-testid="stSidebar"] {
        background-color: #D3DDD3 !important;
        border-right: 1px solid var(--brand-line) !important;
    }

    [data-testid="stSidebarContent"] {
        padding-top: 1.6rem !important;
    }

    div.stButton > button,
    div.stFormSubmitButton > button {
        background-color: #2A5C36 !important;
        color: #FFFFFF !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 10px 24px !important;
        transition: all 0.3s ease !important;
        width: 100%;
    }

    div.stButton > button:hover,
    div.stFormSubmitButton > button:hover {
        background-color: #1E4327 !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(42, 92, 54, 0.25) !important;
    }

    h1, h2, h3 {
        color: #112214 !important;
        font-weight: 700 !important;
    }

    div[data-baseweb="input"] > div,
    div[data-baseweb="textarea"] > div,
    div[data-baseweb="select"] > div {
        background: #C9C9C9 !important;
        border-color: #C1CDC1 !important;
    }

    div[data-baseweb="input"] input,
    div[data-baseweb="textarea"] textarea,
    div[data-baseweb="select"] input {
        background: transparent !important;
        color: #202020 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =================================================================================
# GOOGLE SHEETS
# =================================================================================
conn = st.connection("gsheets", type=GSheetsConnection)


def normalizar_colunas(df):
    if df is not None and not df.empty:
        df = df.copy()
        df.columns = df.columns.astype(str).str.strip()
    return df


def carregar_dados_planilha(worksheet=None):
    try:
        kwargs = {"ttl": 0}
        if worksheet:
            kwargs["worksheet"] = worksheet
        df = conn.read(**kwargs)
        return normalizar_colunas(df)
    except Exception:
        return None


def localizar_coluna(df, candidatos):
    if df is None or df.empty:
        return None
    mapa = {str(c).strip().lower(): c for c in df.columns}
    for candidato in candidatos:
        chave = str(candidato).strip().lower()
        if chave in mapa:
            return mapa[chave]
    return None


def valor_ativo(valor):
    return str(valor).strip().lower() in {
        "sim", "true", "1", "ativo", "yes"
    }


# =================================================================================
# AUTENTICAÇÃO POR CADASTRO — SEM GOOGLE LOGIN
# =================================================================================

def autenticar_nutricionista(login, senha):
    """
    Valida Login + Senha diretamente contra a aba Clientes.

    Compatibilidade:
    - Login/Senha passam a ser obrigatórios para os novos cadastros.
    - O cadastro ainda mantém E-mail e WhatsApp para identificação e comunicação.
    """
    df = carregar_dados_planilha("Clientes")

    if df is None or df.empty:
        return None, "Não foi possível carregar o cadastro de nutricionistas."

    c_nome = localizar_coluna(df, ["Nome"])
    c_email = localizar_coluna(df, ["E-mail", "Email", "E-mail Nutricionista"])
    c_whatsapp = localizar_coluna(df, ["WhatsApp"])
    c_limite = localizar_coluna(df, ["Limite mensal", "Limite Mensal"])
    c_ativo = localizar_coluna(df, ["Ativo"])
    c_consumo = localizar_coluna(df, ["Nutribooks no mês", "Nutribooks no mes"])
    c_login = localizar_coluna(df, ["Login", "Usuário", "Usuario"])
    c_senha = localizar_coluna(df, ["Senha", "Password"])
    c_nutri_id = localizar_coluna(df, ["Nutri_ID", "Nutri ID", "Cliente_ID", "Cliente ID"])

    obrigatorias = {
        "Nome": c_nome,
        "E-mail": c_email,
        "WhatsApp": c_whatsapp,
        "Ativo": c_ativo,
        "Login": c_login,
        "Senha": c_senha,
        "Nutri_ID": c_nutri_id,
    }

    faltantes = [nome for nome, coluna in obrigatorias.items() if not coluna]
    if faltantes:
        return None, (
            "A aba Clientes está incompleta. "
            f"Colunas ausentes: {', '.join(faltantes)}."
        )

    login_normalizado = str(login or "").strip().lower()
    df["__login"] = (
        df[c_login]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    encontrados = df[df["__login"] == login_normalizado].copy()

    if encontrados.empty:
        return None, "Login ou senha inválidos."

    if len(encontrados) > 1:
        return None, "Este login está duplicado no cadastro. Procure o suporte."

    registro = encontrados.iloc[0]

    if not valor_ativo(registro[c_ativo]):
        return None, "Seu cadastro está inativo no Nutribook."

    if str(senha or "") != str(registro[c_senha] or ""):
        return None, "Login ou senha inválidos."

    nome = str(registro[c_nome]).strip() if c_nome else "Nutricionista"
    email = str(registro[c_email]).strip().lower() if c_email else ""
    whatsapp = str(registro[c_whatsapp]).strip() if c_whatsapp else ""
    nutri_id = str(registro[c_nutri_id]).strip() if c_nutri_id and pd.notna(registro[c_nutri_id]) else ""

    if not nutri_id:
        return None, "Este cadastro não possui Nutri_ID."

    return {
        "nome": nome,
        "email": email,
        "whatsapp": whatsapp,
        "limite": registro[c_limite] if c_limite else "",
        "consumo": registro[c_consumo] if c_consumo else "",
        "login": login_normalizado,
        "nutri_id": nutri_id,
    }, None


def limpar_sessao():
    for chave in [
        "autenticado",
        "nutri_nome",
        "nutri_email",
        "nutri_whatsapp",
        "nutri_limite",
        "nutri_consumo",
        "nutri_login",
        "nutri_id",
    ]:
        st.session_state.pop(chave, None)


def tela_login():
    st.markdown('<div class="login-shell">', unsafe_allow_html=True)

    _, col_login, _ = st.columns([1, 1.1, 1])

    with col_login:
        if os.path.exists("cabecalho.png"):
            st.image("cabecalho.png", width=1000)

        st.markdown(
            """
            <div style="text-align:center;margin-top:28px;margin-bottom:10px;">
                <h2 style="color:#112214;margin:0;font-size:30px;">
                    🔐 Acesso ao Nutribook
                </h2>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div style="text-align:center;color:#334033;font-size:16px;margin-bottom:22px;">
                Entre com seu login e senha para acessar o portal.
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("form_login"):
            login = st.text_input("Login", placeholder="Ex: Digite seu login")
            senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            entrar = st.form_submit_button("ENTRAR", use_container_width=True)

        st.markdown("<div style='height:35px;'></div>", unsafe_allow_html=True)

        if os.path.exists("rodape.png"):
            st.image("rodape.png", width=800)

        if entrar:
            if not login or not senha:
                st.error("Informe o login e a senha.")
                return

            nutricionista, erro = autenticar_nutricionista(login, senha)

            if erro:
                st.error(erro)
                return

            st.session_state["autenticado"] = True
            st.session_state["nutri_nome"] = nutricionista["nome"]
            st.session_state["nutri_email"] = nutricionista["email"]
            st.session_state["nutri_whatsapp"] = nutricionista["whatsapp"]
            st.session_state["nutri_limite"] = nutricionista["limite"]
            st.session_state["nutri_consumo"] = nutricionista["consumo"]
            st.session_state["nutri_login"] = nutricionista["login"]
            st.session_state["nutri_id"] = nutricionista["nutri_id"]
            st.rerun()


if not st.session_state.get("autenticado", False):
    tela_login()
    st.stop()


NOME_NUTRICIONISTA_LOGADA = st.session_state["nutri_nome"]
EMAIL_NUTRICIONISTA_LOGADA = st.session_state["nutri_email"]
WHATSAPP_NUTRICIONISTA_LOGADA = st.session_state.get("nutri_whatsapp", "")
LOGIN_NUTRICIONISTA_LOGADA = st.session_state.get("nutri_login", "")
NUTRI_ID_LOGADA = st.session_state.get("nutri_id", "")
INSTANCE_NAME = NUTRI_ID_LOGADA.strip()


# =================================================================================
# EVOLUTION API — STATUS E CRIAÇÃO AUTOMÁTICA
# =================================================================================

def evolution_configurada():
    return bool(EVOLUTION_API_URL and API_KEY)


def evolution_headers():
    return {
        "apikey": API_KEY,
        "Content-Type": "application/json",
    }


def obter_estado_instancia(instance_name):
    if not instance_name or not evolution_configurada():
        return {
            "ok": False,
            "exists": False,
            "state": "disconnected",
            "status_code": None,
            "data": {},
        }

    try:
        url = f"{EVOLUTION_API_URL}/instance/connectionState/{instance_name}"
        response = requests.get(url, headers=evolution_headers(), timeout=5)
        try:
            data = response.json()
        except Exception:
            data = {}

        if response.status_code == 200:
            state = data.get("instance", {}).get("state", "disconnected")
            return {
                "ok": True,
                "exists": True,
                "state": state,
                "status_code": 200,
                "data": data,
            }

        if response.status_code == 404:
            return {
                "ok": False,
                "exists": False,
                "state": "disconnected",
                "status_code": 404,
                "data": data,
            }

        return {
            "ok": False,
            "exists": True,
            "state": "disconnected",
            "status_code": response.status_code,
            "data": data,
        }

    except Exception as e:
        return {
            "ok": False,
            "exists": None,
            "state": "disconnected",
            "status_code": None,
            "data": {"error": str(e)},
        }


def criar_instancia_evolution(instance_name):
    if not instance_name:
        return {"ok": False, "status_code": None, "data": {}, "mensagem": "Nome da instância não informado."}

    if not evolution_configurada():
        return {"ok": False, "status_code": None, "data": {}, "mensagem": "A Evolution API não está configurada nos Secrets."}

    try:
        url = f"{EVOLUTION_API_URL}/instance/create"
        payload = {
            "instanceName": instance_name,
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS",
        }
        response = requests.post(url, headers=evolution_headers(), json=payload, timeout=15)
        try:
            data = response.json()
        except Exception:
            data = {}

        if response.status_code in {200, 201}:
            return {"ok": True, "status_code": response.status_code, "data": data, "mensagem": "Instância criada com sucesso."}

        texto = str(data or response.text).lower()
        if response.status_code in {400, 409} and any(x in texto for x in ["already", "exist", "instanc"]):
            return {"ok": True, "status_code": response.status_code, "data": data, "mensagem": "A instância já existe."}

        return {"ok": False, "status_code": response.status_code, "data": data, "mensagem": f"A Evolution API retornou status {response.status_code}."}

    except Exception as e:
        return {"ok": False, "status_code": None, "data": {}, "mensagem": f"Falha ao criar a instância: {e}"}


def obter_qr_code_evolution(instance_name):
    if not instance_name:
        return {"ok": False, "base64": None, "pairing_code": None, "code": None, "status_code": None, "data": {}, "mensagem": "Nome da instância não informado."}

    if not evolution_configurada():
        return {"ok": False, "base64": None, "pairing_code": None, "code": None, "status_code": None, "data": {}, "mensagem": "A Evolution API não está configurada nos Secrets."}

    try:
        url = f"{EVOLUTION_API_URL}/instance/connect/{instance_name}"
        response = requests.get(url, headers=evolution_headers(), timeout=10)
        try:
            data = response.json()
        except Exception:
            data = {}

        if response.status_code == 200:
            base64_qr = data.get("base64") or data.get("qrcode") or data.get("qrCode")
            pairing_code = data.get("pairingCode")
            code = data.get("code")
            return {
                "ok": bool(base64_qr or pairing_code or code),
                "base64": base64_qr,
                "pairing_code": pairing_code,
                "code": code,
                "status_code": 200,
                "data": data,
                "mensagem": "QR Code obtido." if (base64_qr or pairing_code or code) else "A Evolution API não retornou o QR Code ainda.",
            }

        return {
            "ok": False,
            "base64": None,
            "pairing_code": None,
            "code": None,
            "status_code": response.status_code,
            "data": data,
            "mensagem": f"A Evolution API retornou status {response.status_code}.",
        }

    except Exception as e:
        return {
            "ok": False,
            "base64": None,
            "pairing_code": None,
            "code": None,
            "status_code": None,
            "data": {},
            "mensagem": f"Falha ao obter o QR Code: {e}",
        }


def extrair_qr_da_resposta(data):
    if not isinstance(data, dict):
        return None, None, None

    base64_qr = data.get("base64") or data.get("qrcode") or data.get("qrCode")
    pairing_code = data.get("pairingCode")
    code = data.get("code")

    if isinstance(data.get("qrcode"), dict):
        obj = data["qrcode"]
        base64_qr = base64_qr or obj.get("base64")
        pairing_code = pairing_code or obj.get("pairingCode")
        code = code or obj.get("code")

    if isinstance(data.get("instance"), dict):
        obj = data["instance"].get("qrcode")
        if isinstance(obj, dict):
            base64_qr = base64_qr or obj.get("base64")
            pairing_code = pairing_code or obj.get("pairingCode")
            code = code or obj.get("code")

    return base64_qr, pairing_code, code


def obter_qr_bytes(base64_qr):
    if not base64_qr:
        return None
    try:
        valor = str(base64_qr).strip()
        if "," in valor:
            valor = valor.split(",", 1)[1]
        return base64.b64decode(valor)
    except Exception:
        return None


def preparar_instancia_para_conexao(instance_name):
    estado = obter_estado_instancia(instance_name)

    if estado["exists"] is True:
        return {"ok": True, "criada_agora": False, "estado": estado, "criacao": None}

    if estado["status_code"] not in {404, None}:
        return {
            "ok": False,
            "criada_agora": False,
            "estado": estado,
            "criacao": None,
            "mensagem": "Não foi possível verificar a instância na Evolution API.",
        }

    criacao = criar_instancia_evolution(instance_name)
    if not criacao["ok"]:
        return {
            "ok": False,
            "criada_agora": False,
            "estado": estado,
            "criacao": criacao,
            "mensagem": criacao["mensagem"],
        }

    return {
        "ok": True,
        "criada_agora": True,
        "estado": estado,
        "criacao": criacao,
    }


def checar_whatsapp_em_tempo_real(instance_name):
    estado = obter_estado_instancia(instance_name)

    if estado["ok"] and estado["exists"] and estado["state"] == "open":
        return {"conectado": True, "motivo": None}

    if estado["status_code"] == 404:
        return {"conectado": False, "motivo": "A instância do WhatsApp ainda não existe na Evolution API."}

    return {"conectado": False, "motivo": "O WhatsApp está desconectado."}


# =================================================================================
# SIDEBAR / NAV
# =================================================================================
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=160)
    else:
        st.title("🍎 Nutribook")

    st.markdown(f"#### Olá, **{NOME_NUTRICIONISTA_LOGADA}**! 👋")
    st.caption("Vamos iniciar o próximo Nutribook?")
    st.caption(LOGIN_NUTRICIONISTA_LOGADA)
    st.caption(f"WhatsApp: {INSTANCE_NAME or 'não configurado'}")

    if st.button("↪️ Sair", help="Sair do Nutribook"):
        limpar_sessao()
        st.rerun()

    st.divider()

    menu = st.radio(
        "Navegação do Consultório:",
        ["➕ Novo Nutribook", "📋 Painel Nutribook", "📱 Conectar WhatsApp"],
        index=0,
    )


# =================================================================================
# NOVO NUTRIBOOK
# =================================================================================
if menu == "➕ Novo Nutribook":
    st.title("🍎 Novo Nutribook")
    st.write(
        "Preencha as informações do paciente e anexe o plano em PDF para disparar a geração."
    )

    estado_visual = obter_estado_instancia(INSTANCE_NAME)
    if estado_visual["ok"] and estado_visual["state"] == "open":
        badge_wa = "🟢 Conectado"
    elif INSTANCE_NAME:
        badge_wa = "🔴 Desconectado"
    else:
        badge_wa = "⚪ Não configurado"

    with st.form("form_nutribook", clear_on_submit=True):
        st.subheader("Dados do Paciente")

        col_nome, col_whatsapp = st.columns(2)

        with col_nome:
            nome_paciente = st.text_input("Nome do Paciente *")

        with col_whatsapp:
            whatsapp_paciente = st.text_input(
                f"WhatsApp do Paciente (com DDD) * — {badge_wa}",
                placeholder="Ex: 5548999999999",
            )

        st.subheader("Perfil / Protocolo do Paciente")

        # Perfis vêm do cadastro da nutricionista na aba Templates.
st.caption("VERSÃO NOVA DO APP — 04/09/2026")
df_templates = carregar_dados_planilha("Templates")
perfis_disponiveis = []

if df_templates is not None and not df_templates.empty:

    c_nutri_id_tpl = localizar_coluna(
        df_templates,
        ["Nutri_ID", "Nutri ID"]
    )

    c_perfil_tpl = localizar_coluna(
        df_templates,
        ["Perfil", "Perfil Clínico", "Perfil Clinico"]
    )

    c_ativo_tpl = localizar_coluna(
        df_templates,
        ["Ativo"]
    )

    if c_nutri_id_tpl and c_perfil_tpl:

        nutri_id_limpo = (
            df_templates[c_nutri_id_tpl]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
        )

        dados_tpl = df_templates[
            nutri_id_limpo
            == NUTRI_ID_LOGADA.strip().lower()
        ].copy()

        if (
            c_ativo_tpl
            and c_ativo_tpl in dados_tpl.columns
        ):
            dados_tpl = dados_tpl[
                dados_tpl[c_ativo_tpl]
                .apply(valor_ativo)
            ].copy()

        if (
            c_perfil_tpl
            and c_perfil_tpl in dados_tpl.columns
        ):
            perfis_disponiveis = sorted(
                [
                    str(v).strip()
                    for v in dados_tpl[c_perfil_tpl]
                    .dropna()
                    .unique()
                    if str(v).strip()
                ]
            )

        if perfis_disponiveis:
            perfil_selecionado = st.radio(
                "Selecione o perfil principal do Nutribook:",
                perfis_disponiveis,
                horizontal=False,
            )
        else:
            st.warning(
                "⚠️ Seu cadastro ainda não possui perfis configurados."
            )
        
            st.info(
                "Para criar um Nutribook, fale com o administrador "
                "para cadastrar os perfis dos seus pacientes."
            )
        
            perfil_selecionado = ""

        st.subheader("Plano Alimentar Base")
        pdf_file = st.file_uploader(
            "Upload do Plano Alimentar Base (PDF):",
            type=["pdf"],
        )

        submitted = st.form_submit_button("CRIAR NUTRIBOOK")

        if submitted:
            if not nome_paciente or not whatsapp_paciente or not pdf_file:
                st.error(
                    "Por favor, preencha o Nome, WhatsApp do Paciente e selecione um arquivo PDF."
                )

            elif not perfil_selecionado:
                st.error(
                    "Selecione um perfil/template válido para gerar o Nutribook."
                )

            elif not WEBAPP_URL:
                st.error(
                    "Por favor, configure a URL do seu Apps Script Web App no código."
                )

            elif not INSTANCE_NAME:
                st.error(
                    "🔴 WhatsApp não configurado para esta nutricionista."
                )
                st.info(
                    "Entre em **📱 Conectar WhatsApp** para preparar a instância."
                )

            else:
                # Verificação SEM CACHE exatamente no momento do envio.
                with st.spinner("Verificando conexão do WhatsApp..."):
                    verificacao = checar_whatsapp_em_tempo_real(INSTANCE_NAME)

                if not verificacao["conectado"]:
                    st.error("🔴 **WhatsApp não conectado**")
                    st.info(
                        "Conecte ou reconecte o WhatsApp em **📱 Conectar WhatsApp** e tente novamente."
                    )
                else:
                    with st.spinner("Enviando arquivo e registrando pedido..."):
                        try:
                            file_bytes = base64.b64encode(
                                pdf_file.getvalue()
                            ).decode("utf-8")

                            mensagem_whatsapp = (
                                f"Olá, *{nome_paciente}*! 🍎✨\n\n"
                                f"Aqui está o seu *Nutribook*, preparado com muito carinho e 100% personalizado para a sua rotina e seus objetivos! 🥗💪\n\n"
                                f"Dê uma olhada no documento em anexo com calma. Qualquer dúvida que tiver, estou por aqui para te ajudar.\n\n"
                                f"Bora caprichar na alimentação e focar nos resultados! 🚀💚"
                            )

                            payload = {
                                "nome": nome_paciente,
                                "whatsapp": whatsapp_paciente,
                                "perfil": perfil_selecionado,
                                "fileName": pdf_file.name,
                                "fileBase64": file_bytes,
                                "nutriId": NUTRI_ID_LOGADA,
                            }

                            response = requests.post(
                                WEBAPP_URL,
                                json=payload,
                                timeout=30,
                            )

                            try:
                                resposta_json = response.json()
                            except Exception:
                                resposta_json = None

                            if (
                                response.status_code == 200
                                and isinstance(resposta_json, dict)
                                and resposta_json.get("ok") is True
                            ):
                                st.success(
                                    f"✅ Nutribook para **{nome_paciente}** registrado com sucesso!"
                                )

                            elif "<html" in response.text.lower() or "<!doctype" in response.text.lower():
                                st.error("🔴 **Não foi possível concluir o envio.**")
                                st.info(
                                    "O WhatsApp pode ter sido desconectado durante o processamento. "
                                    "Verifique a conexão e consulte o painel antes de tentar novamente."
                                )

                            elif isinstance(resposta_json, dict) and resposta_json.get("message"):
                                st.error(
                                    f"Não foi possível registrar o Nutribook: {resposta_json.get('message')}"
                                )

                            else:
                                st.error(
                                    "Não foi possível registrar o Nutribook. Verifique o WhatsApp e tente novamente."
                                )

                        except requests.exceptions.Timeout:
                            st.error("⏱️ **Tempo limite excedido.**")
                            st.info(
                                "O processamento demorou mais que o esperado. "
                                "Verifique o WhatsApp e consulte o painel antes de tentar novamente."
                            )

                        except requests.exceptions.ConnectionError:
                            st.error("🌐 **Não foi possível comunicar com o Apps Script.**")
                            st.info(
                                "Verifique sua conexão com a internet e tente novamente."
                            )

                        except Exception as e:
                            st.error(
                                "Não foi possível concluir o processamento do Nutribook."
                            )
                            st.caption(f"Detalhe técnico: {e}")


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
        col_nutri = localizar_coluna(
            df_dados,
            ["Nutri_ID", "Nutri ID"]
        )

        if col_nutri:
            df_dados = df_dados[
                df_dados[col_nutri].fillna("").astype(str).str.strip().str.lower()
                == NUTRI_ID_LOGADA.strip().lower()
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

        # ================================================================
        # FONTE OFICIAL DAS MÉTRICAS MENSAIS
        # ================================================================
        #
        # A aba Historico_Nutribooks é a fonte oficial dos números mensais.
        # A aba principal continua sendo usada apenas para o histórico
        # detalhado dos pedidos.
        # ================================================================

        VALOR_NUTRIBOOK = 5.00

        try:
            df_historico = conn.read(
                worksheet="Historico_Nutribooks",
                ttl=0
            )
            df_historico = normalizar_colunas(df_historico)
        except Exception as e:
            df_historico = None
            st.error(
                f"Não foi possível carregar o histórico mensal: {e}"
            )

        total_historico = 0
        total_mes = 0
        faturamento_mes = 0.0
        faturamento_total = 0.0
        historico_pronto = False

        if df_historico is not None and not df_historico.empty:

            c_mes_hist = localizar_coluna(
                df_historico,
                ["Mês", "Mes"]
            )
            c_nutri_hist = localizar_coluna(
                df_historico,
                ["Nutri_ID", "Nutri ID"]
            )
            c_nutribooks_hist = localizar_coluna(
                df_historico,
                ["Nutribooks", "Nutribooks no mês", "Quantidade"]
            )

            if (
                c_mes_hist
                and c_nutri_hist
                and c_nutribooks_hist
            ):

                df_historico = df_historico[
                    df_historico[c_nutri_hist]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                    .str.lower()
                    == NUTRI_ID_LOGADA.strip().lower()
                ].copy()

                if not df_historico.empty:

                    # Aceita 2026-08 em texto ou uma data real do Sheets.
                    df_historico["Mes_Parsed"] = pd.to_datetime(
                        df_historico[c_mes_hist],
                        errors="coerce"
                    )

                    df_historico["Mes_Chave"] = (
                        df_historico["Mes_Parsed"]
                        .dt.strftime("%Y-%m")
                    )

                    df_historico["Quantidade"] = pd.to_numeric(
                        df_historico[c_nutribooks_hist],
                        errors="coerce"
                    ).fillna(0)

                    # Garante uma única linha por mês para o painel.
                    df_historico = (
                        df_historico
                        .dropna(subset=["Mes_Parsed"])
                        .sort_values("Mes_Parsed")
                        .drop_duplicates(
                            subset=["Mes_Chave"],
                            keep="last"
                        )
                        .copy()
                    )

                    if not df_historico.empty:

                        agora = pd.Timestamp.now()
                        mes_atual_chave = agora.strftime("%Y-%m")

                        total_historico = int(
                            df_historico["Quantidade"].sum()
                        )

                        total_mes = int(
                            df_historico.loc[
                                df_historico["Mes_Chave"] == mes_atual_chave,
                                "Quantidade"
                            ].sum()
                        )

                        faturamento_mes = (
                            total_mes * VALOR_NUTRIBOOK
                        )

                        faturamento_total = (
                            total_historico * VALOR_NUTRIBOOK
                        )

                        historico_pronto = True

        # ================================================================
        # KPIs — BASEADOS NO HISTÓRICO MENSAL OFICIAL
        # ================================================================

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)

        with kpi1:
            st.metric(
                "Total Concluídos (Geral)",
                f"{total_historico}"
            )

        with kpi2:
            st.metric(
                "Concluídos no Mês",
                f"{total_mes}"
            )

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

        # ================================================================
        # GRÁFICO — MESMA FONTE DOS KPIs
        # ================================================================

        if historico_pronto:

            df_grafico = (
                df_historico
                .sort_values("Mes_Parsed")
                [["Mes_Parsed", "Quantidade"]]
                .copy()
            )

            df_grafico["Mês/Ano"] = (
                df_grafico["Mes_Parsed"]
                .dt.strftime("%m/%Y")
            )

            st.bar_chart(
                df_grafico.set_index("Mês/Ano")[["Quantidade"]],
                height=260
            )

        elif df_historico is not None and df_historico.empty:
            st.info(
                "Nenhum histórico mensal encontrado para "
                "a nutricionista logada."
            )

        elif df_historico is not None:
            st.error(
                "A aba Historico_Nutribooks não possui as colunas "
                "esperadas para as métricas mensais."
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
        "Gerencie a conexão da Evolution API para disparos automáticos de mensagens."
    )
    st.divider()

    if not INSTANCE_NAME:
        st.warning(
            "⚠️ Nenhuma instância de WhatsApp foi definida para esta nutricionista."
        )
        st.info(
            "Verifique o Nutri_ID no cadastro da nutricionista."
        )

    elif not evolution_configurada():
        st.error(
            "A configuração da Evolution API não foi encontrada nos Secrets do Streamlit."
        )
        st.info(
            "Verifique a seção [evolution] com api_url e api_key."
        )

    else:
        st.caption(
            "Instância utilizada nesta sessão: "
            f"**{INSTANCE_NAME}**"
        )

        col_btn, col_status = st.columns([1, 2])

        with col_btn:
            verificar = st.button(
                "🔄 Verificar Status / Gerar QR Code"
            )

        with st.spinner("Verificando WhatsApp..."):
            preparo = preparar_instancia_para_conexao(INSTANCE_NAME)

        if not preparo["ok"]:
            st.error(
                "Não foi possível preparar a instância do WhatsApp."
            )
            st.info(
                preparo.get(
                    "mensagem",
                    "Verifique a configuração da Evolution API."
                )
            )

        else:
            if preparo.get("criada_agora"):
                st.success(
                    "✅ Instância criada automaticamente na Evolution API."
                )

            base64_qr = None
            pairing_code = None
            code = None

            criacao = preparo.get("criacao")
            if criacao:
                base64_qr, pairing_code, code = extrair_qr_da_resposta(
                    criacao.get("data", {})
                )

            estado = obter_estado_instancia(INSTANCE_NAME)

            if estado["state"] == "open":
                st.success(
                    "🟢 **WhatsApp Conectado e Operacional!**"
                )
                st.info(
                    "Sua instância está pronta para enviar os Nutribooks automaticamente aos pacientes."
                )

            else:
                if not base64_qr:
                    with st.spinner("Preparando QR Code..."):
                        qr_resultado = obter_qr_code_evolution(INSTANCE_NAME)

                    if qr_resultado["ok"]:
                        base64_qr = qr_resultado["base64"]
                        pairing_code = qr_resultado["pairing_code"]
                        code = qr_resultado["code"]

                if base64_qr:
                    st.warning(
                        "🟡 **WhatsApp aguardando pareamento**"
                    )
                    st.write(
                        "Abra o WhatsApp no celular que será conectado, "
                        "entre em **Aparelhos Conectados** e escaneie o QR Code abaixo."
                    )

                    qr_bytes = obter_qr_bytes(base64_qr)
                    if qr_bytes:
                        _, col_qr, _ = st.columns([1, 1, 1])
                        with col_qr:
                            st.image(qr_bytes, width=300)
                    else:
                        st.error(
                            "A Evolution API retornou um QR Code, mas não foi possível decodificar a imagem."
                        )

                    if pairing_code:
                        st.caption(
                            f"Código de pareamento: **{pairing_code}**"
                        )

                else:
                    st.warning(
                        "A instância existe, mas a Evolution API ainda não retornou um QR Code."
                    )
                    st.info(
                        "Clique novamente em **Verificar Status / Gerar QR Code**."
                    )

            if verificar:
                st.toast("Status atualizado.", icon="✅")
