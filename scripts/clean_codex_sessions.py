#!/usr/bin/env python3
"""
Clean Codex rollout JSONL sessions for codex-session-review.

V1 goals:
- discover named Codex sessions without modifying Codex data;
- resolve analysis work to provider-native Session IDs;
- batch-clean one or more rollout JSONL files;
- extract reliable cumulative token snapshots where available;
- write analysis-friendly JSON and Markdown derivatives;
- create a lightweight analysis-manifest.json.

The script is deliberately dependency-free and uses only the Python standard
library.

Recommended workflow:

    # 1) Discover candidate sessions by user-facing names.
    python clean_codex_sessions.py discover \
        --scope selected \
        --name "Session Alpha" \
        --name "Session Beta"

    # 2) After real Session IDs are resolved, clean by ID.
    python clean_codex_sessions.py clean \
        --analysis-name "Iteration Review 01" \
        --scope selected \
        --session-id <session-id-1> \
        --session-id <session-id-2> \
        --output-root <analysis-output-directory>

For an Entire Project review, discovery is intentionally candidate-oriented:

    python clean_codex_sessions.py discover \
        --scope project \
        --project "Project Alpha"

The project label is not authoritative identity. Review the candidates, then
clean the final set by Session ID.

Raw Codex files are always opened read-only.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence


SCRIPT_VERSION = "0.1.0"
CLEANED_SCHEMA = "codex-session-review/cleaned-v1"
MANIFEST_SCHEMA = "codex-session-review/analysis-manifest-v1"

DEFAULT_MAX_MESSAGE_CHARS = 50_000
DEFAULT_MAX_TOOL_CHARS = 8_000
DISCOVERY_LIMIT = 100


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_label(value: str | None) -> str:
    if not value:
        return ""
    return "".join(ch.lower() for ch in value if ch.isalnum())


def safe_filename(value: str, fallback: str = "analysis") -> str:
    value = value.strip()
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", value)
    value = re.sub(r"\s+", " ", value).strip(" .")
    return value[:120] or fallback


def truncate_text(text: str | None, limit: int) -> tuple[str, bool, int]:
    if text is None:
        return "", False, 0
    original = len(text)
    if original <= limit:
        return text, False, original
    suffix = f"\n\n[TRUNCATED: original length {original} characters]"
    keep = max(0, limit - len(suffix))
    return text[:keep] + suffix, True, original


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def parse_iso_timestamp(value: str | None) -> dt.datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        text = value
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = dt.datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.astimezone(dt.timezone.utc)
    except ValueError:
        return None


def timestamp_distance_seconds(a: str | None, b: str | None) -> float | None:
    da = parse_iso_timestamp(a)
    db = parse_iso_timestamp(b)
    if da is None or db is None:
        return None
    return abs((da - db).total_seconds())


def int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, float) and value.is_integer() and value >= 0:
        return int(value)
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


# ---------------------------------------------------------------------------
# Codex paths and catalog metadata
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class CatalogEntry:
    # `session_id` is the resolved Codex thread id used by session_index and
    # rollout filenames. The raw session metadata may additionally expose a
    # root `session_id`; both are preserved during cleaning.
    session_id: str
    thread_name: str | None = None
    explicit_name: str | None = None
    sqlite_title: str | None = None
    first_user_message: str | None = None
    preview: str | None = None
    cwd: str | None = None
    rollout_path: str | None = None
    source: str | None = None
    model: str | None = None
    model_provider: str | None = None
    project_id: str | None = None
    project_name: str | None = None
    archived: bool | None = None
    created_at: str | None = None
    updated_at: str | None = None
    index_ordinal: int | None = None

    @property
    def display_name(self) -> str:
        for value in (
            self.thread_name,
            self.explicit_name,
            self.sqlite_title,
            self.first_user_message,
            self.preview,
        ):
            if isinstance(value, str) and value.strip():
                return value.strip()
        return "(unnamed session)"

    @property
    def cwd_basename(self) -> str | None:
        if not self.cwd:
            return None
        try:
            return Path(self.cwd).name or None
        except Exception:
            return None

    def candidate_strings(self) -> list[tuple[str, str]]:
        items: list[tuple[str, str]] = []
        for label, value in (
            ("thread_name", self.thread_name),
            ("explicit_name", self.explicit_name),
            ("sqlite_title", self.sqlite_title),
            ("first_user_message", self.first_user_message),
            ("preview", self.preview),
            ("cwd_basename", self.cwd_basename),
        ):
            if isinstance(value, str) and value.strip():
                items.append((label, value.strip()))
        return items


def resolve_codex_home(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    env = os.environ.get("CODEX_HOME")
    if env:
        return Path(env).expanduser().resolve()
    return (Path.home() / ".codex").resolve()


def resolve_session_roots(codex_home: Path, sessions_dir: str | None) -> list[Path]:
    roots: list[Path] = []
    if sessions_dir:
        roots.append(Path(sessions_dir).expanduser().resolve())
    else:
        roots.append(codex_home / "sessions")

    # Archived sessions are still useful for review. Include the standard
    # archive location if it exists.
    archived = codex_home / "archived_sessions"
    if archived.exists():
        roots.append(archived)

    # Preserve order, remove duplicates.
    unique: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        key = str(root)
        if key not in seen:
            seen.add(key)
            unique.append(root)
    return unique


def iter_jsonl_files(roots: Sequence[Path]) -> Iterator[Path]:
    for root in roots:
        if root.is_file() and root.suffix.lower() == ".jsonl":
            yield root
            continue
        if not root.exists() or not root.is_dir():
            continue
        yield from root.rglob("*.jsonl")


def load_session_index(codex_home: Path) -> dict[str, CatalogEntry]:
    """
    Read session_index.jsonl if present.

    Codex may append multiple naming records for one thread. Later records win
    for thread_name while earlier useful metadata is retained.
    """
    path = codex_home / "session_index.jsonl"
    result: dict[str, CatalogEntry] = {}
    if not path.exists():
        return result

    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            for ordinal, line in enumerate(fh, start=1):
                text = line.strip()
                if not text:
                    continue
                try:
                    obj = json.loads(text)
                except json.JSONDecodeError:
                    continue
                if not isinstance(obj, dict):
                    continue

                sid = (
                    obj.get("id")
                    or obj.get("session_id")
                    or obj.get("thread_id")
                    or obj.get("conversation_id")
                )
                if not isinstance(sid, str) or not sid.strip():
                    continue

                sid = sid.strip()
                entry = result.setdefault(sid, CatalogEntry(session_id=sid))

                name = (
                    obj.get("thread_name")
                    or obj.get("name")
                    or obj.get("title")
                )
                if isinstance(name, str) and name.strip():
                    entry.thread_name = name.strip()
                    entry.index_ordinal = ordinal

                for attr, keys in (
                    ("cwd", ("cwd", "working_directory")),
                    ("rollout_path", ("rollout_path", "path")),
                    ("source", ("source",)),
                    ("model", ("model",)),
                    ("model_provider", ("model_provider",)),
                ):
                    for key in keys:
                        value = obj.get(key)
                        if isinstance(value, str) and value.strip():
                            setattr(entry, attr, value.strip())
                            break

                for attr, keys in (
                    ("created_at", ("created_at", "created_at_ms")),
                    ("updated_at", ("updated_at", "updated_at_ms", "timestamp")),
                ):
                    for key in keys:
                        value = obj.get(key)
                        if value is not None:
                            setattr(entry, attr, str(value))
                            break
    except OSError:
        return result

    return result


def find_state_databases(codex_home: Path) -> list[Path]:
    candidates = [
        codex_home / "state_5.sqlite",
        codex_home / "sqlite" / "state_5.sqlite",
    ]
    return [path for path in candidates if path.exists() and path.is_file()]


def sqlite_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    try:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    except sqlite3.DatabaseError:
        return set()
    return {str(row[1]) for row in rows if len(row) > 1}


def sqlite_time_to_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        # Heuristic only for display metadata; no analytical arithmetic relies
        # on this conversion.
        seconds = float(value)
        if seconds > 10_000_000_000:
            seconds /= 1000.0
        try:
            return (
                dt.datetime.fromtimestamp(seconds, tz=dt.timezone.utc)
                .isoformat()
                .replace("+00:00", "Z")
            )
        except (OverflowError, OSError, ValueError):
            return str(value)
    return str(value)


def load_sqlite_catalog(codex_home: Path) -> dict[str, CatalogEntry]:
    merged: dict[str, CatalogEntry] = {}

    for db_path in find_state_databases(codex_home):
        uri = f"file:{db_path.as_posix()}?mode=ro"
        try:
            conn = sqlite3.connect(uri, uri=True)
        except sqlite3.Error:
            continue

        try:
            cols = sqlite_columns(conn, "threads")
            if not cols or "id" not in cols:
                continue

            wanted = [
                "id",
                "name",
                "title",
                "first_user_message",
                "preview",
                "cwd",
                "rollout_path",
                "source",
                "model",
                "model_provider",
                "project_id",
                "archived",
                "created_at",
                "created_at_ms",
                "updated_at",
                "updated_at_ms",
            ]
            selected = [col for col in wanted if col in cols]
            sql = "SELECT " + ", ".join(f'"{col}"' for col in selected) + " FROM threads"

            conn.row_factory = sqlite3.Row

            # Newer Codex state databases can persist canonical projects.
            # Prefer that assignment for Entire Project discovery when it is
            # available, but keep older Codex installations fully supported.
            project_names: dict[str, str] = {}
            project_cols = sqlite_columns(conn, "projects")
            if {"id", "name"}.issubset(project_cols):
                try:
                    for project_row in conn.execute('SELECT "id", "name" FROM projects'):
                        project_id = project_row["id"]
                        project_name = project_row["name"]
                        if (
                            isinstance(project_id, str)
                            and project_id.strip()
                            and isinstance(project_name, str)
                            and project_name.strip()
                        ):
                            project_names[project_id.strip()] = project_name.strip()
                except sqlite3.Error:
                    project_names = {}

            for row in conn.execute(sql):
                sid = row["id"]
                if not isinstance(sid, str) or not sid.strip():
                    continue
                sid = sid.strip()
                entry = merged.setdefault(sid, CatalogEntry(session_id=sid))

                def assign_text(attr: str, col: str) -> None:
                    if col in row.keys():
                        value = row[col]
                        if isinstance(value, str) and value.strip():
                            setattr(entry, attr, value.strip())

                assign_text("explicit_name", "name")
                assign_text("sqlite_title", "title")
                assign_text("first_user_message", "first_user_message")
                assign_text("preview", "preview")
                assign_text("cwd", "cwd")
                assign_text("rollout_path", "rollout_path")
                assign_text("source", "source")
                assign_text("model", "model")
                assign_text("model_provider", "model_provider")
                assign_text("project_id", "project_id")
                if entry.project_id:
                    entry.project_name = project_names.get(entry.project_id)

                if "archived" in row.keys() and row["archived"] is not None:
                    try:
                        entry.archived = bool(int(row["archived"]))
                    except (TypeError, ValueError):
                        pass

                if "created_at_ms" in row.keys() and row["created_at_ms"] is not None:
                    entry.created_at = sqlite_time_to_text(row["created_at_ms"])
                elif "created_at" in row.keys() and row["created_at"] is not None:
                    entry.created_at = sqlite_time_to_text(row["created_at"])

                if "updated_at_ms" in row.keys() and row["updated_at_ms"] is not None:
                    entry.updated_at = sqlite_time_to_text(row["updated_at_ms"])
                elif "updated_at" in row.keys() and row["updated_at"] is not None:
                    entry.updated_at = sqlite_time_to_text(row["updated_at"])
        except sqlite3.Error:
            pass
        finally:
            conn.close()

    return merged


def merge_catalogs(
    index: dict[str, CatalogEntry],
    sqlite_catalog: dict[str, CatalogEntry],
) -> dict[str, CatalogEntry]:
    result: dict[str, CatalogEntry] = {}

    for sid in sorted(set(index) | set(sqlite_catalog)):
        idx = index.get(sid)
        sql = sqlite_catalog.get(sid)
        entry = CatalogEntry(session_id=sid)

        # session_index is preferred for the latest user-facing rename.
        if idx:
            for field in dataclasses.fields(CatalogEntry):
                if field.name == "session_id":
                    continue
                value = getattr(idx, field.name)
                if value is not None:
                    setattr(entry, field.name, value)

        if sql:
            for field in dataclasses.fields(CatalogEntry):
                if field.name == "session_id":
                    continue
                current = getattr(entry, field.name)
                value = getattr(sql, field.name)
                if current is None and value is not None:
                    setattr(entry, field.name, value)
                elif field.name in {
                    "sqlite_title",
                    "first_user_message",
                    "preview",
                    "archived",
                } and value is not None:
                    setattr(entry, field.name, value)

        result[sid] = entry

    return result


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class Candidate:
    session_id: str
    score: int
    reasons: list[str]
    display_name: str
    cwd_basename: str | None
    project_id: str | None
    project_name: str | None
    source: str | None
    model: str | None
    archived: bool | None
    updated_at: str | None


def match_score(query: str, entry: CatalogEntry, project_mode: bool) -> Candidate | None:
    q = normalize_label(query)
    if not q:
        return None

    best = 0
    reasons: list[str] = []

    # Prefer Codex's canonical project assignment when the current state
    # database exposes one. Name/cwd matching remains a fallback for older
    # installations and sessions without project assignment.
    if project_mode and entry.project_name:
        project_name = normalize_label(entry.project_name)
        if project_name == q:
            best = 120
            reasons = ["project_name"]
        elif project_name.startswith(q) or q.startswith(project_name):
            best = 108
            reasons = ["project_name"]
        elif q in project_name:
            best = 98
            reasons = ["project_name"]

    for label, value in entry.candidate_strings():
        n = normalize_label(value)
        if not n:
            continue

        score = 0
        if n == q:
            score = 100 if label != "cwd_basename" else 95
        elif n.startswith(q) or q.startswith(n):
            score = 88 if label != "cwd_basename" else 84
        elif q in n:
            score = 78 if label != "cwd_basename" else 82
        elif project_mode and n in q and len(n) >= 4:
            score = 70

        if score:
            if score > best:
                best = score
                reasons = [label]
            elif score == best:
                reasons.append(label)

    if best == 0:
        return None

    return Candidate(
        session_id=entry.session_id,
        score=best,
        reasons=sorted(set(reasons)),
        display_name=entry.display_name,
        cwd_basename=entry.cwd_basename,
        project_id=entry.project_id,
        project_name=entry.project_name,
        source=entry.source,
        model=entry.model,
        archived=entry.archived,
        updated_at=entry.updated_at,
    )


def discover_candidates(
    catalog: dict[str, CatalogEntry],
    queries: Sequence[str],
    project_mode: bool,
) -> list[Candidate]:
    by_id: dict[str, Candidate] = {}

    for query in queries:
        for entry in catalog.values():
            candidate = match_score(query, entry, project_mode=project_mode)
            if candidate is None:
                continue
            existing = by_id.get(candidate.session_id)
            if existing is None or candidate.score > existing.score:
                by_id[candidate.session_id] = candidate
            elif candidate.score == existing.score:
                existing.reasons = sorted(set(existing.reasons + candidate.reasons))

    return sorted(
        by_id.values(),
        key=lambda c: (
            -c.score,
            c.updated_at or "",
            c.session_id,
        ),
        reverse=False,
    )[:DISCOVERY_LIMIT]


def candidate_to_dict(candidate: Candidate) -> dict[str, Any]:
    return {
        "session_id": candidate.session_id,
        "score": candidate.score,
        "match_reasons": candidate.reasons,
        "display_name": candidate.display_name,
        "cwd_basename": candidate.cwd_basename,
        "project_id": candidate.project_id,
        "project_name": candidate.project_name,
        "source": candidate.source,
        "model": candidate.model,
        "archived": candidate.archived,
        "updated_at": candidate.updated_at,
    }


def print_candidates(candidates: Sequence[Candidate]) -> None:
    if not candidates:
        print("No matching candidates found.")
        return

    print(f"Candidates: {len(candidates)}")
    for idx, item in enumerate(candidates, start=1):
        name = item.display_name.replace("\n", " ")
        if len(name) > 100:
            name = name[:97] + "..."
        print(
            f"{idx:>3}. score={item.score:<3} "
            f"id={item.session_id} "
            f"name={name!r}"
        )
        extras = []
        if item.cwd_basename:
            extras.append(f"cwd={item.cwd_basename!r}")
        if item.project_name:
            extras.append(f"project={item.project_name!r}")
        if item.project_id:
            extras.append(f"project_id={item.project_id!r}")
        if item.model:
            extras.append(f"model={item.model!r}")
        if item.source:
            extras.append(f"source={item.source!r}")
        if item.archived is not None:
            extras.append(f"archived={item.archived}")
        if item.updated_at:
            extras.append(f"updated={item.updated_at}")
        if item.reasons:
            extras.append("matched=" + ",".join(item.reasons))
        if extras:
            print("     " + " | ".join(extras))


# ---------------------------------------------------------------------------
# Rollout file resolution
# ---------------------------------------------------------------------------


def path_matches_session_id(path: Path, session_id: str) -> bool:
    return session_id.lower() in path.name.lower()


def find_rollout_file(
    session_id: str,
    catalog_entry: CatalogEntry | None,
    session_roots: Sequence[Path],
) -> Path | None:
    if catalog_entry and catalog_entry.rollout_path:
        candidate = Path(catalog_entry.rollout_path).expanduser()
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()

    matches: list[Path] = []
    for path in iter_jsonl_files(session_roots):
        if path_matches_session_id(path, session_id):
            matches.append(path.resolve())

    if not matches:
        return None

    # Prefer canonical rollout naming, then newest file.
    matches.sort(
        key=lambda p: (
            0 if p.name.startswith("rollout-") else 1,
            -(p.stat().st_mtime_ns if p.exists() else 0),
            str(p),
        )
    )
    return matches[0]


# ---------------------------------------------------------------------------
# Rollout parsing and cleaning
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class TokenSnapshot:
    timestamp: str | None
    input_tokens: int | None
    cached_input_tokens: int | None
    cache_write_input_tokens: int | None
    output_tokens: int | None
    reasoning_output_tokens: int | None
    total_tokens: int | None
    codex_rollout_budget_units: int | None
    source: str

    def as_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


class SessionCleaner:
    def __init__(
        self,
        session_id: str,
        source_path: Path,
        catalog_entry: CatalogEntry | None,
        max_message_chars: int,
        max_tool_chars: int,
    ) -> None:
        self.session_id = session_id
        self.source_path = source_path
        self.catalog_entry = catalog_entry
        self.max_message_chars = max_message_chars
        self.max_tool_chars = max_tool_chars

        self.events: list[dict[str, Any]] = []
        self.metadata: dict[str, Any] = {
            # V1 keeps the user-facing term `session_id`, but this resolved ID
            # is specifically Codex's named thread/rollout identity.
            "session_id": session_id,
            "identity_basis": "codex_thread_id",
            "display_name": catalog_entry.display_name if catalog_entry else None,
            "source_file_name": source_path.name,
            "source_file_sha256": None,
        }

        self.records_inspected = 0
        self.records_retained = 0
        self.records_discarded = 0
        self.malformed_records = 0
        self.deferred_records = 0
        self.unknown_record_types: dict[str, int] = {}
        self.reasoning_records_omitted = 0
        self.truncated_records = 0
        self.compaction_events = 0

        self.token_snapshots: list[TokenSnapshot] = []
        self.last_token_usage: TokenSnapshot | None = None
        self.token_regressions = 0
        self.models_seen: list[str] = []

    def clean(self) -> dict[str, Any]:
        raw_hasher = hashlib.sha256()
        try:
            with self.source_path.open("rb") as fh:
                for ordinal, raw in enumerate(fh, start=1):
                    raw_hasher.update(raw)
                    self.records_inspected += 1
                    line_terminated = raw.endswith(b"\n") or raw.endswith(b"\r")
                    text = raw.decode("utf-8", errors="replace").strip()

                    if not text:
                        self.records_discarded += 1
                        continue

                    try:
                        record = json.loads(text)
                    except json.JSONDecodeError:
                        # A non-terminated JSONL record is treated as an
                        # incomplete final write rather than as stable
                        # malformed data. This keeps active rollouts safe.
                        if not line_terminated:
                            self.deferred_records += 1
                        else:
                            self.malformed_records += 1
                        self.records_discarded += 1
                        continue

                    if not isinstance(record, dict):
                        self.records_discarded += 1
                        continue

                    retained_before = len(self.events)
                    handled = self._process_record(record, ordinal)
                    if handled or len(self.events) > retained_before:
                        self.records_retained += 1
                    else:
                        self.records_discarded += 1
        except OSError as exc:
            raise RuntimeError(f"Unable to read source session: {exc}") from exc

        self.metadata["source_file_sha256"] = raw_hasher.hexdigest()
        self._finalize_metadata()

        return {
            "schema": CLEANED_SCHEMA,
            "cleaner_version": SCRIPT_VERSION,
            "generated_at": utc_now_iso(),
            "session": self.metadata,
            "cleaning": {
                "records_inspected": self.records_inspected,
                "records_retained": self.records_retained,
                "records_discarded": self.records_discarded,
                "malformed_records": self.malformed_records,
                "deferred_records": self.deferred_records,
                "reasoning_records_omitted": self.reasoning_records_omitted,
                "truncated_records": self.truncated_records,
                "compaction_events": self.compaction_events,
                "unknown_record_types": self.unknown_record_types,
            },
            "token_usage": self._token_summary(),
            "events": self.events,
        }


    def _process_record(self, record: dict[str, Any], ordinal: int) -> bool:
        timestamp = record.get("timestamp")
        if not isinstance(timestamp, str):
            timestamp = None

        top_type = record.get("type")
        payload = record.get("payload")
        if not isinstance(payload, dict):
            payload = {}

        if top_type == "session_meta":
            return self._handle_session_meta(payload, timestamp)

        if top_type == "turn_context":
            return self._handle_turn_context(payload, timestamp, ordinal)

        if top_type == "response_item":
            return self._handle_response_item(payload, timestamp, ordinal)

        if top_type == "event_msg":
            return self._handle_event_msg(payload, timestamp, ordinal)

        if top_type == "compacted":
            self.compaction_events += 1
            self._append_event(
                {
                    "ordinal": ordinal,
                    "timestamp": timestamp,
                    "kind": "system_event",
                    "event": "compacted",
                }
            )
            return True

        if isinstance(top_type, str):
            self.unknown_record_types[top_type] = (
                self.unknown_record_types.get(top_type, 0) + 1
            )
        return False

    def _handle_session_meta(
        self,
        payload: dict[str, Any],
        timestamp: str | None,
    ) -> bool:
        meta = payload.get("meta")
        if isinstance(meta, dict):
            # Some Codex versions wrap metadata in payload.meta.
            source = meta
        else:
            source = payload

        raw_thread_id = source.get("id")
        if isinstance(raw_thread_id, str) and raw_thread_id.strip():
            self.metadata["thread_id_from_source"] = raw_thread_id.strip()
            if raw_thread_id.strip() != self.session_id:
                self.metadata["identity_warning"] = (
                    "Resolved thread id does not match the rollout session-meta id."
                )

        raw_session_id = source.get("session_id")
        if isinstance(raw_session_id, str) and raw_session_id.strip():
            self.metadata["root_session_id_from_source"] = raw_session_id.strip()

        for out_key, keys in (
            ("originator", ("originator",)),
            ("cli_version", ("cli_version",)),
            ("source", ("source",)),
            ("thread_source", ("thread_source",)),
            ("model_provider", ("model_provider",)),
            ("parent_thread_id", ("parent_thread_id",)),
        ):
            for key in keys:
                value = source.get(key)
                if value is not None:
                    self.metadata[out_key] = value
                    break

        cwd = source.get("cwd")
        if isinstance(cwd, str) and cwd:
            self.metadata["cwd_basename"] = Path(cwd).name or None
            self.metadata["cwd_sha256"] = sha256_text(cwd)

        if timestamp:
            self.metadata.setdefault("session_meta_timestamp", timestamp)

        return True

    def _handle_turn_context(
        self,
        payload: dict[str, Any],
        timestamp: str | None,
        ordinal: int,
    ) -> bool:
        model = payload.get("model")
        if isinstance(model, str) and model:
            if model not in self.models_seen:
                self.models_seen.append(model)

        event = {
            "ordinal": ordinal,
            "timestamp": timestamp,
            "kind": "turn_context",
            "turn_id": payload.get("turn_id"),
            "model": model,
            "reasoning_effort": payload.get("reasoning_effort"),
        }

        cwd = payload.get("cwd")
        if isinstance(cwd, str) and cwd:
            event["cwd_basename"] = Path(cwd).name or None

        self._append_event(event)
        return True

    def _handle_response_item(
        self,
        payload: dict[str, Any],
        timestamp: str | None,
        ordinal: int,
    ) -> bool:
        item_type = payload.get("type")

        if item_type == "message":
            role = payload.get("role")
            if role not in {"user", "assistant", "developer", "system"}:
                role = str(role) if role is not None else "unknown"

            text = self._extract_content_text(payload.get("content"))
            if not text:
                return False

            cleaned, truncated, original_chars = truncate_text(
                text,
                self.max_message_chars,
            )
            if truncated:
                self.truncated_records += 1

            self._append_event(
                {
                    "ordinal": ordinal,
                    "timestamp": timestamp,
                    "kind": "message",
                    "role": role,
                    "text": cleaned,
                    "truncated": truncated,
                    "original_chars": original_chars,
                },
                dedupe_message=True,
            )
            return True

        if item_type in {"reasoning", "reasoning_summary"}:
            # Deliberately omit private/model reasoning text. Reasoning-token
            # counts remain available through token_count metadata when present.
            self.reasoning_records_omitted += 1
            return True

        if item_type in {
            "function_call",
            "custom_tool_call",
            "shell_command",
            "web_search_call",
            "computer_call",
            "apply_patch",
        }:
            name = (
                payload.get("name")
                or payload.get("tool_name")
                or payload.get("type")
            )
            raw_input = (
                payload.get("arguments")
                if payload.get("arguments") is not None
                else payload.get("input")
            )
            if raw_input is None:
                raw_input = payload.get("command")

            text = self._stringify_tool_value(raw_input)
            cleaned, truncated, original_chars = truncate_text(
                text,
                self.max_tool_chars,
            )
            if truncated:
                self.truncated_records += 1

            self._append_event(
                {
                    "ordinal": ordinal,
                    "timestamp": timestamp,
                    "kind": "tool_call",
                    "tool": name,
                    "call_id": payload.get("call_id") or payload.get("id"),
                    "input": cleaned,
                    "truncated": truncated,
                    "original_chars": original_chars,
                }
            )
            return True

        if item_type in {
            "function_call_output",
            "custom_tool_call_output",
            "shell_command_output",
            "computer_call_output",
        }:
            raw_output = (
                payload.get("output")
                if payload.get("output") is not None
                else payload.get("content")
            )
            text = self._stringify_tool_value(raw_output)
            cleaned, truncated, original_chars = truncate_text(
                text,
                self.max_tool_chars,
            )
            if truncated:
                self.truncated_records += 1

            self._append_event(
                {
                    "ordinal": ordinal,
                    "timestamp": timestamp,
                    "kind": "tool_result",
                    "call_id": payload.get("call_id") or payload.get("id"),
                    "output": cleaned,
                    "truncated": truncated,
                    "original_chars": original_chars,
                }
            )
            return True

        if item_type in {
            "compaction",
            "context_compaction",
            "compaction_trigger",
        }:
            self.compaction_events += 1
            self._append_event(
                {
                    "ordinal": ordinal,
                    "timestamp": timestamp,
                    "kind": "system_event",
                    "event": str(item_type),
                }
            )
            return True

        if isinstance(item_type, str):
            key = f"response_item:{item_type}"
            self.unknown_record_types[key] = (
                self.unknown_record_types.get(key, 0) + 1
            )
        return False

    def _handle_event_msg(
        self,
        payload: dict[str, Any],
        timestamp: str | None,
        ordinal: int,
    ) -> bool:
        event_type = payload.get("type")

        if event_type == "token_count":
            return self._handle_token_count(payload, timestamp, ordinal)

        if event_type in {"user_message", "agent_message", "assistant_message"}:
            role = "user" if event_type == "user_message" else "assistant"
            message = payload.get("message")
            if not isinstance(message, str):
                message = self._extract_content_text(payload.get("content"))
            if not message:
                return False

            cleaned, truncated, original_chars = truncate_text(
                message,
                self.max_message_chars,
            )
            if truncated:
                self.truncated_records += 1

            self._append_event(
                {
                    "ordinal": ordinal,
                    "timestamp": timestamp,
                    "kind": "message",
                    "role": role,
                    "text": cleaned,
                    "truncated": truncated,
                    "original_chars": original_chars,
                },
                dedupe_message=True,
            )
            return True

        if event_type in {
            "task_started",
            "task_complete",
            "turn_started",
            "turn_complete",
            "turn_aborted",
            "context_compacted",
            "thread_settings_applied",
            "thread_rolled_back",
        }:
            if event_type == "context_compacted":
                self.compaction_events += 1
            self._append_event(
                {
                    "ordinal": ordinal,
                    "timestamp": timestamp,
                    "kind": "system_event",
                    "event": event_type,
                    "turn_id": payload.get("turn_id"),
                }
            )
            return True

        # Newer history modes may persist completed items inside event messages.
        if event_type in {"item_started", "item_completed"}:
            item = payload.get("item")
            if isinstance(item, dict):
                item_type = item.get("type")
                if item_type in {"command_execution", "tool_call", "mcp_tool_call"}:
                    text = self._stringify_tool_value(item)
                    cleaned, truncated, original_chars = truncate_text(
                        text,
                        self.max_tool_chars,
                    )
                    if truncated:
                        self.truncated_records += 1
                    self._append_event(
                        {
                            "ordinal": ordinal,
                            "timestamp": timestamp,
                            "kind": "tool_activity",
                            "event": event_type,
                            "item_type": item_type,
                            "detail": cleaned,
                            "truncated": truncated,
                            "original_chars": original_chars,
                        }
                    )
                    return True
            # Keep only the event boundary when the item shape is unknown.
            self._append_event(
                {
                    "ordinal": ordinal,
                    "timestamp": timestamp,
                    "kind": "system_event",
                    "event": event_type,
                }
            )
            return True

        if isinstance(event_type, str):
            key = f"event_msg:{event_type}"
            self.unknown_record_types[key] = (
                self.unknown_record_types.get(key, 0) + 1
            )
        return False

    def _handle_token_count(
        self,
        payload: dict[str, Any],
        timestamp: str | None,
        ordinal: int,
    ) -> bool:
        info = payload.get("info")
        if not isinstance(info, dict):
            # Rate-limit-only updates can legitimately have no token info.
            return True

        total = info.get("total_token_usage")
        last = info.get("last_token_usage")

        if isinstance(total, dict):
            snapshot = self._snapshot_from_usage(
                total,
                timestamp,
                source="total_token_usage",
            )
            if self._snapshot_has_any_value(snapshot):
                before_count = len(self.token_snapshots)
                self._record_cumulative_snapshot(snapshot)
                # Keep token timeline only when a new cumulative observation
                # was accepted. Exact rebroadcasts are deliberately ignored.
                if len(self.token_snapshots) > before_count:
                    self._append_event(
                        {
                            "ordinal": ordinal,
                            "timestamp": timestamp,
                            "kind": "token_snapshot",
                            "usage": snapshot.as_dict(),
                        }
                    )

        if isinstance(last, dict):
            last_snapshot = self._snapshot_from_usage(
                last,
                timestamp,
                source="last_token_usage",
            )
            if self._snapshot_has_any_value(last_snapshot):
                self.last_token_usage = last_snapshot

        return True

    def _snapshot_from_usage(
        self,
        usage: dict[str, Any],
        timestamp: str | None,
        source: str,
    ) -> TokenSnapshot:
        return TokenSnapshot(
            timestamp=timestamp,
            input_tokens=int_or_none(usage.get("input_tokens")),
            cached_input_tokens=int_or_none(
                usage.get("cached_input_tokens")
                if usage.get("cached_input_tokens") is not None
                else usage.get("cache_read_tokens")
            ),
            cache_write_input_tokens=int_or_none(
                usage.get("cache_write_input_tokens")
            ),
            output_tokens=int_or_none(usage.get("output_tokens")),
            reasoning_output_tokens=int_or_none(
                usage.get("reasoning_output_tokens")
            ),
            total_tokens=int_or_none(usage.get("total_tokens")),
            codex_rollout_budget_units=int_or_none(
                usage.get("codex_rollout_budget_units")
            ),
            source=source,
        )

    @staticmethod
    def _snapshot_has_any_value(snapshot: TokenSnapshot) -> bool:
        return any(
            value is not None
            for value in (
                snapshot.input_tokens,
                snapshot.cached_input_tokens,
                snapshot.cache_write_input_tokens,
                snapshot.output_tokens,
                snapshot.reasoning_output_tokens,
                snapshot.total_tokens,
                snapshot.codex_rollout_budget_units,
            )
        )

    def _record_cumulative_snapshot(self, snapshot: TokenSnapshot) -> None:
        if self.token_snapshots:
            prev = self.token_snapshots[-1]
            comparable = [
                (prev.input_tokens, snapshot.input_tokens),
                (prev.output_tokens, snapshot.output_tokens),
                (prev.total_tokens, snapshot.total_tokens),
            ]
            for old, new in comparable:
                if old is not None and new is not None and new < old:
                    self.token_regressions += 1
                    break

            # Ignore exact rebroadcasts; Codex can re-emit token_count when
            # only rate-limit state changes.
            if self._same_usage(prev, snapshot):
                return

        self.token_snapshots.append(snapshot)

    @staticmethod
    def _same_usage(a: TokenSnapshot, b: TokenSnapshot) -> bool:
        return (
            a.input_tokens == b.input_tokens
            and a.cached_input_tokens == b.cached_input_tokens
            and a.cache_write_input_tokens == b.cache_write_input_tokens
            and a.output_tokens == b.output_tokens
            and a.reasoning_output_tokens == b.reasoning_output_tokens
            and a.total_tokens == b.total_tokens
            and a.codex_rollout_budget_units == b.codex_rollout_budget_units
        )

    @staticmethod
    def _extract_content_text(content: Any) -> str:
        if isinstance(content, str):
            return content
        if not isinstance(content, list):
            return ""

        chunks: list[str] = []
        for item in content:
            if isinstance(item, str):
                chunks.append(item)
                continue
            if not isinstance(item, dict):
                continue
            for key in ("text", "content", "message"):
                value = item.get(key)
                if isinstance(value, str) and value:
                    chunks.append(value)
                    break
        return "\n".join(chunks).strip()

    @staticmethod
    def _stringify_tool_value(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        try:
            return json.dumps(value, ensure_ascii=False, sort_keys=True)
        except (TypeError, ValueError):
            return repr(value)

    def _append_event(
        self,
        event: dict[str, Any],
        dedupe_message: bool = False,
    ) -> None:
        if dedupe_message and event.get("kind") == "message":
            role = event.get("role")
            text = event.get("text")
            for previous in reversed(self.events[-5:]):
                if previous.get("kind") != "message":
                    continue
                if previous.get("role") != role or previous.get("text") != text:
                    continue
                distance = timestamp_distance_seconds(
                    previous.get("timestamp"),
                    event.get("timestamp"),
                )
                if distance is None or distance <= 2.0:
                    return

        self.events.append(event)

    def _finalize_metadata(self) -> None:
        timestamps = [
            event.get("timestamp")
            for event in self.events
            if isinstance(event.get("timestamp"), str)
        ]
        if timestamps:
            self.metadata["first_event_timestamp"] = timestamps[0]
            self.metadata["last_event_timestamp"] = timestamps[-1]

        self.metadata["models_seen"] = self.models_seen

        if self.catalog_entry:
            self.metadata["catalog"] = {
                "display_name": self.catalog_entry.display_name,
                "source": self.catalog_entry.source,
                "model": self.catalog_entry.model,
                "model_provider": self.catalog_entry.model_provider,
                "archived": self.catalog_entry.archived,
                "created_at": self.catalog_entry.created_at,
                "updated_at": self.catalog_entry.updated_at,
                "cwd_basename": self.catalog_entry.cwd_basename,
            }

    def _token_summary(self) -> dict[str, Any]:
        if self.token_snapshots:
            latest = self.token_snapshots[-1]
            coverage = "complete" if self.token_regressions == 0 else "partial"
            note = (
                "Latest reliable cumulative token snapshot from Codex."
                if self.token_regressions == 0
                else (
                    "Cumulative token counters regressed at least once. "
                    "Latest snapshot is preserved, but scope-level interpretation "
                    "should be treated as partial."
                )
            )
            return {
                "coverage": coverage,
                "observation_count": len(self.token_snapshots),
                "counter_regressions": self.token_regressions,
                "cumulative_snapshot": latest.as_dict(),
                "last_token_usage_snapshot": (
                    self.last_token_usage.as_dict()
                    if self.last_token_usage is not None
                    else None
                ),
                "note": note,
            }

        if self.last_token_usage is not None:
            return {
                "coverage": "partial",
                "observation_count": 0,
                "counter_regressions": 0,
                "cumulative_snapshot": None,
                "last_token_usage_snapshot": self.last_token_usage.as_dict(),
                "note": (
                    "Only last_token_usage evidence was available. "
                    "It is not summed because Codex may rebroadcast the same "
                    "last-usage values on non-usage updates."
                ),
            }

        return {
            "coverage": "unavailable",
            "observation_count": 0,
            "counter_regressions": 0,
            "cumulative_snapshot": None,
            "last_token_usage_snapshot": None,
            "note": "No reliable token-usage record was found.",
        }


# ---------------------------------------------------------------------------
# Output rendering
# ---------------------------------------------------------------------------


def event_to_markdown(event: dict[str, Any]) -> str:
    timestamp = event.get("timestamp") or "timestamp unavailable"
    kind = event.get("kind")

    if kind == "message":
        role = str(event.get("role") or "unknown").upper()
        return f"### {role} · {timestamp}\n\n{event.get('text', '')}\n"

    if kind == "tool_call":
        tool = event.get("tool") or "tool"
        return (
            f"### TOOL CALL · {tool} · {timestamp}\n\n"
            f"```text\n{event.get('input', '')}\n```\n"
        )

    if kind == "tool_result":
        return (
            f"### TOOL RESULT · {timestamp}\n\n"
            f"```text\n{event.get('output', '')}\n```\n"
        )

    if kind == "tool_activity":
        return (
            f"### TOOL ACTIVITY · {timestamp}\n\n"
            f"```text\n{event.get('detail', '')}\n```\n"
        )

    if kind == "token_snapshot":
        usage = event.get("usage") or {}
        return (
            f"### TOKEN SNAPSHOT · {timestamp}\n\n"
            f"```json\n{json.dumps(usage, ensure_ascii=False, indent=2)}\n```\n"
        )

    if kind == "turn_context":
        summary = {
            "turn_id": event.get("turn_id"),
            "model": event.get("model"),
            "reasoning_effort": event.get("reasoning_effort"),
            "cwd_basename": event.get("cwd_basename"),
        }
        return (
            f"### TURN CONTEXT · {timestamp}\n\n"
            f"```json\n{json.dumps(summary, ensure_ascii=False, indent=2)}\n```\n"
        )

    if kind == "system_event":
        return (
            f"### SYSTEM EVENT · {timestamp}\n\n"
            f"`{event.get('event', 'unknown')}`\n"
        )

    return (
        f"### {str(kind or 'event').upper()} · {timestamp}\n\n"
        f"```json\n{json.dumps(event, ensure_ascii=False, indent=2)}\n```\n"
    )


def cleaned_to_markdown(cleaned: dict[str, Any]) -> str:
    session = cleaned["session"]
    token_usage = cleaned["token_usage"]
    cleaning = cleaned["cleaning"]

    lines = [
        "# Cleaned Codex Session",
        "",
        "## Session",
        "",
        f"- Session ID: `{session.get('session_id')}`",
        f"- Display Name: {session.get('display_name') or 'Unavailable'}",
        f"- Source File: `{session.get('source_file_name')}`",
        f"- First Event: {session.get('first_event_timestamp') or 'Unavailable'}",
        f"- Last Event: {session.get('last_event_timestamp') or 'Unavailable'}",
        f"- Models Seen: {', '.join(session.get('models_seen') or []) or 'Unavailable'}",
        "",
        "## Cleaning Summary",
        "",
        f"- Records inspected: {cleaning.get('records_inspected')}",
        f"- Records retained: {cleaning.get('records_retained')}",
        f"- Records discarded: {cleaning.get('records_discarded')}",
        f"- Malformed records: {cleaning.get('malformed_records')}",
        f"- Deferred records: {cleaning.get('deferred_records')}",
        f"- Reasoning records omitted: {cleaning.get('reasoning_records_omitted')}",
        f"- Truncated records: {cleaning.get('truncated_records')}",
        f"- Compaction events: {cleaning.get('compaction_events')}",
        "",
        "## Token Usage",
        "",
        f"- Coverage: **{token_usage.get('coverage')}**",
        f"- Cumulative observations: {token_usage.get('observation_count')}",
        f"- Counter regressions: {token_usage.get('counter_regressions')}",
        "",
        "```json",
        json.dumps(
            token_usage.get("cumulative_snapshot"),
            ensure_ascii=False,
            indent=2,
        ),
        "```",
        "",
        f"> {token_usage.get('note')}",
        "",
        "## Timeline",
        "",
    ]

    for event in cleaned["events"]:
        lines.append(event_to_markdown(event))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_cleaned_outputs(
    output_root: Path,
    cleaned: dict[str, Any],
) -> dict[str, str]:
    cleaned_dir = output_root / "cleaned"
    cleaned_dir.mkdir(parents=True, exist_ok=True)

    sid = str(cleaned["session"]["session_id"])
    json_path = cleaned_dir / f"session-{safe_filename(sid, 'session')}.json"
    md_path = cleaned_dir / f"session-{safe_filename(sid, 'session')}.md"

    json_path.write_text(json_dumps(cleaned) + "\n", encoding="utf-8")
    md_path.write_text(cleaned_to_markdown(cleaned), encoding="utf-8")

    return {
        "json": str(json_path),
        "markdown": str(md_path),
    }


# ---------------------------------------------------------------------------
# Combined token summary and manifest
# ---------------------------------------------------------------------------


TOKEN_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
    "codex_rollout_budget_units",
)


def combined_token_summary(cleaned_sessions: Sequence[dict[str, Any]]) -> dict[str, Any]:
    snapshots: list[dict[str, Any] | None] = [
        session.get("token_usage", {}).get("cumulative_snapshot")
        for session in cleaned_sessions
    ]
    coverages = [
        session.get("token_usage", {}).get("coverage", "unavailable")
        for session in cleaned_sessions
    ]

    known_count = sum(1 for item in snapshots if isinstance(item, dict))
    if known_count == 0:
        scope_coverage = "unavailable"
    elif known_count == len(cleaned_sessions) and all(c == "complete" for c in coverages):
        scope_coverage = "complete"
    else:
        scope_coverage = "partial"

    known_sum: dict[str, int] = {}
    complete_scope_total: dict[str, int | None] = {}

    for field in TOKEN_FIELDS:
        values = [
            int_or_none(snapshot.get(field)) if isinstance(snapshot, dict) else None
            for snapshot in snapshots
        ]
        known_values = [value for value in values if value is not None]
        known_sum[field] = sum(known_values)
        complete_scope_total[field] = (
            sum(known_values)
            if len(known_values) == len(cleaned_sessions)
            else None
        )

    return {
        "coverage": scope_coverage,
        "session_count": len(cleaned_sessions),
        "sessions_with_cumulative_snapshot": known_count,
        "known_session_sum": known_sum,
        "complete_scope_total": complete_scope_total,
        "note": (
            "known_session_sum adds only available cumulative session snapshots. "
            "complete_scope_total is populated for a field only when every "
            "selected session provides that field."
        ),
    }


def build_manifest(
    args: argparse.Namespace,
    cleaned_sessions: Sequence[dict[str, Any]],
    outputs: Sequence[dict[str, str]],
) -> dict[str, Any]:
    requested_labels = list(args.requested_label or [])
    return {
        "schema": MANIFEST_SCHEMA,
        "skill": "codex-session-review",
        "cleaner_version": SCRIPT_VERSION,
        "analysis_name": args.analysis_name,
        "analysis_scope": args.scope,
        "requested_labels": requested_labels,
        "resolved_session_ids": [
            session["session"]["session_id"] for session in cleaned_sessions
        ],
        "session_dates": [
            {
                "session_id": session["session"]["session_id"],
                "first_event_timestamp": session["session"].get(
                    "first_event_timestamp"
                ),
                "last_event_timestamp": session["session"].get(
                    "last_event_timestamp"
                ),
            }
            for session in cleaned_sessions
        ],
        "analysis_created_at": utc_now_iso(),
        "report_length": args.report_length,
        "report_language": args.report_language,
        "previous_report_reference": args.previous_report,
        "special_focus": args.special_focus,
        "combined_token_usage": combined_token_summary(cleaned_sessions),
        "cleaning": [
            {
                "session_id": session["session"]["session_id"],
                **session["cleaning"],
                "token_coverage": session["token_usage"]["coverage"],
                "outputs": output,
            }
            for session, output in zip(cleaned_sessions, outputs)
        ],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def add_location_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--codex-home",
        help=(
            "Codex home directory. Defaults to $CODEX_HOME when set, "
            "otherwise ~/.codex."
        ),
    )
    parser.add_argument(
        "--sessions-dir",
        help=(
            "Custom Codex sessions directory. If omitted, use "
            "<codex-home>/sessions."
        ),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Discover and clean Codex session rollout JSONL files."
    )
    parser.add_argument("--version", action="version", version=SCRIPT_VERSION)

    subparsers = parser.add_subparsers(dest="command", required=True)

    discover = subparsers.add_parser(
        "discover",
        help="Find candidate Codex sessions from user-facing names.",
    )
    add_location_args(discover)
    discover.add_argument(
        "--scope",
        required=True,
        choices=("single", "selected", "project"),
    )
    discover.add_argument(
        "--name",
        action="append",
        default=[],
        help="Session name to match. Repeat for Selected Sessions.",
    )
    discover.add_argument(
        "--project",
        help="Project/session-group label for Entire Project discovery.",
    )
    discover.add_argument(
        "--json",
        action="store_true",
        help="Print JSON instead of the human-readable candidate list.",
    )

    clean = subparsers.add_parser(
        "clean",
        help="Clean one or more already-resolved Codex Session IDs.",
    )
    add_location_args(clean)
    clean.add_argument("--analysis-name", required=True)
    clean.add_argument(
        "--scope",
        required=True,
        choices=("single", "selected", "project"),
    )
    clean.add_argument(
        "--session-id",
        action="append",
        required=True,
        help="Resolved Codex Session ID. Repeat for multiple sessions.",
    )
    clean.add_argument(
        "--requested-label",
        action="append",
        default=[],
        help=(
            "Original user-facing session/project label for the manifest. "
            "Repeat as needed."
        ),
    )
    clean.add_argument("--output-root", required=True)
    clean.add_argument(
        "--report-length",
        choices=("Brief", "Standard", "Deep"),
        default="Standard",
    )
    clean.add_argument(
        "--report-language",
        default="English",
        help="Defaults to English.",
    )
    clean.add_argument("--previous-report")
    clean.add_argument("--special-focus")
    clean.add_argument(
        "--max-message-chars",
        type=int,
        default=DEFAULT_MAX_MESSAGE_CHARS,
    )
    clean.add_argument(
        "--max-tool-chars",
        type=int,
        default=DEFAULT_MAX_TOOL_CHARS,
    )

    return parser


def command_discover(args: argparse.Namespace) -> int:
    if args.scope == "project":
        if not args.project:
            raise SystemExit("--project is required when --scope project is used.")
        queries = [args.project]
        project_mode = True
    else:
        if not args.name:
            raise SystemExit("--name is required for single/selected discovery.")
        if args.scope == "single" and len(args.name) != 1:
            raise SystemExit("--scope single requires exactly one --name.")
        queries = args.name
        project_mode = False

    codex_home = resolve_codex_home(args.codex_home)
    index = load_session_index(codex_home)
    sqlite_catalog = load_sqlite_catalog(codex_home)
    catalog = merge_catalogs(index, sqlite_catalog)

    candidates = discover_candidates(
        catalog,
        queries=queries,
        project_mode=project_mode,
    )

    if args.json:
        print(
            json_dumps(
                {
                    "scope": args.scope,
                    "queries": queries,
                    "candidate_count": len(candidates),
                    "candidates": [candidate_to_dict(c) for c in candidates],
                }
            )
        )
    else:
        print_candidates(candidates)

    return 0 if candidates else 2


def command_clean(args: argparse.Namespace) -> int:
    if args.max_message_chars <= 0 or args.max_tool_chars <= 0:
        raise SystemExit("Text limits must be positive integers.")

    # Preserve user order while removing duplicate Session IDs.
    session_ids = list(dict.fromkeys(sid.strip() for sid in args.session_id if sid.strip()))
    if not session_ids:
        raise SystemExit("No usable --session-id values were supplied.")
    if args.scope == "single" and len(session_ids) != 1:
        raise SystemExit("--scope single requires exactly one unique Session ID.")

    codex_home = resolve_codex_home(args.codex_home)
    session_roots = resolve_session_roots(codex_home, args.sessions_dir)

    catalog = merge_catalogs(
        load_session_index(codex_home),
        load_sqlite_catalog(codex_home),
    )

    output_root = Path(args.output_root).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    cleaned_sessions: list[dict[str, Any]] = []
    outputs: list[dict[str, str]] = []
    unresolved: list[str] = []

    for session_id in session_ids:
        entry = catalog.get(session_id)
        rollout = find_rollout_file(session_id, entry, session_roots)
        if rollout is None:
            unresolved.append(session_id)
            continue

        cleaner = SessionCleaner(
            session_id=session_id,
            source_path=rollout,
            catalog_entry=entry,
            max_message_chars=args.max_message_chars,
            max_tool_chars=args.max_tool_chars,
        )
        cleaned = cleaner.clean()
        output = write_cleaned_outputs(output_root, cleaned)

        cleaned_sessions.append(cleaned)
        outputs.append(output)

    if unresolved:
        print(
            "Unable to locate rollout files for Session IDs:\n- "
            + "\n- ".join(unresolved),
            file=sys.stderr,
        )

    if not cleaned_sessions:
        return 3

    manifest = build_manifest(args, cleaned_sessions, outputs)
    if unresolved:
        manifest["unresolved_session_ids"] = unresolved

    manifest_path = output_root / "analysis-manifest.json"
    manifest_path.write_text(json_dumps(manifest) + "\n", encoding="utf-8")

    print(f"Analysis: {args.analysis_name}")
    print(f"Scope: {args.scope}")
    print(f"Sessions requested: {len(session_ids)}")
    print(f"Sessions cleaned: {len(cleaned_sessions)}")
    print(f"Sessions unresolved: {len(unresolved)}")

    total_records = sum(
        session["cleaning"]["records_inspected"] for session in cleaned_sessions
    )
    retained = sum(
        session["cleaning"]["records_retained"] for session in cleaned_sessions
    )
    discarded = sum(
        session["cleaning"]["records_discarded"] for session in cleaned_sessions
    )
    malformed = sum(
        session["cleaning"]["malformed_records"] for session in cleaned_sessions
    )

    print(f"Records inspected: {total_records}")
    print(f"Records retained: {retained}")
    print(f"Records discarded: {discarded}")
    print(f"Malformed records: {malformed}")
    print(
        "Combined token coverage: "
        f"{manifest['combined_token_usage']['coverage']}"
    )
    print(f"Manifest: {manifest_path}")

    return 0 if not unresolved else 4


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "discover":
        return command_discover(args)
    if args.command == "clean":
        return command_clean(args)

    parser.error("Unknown command.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
