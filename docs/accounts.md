# Cuentas y credenciales

Todo va en `secrets/` (ignorado por git). Después de cada paso: `uv run social-forge doctor` desde `mcp/social-forge`.

## Navegador (`browser`): el camino sin aprobaciones

1. `cd mcp/social-forge && uv sync --extra browser --extra youtube && uv run playwright install chromium`
2. `uv run social-forge login tiktok` (y `instagram`, `facebook`, `youtube`): se abre Chrome, inicias sesión, cierras la ventana.
   La sesión queda en `.profiles/<plataforma>`. Si un día falla con la página de login, repite este paso.
3. Prueba con un video de prueba en una cuenta secundaria antes de confiar en los selectores
   (`config/browser_flows.yaml`; si algo cambió en la web, el error trae captura en `content/handoff/screenshots/`).

## YouTube (`youtube_api`)

1. Google Cloud Console → proyecto nuevo → habilita **YouTube Data API v3**.
2. OAuth consent screen: External, agrega tu correo como test user; **publica la app** (en modo Testing los tokens caducan a los 7 días).
3. Credentials → OAuth client ID → *Desktop app* → descarga el JSON a `secrets/youtube_client_secret.json`.
4. `uv run social-forge auth youtube` → autoriza en el navegador → crea `secrets/youtube_token.json`.
5. Importante: los proyectos sin auditoría suben **solo privados**. Solicita el audit (formulario "YouTube API Services - Audit and Quota Extension").
   Mientras tanto usa `browser` o `postiz` para YouTube.

## Instagram + Facebook (`meta_api`)

Requisitos: cuenta de Instagram **Business** vinculada a una **Página** de Facebook.
1. developers.facebook.com → App (tipo Business) → producto *Facebook Login for Business* + *Instagram*.
2. Permisos: `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`,
   `pages_manage_posts`, `instagram_manage_insights`, `read_insights`, `business_management`.
3. Lo más estable: Business Manager → *System User* (admin) → asigna la app, la Página y la cuenta IG → genera token
   (no caduca). Alternativa: token de usuario de larga duración (60 días) + token de página.
4. `secrets/meta.json`:
   ```json
   {"access_token": "<token con permisos de Instagram>", "page_access_token": "<token de la Página>"}
   ```
5. En `config/social.yaml` → `accounts.meta.ig_user_id` (Graph API Explorer: `me/accounts?fields=instagram_business_account`)
   y `accounts.meta.page_id`.
6. Uso propio (tu cuenta, tu app en modo Live con tu rol de admin) no necesita App Review para publicar en tus cuentas.

## TikTok (`tiktok_api`)

1. developers.tiktok.com → app → producto *Content Posting API* con **Direct Post** → scope `video.publish` (+ `video.list` para métricas).
2. OAuth (Login Kit) para obtener `access_token` del creador → `secrets/tiktok.json`: `{"access_token": "act...."}`.
   El token dura 24 h; refresca con `refresh_token` (365 días) o usa `browser`/`postiz`.
3. Sin auditoría todo se publica **SELF_ONLY** (privado). Solicita el audit; mientras, TikTok va por `browser` o `postiz`.

## Postiz (`postiz`): todas las redes, la PC puede estar apagada

1. Postiz cloud (postiz.com) o self-hosted (github.com/gitroomhq/postiz-app, Docker).
2. Conecta TikTok, Instagram, Facebook y YouTube en Postiz (usa sus apps ya auditadas en cloud).
3. Settings → Developers → Public API → API key → `secrets/postiz.json`: `{"api_key": "..."}`.
4. `config/social.yaml`: `accounts.postiz.url` y `accounts.postiz.integrations` (ids: `social-forge doctor` los lista).
5. Pon `backends: {...: postiz}` y `mode: ahead` para subir con anticipación y que Postiz publique a las 05:00.
   Postiz también trae su propio MCP (`/mcp` en tu instancia) si quieres usarlo directamente.
