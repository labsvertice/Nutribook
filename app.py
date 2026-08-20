import io
import json
import os
import re
import importlib
import random
from difflib import SequenceMatcher
from typing import Optional

import requests
import streamlit as st
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

# A única chave usada pelo app é a chave Gemini.
# A geração de texto e imagem passa diretamente pela API Gemini.
GEMINI_API_KEY = st.secrets.get(
    "GEMINI_API_KEY",
    "",
)

# ============================================================
# CONFIGURAÇÃO GEMINI
# ============================================================

GEMINI_TEXT_MODEL = "gemini-3.1-flash-lite"
GEMINI_IMAGE_MODEL = "gemini-3.1-flash-image-preview"

# Durante o desenvolvimento/testes usamos 1K.
# Depois da aprovação, altere SOMENTE para "2K".
GEMINI_IMAGE_SIZE = "1K"

GEMINI_API_BASE = (
    "https://generativelanguage.googleapis.com/v1beta"
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


# Histórico da sessão: usado apenas para impedir repetição de ideias.
# Não é apagado ao clicar em "Iniciar Novo Conteúdo".
if "historico_ideias" not in st.session_state:

    st.session_state.historico_ideias = []


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

    texto = " ".join(
        texto.split()
    ).strip()

    # Corrige mojibake comum (ex.: "nÃºmeros") sem alterar
    # texto legítimo em português.
    marcadores_mojibake = (
        "Ã", "Â", "â€", "ðŸ", "�"
    )

    if any(m in texto for m in marcadores_mojibake):
        try:
            corrigido = texto.encode("latin1").decode("utf-8")
            if "�" not in corrigido:
                texto = corrigido
        except Exception:
            pass

    return texto


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

                "direcao_visual":
                    limpar_texto(
                        pagina.get(
                            "direcao_visual",
                            "",
                        )
                    ),

                "sujeito_visual":
                    limpar_texto(
                        pagina.get(
                            "sujeito_visual",
                            "",
                        )
                    ),

                "acao_visual":
                    limpar_texto(
                        pagina.get(
                            "acao_visual",
                            "",
                        )
                    ),

                "ambiente_visual":
                    limpar_texto(
                        pagina.get(
                            "ambiente_visual",
                            "",
                        )
                    ),

                "enquadramento_visual":
                    limpar_texto(
                        pagina.get(
                            "enquadramento_visual",
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

def _normalizar_ideia_para_comparacao(texto: str) -> str:

    texto = limpar_texto(texto).lower()

    texto = re.sub(
        r"[^a-zà-ÿ0-9\s]",
        " ",
        texto,
    )

    return " ".join(texto.split())


def _ideia_muito_parecida(
    ideia: str,
    anteriores: list,
    limite: float = 0.66,
):

    atual = _normalizar_ideia_para_comparacao(
        ideia
    )

    if not atual:
        return True

    for anterior in anteriores:

        base = _normalizar_ideia_para_comparacao(
            anterior
        )

        if not base:
            continue

        if atual == base:
            return True

        similaridade = SequenceMatcher(
            None,
            atual,
            base,
        ).ratio()

        if similaridade >= limite:
            return True

    return False


def _limitar_ideia(
    ideia: str,
    max_palavras: int = 10,
):

    ideia = limpar_texto(
        ideia
    )

    ideia = re.sub(
        r"^(ideia|tema|sugestão)\s*:\s*",
        "",
        ideia,
        flags=re.IGNORECASE,
    )

    palavras = ideia.split()

    if len(palavras) > max_palavras:

        ideia = " ".join(
            palavras[:max_palavras]
        )

    return ideia.rstrip(
        ".;:-"
    )


def _gemini_generate_text(
    api_key: str,
    prompt: str,
    temperature: float = 0.7,
    response_json: bool = False,
):
    """Chamada REST direta à Gemini API, sem SDK legado."""

    if not api_key:
        raise ValueError("GEMINI_API_KEY não configurada.")

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt}
                ],
            }
        ],
        "generationConfig": {
            "temperature": temperature,
        },
    }

    if response_json:
        payload["generationConfig"]["responseMimeType"] = "application/json"

    url = (
        f"{GEMINI_API_BASE}/models/"
        f"{GEMINI_TEXT_MODEL}:generateContent"
        f"?key={api_key}"
    )

    resposta = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=120,
    )

    try:
        dados = resposta.json()
    except Exception:
        dados = {"raw": resposta.text}

    if resposta.status_code != 200:
        detalhe = dados.get("error", dados)
        raise RuntimeError(
            f"Gemini texto: HTTP {resposta.status_code}: {detalhe}"
        )

    try:
        partes = (
            dados["candidates"][0]
            ["content"]["parts"]
        )
        texto = "".join(
            parte.get("text", "")
            for parte in partes
            if isinstance(parte, dict)
        ).strip()
    except Exception as erro:
        raise RuntimeError(
            f"Gemini texto: resposta sem conteúdo utilizável: {dados}"
        ) from erro

    if not texto:
        raise RuntimeError(
            f"Gemini texto: modelo retornou resposta vazia: {dados}"
        )

    return texto


