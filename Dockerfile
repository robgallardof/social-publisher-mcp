# syntax=docker/dockerfile:1
# Image for the social-forge MCP + CLI. It only contains the server code: your videos,
# config/social.yaml, secrets/ and the browser profile are mounted at /workspace at run
# time and never baked into the image. See docs/DOCKER.md.
#
# Optional extras at build time: --build-arg EXTRAS=youtube,analysis
#   youtube  -> YouTube Data API backend (default)
#   analysis -> faster-whisper transcripts/subtitles (bigger image, CPU)
# The Playwright `browser` backend is not supported in the image: its one-time login
# needs a desktop browser session. Use it natively.
FROM python:3.12-slim-bookworm AS build
COPY --from=ghcr.io/astral-sh/uv:0.12.13 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
ARG EXTRAS=youtube
WORKDIR /app
COPY mcp/social-forge/pyproject.toml mcp/social-forge/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    set -e; flags=""; for e in $(echo "$EXTRAS" | tr ',' ' '); do flags="$flags --extra $e"; done; \
    uv sync --locked --no-dev --no-install-project $flags
COPY mcp/social-forge/src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    set -e; flags=""; for e in $(echo "$EXTRAS" | tr ',' ' '); do flags="$flags --extra $e"; done; \
    uv sync --locked --no-dev --no-editable $flags

FROM python:3.12-slim-bookworm
RUN groupadd --gid 10001 forge && useradd --uid 10001 --gid forge --create-home forge \
    && mkdir /workspace && chown forge:forge /workspace
COPY --from=build /app/.venv /app/.venv
ENV PATH=/app/.venv/bin:$PATH SOCIAL_FORGE_ROOT=/workspace PYTHONUNBUFFERED=1 PYTHONUTF8=1 \
    HF_HOME=/workspace/.cache/huggingface TZ=America/Mexico_City
USER forge
WORKDIR /workspace
EXPOSE 8080
ENTRYPOINT ["social-forge-mcp"]
CMD ["--stdio"]
