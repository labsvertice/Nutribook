import io
import json
import os
import re
import importlib
import unicodedata
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
    .stApp {
        background-color:#0b1120;
        color:#ffffff;
    }

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

    /* Remove o pequeno ícone/link automático do título */
    h1.titulo-vertice a,
    h1.titulo-vertice button {
        display:none !important;
    }

    p.subtitulo-vertice {
        color:#8892b0 !important;
        font-family:'Montserrat',sans-serif !important;
        font-size:1.1rem !important;
        margin-top:4px !important;
    }

    hr {
        border-color:#1e2d4a !important;
    }

    .caption-box {
        background:#0e1d35;
        border:1px solid #243b63;
        border-radius:12px;
        padding:18px 20px;
        margin-top:14px;
    }

    .caption-title {
        color:#f4c70f;
        font-weight:800;
        margin-bottom:8px;
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
        st.image(
            "logo.png",
            width=125,
        )
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
    st.error(
        "Erro ao carregar configurações do perfil."
    )
    st.stop()


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
# ESTADOS DO FLUXO
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


def resetar_fluxo():

    for key in ESTADOS:
        st.session_state[key] = None

    st.session_state.etapa = 0


# ============================================================
# SIDEBAR — PRESERVADA
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

    for chave, (
        nome,
        url,
    ) in fontes.items():

        if not os.path.exists(nome):

            try:

                resposta = requests.get(
                    url,
                    timeout=15,
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
# UTILITÁRIOS DE TEXTO
# ============================================================

def corrigir_encoding(texto: str) -> str:

    texto = texto or ""

    sinais = [
        "Ã",
        "Â",
        "â",
        "�",
        "ð",
        "œ",
    ]

    if any(
        sinal in texto
        for sinal in sinais
    ):

        try:

            corrigido = (
                texto
                .encode("latin1")
                .decode("utf-8")
            )

            return corrigido

        except Exception:
            pass

    return texto


def limpar_texto(
    texto: str,
) -> str:

    texto = texto or ""

    texto = corrigir_encoding(
        texto
    )

    texto = re.sub(
        r"\*\*",
        "",
        texto,
    )

    texto = texto.replace(
        "“",
        "",
    )

    texto = texto.replace(
        "”",
        "",
    )

    texto = texto.replace(
        "📌",
        "",
    )

    return " ".join(
        texto.split()
    ).strip()


def limpar_texto_para_imagem(
    texto: str,
) -> str:

    texto = limpar_texto(
        texto
    )

    # Remove emojis e símbolos que
    # podem causar problemas na renderização PIL.
    resultado = []

    for caractere in texto:

        categoria = unicodedata.category(
            caractere
        )

        if (
            categoria.startswith("L")
            or categoria.startswith("N")
            or categoria.startswith("P")
            or caractere.isspace()
            or caractere in "•–—"
        ):
            resultado.append(
                caractere
            )

    return "".join(
        resultado
    ).strip()


# ============================================================
# JSON
# ============================================================

def extrair_json_resposta(
    texto: str,
):

    texto = (
        texto or ""
    ).strip()

    texto = re.sub(
        r"^```(?:json)?\s*",
        "",
        texto,
        flags=re.IGNORECASE,
    )

    texto = re.sub(
        r"\s*```$",
        "",
        texto,
    )

    try:

        return json.loads(
            texto
        )

    except Exception:
        pass

    inicio_obj = texto.find(
        "{"
    )

    fim_obj = texto.rfind(
        "}"
    )

    if (
        inicio_obj >= 0
        and fim_obj > inicio_obj
    ):

        try:

            return json.loads(
                texto[
                    inicio_obj:
                    fim_obj + 1
                ]
            )

        except Exception:
            pass

    raise ValueError(
        "O Gemini não retornou JSON válido."
    )


def normalizar_lista(
    valor,
):

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
            limpar_texto(
                valor
            )
        ]

    return []


# ============================================================
# NORMALIZAÇÃO DO CONTEÚDO
# ============================================================

def limitar_palavras(
    texto: str,
    limite: int,
) -> str:

    texto = limpar_texto(
        texto
    )

    palavras = texto.split()

    if len(palavras) <= limite:
        return texto

    return " ".join(
        palavras[:limite]
    ).rstrip(
        ".,!?;:"
    )


def normalizar_conteudo(
    dados: dict,
    formato: str,
) -> dict:

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
    # POST = EXATAMENTE 1 PÁGINA
    # --------------------------------------------------------

    if formato == "Post Único (4:5)":

        if paginas:
            pagina = paginas[0]

        else:
            pagina = dados.get(
                "pagina",
                {},
            )

        if not isinstance(
            pagina,
            dict,
        ):
            pagina = {}

        resultado["paginas"] = [
            pagina
        ]


    else:

        resultado["paginas"] = (
            paginas
        )


    pagina_normalizada = []


    for pagina in resultado[
        "paginas"
    ]:

        if not isinstance(
            pagina,
            dict,
        ):
            pagina = {}


        headline = limitar_palavras(
            pagina.get(
                "headline",
                "",
            ),
            8,
        )


        apoios = []

        for apoio in normalizar_lista(
            pagina.get(
                "apoios",
                [],
            )
        )[:2]:

            apoio = limitar_palavras(
                apoio,
                6,
            )

            if apoio:
                apoios.append(
                    apoio
                )


        cta = limitar_palavras(
            pagina.get(
                "cta",
                "",
            ),
            6,
        )


        # Nunca deixar o bordão entrar
        # automaticamente na arte.
        if re.search(
            r"vamos transformar seus dados em decisão",
            cta,
            flags=re.IGNORECASE,
        ):
            cta = ""


        prompt_visual = limpar_texto(
            pagina.get(
                "prompt_visual",
                "",
            )
        )


        pagina_normalizada.append(
            {
                "headline":
                    headline,

                "apoios":
                    apoios,

                "cta":
                    cta,

                "prompt_visual":
                    prompt_visual,
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
                    limitar_palavras(
                        dados.get(
                            "headline",
                            "",
                        ),
                        8,
                    ),

                "apoios":
                    normalizar_lista(
                        dados.get(
                            "apoios",
                            [],
                        )
                    )[:2],

                "cta":
                    limitar_palavras(
                        dados.get(
                            "cta",
                            "",
                        ),
                        6,
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


    # --------------------------------------------------------
    # GARANTIA DE LEGENDA
    # --------------------------------------------------------

    if not resultado[
        "legenda"
    ]:

        headline_fallback = (
            resultado[
                "paginas"
            ][0].get(
                "headline",
                "",
            )
        )

        if headline_fallback:

            resultado[
                "legenda"
            ] = (
                headline_fallback
            )


    return resultado


# ============================================================
# IMAGEM — CANVAS FINAL 1080x1350
# ============================================================

def preparar_canvas_4x5(
    image_bytes: bytes,
) -> Image.Image:

    base = Image.open(
        io.BytesIO(
            image_bytes
        )
    ).convert(
        "RGB"
    )


    proporcao_alvo = (
        CANVAS_W
        / CANVAS_H
    )

    proporcao_base = (
        base.width
        / base.height
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
            )
            // 2,
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
            )
            // 2,
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
) -> Image.Image:

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
        (
            0,
            0,
            0,
            0,
        ),
    )

    draw = ImageDraw.Draw(
        overlay
    )

    largura, altura = (
        img.size
    )


    # --------------------------------------------------------
    # PROTEÇÃO DA ÁREA ESQUERDA
    # --------------------------------------------------------

    limite_esquerdo = int(
        largura * 0.72
    )

    for x in range(
        limite_esquerdo
    ):

        proporcao = (
            x
            / limite_esquerdo
        )

        alpha = int(
            175
            * (
                1
                - proporcao
            ) ** 1.30
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

    limite_superior = int(
        altura * 0.30
    )

    for y in range(
        limite_superior
    ):

        proporcao = (
            y
            / limite_superior
        )

        alpha = int(
            80
            * (
                1
                - proporcao
            ) ** 1.70
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
# ELEMENTOS GRÁFICOS
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


    nome = (
        "Jean Victor"
    )

    sub = (
        "Dados • Comunicação • Conteúdo Inteligente"
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
            - 115,
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
            - 65,
        ),
        sub,
        font=fonte_sub,
        fill=GRAY,
    )


# ============================================================
# CTA
# ============================================================

def desenhar_cta(
    draw,
    texto,
):

    texto = (
        limpar_texto_para_imagem(
            texto
        )
    )

    if not texto:
        return


    texto = limitar_palavras(
        texto,
        6,
    )


    fonte = fonte_montserrat(
        24,
        "bold",
    )

    padding_x = 28
    padding_y = 16


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
        CANVAS_W - 124,
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
        radius=18,
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
# RENDERIZAÇÃO FINAL
# ============================================================

def renderizar_arte_final(
    image_bytes: bytes,
    headline_texto: str,
    subtextos: Optional[list] = None,
    cta: str = "",
    exibir_assinatura: bool = True,
) -> Image.Image:

    subtextos = (
        subtextos
        or []
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
    # LINHA VÉRTICE
    # --------------------------------------------------------

    desenhar_linha_amarela(
        draw,
        62,
        82,
    )


    # --------------------------------------------------------
    # HEADLINE
    # --------------------------------------------------------

    headline = (
        limpar_texto_para_imagem(
            headline_texto
        )
    )


    if not headline:

        headline = (
            "conteúdo que comunica valor."
        )


    headline = limitar_palavras(
        headline,
        8,
    )


    fonte_headline = fonte_montserrat(
        82,
        "extrabold",
    )


    linhas = quebrar_texto(
        draw,
        headline,
        fonte_headline,
        largura_max=650,
    )[:3]


    y = 145


    for indice, linha in enumerate(
        linhas
    ):

        cor = (
            WHITE
            if indice
            < max(
                1,
                len(linhas) - 1,
            )
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
        ) + 10


    # --------------------------------------------------------
    # APOIOS
    # --------------------------------------------------------

    if subtextos:

        fonte_sub = fonte_montserrat(
            28,
            "bold",
        )


        y_sub = min(
            y + 28,
            720,
        )


        for texto in subtextos[:2]:

            texto = (
                limpar_texto_para_imagem(
                    texto
                )
            )


            texto = limitar_palavras(
                texto,
                6,
            )


            if not texto:
                continue


            linhas_sub = quebrar_texto(
                draw,
                texto,
                fonte_sub,
                largura_max=540,
            )[:1]


            for linha in linhas_sub:

                draw.text(
                    (
                        62,
                        y_sub,
                    ),
                    linha,
                    font=fonte_sub,
                    fill=WHITE,
                )


                bbox = draw.textbbox(
                    (
                        62,
                        y_sub,
                    ),
                    linha,
                    font=fonte_sub,
                )


                y_sub += (
                    bbox[3]
                    - bbox[1]
                ) + 6


            y_sub += 8


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
# QUEBRA DE TEXTO
# ============================================================

def quebrar_texto(
    draw,
    texto,
    font,
    largura_max,
):

    texto = (
        limpar_texto_para_imagem(
            texto
        )
    )

    palavras = texto.split()


    if not palavras:
        return []


    linhas = []

    atual = ""


    for palavra in palavras:

        teste = (
            palavra
            if not atual
            else f"{atual} {palavra}"
        )


        bbox = draw.textbbox(
            (0, 0),
            teste,
            font=font,
        )


        if (
            bbox[2]
            - bbox[0]
            <= largura_max
        ):

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
# GEMINI — IDEIAS
# ============================================================

def gerar_ideias_gemini(
    api_key: str,
    base_conhecimento: str,
) -> list:

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
Você é o estrategista de conteúdo da Plataforma Vértice — Jean Victor.

BASE DE CONHECIMENTO:
{base_conhecimento}

Gere EXATAMENTE 5 ideias de conteúdo para Instagram.

DISTRIBUIÇÃO:
- descoberta
- conteúdo técnico
- posicionamento

REGRAS ABSOLUTAS:

1. Cada ideia deve ter NO MÁXIMO 12 palavras.
2. Cada ideia deve ser UMA única frase.
3. A ideia deve funcionar como HOOK ou TEMA.
4. Deve ser compreendida rapidamente.
5. Deve ser específica à base de conhecimento.
6. Deve ser estratégica.
7. Deve ser curta.
8. Deve ser variada.
9. Não seja genérico.
10. Não seja motivacional.
11. Não seja professoral.
12. Não explique a ideia.
13. Não justifique a ideia.
14. Não descreva o formato da publicação.
15. Não use "Post", "Carrossel", "Estudo de caso", "Manifesto" etc.
16. Não coloque categoria.
17. Não coloque CTA.
18. Não coloque hashtags.
19. Não use emojis.
20. Não use bordões.
21. NÃO use "Vamos transformar seus dados em decisão?"
22. NÃO use qualquer outro bordão comercial.
23. NÃO transforme a ideia em briefing.

EXEMPLOS:

ERRADO:
"Post comparativo mostrando o impacto de uma decisão tomada por feeling versus indicadores integrados."

CERTO:
"Achismo ou dados: qual decide melhor?"

ERRADO:
"Estudo de caso sobre como um gestor economizou horas cruzando dados manualmente."

CERTO:
"Quanto tempo sua empresa perde cruzando planilhas?"

ERRADO:
"Chamada forte para ação provocando o empresário que ainda gerencia a empresa no achismo."

CERTO:
"Decidir no achismo custa mais do que parece."

RETORNE SOMENTE JSON VÁLIDO:

{{
  "ideias": [
    "ideia 1",
    "ideia 2",
    "ideia 3",
    "ideia 4",
    "ideia 5"
  ]
}}
"""


    resposta = model.generate_content(
        prompt
    )


    ideias = []


    try:

        dados = extrair_json_resposta(
            resposta.text
        )

        ideias = dados.get(
            "ideias",
            [],
        )

    except Exception:

        linhas = [
            linha.strip()
            for linha
            in resposta.text.splitlines()
            if linha.strip()
        ]

        ideias = linhas


    ideias_finais = []


    for ideia in ideias:

        ideia = limpar_texto(
            str(ideia)
        )


        ideia = re.sub(
            r"^\d+[\.\)]\s*",
            "",
            ideia,
        ).strip()


        ideia = re.sub(
            r"^\[(descoberta|conteúdo técnico|posicionamento)\]\s*",
            "",
            ideia,
            flags=re.IGNORECASE,
        ).strip()


        ideia = re.sub(
            r"vamos transformar seus dados em decisão[?!\.]*",
            "",
            ideia,
            flags=re.IGNORECASE,
        ).strip()


        # Remove emojis.
        ideia = "".join(
            caractere
            for caractere in ideia
            if not unicodedata.category(
                caractere
            ).startswith("So")
        )


        ideia = limitar_palavras(
            ideia,
            12,
        )


        if ideia:
            ideias_finais.append(
                ideia
            )


    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    fallback = [

        "Achismo ou dados: qual decide melhor?",

        "Seu dashboard informa ou ajuda a decidir?",

        "Dashboard bonito não significa decisão melhor.",

        "Quanto tempo sua empresa perde cruzando planilhas?",

        "O problema não é o Excel.",
    ]


    for ideia in fallback:

        if (
            ideia
            not in ideias_finais
            and len(ideias_finais)
            < 5
        ):

            ideias_finais.append(
                ideia
            )


    return ideias_finais[:5]


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
) -> dict:

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
Gere EXATAMENTE 1 página.

NUNCA gere página 2.
NUNCA gere página 3.
NUNCA trate o post como carrossel.

O post deve comunicar UMA única ideia.
"""


    elif formato == "Carrossel (4:5)":

        instrucoes_formato = f"""
FORMATO: CARROSSEL.

Gere EXATAMENTE {paginas} páginas.

Cada página deve ter uma única ideia.
Nunca coloque duas páginas dentro de uma mesma página.
"""


    else:

        instrucoes_formato = """
FORMATO: REELS.

Não gerar imagem.
Gerar somente roteiro.
"""


    prompt = f"""
Você é o estrategista de conteúdo premium da Plataforma Vértice — Jean Victor.

IDEIA ESCOLHIDA:
{ideia}

{instrucoes_formato}

BASE DE CONHECIMENTO DO PRODUTO:
{base_conhecimento}

==================================================
REGRA CENTRAL
==================================================

A base de conhecimento define o universo do produto.

Não invente:
- funcionalidades;
- benefícios;
- números;
- resultados;
- informações.

A ferramenta é meio, não protagonista.

Foque em:
- decisões;
- dores;
- falta de clareza;
- desorganização;
- perda;
- ganho;
- produtividade;
- autoridade;
- percepção profissional;
- experiência do cliente.

==================================================
TOM
==================================================

Estratégico.
Direto.
Provocativo quando fizer sentido.
Premium.
Claro.

Nunca:
- motivacional;
- genérico;
- professoral;
- amigável demais;
- técnico demais.

==================================================
COPY DA ARTE
==================================================

A arte deve ser compreendida em até 3 segundos.

HEADLINE:
- 3 a 8 palavras;
- forte;
- memorável;
- objetiva;
- máximo absoluto de 8 palavras.

APOIOS:
- no máximo 2;
- máximo 6 palavras cada;
- só usar se forem realmente necessários;
- nunca explicar o assunto.

CTA:
- máximo 6 palavras;
- somente quando fizer sentido;
- não usar bordão automaticamente;
- NÃO usar "Vamos transformar seus dados em decisão?"

REGRA DE OURO:

Se retirar 50% do texto e a mensagem continuar clara,
retire o texto.

==================================================
POST
==================================================

O post deve ter:
- UMA headline;
- no máximo 2 apoios curtos;
- CTA opcional;
- UMA ideia principal.

Nunca transformar o post em carrossel.

==================================================
CARROSSEL
==================================================

Cada página:
- uma ideia;
- uma headline;
- apoio mínimo;
- sem parágrafos;
- sem explicações longas.

==================================================
VISUAL
==================================================

Identidade Vértice:

- azul navy profundo;
- azul royal sofisticado;
- azul moderno tecnológico;
- branco;
- amarelo #F4C70F;
- Montserrat ExtraBold/Bold;
- visual premium;
- editorial;
- moderno;
- limpo;
- sofisticado;
- respiro visual;
- profundidade;
- iluminação azul elegante.

O azul deve permanecer VISIVELMENTE azul.

PROIBIDO ABSOLUTAMENTE:

- folhas;
- plantas;
- ramos;
- folhagens;
- flores;
- elementos botânicos;
- estética naturalista;
- estética tropical;
- decoração vegetal;
- logos;
- logotipos;
- marcas;
- marcas d'água;
- texto;
- palavras;
- letras;
- tipografia;
- gráficos;
- infográficos;
- interfaces;
- telas com texto;
- ilustrações;
- CGI;
- 3D;
- mockups desnecessários.

O gerador de imagem deve produzir SOMENTE fotografia/fundo.

A tipografia será adicionada posteriormente pelo Python.

Preferir:

- fotografia hiper-realista;
- fotografia comercial premium;
- ambiente corporativo moderno;
- materiais reais;
- iluminação cinematográfica;
- azul sofisticado;
- profundidade de campo;
- composição limpa;
- assunto principal à direita ou centro-direita;
- área visual limpa à esquerda.

==================================================
LEGENDA
==================================================

A legenda é OBRIGATÓRIA.

Deve:
- complementar a arte;
- ser curta;
- ser estratégica;
- não repetir integralmente a headline;
- ter CTA natural;
- usar PT-BR;
- conter exatamente 5 hashtags.

Não colocar o bordão automaticamente.

==================================================
SAÍDA
==================================================

Retorne SOMENTE JSON válido.

Formato:

{{
  "categoria": "Descoberta | Conteúdo Técnico | Posicionamento",

  "objetivo": "Atrair | Ensinar | Fortalecer autoridade",

  "legenda": "legenda completa em PT-BR",

  "hashtags": [
    "#tag1",
    "#tag2",
    "#tag3",
    "#tag4",
    "#tag5"
  ],

  "paginas": [
    {{
      "headline": "headline de 3 a 8 palavras",

      "apoios": [
        "apoio de até 6 palavras"
      ],

      "cta": "CTA de até 6 palavras",

      "prompt_visual": "prompt em inglês SOMENTE para fotografia/fundo, sem texto, sem logo, sem plantas, sem folhas"
    }}
  ]
}}

IMPORTANTE:

POST:
"paginas" deve conter EXATAMENTE 1 item.

CARROSSEL:
"paginas" deve conter EXATAMENTE {paginas} itens.

O prompt_visual nunca deve pedir texto.

O prompt_visual nunca deve pedir logo.

O prompt_visual nunca deve pedir folhas ou plantas.

A legenda nunca pode ficar vazia.
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
# PROMPT VISUAL FINAL
# ============================================================

def construir_prompt_visual(
    prompt_base: str,
) -> str:

    prompt_base = limpar_texto(
        prompt_base
    )


    reforco = """
HYPER-REALISTIC PREMIUM EDITORIAL PHOTOGRAPHY.

Create only the photographic background.

Deep navy blue.
Sophisticated royal blue.
Clearly visible blue tones.
Elegant cinematic lighting.
Realistic materials.
Authentic professional environment.
Commercial photography.
Natural photographic textures.
Subtle depth of field.
Premium editorial composition.

Main subject preferably on the right or center-right.

Leave clean negative space on the left for typography.

ABSOLUTELY NO TEXT.
ABSOLUTELY NO WORDS.
ABSOLUTELY NO LETTERS.
ABSOLUTELY NO TYPOGRAPHY.
ABSOLUTELY NO LOGO.
ABSOLUTELY NO BRAND MARK.
ABSOLUTELY NO WATERMARK.

ABSOLUTELY NO LEAVES.
ABSOLUTELY NO PLANTS.
ABSOLUTELY NO BRANCHES.
ABSOLUTELY NO FOLIAGE.
ABSOLUTELY NO FLOWERS.
ABSOLUTELY NO BOTANICAL ELEMENTS.
ABSOLUTELY NO VEGETATION.

NO GRAPHICS.
NO INFOGRAPHICS.
NO UI.
NO SCREEN TEXT.
NO ILLUSTRATION.
NO CGI.
NO 3D RENDER.
NO MOCKUP.

The final image must look like authentic premium commercial photography.
"""


    return (
        prompt_base
        + "\n"
        + reforco
    )


# ============================================================
# IDEOGRAM
# ============================================================

def gerar_fundo_ideogram(
    prompt_visual: str,
) -> bytes:

    prompt_final = construir_prompt_visual(
        prompt_visual
    )


    output = replicate.run(
        "ideogram-ai/ideogram-v2",
        input={
            "prompt":
                prompt_final,

            "aspect_ratio":
                "3:4",

            "style_type":
                "Realistic",

            "magic_prompt_option":
                "Off",
        },
    )


    image_url = (
        str(output[0])
        if isinstance(
            output,
            list,
        )
        else str(output)
    )


    resposta = requests.get(
        image_url,
        timeout=90,
    )


    resposta.raise_for_status()


    return resposta.content


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

        return


    st.markdown(
        '<div class="caption-box">'
        '<div class="caption-title">📝 Legenda pronta</div>',
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
# FLUXO PRINCIPAL
# ============================================================

# ============================================================
# PASSO 0 — FORMATO
# ============================================================

if st.session_state.formato is None:

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

elif st.session_state.etapa == 1:

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
# ETAPA 2 — IDEIA
# ============================================================

elif st.session_state.etapa == 2:

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
# ETAPA 3 — DEFINIÇÃO DA IDEIA
# ============================================================

elif st.session_state.etapa == 3:

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
    # IDEIAS GERADAS
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
    # IDEIA MANUAL
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
#
# A antiga etapa de estrutura/aprovação permanece eliminada.
# ============================================================

elif st.session_state.etapa == 4:

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

                st.session_state.imagem_processada_bytes = None


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
    # PROTEÇÃO ABSOLUTA DO POST
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
        len(paginas_conteudo) - 1,
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
    # GERAÇÃO DA ARTE
    # ========================================================

    if not st.session_state.imagem_processada_bytes:

        with st.spinner(
            "Gerando fotografia e aplicando composição Vértice..."
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
Premium modern corporate environment.
Hyper-realistic commercial photography.
Sophisticated navy blue and royal blue atmosphere.
Main subject on the right.
Clean negative space on the left.
Elegant cinematic lighting.
Authentic materials.
Professional editorial photography.
"""


                raw_bytes = (
                    gerar_fundo_ideogram(
                        prompt_visual
                    )
                )


                # ------------------------------------------------
                # ASSINATURA:
                # POST = SIM
                # CARROSSEL = SOMENTE ÚLTIMA PÁGINA
                # ------------------------------------------------

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
            < len(
                paginas_conteudo
            )
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


            if st.button(
                "🔄 Criar outro conteúdo"
            ):

                resetar_fluxo()
                st.rerun()


    # ========================================================
    # POST
    # ========================================================

    else:

        st.divider()


        if st.button(
            "🔄 Criar outro conteúdo"
        ):

            resetar_fluxo()
            st.rerun()
