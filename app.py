import streamlit as st
import google.generativeai as genai
import replicate
import importlib
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Plataforma Vértice | Jean Victor", layout="centered")

# CSS Customizado com Fonte Montserrat e Paleta Vértice
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&display=swap');

    html, body, [class*="css"], .stApp {
        font-family: 'Montserrat', sans-serif !important;
        background-color: #020b18;
        color: #ffffff;
    }

    /* REDUZ O PADDING SUPERIOR PADRÃO DO STREAMLIT */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 900px;
    }

    [data-testid="stSidebar"] { 
        background-color: #0a192f; 
    }
    
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.5rem !important;
    }
    
    /* ESTILO DOS BOTÕES PADRÃO */
    .stButton>button { 
        background-color: #f4c70f; 
        color: #000000; 
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 700; 
        border-radius: 6px; 
        width: 100%; 
        min-height: 48px;
        height: auto;
        border: none; 
        padding: 10px 15px;
    }

    /* ESTILO ESPECÍFICO PARA OS BOTÕES DE SELEÇÃO DE IDEIAS (LEITURA LIMPA E CLARA) */
    div[data-testid="stVerticalBlock"] div.stButton > button {
        background-color: #0e2447 !important;
        color: #ffffff !important;
        border: 1px solid #f4c70f !important;
        font-weight: 600 !important;
        text-align: left !important;
        line-height: 1.4 !important;
        transition: all 0.2s ease-in-out;
    }

    div[data-testid="stVerticalBlock"] div.stButton > button:hover {
        background-color: #f4c70f !important;
        color: #000000 !important;
        border-color: #f4c70f !important;
    }

    div[data-testid="stVerticalBlock"] div.stButton > button:focus, 
    div[data-testid="stVerticalBlock"] div.stButton > button:active {
        background-color: #1a365d !important;
        color: #ffffff !important;
        border-color: #f4c70f !important;
        box-shadow: 0 0 8px rgba(244, 199, 15, 0.4) !important;
    }
    
    .stSelectbox, .stTextInput, .stRadio { 
        font-family: 'Montserrat', sans-serif !important;
        color: #ffffff; 
    }
    
    div[data-baseweb="radio"] label { 
        font-family: 'Montserrat', sans-serif !important;
        color: #ffffff !important; 
    }

    /* Cabeçalho Principal */
    h1.titulo-vertice {
        color: #f4c70f !important;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 900 !important;
        font-size: 3.2rem !important;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.0 !important;
        letter-spacing: -1px !important;
    }
    
    p.subtitulo-vertice {
        color: #8892b0 !important;
        font-family: 'Montserrat', sans-serif !important;
        font-size: 1.1rem !important;
        margin-top: 4px !important;
        margin-bottom: 0px !important;
        font-weight: 500 !important;
    }

    /* Reduz espaçamento do divisor */
    hr {
        margin-top: 0.8rem !important;
        margin-bottom: 1rem !important;
        border-color: #1e2d4a !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- LOGO & TÍTULO (ALINHAMENTO COMPACTO) ---
col_logo, col_titulo = st.columns([1, 3.5], vertical_alignment="center")

with col_logo:
    try:
        st.image("logo.png", width=125)
    except Exception:
        pass

with col_titulo:
    st.markdown('<h1 class="titulo-vertice">Plataforma Vértice</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitulo-vertice">Motor Estratégico de Conteúdo Premium — Jean Victor</p>', unsafe_allow_html=True)

st.write("---")

# --- CHAVES DE API ---
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
REPLICATE_API_TOKEN = st.secrets.get("REPLICATE_API_TOKEN", "")

# Configura o Gemini com alias dinâmico
genai.configure(api_key=GEMINI_API_KEY)
model_gemini = genai.GenerativeModel("gemini-flash-latest")

# --- CARREGA CONFIGURAÇÃO VISUAL DO PERFIL ---
try:
    config_perfil = importlib.import_module("profiles.jean_victor.config").CONFIG
except Exception as e:
    st.error(f"Erro ao carregar configurações do perfil: {e}")
    st.stop()

# --- MAPEAMENTO DOS PRODUTOS / BASES DE CONHECIMENTO ---
MAPA_PRODUTOS = {
    "1️⃣ Dados": "profiles.jean_victor.dados",
    "2️⃣ Apresentações Profissionais": "profiles.jean_victor.apresentacoes",
    "3️⃣ Plataforma Vértice": "profiles.jean_victor.vertice",
    "4️⃣ Método 5P": "profiles.jean_victor.metodo5p",
    "5️⃣ Nutribook": "profiles.jean_victor.nutribook"
}

# --- ESTADOS DO FLUXO ---
if "etapa" not in st.session_state:
    st.session_state.etapa = 1
if "formato" not in st.session_state:
    st.session_state.formato = None
if "produto" not in st.session_state:
    st.session_state.produto = None
if "opcao_ideia" not in st.session_state:
    st.session_state.opcao_ideia = None
if "num_paginas" not in st.session_state:
    st.session_state.num_paginas = 1
if "ideia_escolhida" not in st.session_state:
    st.session_state.ideia_escolhida = ""
if "ideias_lista" not in st.session_state:
    st.session_state.ideias_lista = []
if "estrutura_rascunho" not in st.session_state:
    st.session_state.estrutura_rascunho = None
if "imagem_gerada_url" not in st.session_state:
    st.session_state.imagem_gerada_url = None

# --- PAINEL SIDEBAR ---
with st.sidebar:
    try:
        st.image("logo.png", use_container_width=True)
    except Exception:
        pass
    st.write("---")
    if st.button("🔄 Iniciar Novo Conteúdo"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- PASSO 0: FORMATO (TELA INICIAL) ---
if st.session_state.formato is None:
    st.subheader("Olá Jean Victor! O que vamos criar hoje?")
    fmt = st.radio("Selecione o formato:", ["Post Único (4:5)", "Carrossel (4:5)", "Reels (Apenas Roteiro)"])
    if st.button("Confirmar Formato"):
        st.session_state.formato = fmt
        st.rerun()

else:
    st.info(f"📌 Formato selecionado: **{st.session_state.formato}**")

    # --- ETAPA 1: ESCOLHA DO PRODUTO ---
    if st.session_state.etapa == 1:
        st.subheader("ETAPA 1: Qual é o Produto?")
        prod = st.radio("Selecione uma das opções abaixo:", list(MAPA_PRODUTOS.keys()))
        if st.button("Avançar para Etapa 2"):
            st.session_state.produto = prod
            st.session_state.etapa = 2
            st.rerun()

    # --- ETAPA 2 & 3: ORIGEM DA IDEIA ---
    elif st.session_state.etapa == 2:
        st.subheader("ETAPA 2: Origem da Ideia")
        op = st.radio("Como deseja prosseguir?", ["1️⃣ Já tenho ideia", "2️⃣ Quero ideias estratégicas"])
        
        paginas = 1
        if st.session_state.formato == "Carrossel (4:5)":
            paginas = st.number_input("ETAPA 3: Quantidade de páginas do carrossel:", min_value=3, max_value=10, value=5)

        if st.button("Avançar para Ideação"):
            st.session_state.opcao_ideia = op
            st.session_state.num_paginas = paginas
            st.session_state.etapa = 4
            st.rerun()

    # --- ETAPA 4: DEFINIÇÃO DO CONTEÚDO ---
    elif st.session_state.etapa == 4:
        modulo_produto = importlib.import_module(MAPA_PRODUTOS[st.session_state.produto])
        base_conhecimento = modulo_produto.CONHECIMENTO

        st.subheader(f"ETAPA 4: Definição do Conteúdo — {st.session_state.produto}")
        
        if st.session_state.opcao_ideia == "2️⃣ Quero ideias estratégicas":
            if st.button("💡 Gerar 5 Ideias Estratégicas"):
                with st.spinner("Analisando base de conhecimento do produto..."):
                    prompt_ideias = f"""
                    Você é o estrategista de conteúdo do especialista Jean Victor.
                    Base de Conhecimento do Produto:
                    {base_conhecimento}

                    Gere exatamente 5 ideias curtas, provocativas e de alto impacto de temas para o post.
                    REGRA CRÍTICA: NÃO inclua bordão, slogan, CTA ou frases de encerramento no final das ideias. Apenas o tema/ideia central de forma direta.
                    Responda estritamente em formato de lista numerada simples (1. Ideia, 2. Ideia...).
                    """
                    try:
                        res = model_gemini.generate_content(prompt_ideias)
                        linhas = [line.strip() for line in res.text.split("\n") if line.strip() and line.strip()[0].isdigit()]
                        st.session_state.ideias_lista = linhas if len(linhas) > 0 else [res.text]
                    except Exception as err:
                        st.error(f"Erro na conexão com o Gemini (Etapa 4): {err}")

            if st.session_state.ideias_lista:
                st.write("---")
                st.write("**Clique na ideia escolhida para avançar:**")
                for i, idx_ideia in enumerate(st.session_state.ideias_lista):
                    if st.button(f"{idx_ideia}", key=f"btn_ideia_{i}"):
                        st.session_state.ideia_escolhida = idx_ideia
                        st.session_state.estrutura_rascunho = None # Reseta o rascunho anterior
                        st.session_state.imagem_gerada_url = None
                        st.session_state.etapa = 5
                        st.rerun()

        else:
            st.session_state.ideia_escolhida = st.text_input("Digite a sua ideia/tema para estruturação:")
            if st.session_state.ideia_escolhida:
                if st.button("Avançar para Estruturação Estratégica"):
                    st.session_state.estrutura_rascunho = None
                    st.session_state.imagem_gerada_url = None
                    st.session_state.etapa = 5
                    st.rerun()

    # --- ETAPA 5 & 6: ESTRUTURA E DIREÇÃO VISUAL ---
    elif st.session_state.etapa == 5:
        modulo_produto = importlib.import_module(MAPA_PRODUTOS[st.session_state.produto])
        base_conhecimento = modulo_produto.CONHECIMENTO

        st.subheader("ETAPA 5 & 6: Estrutura Estratégica e Direção Visual")

        if not st.session_state.estrutura_rascunho:
            with st.spinner("Construindo narrativa de alta retenção..."):
                
                # Regra do Bordão apenas para Reels
                regra_bordao = ""
                if st.session_state.formato == "Reels (Apenas Roteiro)":
                    regra_bordao = "- OBRIGATÓRIO: Forneça a LEGENDA/ROTEIRO completa finalizando rigorosamente com o JARGÃO/CTA OBRIGATÓRIO indicado na base de conhecimento."
                else:
                    regra_bordao = "- NÃO utilize bordão fixo ao final da legenda/post a menos que seja um roteiro de Reels."

                prompt_estrutura = f"""
                Você é o motor da Plataforma Vértice para o especialista Jean Victor.
                Tema: '{st.session_state.ideia_escolhida}'
                Formato: {st.session_state.formato} ({st.session_state.num_paginas} páginas se carrossel)
                
                BASE DE CONHECIMENTO E REGRAS DO PRODUTO:
                {base_conhecimento}
                
                Regras de Copy:
                - Identifique a Categoria e Objetivo (Atrair, Ensinar ou Fortalecer autoridade).
                - Headline dominante com máximo 12 a 18 palavras NO TOTAL da arte.
                - Predomínio de caixa baixa (70% caixa baixa / 30% caixa alta em termos estratégicos).
                - Tensão, provocação e corte de 50% de textos desnecessários.
                - OBRIGATÓRIO: Forneça a HEADLINE exata da capa/arte.
                {regra_bordao}
                """
                try:
                    res = model_gemini.generate_content(prompt_estrutura)
                    st.session_state.estrutura_rascunho = res.text
                    st.rerun()
                except Exception as err:
                    st.error(f"Erro na conexão com o Gemini (Etapa 5): {err}")

        if st.session_state.estrutura_rascunho:
            st.markdown(st.session_state.estrutura_rascunho)

            st.divider()
            st.subheader("ETAPA 7: Validação de Segurança")
            st.write("Aprova essa estrutura e direção visual? Posso gerar a imagem da arte?")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ SIM, Aprovo! Gerar Imagem"):
                    st.session_state.etapa = 8
                    st.rerun()
            with col2:
                if st.button("❌ Refazer Estrutura"):
                    st.session_state.estrutura_rascunho = None
                    st.rerun()

    # --- ETAPA 8: EXECUÇÃO VISUAL ---
    elif st.session_state.etapa == 8:
        st.subheader("ETAPA 8: Renderização Visual Vértice")
        
        if st.session_state.formato == "Reels (Apenas Roteiro)":
            st.success("O Roteiro para Reels foi concluído na etapa anterior.")
        else:
            if not st.session_state.imagem_gerada_url:
                with st.spinner("Renderizando arte no FLUX.1 [dev] no padrão Vértice (Aguarde até 45s)..."):
                    try:
                        prompt_flux = f"""
                        {config_perfil['prompt_visual_flux']}
                        Topic/Headline: '{st.session_state.ideia_escolhida}'.
                        """

                        rep_client = replicate.Client(api_token=REPLICATE_API_TOKEN, timeout=120)
                        
                        output = rep_client.run(
                            "black-forest-labs/flux-dev",
                            input={
                                "prompt": prompt_flux,
                                "aspect_ratio": "4:5",
                                "output_format": "png",
                                "guidance": 3.5
                            }
                        )
                        
                        image_url = str(output[0]) if isinstance(output, list) else str(output)
                        st.session_state.imagem_gerada_url = image_url

                    except Exception as err:
                        st.error(f"Erro ao gerar a imagem no Replicate: {err}")
                        if st.button("🔄 Tentar Gerar Novamente"):
                            st.rerun()

            if st.session_state.imagem_gerada_url:
                st.image(st.session_state.imagem_gerada_url, caption=f"Arte Final Vértice — Proporção {config_perfil['proporcao']}", use_container_width=True)
                st.markdown(f"[📥 Baixar Arte em Alta Resolução (PNG)]({st.session_state.imagem_gerada_url})")

        st.divider()
        st.subheader("📝 Rascunho & Legenda Estratégica:")
        if st.session_state.estrutura_rascunho:
            st.markdown(st.session_state.estrutura_rascunho)
