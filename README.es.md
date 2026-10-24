<div align="center">

# 📲 social-publisher-mcp

**Un community manager con IA para video corto, empaquetado como servidor MCP.**<br>
Deja tus videos terminados en una carpeta: los ve, escribe el texto para cada red,<br>
programa todo para las **05:00**, agrega subtítulos cuando hacen falta y te dice qué funcionó.

[![tests](https://github.com/robgallardof/social-publisher-mcp/actions/workflows/tests.yml/badge.svg)](https://github.com/robgallardof/social-publisher-mcp/actions/workflows/tests.yml)
![python](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)
![MCP](https://img.shields.io/badge/MCP-stdio-8A2BE2)
![plataformas](https://img.shields.io/badge/TikTok%20·%20Reels%20·%20Facebook%20·%20Shorts-ff3b5c)
![SO](https://img.shields.io/badge/Windows%20·%20macOS%20·%20Linux-555)

[English](README.md) · **Español**

</div>

---

## ✨ Qué hace

| | |
|---|---|
| 📂 **Cola por fecha** | `content/queue/2026-10-27/*.mp4` sale el 27 de octubre. Tres videos en la carpeta = tres publicaciones a las 05:00. Las carpetas de semana (`2026-W44/`) se reparten solas entre los días. |
| 👀 **Ve cada video** | Hoja de 8 fotogramas + transcripción (faster-whisper) → sabe qué pasa, si hay voz y si ya trae subtítulos. |
| ✍️ **Texto por red** | Gancho, cuerpo, llamada a la acción, hashtags y palabras clave para TikTok, Instagram Reels, Facebook Reels y YouTube Shorts, validados contra los límites reales de cada una. |
| 🔁 **Pie de redes** | Cada descripción termina con `📲 Síguenos también:` y tus usuarios en las *otras* redes, automático. |
| 💬 **Subtítulos** | Decide: ninguno / automáticos de la plataforma / `.srt` / quemados en el video, y los renderiza con estilo para vertical. |
| 🚀 **Publica como sea** | APIs oficiales (Meta, YouTube, TikTok) → Postiz → perfil de navegador con Playwright → el propio agente (Claude in Chrome, Playwright MCP, computer use). |
| ⏰ **05:00 todos los días** | Tarea programada de Windows (cron en macOS/Linux): publicador idempotente con reintentos; despierta la PC y se pone al día si estuvo apagada. |
| 📈 **Aprende** | Saca métricas, mejores días, videos top y bottom, y un reporte semanal con máximo tres acciones. |

## 🧩 Funciona con cualquier agente

`social-forge` es un **servidor MCP stdio** estándar. Además de sus herramientas expone cada **skill como recurso MCP** (`skill://<nombre>`) y cada **rol como prompt MCP**, así cualquier cliente MCP recibe el manual completo, no solo los que leen `.agents/`.

| Cliente | Cómo |
|---|---|
| Claude Code | `.mcp.json` en la carpeta, o para tu usuario con el instalador (+ skills/agentes enlazados en `~/.claude`) |
| Codex | `.codex/config.toml` / `~/.codex/config.toml` |
| Antigravity | `.agents/mcp_config.json` / `~/.gemini/antigravity/mcp_config.json` |
| Cursor · VS Code · Gemini CLI · Windsurf · Claude Desktop | configs generadas, o el instalador |

```powershell
python scripts/install-mcp.py --list         # qué clientes tienes
python scripts/install-mcp.py --with-skills  # lo registra para tu usuario en todos (respaldo .bak de cada archivo)
python scripts/install-mcp.py --remove       # deshacer
```

## 🚀 Inicio rápido

```powershell
git clone https://github.com/robgallardof/social-publisher-mcp.git
cd social-publisher-mcp
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap.ps1        # entorno, pruebas, configs, MCP
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/install-schedule.ps1 # tarea diaria de las 05:00
```

macOS / Linux: `sh scripts/bootstrap.sh` y la línea de cron que imprime al final. Requiere [uv](https://docs.astral.sh/uv/).

Luego háblale a tu agente:

> *"Procesa el inbox"* · *"Prepara lo de mañana"* · *"Reparte la semana 44, dos por día"* · *"Ponle subtítulos al storytime"* · *"¿Qué funcionó esta semana?"* · *"Investiga tendencias de ardillas en México"*

## 🔄 El camino de un video

```mermaid
flowchart LR
    A[content/inbox] -->|analyze_video| B(fotogramas + transcripción)
    B --> C{video-analyst}
    C -->|carpeta del día| D[content/queue/AAAA-MM-DD]
    D -->|write_post| E[.post.yaml<br/>texto · pie · subtítulos]
    E -->|05:00 run-due| F{backend}
    F --> G[API Meta / YouTube / TikTok]
    F --> H[Postiz]
    F --> I[Perfil de navegador]
    F --> J[Agente]
    G & H & I & J --> K[content/published + recibos]
    K -->|pull_metrics| L[analítica · reporte semanal]
```

## 🛠️ Herramientas MCP (15)

| Herramienta | |
|---|---|
| `queue_status` | Qué sale cada día, atrasados, sin texto, videos nuevos en el inbox |
| `plan_week` | Reparte una carpeta de semana en sus días restantes |
| `analyze_video` | Fotogramas, transcripción, voz sí/no, `.srt` |
| `make_subtitles` | `.srt` y, si quieres, una copia con subtítulos quemados para revisar |
| `check_video` | Duración/resolución contra cada plataforma |
| `write_post` · `preview_post` | Guardar y previsualizar el texto por red (el pie se agrega solo) |
| `brand_info` | Usuarios por red y cuáles faltan |
| `publish_due` · `publish_now` | Publicar o programar (siempre `dry_run` primero) |
| `mark_published` | Cerrar una subida hecha por el agente o a mano |
| `backends_status` | ¿Cada red está lista? |
| `platform_rules` | Límites por plataforma |
| `pull_metrics` · `insights_report` | Métricas y resumen |

## 👥 Roles y skills

**Roles** (`.agents/agents/`): `community-manager` (líder) · `video-analyst` · `content-strategist` · `copywriter` · `publisher` · `audience-analyst` · `trend-researcher`

**Skills** (`.agents/skills/`): `content-queue` · `video-analysis` · `subtitles` · `platform-copywriting` · `social-publishing` (+ guía por red) · `agent-browser-upload` · `content-strategy` · `audience-analytics` · `trend-research` · `community-engagement`

El rol líder **pregunta antes de escribir**: tus usuarios en cada red, @menciones, links, hashtags fijos y preferencia de subtítulos.

## 🔌 Formas de publicar

| Backend | Redes | ¿Público de inmediato? | ¿Programa solo? |
|---|---|---|---|
| `meta_api` | Instagram, Facebook | ✅ | Facebook ✅ |
| `youtube_api` | YouTube | tras la auditoría de Google | ✅ `publishAt` |
| `tiktok_api` | TikTok | tras la auditoría de TikTok | — |
| `postiz` | todas | ✅ | ✅ (la PC puede estar apagada) |
| `browser` | todas | ✅ | — |
| `handoff` | todas | lo hace el agente | — |

Credenciales: [`docs/accounts.md`](docs/accounts.md). Viven en `secrets/` (ignorado por git).

## 📁 Estructura

```
content/inbox/        suelta aquí los videos nuevos
content/queue/        AAAA-MM-DD/ (o AAAA-Www/) + <video>.post.yaml
content/published/    archivo con recibos          content/library/  tomas crudas, versiones renderizadas
brand/                voz, audiencia, hashtags     config/           social.yaml, flujos de navegador, servidores MCP
mcp/social-forge/     el MCP + CLI (domain → services → app → server/cli)
.agents/              skills y roles portables     scripts/          bootstrap, install-mcp, schedule, sync
```

## 🧪 Desarrollo

```bash
cd mcp/social-forge && uv run pytest     # 46 pruebas, sin red (HTTP simulado, ffmpeg real)
python scripts/sync.py                   # después de editar .agents/ o config/
git config core.hooksPath .githooks      # quita los coautores de IA de los mensajes de commit
```

Reglas de arquitectura y cómo agregar un backend: [`AGENTS.md`](AGENTS.md).

## ⚠️ Bueno saber

- Por **API**, TikTok y YouTube publican en privado hasta que auditen tu app: mientras, usa `browser` o `postiz`.
- La API de Instagram no tiene hora de publicación: se publica a las 05:00 en el momento, así que la PC debe estar encendida (o usa Postiz).
- Nunca publica dos veces: cada subida deja un recibo y los reintentos solo tocan lo que falló.
- Configurado ahora para **Chomi la ardilla** 🐿️; una marca nueva solo necesita `brand/` y `config/social.yaml`.

<div align="center"><sub>Hecho para creadores que prefieren grabar que pelearse con programadores de publicaciones.</sub></div>
