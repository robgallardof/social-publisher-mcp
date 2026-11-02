"""No provider traffic. Code Mode is standard; real restricted JS tests use the required Deno runtime."""

import asyncio
import json
import os
import shutil

import pytest
from conftest import add_video, at

from social_forge import config
from social_forge.domain.code_mode import CodeModeError, CodeModeSettings
from social_forge.services import media, queue, runner
from social_forge.services.code_approvals import Approvals
from social_forge.services.code_registry import Registry
from social_forge.services.code_sandbox import execute
from social_forge.services.locking import WorkspaceBusy, exclusive
from social_forge.services.publishers import RetrySafePublisherError

DRAFT = {"caption": "A short video", "title": "A title", "platforms": ["tiktok", "youtube"]}


@pytest.fixture
def cm(settings, monkeypatch):
    settings.backends = {"tiktok": "tiktok_api", "youtube": "youtube_api"}
    settings.code_mode = {}
    deno = os.environ.get("SOCIAL_FORGE_TEST_DENO") or shutil.which("deno")
    if deno:
        settings.code_mode["deno"] = deno
    monkeypatch.setattr(media, "probe", lambda _: media.Probe(4, 1080, 1920, 0.001))
    return settings


@pytest.fixture
def js(cm):
    if not shutil.which(cm.code_mode.get("deno", "deno")):
        pytest.fail("Deno 2 is required; install it or set SOCIAL_FORGE_TEST_DENO to its executable")
    return cm


def proposal(cm, ws):
    add_video(ws, "2026-10-27/a.mp4")
    return Registry(cm).dispatch("posts.propose", {"video": "2026-10-27/a.mp4", "draft": DRAFT})


def approved(cm, ws):
    value = proposal(cm, ws)
    Approvals(cm).approve(value["proposal_id"], value["digest"])
    return value


def test_discovery_schemas_relevance_and_permission_filters(cm):
    registry = Registry(cm)
    found = registry.search("schedule", limit=3)
    assert found["capabilities"][0]["name"].startswith("schedule.")
    assert all(c["side_effect"] == "read" for c in registry.search(read_only=True, limit=10)["capabilities"])
    draft = registry.capabilities["posts.propose"].describe(registry.providers)
    assert "$defs" in draft["input_schema"] and draft["output_schema"]["type"] == "object"
    assert "approve" not in registry.capabilities
    assert "posts.publish" not in registry.capabilities
    assert len(registry.search("nonexistent gibberish")["capabilities"]) == 0


@pytest.mark.parametrize("name,args", [
    ("posts.publish", {}), ("owner.approve", {}), ("__class__", {}),
    ("accounts.list", {"accountId": "other-user"}), ("accounts.capabilities", {"platform": "linkedin"}),
    ("media.inspect", {"video": "../secrets/tiktok.json", "targets": ["tiktok"]}),
    ("queue.list", {"days": "7"}), ("queue.list", {"days": 0}),
    ("posts.propose", {"video": "x", "draft": {**DRAFT, "approved": True}}),
])
def test_dispatch_rejects_unknown_operations_arguments_and_paths(cm, name, args):
    with pytest.raises(CodeModeError):
        Registry(cm).dispatch(name, args)


def test_account_isolation_and_host_permission_checks(cm):
    cm.code_mode["allowed_platforms"] = ["youtube"]
    registry = Registry(cm)
    assert [a["platform"] for a in registry.dispatch("accounts.list", {})["accounts"]] == ["youtube"]
    with pytest.raises(CodeModeError, match="account_denied"):
        registry.dispatch("accounts.capabilities", {"platform": "tiktok"})
    with pytest.raises(CodeModeError, match="capability_denied"):
        registry.dispatch("schedule.create", {"proposal_id": "x"}, permissions={"accounts:read"})
    with pytest.raises(CodeModeError):
        registry.search(provider="facebook")


