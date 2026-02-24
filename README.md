# 🚀 Cardano Bot Automático - Twitter

**Bot automático que publica tweets sobre Cardano cada 3 horas usando GitHub Actions.**

## ✨ Características

- 🔄 **Publicación automática cada 3 horas** vía GitHub Actions
- 🤖 **Powered by Perplexity AI** - Contenido actualizado en tiempo real
- 🔒 **Seguro** - Secrets encriptados en GitHub
- 📈 **Engagement optimizado** - Emojis, CTAs, hashtags estratégicos
- 📊 **Logs automáticos** - Monitoreo de publicaciones

## 🛑 Requisitos

### 1. API Perplexity
- Crea cuenta en [perplexity.ai](https://www.perplexity.ai)
- Ve a Settings → API → Generate new key
- Copia tu API key: `pplx-xxxxxxxxxxxxxxxx`

### 2. Twitter Developer Account
- Aplica en [developer.twitter.com](https://developer.twitter.com)
- Crea app con permisos **Read and Write**
- Obtén:
  - `API Key` (Consumer Key)
  - `API Key Secret` (Consumer Secret)
  - `Access Token`
  - `Access Token Secret`

## ⚙️ Configuración (5 minutos)

### Paso 1: Configura Secrets en GitHub

1. Ve a tu repositorio → **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"** para cada uno:

| Nombre | Valor |
|--------|-------|
| `PPLX_API` | Tu API key de Perplexity |
| `TWITTER_API_KEY` | Consumer Key de Twitter |
| `TWITTER_API_KEY_SECRET` | Consumer Secret de Twitter |
| `TWITTER_ACCESS_TOKEN` | Access Token de Twitter |
| `TWITTER_ACCESS_TOKEN_SECRET` | Access Token Secret de Twitter |
| `PERPLEXITY_MODEL` | `sonar` (opcional) |
| `TOPIC` | `Cardano Voltaire` (opcional) |

### Paso 2: Activa GitHub Actions

1. Ve a **Actions** tab
2. Si aparece mensaje de habilitación, click **"I understand my workflows, go ahead and enable them"**
3. Workflow **"CardanoNEW AutoTweet"** ya está configurado

### Paso 3: Prueba Manual (Recomendado)

1. Actions → **CardanoNEW AutoTweet** → **Run workflow** → **Run workflow**
2. Espera ~30 segundos
3. Revisa tu cuenta de Twitter 🎉

## 📅 Programación Automática

**El bot publicará cada 3 horas:**
- 00:00, 03:00, 06:00, 09:00, 12:00, 15:00, 18:00, 21:00 UTC
- **8 tweets diarios automáticos**

**Próxima publicación:** Revisa en Actions → Scheduled workflows

## 🛠️ Personalización

### Cambiar Tema de Tweets
Agrega/edita el secret `TOPIC` con tu tema preferido:
```
Voltaire governance Cardano
Cardano DeFi adoption
ADA price prediction
```

### Cambiar Frecuencia
Edita `.github/workflows/cardano-auto.yml`:
```yaml
cron: '0 */6 * * *'  # Cada 6 horas
cron: '0 */12 * * *' # Cada 12 horas
cron: '0 9 * * *'    # Diario a las 9:00 UTC
```

### Cambiar Modelo Perplexity
Agrega secret `PERPLEXITY_MODEL`:
- `sonar` (default, rápido)
- `sonar-pro` (más profundo, requiere plan Pro)

## 📊 Monitoreo

### Ver Logs
1. Actions → Workflow run más reciente
2. Click en job "tweet"
3. Expande "Run Cardano Bot"

### Logs incluyen:
- ✅ Timestamp de ejecución
- 📝 Contenido del tweet generado
- 🔗 ID del tweet publicado
- ⚠️ Errores (si los hay)

## ☠️ Solución de Problemas

### Error: "Falta PPLX_API en .env"
- Verifica que configuraste el secret `PPLX_API` correctamente
- Asegúrate que no tiene espacios extra

### Error: "get_me() sin data"
- Verifica credenciales de Twitter
- Confirma que tu app tiene permisos **Read and Write**
- Regenera Access Tokens si es necesario

### Error: "Rate limit (429)"
- Perplexity: Límite de API alcanzado (espera 1 hora)
- Twitter: Demasiados tweets (reduce frecuencia)

### Bot no publica automáticamente
1. Verifica que GitHub Actions esté habilitado
2. Revisa que el workflow existe en `.github/workflows/`
3. Chequea que todos los secrets estén configurados

## 💻 Uso Local (Testing)

```bash
# Clona el repo
git clone https://github.com/ariaslopez/cardano-mercados-bot.git
cd cardano-mercados-bot

# Instala dependencias
pip install -r requirements.txt

# Crea archivo .env
cp .env.example .env
# Edita .env con tus API keys

# Ejecuta bot
python bot.py
```

## 📚 Estructura del Proyecto

```
cardano-mercados-bot/
├── bot.py                    # Script principal
├── requirements.txt          # Dependencias Python
├── .env.example              # Plantilla variables
├── .github/
│   └── workflows/
│       └── cardano-auto.yml  # GitHub Actions
└── README.md                 # Esta guía
```

## 🔒 Seguridad

- **NUNCA** commitees tu archivo `.env` con keys reales
- Usa GitHub Secrets para producción
- Revoca tokens si los expones accidentalmente
- `.env` está en `.gitignore` por seguridad

## 🚀 Próximas Mejoras

- [ ] Anti-repetición de contenido
- [ ] Múltiples cuentas Twitter
- [ ] Dashboard de métricas
- [ ] Respuestas automáticas a menciones
- [ ] Integración con imágenes AI

## 💬 Soporte

¿Problemas? Abre un [Issue](https://github.com/ariaslopez/cardano-mercados-bot/issues)

## 📦 Stack Tecnológico

- **Python 3.11**
- **Tweepy 4.14** - Twitter API client
- **Perplexity AI** - Content generation
- **GitHub Actions** - CI/CD automation
- **dotenv** - Environment variables

---

**⭐ Dale Star si te sirvió | 👁️ Watch para actualizaciones**

Creado con ❤️ por [@ariaslopez](https://github.com/ariaslopez)