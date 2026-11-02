"""Command line for the scheduled task and one-time setup.

  social-forge run-due [--dry-run]      publish what is due (the 05:00 task calls this)
  social-forge status | doctor | plan-week [WEEK] [--apply]
  social-forge auth youtube             OAuth once, stores secrets/youtube_token.json
  social-forge login <platform>         log in once in the Playwright profile (browser backend)
  social-forge metrics | report
"""

from __future__ import annotations

import json
import logging
import sys
from logging.handlers import RotatingFileHandler

from . import app


def log_to_file() -> logging.Logger:
    path = app.settings().root / "logs" / "social-forge.log"
    path.parent.mkdir(exist_ok=True)
    log = logging.getLogger("social-forge")
    log.setLevel(logging.INFO)
    log.addHandler(RotatingFileHandler(path, maxBytes=1_000_000, backupCount=5, encoding="utf-8"))
    return log


def dump(obj) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):  # Windows consoles default to cp1252: captions carry emojis
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = list(sys.argv[1:] if argv is None else argv)
    cmd = args.pop(0) if args else "status"
    flag = lambda name: name in args and not args.remove(name)  # noqa: E731
    if cmd == "run-due":
        dry = flag("--dry-run")
        report = app.publish_due(dry_run=dry)
        log_to_file().info("%s run-due dry=%s %s", app.now().isoformat(), dry, json.dumps(report, default=str))
        dump(report)
        return 1 if any((r.get("result") or {}).get("status") == "failed" for r in report) else 0
    if cmd == "status":
        dump(app.queue_status())
    elif cmd == "doctor":
        dump(app.backends_status())
    elif cmd == "plan-week":
        apply = flag("--apply")
        dump(app.plan_week(args[0] if args else None, apply))
    elif cmd == "auth" and args[:1] == ["youtube"]:
        from .services.publishers import youtube
        print(youtube.authorize(app.settings()))
    elif cmd == "login" and args:
        from .services.publishers import browser
        print(browser.login(app.settings(), args[0]))
    elif cmd == "metrics":
        dump(app.pull_metrics())
    elif cmd == "report":
        dump(app.insights_report())
    elif cmd in ("code-review", "code-approve", "code-cancel", "code-reconcile"):
        from .services.code_approvals import Approvals
        from .domain.code_mode import CodeModeError
        approvals = Approvals(app.settings())
        try:
            if cmd == "code-review" and len(args) == 1:
                dump(approvals.get(args[0]))
            elif cmd == "code-approve" and len(args) in (2, 3):
                dump(approvals.approve(args[0], args[1], int(args[2]) if len(args) == 3 else 604800))
            elif cmd == "code-cancel" and len(args) == 1:
                dump(approvals.cancel(args[0]))
            elif cmd == "code-reconcile" and len(args) in (3, 4):
                dump(approvals.reconcile(args[0], args[1], args[2], args[3] if len(args) == 4 else None))
            else:
                print("Usage: code-review ID | code-approve ID EXACT_DIGEST [TTL_SECONDS] | code-cancel ID | "
                      "code-reconcile ID PLATFORM published REMOTE_ID | code-reconcile ID PLATFORM not_published")
                return 2
        except CodeModeError as error:
            dump({"error": error.code})
            return 1
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
