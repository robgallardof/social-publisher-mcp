<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/readme/banner-es-dark.svg">
  <img src="assets/readme/banner-es-light.svg" alt="social-publisher-mcp — Un community manager con IA para video corto" width="100%">
</picture>

<br/>

[![tests](https://github.com/robgallardof/social-publisher-mcp/actions/workflows/tests.yml/badge.svg)](https://github.com/robgallardof/social-publisher-mcp/actions/workflows/tests.yml)
![python](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)
![MCP](https://img.shields.io/badge/MCP-stdio-8A2BE2)
![plataformas](https://img.shields.io/badge/TikTok%20·%20Reels%20·%20Facebook%20·%20Shorts-ff3b5c)
![SO](https://img.shields.io/badge/Windows%20·%20macOS%20·%20Linux-555)

[English](README.md) · **Español**

</div>

<p align="center">
<a href="#-qué-hace"><img src="https://img.shields.io/badge/Qu%C3%A9%20hace-6D28D9?style=for-the-badge" alt="Qué hace" /></a>
<a href="#-funciona-con-cualquier-agente"><img src="https://img.shields.io/badge/Funciona%20con%20cualquier%20agente-5B21B6?style=for-the-badge" alt="Funciona con cualquier agente" /></a>
<a href="#-inicio-rápido"><img src="https://img.shields.io/badge/Inicio%20r%C3%A1pido-4F46E5?style=for-the-badge" alt="Inicio rápido" /></a>
<a href="#-el-camino-de-un-video"><img src="https://img.shields.io/badge/El%20camino%20de%20un%20video-4338CA?style=for-the-badge" alt="El camino de un video" /></a>
<a href="#️-herramientas-mcp-15"><img src="https://img.shields.io/badge/Herramientas%20MCP%20%2815%29-2563EB?style=for-the-badge" alt="Herramientas MCP (15)" /></a>
<a href="#-roles-y-skills"><img src="https://img.shields.io/badge/Roles%20y%20skills-0284C7?style=for-the-badge" alt="Roles y skills" /></a>
<a href="#-formas-de-publicar"><img src="https://img.shields.io/badge/Formas%20de%20publicar-0EA5E9?style=for-the-badge" alt="Formas de publicar" /></a>
<a href="#-estructura"><img src="https://img.shields.io/badge/Estructura-0891B2?style=for-the-badge" alt="Estructura" /></a>
<a href="#-desarrollo"><img src="https://img.shields.io/badge/Desarrollo-0E7490?style=for-the-badge" alt="Desarrollo" /></a>
<a href="#️-bueno-saber"><img src="https://img.shields.io/badge/Bueno%20saber-155E75?style=for-the-badge" alt="Bueno saber" /></a>
</p>

<p align="center"><img src="assets/readme/divider.svg" alt="" width="80%" /></p>

<a id="-qué-hace"></a>
<p align="center"><img src="assets/readme/sections/es-01.svg" alt="01 · Qué hace" width="100%" /></p>

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

<a id="-funciona-con-cualquier-agente"></a>
<p align="center"><img src="assets/readme/sections/es-02.svg" alt="02 · Funciona con cualquier agente" width="100%" /></p>

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
python scripts/install-mcp.py --workspace ../davinci-agents  # cualquier otro workspace con config/mcp.servers.json
```

<a id="-inicio-rápido"></a>
<p align="center"><img src="assets/readme/sections/es-03.svg" alt="03 · Inicio rápido" width="100%" /></p>

```powershell
git clone https://github.com/robgallardof/social-publisher-mcp.git
cd social-publisher-mcp
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap.ps1        # entorno, pruebas, configs, MCP
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/install-schedule.ps1 # tarea diaria de las 05:00
```

macOS / Linux: `sh scripts/bootstrap.sh` y la línea de cron que imprime al final. Requiere [uv](https://docs.astral.sh/uv/).

Luego háblale a tu agente:

> *"Procesa el inbox"* · *"Prepara lo de mañana"* · *"Reparte la semana 44, dos por día"* · *"Ponle subtítulos al storytime"* · *"¿Qué funcionó esta semana?"* · *"Investiga tendencias de ardillas en México"*

<a id="-el-camino-de-un-video"></a>
<p align="center"><img src="assets/readme/sections/es-04.svg" alt="04 · El camino de un video" width="100%" /></p>

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

<a id="️-herramientas-mcp-15"></a>
<p align="center"><img src="assets/readme/sections/es-05.svg" alt="05 · Herramientas MCP (15)" width="100%" /></p>

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

<a id="-roles-y-skills"></a>
<p align="center"><img src="assets/readme/sections/es-06.svg" alt="06 · Roles y skills" width="100%" /></p>

**Roles** (`.agents/agents/`): `community-manager` (líder) · `video-analyst` · `content-strategist` · `copywriter` · `publisher` · `audience-analyst` · `trend-researcher`

**Skills** (`.agents/skills/`): `content-queue` · `video-analysis` · `subtitles` · `platform-copywriting` · `social-publishing` (+ guía por red) · `agent-browser-upload` · `content-strategy` · `audience-analytics` · `trend-research` · `community-engagement`

El rol líder **pregunta antes de escribir**: tus usuarios en cada red, @menciones, links, hashtags fijos y preferencia de subtítulos.

<a id="-formas-de-publicar"></a>
<p align="center"><img src="assets/readme/sections/es-07.svg" alt="07 · Formas de publicar" width="100%" /></p>

| Backend | Redes | ¿Público de inmediato? | ¿Programa solo? |
|---|---|---|---|
| `meta_api` | Instagram, Facebook | ✅ | Facebook ✅ |
| `youtube_api` | YouTube | tras la auditoría de Google | ✅ `publishAt` |
| `tiktok_api` | TikTok | tras la auditoría de TikTok | — |
| `postiz` | todas | ✅ | ✅ (la PC puede estar apagada) |
| `browser` | todas | ✅ | — |
| `handoff` | todas | lo hace el agente | — |

Credenciales: [`docs/accounts.md`](docs/accounts.md). Viven en `secrets/` (ignorado por git).

<a id="-estructura"></a>
<p align="center"><img src="assets/readme/sections/es-08.svg" alt="08 · Estructura" width="100%" /></p>

```
content/inbox/        suelta aquí los videos nuevos
content/queue/        AAAA-MM-DD/ (o AAAA-Www/) + <video>.post.yaml
content/published/    archivo con recibos          content/library/  tomas crudas, versiones renderizadas
brand/                voz, audiencia, hashtags     config/           social.yaml, flujos de navegador, servidores MCP
mcp/social-forge/     el MCP + CLI (domain → services → app → server/cli)
.agents/              skills y roles portables     scripts/          bootstrap, install-mcp, schedule, sync
```

<a id="-desarrollo"></a>
<p align="center"><img src="assets/readme/sections/es-09.svg" alt="09 · Desarrollo" width="100%" /></p>

```bash
cd mcp/social-forge && uv run pytest     # 46 pruebas, sin red (HTTP simulado, ffmpeg real)
python scripts/sync.py                   # después de editar .agents/ o config/
git config core.hooksPath .githooks      # quita los coautores de IA de los mensajes de commit
```

Reglas de arquitectura y cómo agregar un backend: [`AGENTS.md`](AGENTS.md).

<a id="️-bueno-saber"></a>
<p align="center"><img src="assets/readme/sections/es-10.svg" alt="10 · Bueno saber" width="100%" /></p>

- Por **API**, TikTok y YouTube publican en privado hasta que auditen tu app: mientras, usa `browser` o `postiz`.
- La API de Instagram no tiene hora de publicación: se publica a las 05:00 en el momento, así que la PC debe estar encendida (o usa Postiz).
- Nunca publica dos veces: cada subida deja un recibo y los reintentos solo tocan lo que falló.
- Configurado ahora para **Chomi la ardilla** 🐿️; una marca nueva solo necesita `brand/` y `config/social.yaml`.

<div align="center"><sub>Hecho para creadores que prefieren grabar que pelearse con programadores de publicaciones.</sub></div>

<br/>

<img src="assets/readme/footer-es.svg" alt="social-publisher-mcp" width="100%" />
