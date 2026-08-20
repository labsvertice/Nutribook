import importlib
import io
import os
import time
import google.generativeai as genai
from PIL import Image
import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Plataforma Vértice | Jean Victor", layout="centered"
)

# CSS Customizado - Identidade Visual Vértice
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&display=swap');

    html, body, [class*="css"], .stApp {
        font-family: 'Montserrat', sans-serif !important;
        background-color: #020b18;
        color: #ffffff;
    }

    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 900px;
    }

    [data-testid="stSidebar"] { 
        background-color: #0a192f; 
    }
    
    .stButton>button, .stDownloadButton>button { 
        background-color: #f4c70f !important; 
        color: #000000 !important; 
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 700 !important; 
        border-radius: 6px !important; 
        width: 100% !important; 
        min-height: 48px !important;
        border: none !important; 
        padding: 10px 15px !important;
    }

    div[data-testid="stVerticalBlock"] div.stButton > button {
        background-color: #0e2447 !important;
        color: #ffffff !important;
        border: 1px solid #f4c70f !important;
        font-weight: 600 !important;
        text-align: left !important;
        line-height: 1.4 !important;
    }

    div[data-testid="stVerticalBlock"] div.stButton > button:hover {
        background-color: #f4c70f !important;
        color: #000000 !important;
    }

    h1.titulo-vertice {
        color: #f4c70f !important;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 900 !important;
        font-size: 3.2rem !important;
        margin: 0 !important;
        line-height: 1.0 !important;
    }
    
    p.subtitulo-vertice {
        color: #8892b0 !important;
        font-family: 'Montserrat', sans-serif !important;
        font-size: 1.1rem !important;
        margin-top: 4px !important;
    }

    hr { border-color: #1e2d4a !important; }
    </style>
""",
    unsafe_allow_html=True,
)

# --- CABEÇALHO ---
col_logo, col_titulo = st.columns([1, 3.5], vertical_alignment="center")
with col_logo:
  try:
    st.image("logo.png", width=125)
  except Exception:
    pass

with col_titulo:
  st.markdown(
      '<h1 class="titulo-vertice">Plataforma Vértice</h1>',
      unsafe_allow_html=True,
  )
  st.markdown(
      '<p class="subtitulo-vertice">Motor Estratégico de Conteúdo Premium —'
      " Jean Victor</p>",
      unsafe_allow_html=True,
  )

st.write("---")

# --- CONFIGURAÇÃO DA CHAVE GOOGLE API ---
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
  genai.configure(api_key=GEMINI_API_KEY)


def limpar_rascunho_exibicao(texto: str) -> str:
  linhas = texto.split("\n")
  resultado = []
  ignorar = False
  for linha in linhas:
    if "PROMPT VISUAL" in linha.upper():
      ignorar = True
      continue
    if ignorar and (
        linha.startswith("📌") or "LEGENDA DO POST" in linha.upper()
    ):
      ignorar = False
    if not ignorar:
      resultado.append(linha)
  return "\n".join(resultado)


def gerar_ideias_gemini(api_key: str, base_conhecimento: str) -> list:
  genai.configure(api_key=api_key)
  model = genai.GenerativeModel(
      "gemini-2.5-flash", generation_config={"temperature": 0.95}
  )
  prompt = (
      f"Estrategista Jean Victor. Base: {base_conhecimento}. Seed: {time.time()}."
      " Gere 5 ideias ÚNICAS e VARIADAS. Formato numerado: 1. Ideia"
  )
  res = model.generate_content(prompt)
  linhas = [
      line.strip()
      for line in res.text.split("\n")
      if line.strip() and line.strip()[0].isdigit()
  ]
  return linhas if linhas else [res.text]


@st.cache_data(show_spinner=False)
def gerar_estrutura_gemini(
    api_key: str, ideia: str, formato: str, paginas: int, base_conhecimento: str
) -> str:
  genai.configure(api_key=api_key)
  model = genai.GenerativeModel("gemini-2.5-flash")

  prompt = f"""
    Você é o estrategista de copy do Jean Victor.
    Tema: '{ideia}'
    Formato: {formato} ({paginas} páginas se carrossel)
    
    BASE DE CONHECIMENTO DO PRODUTO:
    {base_conhecimento}
    
    REGRAS DA LEGENDA:
    1. MÁXIMO DE 4 A 7 PALAVRAS POR LINHA.
    2. CADA FRASE EM UMA LINHA ISOLADA.

    ESTRUTURA DE SAÍDA:

    📌 **TEXTO DA ARTE / CAPA**
    HEADLINE CAPA:
    [Escreva a frase principal provocativa em caixa alta, curta e de alto impacto]

    📌 **LEGENDA DO POST**
    [Legenda em linhas curtas e encerramento oficial]
    """
  res = model.generate_content(prompt)
  return res.text


# --- CARREGA CONFIGURAÇÃO DO PERFIL ---
try:
  config_perfil = importlib.import_module("profiles.jean_victor.config").CONFIG
except Exception:
  st.error("Erro ao carregar configurações do perfil.")
  st.stop()

MAPA_PRODUTOS = {
    "1️⃣ Dados": "profiles.jean_victor.dados",
    "2️⃣ Apresentações Profissionais": "profiles.jean_victor.apresentacoes",
    "3️⃣ Plataforma Vértice": "profiles.jean_victor.vertice",
    "4️⃣ Método 5P": "profiles.jean_victor.metodo5p",
    "5️⃣ Nutribook": "profiles.jean_victor.nutribook",
}

# --- ESTADOS DO FLUXO ---
for key in [
    "etapa",
    "formato",
    "produto",
    "opcao_ideia",
    "num_paginas",
    "ideia_escolhida",
    "ideias_lista",
    "estrutura_rascunho",
    "imagem_processada_bytes",
]:
  if key not in st.session_state:
    st.session_state[key] = 1 if key == "etapa" else None

# --- SIDEBAR ---
with st.sidebar:
  try:
    st.image("logo.png", use_container_width=True)
  except Exception:
    pass
  st.write("---")
  if st.button("🔄 Iniciar Novo Conteúdo"):
    for k in list(st.session_state.keys()):
      del st.session_state[k]
    st.rerun()

# --- FLUXO PRINCIPAL ---
if st.session_state.formato is None:
  st.subheader("Olá Jean Victor! O que vamos criar hoje?")
  fmt = st.radio(
      "Selecione o formato:",
      ["Post Único (3:4)", "Carrossel (3:4)", "Reels (Apenas Roteiro)"],
  )
  if st.button("Confirmar Formato"):
    st.session_state.formato = fmt
    st.rerun()
else:
  st.info(f"📌 Formato selecionado: **{st.session_state.formato}**")

  if st.session_state.etapa == 1:
    st.subheader("ETAPA 1: Qual é o Produto?")
    prod = st.radio("Selecione:", list(MAPA_PRODUTOS.keys()))
    if st.button("Avançar para Etapa 2"):
      st.session_state.produto = prod
      st.session_state.etapa = 2
      st.rerun()

  elif st.session_state.etapa == 2:
    st.subheader("ETAPA 2: Origem da Ideia")
    op = st.radio(
        "Como deseja prosseguir?",
        ["1️⃣ Já tenho ideia", "2️⃣ Quero ideias estratégicas"],
    )
    paginas = 5 if "Carrossel" in st.session_state.formato else 1
    if st.button("Avançar para Ideação"):
      st.session_state.opcao_ideia = op
      st.session_state.num_paginas = paginas
      st.session_state.etapa = 4
      st.rerun()

  elif st.session_state.etapa == 4:
    modulo = importlib.import_module(MAPA_PRODUTOS[st.session_state.produto])
    st.subheader(f"ETAPA 4: Definição do Conteúdo — {st.session_state.produto}")

    if st.session_state.opcao_ideia == "2️⃣ Quero ideias estratégicas":
      if not st.session_state.ideias_lista:
        st.session_state.ideias_lista = gerar_ideias_gemini(
            GEMINI_API_KEY, modulo.CONHECIMENTO
        )
        st.rerun()

      for i, idx_ideia in enumerate(st.session_state.ideias_lista):
        if st.button(f"{idx_ideia}", key=f"btn_ideia_{i}"):
          st.session_state.ideia_escolhida = idx_ideia
          st.session_state.etapa = 5
          st.rerun()
    else:
      st.session_state.ideia_escolhida = st.text_input("Digite a sua ideia:")
      if st.session_state.ideia_escolhida and st.button("Avançar"):
        st.session_state.etapa = 5
        st.rerun()

  elif st.session_state.etapa == 5:
    modulo = importlib.import_module(MAPA_PRODUTOS[st.session_state.produto])
    st.subheader("ETAPA 5: Estrutura Estratégica")

    if not st.session_state.estrutura_rascunho:
      st.session_state.estrutura_rascunho = gerar_estrutura_gemini(
          GEMINI_API_KEY,
          st.session_state.ideia_escolhida,
          st.session_state.formato,
          st.session_state.num_paginas,
          modulo.CONHECIMENTO,
      )
      st.rerun()

    st.markdown(limpar_rascunho_exibicao(st.session_state.estrutura_rascunho))
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
      if st.button("✅ Aprovar e Gerar Foto de Fundo"):
        st.session_state.etapa = 8
        st.rerun()
    with col2:
      if st.button("❌ Refazer Estrutura"):
        st.session_state.estrutura_rascunho = None
        st.rerun()

  elif st.session_state.etapa == 8:
    st.subheader("ETAPA 8: Fotografia de Fundo Premium (Google Imagen 3)")

    if not st.session_state.imagem_processada_bytes:
      with st.spinner(
          "Google Imagen 3 gerando fotografia corporativa de alta resolução..."
      ):
        try:
          # Prompt fotográfico realista e limpo sem texto distorcido
          prompt_imagem = (
              "A high-end, realistic editorial photograph of a dark navy blue"
              " executive boardroom, modern luxury furniture, subtle yellow"
              " ambient lighting, cinematic focus, ultra detailed, minimalist"
              " luxury atmosphere, no text, 35mm photograph."
          )

          imagen_model = genai.ImageGenerationModel("imagen-3.0-generate-002")
          result = imagen_model.generate_images(
              prompt=prompt_imagem,
              number_of_images=1,
              aspect_ratio="3:4",
              output_mime_type="image/png",
          )

          pil_img = result.images[0]._pil_image
          buf = io.BytesIO()
          pil_img.save(buf, format="PNG")

          st.session_state.imagem_processada_bytes = buf.getvalue()
          st.rerun()

        except Exception as err:
          st.error(f"Erro na geração com Imagen 3: {err}")

    if st.session_state.imagem_processada_bytes:
      col_esq, col_centro, col_dir = st.columns([0.5, 2, 0.5])
      with col_centro:
        st.image(
            st.session_state.imagem_processada_bytes,
            caption="Fotografia Corporativa Base (Google Imagen 3)",
            use_container_width=True,
        )

      st.download_button(
          label="📥 Baixar Imagem HD (PNG 3:4)",
          data=st.session_state.imagem_processada_bytes,
          file_name="vertice_imagem_fundo.png",
          mime="image/png",
      )

    st.divider()
    st.subheader("📝 Legenda do Post para Copiar e Publicar:")
    if st.session_state.estrutura_rascunho:
      st.markdown(limpar_rascunho_exibicao(st.session_state.estrutura_rascunho))