def gerar_ideias_gemini(
    api_key: str,
    base_conhecimento: str,
    historico: Optional[list] = None,
):

    historico = historico or []

    territorios = [
        "dor silenciosa",
        "erro comum",
        "contraste inesperado",
        "mito do mercado",
        "custo invisível",
        "pergunta incômoda",
        "sinal que o gestor ignora",
        "bastidor de uma decisão",
        "consequência prática",
        "mudança de perspectiva",
        "antes e depois conceitual",
        "opinião forte",
    ]

    territorios_selecionados = random.sample(
        territorios,
        5,
    )

    usadas = historico[-30:]

    historico_texto = "\n".join(
        f"- {x}"
        for x in usadas
    ) or "- nenhuma"

    rodada = random.randint(1000, 999999)

    prompt = f"""
Você é o estrategista de conteúdo premium
da Plataforma Vértice — Jean Victor.

BASE DE CONHECIMENTO:
{base_conhecimento}

RODADA DE CRIAÇÃO: {rodada}

Gere EXATAMENTE 5 ideias para Instagram.

Cada ideia deve usar UM território narrativo diferente:

1. {territorios_selecionados[0]}
2. {territorios_selecionados[1]}
3. {territorios_selecionados[2]}
4. {territorios_selecionados[3]}
5. {territorios_selecionados[4]}

Distribua naturalmente entre:
• descoberta
• conteúdo técnico
• posicionamento

REGRAS:
• máximo 10 palavras;
• preferência por 5 a 8 palavras;
• uma única frase;
• sem subtítulo;
• sem explicação;
• sem justificativa;
• cada ideia deve ter ângulo realmente diferente;
• não apenas troque palavras de uma mesma ideia;
• não repita a mesma dor;
• varie o vocabulário;
• seja específico ao produto;
• seja fácil de entender;
• provoque curiosidade quando fizer sentido.

NÃO FAÇA:
• mini textos;
• parágrafos;
• listas internas;
• emojis;
• CTA;
• hashtags;
• bordões;
• slogans;
• assinatura;
• frases institucionais.

A ideia é APENAS o tema/ângulo.

IDEIAS JÁ USADAS NESTA SESSÃO:
{historico_texto}

NENHUMA das 5 novas ideias pode ser igual
ou muito parecida com essas ideias.

Retorne SOMENTE 5 linhas numeradas.
"""

    texto = _gemini_generate_text(
        api_key,
        prompt,
        temperature=0.95,
    )

    candidatas = []

    for linha in texto.splitlines():

        linha = linha.strip()

        if not linha:
            continue

        linha = re.sub(
            r"^\d+[\.\)]\s*",
            "",
            linha,
        )

        linha = _limitar_ideia(
            linha,
            10,
        )

        if not linha:
            continue

        if _ideia_muito_parecida(
            linha,
            candidatas + usadas,
        ):
            continue

        candidatas.append(linha)

        if len(candidatas) == 5:
            break

    # Se o modelo não entregar 5 válidas, fazemos UMA segunda chamada.
    if len(candidatas) < 5:

        faltam = 5 - len(candidatas)

        prompt_reforco = f"""
Crie exatamente {faltam} ideias NOVAS para Instagram
sobre este produto:

{base_conhecimento}

Já aceitas:
{chr(10).join("- " + x for x in candidatas) or "- nenhuma"}

Já usadas:
{historico_texto}

REGRAS:
- máximo 8 palavras por ideia;
- ângulos totalmente diferentes;
- não repetir estrutura;
- não usar bordões;
- não usar CTA;
- não usar hashtags;
- não explicar;
- retornar somente as ideias numeradas.
"""

        texto_2 = _gemini_generate_text(
            api_key,
            prompt_reforco,
            temperature=1.0,
        )

        for linha in texto_2.splitlines():

            linha = re.sub(
                r"^\d+[\.\)]\s*",
                "",
                linha.strip(),
            )

            linha = _limitar_ideia(
                linha,
                10,
            )

            if not linha:
                continue

            if _ideia_muito_parecida(
                linha,
                candidatas + usadas,
            ):
                continue

            candidatas.append(linha)

            if len(candidatas) == 5:
                break

    return candidatas[:5]


