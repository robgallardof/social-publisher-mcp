"""Upload through the real website with Playwright and a persistent, logged-in profile per platform.

No API approval needed, posts are public. Selectors live in config/browser_flows.yaml (data, not code)
so a UI change is fixed by editing YAML. Log in once with `uv run social-forge login <platform>`.
Profiles: <root>/.profiles/<platform> (git-ignored, they hold your session cookies).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import yaml

from ...config import Settings
from . import Job, PublisherError


def flows(settings: Settings) -> dict:
    return yaml.safe_load((settings.root / "config" / "browser_flows.yaml").read_text(encoding="utf-8"))


def profile_dir(settings: Settings, platform: str) -> Path:
    return settings.root / ".profiles" / platform


def launch(pw, settings: Settings, platform: str, headless: bool):
    opts = settings.accounts.get("browser", {})
    return pw.chromium.launch_persistent_context(
        str(profile_dir(settings, platform)), headless=headless, channel=opts.get("channel", "chrome"),
        viewport={"width": 1366, "height": 900}, locale=opts.get("locale", "es-MX"),
        timezone_id=settings.timezone, args=["--disable-blink-features=AutomationControlled"])


def login(settings: Settings, platform: str) -> str:
    from playwright.sync_api import sync_playwright

    flow = flows(settings)[platform]
    with sync_playwright() as pw:
        ctx = launch(pw, settings, platform, headless=False)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(flow["login_url"])
        print(f"Log in to {platform} in the opened window, then close it.")
        page.wait_for_event("close", timeout=0)
        ctx.close()
    return f"{platform} session saved in {profile_dir(settings, platform)}"


def render(value: str, job: Job) -> str:
    return value.format(caption=job.copy.caption, title=job.copy.title or "", video=str(job.video))


def run_steps(page, steps: list[dict], job: Job) -> None:
    for i, step in enumerate(steps):
        kind, timeout = step["do"], step.get("timeout", 30) * 1000
        try:
            if kind == "goto":
                page.goto(step["url"], wait_until="domcontentloaded")
            elif kind == "upload":
                page.locator(step["selector"]).first.set_input_files(str(job.video), timeout=timeout)
            elif kind == "wait":
                page.wait_for_timeout(step["seconds"] * 1000)
            elif kind == "wait_for":
                page.locator(step["selector"]).first.wait_for(state=step.get("state", "visible"), timeout=timeout)
            elif kind == "click":
                page.locator(step["selector"]).first.click(timeout=timeout)
            elif kind == "fill":
                box = page.locator(step["selector"]).first
                box.click(timeout=timeout)
                if step.get("clear", True):
                    page.keyboard.press("Control+A")
                    page.keyboard.press("Delete")
                page.keyboard.insert_text(render(step["text"], job))
            elif kind == "press":
                page.keyboard.press(step["key"])
            else:
                raise PublisherError(f"unknown browser step {kind!r}")
        except PublisherError:
            raise
        except Exception as e:  # noqa: BLE001 - playwright raises many types; report which step broke
            if step.get("optional"):
                continue
            raise PublisherError(f"step {i + 1} ({kind} {step.get('selector', step.get('url', ''))}): "
                                 f"{str(e).splitlines()[0]}") from e


class Browser:
    name = "browser"
    native_schedule = False

    def __init__(self, settings: Settings, platform: str):
        self.settings, self.platform = settings, platform

    def check(self) -> str:
        try:
            import playwright  # noqa: F401
        except ImportError:
            return "install extras: uv sync --extra browser && uv run playwright install chromium"
        if not profile_dir(self.settings, self.platform).exists():
            return f"not logged in: uv run social-forge login {self.platform}"
        return "ready (session may expire: re-run login if a post fails on the login page)"

    def publish(self, job: Job, now: datetime) -> dict:
        from playwright.sync_api import sync_playwright

        flow = flows(self.settings)[self.platform]
        shots = self.settings.root / "content" / "handoff" / "screenshots"
        shots.mkdir(parents=True, exist_ok=True)
        headless = self.settings.accounts.get("browser", {}).get("headless", False)
        with sync_playwright() as pw:
            ctx = launch(pw, self.settings, self.platform, headless=headless)
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            shot = shots / f"{job.video.stem}-{self.platform}.png"
            try:
                run_steps(page, flow["steps"], job)
            except PublisherError as e:
                page.screenshot(path=str(shot), full_page=True)
                raise PublisherError(f"{e} (screenshot: {shot})") from e
            finally:
                page.wait_for_timeout(1500)
                ctx.close()
        return {"status": "published", "via": "browser", "url": None,
                "note": "confirm the post on the profile; browser uploads have no post id"}
