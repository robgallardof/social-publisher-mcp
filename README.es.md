<a id="top"></a>

<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/readme/banner-es-dark.svg">
  <img src="assets/readme/banner-es-light.svg" alt="social-publisher-mcp — Un community manager con IA para video corto" width="100%">
</picture>

<br/>

[![tests](https://github.com/robgallardof/social-publisher-mcp/actions/workflows/tests.yml/badge.svg)](https://github.com/robgallardof/social-publisher-mcp/actions/workflows/tests.yml)
![python](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)
![MCP](https://img.shields.io/badge/MCP-stdio%20%C2%B7%20HTTP-8A2BE2)
![Docker](https://img.shields.io/badge/Docker-optional-2496ED?logo=docker&logoColor=white)
![plataformas](https://img.shields.io/badge/TikTok%20·%20Reels%20·%20Facebook%20·%20Shorts-ff3b5c)
![SO](https://img.shields.io/badge/Windows%20·%20macOS%20·%20Linux-555)

[English](README.md) · **Español**

</div>

<p align="center">
<a href="#-qué-hace"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme-builder/kit/btn-que-hace-outline-sm-dark.svg" /><img src="assets/readme-builder/kit/btn-que-hace-outline-sm-light.svg" alt="Qué hace" height="34" /></picture></a>
<a href="#-funciona-con-cualquier-agente"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme-builder/kit/btn-funciona-con-cualquier-agente-outline-sm-dark.svg" /><img src="assets/readme-builder/kit/btn-funciona-con-cualquier-agente-outline-sm-light.svg" alt="Funciona con cualquier agente" height="34" /></picture></a>
<a href="#-inicio-rápido"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme-builder/kit/btn-inicio-rapido-outline-sm-dark.svg" /><img src="assets/readme-builder/kit/btn-inicio-rapido-outline-sm-light.svg" alt="Inicio rápido" height="34" /></picture></a>
<a href="#-el-camino-de-un-video"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme-builder/kit/btn-el-camino-de-un-video-outline-sm-dark.svg" /><img src="assets/readme-builder/kit/btn-el-camino-de-un-video-outline-sm-light.svg" alt="El camino de un video" height="34" /></picture></a>
<a href="#-herramientas-mcp-15"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme-builder/kit/btn-herramientas-mcp-15-outline-sm-dark.svg" /><img src="assets/readme-builder/kit/btn-herramientas-mcp-15-outline-sm-light.svg" alt="Herramientas MCP (15)" height="34" /></picture></a>
<a href="#-roles-y-skills"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme-builder/kit/btn-roles-y-skills-outline-sm-dark.svg" /><img src="assets/readme-builder/kit/btn-roles-y-skills-outline-sm-light.svg" alt="Roles y skills" height="34" /></picture></a>
<a href="#-formas-de-publicar"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme-builder/kit/btn-formas-de-publicar-outline-sm-dark.svg" /><img src="assets/readme-builder/kit/btn-formas-de-publicar-outline-sm-light.svg" alt="Formas de publicar" height="34" /></picture></a>
<a href="#-estructura"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme-builder/kit/btn-estructura-outline-sm-dark.svg" /><img src="assets/readme-builder/kit/btn-estructura-outline-sm-light.svg" alt="Estructura" height="34" /></picture></a>
<a href="#-desarrollo"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme-builder/kit/btn-desarrollo-outline-sm-dark.svg" /><img src="assets/readme-builder/kit/btn-desarrollo-outline-sm-light.svg" alt="Desarrollo" height="34" /></picture></a>
<a href="#-bueno-saber"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme-builder/kit/btn-bueno-saber-outline-sm-dark.svg" /><img src="assets/readme-builder/kit/btn-bueno-saber-outline-sm-light.svg" alt="Bueno saber" height="34" /></picture></a>
</p>

<a id="-qué-hace"></a>
## <img src="assets/readme-builder/icons/layers.svg" width="24" height="24" alt="" /> Qué hace

<!-- kit:features -->
<p align="center"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme-builder/kit/features-es-dark.svg" /><img src="assets/readme-builder/kit/features-es-light.svg" alt="Cola por fecha: Una carpeta de día sale ese día: tres videos, tres publicaciones a las 05:00. Las semanas se reparten solas. · Ve cada video: 8 fotogramas y transcripción: qué pasa, si hay voz, si trae texto. · Texto por red: Gancho, cuerpo, CTA y hashtags validados con los límites reales de cada red. · Pie de redes: Cada descripción termina con tus usuarios en las otras redes. · Subtítulos: Ninguno, automáticos, .srt o quemados, con estilo para vertical. · Como sea: APIs oficiales, Postiz, un perfil de navegador o el propio agente. · Todos los días: Tarea programada con reintentos; se pone al día si la PC estuvo apagada. · Aprende: Mejores días, videos top y bottom, y un reporte semanal con máximo tres acciones." width="100%" /></picture></p>
<!-- /kit:features -->

<p align="center"><img src="assets/readme-builder/kit/wave.svg" alt="" width="100%" /></p>

<a id="-inicio-rápido"></a>
## <img src="assets/readme-builder/icons/rocket.svg" width="24" height="24" alt="" /> Inicio rápido

<p align="center"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/diagrams/publishing-es-dark.svg" /><img src="assets/readme/diagrams/publishing-es-light.svg" alt="Recorrido de uso, generado con Archify" width="100%" /></picture></p>


```powershell
git clone https://github.com/robgallardof/social-publisher-mcp.git
cd social-publisher-mcp
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/bootstrap.ps1        # entorno, pruebas, configs, MCP
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/install-schedule.ps1 # tarea diaria de las 05:00
```

macOS / Linux: `sh scripts/bootstrap.sh` y la línea de cron que imprime al final. Requiere [uv](https://docs.astral.sh/uv/).

**¿Prefieres Docker?** Es opcional: la imagen solo lleva el código del MCP y tu carpeta se monta al ejecutarla.

```bash
docker build -t social-forge:local .
docker run --rm -i -v "C:/ruta/a/social-publisher-mcp:/workspace" social-forge:local      # stdio, para clientes MCP
export SOCIAL_FORGE_MCP_TOKEN="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export SOCIAL_FORGE_PORT=8766
docker compose up -d --build --wait social-forge   # HTTP con token
```

Puertos, extras (`analysis`), el servicio de CLI y cómo programar `run-due` desde tu PC: [docs/DOCKER.md](docs/DOCKER.md) (en inglés).

Luego háblale a tu agente:

> *"Procesa el inbox"* · *"Prepara lo de mañana"* · *"Reparte la semana 44, dos por día"* · *"Ponle subtítulos al storytime"* · *"¿Qué funcionó esta semana?"* · *"Investiga tendencias de ardillas en México"*

### Conecta tu agente

Elige OpenCode o DeepSeek Harness para trabajar con este servidor desde tu agente. Primero revisa los cambios; después aplica la configuración.

```sh
python scripts/install-mcp.py --clients opencode --dry-run
python scripts/install-mcp.py --clients opencode
opencode mcp list
```

<details>
<summary>Usar DeepSeek Harness en su lugar</summary>

```sh
python scripts/install-mcp.py --clients deepseek --dry-run
python scripts/install-mcp.py --clients deepseek
dsh web --patch .dsh/mcp.cordis.yml
```

</details>

[Configuración, retirada y versiones comprobadas](scripts/CLIENTS.md).

<p align="center"><img src="assets/readme-builder/kit/wave.svg" alt="" width="100%" /></p>

<a id="-instalación-retirada-y-compatibilidad"></a>
<a id="-funciona-con-cualquier-agente"></a>
## <img src="assets/readme-builder/icons/bot.svg" width="24" height="24" alt="" /> Instalación, retirada y compatibilidad

`social-forge` es un **servidor MCP stdio** estándar. Además de sus herramientas expone cada **skill como recurso MCP** (`skill://<nombre>`) y cada **rol como prompt MCP**, así cualquier cliente MCP recibe el manual completo, no solo los que leen `.agents/`.

Un solo instalador lo registra, muestra el cambio antes y lo vuelve a quitar. Respalda cada archivo que toca como `.bak` y respeta los demás servidores del archivo.

| Cliente | `--clients` | Archivo que edita | Alcance | Probado |
|---|---|---|---|---|
| Claude Code | `claude-code` | `claude mcp --scope user` (+ skills y roles en `~/.claude` con `--with-skills`) | usuario | Pruebas del instalador con archivos temporales |
| Codex | `codex` | `~/.codex/config.toml` | usuario | Pruebas del instalador con archivos temporales |
| OpenCode 1.x | `opencode` | `opencode.json` | proyecto | Prueba con el host real 1.19.4 (CI en Linux) |
| DeepSeek Harness | `deepseek` | `.dsh/mcp.cordis.yml` | proyecto | Prueba con el runtime real 0.2.1-rc.2 (CI en Linux) |
| Gemini CLI | `gemini-cli` | `~/.gemini/settings.json` | usuario | Pruebas del instalador con archivos temporales |
| Antigravity | `antigravity` | `~/.gemini/antigravity/mcp_config.json` | usuario | Pruebas del instalador con archivos temporales |
| Cursor | `cursor` | `~/.cursor/mcp.json` | usuario | Pruebas del instalador con archivos temporales |
| VS Code | `vscode` | `Code/User/mcp.json` | usuario | Pruebas del instalador con archivos temporales |
| Windsurf | `windsurf` | `~/.codeium/windsurf/mcp_config.json` | usuario | Pruebas del instalador con archivos temporales |
| Claude Desktop | `claude-desktop` | `Claude/claude_desktop_config.json` | usuario | Pruebas del instalador con archivos temporales |

```powershell
python scripts/install-mcp.py --list                              # qué clientes tienes
python scripts/install-mcp.py --dry-run                           # muestra cada cambio, no escribe nada
python scripts/install-mcp.py --with-skills                       # lo registra para tu usuario en todos
python scripts/install-mcp.py --clients codex,cursor              # solo algunos clientes
python scripts/install-mcp.py --remove                            # deshacer (o --clients … --remove)
python scripts/install-mcp.py --workspace ../davinci-agents       # cualquier otro workspace con config/mcp.servers.json
```

La inferencia del modelo dentro de cada host necesita su propio login y no forma parte de estas pruebas.

<!-- kit:agent-links -->
<p align="center"><a href="scripts/CLIENTS.md"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme-builder/kit/agent-links-es-01-dark.svg" /><img src="assets/readme-builder/kit/agent-links-es-01-light.svg" alt="Instalación, retirada y versiones probadas" height="44" /></picture></a>&nbsp;
<a href="docs/DOCKER.md"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme-builder/kit/agent-links-es-02-dark.svg" /><img src="assets/readme-builder/kit/agent-links-es-02-light.svg" alt="Docker" height="34" /></picture></a></p>
<!-- /kit:agent-links -->

<p align="center"><img src="assets/readme-builder/kit/wave.svg" alt="" width="100%" /></p>

<a id="-el-camino-de-un-video"></a>
## <img src="assets/readme-builder/icons/layers.svg" width="24" height="24" alt="" /> El camino de un video

<details>
<summary>Diagrama técnico</summary>

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

</details>

<p align="center"><img src="assets/readme-builder/kit/wave.svg" alt="" width="100%" /></p>

<a id="-roles-y-skills"></a>
## <img src="assets/readme-builder/icons/layers.svg" width="24" height="24" alt="" /> Roles y skills

**Roles** (`.agents/agents/`): `community-manager` (líder) · `video-analyst` · `content-strategist` · `copywriter` · `publisher` · `audience-analyst` · `trend-researcher`

**Skills** (`.agents/skills/`): `content-queue` · `video-analysis` · `subtitles` · `platform-copywriting` · `social-publishing` (+ guía por red) · `agent-browser-upload` · `content-strategy` · `audience-analytics` · `trend-research` · `community-engagement`

El rol líder **pregunta antes de escribir**: tus usuarios en cada red, @menciones, links, hashtags fijos y preferencia de subtítulos.

<p align="center"><img src="assets/readme-builder/kit/wave.svg" alt="" width="100%" /></p>

<a id="-herramientas-mcp-15"></a>
## <img src="assets/readme-builder/icons/bot.svg" width="24" height="24" alt="" /> Herramientas MCP (15)

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

<p align="center"><img src="assets/readme-builder/kit/wave.svg" alt="" width="100%" /></p>

<a id="-formas-de-publicar"></a>
## <img src="assets/readme-builder/icons/layers.svg" width="24" height="24" alt="" /> Formas de publicar

| Backend | Redes | ¿Público de inmediato? | ¿Programa solo? |
|---|---|---|---|
| `meta_api` | Instagram, Facebook | <img src="assets/readme-builder/icons/check.svg" width="20" height="20" alt="" /> | Facebook <img src="assets/readme-builder/icons/check.svg" width="20" height="20" alt="" /> |
| `youtube_api` | YouTube | tras la auditoría de Google | <img src="assets/readme-builder/icons/check.svg" width="20" height="20" alt="" /> `publishAt` |
| `tiktok_api` | TikTok | tras la auditoría de TikTok | — |
| `postiz` | todas | <img src="assets/readme-builder/icons/check.svg" width="20" height="20" alt="" /> | <img src="assets/readme-builder/icons/check.svg" width="20" height="20" alt="" /> (la PC puede estar apagada) |
| `browser` | todas | <img src="assets/readme-builder/icons/check.svg" width="20" height="20" alt="" /> | — |
| `handoff` | todas | lo hace el agente | — |

Credenciales: [`docs/accounts.md`](docs/accounts.md). Viven en `secrets/` (ignorado por git).

<p align="center"><img src="assets/readme-builder/kit/wave.svg" alt="" width="100%" /></p>

<a id="-estructura"></a>
## <img src="assets/readme-builder/icons/layers.svg" width="24" height="24" alt="" /> Estructura

```
content/inbox/        suelta aquí los videos nuevos
content/queue/        AAAA-MM-DD/ (o AAAA-Www/) + <video>.post.yaml
content/published/    archivo con recibos          content/library/  tomas crudas, versiones renderizadas
brand/                voz, audiencia, hashtags     config/           social.yaml, flujos de navegador, servidores MCP
mcp/social-forge/     el MCP + CLI (domain → services → app → server/cli)
Dockerfile, compose.yaml   imagen opcional (stdio o HTTP con token)
.agents/              skills y roles portables     scripts/          bootstrap, install-mcp, schedule, sync
```

<p align="center"><img src="assets/readme-builder/kit/wave.svg" alt="" width="100%" /></p>

<a id="-bueno-saber"></a>
## <img src="assets/readme-builder/icons/layers.svg" width="24" height="24" alt="" /> Bueno saber

- Por **API**, TikTok y YouTube publican en privado hasta que auditen tu app: mientras, usa `browser` o `postiz`.
- La API de Instagram no tiene hora de publicación: se publica a las 05:00 en el momento, así que la PC debe estar encendida (o usa Postiz).
- Nunca publica dos veces: cada subida deja un recibo y los reintentos solo tocan lo que falló.
- Configurado ahora para **Chomi la ardilla** <img src="assets/readme-builder/icons/spark.svg" width="20" height="20" alt="" />; una marca nueva solo necesita `brand/` y `config/social.yaml`.

<div align="center"><sub>Hecho para creadores que prefieren grabar que pelearse con programadores de publicaciones.</sub></div>

<br/>

<p align="center"><img src="assets/readme-builder/kit/wave.svg" alt="" width="100%" /></p>

<a id="-desarrollo"></a>
## <img src="assets/readme-builder/icons/code.svg" width="24" height="24" alt="" /> Desarrollo

```bash
cd mcp/social-forge && uv run pytest     # 53 pruebas: sin red, ffmpeg real, MCP real por HTTP
python scripts/test_docker.py            # imagen real: stdio, CLI, HTTP con token, sin datos personales
python scripts/sync.py                   # después de editar .agents/ o config/
git config core.hooksPath .githooks      # quita los coautores de IA de los mensajes de commit
```

Reglas de arquitectura y cómo agregar un backend: [`AGENTS.md`](AGENTS.md).

<p align="center"><a href="#top"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme-builder/kit/btn-volver-al-inicio-outline-sm-dark.svg" /><img src="assets/readme-builder/kit/btn-volver-al-inicio-outline-sm-light.svg" alt="Volver al inicio" height="34" /></picture></a></p>

<!-- readme-builder:signature:start -->
<p align="center"><a href="https://github.com/robgallardof"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/brand/signature-es-dark.svg" /><img src="assets/readme/brand/signature-es-light.svg" alt="Social Forge / Roberto Gallardo" width="100%" /></picture></a></p>
<!-- readme-builder:signature:end -->