# ============================================================
# GEMINI — CONTEÚDO FINAL
# ============================================================

@st.cache_data(show_spinner=False)
def gerar_conteudo_final(
    api_key: str,
    ideia: str,
    formato: str,
    paginas: int,
    base_conhecimento: str,
):

    if formato == "Post Único (4:5)":

        instrucoes_formato = """
FORMATO: POST ÚNICO.

"paginas" deve conter EXATAMENTE 1 item.
NUNCA gere página 2, página 3, carrossel ou continuação.
O post comunica UMA única ideia.
"""

    elif formato == "Carrossel (4:5)":

        instrucoes_formato = f"""
FORMATO: CARROSSEL.

"paginas" deve conter EXATAMENTE {paginas} itens.
Cada página possui UMA ideia principal.
"""

    else:

        instrucoes_formato = """
FORMATO: REELS.

Não gerar imagem.
Gerar apenas roteiro.
"""

    prompt = f"""
Você é o estrategista de conteúdo premium da Plataforma Vértice — Jean Victor.

IDEIA ESCOLHIDA:
{ideia}

{instrucoes_formato}

BASE DE CONHECIMENTO DO PRODUTO:
{base_conhecimento}

==================================================
ESTRATÉGIA
==================================================

Use a base de conhecimento como fonte principal.
Não invente funcionalidades, números, resultados ou promessas.

A comunicação deve ser estratégica, direta, provocativa e premium.
Evite conteúdo motivacional, genérico ou professoral.

==================================================
COPY DA ARTE
==================================================

A arte precisa ser compreendida em até 3 segundos.

POST:
- exatamente 1 página;
- headline de 3 a 8 palavras;
- no máximo 2 apoios;
- cada apoio com no máximo 6 palavras;
- CTA opcional, máximo 4 palavras;
- UMA única ideia.

CARROSSEL:
- exatamente {paginas} páginas;
- uma ideia por página;
- headline de 3 a 8 palavras;
- no máximo 1 apoio curto por página;
- CTA somente quando realmente necessário.

NUNCA inserir bordões, slogans ou assinatura institucional.
NUNCA usar automaticamente:
"Vamos transformar seus dados em decisão?"

==================================================
DIREÇÃO VISUAL — REGRA CRÍTICA
==================================================

A fotografia NÃO é decoração.
Ela precisa representar concretamente a ideia escolhida.

Antes de escrever o prompt visual, responda mentalmente:
"Se eu apagar todo o texto da arte, a fotografia ainda comunica a ideia?"
Se não, escolha outra cena.

NÃO use escritório genérico.
NÃO use automaticamente executivo olhando notebook.
NÃO use plantas, decoração vegetal ou cenas de stock genéricas.

Escolha UMA cena específica e visualmente inequívoca.
Prefira, conforme a ideia:
- objeto ou processo em destaque;
- pessoa realizando uma ação relacionada ao problema;
- contraste visual que represente a consequência;
- detalhe de trabalho;
- ambiente profissional somente quando ele for parte da ideia.

A cena deve ter:
- sujeito principal claro;
- ação ou situação clara;
- ambiente coerente;
- enquadramento fotográfico intencional;
- iluminação cinematográfica;
- espaço negativo à esquerda para o texto aplicado pelo Python.

IDENTIDADE VÉRTICE:
- navy profundo + azul royal/elétrico claramente visível;
- pequenos acentos amarelos;
- fotografia comercial premium;
- realista, sofisticada, moderna;
- profundidade e contraste;
- nunca cinza, nunca preta demais.

PROIBIDO NA FOTOGRAFIA:
- qualquer texto, palavra, letra ou número legível;
- logos, marcas, marcas d'água;
- gráficos, dashboards ou telas com informação legível;
- infográficos, pôsteres, slides, interfaces;
- ilustração, CGI, 3D, render;
- plantas, folhas, ramos, flores, vasos com vegetação.

IMPORTANTE: o gerador de imagem recebe a direção abaixo e deve produzir SOMENTE a fotografia.
Toda tipografia, headline, apoio, CTA e assinatura será aplicada posteriormente pelo Python.

==================================================
LEGENDA
==================================================

Legenda curta em PT-BR, complementar à arte, sem repetir integralmente a headline.
CTA natural e contextual. Exatamente 5 hashtags.

==================================================
SAÍDA
==================================================

Retorne SOMENTE JSON válido, sem markdown.

Formato:

{{
  "categoria": "Descoberta | Conteúdo Técnico | Posicionamento",
  "objetivo": "Atrair | Ensinar | Fortalecer autoridade",
  "legenda": "legenda curta em PT-BR",
  "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"],
  "paginas": [
    {{
      "headline": "headline curta",
      "apoios": ["apoio curto"],
      "cta": "CTA curto",
      "sujeito_visual": "main concrete subject in English",
      "acao_visual": "specific action or situation in English",
      "ambiente_visual": "specific real environment in English",
      "enquadramento_visual": "camera angle, lens feel and composition in English",
      "prompt_visual": "complete English photographic scene description",
      "direcao_visual": "short English art direction"
    }}
  ]
}}

REGRAS DO PROMPT VISUAL:
- escreva em INGLÊS;
- descreva somente fotografia/cena;
- não escreva headline, CTA ou qualquer texto;
- não peça telas com palavras ou números;
- não peça logos ou marcas;
- não peça plantas;
- seja específico à IDEIA ESCOLHIDA;
- uma única cena coerente.

POST: "paginas" = EXATAMENTE 1 item.
CARROSSEL: "paginas" = EXATAMENTE {paginas} itens.
"""

    texto = _gemini_generate_text(
        api_key,
        prompt,
        temperature=0.70,
        response_json=True,
    )

    dados = extrair_json_resposta(texto)

    return normalizar_conteudo(
        dados,
        formato,
    )


