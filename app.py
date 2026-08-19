import io
import os
import re
import importlib
from typing import Optional

import requests
import replicate
import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont, ImageEnhance


# ============================================================
# CONFIGURAÇÃO DA PÁGINA — INTERFACE PRESERVADA
# ============================================================

st.set_page_config(
    page_title="Plataforma Vértice 🚀 | Jean Victor",
    layout="centered",
)

st.markdown(
    """
    <style>
    .stApp { background-color:#0b1120; color:#ffffff; }

    .stButton > button {
        background-color:#0e2447 !important;
        color:#ffffff !important;
        border:1px solid #f4c70f !important;
        font-weight:600 !important;
        text-align:left !important;
        line-height:1.4 !important;
    }

    .stButton > button:hover {
        background-color:#f4c70f !important;
        color:#000000 !important;
    }

    h1.titulo-vertice {
        color:#f4c70f !important;
        font-family:'Montserrat',sans-serif !important;
        font-weight:900 !important;
        font-size:3.2rem !important;
        margin:0 !important;
        line-height:1.0 !important;
    }

    p.subtitulo-vertice {
        color:#8892b0 !important;
        font-family:'Montserrat',sans-serif !important;
        font-size:1.1rem !important;
        margin-top:4px !important;
    }

    hr { border-color:#1e2d4a !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

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
        '<p class="subtitulo-vertice">'
        'Motor Estratégico de Conteúdo Premium — Jean Victor'
        '</p>',
        unsafe_allow_html=True,
    )

st.write("---")


# ============================================================
# CHAVES
# ============================================================

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
REPLICATE_API_TOKEN = st.secrets.get("REPLICATE_API_TOKEN", "")


# ============================================================
# IDENTIDADE VISUAL VÉRTICE
# ============================================================

YELLOW = "#F4C70F"
WHITE = "#FFFFFF"
GRAY = "#A6A6A6"

CANVAS_W = 1080
CANVAS_H = 1350


# ============================================================
# CONFIGURAÇÃO DO PERFIL
# ============================================================

try:
    config_perfil = importlib.import_module(
        "profiles.jean_victor.config"
    ).CONFIG
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


# ============================================================
# ESTADOS DO FLUXO — PRESERVADOS
# ============================================================

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


# ============================================================
# SIDEBAR — PRESERVADA
# ============================================================

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


# ============================================================
# FONTES
# ============================================================

@st.cache_resource(show_spinner=False)
def baixar_fontes_montserrat():
    fontes = {
        "bold": (
            "Montserrat-Bold.ttf",
            "https://github.com/google/fonts/raw/main/"
            "ofl/montserrat/static/Montserrat-Bold.ttf",
        ),
        "extrabold": (
            "Montserrat-ExtraBold.ttf",
            "https://github.com/google/fonts/raw/main/"
            "ofl/montserrat/static/Montserrat-ExtraBold.ttf",
        ),
    }

    caminhos = {}

    for chave, (nome, url) in fontes.items():
        if not os.path.exists(nome):
            try:
                resposta = requests.get(url, timeout=15)
                resposta.raise_for_status()
                with open(nome, "wb") as arquivo:
                    arquivo.write(resposta.content)
            except Exception:
                pass

        caminhos[chave] = nome if os.path.exists(nome) else None

    return caminhos


def fonte_montserrat(tamanho: int, peso: str = "bold"):
    caminhos = baixar_fontes_montserrat()
    caminho = caminhos.get(peso) or caminhos.get("bold")

    if caminho:
        try:
            return ImageFont.truetype(caminho, tamanho)
        except Exception:
            pass

    return ImageFont.load_default()


# ============================================================
# TEXTO
# ============================================================

def limpar_texto(texto: str) -> str:
    texto = texto or ""
    texto = re.sub(r"\*\*", "", texto)
    texto = texto.replace('"', "").replace("“", "").replace("”", "")
    return " ".join(texto.split()).strip()


def extrair_campo(texto: str, marcadores) -> str:
    linhas = (texto or "").splitlines()

    for i, linha in enumerate(linhas):
        upper = linha.upper()

        for marcador in marcadores:
            if marcador.upper() in upper:
                partes = linha.split(":", 1)

                if len(partes) == 2 and partes[1].strip():
                    return limpar_texto(partes[1])

                if i + 1 < len(linhas):
                    prox = limpar_texto(linhas[i + 1])
                    if prox and not prox.startswith("|"):
                        return prox

    return ""


def extrair_headline(texto: str, fallback: str) -> str:
    resultado = extrair_campo(
        texto,
        ["HEADLINE CAPA", "HEADLINE PRINCIPAL", "HEADLINE"],
    )
    return resultado or limpar_texto(fallback)


def extrair_subtextos(texto: str) -> list:
    linhas = (texto or "").splitlines()
    encontrados = []
    capturando = False

    for linha in linhas:
        upper = linha.upper()

        if "SUBTEXTOS DE APOIO" in upper or "SUBTEXTOS" in upper:
            capturando = True
            continue

        if capturando:
            if any(
                marcador in upper
                for marcador in [
                    "PROMPT VISUAL",
                    "LEGENDA DO POST",
                    "CTA",
                    "HEADLINE",
                ]
            ):
                break

            linha = re.sub(r"^[|\-\•\d\.\)\s]+", "", linha)
            linha = limpar_texto(linha)

            if linha and len(linha) > 2:
                encontrados.append(linha)

            if len(encontrados) >= 2:
                break

    return encontrados


def extrair_cta(texto: str) -> str:
    return extrair_campo(
        texto,
        ["CTA:", "CTA FINAL:", "CHAMADA PARA AÇÃO:"],
    )


def extrair_prompt_visual(texto: str) -> str:
    linhas = (texto or "").splitlines()

    for i, linha in enumerate(linhas):
        if "PROMPT VISUAL IDEOGRAM" in linha.upper():
            acumulado = []

            partes = linha.split(":", 1)
            if len(partes) == 2 and partes[1].strip():
                acumulado.append(partes[1].strip())

            for prox in linhas[i + 1:]:
                if (
                    "LEGENDA DO POST" in prox.upper()
                    or prox.strip().startswith("📌")
                ):
                    break
                if prox.strip():
                    acumulado.append(prox.strip())

            return limpar_texto(" ".join(acumulado))

    return ""


def quebrar_texto(draw, texto, font, largura_max):
    palavras = limpar_texto(texto).split()
    if not palavras:
        return []

    linhas = []
    atual = ""

    for palavra in palavras:
        teste = palavra if not atual else f"{atual} {palavra}"
        bbox = draw.textbbox((0, 0), teste, font=font)

        if bbox[2] - bbox[0] <= largura_max:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = palavra

    if atual:
        linhas.append(atual)

    return linhas


# ============================================================
# IMAGEM — CANVAS FINAL 1080x1350
# ============================================================

def preparar_canvas_4x5(image_bytes: bytes) -> Image.Image:
    base = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    proporcao_alvo = CANVAS_W / CANVAS_H
    proporcao_base = base.width / base.height

    if proporcao_base > proporcao_alvo:
        nova_largura = int(base.height * proporcao_alvo)
        esquerda = (base.width - nova_largura) // 2
        base = base.crop(
            (esquerda, 0, esquerda + nova_largura, base.height)
        )
    else:
        nova_altura = int(base.width / proporcao_alvo)
        topo = max(0, (base.height - nova_altura) // 2)
        base = base.crop(
            (0, topo, base.width, topo + nova_altura)
        )

    return base.resize(
        (CANVAS_W, CANVAS_H),
        Image.Resampling.LANCZOS,
    )


def aplicar_tratamento_vertice(img: Image.Image) -> Image.Image:
    img = ImageEnhance.Contrast(img.convert("RGB")).enhance(1.08)
    img = ImageEnhance.Color(img).enhance(1.05)

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    largura, altura = img.size

    # Navy no lado esquerdo para criar área de leitura.
    for x in range(int(largura * 0.70)):
        proporcao = x / (largura * 0.70)
        alpha = int(170 * (1 - proporcao) ** 1.35)
        draw.line(
            [(x, 0), (x, altura)],
            fill=(5, 17, 40, alpha),
        )

    # Gradiente superior discreto.
    for y in range(int(altura * 0.34)):
        proporcao = y / (altura * 0.34)
        alpha = int(100 * (1 - proporcao) ** 1.7)
        draw.line(
            [(0, y), (largura, y)],
            fill=(4, 16, 37, alpha),
        )

    return Image.alpha_composite(
        img.convert("RGBA"),
        overlay,
    ).convert("RGB")


def desenhar_linha_amarela(draw, x, y, largura=150, espessura=5):
    draw.rounded_rectangle(
        (x, y, x + largura, y + espessura),
        radius=espessura,
        fill=YELLOW,
    )


def desenhar_assinatura(draw):
    fonte_nome = fonte_montserrat(42, "bold")
    fonte_sub = fonte_montserrat(18, "bold")

    nome = "Jean Victor"
    sub = "Dados • Comunicação • Conteúdo Inteligente"
    margem = 62

    bbox_nome = draw.textbbox((0, 0), nome, font=fonte_nome)
    bbox_sub = draw.textbbox((0, 0), sub, font=fonte_sub)

    largura_nome = bbox_nome[2] - bbox_nome[0]
    largura_sub = bbox_sub[2] - bbox_sub[0]

    draw.text(
        (CANVAS_W - margem - largura_nome, CANVAS_H - 115),
        nome,
        font=fonte_nome,
        fill=WHITE,
    )

    draw.text(
        (CANVAS_W - margem - largura_sub, CANVAS_H - 65),
        sub,
        font=fonte_sub,
        fill="#A6A6A6",
    )


def desenhar_cta(draw, texto):
    texto = limpar_texto(texto)
    if not texto:
        return

    if len(texto) > 55:
        texto = texto[:55].rsplit(" ", 1)[0] + "…"

    fonte = fonte_montserrat(25, "bold")
    padding_x = 30
    padding_y = 18

    bbox = draw.textbbox((0, 0), texto, font=fonte)
    largura = bbox[2] - bbox[0]
    altura = bbox[3] - bbox[1]

    largura_caixa = min(largura + padding_x * 2, CANVAS_W - 124)
    x = 62
    y = CANVAS_H - 210

    draw.rounded_rectangle(
        (x, y, x + largura_caixa, y + altura + padding_y * 2),
        radius=18,
        outline=YELLOW,
        width=3,
        fill=(7, 18, 39),
    )

    draw.text(
        (x + padding_x, y + padding_y - 2),
        texto,
        font=fonte,
        fill=WHITE,
    )


def renderizar_arte_final(
    image_bytes: bytes,
    headline_texto: str,
    subtextos: Optional[list] = None,
    cta: str = "",
) -> Image.Image:

    subtextos = subtextos or []

    img = preparar_canvas_4x5(image_bytes)
    img = aplicar_tratamento_vertice(img)
    draw = ImageDraw.Draw(img)

    # Elemento gráfico Vértice: linha curta, sem logo.
    desenhar_linha_amarela(draw, 62, 82)

    # Headline curta e dominante.
    headline = limpar_texto(headline_texto)
    palavras = headline.split()

    if len(palavras) > 18:
        headline = " ".join(palavras[:18])

    fonte_headline = fonte_montserrat(82, "extrabold")
    linhas = quebrar_texto(
        draw,
        headline,
        fonte_headline,
        largura_max=650,
    )[:4]

    y = 145

    for indice, linha in enumerate(linhas):
        cor = WHITE if indice < max(1, len(linhas) - 1) else YELLOW

        draw.text(
            (62, y),
            linha,
            font=fonte_headline,
            fill=cor,
        )

        bbox = draw.textbbox(
            (62, y),
            linha,
            font=fonte_headline,
        )

        y += (bbox[3] - bbox[1]) + 12

    # No máximo dois apoios curtos.
    if subtextos:
        fonte_sub = fonte_montserrat(28, "bold")
        y_sub = min(y + 30, 760)

        for texto in subtextos[:2]:
            texto = limpar_texto(texto)

            if len(texto) > 95:
                texto = texto[:95].rsplit(" ", 1)[0] + "…"

            linhas_sub = quebrar_texto(
                draw,
                texto,
                fonte_sub,
                largura_max=570,
            )[:2]

            for linha in linhas_sub:
                draw.text(
                    (62, y_sub),
                    linha,
                    font=fonte_sub,
                    fill=WHITE,
                )

                bbox = draw.textbbox(
                    (62, y_sub),
                    linha,
                    font=fonte_sub,
                )

                y_sub += (bbox[3] - bbox[1]) + 7

            y_sub += 12

    if cta:
        desenhar_cta(draw, cta)

    desenhar_assinatura(draw)

    return img


# ============================================================
# GEMINI — IDEIAS
# ============================================================

def gerar_ideias_gemini(api_key: str, base_conhecimento: str) -> list:
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(
        "gemini-3.5-flash-lite",
        generation_config={"temperature": 0.95},
    )

    prompt = f"""
Você é o estrategista de conteúdo da Plataforma Vértice — Jean Victor.

BASE DE CONHECIMENTO:
{base_conhecimento}

Gere 5 ideias ÚNICAS e VARIADAS para Instagram.

Distribua entre:
• descoberta
• conteúdo técnico
• posicionamento

As ideias devem ser curtas, estratégicas e específicas à base.
Evite linguagem genérica, motivacional ou professoral.
Ferramentas podem aparecer quando fizerem sentido, mas são meio, não fim.

Formato obrigatório:
1. ideia
2. ideia
3. ideia
4. ideia
5. ideia

Não escreva explicações antes ou depois.
"""

    res = model.generate_content(prompt)

    linhas = [
        line.strip()
        for line in res.text.split("\n")
        if line.strip() and re.match(r"^\d+[\.\)]\s*", line.strip())
    ]

    return linhas[:5] if linhas else [res.text.strip()]


# ============================================================
# GEMINI — ESTRUTURA + PROMPT VISUAL
# ============================================================

@st.cache_data(show_spinner=False)
def gerar_estrutura_gemini(
    api_key: str,
    ideia: str,
    formato: str,
    paginas: int,
    base_conhecimento: str,
) -> str:

    genai.configure(api_key=api_key)

    model = genai.GenerativeModel("gemini-3.5-flash-lite")

    prompt = f"""
Você é o estrategista de conteúdo premium da Plataforma Vértice — Jean Victor.

TEMA:
{ideia}

FORMATO:
{formato}

PÁGINAS:
{paginas}

BASE DE CONHECIMENTO DO PRODUTO:
{base_conhecimento}

REGRAS:
- A base define O QUE comunicar.
- Nunca invente informações.
- Ferramentas são meio, não fim.
- Partir de dor, consequência, desejo, oportunidade ou ganho.
- Comunicação estratégica, direta, provocativa e premium.
- Uma ideia principal por peça/slide.
- Todo texto da arte deve ser compreendido em até 3 segundos.
- Poucas palavras, headline dominante e complemento mínimo.
- Evitar parágrafos, miniartigos e excesso de informação.
- Predomínio de caixa baixa.
- Usar PT-BR.
- Para carrossel, criar progressão narrativa e cenas diferentes.
- Não repetir a mesma cena visual em páginas consecutivas.

DIREÇÃO VISUAL VÉRTICE:
- formato final 4:5, 1080x1350;
- azul navy profundo;
- azul escuro cinematográfico;
- azul petróleo e azul noturno;
- branco;
- amarelo #F4C70F;
- Montserrat ExtraBold/Bold;
- premium, limpa, moderna, editorial e estratégica;
- azul VISIVELMENTE azul;
- iluminação azul elegante;
- profundidade;
- contraste cinematográfico suave;
- degradês azulados;
- brilho azul sutil;
- luz suave nas bordas.

PROIBIDO:
- azul acinzentado ou quase preto;
- fundo preto chapado;
- visual apagado;
- sombras excessivas;
- folhas;
- plantas;
- ramos;
- elementos botânicos;
- logos;
- logotipos;
- marcas d'água;
- símbolos de marca;
- texto dentro da fotografia;
- gráficos gerados pelo modelo;
- CGI;
- 3D;
- ilustração.

A ARTE FINAL SERÁ MONTADA PROGRAMATICAMENTE.
O IDEOGRAM DEVE GERAR SOMENTE A FOTOGRAFIA/FUNDO.
Não peça headline, CTA, logo ou texto ao gerador.

A fotografia deve preferencialmente colocar o assunto principal no lado direito ou centro-direito e deixar área limpa no lado esquerdo para tipografia.

SAÍDA OBRIGATÓRIA:

📌 TEXTO DA ARTE / CARROSSEL

CATEGORIA:
[Descoberta / Conteúdo Técnico / Posicionamento]

OBJETIVO:
[Atrair / Ensinar / Fortalecer autoridade]

HEADLINE CAPA:
[headline curta e forte]

SUBTEXTOS DE APOIO:
| [frase curta]
| [frase curta]

CTA:
[CTA curto ou vazio]

PROMPT VISUAL IDEOGRAM:
[Prompt em inglês para fotografia hiper-realista. Descrever somente cena, ambiente, pessoa/objeto, enquadramento, iluminação e atmosfera. Não inserir texto, logos, folhas ou plantas.]

📌 LEGENDA DO POST
[Legenda curta e estratégica, coerente com a base.]

Para POST, manter o texto extremamente enxuto.
Para CARROSSEL, separar cada página e manter uma ideia principal por página.
"""

    res = model.generate_content(prompt)
    return res.text


# ============================================================
# LIMPEZA DO RASCUNHO
# ============================================================

def limpar_rascunho_exibicao(texto: str) -> str:
    linhas = texto.split("\n")
    resultado = []
    ignorar = False

    for linha in linhas:
        if "PROMPT VISUAL IDEOGRAM" in linha.upper():
            ignorar = True
            continue

        if ignorar and (
            linha.startswith("📌")
            or "LEGENDA DO POST" in linha.upper()
        ):
            ignorar = False

        if not ignorar:
            resultado.append(linha)

    return "\n".join(resultado)


# ============================================================
# PASSO 0 — FORMATO
# ============================================================

if st.session_state.formato is None:

    st.subheader("Olá Jean Victor! O que vamos criar hoje?")

    fmt = st.radio(
        "Selecione o formato:",
        [
            "Post Único (4:5)",
            "Carrossel (4:5)",
            "Reels (Apenas Roteiro)",
        ],
    )

    if st.button("Confirmar Formato"):
        st.session_state.formato = fmt
        st.rerun()

else:

    st.info(
        f"📌 Formato selecionado: **{st.session_state.formato}**"
    )

    # ========================================================
    # ETAPA 1
    # ========================================================

    if st.session_state.etapa == 1:

        st.subheader("ETAPA 1: Qual é o Produto?")

        prod = st.radio(
            "Selecione:",
            list(MAPA_PRODUTOS.keys()),
        )

        if st.button("Avançar para Etapa 2"):
            st.session_state.produto = prod
            st.session_state.etapa = 2
            st.rerun()

    # ========================================================
    # ETAPA 2 + 3
    # ========================================================

    elif st.session_state.etapa == 2:

        st.subheader("ETAPA 2: Origem da Ideia")

        op = st.radio(
            "Como deseja prosseguir?",
            [
                "1️⃣ Já tenho ideia",
                "2️⃣ Quero ideias estratégicas",
            ],
        )

        paginas = 5

        if st.session_state.formato == "Carrossel (4:5)":
            paginas = st.number_input(
                "ETAPA 3: Quantidade de páginas do carrossel:",
                min_value=3,
                max_value=10,
                value=5,
            )

        if st.button("Avançar para Ideação"):
            st.session_state.opcao_ideia = op
            st.session_state.num_paginas = paginas
            st.session_state.etapa = 4
            st.rerun()

    # ========================================================
    # ETAPA 4
    # ========================================================

    elif st.session_state.etapa == 4:

        modulo = importlib.import_module(
            MAPA_PRODUTOS[st.session_state.produto]
        )

        st.subheader(
            f"ETAPA 4: Definição do Conteúdo — "
            f"{st.session_state.produto}"
        )

        if (
            st.session_state.opcao_ideia
            == "2️⃣ Quero ideias estratégicas"
        ):

            if not st.session_state.ideias_lista:

                with st.spinner(
                    "Analisando a base de conhecimento..."
                ):
                    st.session_state.ideias_lista = (
                        gerar_ideias_gemini(
                            GEMINI_API_KEY,
                            modulo.CONHECIMENTO,
                        )
                    )

                st.rerun()

            for i, ideia in enumerate(
                st.session_state.ideias_lista
            ):
                if st.button(
                    ideia,
                    key=f"btn_ideia_{i}",
                ):
                    st.session_state.ideia_escolhida = ideia
                    st.session_state.etapa = 5
                    st.rerun()

        else:

            st.session_state.ideia_escolhida = st.text_input(
                "Digite a sua ideia:"
            )

            if (
                st.session_state.ideia_escolhida
                and st.button("Avançar")
            ):
                st.session_state.etapa = 5
                st.rerun()

    # ========================================================
    # ETAPA 5
    # ========================================================

    elif st.session_state.etapa == 5:

        modulo = importlib.import_module(
            MAPA_PRODUTOS[st.session_state.produto]
        )

        st.subheader("ETAPA 5: Estrutura Estratégica")

        if not st.session_state.estrutura_rascunho:

            with st.spinner(
                "Construindo narrativa estratégica..."
            ):
                st.session_state.estrutura_rascunho = (
                    gerar_estrutura_gemini(
                        GEMINI_API_KEY,
                        st.session_state.ideia_escolhida,
                        st.session_state.formato,
                        st.session_state.num_paginas,
                        modulo.CONHECIMENTO,
                    )
                )

            st.rerun()

        st.markdown(
            limpar_rascunho_exibicao(
                st.session_state.estrutura_rascunho
            )
        )

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

    # ========================================================
    # ETAPA 8 — IMAGEM
    # ========================================================

    elif st.session_state.etapa == 8:

        st.subheader(
            "ETAPA 8: Renderização Hiper-Realista "
            "Pronta para Postar"
        )

        if (
            st.session_state.formato
            == "Reels (Apenas Roteiro)"
        ):

            st.success(
                "O roteiro foi concluído. "
                "Reels não gera imagem."
            )

        else:

            if not st.session_state.imagem_processada_bytes:

                with st.spinner(
                    "Gerando fotografia e aplicando "
                    "composição Vértice..."
                ):

                    try:

                        # ------------------------------------
                        # 1. PROMPT VISUAL
                        # ------------------------------------

                        prompt_fundo = extrair_prompt_visual(
                            st.session_state.estrutura_rascunho
                        )

                        if not prompt_fundo:
                            prompt_fundo = (
                                "Hyper-realistic RAW editorial "
                                "photograph, sophisticated modern "
                                "professional environment, realistic "
                                "human subject or relevant object "
                                "connected to the topic, cinematic "
                                "navy blue atmosphere, elegant blue "
                                "edge lighting, realistic materials, "
                                "natural skin texture, shallow depth "
                                "of field, subject positioned on the "
                                "right or center-right, clean dark "
                                "negative space on the left for "
                                "typography, premium editorial "
                                "photography, 35mm lens, realistic "
                                "lighting"
                            )

                        prompt_fundo += (
                            ", deep navy blue, sophisticated royal "
                            "blue accents, visible blue tones, "
                            "subtle yellow accent #F4C70F, premium "
                            "editorial composition, NO CGI, NO 3D, "
                            "NO GRAPHICS, NO TEXT, NO WORDS, NO "
                            "LOGOS, NO WATERMARKS, NO LEAVES, NO "
                            "PLANTS, NO BOTANICAL ELEMENTS"
                        )

                        # ------------------------------------
                        # 2. IDEOGRAM
                        # ------------------------------------

                        output = replicate.run(
                            "ideogram-ai/ideogram-v2",
                            input={
                                "prompt": prompt_fundo,
                                # Preservado por compatibilidade
                                # com o modelo que já está rodando.
                                "aspect_ratio": "3:4",
                                "style_type": "Realistic",
                                "magic_prompt_option": "Off",
                            },
                        )

                        image_url = (
                            str(output[0])
                            if isinstance(output, list)
                            else str(output)
                        )

                        resposta = requests.get(
                            image_url,
                            timeout=60,
                        )
                        resposta.raise_for_status()

                        raw_bytes = resposta.content

                        # ------------------------------------
                        # 3. TEXTO DA ESTRUTURA
                        # ------------------------------------

                        headline_texto = extrair_headline(
                            st.session_state.estrutura_rascunho,
                            st.session_state.ideia_escolhida,
                        )

                        subtextos = extrair_subtextos(
                            st.session_state.estrutura_rascunho
                        )

                        cta = extrair_cta(
                            st.session_state.estrutura_rascunho
                        )

                        # ------------------------------------
                        # 4. COMPOSIÇÃO VÉRTICE
                        # ------------------------------------

                        img_final = renderizar_arte_final(
                            raw_bytes,
                            headline_texto,
                            subtextos,
                            cta,
                        )

                        buffer = io.BytesIO()

                        img_final.save(
                            buffer,
                            format="PNG",
                            optimize=True,
                        )

                        st.session_state.imagem_processada_bytes = (
                            buffer.getvalue()
                        )

                        st.rerun()

                    except Exception as erro:
                        st.error(
                            f"Erro na geração da imagem: {erro}"
                        )

            # --------------------------------------------
            # EXIBIÇÃO — PRESERVADA
            # --------------------------------------------

            if st.session_state.imagem_processada_bytes:

                col_esq, col_centro, col_dir = st.columns(
                    [0.8, 2, 0.8]
                )

                with col_centro:
                    st.image(
                        st.session_state.imagem_processada_bytes,
                        caption=(
                            "Arte Final Pronta para Publicação "
                            "— 1080x1350 / 4:5"
                        ),
                        use_container_width=True,
                    )

                st.download_button(
                    label=(
                        "📥 Baixar Arte Final Pronta "
                        "(PNG Alta Resolução)"
                    ),
                    data=st.session_state.imagem_processada_bytes,
                    file_name="vertice_arte_final.png",
                    mime="image/png",
                )

        st.divider()

        st.subheader(
            "📝 Rascunho & Legenda Estratégica:"
        )

        if st.session_state.estrutura_rascunho:
            st.markdown(
                limpar_rascunho_exibicao(
                    st.session_state.estrutura_rascunho
                )
            )
