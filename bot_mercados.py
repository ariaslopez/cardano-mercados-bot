import os, re, sys, time, datetime, requests, tweepy
from dotenv import load_dotenv

# ====== CONFIG ======
PERPLEXITY_MODEL = os.getenv("PERPLEXITY_MODEL", "sonar")
TWEET_MAX = int(os.getenv("TWEET_MAX", "260"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "60"))
LOG_FILE = os.getenv("LOG_FILE", "mercados.log")

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
    hoy_exacto = now.strftime("%d de %B de %Y %H:%M")
    hoy_mes = now.strftime("%B %Y").capitalize()

    fuentes = """
Fuentes MERCADOS/POLÍTICAS MONETARIAS (real-time PRIORIDAD):
1) bloomberg.com/markets  2) reuters.com/markets  3) cnbc.com/world-markets
4) banrep.gov.co/publicaciones  5) larepublica.co/economia  6) portafolio.co/economia
7) investing.com/indices/major-indices  8) fxstreet.com/es/mercados
9) federalreserve.gov/releases  10) ecb.europa.eu/stats
RSS: banrep.gov.co/es/rss, investing.com/rss_news
""".strip()

    if not topic:
        topic = "Actualización impactante mercados globales o política monetaria (tasas, inflación, TRM, COLCAP, S&P500, Fed, BanRep)"

    url = "https://api.perplexity.ai/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    prompt = f"""
Twitter experto MERCADOS FINANCIEROS (engagement + datos duros).

FECHA: {hoy_exacto} (mes: {hoy_mes}).

OBJETIVO:
- 1 tweet ESPAÑOL (<{TWEET_MAX} chars) sobre 1 noticia MÁS RECIENTE de estas fuentes:
{fuentes}

TEMA:
- {topic}

ESTRUCTURA EXACTA:
🚨 ¡IMPACTO! [Dato clave HOY: precio $ o % cambio de fuente]
[1 dato numérico verificable] impacto [bolsa/crypto/Colombia]
¿Compras/Vendes/HODL? ¡RT/DYOR! #Mercados #Dolar

REGLAS:
- Emoji 🚨📈💹 inicio
- Dato "HOY" prioritario (ej. TRM $, S&P500 pts, BTC $)
- NO inventes, usa fuentes exactas
- SIN [1] citas ni chars count
- SOLO tweet limpio

Ejemplo (187 chars):
🚨 ¡IMPACTO! S&P500 -0.7% 6789pts HOY tech Nvidia pesa. Fed vigila inflación. ¿Compras dip USA? ¡RT! #Mercados #SP500
""".strip()

    payload = {
        "model": PERPLEXITY_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 220,
        "temperature": 0.7
    }

    for attempt in range(3):
        r = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        if r.status_code == 429 and attempt < 2:
            time.sleep(2 ** attempt)
            continue
        if r.status_code != 200:
            raise RuntimeError(f"Perplexity {r.status_code}")
        data = r.json()
        raw = data["choices"][0]["message"]["content"]
        tweet = clean_text(raw)
        if tweet:
            log(f"Tweet ({len(tweet)}): {tweet}")
            return tweet
    raise RuntimeError("Perplexity vacío")

def x_client() -> tweepy.Client:
    return tweepy.Client(
        consumer_key=need("TWITTER_API_KEY"),
        consumer_secret=need("TWITTER_API_KEY_SECRET"),
        access_token=need("TWITTER_ACCESS_TOKEN"),
        access_token_secret=need("TWITTER_ACCESS_TOKEN_SECRET")
    )

def main():
    log("=== INICIO BotMercado (Mercados/Monetaria) ===")
    topic = os.getenv("TOPIC", "").strip() or None
    log(f"Tema: {topic or 'default'}")
    
    tweet = generate_tweet_perplexity(topic)
    client = x_client()
    me = client.get_me(user_auth=True)
    if not getattr(me, "data", None):
        raise RuntimeError("get_me sin data")
    
    log(f"@{me.data.username}")
    resp = client.create_tweet(text=tweet)
    log(f"PUBLICADO ID {resp.data['id']} ({len(tweet)} chars)")
    log("=== FIN OK ===")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("=== FIN ERROR ===")
        log(repr(e))
        sys.exit(1)