def test_read_only_workflow(js):
    result = asyncio.run(execute(js, """
      const accounts = (await social.accounts.list()).accounts;
      return await Promise.all(accounts.map(a => social.accounts.capabilities({platform:a.platform})));
    """))
    assert result["status"] == "ok"
    assert {r["account_id"] for r in result["result"]} == {"workspace:tiktok", "workspace:youtube"}
    assert len(result["calls"]) == 3
    assert result["metrics"]["peak_rss_bytes"] > 0


def test_draft_and_approval_workflow(js, ws):
    add_video(ws, "2026-10-27/a.mp4")
    code = f"""
      const args = {{video:'2026-10-27/a.mp4', draft:{json.dumps(DRAFT)}}};
      const preview = await social.posts.preview(args);
      const proposal = await social.posts.propose(args);
      let blocked = false;
      try {{ await social.schedule.create({{proposal_id:proposal.proposal_id}}); }}
      catch {{ blocked = true; }}
      return {{preview, proposal, blocked}};
    """
    result = asyncio.run(execute(js, code, read_only=False))["result"]
    assert result["blocked"] and result["proposal"]["status"] == "PENDING_APPROVAL"
    assert not queue.scan(js.queue_dir)[0].sidecar.exists()


class FakeOfficial:
    native_schedule = True

    def __init__(self, platform, calls, fail=False, uncertain=False):
        self.platform, self.calls, self.fail, self.uncertain = platform, calls, fail, uncertain

    def check(self):
        return "ready"

    def publish(self, job, now):
        self.calls.append(self.platform)
        if self.uncertain:
            raise TimeoutError("secret-token-must-not-leak")
        if self.fail:
            raise RetrySafePublisherError("secret-token-must-not-leak")
        return {"status": "published", "id": self.platform + "-remote"}


def test_scheduled_restart_partial_failure_and_safe_retry(cm, ws):
    value = approved(cm, ws)
    pid = value["proposal_id"]
    assert Approvals(cm).schedule(pid)["status"] == "SCHEDULED"
    assert Approvals(cm).schedule(pid)["status"] == "SCHEDULED"  # activation is idempotent
    # New Settings / Approvals instances simulate restart; no runtime JS or in-memory timer is needed.
    restarted = config.load(ws)
    restarted.backends, restarted.code_mode = cm.backends, cm.code_mode
    calls = []
    runner.run(restarted, at(2026, 10, 27, 5), factory=lambda _, p, s: FakeOfficial(p, calls, fail=p == "tiktok"))
    assert sorted(calls) == ["tiktok", "youtube"]
    first = Registry(cm).status(pid)
    assert first["status"] == "PARTIALLY_PUBLISHED"
    opid = first["receipts"]["tiktok"]["operation_id"]
    calls.clear()
    runner.run(restarted, at(2026, 10, 27, 5, 1), factory=lambda _, p, s: FakeOfficial(p, calls))
    assert calls == ["tiktok"]
    final = Registry(cm).status(pid)
    assert final["status"] == "PUBLISHED"
    assert final["receipts"]["tiktok"]["operation_id"] == opid
    assert runner.run(restarted, at(2026, 10, 27, 5, 2), factory=lambda *_: pytest.fail("duplicate")) == []


@pytest.mark.parametrize("change", ["media", "copy", "target", "privacy", "time", "identity", "expiry", "cancel"])
def test_material_changes_invalidate_approval(cm, ws, change):
    value = approved(cm, ws)
    pid = value["proposal_id"]
    approvals = Approvals(cm)
    approvals.schedule(pid)
    item = queue.scan(cm.queue_dir)[0]
    if change == "media":
        item.video.write_bytes(b"modified")
    elif change in ("copy", "privacy", "time"):
        if change == "copy":
            item.spec.caption = "changed"
        elif change == "privacy":
            item.spec.overrides["youtube"]["privacy"] = "private"
        else:
            item.spec.publish_time = "06:00"
        queue.save_spec(item.video, item.spec)
    elif change == "target":
        cm.accounts["meta"] = {"page_id": "another-owner"}
    elif change == "identity":
        cm.code_mode["principal"] = "another-owner"
    elif change == "expiry":
        with approvals.connect() as db:
            db.execute("UPDATE proposals SET expires=0")
    else:
        approvals.cancel(pid)
    result = runner.run(cm, at(2026, 10, 27, 6), factory=lambda *_: pytest.fail("unauthorized publication"))
    assert all(r["do"] == "skip" for r in result)