# ============================================================
# MOTOR VISUAL — VÉRTICE
# ============================================================

def construir_prompt_visual(
    prompt_base: str,
    direcao_visual: str = "",
    ideia: str = "",
    produto: str = "",
    sujeito_visual: str = "",
    acao_visual: str = "",
    ambiente_visual: str = "",
    enquadramento_visual: str = "",
):
    """Monta uma direção fotográfica fechada para o Gemini Image.

    O objetivo é impedir que o modelo transforme o post em uma
    foto corporativa genérica.
    """

    campos = {
        "IDEIA CENTRAL": ideia,
        "PRODUTO": produto,
        "SUJEITO PRINCIPAL": sujeito_visual,
        "AÇÃO / SITUAÇÃO": acao_visual,
        "AMBIENTE": ambiente_visual,
        "ENQUADRAMENTO": enquadramento_visual,
        "DIREÇÃO VISUAL": direcao_visual,
        "CENA COMPLETA": prompt_base,
    }

    blocos = []
    for titulo, valor in campos.items():
        valor = limpar_texto(valor)
        if valor:
            blocos.append(f"{titulo}: {valor}")

    reforco = """

ROLE: You are a premium commercial photographer, not a graphic designer.
Create ONE single coherent photograph that visually explains the central idea.

CRITICAL SEMANTIC RULE:
The photograph must make sense without any written text.
Do not make a generic office scene. Do not default to a business person looking at a laptop.
Choose the most literal and visually recognizable real-world situation for the idea.

VÉRTICE VISUAL IDENTITY:
Deep navy blue environment, clearly visible sophisticated royal/electric blue accents, restrained warm yellow accents, cinematic commercial lighting, premium editorial photography, realistic materials, realistic skin, natural proportions, sophisticated contrast, subtle depth of field.

COMPOSITION:
Vertical 4:5 composition. Main subject on the right or center-right. Keep the upper-left and left third visually calm and dark enough for typography added later. Do not place important objects behind the future headline. Strong focal point and clear visual hierarchy.

ABSOLUTE EXCLUSIONS:
No text. No words. No letters. No numbers. No readable screens. No labels. No signs. No logos. No brands. No watermarks. No UI. No dashboard interface. No infographic. No presentation slide. No poster. No graphic design. No illustration. No CGI. No 3D render. No artificial typography. No plants. No leaves. No branches. No foliage. No flowers. No vegetation.

The final image must look like a real photograph taken for a premium Brazilian business brand.
"""

    return "\n".join(blocos) + reforco


# ============================================================
# GEMINI IMAGE — GERAÇÃO VISUAL VÉRTICE
# ============================================================

