import streamlit as st
from google import genai
import replicate
import importlib

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Plataforma Vértice 🚀 | Jean Victor", layout="centered")

# Visual escuro premium Vértice
st.markdown("""
    <style>
    .stApp { background-color: #0b1120; color: #ffffff; }
    .stButton>button { background-color: #f4c70f; color: #000000; font-weight: bold; border-radius: 6px; width: 100%; height: 48px; border: none; }
    .stSelectbox, .stTextInput, .stRadio { color: #ffffff; }
    </style>
""", unsafe_allow_html=True)

st.title("Plataforma Vértice 🚀")
st.caption("Motor Estratégico de Conteúdo Premium — Jean Victor")

# --- CHAVES DE API ---
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
REPLICATE_API_TOKEN = st.secrets.get("REPLICATE_API_TOKEN", "")

client_gemini = genai.Client(api_key=GEMINI_API_KEY)

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

# --- ESTADOS DO FLUXO (ETAPAS 1 A 8) ---
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
if "estrutura_aprovada" not in st.session_state:
    st.session_state.estrutura_aprovada = False
if "headline_gerada" not in st.session_state:
    st.session_state.headline_gerada = ""

# --- PAINEL REINICIAR ---
if st.sidebar.button("🔄 Iniciar Novo Conteúdo"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- PASSO 0: FORMATO (PERMANENTE) ---
if st.session_state.formato is None:
    st.subheader("Qual formato de conteúdo você deseja criar?")
    fmt = st.radio("Selecione:", ["Post Único (4:5)", "Carrossel (4:5)", "Reels (Apenas Roteiro)"])
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

    # --- ETAPA 2 & 3: IDEIA E PÁGINAS ---
    elif st.session_state.etapa == 2:
        st.subheader("ETAPA 2: Origem da Ideia")
        op = st.radio("Como deseja prosseguir?", ["1️⃣ Já tenho ideia", "2️⃣ Quero sugestões estratégicas"])
        
        paginas = 1
        if st.session_state.formato == "Carrossel (4:5)":
            paginas = st.number_input("ETAPA 3: Quantidade de páginas do carrossel:", min_value=3, max_value=10, value=5)

        if st.button("Avançar para Ideation"):
            st.session_state.opcao_ideia = op
            st.session_state.num_paginas = paginas
            st.session_state.etapa = 4
            st.rerun()

    # --- ETAPA 4: DEFINIÇÃO DO TEMA ---
    elif st.session_state.etapa == 4:
        modulo_produto = importlib.import_module(MAPA_PRODUTOS[st.session_state.produto])
        base_conhecimento = modulo_produto.CONHECIMENTO

        st.subheader(f"ETAPA 4: Definição do Conteúdo — {st.session_state.produto}")
        
        if st.session_state.opcao_ideia == "2️⃣ Quero sugestões estratégicas":
            if st.button("💡 Gerar 5 Ideias Estratégicas"):
                with st.spinner("Analisando base de conhecimento do produto..."):
                    prompt_ideias = f"""
                    Você é o estrategista do Vértice (Jean Victor).
                    Base de Conhecimento do Produto:
                    {base_conhecimento}

                    Gere 5 ideias curtas, provocativas e de alto impacto respeitando 100% as restrições obrigatórias.
                    Distribua entre: Descoberta, Conteúdo Técnico e Posicionamento.
                    Não use linguagem genérica, motivacional ou professoral.
                    """
                    try:
                        res = client_gemini.models.generate_content(
                            model="gemini-2.0-flash",
                            contents=prompt_ideias,
                        )
                        st.markdown(res.text)
                    except Exception as err:
                        st.error(f"Erro na conexão com o Gemini (Etapa 4): {err}")
            
            st.session_state.ideia_escolhida = st.text_input("Cole ou digite a ideia escolhida acima:")
        else:
            st.session_state.ideia_escolhida = st.text_input("Digite a sua ideia/tema para estruturação:")

        if st.session_state.ideia_escolhida:
            if st.button("Avançar para Estruturação Estratégica"):
                st.session_state.etapa = 5
                st.rerun()

    # --- ETAPA 5 & 6: ESTRUTURA E DIREÇÃO VISUAL ---
    elif st.session_state.etapa == 5:
        modulo_produto = importlib.import_module(MAPA_PRODUTOS[st.session_state.produto])
        base_conhecimento = modulo_produto.CONHECIMENTO

        st.subheader("ETAPA 5 & 6: Estrutura Estratégica e Direção Visual")

        with st.spinner("Construindo narrativa de alta retenção com base nas regras..."):
            prompt_estrutura = f"""
            Você é o motor da Plataforma Vértice para o especialista Jean Victor.
            Tema: '{st.session_state.ideia_escolhida}'
            Formato: {st.session_state.formato} ({st.session_state.num_paginas} páginas/slides se carrossel)
            
            BASE DE CONHECIMENTO E REGRAS DO PRODUTO:
            {base_conhecimento}
            
            Regras de Copy:
            - Identifique a Categoria e Objetivo (Atrair, Ensinar ou Fortalecer autoridade).
            - Headline dominante com máximo 12 a 18 palavras NO TOTAL da arte.
            - Predomínio de caixa baixa (70% caixa baixa / 30% caixa alta em termos estratégicos).
            - Tensão, provocação e corte de 50% de textos desnecessários.
            - OBRIGATÓRIO: Forneça a HEADLINE exata da capa/arte.
            - OBRIGATÓRIO: Forneça a LEGENDA completa finalizando rigorosamente com o JARGÃO/CTA OBRIGATÓRIO indicado na base de conhecimento.
            """
            
            if not st.session_state.headline_gerada:
                try:
                    res = client_gemini.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=prompt_estrutura,
                    )
                    conteudo = res.text
                    st.markdown(conteudo)
                    st.session_state.estrutura_rascunho = conteudo
                except Exception as err:
                    st.error(f"Erro na conexão com o Gemini (Etapa 5): {err}")

        st.divider()
        st.subheader("ETAPA 7: Validação de Segurança")
        st.write("Aprova essa estrutura e direção visual? Posso gerar a imagem da arte?")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ SIM, Aprovo! Gerar Imagem"):
                st.session_state.estrutura_aprovada = True
                st.session_state.etapa = 8
                st.rerun()
        with col2:
            if st.button("❌ Refazer Estrutura"):
                st.session_state.headline_gerada = ""
                st.rerun()

    # --- ETAPA 8: EXECUÇÃO VISUAL (FLUX.1 [DEV]) ---
    elif st.session_state.etapa == 8:
        st.subheader("ETAPA 8: Renderização Visual Vértice")
        
        if st.session_state.formato == "Reels (Apenas Roteiro)":
            st.success("O Roteiro para Reels foi concluído na etapa anterior (sem geração de imagem conforme regra).")
        else:
            with st.spinner("Renderizando arte no FLUX.1 [dev] no padrão Vértice..."):
                prompt_flux = f"""
                {config_perfil['prompt_visual_flux']}
                Topic/Headline: '{st.session_state.ideia_escolhida}'.
                """

                rep_client = replicate.Client(api_token=REPLICATE_API_TOKEN)
                
                output = rep_client.run(
                    "black-forest-labs/flux-dev",
                    input={
                        "prompt": prompt_flux,
                        "aspect_ratio": "4:5",
                        "output_format": "png",
                        "guidance": 3.5
                    }
                )
                
                image_url = output[0] if isinstance(output, list) else output

                st.image(image_url, caption=f"Arte Final Vértice — Proporção {config_perfil['proporcao']}", use_column_width=True)
                st.markdown(f"[📥 Baixar Arte em Alta Resolução (PNG)]({image_url})")

        st.divider()
        st.subheader("📝 Rascunho & Legenda Estratégica:")
        if "estrutura_rascunho" in st.session_state:
            st.markdown(st.session_state.estrutura_rascunho)