def test_wrong_digest_rejection_and_identity_isolation(cm, ws):
    value = proposal(cm, ws)
    with pytest.raises(CodeModeError, match="approval_mismatch"):
        Approvals(cm).approve(value["proposal_id"], "wrong")
    cm.code_mode["principal"] = "other"
    with pytest.raises(CodeModeError, match="proposal_not_found"):
        Approvals(cm).get(value["proposal_id"])


def test_credential_replacement_invalidates_approved_targets(cm, ws):
    from social_forge.services import secrets
    secrets.save(cm, "tiktok", {"access_token": "FAKE_ORIGINAL_OWNER"})
    value = approved(cm, ws)
    assert "credential_hash" not in value
    secrets.save(cm, "tiktok", {"access_token": "FAKE_DIFFERENT_OWNER"})
    with pytest.raises(CodeModeError, match="approval_invalidated"):
        Approvals(cm).schedule(value["proposal_id"])


def test_youtube_refresh_preserves_binding_but_new_identity_does_not(cm, ws):
    from social_forge.services import secrets
    secrets.save(cm, "youtube_token", {"token": "OLD_ACCESS", "refresh_token": "STABLE_FAKE", "client_id": "APP"})
    value = approved(cm, ws)
    secrets.save(cm, "youtube_token", {"token": "NEW_ACCESS", "refresh_token": "STABLE_FAKE", "client_id": "APP"})
    assert Approvals(cm).schedule(value["proposal_id"])["status"] == "SCHEDULED"
    secrets.save(cm, "youtube_token", {"token": "NEW_ACCESS", "refresh_token": "OTHER_FAKE", "client_id": "APP"})
    assert all(a["do"] == "skip" for a in runner.plan(cm, at(2026, 10, 27, 5)))


def test_timeout_and_crash_do_not_republish(cm, ws):
    value = approved(cm, ws)
    Approvals(cm).schedule(value["proposal_id"])
    calls = []
    runner.run(cm, at(2026, 10, 27, 5), factory=lambda _, p, s: FakeOfficial(p, calls, uncertain=True))
    assert len(calls) == 2
    assert Registry(cm).status(value["proposal_id"])["status"] == "UNKNOWN"
    result = runner.run(cm, at(2026, 10, 27, 5, 1), factory=lambda *_: pytest.fail("unsafe retry"))
    assert all(r["do"] == "attention" for r in result)
    assert "secret-token" not in json.dumps(result)


def test_inflight_after_process_death_requires_reconciliation(cm, ws):
    value = approved(cm, ws)
    Approvals(cm).schedule(value["proposal_id"])
    item = queue.scan(cm.queue_dir)[0]
    for target in DRAFT["platforms"]:
        queue.record(item, target, {"status": "publishing", "operation_id": "stable"})
    assert all(r["do"] == "attention" for r in runner.run(cm, at(2026, 10, 27, 5),
                                                         factory=lambda *_: pytest.fail("unsafe retry")))


def test_worker_lock_blocks_simultaneous_publishing(cm):
    with exclusive(cm.root), pytest.raises(WorkspaceBusy):
        runner.run(cm, at(2026, 10, 27, 5))


