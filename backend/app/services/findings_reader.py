"""读取 .security 产物并扁平化。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _evidence_to_text(evidence) -> str:
    if evidence is None:
        return ""
    if isinstance(evidence, str):
        return evidence[:500]
    if isinstance(evidence, list):
        parts = []
        for item in evidence:
            if isinstance(item, dict):
                snippet = item.get("snippet", "")
                note = item.get("note", "")
                role = item.get("role", "")
                if snippet:
                    parts.append(f"[{role}] {snippet}" if role else snippet)
                elif note:
                    parts.append(note)
            else:
                parts.append(str(item))
        return "\n".join(parts)[:500]
    return str(evidence)[:500]


def list_findings(out_dir: str | Path, severity: str | None = None,
                  status: str | None = None, source: str | None = None,
                  keyword: str | None = None, cwe: str | None = None,
                  page: int = 1, page_size: int = 50) -> dict:
    doc = _load_json(Path(out_dir) / "findings.json")
    findings = doc.get("findings", [])
    flat = []
    for f in findings:
        cls = f.get("classification") or {}
        pri = f.get("priority") or {}
        row = {
            "id": f.get("id", ""),
            "severity": f.get("severity", "info"),
            "type": f.get("type", ""),
            "file": f.get("file", ""),
            "line": f.get("line"),
            "status": f.get("status", ""),
            "source": f.get("source", ""),
            "source_stage": f.get("source_stage", ""),
            "confidence": f.get("confidence"),
            "evidence": _evidence_to_text(f.get("evidence")),
            "cwe": cls.get("cwe"),
            "owasp_id": (cls.get("owasp") or {}).get("id"),
            "cvss_score": (cls.get("cvss") or {}).get("score"),
            "priority_level": pri.get("level"),
            "sla": pri.get("sla"),
        }
        flat.append(row)

    filtered = flat
    if severity:
        filtered = [r for r in filtered if r["severity"] == severity]
    if status:
        filtered = [r for r in filtered if r["status"] == status]
    if source:
        filtered = [r for r in filtered if source in r["source"]]
    if cwe:
        filtered = [r for r in filtered if r["cwe"] and cwe in r["cwe"]]
    if keyword:
        kw = keyword.lower()
        filtered = [r for r in filtered
                    if kw in r["file"].lower() or kw in str(r["evidence"]).lower()
                    or kw in r["id"].lower() or kw in r["type"].lower()]

    total = len(filtered)
    start = (page - 1) * page_size
    items = filtered[start:start + page_size]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def get_finding(out_dir: str | Path, finding_id: str) -> dict | None:
    doc = _load_json(Path(out_dir) / "findings.json")
    for f in doc.get("findings", []):
        if f.get("id") == finding_id:
            return f
    return None


def get_taint(out_dir: str | Path, finding_id: str) -> dict | None:
    doc = _load_json(Path(out_dir) / "taint-findings.json")
    for f in doc.get("findings", []):
        if f.get("id") == finding_id:
            return f
    return None


def dashboard_stats(out_dir: str | Path) -> dict[str, Any]:
    doc = _load_json(Path(out_dir) / "findings.json")
    findings = doc.get("findings", [])
    sev_order = ["critical", "high", "medium", "low", "info"]
    by_sev = {s: 0 for s in sev_order}
    by_status: dict[str, int] = {}
    by_cwe: dict[str, int] = {}
    by_owasp: dict[str, int] = {}
    by_source: dict[str, int] = {}
    triage_by_status: dict[str, int] = {}

    for f in findings:
        sev = f.get("severity", "info")
        by_sev[sev] = by_sev.get(sev, 0) + 1
        st = f.get("status", "unknown")
        by_status[st] = by_status.get(st, 0) + 1
        cls = f.get("classification") or {}
        cwe = cls.get("cwe")
        if cwe:
            by_cwe[cwe] = by_cwe.get(cwe, 0) + 1
        owasp = (cls.get("owasp") or {}).get("id")
        if owasp:
            by_owasp[owasp] = by_owasp.get(owasp, 0) + 1
        src = f.get("source", "unknown")
        by_source[src] = by_source.get(src, 0) + 1

    triage = _load_json(Path(out_dir) / "triage" / "triage.json")
    for t in triage.get("items", []):
        s = t.get("status", "unknown")
        triage_by_status[s] = triage_by_status.get(s, 0) + 1

    gate = _load_json(Path(out_dir) / "security-gate.json")
    review = _load_json(Path(out_dir) / "review.json")
    inventory = _load_json(Path(out_dir) / "inventory.json")

    return {
        "total_findings": len(findings),
        "by_severity": by_sev,
        "by_status": by_status,
        "by_cwe": dict(sorted(by_cwe.items(), key=lambda x: -x[1])[:10]),
        "by_owasp": by_owasp,
        "by_source": by_source,
        "triage_by_status": triage_by_status,
        "gate": {"passed": gate.get("passed"), "exit_code": gate.get("exit_code"),
                 "blocked_reason": gate.get("blocked_reason"),
                 "blocking_count": gate.get("blocking_count", 0)},
        "review_count": len(review.get("items", [])),
        "inventory": {
            "files": len(inventory.get("file_index", []) or {}),
            "languages": list(inventory.get("languages", {}).keys()) if isinstance(inventory.get("languages"), dict) else (inventory.get("languages") or []),
            "entries": len(inventory.get("entries", [])),
        },
    }


def get_report(out_dir: str | Path) -> dict:
    md_path = Path(out_dir) / "report" / "security-report.md"
    json_path = Path(out_dir) / "report" / "security-report.json"
    return {
        "markdown": md_path.read_text(encoding="utf-8") if md_path.is_file() else "",
        "json": _load_json(json_path),
    }


def get_feedback_rules(out_dir: str | Path) -> list[dict]:
    rules_path = Path(out_dir) / "knowledge" / "false-positive-rules.json"
    if not rules_path.is_file():
        return []
    try:
        data = json.loads(rules_path.read_text(encoding="utf-8"))
        return data.get("rules", []) if isinstance(data, dict) else data
    except (OSError, ValueError):
        return []


def get_benchmark(out_dir: str | Path) -> dict:
    report_path = Path(out_dir) / "benchmark-report.json"
    if not report_path.is_file():
        return {}
    return _load_json(report_path)
