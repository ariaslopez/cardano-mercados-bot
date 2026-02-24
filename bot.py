import os
import re
import sys
import time
import datetime
import requests
import tweepy
from dotenv import load_dotenv

# ====== CONFIG ======
PERPLEXITY_MODEL = os.getenv("PERPLEXITY_MODEL", "sonar")
TWEET_MAX = int(os.getenv("TWEET_MAX", "260"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "60"))
LOG_FILE = os.getenv("LOG_FILE", "bot.log")

load_dotenv()


def log(msg: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def need(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise RuntimeError(f"Falta {name} en .env")
    return val


def clean_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\[\d+\]", "", text).strip()
    text = re.sub(r"\(\d+ chars?\)", "", text)
    text = re.sub(r"\b\d+ chars?\b", "", text)
    text = re.sub(r"Final:?\s*\d+ chars?", "", text)
    text = text.replace("**", "").replace("*", "")
    text = re.sub(r"\s{2,}", " ", text).strip()

    if len(text) <= TWEET_MAX:
        return text

    cut = text[: TWEET_MAX - 1].rsplit(" ", 1)[0]
    return (cut + "…").strip()


def generate_tweet_perplexity(topic: str | None = None) -> str:
    api_key = need("PPLX_API")

    now = datetime.datetime.now()
    hoy_exacto = now.strftime("%d de %B de %Y %H:%M")
    hoy_mes = now.strftime("%B %Y").capitalize()
    next_month = (now + datetime.timedelta(days=30)).strftime("%B").capitalize()

    fuentes = """
Fuentes WEB RECIENTES (extrae HOY / real-time):
1) cardano.org/news (oficial)
2) CoinMarketCap.com Cardano
3) CoinGecko.com/coins/cardano
4) cryptopanic.com/news/cardano (agregador)
5) forum.cardano.org
6) crypto.com/coins/cardano
7) u.today/cardano
8) cardanofeed.com
9) newsbtc.com/news/cardano
10) fool.com (Cardano)
RSS: developers.cardano.org/blog, builtoncardano.com/blog
""".strip()

    if not topic:
        topic = "Actualización/noticia reciente sobre Cardano (ecosistema, adopción, mainnet o mercado)"

    url = "https://api.perplexity.ai/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    prompt = f"""
Eres experto en X/Twitter crypto (alto engagement, directo, sin relleno).
FECHA/TIEMPO ACTUAL: {hoy_exacto} (mes: {hoy_mes}). Next month auto-adapt (ej. {next_month} si aplica).

OBJETIVO:
- Genera EXACTO 1 tweet en ESPAÑOL (<{TWEET_MAX} chars) sobre CARDANO basado en 1 noticia/actualización MÁS RECIENTE obtenida de estas fuentes (no inventes).

{fuentes}

TEMA/GUÍA:
- {topic}

REGLAS OBLIGATORIAS:
- Hook con emoji al inicio.
- Incluye 1 dato "HOY" si está disponible en las fuentes (precio ADA o variación %, volumen, métrica on-chain, mainnet/dev, TVL, etc.). Si NO hay dato fiable, no lo inventes; usa un dato cualitativo verificable del titular.
- Resume en 1 sola idea (una noticia), sin mezclar 2 temas.
- Cierra con CTA: "DYOR" o "Más en mi bio".
- Incluye #Cardano #ADA.
- Evita frases repetidas y evita mencionar meses ("en marzo", etc.).
- No uses citas tipo [1] y no pongas listas; solo 1 párrafo.

Devuelve SOLO el tweet final.
""".strip()

    payload = {
        "model": PERPLEXITY_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 220,
        "temperature": 0.7,
    }

    for attempt in range(3):
        r = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)

        if r.status_code == 429 and attempt < 2:
            time.sleep(2 ** attempt)
            continue

        if r.status_code != 200:
            raise RuntimeError(f"Perplexity {r.status_code}: {r.text}")

        data = r.json()
        raw = data["choices"][0]["message"]["content"]
        tweet = clean_text(raw)

        if not tweet:
            raise RuntimeError("Perplexity devolvió texto vacío tras limpieza.")

        log(f"Tweet ({len(tweet)} chars): {tweet}")
        return tweet

    raise RuntimeError("Rate limit persistente (429) en Perplexity.")


def x_client() -> tweepy.Client:
    return tweepy.Client(
        consumer_key=need("TWITTER_API_KEY"),
        consumer_secret=need("TWITTER_API_KEY_SECRET"),
        access_token=need("TWITTER_ACCESS_TOKEN"),
        access_token_secret=need("TWITTER_ACCESS_TOKEN_SECRET"),
    )


def main():
    log("=== INICIO CardanoNEW (Unificado) ===")

    topic = os.getenv("TOPIC", "").strip() or None

    log(f"Generando tweet con Perplexity (model={PERPLEXITY_MODEL})...")
    tweet = generate_tweet_perplexity(topic)

    client = x_client()

    me = client.get_me(user_auth=True)
    if not getattr(me, "data", None):
        raise RuntimeError(f"get_me() sin data. Respuesta: {me}")
    log(f"Autenticado en X como: @{me.data.username}")

    resp = client.create_tweet(text=tweet, user_auth=True)
    log(f"Publicado OK: ID {resp.data['id']} ({len(tweet)} chars)")

    log("=== FIN OK ===")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("=== FIN ERROR ===")
        log(repr(e))
        sys.exit(1)