@pytest.mark.parametrize("attack", [
    "Deno.readTextFile('/etc/passwd')", "Deno.env.get('SOCIAL_FORGE_MCP_TOKEN')",
    "Deno.writeTextFile('owned.txt','owned')", "new Deno.Command('whoami').output()",
    "fetch('https://example.com')", "import('node:fs').then(fs=>fs.readFileSync('/etc/passwd'))",
    "import('https://example.com/exploit.js')", "import('file:///etc/passwd')",
    "Deno.dlopen('anything',{})",
])
def test_real_sandbox_denies_host_access(js, attack):
    result = asyncio.run(execute(js, f"try {{ await ({attack}); return 'ESCAPED'; }} catch {{return 'denied';}}"))
    assert result["result"] == "denied"


def test_generated_code_cannot_request_permissions(js):
    result = asyncio.run(execute(js, "return (await Deno.permissions.request({name:'read'})).state"))
    assert result["result"] == "denied"


def test_existing_credential_file_canary_is_not_readable(js, ws):
    path = ws / "secrets" / "canary.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text('{"access_token":"FAKE_CANARY_MUST_STAY_PRIVATE"}', encoding="utf-8")
    for operation in (f"Deno.readTextFile({json.dumps(str(path))})",
                      f"import('node:fs').then(fs=>fs.readFileSync({json.dumps(str(path))},'utf8'))"):
        result = asyncio.run(execute(js, f"try {{return await ({operation});}} catch(e) {{return e.name;}}"))
        assert result["result"] in ("NotCapable", "PermissionDenied")


def test_process_wide_execution_admission_limit(js):
    async def run():
        first = asyncio.create_task(execute(js, "await new Promise(r=>setTimeout(r,5000)); return 1"))
        second = asyncio.create_task(execute(js, "await new Promise(r=>setTimeout(r,5000)); return 1"))
        await asyncio.sleep(0.2)
        try:
            with pytest.raises(CodeModeError, match="execution_concurrency_limit"):
                await execute(js, "return 1")
        finally:
            first.cancel()
            second.cancel()
            await asyncio.gather(first, second, return_exceptions=True)
        return await execute(js, "return 42")
    assert asyncio.run(run())["result"] == 42


def test_native_memory_is_monitored(js):
    js.code_mode["memory_mb"] = 64
    code = "const a=[]; while(true) {a.push(new Uint8Array(8*1024*1024).fill(1)); await new Promise(r=>setTimeout(r,5));}"
    with pytest.raises(CodeModeError, match="memory_limit"):
        asyncio.run(execute(js, code))


def test_js_read_only_cannot_write_and_partial_failure_is_reported(js):
    result = asyncio.run(execute(js, """
      const good = await social.accounts.list();
      try { await social.schedule.cancel({proposal_id:'x'}); } catch(e) { return {good, error:e.message}; }
    """))
    assert result["result"]["error"] == "capability_denied"
    assert [c["status"] for c in result["calls"]] == ["ok", "capability_denied"]


@pytest.mark.parametrize("code,limits,error", [
    ("while(true) {}", {"timeout_ms": 200}, "execution_timeout"),
    ("return 'x'.repeat(100000)", {"max_output_bytes": 1024}, "output_limit"),
    ("for(let i=0;i<5;i++) await social.accounts.list(); return 1;", {"max_calls": 2}, "call_limit"),
    ("while(true) {}", {"cpu_ms": 100}, "cpu_limit"),
])
def test_resource_limits(js, code, limits, error):
    js.code_mode.update(limits)
    with pytest.raises(CodeModeError, match=error):
        asyncio.run(execute(js, code))


def test_cancellation_releases_execution_slot(js):
    async def run():
        task = asyncio.create_task(execute(js, "while(true) {}"))
        await asyncio.sleep(0.3)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        return await execute(js, "return 42")
    assert asyncio.run(run())["result"] == 42
    with Approvals(js).connect() as db:
        assert db.execute("SELECT count(*) FROM audit WHERE operation='sandbox' AND status='cancelled'").fetchone()[0] == 1


