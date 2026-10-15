#!/usr/bin/env python3
"""Self-contained verification for local patches holographic-0001/0002.

Runs the real plugin auto-extract code path against throwaway temp DBs; never touches
~/.hermes/memory_store.db. Pass: exit 0. Fail: exit 1 with FAIL lines.

Usage: python3 0001-zh-auto-extract-v0.6.1.test.py [plugin_dir]
  plugin_dir defaults to /root/.hermes/plugins/holographic
"""
import importlib.util
import os
import shutil
import sys
import tempfile
from pathlib import Path

PLUGIN = Path(sys.argv[1] if len(sys.argv) > 1 else "/root/.hermes/plugins/holographic")
HERMES_SRC = Path("/usr/local/lib/hermes-agent")


def runtime_python():
    """The plugin runs under hermes' managed python3.14 venv (numpy + hermes deps live there)."""
    roots = sorted(Path("/root/.hermes/installs").glob("*/environments/*/venv/bin/python"))
    return str(roots[-1]) if roots else sys.executable


def load_plugin():
    if not (PLUGIN / "__init__.py").exists():
        sys.exit("plugin dir not found: %s" % PLUGIN)
    if str(HERMES_SRC) not in sys.path:
        sys.path.insert(0, str(HERMES_SRC))
    pkg = "hermes_plugin_holographic"
    spec = importlib.util.spec_from_file_location(
        pkg, PLUGIN / "__init__.py", submodule_search_locations=[str(PLUGIN)])
    mod = importlib.util.module_from_spec(spec)
    sys.modules[pkg] = mod
    spec.loader.exec_module(mod)
    return mod


CASES = [
    ("我更喜欢公众号 tech-dark 主题，浅色主题不好看。", "user_pref", True),
    ("以后都用中文回复我，不要再中英夹杂。", "user_pref", True),
    ("我的默认浏览器是 Chrome。", "user_pref", True),
    ("我不喜欢三线表，表格要全边框。", "user_pref", True),
    ("我们决定用 pandoc 生成 docx。", "project", True),
    ("这个项目统一用飞书文档交付。", "project", True),
    ("统一按 v1.18 的口径写。", "project", True),
    ("we decided to use PostgreSQL for the persistence layer", "project", True),
    ("I prefer pytest 8.3 over unittest.", "user_pref", True),
    ("я предпочитаю тёмную тему", "user_pref", True),
    ("把这份 MD 转成 HTML 发我。", None, False),
    ("这个图为什么是字符图？", None, False),
    ("你好", None, False),
    ("先看下现状，明天再说。", None, False),
    ("帮我把 /root/workspace/aicc-os 的目录列一下。", None, False),
]
SPLIT_CASES = [
    ("先看下现状。我们决定用 vLLM 部署推理服务。剩下的以后再说。",
     [("我们决定用 vLLM 部署推理服务。", "project")]),
    ("I prefer dark mode. We decided to use uv on Linux.",
     [("I prefer dark mode.", "user_pref"), ("We decided to use uv on Linux.", "project")]),
]


def main():
    mod = load_plugin()
    provider_cls = mod.HolographicMemoryProvider
    tmp = Path(tempfile.mkdtemp(prefix="holo-patch-test-"))
    os.environ.setdefault("HERMES_HOME", str(tmp / "home"))
    (tmp / "home").mkdir(exist_ok=True)
    failures = []

    def run_once(text, dbname):
        db = tmp / dbname
        for suffix in ("", "-wal", "-shm"):
            p = Path(str(db) + suffix)
            if p.exists():
                p.unlink()
        prov = provider_cls(config={"db_path": str(db), "hrr_dim": 128, "auto_extract": True})
        prov.initialize(session_id="test")
        prov.on_session_end([{"role": "user", "content": text}])
        rows = [(f["content"], f["category"]) for f in prov._store.list_facts(limit=100)]
        prov.shutdown()
        return rows

    idx = 0
    for text, cat, should in CASES:
        idx += 1
        rows = run_once(text, "one-%d.db" % idx)
        got = rows[0] if rows else None
        ok = bool(got) == should and (not got or got[1] == cat)
        print("  %s %r -> %s" % ("PASS" if ok else "FAIL", text[:36], got))
        if not ok:
            failures.append(text)

    for text, expected in SPLIT_CASES:
        rows = run_once(text, "split.db")
        ok = rows == expected
        print("  %s split %r -> %s" % ("PASS" if ok else "FAIL", text[:40], rows))
        if not ok:
            failures.append(text)

    db = tmp / "off.db"
    prov = provider_cls(config={"db_path": str(db), "hrr_dim": 128, "auto_extract": "false"})
    prov.initialize(session_id="test")
    prov.on_session_end([{"role": "user", "content": c[0]} for c in CASES])
    rows = prov._store.list_facts(limit=100)
    prov.shutdown()
    ok = not rows
    print("  %s auto_extract=false stores nothing" % ("PASS" if ok else "FAIL"))
    if not ok:
        failures.append("auto_extract=false")

    shutil.rmtree(str(tmp), ignore_errors=True)
    if failures:
        print("\n%d FAILURE(S): %s" % (len(failures), failures))
        return 1
    print("\nALL %d CHECKS PASSED" % (len(CASES) + len(SPLIT_CASES) + 1))
    return 0


if __name__ == "__main__":
    if sys.executable != runtime_python() and os.environ.get("HOLO_TEST_REEXEC") != "1":
        os.environ["HOLO_TEST_REEXEC"] = "1"
        py = runtime_python()
        os.execv(py, [py, __file__] + sys.argv[1:])
    sys.exit(main())
