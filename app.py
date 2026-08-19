import io
import json
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
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Plataforma Vértice 🚀 | Jean Victor",
    layout="centered",
)


# ============================================================
# CSS — INTERFACE PRESERVADA
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background-color: #0b1120;
        color: #ffffff;
    }

    .stButton > button {
        background-color: #0e2447 !important;
        color: #ffffff !important;
        border: 1px solid #f4c70f !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        min-height: 46px !important;
        line-height: 1.35 !important;
    }

    .stButton > button:hover {
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

    hr {
        border-color: #1e2d4a !important;
    }

    .caption-box {
        background: #0e1d35;
        border: 1px solid #243b63;
        border-radius: 12px;
        padding: 18px 20px;
        margin-top: 18px;
    }

    .caption-title {
        color: #f4c70f;
        font-weight: 800;
        margin-bottom: 8px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# CABEÇALHO
# ============================================================

col_logo, col_titulo = st.columns(
    [1, 3.5],
    vertical_alignment="center",
)

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

GEMINI_API_KEY = st.secrets.get(
    "GEMINI_API_KEY",
    "",
)

REPLICATE_API_TOKEN = st.secrets.get(
    "REPLICATE_API_TOKEN",
    "",
)

if REPLICATE_API_TOKEN:
    os.environ["REPLICATE_API_TOKEN"] = (
        REPLICATE_API_TOKEN
    )


# ============================================================
# IDENTIDADE VÉRTICE
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

    config_perfil = {}


# ============================================================
# PRODUTOS
# ============================================================

MAPA_PRODUTOS = {

    "1️⃣ Dados":
        "profiles.jean_victor.dados",

    "2️⃣ Apresentações Profissionais":
        "profiles.jean_victor.apresentacoes",

    "3️⃣ Plataforma Vértice":
        "profiles.jean_victor.vertice",

    "4️⃣ Método 5P":
        "profiles.jean_victor.metodo5p",

    "5️⃣ Nutribook":
        "profiles.jean_victor.nutribook",
}


# ============================================================
# ESTADOS
# ============================================================

ESTADOS = [

    "formato",

    "produto",

    "opcao_ideia",

    "num_paginas",

    "ideia_escolhida",

    "ideias_lista",

    "conteudo_gerado",

    "pagina_atual",

    "imagem_processada_bytes",

]


for key in ESTADOS:

    if key not in st.session_state:

        st.session_state[key] = None


if "etapa" not in st.session_state:

    st.session_state.etapa = 0


# ============================================================
# RESET
# ============================================================

def resetar_fluxo():

    for key in ESTADOS:

        st.session_state[key] = None

    st.session_state.etapa = 0


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    try:

        st.image(
            "logo.png",
            use_container_width=True,
        )

    except Exception:

        pass

    st.write("---")

    if st.button(
        "🔄 Iniciar Novo Conteúdo"
    ):

        resetar_fluxo()

        st.rerun()


# ============================================================
# FONTES MONTSERRAT
# ============================================================

@st.cache_resource(
    show_spinner=False
)
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

    for chave, dados in fontes.items():

        nome, url = dados

        if not os.path.exists(nome):

            try:

                resposta = requests.get(
                    url,
                    timeout=20,
                )

                resposta.raise_for_status()

                with open(
                    nome,
                    "wb",
                ) as arquivo:

                    arquivo.write(
                        resposta.content
                    )

            except Exception:

                pass

        caminhos[chave] = (
            nome
            if os.path.exists(nome)
            else None
        )

    return caminhos


def fonte_montserrat(
    tamanho: int,
    peso: str = "bold",
):

    caminhos = baixar_fontes_montserrat()

    caminho = (
        caminhos.get(peso)
        or caminhos.get("bold")
    )

    if caminho:

        try:

            return ImageFont.truetype(
                caminho,
                tamanho,
            )

        except Exception:

            pass

    return ImageFont.load_default()


# ============================================================
# UTILITÁRIOS
# ============================================================

def limpar_texto(texto: str) -> str:

    texto = texto or ""

    texto = re.sub(
        r"\*\*",
        "",
        texto,
    )

    texto = texto.replace(
        "“",
        "",
    ).replace(
        "”",
        "",
    )

    texto = texto.replace(
        "📌",
        "",
    )

    texto = texto.replace(
        "🚀",
        "",
    )

    return " ".join(
        texto.split()
    ).strip()


def normalizar_lista(valor):

    if valor is None:

        return []

    if isinstance(
        valor,
        list,
    ):

        return [
            limpar_texto(
                str(x)
            )

            for x in valor

            if str(x).strip()
        ]

    if isinstance(
        valor,
        str,
    ):

        return [
            limpar_texto(valor)
        ]

    return []


# ============================================================
# JSON GEMINI
# ============================================================

def extrair_json_resposta(
    texto: str
):

    texto = (
        texto or ""
    ).strip()

    texto = re.sub(
        r"^```json",
        "",
        texto,
        flags=re.IGNORECASE,
    )

    texto = re.sub(
        r"^```",
        "",
        texto,
    )

    texto = re.sub(
        r"```$",
        "",
        texto,
    )

    texto = texto.strip()

    try:

        return json.loads(
            texto
        )

    except Exception:

        inicio = texto.find("{")
        fim = texto.rfind("}")

        if inicio >= 0 and fim > inicio:

            try:

                return json.loads(
                    texto[
                        inicio:fim + 1
                    ]
                )

            except Exception:

                pass

    raise ValueError(
        "O Gemini não retornou JSON válido."
    )


# ============================================================
# NORMALIZAÇÃO DO CONTEÚDO
# ============================================================

def normalizar_conteudo(
    dados: dict,
    formato: str,
):

    if not isinstance(
        dados,
        dict,
    ):

        dados = {}

    resultado = {

        "categoria":
            limpar_texto(
                dados.get(
                    "categoria",
                    "Conteúdo Técnico",
                )
            ),

        "objetivo":
            limpar_texto(
                dados.get(
                    "objetivo",
                    "Atrair",
                )
            ),

        "legenda":
            limpar_texto(
                dados.get(
                    "legenda",
                    "",
                )
            ),

        "hashtags":
            normalizar_lista(
                dados.get(
                    "hashtags",
                    [],
                )
            )[:5],

        "paginas": [],

    }

    paginas = dados.get(
        "paginas",
        [],
    )

    if not isinstance(
        paginas,
        list,
    ):

        paginas = []


    # --------------------------------------------------------
    # POST = UMA ÚNICA PÁGINA
    # --------------------------------------------------------

    if formato == "Post Único (4:5)":

        pagina = (
            paginas[0]
            if paginas
            else dados.get(
                "pagina",
                {},
            )
        )

        if not isinstance(
            pagina,
            dict,
        ):

            pagina = {}

        paginas = [pagina]


    pagina_normalizada = []

    for pagina in paginas:

        if not isinstance(
            pagina,
            dict,
        ):

            pagina = {}

        pagina_normalizada.append(

            {

                "headline":
                    limpar_texto(
                        pagina.get(
                            "headline",
                            "",
                        )
                    ),

                "apoios":
                    normalizar_lista(
                        pagina.get(
                            "apoios",
                            [],
                        )
                    )[:2],

                "cta":
                    limpar_texto(
                        pagina.get(
                            "cta",
                            "",
                        )
                    ),

                "prompt_visual":
                    limpar_texto(
                        pagina.get(
                            "prompt_visual",
                            "",
                        )
                    ),

            }

        )

    resultado[
        "paginas"
    ] = pagina_normalizada


    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    if not resultado[
        "paginas"
    ]:

        resultado[
            "paginas"
        ] = [

            {

                "headline":
                    limpar_texto(
                        dados.get(
                            "headline",
                            "",
                        )
                    ),

                "apoios":
                    normalizar_lista(
                        dados.get(
                            "apoios",
                            [],
                        )
                    )[:2],

                "cta":
                    limpar_texto(
                        dados.get(
                            "cta",
                            "",
                        )
                    ),

                "prompt_visual":
                    limpar_texto(
                        dados.get(
                            "prompt_visual",
                            "",
                        )
                    ),

            }

        ]

    return resultado


# ============================================================
# GEMINI — IDEIAS
# ============================================================

def gerar_ideias_gemini(
    api_key: str,
    base_conhecimento: str,
):

    genai.configure(
        api_key=api_key
    )

    model = genai.GenerativeModel(
        "gemini-3.5-flash-lite",
        generation_config={
            "temperature": 0.85,
        },
    )

    prompt = f"""

Você é o estrategista de conteúdo premium
da Plataforma Vértice — Jean Victor.

BASE DE CONHECIMENTO:
{base_conhecimento}

Gere EXATAMENTE 5 ideias para Instagram.

Distribua entre:
• descoberta
• conteúdo técnico
• posicionamento

REGRAS:

• cada ideia deve ser curta;
• cada ideia deve ter no máximo 12 palavras;
• preferência por 5 a 9 palavras;
• uma única frase;
• específica;
• estratégica;
• provocativa quando fizer sentido;
• fácil de entender;
• sem explicações;
• sem subtítulo;
• sem justificativa;
• sem descrição de formato.

NÃO faça:

• ideias longas;
• mini textos;
• parágrafos;
• explicações;
• listas internas;
• emojis;
• CTA;
• hashtags;
• bordões;
• slogans da marca;
• "Vamos transformar seus dados em decisão?";
• qualquer assinatura ou frase institucional.

IMPORTANTE:

A ideia deve ser apenas o TEMA/ÂNGULO
do conteúdo.

Retorne SOMENTE:

1. ideia curta
2. ideia curta
3. ideia curta
4. ideia curta
5. ideia curta

"""

    resposta = model.generate_content(
        prompt
    )

    linhas = []

    for linha in (
        resposta.text or ""
    ).splitlines():

        linha = linha.strip()

        if not linha:
            continue

        linha = re.sub(
            r"^\d+[\.\)]\s*",
            "",
            linha,
        )

        linha = limpar_texto(
            linha
        )

        if linha:
            linhas.append(
                linha
            )

    return linhas[:5]


# ============================================================
# GEMINI — CONTEÚDO FINAL
# ============================================================

@st.cache_data(
    show_spinner=False
)
def gerar_conteudo_final(
    api_key: str,
    ideia: str,
    formato: str,
    paginas: int,
    base_conhecimento: str,
):

    genai.configure(
        api_key=api_key
    )

    model = genai.GenerativeModel(
        "gemini-3.5-flash-lite",
        generation_config={
            "temperature": 0.70,
            "response_mime_type":
                "application/json",
        },
    )


    # --------------------------------------------------------
    # FORMATO
    # --------------------------------------------------------

    if formato == "Post Único (4:5)":

        instrucoes_formato = """

FORMATO: POST ÚNICO.

REGRA ABSOLUTA:

"paginas" deve conter EXATAMENTE 1 item.

NUNCA gere:
• página 2;
• página 3;
• carrossel;
• sequência;
• continuação.

O post comunica UMA única ideia.

"""


    elif formato == "Carrossel (4:5)":

        instrucoes_formato = f"""

FORMATO: CARROSSEL.

"paginas" deve conter EXATAMENTE
{paginas} itens.

Cada página possui UMA ideia principal.

"""


    else:

        instrucoes_formato = """

FORMATO: REELS.

Não gerar imagem.

Gerar apenas roteiro.

"""


    prompt = f"""

Você é o estrategista de conteúdo premium
da Plataforma Vértice — Jean Victor.

IDEIA ESCOLHIDA:
{ideia}

{instrucoes_formato}

BASE DE CONHECIMENTO DO PRODUTO:
{base_conhecimento}

==================================================
ESTRATÉGIA
==================================================

A base de conhecimento define o que pode
ser comunicado.

Não invente:

• funcionalidades;
• benefícios;
• números;
• resultados;
• promessas;
• informações.

Nunca faça a ferramenta ser a protagonista.

Priorize:

• dor;
• clareza;
• decisão;
• produtividade;
• organização;
• autoridade;
• percepção profissional;
• experiência;
• ganho;
• consequência.

Tom:

• estratégico;
• direto;
• provocativo;
• premium.

Evite:

• motivacional;
• genérico;
• professoral;
• amigável demais;
• técnico demais.

==================================================
COPY DA ARTE
==================================================

A arte deve ser compreendida em até 3 segundos.

REGRA PRINCIPAL:

MENOS TEXTO.

Se 50% do texto puder ser retirado
sem perder a mensagem, retire.

POST:

• headline de 3 a 8 palavras;
• máximo 2 apoios;
• cada apoio com no máximo 6 palavras;
• CTA de no máximo 4 palavras;
• comunicação principal extremamente curta.

CARROSSEL:

• uma ideia por página;
• headline dominante;
• headline de preferência 3 a 8 palavras;
• no máximo 1 apoio;
• apoio de preferência até 6 palavras;
• CTA apenas quando realmente necessário.

Não transforme a arte em explicação.

==================================================
BORDÕES
==================================================

NUNCA inserir bordões ou slogans
nas ideias.

NUNCA inserir automaticamente:

"Vamos transformar seus dados em decisão?"

ou qualquer outro bordão institucional.

CTA deve ser contextual.

==================================================
VISUAL
==================================================

A fotografia precisa representar
VISUALMENTE o assunto da página.

Não gere um escritório genérico
apenas porque o conteúdo é profissional.

Escolha uma cena específica.

Exemplos:

• dashboard → tela com indicadores;
• apresentação → palco, tela, apresentação;
• dados → visualização de dados ou análise;
• produtividade → processo, documentos, fluxo;
• decisão → pessoa analisando informação;
• Nutribook → material nutricional, planejamento,
  atendimento, organização;
• Vértice → branding, conteúdo, comunicação;
• apresentações → apresentação profissional,
  palco, audiência, tela;
• Método 5P → conteúdo, posicionamento,
  comunicação e estratégia.

A cena deve fazer sentido mesmo sem texto.

==================================================
IDENTIDADE VISUAL
==================================================

Padrão Vértice:

• azul navy profundo;
• azul royal;
• azul elétrico sofisticado;
• branco;
• amarelo #F4C70F;
• iluminação azul cinematográfica;
• contraste elegante;
• profundidade;
• fotografia editorial premium;
• aparência comercial;
• visual moderno;
• visual tecnológico;
• acabamento sofisticado.

O azul precisa ser VISIVELMENTE azul.

Não deixar a imagem cinza.

Não deixar a imagem preta.

Não deixar a imagem excessivamente escura.

==================================================
ELEMENTOS PROIBIDOS
==================================================

NUNCA inserir:

• folhas;
• plantas;
• ramos;
• folhagens;
• flores;
• vasos com plantas;
• vegetação;
• elementos botânicos;
• estética naturalista;
• estética tropical;
• decoração vegetal;
• logos;
• logotipos;
• marcas;
• marcas d'água;
• textos;
• letras;
• palavras;
• gráficos com texto;
• infográficos;
• ilustrações;
• CGI;
• 3D;
• arte digital;
• visual artificial.

A fotografia deve parecer fotografia real.

==================================================
COMPOSIÇÃO
==================================================

Sempre pensar na composição final.

O texto será aplicado posteriormente pelo Python.

Portanto:

• reservar área limpa para texto;
• evitar elementos importantes no lado esquerdo;
• assunto principal preferencialmente
  à direita ou centro-direita;
• profundidade visual;
• composição editorial;
• iluminação cinematográfica;
• enquadramento vertical;
• fotografia realista.

==================================================
LEGENDA
==================================================

A legenda é OBRIGATÓRIA.

Deve:

• complementar a arte;
• não repetir integralmente a headline;
• ser estratégica;
• ser curta;
• ter CTA natural;
• estar em PT-BR;
• conter exatamente 5 hashtags.

==================================================
PROMPT VISUAL
==================================================

"prompt_visual" deve ser escrito EM INGLÊS.

Ele deve descrever SOMENTE:

• cena;
• ambiente;
• objeto;
• pessoa, quando necessária;
• enquadramento;
• iluminação;
• fotografia;
• composição.

NUNCA coloque no prompt_visual:

• texto;
• headline;
• CTA;
• logo;
• marca;
• folhas;
• plantas;
• elementos botânicos.

O prompt deve ser específico à ideia.

Não escreva apenas:

"modern office".

Descreva a cena que realmente representa
o conteúdo.

==================================================
SAÍDA
==================================================

Retorne SOMENTE JSON válido.

Formato:

{{
  "categoria": "Descoberta | Conteúdo Técnico | Posicionamento",
  "objetivo": "Atrair | Ensinar | Fortalecer autoridade",

  "legenda": "legenda curta em PT-BR",

  "hashtags": [
    "#tag1",
    "#tag2",
    "#tag3",
    "#tag4",
    "#tag5"
  ],

  "paginas": [
    {{
      "headline": "headline curta",
      "apoios": [
        "apoio curto"
      ],
      "cta": "CTA curto",
      "prompt_visual": "specific English photographic scene, realistic commercial photography, vertical composition, subject on right, clean space on left"
    }}
  ]
}}

IMPORTANTE:

POST:
"paginas" = EXATAMENTE 1 item.

CARROSSEL:
"paginas" = EXATAMENTE {paginas} itens.

"""

    resposta = model.generate_content(
        prompt
    )

    dados = extrair_json_resposta(
        resposta.text
    )

    return normalizar_conteudo(
        dados,
        formato,
    )


# ============================================================
# PROMPT VISUAL — REFORÇO IDEOGRAM
# ============================================================

def construir_prompt_visual(
    prompt_base: str,
):

    prompt_base = limpar_texto(
        prompt_base
    )

    reforco = """

Hyper-realistic premium editorial commercial photography.
Authentic real-world scene.
Sophisticated deep navy blue and royal blue color environment.
Clearly visible blue tones.
Elegant cinematic blue lighting.
Professional photography.
Natural realistic materials.
Realistic textures.
Natural photographic depth of field.
Premium advertising photography.
Vertical editorial composition.
Main subject on the right or center-right.
Clean visual negative space on the left for later typography.
The scene must visually represent the subject of the content.
No generic decorative office scene unless the topic explicitly requires it.
No text.
No words.
No letters.
No typography.
No logo.
No brand mark.
No watermark.
No leaves.
No plants.
No branches.
No foliage.
No flowers.
No vase with plants.
No botanical elements.
No vegetation.
No natural decoration.
No CGI.
No 3D render.
No illustration.
No infographic.
No graphic design.
No poster.
No mockup.
"""

    return (
        prompt_base
        + "\n"
        + reforco
    )


# ============================================================
# IDEOGRAM — NEGATIVE PROMPT
# ============================================================

NEGATIVE_PROMPT = """

text, words, letters, typography, headline,
caption, logo, brand mark, watermark,
poster, graphic design, infographic,
presentation slide, UI screenshot,
leaves, plants, branches, foliage, flowers,
vase plants, botanical decoration, vegetation,
tropical plants, natural decoration,
generic office plant,
CGI, 3D render, illustration, cartoon,
artificial looking scene,
plastic looking objects,
oversaturated colors,
gray image, black image,
low contrast, blurry subject,
distorted anatomy, deformed hands,
extra fingers, duplicated objects,
empty generic office,
generic corporate stock photo
"""


# ============================================================
# IDEOGRAM
# ============================================================

def gerar_fundo_ideogram(
    prompt_visual: str,
):

    prompt_final = construir_prompt_visual(
        prompt_visual
    )

    if not REPLICATE_API_TOKEN:

        raise ValueError(
            "REPLICATE_API_TOKEN não configurada."
        )

    output = replicate.run(

        "ideogram-ai/ideogram-v2",

        input={

            "prompt":
                prompt_final,

            "negative_prompt":
                NEGATIVE_PROMPT,

            "aspect_ratio":
                "3:4",

            "style_type":
                "Realistic",

            "magic_prompt_option":
                "Off",

        },

    )

    if isinstance(
        output,
        list,
    ):

        image_url = str(
            output[0]
        )

    elif hasattr(
        output,
        "url",
    ):

        image_url = str(
            output.url
        )

    else:

        image_url = str(
            output
        )

    resposta = requests.get(
        image_url,
        timeout=120,
    )

    resposta.raise_for_status()

    return resposta.content


# ============================================================
# CANVAS 4:5
# ============================================================

def preparar_canvas_4x5(
    image_bytes: bytes,
):

    base = Image.open(
        io.BytesIO(
            image_bytes
        )
    ).convert(
        "RGB"
    )

    proporcao_alvo = (
        CANVAS_W / CANVAS_H
    )

    proporcao_base = (
        base.width / base.height
    )


    if (
        proporcao_base
        > proporcao_alvo
    ):

        nova_largura = int(
            base.height
            * proporcao_alvo
        )

        esquerda = max(
            0,
            (
                base.width
                - nova_largura
            ) // 2,
        )

        base = base.crop(
            (
                esquerda,
                0,
                esquerda
                + nova_largura,
                base.height,
            )
        )

    else:

        nova_altura = int(
            base.width
            / proporcao_alvo
        )

        topo = max(
            0,
            (
                base.height
                - nova_altura
            ) // 2,
        )

        base = base.crop(
            (
                0,
                topo,
                base.width,
                topo
                + nova_altura,
            )
        )


    return base.resize(
        (
            CANVAS_W,
            CANVAS_H,
        ),
        Image.Resampling.LANCZOS,
    )


# ============================================================
# TRATAMENTO VISUAL VÉRTICE
# ============================================================

def aplicar_tratamento_vertice(
    img: Image.Image,
):

    img = ImageEnhance.Contrast(
        img.convert("RGB")
    ).enhance(
        1.08
    )

    img = ImageEnhance.Color(
        img
    ).enhance(
        1.08
    )


    overlay = Image.new(
        "RGBA",
        img.size,
        (0, 0, 0, 0),
    )

    draw = ImageDraw.Draw(
        overlay
    )

    largura, altura = (
        img.size
    )


    # --------------------------------------------------------
    # GRADIENTE DE LEITURA
    # --------------------------------------------------------

    limite = int(
        largura * 0.60
    )

    for x in range(
        limite
    ):

        proporcao = (
            x / limite
        )

        alpha = int(
            150
            * (
                1
                - proporcao
            ) ** 1.45
        )

        draw.line(
            [
                (x, 0),
                (x, altura),
            ],
            fill=(
                5,
                17,
                40,
                alpha,
            ),
        )


    # --------------------------------------------------------
    # PROTEÇÃO SUPERIOR
    # --------------------------------------------------------

    limite_y = int(
        altura * 0.22
    )

    for y in range(
        limite_y
    ):

        proporcao = (
            y / limite_y
        )

        alpha = int(
            65
            * (
                1
                - proporcao
            ) ** 1.6
        )

        draw.line(
            [
                (0, y),
                (largura, y),
            ],
            fill=(
                4,
                16,
                37,
                alpha,
            ),
        )


    return Image.alpha_composite(
        img.convert("RGBA"),
        overlay,
    ).convert(
        "RGB"
    )


# ============================================================
# LINHA AMARELA
# ============================================================

def desenhar_linha_amarela(
    draw,
    x,
    y,
    largura=150,
    espessura=5,
):

    draw.rounded_rectangle(

        (
            x,
            y,
            x + largura,
            y + espessura,
        ),

        radius=espessura,

        fill=YELLOW,

    )


# ============================================================
# ASSINATURA
# ============================================================

def desenhar_assinatura(
    draw,
):

    fonte_nome = fonte_montserrat(
        42,
        "bold",
    )

    fonte_sub = fonte_montserrat(
        18,
        "bold",
    )

    nome = "Jean Victor"

    sub = (
        "Dados • Comunicação • "
        "Conteúdo Inteligente"
    )

    margem = 62


    bbox_nome = draw.textbbox(
        (0, 0),
        nome,
        font=fonte_nome,
    )

    bbox_sub = draw.textbbox(
        (0, 0),
        sub,
        font=fonte_sub,
    )


    largura_nome = (
        bbox_nome[2]
        - bbox_nome[0]
    )

    largura_sub = (
        bbox_sub[2]
        - bbox_sub[0]
    )


    draw.text(

        (
            CANVAS_W
            - margem
            - largura_nome,

            CANVAS_H
            - 118,
        ),

        nome,

        font=fonte_nome,

        fill=WHITE,

    )


    draw.text(

        (
            CANVAS_W
            - margem
            - largura_sub,

            CANVAS_H
            - 68,
        ),

        sub,

        font=fonte_sub,

        fill=GRAY,

    )


# ============================================================
# QUEBRA DE TEXTO
# ============================================================

def quebrar_texto(
    draw,
    texto,
    font,
    largura_max,
):

    palavras = (
        limpar_texto(
            texto
        )
        .split()
    )

    if not palavras:

        return []


    linhas = []

    atual = ""


    for palavra in palavras:

        teste = (

            palavra

            if not atual

            else
            f"{atual} {palavra}"

        )


        bbox = draw.textbbox(

            (0, 0),

            teste,

            font=font,

        )


        largura = (
            bbox[2]
            - bbox[0]
        )


        if largura <= largura_max:

            atual = teste

        else:

            if atual:

                linhas.append(
                    atual
                )

            atual = palavra


    if atual:

        linhas.append(
            atual
        )


    return linhas


# ============================================================
# CTA
# ============================================================

def desenhar_cta(
    draw,
    texto,
):

    texto = limpar_texto(
        texto
    )

    if not texto:

        return


    palavras = texto.split()

    if len(palavras) > 4:

        texto = " ".join(
            palavras[:4]
        )


    fonte = fonte_montserrat(
        25,
        "bold",
    )


    padding_x = 28
    padding_y = 15


    bbox = draw.textbbox(
        (0, 0),
        texto,
        font=fonte,
    )


    largura = (
        bbox[2]
        - bbox[0]
    )

    altura = (
        bbox[3]
        - bbox[1]
    )


    largura_caixa = min(
        largura
        + padding_x * 2,
        440,
    )


    x = 62

    y = CANVAS_H - 215


    draw.rounded_rectangle(

        (
            x,
            y,
            x + largura_caixa,
            y
            + altura
            + padding_y * 2,
        ),

        radius=16,

        outline=YELLOW,

        width=3,

        fill=(
            7,
            18,
            39,
        ),

    )


    draw.text(

        (
            x + padding_x,
            y + padding_y - 2,
        ),

        texto,

        font=fonte,

        fill=WHITE,

    )


# ============================================================
# ARTE FINAL
# ============================================================

def renderizar_arte_final(
    image_bytes: bytes,
    headline_texto: str,
    subtextos: Optional[list] = None,
    cta: str = "",
    exibir_assinatura: bool = True,
):

    subtextos = (
        subtextos or []
    )


    img = preparar_canvas_4x5(
        image_bytes
    )

    img = aplicar_tratamento_vertice(
        img
    )


    draw = ImageDraw.Draw(
        img
    )


    # --------------------------------------------------------
    # LINHA
    # --------------------------------------------------------

    desenhar_linha_amarela(
        draw,
        62,
        82,
        150,
        5,
    )


    # --------------------------------------------------------
    # HEADLINE
    # --------------------------------------------------------

    headline = limpar_texto(
        headline_texto
    )


    if not headline:

        headline = (
            "conteúdo que "
            "comunica valor."
        )


    # segurança
    palavras = headline.split()

    if len(palavras) > 10:

        headline = " ".join(
            palavras[:10]
        )


    fonte_headline = (
        fonte_montserrat(
            82,
            "extrabold",
        )
    )


    linhas = quebrar_texto(
        draw,
        headline,
        fonte_headline,
        650,
    )[:4]


    y = 145


    for indice, linha in enumerate(
        linhas
    ):

        cor = (

            WHITE

            if indice
            < len(linhas) - 1

            else YELLOW

        )


        draw.text(

            (
                62,
                y,
            ),

            linha,

            font=fonte_headline,

            fill=cor,

        )


        bbox = draw.textbbox(

            (
                62,
                y,
            ),

            linha,

            font=fonte_headline,

        )


        y += (

            bbox[3]
            - bbox[1]

        ) + 8


    # --------------------------------------------------------
    # APOIOS
    # --------------------------------------------------------

    apoios_validos = []

    for texto in subtextos[:2]:

        texto = limpar_texto(
            texto
        )

        if not texto:

            continue

        palavras_apoio = (
            texto.split()
        )

        if len(
            palavras_apoio
        ) > 7:

            texto = " ".join(
                palavras_apoio[:7]
            )

        apoios_validos.append(
            texto
        )


    if apoios_validos:

        fonte_sub = (
            fonte_montserrat(
                28,
                "bold",
            )
        )

        y_sub = min(
            y + 30,
            720,
        )


        for texto in (
            apoios_validos
        ):

            linhas_sub = (
                quebrar_texto(
                    draw,
                    texto,
                    fonte_sub,
                    570,
                )[:2]
            )


            for linha in (
                linhas_sub
            ):

                draw.text(

                    (
                        62,
                        y_sub,
                    ),

                    linha,

                    font=fonte_sub,

                    fill=WHITE,

                )


                bbox = (
                    draw.textbbox(
                        (
                            62,
                            y_sub,
                        ),
                        linha,
                        font=fonte_sub,
                    )
                )


                y_sub += (
                    bbox[3]
                    - bbox[1]
                ) + 7


            y_sub += 12


    # --------------------------------------------------------
    # CTA
    # --------------------------------------------------------

    if cta:

        desenhar_cta(
            draw,
            cta,
        )


    # --------------------------------------------------------
    # ASSINATURA
    # --------------------------------------------------------

    if exibir_assinatura:

        desenhar_assinatura(
            draw
        )


    return img


# ============================================================
# LEGENDA
# ============================================================

def exibir_legenda(
    conteudo: dict,
):

    legenda = limpar_texto(
        conteudo.get(
            "legenda",
            "",
        )
    )


    hashtags = normalizar_lista(
        conteudo.get(
            "hashtags",
            [],
        )
    )[:5]


    if not legenda:

        st.warning(
            "A legenda não foi retornada pelo Gemini."
        )

        return


    st.markdown(

        '<div class="caption-box">'
        '<div class="caption-title">'
        '📝 Legenda pronta'
        '</div>',

        unsafe_allow_html=True,
    )


    st.write(
        legenda
    )


    if hashtags:

        st.write(
            " ".join(
                hashtags
            )
        )


    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


# ============================================================
# PASSO 0 — FORMATO
# ============================================================

if (
    st.session_state.formato
    is None
):

    st.subheader(
        "Olá Jean Victor! O que vamos criar hoje?"
    )


    fmt = st.radio(

        "Selecione o formato:",

        [

            "Post Único (4:5)",

            "Carrossel (4:5)",

            "Reels (Apenas Roteiro)",

        ],

    )


    if st.button(
        "Confirmar Formato"
    ):

        st.session_state.formato = (
            fmt
        )

        st.session_state.etapa = 1

        st.rerun()


# ============================================================
# ETAPA 1 — PRODUTO
# ============================================================

elif (
    st.session_state.etapa
    == 1
):

    st.info(

        f"📌 Formato selecionado: "
        f"**{st.session_state.formato}**"

    )


    st.subheader(
        "ETAPA 1: Qual é o Produto?"
    )


    prod = st.radio(

        "Selecione:",

        list(
            MAPA_PRODUTOS.keys()
        ),

    )


    if st.button(
        "Avançar para Etapa 2"
    ):

        st.session_state.produto = (
            prod
        )

        st.session_state.etapa = 2

        st.rerun()


# ============================================================
# ETAPA 2 — COMO DEFINIR O CONTEÚDO
# ============================================================

elif (
    st.session_state.etapa
    == 2
):

    st.info(

        f"📌 Formato: "
        f"**{st.session_state.formato}**"

    )


    st.subheader(
        "ETAPA 2: Como vamos definir o conteúdo?"
    )


    op = st.radio(

        "Selecione:",

        [

            "1️⃣ Já tenho ideia",

            "2️⃣ Quero ideias estratégicas",

        ],

    )


    paginas = 1


    if (
        st.session_state.formato
        == "Carrossel (4:5)"
    ):

        paginas = st.number_input(

            "Quantidade de páginas:",

            min_value=3,

            max_value=10,

            value=5,

        )


    if st.button(
        "Avançar"
    ):

        st.session_state.opcao_ideia = (
            op
        )

        st.session_state.num_paginas = (
            paginas
        )

        st.session_state.etapa = 3

        st.rerun()


# ============================================================
# ETAPA 3 — IDEIA
# ============================================================

elif (
    st.session_state.etapa
    == 3
):

    modulo = importlib.import_module(

        MAPA_PRODUTOS[
            st.session_state.produto
        ]

    )


    st.info(

        f"📌 Produto: "
        f"**{st.session_state.produto}**"

    )


    # --------------------------------------------------------
    # SUGESTÕES
    # --------------------------------------------------------

    if (
        st.session_state.opcao_ideia
        == "2️⃣ Quero ideias estratégicas"
    ):

        st.subheader(
            "ETAPA 3: Escolha uma ideia"
        )


        if not st.session_state.ideias_lista:

            if not GEMINI_API_KEY:

                st.error(
                    "GEMINI_API_KEY não configurada."
                )

                st.stop()


            with st.spinner(
                "Consultando a base de conhecimento..."
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

                st.session_state.ideia_escolhida = (
                    ideia
                )

                st.session_state.etapa = 4

                st.rerun()


    # --------------------------------------------------------
    # IDEIA PRÓPRIA
    # --------------------------------------------------------

    else:

        st.subheader(
            "ETAPA 3: Digite sua ideia"
        )


        ideia = st.text_area(

            "Sua ideia:",

            height=120,

            placeholder=(
                "Ex.: seu dashboard tem muitos números, "
                "mas pouca clareza."
            ),

        )


        if ideia.strip():

            if st.button(
                "🚀 Criar conteúdo"
            ):

                st.session_state.ideia_escolhida = (
                    ideia.strip()
                )

                st.session_state.etapa = 4

                st.rerun()


# ============================================================
# ETAPA 4 — GERAÇÃO DIRETA
# ============================================================

elif (
    st.session_state.etapa
    == 4
):

    modulo = importlib.import_module(

        MAPA_PRODUTOS[
            st.session_state.produto
        ]

    )


    if not GEMINI_API_KEY:

        st.error(
            "GEMINI_API_KEY não configurada."
        )

        st.stop()


    # --------------------------------------------------------
    # GERA CONTEÚDO
    # --------------------------------------------------------

    if not st.session_state.conteudo_gerado:

        with st.spinner(
            "Construindo conteúdo estratégico..."
        ):

            try:

                st.session_state.conteudo_gerado = (

                    gerar_conteudo_final(

                        GEMINI_API_KEY,

                        st.session_state.ideia_escolhida,

                        st.session_state.formato,

                        st.session_state.num_paginas or 1,

                        modulo.CONHECIMENTO,

                    )

                )


                st.session_state.pagina_atual = 0

                st.session_state.imagem_processada_bytes = (
                    None
                )


            except Exception as erro:

                st.error(
                    f"Erro ao construir conteúdo: {erro}"
                )

                st.stop()


    conteudo = (
        st.session_state.conteudo_gerado
    )


    pagina_index = (
        st.session_state.pagina_atual
        or 0
    )


    paginas_conteudo = (
        conteudo.get(
            "paginas",
            [],
        )
    )


    # --------------------------------------------------------
    # POST = UMA PÁGINA
    # --------------------------------------------------------

    if (
        st.session_state.formato
        == "Post Único (4:5)"
    ):

        paginas_conteudo = (
            paginas_conteudo[:1]
        )


    if not paginas_conteudo:

        st.error(
            "O conteúdo não retornou uma página válida."
        )

        st.stop()


    pagina_index = min(

        pagina_index,

        len(
            paginas_conteudo
        ) - 1,

    )


    pagina = (
        paginas_conteudo[
            pagina_index
        ]
    )


    # ========================================================
    # REELS
    # ========================================================

    if (
        st.session_state.formato
        == "Reels (Apenas Roteiro)"
    ):

        st.subheader(
            "🎬 Roteiro do Reels"
        )


        st.write(
            conteudo.get(
                "legenda",
                "",
            )
        )


        if conteudo.get(
            "hashtags"
        ):

            st.write(

                " ".join(

                    conteudo[
                        "hashtags"
                    ][:5]

                )

            )


        st.stop()


    # ========================================================
    # ASSINATURA
    # ========================================================

    exibir_assinatura = (

        st.session_state.formato
        == "Post Único (4:5)"

    )


    if (
        st.session_state.formato
        == "Carrossel (4:5)"
    ):

        exibir_assinatura = (

            pagina_index
            == len(
                paginas_conteudo
            ) - 1

        )


    # ========================================================
    # GERAÇÃO DA ARTE
    # ========================================================

    if not st.session_state.imagem_processada_bytes:

        with st.spinner(

            "Gerando fotografia e "
            "composição Vértice..."

        ):

            try:

                prompt_visual = (
                    pagina.get(
                        "prompt_visual",
                        "",
                    )
                )


                if not prompt_visual:

                    prompt_visual = """

Specific premium commercial scene
directly related to the content topic.
Hyper-realistic editorial photography.
Sophisticated professional environment.
Deep navy blue and royal blue atmosphere.
Main subject on the right.
Clean negative space on the left.
Elegant cinematic blue lighting.
Realistic materials.
No generic office decoration.
"""


                raw_bytes = (
                    gerar_fundo_ideogram(
                        prompt_visual
                    )
                )


                imagem_final = (
                    renderizar_arte_final(

                        raw_bytes,

                        pagina.get(
                            "headline",
                            "",
                        ),

                        pagina.get(
                            "apoios",
                            [],
                        ),

                        pagina.get(
                            "cta",
                            "",
                        ),

                        exibir_assinatura,

                    )
                )


                buffer = io.BytesIO()


                imagem_final.save(

                    buffer,

                    format="PNG",

                    optimize=True,

                )


                st.session_state.imagem_processada_bytes = (
                    buffer.getvalue()
                )


            except Exception as erro:

                st.error(
                    f"Erro na geração da imagem: {erro}"
                )

                st.stop()


    # ========================================================
    # RESULTADO
    # ========================================================

    st.subheader(
        "✨ Arte Final — Vértice"
    )


    col_esq, col_centro, col_dir = (
        st.columns(
            [0.8, 2, 0.8]
        )
    )


    with col_centro:

        st.image(

            st.session_state.imagem_processada_bytes,

            caption=(
                "1080x1350 • 4:5 • "
                "Composição Vértice"
            ),

            use_container_width=True,

        )


    st.download_button(

        label=(
            "📥 Baixar Arte Final "
            "(PNG Alta Resolução)"
        ),

        data=(
            st.session_state
            .imagem_processada_bytes
        ),

        file_name=(
            "vertice_arte_final.png"
        ),

        mime="image/png",

    )


    # ========================================================
    # LEGENDA
    # ========================================================

    exibir_legenda(
        conteudo
    )


    # ========================================================
    # CARROSSEL
    # ========================================================

    if (

        st.session_state.formato
        == "Carrossel (4:5)"

        and len(
            paginas_conteudo
        ) > 1

    ):

        st.divider()


        st.write(

            f"Página "
            f"{pagina_index + 1} "
            f"de "
            f"{len(paginas_conteudo)}"

        )


        if (
            pagina_index + 1
            < len(paginas_conteudo)
        ):

            if st.button(
                "➡️ Gerar próxima página"
            ):

                st.session_state.pagina_atual = (
                    pagina_index + 1
                )

                st.session_state.imagem_processada_bytes = (
                    None
                )

                st.rerun()


        else:

            st.success(
                "Carrossel concluído."
            )


    # ========================================================
    # NOVA ARTE
    # ========================================================

    st.divider()


    if st.button(
        "🔄 Gerar outra arte"
    ):

        st.session_state.imagem_processada_bytes = (
            None
        )

        st.rerun()