def test_missing_runtime_and_invalid_config(cm):
    cm.code_mode = {"deno": "no-such-deno"}
    with pytest.raises(CodeModeError, match="deno_executable_required"):
        asyncio.run(execute(cm, "return 1"))
    for data in ({"max_concurrency": 0}, {"enabled": False}, {"enabled": True}, {"require_approval": False}):
        with pytest.raises((ValueError, TypeError)):
            CodeModeSettings.from_dict(data)


def test_provider_errors_and_audit_do_not_contain_secrets(cm, monkeypatch):
    registry = Registry(cm)
    def fail():
        raise RuntimeError("Bearer SUPER_SECRET")
    registry.capabilities["accounts.list"].handler = fail
    with pytest.raises(CodeModeError, match="operation_failed"):
        registry.dispatch("accounts.list", {})
    with registry.approvals.connect() as db:
        rows = [tuple(r) for r in db.execute("SELECT * FROM audit")]
    assert "SUPER_SECRET" not in str(rows)


def test_analytics_cached_and_explicit_unavailable(cm):
    result = Registry(cm).dispatch("analytics.summary", {})
    assert result["freshness"] == "cached" and "reach" in result["unavailable"]


def test_official_adapter_and_privacy_restrictions(cm, ws):
    add_video(ws, "2026-10-27/a.mp4")
    cm.backends["tiktok"] = "browser"
    with pytest.raises(CodeModeError, match="official_backend_required"):
        Registry(cm).dispatch("posts.propose", {"video": "2026-10-27/a.mp4", "draft": DRAFT})
    cm.backends["tiktok"] = "tiktok_api"
    with pytest.raises(CodeModeError, match="privacy_unsupported"):
        Registry(cm).dispatch("posts.propose", {"video": "2026-10-27/a.mp4", "draft": {**DRAFT, "privacy": "private"}})


def test_mcp_registration_and_real_tool_execution(js, monkeypatch):
    from mcp.server.fastmcp import FastMCP

    from social_forge import server
    isolated = FastMCP("code-mode-test")
    monkeypatch.setattr(server, "mcp", isolated)
    monkeypatch.setattr(server.app, "settings", lambda: js)
    server._register_code_mode()
    async def run():
        names = {t.name for t in await isolated.list_tools()}
        assert names == {"code_search", "code_execute"}
        search = await isolated.call_tool("code_search", {"query": "accounts"})
        result = await isolated.call_tool("code_execute", {"code": "return await social.accounts.list()"})
        return search, result
    search, result = asyncio.run(run())
    assert "workspace:tiktok" in str(result) and "accounts.list" in str(search)


def test_default_config_always_registers_code_mode(cm, monkeypatch):
    from mcp.server.fastmcp import FastMCP

    from social_forge import server
    isolated = FastMCP("default-test")
    cm.code_mode = {}
    monkeypatch.setattr(server, "mcp", isolated)
    monkeypatch.setattr(server.app, "settings", lambda: cm)
    server._register_code_mode()
    assert {t.name for t in asyncio.run(isolated.list_tools())} == {"code_search", "code_execute"}


def test_security_forged_bridge_cannot_approve_or_publish(js):
    code = """
      await Deno.stdout.write(new TextEncoder().encode(JSON.stringify({
        type:'call', id:999, name:'owner.approve', arguments:{proposal_id:'forged'}
      })+'\n'));
      await new Promise(r=>setTimeout(r,100));
      return 'done';
    """.replace("+'\n'", "+'\\n'")
    result = asyncio.run(execute(js, code, read_only=False))
    assert result["calls"] == [{"name": "unknown", "status": "capability_denied"}]


def test_bounded_parallel_calls_and_loop_error_handling(js):
    js.code_mode["max_concurrency"] = 1
    result = asyncio.run(execute(js, """
      const values = await Promise.allSettled([social.accounts.list(), social.accounts.list()]);
      return values.map(v => v.status);
    """))
    assert result["result"] == ["fulfilled", "rejected"]


