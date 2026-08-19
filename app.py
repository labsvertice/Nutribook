import importlib
import io
import os
import re
import time
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai
import replicate
import requests
import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Plataforma Vértice | Jean Victor", layout="centered"
)

# CSS Customizado com Fonte Montserrat e Paleta Vértice
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
    
    /* BOTÕES PADRÃO */
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

    /* BOTÕES DE SELEÇÃO DE IDEIAS */
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

# --- CHAVES DE API ---
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
REPLICATE_API_TOKEN = st.secrets.get("REPLICATE_API_TOKEN", "")


# --- FUNÇÃO DE MOTOR TIPOGRÁFICO VIA CÓDIGO (PADRÃO AGÊNCIA) ---
def baixar_fonte_montserrat():
  """Baixa a fonte Montserrat-Bold oficial direto do Google Fonts."""
  caminho_fonte = "Montserrat-Bold.ttf"
  if not os.path.exists(caminho_fonte):
    url_fonte = "https://github.com/google/fonts/raw/main/ofl/montserrat/static/Montserrat-Bold.ttf"
    try:
      res = requests.get(url_fonte, timeout=10)
      if res.status_code == 200:
        with open(caminho_fonte, "wb") as f:
          f.write(res.content)
    except Exception:
      pass
  return caminho_fonte if os.path.exists(caminho_fonte) else None


