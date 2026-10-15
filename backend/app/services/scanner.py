"""调用现有 runtime 执行扫描与扫描器探测（子进程）。"""
from __future__ import annotations

import asyncio
import re
import subprocess
import tempfile
from pathlib import Path

from app.config import settings

# runtime `list-scanners` 的两类输出行：
#   探测模式（带 --config）：  - builtin-regex  AVAILABLE   builtin (no external binary required)
#   仅名称模式（无 --config）：- builtin-regex
SCANNER_ROW_RE = re.compile(
    r"^\s*-\s+(?P<name>\S+)\s+(?P<state>AVAILABLE|SKIPPED)\s*(?P<rest>.*)$")
SCANNER_NAME_RE = re.compile(r"^\s*-\s+(?P<name>\S+)\s*$")


async def run_scan(project_name: str, source_path: str, out_dir: str,
                   scanners: str = "builtin-regex,semgrep,trivy,gitleaks,osv",
                   progress_cb=None) -> dict:
    runtime = Path(settings.runtime_path)
    main_py = runtime / "main.py"
    cmd = [settings.python_exe, str(main_py), "scan", source_path,
           "--out", out_dir, "--scanners", scanners, "--offline"]

    stages = ["inventory", "scan", "normalize", "context", "taint", "triage", "output"]
    if progress_cb:
        for s in stages:
            await progress_cb({"stage": s, "status": "running"})

    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=str(runtime))
    stdout, stderr = await proc.communicate()
    out_text = stdout.decode("utf-8", errors="replace")
    err_text = stderr.decode("utf-8", errors="replace")

    if progress_cb:
        for s in stages:
            await progress_cb({"stage": s, "status": "done"})

    return {"returncode": proc.returncode, "stdout": out_text[-4000:],
            "stderr": err_text[-2000:]}


async def probe_scanners() -> list[dict]:
    """调用 runtime `list-scanners --config` 探测已注册扫描器的可用性。

    返回 [{name, available, version, location}]；available 为 None 表示未能探测。
    """
    runtime = Path(settings.runtime_path)
    main_py = runtime / "main.py"

    # 生成 UTF-8 无 BOM 的最小配置，runtime 借此进入"探测可用性"分支
    tmp_dir = tempfile.mkdtemp(prefix="sap_probe_")
    cfg = Path(tmp_dir) / "probe.json"
    cfg.write_text("{}", encoding="utf-8")
    try:
        proc = await asyncio.create_subprocess_exec(
            settings.python_exe, str(main_py), "list-scanners", "--config", str(cfg),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=str(runtime))
        stdout, _ = await proc.communicate()
    except OSError as exc:
        raise RuntimeError(f"无法执行 list-scanners: {exc}") from exc
    finally:
        try:
            cfg.unlink(missing_ok=True)
            Path(tmp_dir).rmdir()
        except OSError:
            pass

    rows: list[dict] = []
    for line in stdout.decode("utf-8", errors="replace").splitlines():
        m = SCANNER_ROW_RE.match(line)
        if m:
            rest = m.group("rest").strip()
            version = None
            vm = re.match(r"^v(?P<v>\S+)\s*(?P<loc>.*)$", rest)
            if vm:
                version = vm.group("v")
                rest = vm.group("loc").strip()
            rows.append({"name": m.group("name"),
                         "available": m.group("state") == "AVAILABLE",
                         "version": version, "location": rest})
            continue
        m2 = SCANNER_NAME_RE.match(line)
        if m2:
            rows.append({"name": m2.group("name"), "available": None,
                         "version": None, "location": ""})
    return rows