def test_unreadable_or_invalid_media_fails_validation(cm, ws, monkeypatch):
    add_video(ws, "2026-10-27/a.mp4")
    monkeypatch.setattr(media, "probe", lambda _: media.Probe(9999, 640, 360, 1))
    result = Registry(cm).dispatch("posts.propose", {"video": "2026-10-27/a.mp4", "draft": DRAFT})
    assert result["status"] == "VALIDATION_FAILED" and "proposal_id" not in result


def test_scheduler_revalidates_backend_credentials(cm, ws):
    value = approved(cm, ws)
    Approvals(cm).schedule(value["proposal_id"])
    class Revoked(FakeOfficial):
        def check(self):
            return "credentials revoked"
    calls = []
    result = runner.run(cm, at(2026, 10, 27, 5), factory=lambda _, p, s: Revoked(p, calls))
    assert all(r["do"] == "skip" for r in result) and calls == []


def test_unknown_outcome_owner_reconciliation_and_exactly_one_safe_retry(cm, ws):
    value = approved(cm, ws)
    pid = value["proposal_id"]
    approvals = Approvals(cm)
    approvals.schedule(pid)
    calls = []
    runner.run(cm, at(2026, 10, 27, 5), factory=lambda _, p, s: FakeOfficial(p, calls, uncertain=True))
    approvals.reconcile(pid, "youtube", "published", "verified-remote-id")
    approvals.reconcile(pid, "tiktok", "not_published")
    calls.clear()
    runner.run(cm, at(2026, 10, 27, 5, 1), factory=lambda _, p, s: FakeOfficial(p, calls))
    assert calls == ["tiktok"] and Registry(cm).status(pid)["status"] == "PUBLISHED"


def test_cross_process_lock(cm):
    import subprocess
    import sys
    code = ("from pathlib import Path; from social_forge.services.locking import exclusive, WorkspaceBusy; "
            "import sys\ntry:\n with exclusive(Path(sys.argv[1])): sys.exit(9)\nexcept WorkspaceBusy: sys.exit(0)")
    with exclusive(cm.root):
        result = subprocess.run([sys.executable, "-c", code, str(cm.root)], timeout=5, check=False)
    assert result.returncode == 0


def test_real_stdio_mcp_client_and_backward_compatibility(js, ws):
    import sys

    import yaml
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    (ws / "config" / "social.yaml").write_text(yaml.safe_dump({
        "default_platforms": js.default_platforms, "backends": js.backends, "code_mode": js.code_mode,
    }), encoding="utf-8")
    async def run():
        parameters = StdioServerParameters(command=sys.executable, args=["-m", "social_forge.server"],
                                           env={**os.environ, "SOCIAL_FORGE_ROOT": str(ws)})
        async with stdio_client(parameters) as (read, write), ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert {"publish_due", "write_post", "code_search", "code_execute"} <= {t.name for t in tools.tools}
            result = await session.call_tool("code_execute", {"code": "return await social.accounts.list()"})
            assert not result.isError
            assert "workspace:youtube" in result.content[0].text
            direct = await session.call_tool("platform_rules", {})
            assert "YouTube" in direct.content[0].text
    asyncio.run(run())


def test_approved_tiktok_never_falls_back_to_different_privacy(cm, ws):
    import httpx

    from social_forge.domain.post import Copy
    from social_forge.services import secrets
    from social_forge.services.publishers import Job
    from social_forge.services.publishers.tiktok import TikTokApi
    video = add_video(ws, "2026-10-27/a.mp4")
    secrets.save(cm, "tiktok", {"access_token": "FAKE_FOR_TEST"})
    requests = []
    def handler(request):
        requests.append(request.url.path)
        return httpx.Response(200, json={"data": {"privacy_level_options": ["SELF_ONLY"]}, "error": {"code": "ok"}})
    client = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(RetrySafePublisherError):
        TikTokApi(cm, client).publish(Job(video, Copy("tiktok", "caption"), at(2026, 10, 27, 5),
                                        "operation", "approval"), at(2026, 10, 27, 5))
    assert len(requests) == 1 and requests[0].endswith("creator_info/query/")