def _extrair_imagem_generate_content(dados: dict) -> bytes:
    """Extrai a primeira imagem inline da resposta Gemini REST."""

    candidatos = dados.get("candidates", [])
    if not candidatos:
        raise RuntimeError(f"Gemini Image sem candidates: {dados}")

    partes = (
        candidatos[0]
        .get("content", {})
        .get("parts", [])
    )

    for parte in partes:
        inline = parte.get("inlineData") or parte.get("inline_data")
        if isinstance(inline, dict) and inline.get("data"):
            import base64
            return base64.b64decode(inline["data"])

    raise RuntimeError(
        "Gemini Image respondeu sem imagem utilizável."
    )


def _gerar_imagem_gemini(
    prompt_final: str,
    image_size: str = GEMINI_IMAGE_SIZE,
) -> bytes:
    """Gera uma única fotografia usando a API Gemini documentada."""

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY não configurada.")

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_final}
                ]
            }
        ],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {
                "aspectRatio": "4:5",
                "imageSize": image_size,
            },
        },
    }

    url = (
        f"{GEMINI_API_BASE}/models/"
        f"{GEMINI_IMAGE_MODEL}:generateContent"
    )

    resposta = requests.post(
        url,
        headers={
            "x-goog-api-key": GEMINI_API_KEY,
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=180,
    )

    try:
        dados = resposta.json()
    except Exception:
        dados = {"raw": resposta.text}

    if resposta.status_code != 200:
        detalhe = dados.get("error", dados)
        raise RuntimeError(
            f"Gemini Image: HTTP {resposta.status_code}: {detalhe}"
        )

    return _extrair_imagem_generate_content(dados)


def gerar_fundo_ideogram(
    prompt_visual: str,
    direcao_visual: str = "",
    ideia: str = "",
    produto: str = "",
    sujeito_visual: str = "",
    acao_visual: str = "",
    ambiente_visual: str = "",
    enquadramento_visual: str = "",
):
    """Nome histórico preservado; agora gera 100% via Gemini."""

    prompt_final = construir_prompt_visual(
        prompt_visual,
        direcao_visual,
        ideia,
        produto,
        sujeito_visual,
        acao_visual,
        ambiente_visual,
        enquadramento_visual,
    )

    return _gerar_imagem_gemini(
        prompt_final,
        GEMINI_IMAGE_SIZE,
    )


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
                "Criando 5 ângulos diferentes..."
            ):

                st.session_state.ideias_lista = (
                    gerar_ideias_gemini(
                        GEMINI_API_KEY,
                        modulo.CONHECIMENTO,
                        st.session_state.historico_ideias,
                    )
                )


            # Guarda apenas ideias efetivamente apresentadas.
            for ideia in st.session_state.ideias_lista:

                if ideia not in st.session_state.historico_ideias:

                    st.session_state.historico_ideias.append(
                        ideia
                    )

            st.session_state.historico_ideias = (
                st.session_state.historico_ideias[-50:]
            )

            st.rerun()


        for i, ideia in enumerate(
            st.session_state.ideias_lista
        ):

            if st.button(

                ideia,

                key=f"btn_ideia_{i}",

                use_container_width=False,

            ):

                st.session_state.ideia_escolhida = (
                    ideia
                )

                st.session_state.etapa = 4

                st.rerun()


        st.write("")

        if st.button(
            "🔄 Gerar outras 5 ideias",
            key="btn_novas_ideias",
        ):

            st.session_state.ideias_lista = None

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

            "Gerando fotografia Vértice..."

        ):

            try:

                prompt_visual = (
                    pagina.get(
                        "prompt_visual",
                        "",
                    )
                )

                direcao_visual = (
                    pagina.get(
                        "direcao_visual",
                        "",
                    )
                )


                if not prompt_visual:

                    prompt_visual = f"""

A specific real-world photographic scene
that visually represents this content:
{st.session_state.ideia_escolhida}.

Choose one strong concrete visual metaphor,
not a generic office.
The subject must be obvious from the scene.
Premium editorial commercial photography.
Main subject on the right.
Clean dark-blue negative space on the left.
"""


                raw_bytes = (
                    gerar_fundo_ideogram(
                        prompt_visual,
                        direcao_visual,
                        ideia=st.session_state.ideia_escolhida,
                        produto=st.session_state.produto,
                        sujeito_visual=pagina.get(
                            "sujeito_visual",
                            "",
                        ),
                        acao_visual=pagina.get(
                            "acao_visual",
                            "",
                        ),
                        ambiente_visual=pagina.get(
                            "ambiente_visual",
                            "",
                        ),
                        enquadramento_visual=pagina.get(
                            "enquadramento_visual",
                            "",
                        ),
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
