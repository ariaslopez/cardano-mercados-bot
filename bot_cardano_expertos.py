import os, re, sys, time, datetime, requests, tweepy
from dotenv import load_dotenv

# ====== CONFIG ======
PERPLEXITY_MODEL = os.getenv("PERPLEXITY_MODEL", "sonar")
TWEET_MAX = int(os.getenv("TWEET_MAX", "250"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "60"))
LOG_FILE = os.getenv("LOG_FILE", "cardanonew.log")

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
CEO/Expertos/Pensadores Cardano (prioridad citas DIRECTAS):
1) Charles Hoskinson @IOHK_Charles (fundador Cardano)
2) Input Output Global iohk.io/blog
3) Cardano Foundation cardanofoundation.org/news
4) Emurgo emurgo.io/press
5) developers.cardano.org/blog (devs oficiales)
6) forum.cardano.org/c/developers (discusiones expertas)
7) journal.cardano.org (análisis profundos)
8) sundae.fi/blog (DeFi Cardano expertos)
9) mellifera.network/blog (stake pool operators)
10) Entropic (validator experto)
RSS: iohk.io/feed.xml, cardanofoundation.org/feed
""".strip()

    if not topic:
        topic = "Opinión reciente CEO/experto/pensador Cardano"

    url = "https://api.perplexity.ai/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    prompt = f"""
Twitter experto CRYPTO Cardano (engagement + citas autorizadas).

FECHA: {hoy_exacto}.

OBJETIVO:
- 1 tweet ESPAÑOL <{TWEET_MAX} chars sobre 1 opinión/comentario reciente de CEO/EXPERTO/PENSADOR:
{fuentes}

TEMA: {topic}

ESTRUCTURA OBLIGATORIA:
1) Emoji + Nombre Experto: "cita directa"
2) 1 idea clave de su visión/estrategia Cardano
3) Implicación ecosistema/mainnet
4) CTA: ¿Qué opinas? ¡RT/DYOR!
5) #Cardano #ADA

REGLAS Estrictas:
- SOLO si experto menciona dato numérico (ej. Charles: "staking 70%"), inclúyelo CITANDO
- NO inventes precios/porcentajes/volúmenes (ej. NO "$0.26" sin cita directa)
- Opinión cualitativa si no datos (ej. "Charles: Cardano listo mainnet Voltaire")
- Fuente en cita: "@usuario" o "en [medio]"
- NO listas, NO meses futuros, 1 párrafo
- Emoji relevante (🔥🧠💡🚀)

Ejemplo (178 chars):
🔥 Charles Hoskinson: "Voltaire governance transforma Cardano en DAO soberano". Expertos celebran mainnet upgrade. ¿Adoptarás votación? ¡RT/DYOR! #Cardano #ADA @IOHK_Charles

SOLO tweet final.
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
        if tweet and len(tweet) >= 100:
            log(f"EXPERTO ({len(tweet)}): {tweet}")
            return tweet
    raise RuntimeError("Sin tweet experto válido")

def x_client() -> tweepy.Client:
    return tweepy.Client(
        consumer_key=need("TWITTER_API_KEY"),
        consumer_secret=need("TWITTER_API_KEY_SECRET"),
        access_token=need("TWITTER_ACCESS_TOKEN"),
        access_token_secret=need("TWITTER_ACCESS_TOKEN_SECRET")
    )

def main():
    log("=== CardanoNEW Expertos (CEO/Pensadores) ===")
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
    log("=== FIN Expertos ===")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("=== ERROR ===")
        log(repr(e))
        sys.exit(1)