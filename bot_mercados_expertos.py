import os, re, sys, time, datetime, requests, tweepy
from dotenv import load_dotenv

# ====== CONFIG ======
PERPLEXITY_MODEL = os.getenv("PERPLEXITY_MODEL", "sonar")
TWEET_MAX = int(os.getenv("TWEET_MAX", "250"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "60"))
LOG_FILE = os.getenv("LOG_FILE", "mercadosexpertos.log")

load_dotenv()

def log(msg: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f: f.write(line + "\n")

def need(name: str) -> str:
    val = os.getenv(name)
    if not val: raise RuntimeError(f"Falta {name} en .env")
    return val

def clean_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\[\d+\]", "", text).strip()
    text = re.sub(r"\(\d+ chars?\)", "", text)
    text = re.sub(r"\b\d+ chars?\b", "", text)
    text = re.sub(r"Final:?\s*\d+ chars?", "", text)
    text = text.replace("**", "").replace("*", "")
    text = re.sub(r"\s{2,}", " ", text).strip()
    if len(text) <= TWEET_MAX: return text
    cut = text[:TWEET_MAX - 1].rsplit(" ", 1)[0]
    return (cut + "…").strip()

def generate_tweet_perplexity(topic: str | None = None) -> str:
    api_key = need("PPLX_API")

    now = datetime.datetime.now()
    hoy_exacto = now.strftime("%d de %B %Y")

    fuentes = """
CEO/Expertos/Pensadores Mercados/Política Monetaria (citas DIRECTAS):
GLOBAL:
1) Jerome Powell @federalreserve (Fed Chair)
2) Christine Lagarde @ecb (BCE)
3) Jamie Dimon @JamieDimon (JPMorgan CEO)
4) Larry Fink @BlackRock (CEO)
5) Ray Dalio @RayDalio (Bridgewater)
6) Stanley Druckenmiller @StanleyDrucken (hedge fund)
7) Mohamed El-Erian @elerianm (Allianz)

COLOMBIA:
8) Leonardo Villar @BanRep (BanRep Chair)
9) José Antonio Ocampo (ex-MinHacienda)
10) Salomón Kalmanovitz (analista BanRep)
11) Andrés Pardo (Credicorp)
12) Diego Guevara @DiegoGuevaraE (Davivienda)

MEDIOS:
bloomberg.com/authors | reuters.com/authors | banrep.gov.co/autores
""".strip()

    if not topic:
        topic = "Opinión reciente CEO/banquero/experto mercados o política monetaria"

    url = "https://api.perplexity.ai/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    prompt = f"""
Twitter experto MERCADOS FINANCIEROS (citas autorizadas).

FECHA: {hoy_exacto}.

1 tweet ESPAÑOL <{TWEET_MAX} chars sobre 1 opinión/comentario reciente de:
{fuentes}

TEMA: {topic}

ESTRUCTURA:
1) Emoji + Nombre Experto: "cita textual"
2) Contexto 1 oración (mercados/tasas/inflación)
3) Implicación estrategia inversión
4) CTA: ¿Estás de acuerdo? ¡RT/comenta!
5) #Mercados + 1 hashtag específico

REGLAS Rígidas:
- SOLO cita DIRECTA experto (ej. "Powell: tasas más altas por más tiempo")
- NO inventes datos numéricos/precios (ej. NO "$3691" sin cita textual)
- Opinión cualitativa si sin números (ej. "Dimon: bancos preparados recesión")
- Menciona @usuario o fuente
- Emoji relevante (📈🧠💼🚨)
- 1 párrafo, NO listas

Ejemplo (196 chars):
📈 Jerome Powell: "tasas más altas por más tiempo". Fed prioriza inflación control. ¿Cambias bonos acciones? ¡RT! #Mercados #Fed @federalreserve

SOLO tweet final limpio.
""".strip()

    payload = {
        "model": PERPLEXITY_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200,
        "temperature": 0.75
    }

    for attempt in range(3):
        r = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        if r.status_code == 429 and attempt < 2:
            time.sleep(2 ** attempt); continue
        if r.status_code != 200:
            raise RuntimeError(f"Perplexity {r.status_code}")
        raw = r.json()["choices"][0]["message"]["content"]
        tweet = clean_text(raw)
        if tweet and len(tweet) >= 120:
            log(f"EXPERTO ({len(tweet)}): {tweet}")
            return tweet
    raise RuntimeError("Sin tweet experto")

def x_client() -> tweepy.Client:
    return tweepy.Client(
        consumer_key=need("TWITTER_API_KEY"),
        consumer_secret=need("TWITTER_API_KEY_SECRET"),
        access_token=need("TWITTER_ACCESS_TOKEN"),
        access_token_secret=need("TWITTER_ACCESS_TOKEN_SECRET")
    )

def main():
    log("=== MercadosExpertos (CEO/Banqueros) ===")
    topic = os.getenv("TOPIC", "").strip() or None
    log(f"Tema experto: {topic or 'default'}")
    
    tweet = generate_tweet_perplexity(topic)
    client = x_client()
    me = client.get_me(user_auth=True)
    if not getattr(me, "data", None):
        raise RuntimeError("get_me fail")
    
    log(f"@{me.data.username}")
    resp = client.create_tweet(text=tweet)
    log(f"PUBLISH ID {resp.data['id']} ({len(tweet)} chars)")
    log("=== FIN Expertos Mercados ===")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("=== ERROR ===")
        log(repr(e))
        sys.exit(1)