def aplicar_tipografia_codigo(
    image_bytes: bytes, headline_texto: str
) -> Image.Image:
  """Desenha a headline em Montserrat com cor Amarelo Vértice e alto contraste."""
  img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
  draw = ImageDraw.Draw(img)
  largura_img, altura_img = img.size

  # Carrega fonte Montserrat na escala correta da imagem
  caminho_fonte = baixar_fonte_montserrat()
  tamanho_fonte = int(largura_img * 0.075)  # 7.5% da largura da imagem

  try:
    if caminho_fonte:
      font = ImageFont.truetype(caminho_fonte, tamanho_fonte)
    else:
      font = ImageFont.load_default()
  except Exception:
    font = ImageFont.load_default()

  # Tratamento da headline (Caixa Alta e Quebra de Linhas)
  texto_limpo = headline_texto.upper().replace('"', "").replace("*", "").strip()
  palavras = texto_limpo.split()
  linhas = []
  linha_atual = []

  for p in palavras:
    linha_atual.append(p)
    if len(" ".join(linha_atual)) > 15:
      linhas.append(" ".join(linha_atual[:-1]))
      linha_atual = [p]
  if linha_atual:
    linhas.append(" ".join(linha_atual))

  # Posição vertical inicial (Topo com margem proporcional)
  y_pos = int(altura_img * 0.08)
  cor_texto = (244, 199, 15)  # Amarelo Ouro (#f4c70f)
  cor_sombra = (2, 11, 24)  # Azul Escuro (#020b18)

  for linha in linhas:
    bbox = draw.textbbox((0, 0), linha, font=font)
    largura_texto = bbox[2] - bbox[0]
    altura_linha = bbox[3] - bbox[1]
    x_pos = (largura_img - largura_texto) // 2

    # Sombra de alto contraste (múltiplos offsets para criar borda espessa)
    espessura_sombra = max(3, tamanho_fonte // 15)
    for dx in range(-espessura_sombra, espessura_sombra + 1):
      for dy in range(-espessura_sombra, espessura_sombra + 1):
        draw.text((x_pos + dx, y_pos + dy), linha, font=font, fill=cor_sombra)

    # Texto principal em Amarelo Vértice
    draw.text((x_pos, y_pos), linha, font=font, fill=cor_texto)

    y_pos += altura_linha + int(tamanho_fonte * 0.3)

  return img


def limpar_rascunho_exibicao(texto: str) -> str:
  linhas = texto.split("\n")
  resultado = []
  ignorar = False
  for linha in linhas:
    if "PROMPT VISUAL IDEOGRAM" in linha.upper():
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
      "gemini-3.5-flash-lite", generation_config={"temperature": 0.95}
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
  model = genai.GenerativeModel("gemini-3.5-flash-lite")

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

    📌 **TEXTO DA ARTE / CARROSSEL**
    HEADLINE CAPA:
    [Escreva a frase principal provocativa]

    SUBTEXTOS DE APOIO:
    | [frase curta 1]
    | [frase curta 2]

    PROMPT VISUAL IDEOGRAM (EM INGLÊS):
    [Descrição em inglês da cena corporativa em azul marinho e dourado. Especifique NENHUM TEXTO NA IMAGEM. Finalize com: 'clean background, corporate photography, cinematic lighting, NO TEXT, NO WORDS, NO LOGOS, NO WATERMARKS']

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

# --- PASSO 0: FORMATO ---
if st.session_state.formato is None:
  st.subheader("Olá Jean Victor! O que vamos criar hoje?")
  fmt = st.radio(
      "Selecione o formato:",
      ["Post Único (4:5)", "Carrossel (4:5)", "Reels (Apenas Roteiro)"],
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
    paginas = 5 if st.session_state.formato == "Carrossel (4:5)" else 1
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
      if st.button("✅ Aprovar e Gerar Arte"):
        st.session_state.etapa = 8
        st.rerun()
    with col2:
      if st.button("❌ Refazer Estrutura"):
        st.session_state.estrutura_rascunho = None
        st.rerun()

  elif st.session_state.etapa == 8:
    st.subheader(
        "ETAPA 8: Renderização Agência Vértice (Imagem Limpa + Tipografia"
        " Montserrat)"
    )

    if not st.session_state.imagem_processada_bytes:
      with st.spinner(
          "Gerando imagem de fundo e aplicando tipografia oficial..."
      ):
        try:
          # Prompt sem texto para a IA de imagem
          prompt_fundo = (
              "A stressed corporate executive sitting at a modern glass desk,"
              " surrounded by multiple glowing monitors with messy"
              " spreadsheets. Deep dark navy blue office background, warm"
              " golden lighting accents, cinematic atmosphere, photorealistic"
              " 8k, NO TEXT, NO WORDS, NO LOGOS, NO WATERMARKS, clean background"
              " composition."
          )

          if (
              st.session_state.estrutura_rascunho
              and "PROMPT VISUAL IDEOGRAM"
              in st.session_state.estrutura_rascunho.upper()
          ):
            lines = st.session_state.estrutura_rascunho.split("\n")
            for idx, line in enumerate(lines):
              if (
                  "PROMPT VISUAL IDEOGRAM" in line.upper()
                  and idx + 1 < len(lines)
              ):
                prox = lines[idx + 1].strip()
                if prox:
                  prompt_fundo = (
                      prox
                      + ", clean background composition, NO TEXT, NO WORDS, NO"
                      " LOGOS, NO WATERMARKS"
                  )
                  break

          output = replicate.run(
              "ideogram-ai/ideogram-v2",
              input={
                  "prompt": prompt_fundo,
                  "aspect_ratio": "3:4",
                  "style_type": "Design",
                  "magic_prompt_option": "Auto",
              },
          )
          image_url = str(output[0]) if isinstance(output, list) else str(output)
          raw_bytes = requests.get(image_url).content

          # Extrai a headline do rascunho de forma garantida
          headline_texto = st.session_state.ideia_escolhida
          if st.session_state.estrutura_rascunho:
            for line in st.session_state.estrutura_rascunho.split("\n"):
              if "HEADLINE CAPA" in line.upper():
                partes = line.split(":")
                if len(partes) > 1 and partes[1].strip():
                  headline_texto = partes[1].strip()
                  break

          # Aplica a tipografia perfeita via código
          img_final = aplicar_tipografia_codigo(raw_bytes, headline_texto)

          buf = io.BytesIO()
          img_final.save(buf, format="PNG")
          st.session_state.imagem_processada_bytes = buf.getvalue()
          st.rerun()

        except Exception as err:
          st.error(f"Erro no processamento da imagem: {err}")

    if st.session_state.imagem_processada_bytes:
      col_esq, col_centro, col_dir = st.columns([0.8, 2, 0.8])
      with col_centro:
        st.image(
            st.session_state.imagem_processada_bytes,
            caption="Arte Final Vértice (Zero Erro Tipográfico)",
            use_container_width=True,
        )

      st.download_button(
          label="📥 Baixar Arte Final (PNG Alta Resolução)",
          data=st.session_state.imagem_processada_bytes,
          file_name="vertice_arte_final.png",
          mime="image/png",
      )

    st.divider()
    st.subheader("📝 Rascunho & Legenda Estratégica:")
    if st.session_state.estrutura_rascunho:
      st.markdown(limpar_rascunho_exibicao(st.session_state.estrutura_rascunho))