def test_scheduled_actual_meta_adapters_with_fake_http_servers(cm, ws):
    """Workflow C through real provider adapters; MockTransport stands in for both provider servers."""
    import httpx

    from social_forge.services import secrets
    from social_forge.services.publishers.meta import MetaApi
    cm.default_platforms = ["instagram", "facebook"]
    cm.backends = {"instagram": "meta_api", "facebook": "meta_api"}
    cm.accounts = {"meta": {"ig_user_id": "IG", "page_id": "PAGE"}}
    secrets.save(cm, "meta", {"access_token": "FAKE_IG", "page_access_token": "FAKE_FB"})
    add_video(ws, "2026-10-27/a.mp4")
    value = Registry(cm).dispatch("posts.propose", {"video": "2026-10-27/a.mp4", "draft": {
        **DRAFT, "platforms": cm.default_platforms}})
    approvals = Approvals(cm)
    approvals.approve(value["proposal_id"], value["digest"])
    approvals.schedule(value["proposal_id"])
    posted, attempts = [], []
    fail_facebook = True
    def fake_server(request):
        nonlocal fail_facebook
        attempts.append((request.method, request.url.path))
        if request.url.path.endswith("/IG/media"):
            return httpx.Response(200, json={"id": "CONTAINER"})
        if request.url.path.endswith("/CONTAINER") and request.method == "GET":
            return httpx.Response(200, json={"status_code": "FINISHED"})
        if request.url.path.endswith("/IG/media_publish"):
            posted.append("instagram")
            return httpx.Response(200, json={"id": "IG_REMOTE"})
        if request.url.path.endswith("/IG_REMOTE"):
            return httpx.Response(200, json={"permalink": "https://example.test/IG_REMOTE"})
        if request.url.path.endswith("/PAGE/video_reels"):
            if b"upload_phase=start" in request.content:
                if fail_facebook:
                    fail_facebook = False
                    return httpx.Response(429, json={"error": {"message": "rate limit"}})
                return httpx.Response(200, json={"video_id": "FB_REMOTE", "upload_url": "https://rupload.facebook.com/upload"})
            posted.append("facebook")
            return httpx.Response(200, json={"success": True})
        return httpx.Response(200, json={})
    http = httpx.Client(transport=httpx.MockTransport(fake_server))
    make = lambda _, p, s: MetaApi(s, p, http, sleep=lambda _: None)
    runner.run(cm, at(2026, 10, 27, 5), factory=make)
    assert posted == ["instagram"]
    assert Registry(cm).status(value["proposal_id"])["status"] == "PARTIALLY_PUBLISHED"
    # Generic provider errors are uncertain, even 429 after a multi-step API call. The owner verifies
    # the fake server has no FB post before permitting a retry; production never guesses from error text.
    approvals.reconcile(value["proposal_id"], "facebook", "not_published")
    restarted = config.load(ws)
    restarted.default_platforms, restarted.backends = cm.default_platforms, cm.backends
    restarted.accounts, restarted.code_mode = cm.accounts, cm.code_mode
    runner.run(restarted, at(2026, 10, 27, 5, 1), factory=make)
    assert posted == ["instagram", "facebook"]
    state = Registry(restarted).status(value["proposal_id"])
    assert state["status"] == "PUBLISHED"
    assert state["receipts"]["instagram"]["id"] == "IG_REMOTE"
    assert state["receipts"]["facebook"]["id"] == "FB_REMOTE"
    assert runner.run(restarted, at(2026, 10, 27, 5, 2), factory=make) == []
