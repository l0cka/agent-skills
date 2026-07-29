#!/usr/bin/env python3
"""kg.py — build, query, validate, and maintain a project knowledge graph.

Stdlib-only. The graph lives in a directory (default ./kg) as line-based files
designed to be diffed, grepped, and committed:

  kg/nodes.jsonl    one node per line:
                    {"id":"type:slug","type":"Module","label":"Auth service",
                     "aliases":["auth"],"description":"...","props":{},
                     "sources":["docs/arch.md#auth"]}
  kg/edges.jsonl    one edge per line:
                    {"id":"a:<content-hash>","from":"module:auth","rel":"depends_on",
                     "to":"module:db","source":"docs/arch.md#L12","recorded":"2026-07-29","props":{}}
  kg/schema.json    node_types, edge_types, conditional shapes, executable
                    competency_questions
  kg/manifest.json  ingested sources -> content hash (staleness tracking)
  kg/README.md      how any agent/human can use the graph (written by init)

Run `kg.py --help` or `kg.py <command> --help` for usage.
"""

import argparse
import contextlib
import difflib
import fcntl
import hashlib
import json
import os
import re
import sys
import tempfile
import uuid
from collections import Counter, defaultdict, deque
from datetime import date, datetime, timezone

VERSION = "2.0.0"
GRAPH_FORMAT_VERSION = 2
SCHEMA_VERSION = 2
MAX_SOURCE_BYTES = 2 * 1024 * 1024
SOURCE_RE = re.compile(r"^(?P<path>[^#]+)#(?P<anchor>[^#\s].*)$")
ID_RE = re.compile(r"^[a-z0-9_-]+:[^\s]+$")
EXCLUDED_PARTS = {
    ".git", ".hg", ".svn", "__pycache__", ".pytest_cache", ".mypy_cache",
    "node_modules", "vendor", "dist", "build", ".next", ".cache",
}
SENSITIVE_NAMES = re.compile(
    r"(^|/)(\.env($|\.)|id_(rsa|dsa|ecdsa|ed25519)(\.pub)?$|"
    r".*\.(pem|key|p12|pfx|keystore)$|credentials?(\..*)?$|secrets?(\..*)?$)",
    re.IGNORECASE,
)
RUNTIME_NAMES = re.compile(r"(^|/)(logs?|runtime|state|tmp|cache)(/|$)|\.(log|sqlite|db)$", re.IGNORECASE)
SECRET_PATTERNS = [
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(rb"(?i)\b(?:api[_-]?key|secret|token|password)\s*[:=]\s*[\"']?[A-Za-z0-9_./+=-]{16,}"),
]


@contextlib.contextmanager
def graph_lock(kgdir, exclusive=True):
    """Serialize mutations and keep cooperating readers away from partial commits."""
    os.makedirs(kgdir, exist_ok=True)
    lock_path = os.path.join(kgdir, ".kg.lock")
    with open(lock_path, "a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        try:
            yield
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def atomic_write(path, content):
    """Write and fsync a same-directory temporary file, then atomically replace."""
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{os.path.basename(path)}.", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def atomic_write_json(path, value):
    atomic_write(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def jsonl_text(objs):
    return "".join(json.dumps(obj, ensure_ascii=False) + "\n" for obj in objs)

# ---------------------------------------------------------------- loading

class KG:
    def __init__(self, kgdir):
        self.dir = kgdir
        self.nodes = {}            # id -> node dict
        self.edges = []            # list of edge dicts
        self.out = defaultdict(list)   # id -> [edge]
        self.inc = defaultdict(list)   # id -> [edge]
        self.schema = {"node_types": {}, "edge_types": {}}
        self.manifest = {"sources": {}}
        self.errors = []           # (file, lineno, message)

    @property
    def node_file(self): return os.path.join(self.dir, "nodes.jsonl")
    @property
    def edge_file(self): return os.path.join(self.dir, "edges.jsonl")
    @property
    def schema_file(self): return os.path.join(self.dir, "schema.json")
    @property
    def manifest_file(self): return os.path.join(self.dir, "manifest.json")

    def load(self, lock=True):
        if not os.path.isdir(self.dir):
            sys.exit(f"error: no knowledge graph directory at {self.dir!r} (run: kg.py init)")
        if lock:
            with graph_lock(self.dir, exclusive=False):
                return self.load(lock=False)
        for path, kind in [(self.node_file, "node"), (self.edge_file, "edge")]:
            if not os.path.exists(path):
                continue
            with open(path, encoding="utf-8") as f:
                for i, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError as e:
                        self.errors.append((os.path.basename(path), i, f"bad JSON: {e}"))
                        continue
                    if kind == "node":
                        nid = obj.get("id", f"?line{i}")
                        if nid in self.nodes:
                            self.errors.append((os.path.basename(path), i, f"duplicate node id {nid}"))
                        self.nodes[nid] = obj
                    else:
                        self.edges.append(obj)
        for e in self.edges:
            self.out[e.get("from")].append(e)
            self.inc[e.get("to")].append(e)
        if os.path.exists(self.schema_file):
            try:
                self.schema = json.load(open(self.schema_file, encoding="utf-8"))
            except json.JSONDecodeError as e:
                self.errors.append(("schema.json", 0, f"bad JSON: {e}"))
        if os.path.exists(self.manifest_file):
            try:
                self.manifest = json.load(open(self.manifest_file, encoding="utf-8"))
            except json.JSONDecodeError as e:
                self.errors.append(("manifest.json", 0, f"bad JSON: {e}"))
        return self

    # ------------------------------------------------------------ helpers

    def label(self, nid):
        n = self.nodes.get(nid)
        return n.get("label", nid) if n else nid

    def fmt(self, nid, ids_only=False):
        if ids_only or nid not in self.nodes:
            return nid
        lab = self.nodes[nid].get("label", "")
        return f"{nid} ({lab})" if lab and lab != nid else nid

    def norm(self, s):
        return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()

    def lexical_index(self):
        """normalised label/alias -> set of node ids (the gazetteer)."""
        idx = defaultdict(set)
        for nid, n in self.nodes.items():
            idx[self.norm(n.get("label", ""))].add(nid)
            for a in n.get("aliases", []) or []:
                idx[self.norm(a)].add(nid)
        idx.pop("", None)
        return idx

    def resolve(self, term):
        """Resolve a user-supplied term to a node id: exact id, else unique label/alias match."""
        if term in self.nodes:
            return term
        idx = self.lexical_index()
        hits = idx.get(self.norm(term), set())
        if len(hits) == 1:
            return next(iter(hits))
        if len(hits) > 1:
            sys.exit(f"error: {term!r} is ambiguous: {sorted(hits)}")
        # substring + fuzzy suggestions
        sub = [nid for nid, n in self.nodes.items()
               if self.norm(term) in self.norm(n.get("label", "")) or
                  any(self.norm(term) in self.norm(a) for a in n.get("aliases", []) or [])]
        sugg = sub[:5] or difflib.get_close_matches(term, list(self.nodes), n=5, cutoff=0.5)
        hint = f" did you mean: {sugg}?" if sugg else ""
        sys.exit(f"error: no node matches {term!r}.{hint}")

    def rel_info(self, rel):
        return (self.schema.get("edge_types") or {}).get(rel, {})

    @staticmethod
    def gone_note(e):
        """Marker for tombstoned (historical) edges so they are never mistaken for current facts."""
        g = (e.get("props") or {}).get("gone")
        return f"  [GONE {g}]" if g else ""

    def subtype_chain(self, t):
        chain, seen = [t], {t}
        nt = self.schema.get("node_types") or {}
        while t in nt and nt[t].get("subtype_of") and nt[t]["subtype_of"] not in seen:
            t = nt[t]["subtype_of"]
            chain.append(t); seen.add(t)
        return chain

    def related(self, nid, rel=None, direction="both"):
        """Yield (edge, other_id, outgoing?) honouring symmetric + inverse schema flags."""
        results = []
        if direction in ("out", "both"):
            for e in self.out.get(nid, []):
                if rel is None or e.get("rel") == rel:
                    results.append((e, e.get("to"), True))
        if direction in ("in", "both"):
            for e in self.inc.get(nid, []):
                if rel is None or e.get("rel") == rel:
                    results.append((e, e.get("from"), False))
        if rel:
            info = self.rel_info(rel)
            if info.get("symmetric") and direction in ("out", "both"):
                for e in self.inc.get(nid, []):
                    if e.get("rel") == rel:
                        results.append((e, e.get("from"), True))
            inv = info.get("inverse")
            if inv and direction in ("out", "both"):
                for e in self.inc.get(nid, []):
                    if e.get("rel") == inv:
                        results.append((e, e.get("from"), True))
            # nodes whose declared inverse points here
            for r2, i2 in (self.schema.get("edge_types") or {}).items():
                if i2.get("inverse") == rel and direction in ("out", "both"):
                    for e in self.inc.get(nid, []):
                        if e.get("rel") == r2:
                            results.append((e, e.get("from"), True))
        seen, out = set(), []
        for e, other, o in results:
            k = (id(e), other, o)
            if k not in seen:
                seen.add(k); out.append((e, other, o))
        return out

    def neighbors_undirected(self, nid):
        return {e.get("to") for e in self.out.get(nid, [])} | \
               {e.get("from") for e in self.inc.get(nid, [])}

    def components(self):
        seen, comps = set(), []
        for nid in sorted(self.nodes):
            if nid in seen:
                continue
            comp, q = [], deque([nid]); seen.add(nid)
            while q:
                cur = q.popleft(); comp.append(cur)
                for nb in self.neighbors_undirected(cur):
                    if nb in self.nodes and nb not in seen:
                        seen.add(nb); q.append(nb)
            comps.append(comp)
        return sorted(comps, key=len, reverse=True)


def project_root(kgdir):
    return os.path.dirname(os.path.abspath(kgdir))


def hash_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def split_source(source):
    match = SOURCE_RE.match(str(source or ""))
    if not match:
        return None, None
    return match.group("path"), match.group("anchor")


def normalize_source_path(path, root, manifest=None):
    """Return a canonical source key or raise ValueError."""
    if not path:
        raise ValueError("source path is empty")
    manifest = manifest or {}
    if os.path.isabs(path):
        meta = (manifest.get("sources") or {}).get(path, {})
        if not meta.get("external"):
            raise ValueError("absolute source path is not an approved external manifest source")
        return os.path.normpath(path)
    normalized = os.path.normpath(path).replace(os.sep, "/")
    if normalized in (".", "") or normalized == ".." or normalized.startswith("../"):
        raise ValueError("source must stay within the canonical project root")
    if any(part in EXCLUDED_PARTS for part in normalized.split("/")):
        raise ValueError("source is inside an excluded dependency, cache, VCS, or generated directory")
    candidate = os.path.realpath(os.path.join(root, normalized))
    root_real = os.path.realpath(root)
    if os.path.commonpath([candidate, root_real]) != root_real:
        raise ValueError("source resolves outside the canonical project root")
    return normalized


def evidence_list(node):
    values = list(node.get("sources") or [])
    if node.get("source"):
        values.append(node["source"])
    return list(dict.fromkeys(values))


def source_file_path(root, source_key):
    return source_key if os.path.isabs(source_key) else os.path.join(root, source_key)


def preflight_source(path, source_key, allow_runtime=False):
    lowered = source_key.replace(os.sep, "/")
    if SENSITIVE_NAMES.search(lowered):
        raise ValueError("source path matches a credential, key, environment, or secret-file exclusion")
    if RUNTIME_NAMES.search(lowered) and not allow_runtime:
        raise ValueError("runtime state/log ingestion requires --allow-runtime")
    if not os.path.isfile(path):
        raise ValueError("source is not a regular file")
    size = os.path.getsize(path)
    if size > MAX_SOURCE_BYTES:
        raise ValueError(f"source is oversized ({size} bytes; limit {MAX_SOURCE_BYTES})")
    with open(path, "rb") as f:
        sample = f.read(MAX_SOURCE_BYTES + 1)
    if b"\x00" in sample:
        raise ValueError("binary sources are excluded")
    for pattern in SECRET_PATTERNS:
        if pattern.search(sample):
            raise ValueError("source content matched the secret-pattern preflight")


def assertion_id(frm, rel, to, source):
    identity = "\x1f".join([frm, rel, to, source])
    return "a:" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]


def source_freshness(kg, source):
    """Return (ok, reason) for a path#anchor assertion source."""
    path, anchor = split_source(source)
    if not path or not anchor:
        return False, "malformed source; expected path#anchor"
    root = project_root(kg.dir)
    try:
        key = normalize_source_path(path, root, kg.manifest)
    except ValueError as exc:
        return False, str(exc)
    meta = (kg.manifest.get("sources") or {}).get(key)
    if not meta:
        return False, f"source {key!r} is absent from manifest"
    disk_path = source_file_path(root, key)
    if not os.path.isfile(disk_path):
        return False, f"source {key!r} no longer exists"
    expected = meta.get("sha256") or meta.get("sha1")
    if not expected:
        return False, f"source {key!r} has no content hash"
    actual = hash_file(disk_path) if meta.get("sha256") else hashlib.sha1(open(disk_path, "rb").read()).hexdigest()
    if actual != expected:
        return False, f"source {key!r} is stale"
    return True, key


# ---------------------------------------------------------------- init

STARTER_SCHEMA = {
    "schema_version": SCHEMA_VERSION,
    "project": "",
    "conventions": "IDs are type:slug, minted once, never renamed. Every node needs label; "
                   "aliases collect every alternate surface form. Every node and edge needs "
                   "source evidence (path#anchor). Missing edge = unknown, not false (open world). Store one "
                   "direction only for symmetric/inverse relations.",
    "node_types": {
        "Person":   {"description": "A human involved in the project.", "expected": {"role": "recommended"}},
        "Organization": {"description": "A company, team, firm, or institution."},
        "Component": {"description": "A module, service, subsystem, or other named part of the system.",
                      "expected": {"path": "recommended"}},
        "File":     {"description": "A significant file in the project. The file, not the concept it describes.",
                     "expected": {"path": "required"}},
        "Technology": {"description": "An external tool, library, platform, or system the project uses."},
        "Concept":  {"description": "A named domain concept, term of art, or recurring idea."},
        "Decision": {"description": "A recorded decision. Promote to a node so rationale, actors and dates attach to it.",
                     "expected": {"date": "recommended", "status": "recommended"}},
        "Event":    {"description": "A meeting, milestone, release, or other dated occurrence.",
                     "expected": {"date": "recommended"}},
        "Requirement": {"description": "A stated requirement, constraint, or goal."},
    },
    "edge_types": {
        "depends_on":  {"description": "Subject requires object to function.", "transitive": True,
                        "domain": [], "range": []},
        "part_of":     {"description": "Subject is a part/member of object.", "transitive": True,
                        "inverse": "contains"},
        "uses":        {"description": "Subject makes use of object (looser than depends_on)."},
        "implements":  {"description": "Subject realises object (a concept, requirement, or decision)."},
        "authored_by": {"description": "Subject was created/written by object.", "range": ["Person", "Organization"]},
        "involves":    {"description": "Subject (event/decision) involves object (person/component)."},
        "decided_in":  {"description": "Subject (decision) was made in object (event/file)."},
        "defined_in":  {"description": "Subject is defined/specified in object (file).", "functional": True,
                        "range": ["File"]},
        "described_in": {"description": "Subject is documented in object (file).", "range": ["File"]},
        "mentions":    {"description": "Subject (file/event) mentions object. Weakest link; use sparingly."},
        "supersedes":  {"description": "Subject replaces object (decision/version/doc)."},
        "relates_to":  {"description": "Generic association. Symmetric. Last resort - prefer a specific relation.",
                        "symmetric": True},
    },
    "shapes": [],
    "competency_questions": [],
}

RESEARCH_SCHEMA = {
    **STARTER_SCHEMA,
    "node_types": {
        **STARTER_SCHEMA["node_types"],
        "Experiment": {
            "description": "A bounded research test with a frozen success bar.",
            "expected": {"status": "required", "opened": "recommended"},
        },
        "Gate": {"description": "A measurable criterion used to accept, promote, or reject an experiment."},
        "Lesson": {"description": "A reusable conclusion supported by completed research."},
        "Strategy": {
            "description": "A candidate or live strategic approach.",
            "expected": {"status": "required"},
        },
    },
    "edge_types": {
        **STARTER_SCHEMA["edge_types"],
        "tested_by": {"description": "Subject strategy or hypothesis is tested by object experiment."},
        "evaluated_by": {"description": "Subject experiment or strategy is evaluated by object gate."},
        "concluded_by": {"description": "Subject experiment is concluded by object decision or lesson."},
        "killed_by": {"description": "Subject strategy was terminated by object decision.", "range": ["Decision"]},
        "promoted_by": {"description": "Subject strategy was promoted by object decision.", "range": ["Decision"]},
        "produced": {"description": "Subject experiment or decision produced object lesson.", "range": ["Lesson"]},
    },
    "shapes": [
        {
            "id": "closed-experiment-conclusion",
            "target": {"type": "Experiment", "props.status": ["closed", "completed"]},
            "require_edges": [{"rel": "concluded_by", "min": 1, "source_policy": "canonical-fresh"}],
        },
        {
            "id": "terminal-strategy-decision",
            "target": {"type": "Strategy", "props.status": ["killed", "retired"]},
            "require_edges": [{"rel": "killed_by", "min": 1, "source_policy": "canonical-fresh"}],
        },
    ],
    "competency_questions": [],
}

KG_README = """# Project knowledge graph

This directory is a knowledge graph of the project, maintained for use by AI agents
(and humans). It records the entities that matter (components, people, decisions,
concepts, files...) and the relationships between them, with provenance back to
source files.

## Files

- `nodes.jsonl` - one JSON object per line per entity. Fields: `id` (stable,
  `type:slug`, never renamed), `type`, `label`, `aliases`, `description`, `props`,
  and `sources` (one or more `path#anchor` evidence references).
- `edges.jsonl` - one JSON object per line per source-scoped assertion. Fields: `id`, `from`,
  `rel`, `to` (node ids), `source` (path#anchor of the evidence), `recorded`
  (ISO date), `props`.
- `schema.json` - the vocabulary, conditional shapes, executable competency
  questions, and inference flags (`transitive`, `symmetric`, `inverse`,
  `functional`, `domain`, `range`).
  Read it before adding data; align new facts to the existing vocabulary.
- `manifest.json` - which source files were ingested, with content hashes, so
  staleness is detectable.

## Using the graph (agents: start here)

The query tool is `kg.py` (in this directory or the skill that created it):

    python3 kg.py stats                     # overview
    python3 kg.py find "auth"               # locate entities by label/alias
    python3 kg.py show module:auth          # one entity, all its edges
    python3 kg.py context module:auth       # markdown briefing for an entity
    python3 kg.py neighbors module:auth --depth 2
    python3 kg.py path person:jane module:billing
    python3 kg.py query "?x depends_on module:db" "?x type Component"
    python3 kg.py query "?a depends_on+ ?b"  # + = transitive closure
    python3 kg.py query "?e type Experiment" --not "?e concluded_by ?d"
    python3 kg.py test-cq                    # executable acceptance questions
    python3 kg.py important                 # key entities by centrality
    python3 kg.py validate --strict         # completion gate
    python3 kg.py export --format html      # interactive visualisation

## Maintaining it

Before adding a node, search first (`find`) - if the entity exists under another
name, add an alias instead of a duplicate. Every node and assertion must carry
fresh manifest-backed evidence. Refresh a changed source with `refresh-source`,
then run `validate --strict` and `test-cq`. Missing edge = unknown, not false.
"""

def cmd_init(args):
    kgdir = args.kg
    profile = RESEARCH_SCHEMA if args.profile == "research" else STARTER_SCHEMA
    schema = json.loads(json.dumps(profile))
    schema["project"] = args.project or os.path.basename(os.path.abspath(os.path.join(kgdir, "..")))
    manifest = {
        "graph_format_version": GRAPH_FORMAT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "tool_version": VERSION,
        "hash_algorithm": "sha256",
        "project": schema["project"],
        "created": date.today().isoformat(),
        "updated": date.today().isoformat(),
        "sources": {},
    }
    with graph_lock(kgdir, exclusive=True):
        for fname, content in [
            ("nodes.jsonl", ""), ("edges.jsonl", ""),
            ("schema.json", json.dumps(schema, indent=2) + "\n"),
            ("manifest.json", json.dumps(manifest, indent=2) + "\n"),
            ("README.md", KG_README),
        ]:
            path = os.path.join(kgdir, fname)
            if os.path.exists(path) and os.path.getsize(path) > 0 and not args.force:
                print(f"kept existing {path}")
                continue
            atomic_write(path, content)
            print(f"wrote {path}")
        tool_target = os.path.join(kgdir, "kg.py")
        if os.path.realpath(tool_target) != os.path.realpath(__file__):
            with open(__file__, encoding="utf-8") as f:
                tool_source = f.read()
            if not os.path.exists(tool_target) or args.force:
                atomic_write(tool_target, tool_source)
                os.chmod(tool_target, 0o755)
                print(f"wrote {tool_target}")
    print(f"\nInitialised knowledge graph for project {schema['project']!r} at {kgdir}/")
    print(f"Profile: {args.profile}. Next: define shapes and competency questions, then stage extraction.")

# ---------------------------------------------------------------- writes

def append_jsonl(path, obj):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())

def rewrite_jsonl(path, objs):
    atomic_write(path, jsonl_text(objs))

def cmd_add_node(args):
    with graph_lock(args.kg, exclusive=True):
        kg = KG(args.kg).load(lock=False)
        nid = args.id
        if nid in kg.nodes:
            sys.exit(f"error: node {nid!r} already exists (use show/merge, or pick a new id)")
        if not ID_RE.match(nid):
            sys.exit(f"error: id {nid!r} does not match the 'type:slug' convention")
        nt = kg.schema.get("node_types") or {}
        if args.type not in nt:
            sys.exit(f"error: type {args.type!r} is not declared in schema.json "
                     f"(closed vocabulary: choose one of {', '.join(sorted(nt))} or update the schema)")
        sources = []
        for source in args.source:
            path, anchor = split_source(source)
            if not path or not anchor:
                sys.exit(f"error: malformed node source {source!r}; expected path#anchor")
            try:
                key = normalize_source_path(path, project_root(args.kg), kg.manifest)
            except ValueError as exc:
                sys.exit(f"error: invalid node source {source!r}: {exc}")
            sources.append(f"{key}#{anchor}")
        # Entity-linking check: does a node with this label/alias already exist?
        idx = kg.lexical_index()
        clashes = set()
        for form in [args.label] + (args.aliases.split(",") if args.aliases else []):
            clashes |= idx.get(kg.norm(form), set())
        if clashes and not args.force:
            listing = "; ".join(f"{c} (label={kg.label(c)!r})" for c in sorted(clashes))
            sys.exit(f"error: possible duplicate - existing node(s) share this label/alias: {listing}.\n"
                     f"Add an alias to that node instead, or re-run with --force if genuinely distinct.")
        node = {"id": nid, "type": args.type, "label": args.label, "sources": sources}
        if args.aliases:
            node["aliases"] = [a.strip() for a in args.aliases.split(",") if a.strip()]
        if args.description:
            node["description"] = args.description
        if args.props:
            node["props"] = json.loads(args.props)
        append_jsonl(kg.node_file, node)
        print(f"added {nid}")

def cmd_add_edge(args):
    with graph_lock(args.kg, exclusive=True):
        kg = KG(args.kg).load(lock=False)
        frm, to = kg.resolve(args.frm), kg.resolve(args.to)
        et = kg.schema.get("edge_types") or {}
        if args.rel not in et:
            sugg = difflib.get_close_matches(args.rel, list(et), n=3, cutoff=0.4)
            sys.exit(f"error: relation {args.rel!r} is not in schema.json edge_types "
                     f"(closed vocabulary - align to an existing relation"
                     f"{': ' + str(sugg) if sugg else ''}, or update the schema).")
        path, anchor = split_source(args.source)
        if not path or not anchor:
            sys.exit(f"error: malformed edge source {args.source!r}; expected path#anchor")
        try:
            key = normalize_source_path(path, project_root(args.kg), kg.manifest)
        except ValueError as exc:
            sys.exit(f"error: invalid edge source {args.source!r}: {exc}")
        source = f"{key}#{anchor}"
        dup = [
            e for e in kg.out.get(frm, [])
            if (e.get("rel"), e.get("to"), e.get("source")) == (args.rel, to, source)
        ]
        if dup:
            sys.exit(f"error: assertion already exists: {dup[0].get('id')}")
        edge = {
            "id": assertion_id(frm, args.rel, to, source),
            "from": frm,
            "rel": args.rel,
            "to": to,
            "source": source,
            "recorded": date.today().isoformat(),
        }
        if args.props:
            edge["props"] = json.loads(args.props)
        append_jsonl(kg.edge_file, edge)
        print(f"added {edge['id']}: {frm} -[{args.rel}]-> {to} ({source})")

def cmd_merge(args):
    with graph_lock(args.kg, exclusive=True):
        kg = KG(args.kg).load(lock=False)
        dup, canon = kg.resolve(args.dup), kg.resolve(args.canon)
        if dup == canon:
            sys.exit("error: same node")
        d, c = kg.nodes[dup], kg.nodes[canon]
        conflicts = {}
        for field in ("type", "description"):
            if d.get(field) and c.get(field) and d[field] != c[field]:
                conflicts[field] = {"duplicate": d[field], "canonical": c[field]}
        for key in sorted(set(d.get("props") or {}) & set(c.get("props") or {})):
            if d["props"][key] != c["props"][key]:
                conflicts[f"props.{key}"] = {
                    "duplicate": d["props"][key],
                    "canonical": c["props"][key],
                }
        if conflicts and not args.prefer:
            print(json.dumps({"status": "conflict", "conflicts": conflicts}, indent=2))
            sys.exit("error: merge has conflicting values; resolve manually or pass --prefer canon|dup")
        chosen = d if args.prefer == "dup" else c
        merged = json.loads(json.dumps(chosen))
        merged["id"] = canon
        aliases = list(dict.fromkeys(
            (c.get("aliases") or []) + [d.get("label", "")] + (d.get("aliases") or [])
        ))
        merged["aliases"] = [
            a for a in aliases if a and kg.norm(a) != kg.norm(merged.get("label", ""))
        ]
        merged["sources"] = list(dict.fromkeys(evidence_list(c) + evidence_list(d)))
        props = dict(d.get("props") or {})
        props.update(c.get("props") or {})
        if args.prefer == "dup":
            props.update(d.get("props") or {})
        props.setdefault("merged_from", [])
        if dup not in props["merged_from"]:
            props["merged_from"].append(dup)
        merged["props"] = props
        new_nodes = [merged if nid == canon else n for nid, n in kg.nodes.items() if nid != dup]
        moved = 0
        rewritten = []
        for edge in kg.edges:
            e = dict(edge)
            if e.get("from") == dup:
                e["from"] = canon
                moved += 1
            if e.get("to") == dup:
                e["to"] = canon
                moved += 1
            e["id"] = assertion_id(e.get("from", ""), e.get("rel", ""), e.get("to", ""), e.get("source", ""))
            rewritten.append(e)
        seen, kept = set(), []
        for e in rewritten:
            key = (e.get("from"), e.get("rel"), e.get("to"), e.get("source"))
            if key in seen:
                continue
            seen.add(key)
            kept.append(e)
        dropped = len(rewritten) - len(kept)
        print(f"merge plan: {dup} -> {canon}; {moved} endpoints; {dropped} duplicate assertions")
        if conflicts:
            print(json.dumps({"resolved_by": args.prefer, "conflicts": conflicts}, indent=2))
        if args.dry_run:
            print("dry-run: no files changed")
            return
        rewrite_jsonl(kg.node_file, new_nodes)
        rewrite_jsonl(kg.edge_file, kept)
        print(f"merged {dup} into {canon}; aliases now {merged['aliases']}")

def cmd_mark_ingested(args):
    with graph_lock(args.kg, exclusive=True):
        kg = KG(args.kg).load(lock=False)
        root = project_root(args.kg)
        updates = []
        for src in args.paths:
            raw_path = os.path.abspath(src) if os.path.isabs(src) else os.path.abspath(os.path.join(root, src))
            root_real = os.path.realpath(root)
            external = os.path.commonpath([os.path.realpath(raw_path), root_real]) != root_real
            if external and not args.allow_external:
                sys.exit(f"error: {src!r} is outside project root; external ingestion requires --allow-external")
            if external:
                key = os.path.realpath(raw_path)
            else:
                rel = os.path.relpath(os.path.realpath(raw_path), root_real).replace(os.sep, "/")
                try:
                    key = normalize_source_path(rel, root)
                except ValueError as exc:
                    sys.exit(f"error: cannot ingest {src!r}: {exc}")
            try:
                preflight_source(raw_path, key, allow_runtime=args.allow_runtime)
            except ValueError as exc:
                sys.exit(f"error: cannot ingest {src!r}: {exc}")
            digest = hash_file(raw_path)
            updates.append((key, {
                "sha256": digest,
                "ingested": date.today().isoformat(),
                **({"external": True} if external else {}),
                **({"runtime": True, "max_age_days": args.max_age_days} if args.allow_runtime else {}),
            }))
        for key, meta in updates:
            kg.manifest.setdefault("sources", {})[key] = meta
            print(f"recorded {key} ({meta['sha256'][:12]})")
        kg.manifest.update({
            "graph_format_version": GRAPH_FORMAT_VERSION,
            "schema_version": kg.schema.get("schema_version", SCHEMA_VERSION),
            "tool_version": VERSION,
            "hash_algorithm": "sha256",
            "updated": date.today().isoformat(),
        })
        atomic_write_json(kg.manifest_file, kg.manifest)

def cmd_remove_source(args):
    with graph_lock(args.kg, exclusive=True):
        kg = KG(args.kg).load(lock=False)
        kept_edges = [e for e in kg.edges if split_source(e.get("source"))[0] != args.source]
        removed_edges = len(kg.edges) - len(kept_edges)
        changed_nodes = 0
        new_nodes = []
        for node in kg.nodes.values():
            original = evidence_list(node)
            remaining = [s for s in original if split_source(s)[0] != args.source]
            new_node = dict(node)
            new_node.pop("source", None)
            new_node["sources"] = remaining
            if remaining != original:
                changed_nodes += 1
            new_nodes.append(new_node)
        print(f"remove plan: {removed_edges} edge assertion(s), evidence from {changed_nodes} node(s)")
        if args.dry_run:
            print("dry-run: no files changed")
            return
        rewrite_jsonl(kg.edge_file, kept_edges)
        rewrite_jsonl(kg.node_file, new_nodes)
        kg.manifest.get("sources", {}).pop(args.source, None)
        kg.manifest["updated"] = date.today().isoformat()
        atomic_write_json(kg.manifest_file, kg.manifest)
        print(f"removed assertions recorded from {args.source}; run validate to resolve unsupported nodes")


def load_staged_jsonl(path, kind):
    records = []
    with open(path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: bad JSON: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_no}: {kind} must be a JSON object")
            records.append(value)
    return records


def cmd_refresh_source(args):
    with graph_lock(args.kg, exclusive=True):
        kg = KG(args.kg).load(lock=False)
        root = project_root(args.kg)
        try:
            source = normalize_source_path(args.source, root, kg.manifest)
        except ValueError as exc:
            sys.exit(f"error: invalid source {args.source!r}: {exc}")
        disk_path = source_file_path(root, source)
        try:
            preflight_source(disk_path, source, allow_runtime=args.allow_runtime)
            staged_nodes = load_staged_jsonl(args.nodes, "node")
            staged_edges = load_staged_jsonl(args.edges, "edge")
        except (OSError, ValueError) as exc:
            sys.exit(f"error: staged refresh rejected: {exc}")
        nt = kg.schema.get("node_types") or {}
        et = kg.schema.get("edge_types") or {}
        by_id = {nid: dict(node) for nid, node in kg.nodes.items()}
        conflicts = []
        # Remove the old source-scoped node evidence before applying the stage.
        for nid, node in list(by_id.items()):
            revised = dict(node)
            revised.pop("source", None)
            revised["sources"] = [item for item in evidence_list(node) if split_source(item)[0] != source]
            by_id[nid] = revised
        for node in staged_nodes:
            nid = node.get("id")
            if not nid or not ID_RE.match(nid):
                conflicts.append({"node": nid, "reason": "missing or malformed id"})
                continue
            if node.get("type") not in nt:
                conflicts.append({"node": nid, "reason": f"undeclared type {node.get('type')!r}"})
            staged_sources = evidence_list(node)
            if not staged_sources or any(split_source(item)[0] != source for item in staged_sources):
                conflicts.append({"node": nid, "reason": f"all staged provenance must cite {source}#anchor"})
            existing = by_id.get(nid)
            if existing:
                fields = ("type", "label", "description", "props")
                changed = {
                    field: {"existing": existing.get(field), "staged": node.get(field)}
                    for field in fields
                    if existing.get(field) not in (None, {}, "") and node.get(field) not in (None, {}, "")
                    and existing.get(field) != node.get(field)
                }
                if changed and not args.prefer_staged:
                    conflicts.append({"node": nid, "reason": "attribute conflict", "fields": changed})
                    continue
                merged = dict(existing)
                for field in fields:
                    if node.get(field) not in (None, {}, "") and (args.prefer_staged or not merged.get(field)):
                        merged[field] = node[field]
                merged["sources"] = list(dict.fromkeys(evidence_list(existing) + staged_sources))
                by_id[nid] = merged
            else:
                fresh = dict(node)
                fresh.pop("source", None)
                fresh["sources"] = staged_sources
                by_id[nid] = fresh
        retained_edges = [edge for edge in kg.edges if split_source(edge.get("source"))[0] != source]
        normalized_edges = []
        for edge in staged_edges:
            edge_source = edge.get("source")
            if split_source(edge_source)[0] != source or not split_source(edge_source)[1]:
                conflicts.append({"edge": edge.get("id"), "reason": f"source must be {source}#anchor"})
                continue
            if edge.get("rel") not in et:
                conflicts.append({"edge": edge.get("id"), "reason": f"undeclared relation {edge.get('rel')!r}"})
            if edge.get("from") not in by_id or edge.get("to") not in by_id:
                conflicts.append({"edge": edge.get("id"), "reason": "dangling endpoint"})
                continue
            revised = dict(edge)
            revised["id"] = assertion_id(
                revised["from"], revised["rel"], revised["to"], revised["source"]
            )
            revised.setdefault("recorded", date.today().isoformat())
            normalized_edges.append(revised)
        all_edges = retained_edges + normalized_edges
        referenced = {edge.get("from") for edge in all_edges} | {edge.get("to") for edge in all_edges}
        unsupported = [
            nid for nid, node in by_id.items()
            if not evidence_list(node) and nid in referenced
        ]
        if unsupported:
            conflicts.append({
                "reason": "source removal would leave referenced nodes without provenance",
                "nodes": unsupported,
            })
        by_id = {
            nid: node for nid, node in by_id.items()
            if evidence_list(node) or nid in referenced
        }
        assertion_keys = Counter(
            (edge.get("from"), edge.get("rel"), edge.get("to"), edge.get("source"))
            for edge in all_edges
        )
        duplicates = [key for key, count in assertion_keys.items() if count > 1]
        if duplicates:
            conflicts.append({"reason": "duplicate staged assertions", "assertions": duplicates})
        if conflicts:
            print(json.dumps({"status": "conflict", "conflicts": conflicts}, indent=2))
            sys.exit("error: refresh transaction rejected; no graph files changed")
        new_manifest = json.loads(json.dumps(kg.manifest))
        new_manifest.setdefault("sources", {})[source] = {
            "sha256": hash_file(disk_path),
            "ingested": date.today().isoformat(),
            **({"runtime": True, "max_age_days": args.max_age_days} if args.allow_runtime else {}),
        }
        new_manifest.update({
            "graph_format_version": GRAPH_FORMAT_VERSION,
            "schema_version": kg.schema.get("schema_version", SCHEMA_VERSION),
            "tool_version": VERSION,
            "hash_algorithm": "sha256",
            "updated": date.today().isoformat(),
        })
        print(
            f"refresh plan: {source}: {len(staged_nodes)} staged node(s), "
            f"{len(normalized_edges)} staged assertion(s)"
        )
        if args.dry_run:
            print("dry-run: transaction validated; no files changed")
            return
        # The exclusive advisory lock makes this multi-file replacement atomic to
        # cooperating kg.py readers and writers; each individual file replacement is atomic.
        rewrite_jsonl(kg.node_file, by_id.values())
        rewrite_jsonl(kg.edge_file, all_edges)
        atomic_write_json(kg.manifest_file, new_manifest)
        print("refresh committed")


def cmd_migrate(args):
    with graph_lock(args.kg, exclusive=True):
        kg = KG(args.kg).load(lock=False)
        root = project_root(args.kg)
        nodes = []
        for nid, node in kg.nodes.items():
            revised = dict(node)
            sources = evidence_list(node)
            if not sources:
                sources = list(dict.fromkeys(
                    edge.get("source") for edge in kg.out.get(nid, []) + kg.inc.get(nid, [])
                    if edge.get("source")
                ))
            revised.pop("source", None)
            revised["sources"] = sources
            nodes.append(revised)
        edges = []
        for edge in kg.edges:
            revised = dict(edge)
            if revised.get("source"):
                revised["id"] = assertion_id(
                    revised.get("from", ""), revised.get("rel", ""),
                    revised.get("to", ""), revised["source"],
                )
            edges.append(revised)
        schema = json.loads(json.dumps(kg.schema))
        schema["schema_version"] = SCHEMA_VERSION
        schema.setdefault("shapes", [])
        manifest = json.loads(json.dumps(kg.manifest))
        for source, meta in list((manifest.get("sources") or {}).items()):
            path = source_file_path(root, source)
            if os.path.isfile(path):
                meta.pop("sha1", None)
                meta["sha256"] = hash_file(path)
        manifest.update({
            "graph_format_version": GRAPH_FORMAT_VERSION,
            "schema_version": SCHEMA_VERSION,
            "tool_version": VERSION,
            "hash_algorithm": "sha256",
            "updated": date.today().isoformat(),
        })
        print(
            f"migration plan: format -> {GRAPH_FORMAT_VERSION}, schema -> {SCHEMA_VERSION}, "
            f"{len(nodes)} node(s), {len(edges)} assertion(s)"
        )
        if args.dry_run:
            print("dry-run: no files changed")
            return
        rewrite_jsonl(kg.node_file, nodes)
        rewrite_jsonl(kg.edge_file, edges)
        atomic_write_json(kg.schema_file, schema)
        atomic_write_json(kg.manifest_file, manifest)
        print("migration committed; run validate --strict")

# ---------------------------------------------------------------- reads

def cmd_stats(args):
    kg = KG(args.kg).load()
    comps = kg.components()
    orphans = [c[0] for c in comps if len(c) == 1]
    print(f"project:  {kg.manifest.get('project', '?')}   (updated {kg.manifest.get('updated', '?')})")
    print(f"nodes:    {len(kg.nodes)}")
    print(f"edges:    {len(kg.edges)}")
    print(f"sources:  {len(kg.manifest.get('sources', {}))} ingested")
    print(f"components: {len(comps)} ({len(orphans)} orphan nodes)" if comps else "components: 0")
    tc = Counter(n.get("type", "?") for n in kg.nodes.values())
    print("\nnode types:")
    for t, c in tc.most_common():
        print(f"  {c:4d}  {t}")
    rc = Counter(e.get("rel", "?") for e in kg.edges)
    print("\nrelations:")
    for r, c in rc.most_common():
        print(f"  {c:4d}  {r}")
    undeclared_t = sorted(set(tc) - set(kg.schema.get("node_types") or {}))
    undeclared_r = sorted(set(rc) - set(kg.schema.get("edge_types") or {}))
    if undeclared_t: print(f"\nundeclared types (add to schema.json): {undeclared_t}")
    if undeclared_r: print(f"undeclared relations (align or declare): {undeclared_r}")

def cmd_find(args):
    kg = KG(args.kg).load()
    q = kg.norm(args.text)
    rows = []
    for nid, n in sorted(kg.nodes.items()):
        if args.type and n.get("type") != args.type:
            continue
        hay = [n.get("label", ""), nid] + (n.get("aliases") or [])
        if not args.deep:
            hit = any(q in kg.norm(h) for h in hay)
        else:
            hay += [n.get("description", ""), json.dumps(n.get("props", {}))]
            hit = any(q in kg.norm(h) for h in hay)
        if hit:
            deg = len(kg.out.get(nid, [])) + len(kg.inc.get(nid, []))
            rows.append((deg, nid, n))
    if not rows:
        print(f"no nodes match {args.text!r}" + (f" (type {args.type})" if args.type else "") +
              ("" if args.deep else " - try --deep to search descriptions/props"))
        return
    for deg, nid, n in sorted(rows, reverse=True)[: args.limit]:
        alias = f"  aka {n.get('aliases')}" if n.get("aliases") else ""
        print(f"{nid}  [{n.get('type', '?')}]  {n.get('label', '')!r}  ({deg} edges){alias}")

def cmd_show(args):
    kg = KG(args.kg).load()
    nid = kg.resolve(args.id)
    n = kg.nodes[nid]
    print(f"id:      {nid}")
    print(f"type:    {n.get('type', '?')}")
    print(f"label:   {n.get('label', '')}")
    if n.get("aliases"): print(f"aliases: {n['aliases']}")
    if n.get("description"): print(f"desc:    {n['description']}")
    for k, v in (n.get("props") or {}).items():
        print(f"  .{k} = {v}")
    outs = kg.out.get(nid, []); ins = kg.inc.get(nid, [])
    if outs:
        print(f"\noutgoing ({len(outs)}):")
        for e in sorted(outs, key=lambda e: (e.get("rel", ""), e.get("to", ""))):
            src = f"   [{e['source']}]" if e.get("source") else ""
            print(f"  -[{e.get('rel')}]-> {kg.fmt(e.get('to'))}{src}{kg.gone_note(e)}")
    if ins:
        print(f"\nincoming ({len(ins)}):")
        for e in sorted(ins, key=lambda e: (e.get("rel", ""), e.get("from", ""))):
            src = f"   [{e['source']}]" if e.get("source") else ""
            print(f"  <-[{e.get('rel')}]- {kg.fmt(e.get('from'))}{src}{kg.gone_note(e)}")
    if not outs and not ins:
        print("\n(no edges - orphan node)")

def cmd_neighbors(args):
    kg = KG(args.kg).load()
    start = kg.resolve(args.id)
    seen = {start: 0}
    q = deque([(start, 0)])
    hops = defaultdict(list)
    while q:
        cur, d = q.popleft()
        if d >= args.depth:
            continue
        for e, other, outgoing in kg.related(cur, args.rel, args.direction):
            if other not in kg.nodes:
                continue
            arrow = f"-[{e.get('rel')}]->" if outgoing else f"<-[{e.get('rel')}]-"
            hops[d + 1].append(f"{kg.fmt(cur)} {arrow} {kg.fmt(other)}")
            if other not in seen:
                seen[other] = d + 1
                q.append((other, d + 1))
    if not hops:
        print(f"{kg.fmt(start)} has no matching neighbors")
        return
    for d in sorted(hops):
        print(f"depth {d}:")
        for line in sorted(set(hops[d])):
            print(f"  {line}")

def cmd_path(args):
    kg = KG(args.kg).load()
    a, b = kg.resolve(args.a), kg.resolve(args.b)
    rels = set(args.rel.split(",")) if args.rel else None
    prev = {a: None}
    q = deque([a])
    while q:
        cur = q.popleft()
        if cur == b:
            break
        for e in kg.out.get(cur, []) + (kg.inc.get(cur, []) if not args.directed else []):
            if rels and e.get("rel") not in rels:
                continue
            outgoing = e.get("from") == cur
            other = e.get("to") if outgoing else e.get("from")
            if other in kg.nodes and other not in prev:
                prev[other] = (cur, e, outgoing)
                q.append(other)
    if b not in prev:
        sys.exit(f"no path found between {kg.fmt(a)} and {kg.fmt(b)}" +
                 (f" via {sorted(rels)}" if rels else "") +
                 ("" if args.directed else " (searched both directions)"))
    steps, cur = [], b
    while prev[cur]:
        p, e, outgoing = prev[cur]
        arrow = f"-[{e.get('rel')}]->" if outgoing else f"<-[{e.get('rel')}]-"
        steps.append((p, arrow, cur))
        cur = p
    steps.reverse()
    print(kg.fmt(steps[0][0]) if steps else kg.fmt(a))
    for p, arrow, nxt in steps:
        print(f"  {arrow} {kg.fmt(nxt)}")

# ------------------------------------------------------------ query (patterns)

def parse_pattern(pat):
    toks = pat.split()
    if len(toks) != 3:
        sys.exit(f"error: pattern must be 'subject relation object', got {pat!r}")
    return toks

def term_kind(t):
    if t.startswith("?"): return "var"
    if t in ("*", "_"): return "any"
    return "const"

def closure_pairs(kg, rel):
    pairs = set()
    for start in kg.nodes:
        seen, q = set(), deque([start])
        while q:
            cur = q.popleft()
            for _edge, other, outgoing in kg.related(cur, rel, "out"):
                if outgoing and other not in seen and other in kg.nodes:
                    seen.add(other)
                    q.append(other)
        pairs.update((start, target) for target in seen)
    return sorted(pairs)


def edge_tuples(kg, rel):
    """Return display-deduplicated pairs for graph and virtual property relations."""
    if rel == "type":
        return [(nid, n.get("type", "")) for nid, n in kg.nodes.items()]
    if rel.startswith("prop."):
        prop = rel[5:]
        values = []
        for nid, node in kg.nodes.items():
            if prop not in (node.get("props") or {}):
                continue
            value = node["props"][prop]
            if isinstance(value, list):
                values.extend((nid, str(item)) for item in value)
            else:
                values.append((nid, str(value)))
        return values
    pairs = set()
    for nid in kg.nodes:
        for _edge, other, outgoing in kg.related(nid, rel, "out"):
            if outgoing:
                pairs.add((nid, other))
    return sorted(pairs)


def resolve_query_constant(kg, term, rel, object_side):
    if (rel == "type" or rel.startswith("prop.")) and object_side:
        return term
    if term in kg.nodes:
        return term
    hits = kg.lexical_index().get(kg.norm(term), set())
    return next(iter(hits)) if len(hits) == 1 else term


def evaluate_patterns(kg, patterns, seeds=None):
    results = list(seeds or [dict()])
    for s, raw_rel, o in patterns:
        closure = raw_rel.endswith("+")
        rel = raw_rel[:-1] if closure else raw_rel
        if term_kind(rel) == "var":
            raise ValueError("variable relations are not supported")
        if rel == "*":
            tuples = sorted({(e.get("from"), e.get("to")) for e in kg.edges})
        elif closure:
            tuples = closure_pairs(kg, rel)
        else:
            tuples = edge_tuples(kg, rel)
        new = []
        for binding in results:
            for left, right in tuples:
                candidate = dict(binding)
                valid = True
                for term, value, object_side in ((s, left, False), (o, right, True)):
                    kind = term_kind(term)
                    if kind == "any":
                        continue
                    if kind == "var":
                        if term in candidate and candidate[term] != value:
                            valid = False
                            break
                        candidate[term] = value
                    elif resolve_query_constant(kg, term, rel, object_side) != value:
                        valid = False
                        break
                if valid:
                    new.append(candidate)
        seen = set()
        results = []
        for binding in new:
            key = tuple(sorted(binding.items()))
            if key not in seen:
                seen.add(key)
                results.append(binding)
    return results


def filter_binding(kg, binding, expression):
    match = re.match(r"^(\?\w+)\.(type|id|label|props\.[\w.-]+)\s*(=|!=)\s*(.+)$", expression)
    if not match:
        raise ValueError("filter must be '?var.type=value' or '?var.props.key=value1,value2'")
    var, field, operator, raw_values = match.groups()
    nid = binding.get(var)
    if nid not in kg.nodes:
        return False
    node = kg.nodes[nid]
    if field == "type":
        actual = node.get("type")
    elif field == "id":
        actual = nid
    elif field == "label":
        actual = node.get("label")
    else:
        actual = (node.get("props") or {}).get(field[6:])
    allowed = [value.strip() for value in raw_values.split(",")]
    matched = str(actual) in allowed
    return not matched if operator == "!=" else matched


def evaluate_query(kg, required, optional=None, negative=None, filters=None):
    results = evaluate_patterns(kg, required)
    for pattern in optional or []:
        expanded = []
        for binding in results:
            matches = evaluate_patterns(kg, [pattern], [binding])
            expanded.extend(matches or [binding])
        results = expanded
    if negative:
        results = [
            binding for binding in results
            if not evaluate_patterns(kg, negative, [binding])
        ]
    for expression in filters or []:
        results = [binding for binding in results if filter_binding(kg, binding, expression)]
    return results


def cmd_query(args):
    kg = KG(args.kg).load()
    patterns = [parse_pattern(pattern) for pattern in args.patterns]
    optional = [parse_pattern(pattern) for pattern in args.optional]
    negative = [parse_pattern(pattern) for pattern in args.negative]
    try:
        results = evaluate_query(kg, patterns, optional, negative, args.filters)
    except ValueError as exc:
        sys.exit(f"error: {exc}")
    vars_ = [v for p in patterns for v in p if v.startswith("?")]
    vars_ += [v for p in optional for v in p if v.startswith("?")]
    vars_ = list(dict.fromkeys(vars_))
    if not results:
        print("no matches")
        return
    if not vars_:
        print(f"pattern holds ({len(results)} match{'es' if len(results) != 1 else ''})")
        return
    if args.count_by:
        if args.count_by not in vars_:
            sys.exit(f"error: --count-by variable {args.count_by!r} is not bound by the query")
        counts = Counter(binding.get(args.count_by) for binding in results)
        print(f"{args.count_by}\tcount")
        for value, count in sorted(counts.items(), key=lambda item: (-item[1], str(item[0]))):
            print(f"{kg.fmt(value, args.ids_only)}\t{count}")
        return
    print("\t".join(vars_))
    shown = set()
    for b in results:
        row = "\t".join(kg.fmt(b.get(v, "?"), args.ids_only) for v in vars_)
        if row not in shown:
            shown.add(row); print(row)

# ------------------------------------------------------------ context brief

def cmd_context(args):
    kg = KG(args.kg).load()
    nid = kg.resolve(args.id)
    n = kg.nodes[nid]
    lines = [f"## {n.get('label', nid)}  `{nid}`", ""]
    meta = f"**Type:** {n.get('type', '?')}"
    if n.get("aliases"): meta += f" · **aka:** {', '.join(n['aliases'])}"
    lines.append(meta)
    if n.get("description"): lines.append(f"\n{n['description']}")
    props = n.get("props") or {}
    if props:
        lines.append("")
        for k, v in props.items():
            lines.append(f"- {k}: {v}")
    outs, ins = kg.out.get(nid, []), kg.inc.get(nid, [])
    if outs:
        lines.append("\n### Outgoing")
        by_rel = defaultdict(list)
        for e in outs: by_rel[e.get("rel")].append(e)
        for rel in sorted(by_rel):
            tgts = ", ".join(sorted(kg.fmt(e.get("to")) + kg.gone_note(e) for e in by_rel[rel]))
            lines.append(f"- **{rel}** → {tgts}")
    if ins:
        lines.append("\n### Incoming")
        by_rel = defaultdict(list)
        for e in ins: by_rel[e.get("rel")].append(e)
        for rel in sorted(by_rel):
            srcs = ", ".join(sorted(kg.fmt(e.get("from")) + kg.gone_note(e) for e in by_rel[rel]))
            lines.append(f"- **{rel}** ← {srcs}")
    if args.depth >= 2:
        ring = set()
        for other in kg.neighbors_undirected(nid):
            ring |= kg.neighbors_undirected(other)
        ring -= (kg.neighbors_undirected(nid) | {nid})
        ring = [r for r in ring if r in kg.nodes]
        if ring:
            deg = lambda x: len(kg.out.get(x, [])) + len(kg.inc.get(x, []))
            top = sorted(ring, key=deg, reverse=True)[:10]
            lines.append("\n### Two hops away (best-connected)")
            lines.append(", ".join(kg.fmt(t) for t in top))
    sources = sorted({e.get("source", "").split("#")[0] for e in outs + ins if e.get("source")})
    if sources:
        lines.append("\n### Evidence sources")
        for s in sources:
            lines.append(f"- {s}")
    print("\n".join(lines))

# ------------------------------------------------------------ analytics

def cmd_important(args):
    kg = KG(args.kg).load()
    if not kg.nodes:
        sys.exit("empty graph")
    deg = {nid: len(kg.out.get(nid, [])) + len(kg.inc.get(nid, [])) for nid in kg.nodes}
    pr = {nid: 1.0 / len(kg.nodes) for nid in kg.nodes}
    for _ in range(25):
        nxt = {}
        for nid in sorted(kg.nodes):
            s = 0.0
            for e in kg.inc.get(nid, []):
                src = e.get("from")
                if src in pr:
                    outdeg = len(kg.out.get(src, [])) or 1
                    s += pr[src] / outdeg
            nxt[nid] = 0.15 / len(kg.nodes) + 0.85 * s
        pr = nxt
    print(f"{'degree':>6}  {'pagerank':>8}  node")
    ranked = sorted(kg.nodes, key=lambda x: (pr[x], deg[x]), reverse=True)
    for nid in ranked[: args.top]:
        print(f"{deg[nid]:>6}  {pr[nid]:>8.4f}  {kg.fmt(nid)}  [{kg.nodes[nid].get('type', '?')}]")

def cmd_communities(args):
    kg = KG(args.kg).load()
    label = {nid: nid for nid in kg.nodes}
    for _ in range(30):
        changed = False
        for nid in sorted(kg.nodes):
            nbs = [x for x in kg.neighbors_undirected(nid) if x in label]
            if not nbs:
                continue
            counts = Counter(label[x] for x in nbs)
            best = max(counts.items(), key=lambda kv: (kv[1], kv[0]))[0]
            if counts[best] > counts.get(label[nid], 0):
                label[nid] = best; changed = True
        if not changed:
            break
    groups = defaultdict(list)
    for nid, lab in label.items():
        groups[lab].append(nid)
    comms = sorted(groups.values(), key=len, reverse=True)
    for i, c in enumerate(c for c in comms if len(c) >= args.min_size):
        deg = lambda x: len(kg.out.get(x, [])) + len(kg.inc.get(x, []))
        members = sorted(c, key=deg, reverse=True)
        print(f"community {i + 1} ({len(c)} nodes): " +
              ", ".join(kg.fmt(m) for m in members[:8]) + (" ..." if len(c) > 8 else ""))

def cmd_orphans(args):
    kg = KG(args.kg).load()
    comps = kg.components()
    if not comps:
        sys.exit("empty graph")
    main = comps[0]
    print(f"main component: {len(main)} of {len(kg.nodes)} nodes")
    for c in comps[1:]:
        if len(c) == 1:
            print(f"orphan: {kg.fmt(c[0])}")
        else:
            print(f"island ({len(c)}): " + ", ".join(kg.fmt(x) for x in c[:6]) + (" ..." if len(c) > 6 else ""))
    if len(comps) == 1:
        print("no orphans or islands - fully connected")

def cmd_similar(args):
    kg = KG(args.kg).load()
    nid = kg.resolve(args.id)
    mine = kg.neighbors_undirected(nid)
    if not mine:
        sys.exit(f"{kg.fmt(nid)} has no neighbors to compare")
    scored = []
    for other in kg.nodes:
        if other == nid:
            continue
        theirs = kg.neighbors_undirected(other)
        inter = mine & theirs
        if not inter:
            continue
        j = len(inter) / len(mine | theirs)
        scored.append((j, other, inter))
    if not scored:
        print("no nodes share neighbors with this one")
        return
    print("shared-neighbor similarity (candidates for missing links or duplicates):")
    for j, other, inter in sorted(scored, reverse=True)[: args.top]:
        linked = other in mine
        flag = "" if linked else "   <- no direct edge (candidate)"
        print(f"  {j:.2f}  {kg.fmt(other)}  shares {len(inter)}: "
              f"{', '.join(kg.fmt(x) for x in sorted(inter)[:4])}{flag}")

def cmd_dupes(args):
    kg = KG(args.kg).load()
    idx = defaultdict(list)   # blocking: (type, normalised label/alias) exact collisions
    for nid, n in kg.nodes.items():
        for form in [n.get("label", "")] + (n.get("aliases") or []):
            key = kg.norm(form)
            if key:
                idx[key].append(nid)
    reported = set()
    found = False
    for key, ids in sorted(idx.items()):
        uniq = sorted(set(ids))
        if len(uniq) > 1:
            pair = tuple(uniq)
            if pair not in reported:
                reported.add(pair); found = True
                print(f"same surface form {key!r}: " + ", ".join(kg.fmt(x) for x in uniq))
    # fuzzy pass within same type (blocking by type + first letter)
    by_block = defaultdict(list)
    for nid, n in kg.nodes.items():
        lab = kg.norm(n.get("label", ""))
        if lab:
            by_block[(n.get("type"), lab[:1])].append((nid, lab))
    for (_, _), members in sorted(by_block.items()):
        for i in range(len(members)):
            for jdx in range(i + 1, len(members)):
                a, la = members[i]; b, lb = members[jdx]
                if (a, b) in reported or (b, a) in reported:
                    continue
                ratio = difflib.SequenceMatcher(None, la, lb).ratio()
                shared = kg.neighbors_undirected(a) & kg.neighbors_undirected(b)
                if ratio >= 0.82 or (ratio >= 0.6 and len(shared) >= 2):
                    reported.add((a, b)); found = True
                    why = f"labels {ratio:.0%} similar" + (f", {len(shared)} shared neighbors" if shared else "")
                    print(f"candidate: {kg.fmt(a)} vs {kg.fmt(b)}  ({why})")
    if not found:
        print("no duplicate candidates found")
    else:
        print("\nverify against sources, then consolidate with: kg.py merge <dup-id> <canonical-id>")

# ------------------------------------------------------------ validate

def nested_value(node, key):
    if key == "type":
        return node.get("type")
    if key == "id":
        return node.get("id")
    if key.startswith("props."):
        return (node.get("props") or {}).get(key[6:])
    return node.get(key)


def node_matches_target(node, target):
    for key, expected in (target or {}).items():
        actual = nested_value(node, key)
        allowed = expected if isinstance(expected, list) else [expected]
        if actual not in allowed:
            return False
    return True


def parse_iso_datetime(value):
    text = str(value or "")
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def shape_errors(kg, fresh_sources):
    errors = []
    for index, shape in enumerate(kg.schema.get("shapes") or []):
        sid = shape.get("id") or f"shape[{index}]"
        targets = [node for node in kg.nodes.values() if node_matches_target(node, shape.get("target") or {})]
        for node in targets:
            nid = node.get("id")
            for prop in shape.get("require_props") or []:
                key = prop if isinstance(prop, str) else prop.get("path")
                if nested_value(node, key) in (None, "", []):
                    errors.append(f"shape {sid}: {nid} missing required {key}")
            for requirement in shape.get("require_edges") or []:
                rel = requirement.get("rel")
                direction = requirement.get("direction", "out")
                candidates = []
                if direction in ("out", "both"):
                    candidates.extend(e for e in kg.out.get(nid, []) if e.get("rel") == rel)
                if direction in ("in", "both"):
                    candidates.extend(e for e in kg.inc.get(nid, []) if e.get("rel") == rel)
                policy = requirement.get("source_policy")
                if policy == "canonical-fresh":
                    candidates = [
                        edge for edge in candidates
                        if split_source(edge.get("source"))[0] in fresh_sources
                    ]
                minimum = int(requirement.get("min", 0))
                maximum = requirement.get("max")
                if len(candidates) < minimum:
                    errors.append(
                        f"shape {sid}: {nid} requires at least {minimum} {direction} {rel} "
                        f"edge(s) with source_policy={policy or 'any'}; found {len(candidates)}"
                    )
                if maximum is not None and len(candidates) > int(maximum):
                    errors.append(f"shape {sid}: {nid} allows at most {maximum} {direction} {rel} edge(s)")
            freshness = shape.get("freshness")
            if freshness:
                key = freshness.get("path", "props.observed_at")
                observed = parse_iso_datetime(nested_value(node, key))
                max_age = int(freshness.get("max_age_days", 0))
                if not observed:
                    errors.append(f"shape {sid}: {nid} has no valid ISO timestamp at {key}")
                elif (datetime.now(timezone.utc) - observed).days > max_age:
                    errors.append(f"shape {sid}: {nid} observation at {key} exceeds {max_age} day(s)")
    return errors


def cq_patterns(cq, key):
    value = cq.get(key) or []
    if isinstance(value, str):
        value = [value]
    return [parse_pattern(pattern) for pattern in value]


def run_cq(kg, cq):
    required = cq_patterns(cq, "query")
    if not required:
        return False, "has no executable query"
    try:
        results = evaluate_query(
            kg,
            required,
            cq_patterns(cq, "optional"),
            cq_patterns(cq, "not"),
            cq.get("filter") or [],
        )
    except ValueError as exc:
        return False, str(exc)
    assertion = cq.get("assert") or {"min_results": 1}
    if len(results) < int(assertion.get("min_results", 0)):
        return False, f"returned {len(results)} row(s), below min_results"
    if "max_results" in assertion and len(results) > int(assertion["max_results"]):
        return False, f"returned {len(results)} row(s), above max_results"
    covers = assertion.get("covers")
    if covers:
        var = covers.get("var") or required[0][0]
        expected = {
            node.get("id") for node in kg.nodes.values()
            if node_matches_target(node, {k: v for k, v in covers.items() if k != "var"})
        }
        actual = {binding.get(var) for binding in results}
        missing = sorted(expected - actual)
        if missing:
            return False, f"does not cover {len(missing)} target node(s): {missing[:8]}"
    return True, f"{len(results)} row(s)"


def cmd_test_cq(args):
    kg = KG(args.kg).load()
    questions = kg.schema.get("competency_questions") or []
    if not questions:
        sys.exit("error: schema has no executable competency_questions")
    failures = 0
    for index, cq in enumerate(questions):
        if not isinstance(cq, dict):
            print(f"FAIL cq[{index}]: prose-only competency question")
            failures += 1
            continue
        cid = cq.get("id") or f"cq[{index}]"
        ok, detail = run_cq(kg, cq)
        print(f"{'PASS' if ok else 'FAIL'} {cid}: {detail}")
        failures += not ok
    print(f"\n{len(questions) - failures}/{len(questions)} competency question(s) passed")
    if failures:
        sys.exit(1)


def cmd_validate(args):
    kg = KG(args.kg).load()
    errors, warnings, info = [], [], []
    for f, ln, msg in kg.errors:
        errors.append(f"{f}:{ln}: {msg}")
    if kg.manifest.get("graph_format_version") != GRAPH_FORMAT_VERSION:
        errors.append(
            f"manifest graph_format_version={kg.manifest.get('graph_format_version')!r}; "
            f"expected {GRAPH_FORMAT_VERSION} (run migrate)"
        )
    if kg.schema.get("schema_version") != SCHEMA_VERSION:
        errors.append(
            f"schema schema_version={kg.schema.get('schema_version')!r}; "
            f"expected {SCHEMA_VERSION} (run migrate)"
        )
    seen_ids = set()
    nt = kg.schema.get("node_types") or {}
    et = kg.schema.get("edge_types") or {}
    for nid, n in kg.nodes.items():
        if nid in seen_ids:
            errors.append(f"duplicate node id {nid}")
        seen_ids.add(nid)
        if not ID_RE.match(nid):
            errors.append(f"node id {nid!r} doesn't match type:slug convention")
        if not n.get("label"):
            errors.append(f"node {nid} has no label")
        if not n.get("type"):
            errors.append(f"node {nid} has no type")
        elif n.get("type") not in nt:
            errors.append(f"node {nid} uses undeclared type {n.get('type')!r}")
        sources = evidence_list(n)
        if not sources:
            errors.append(f"node {nid} has no provenance sources")
        for source in sources:
            ok, reason = source_freshness(kg, source)
            if not ok:
                errors.append(f"node {nid} source {source!r}: {reason}")
    used_types = Counter(n.get("type") for n in kg.nodes.values())
    for t, spec in nt.items():
        for prop, need in (spec.get("expected") or {}).items():
            if need != "required":
                continue
            missing = [nid for nid, n in kg.nodes.items() if n.get("type") == t
                       and prop not in (n.get("props") or {})]
            if missing:
                errors.append(f"{len(missing)} {t} node(s) missing required prop {prop!r}: "
                              f"{missing[:5]}{'...' if len(missing) > 5 else ''}")
    eids = set()
    used_rels = Counter()
    func_check = defaultdict(set)
    edge_pairs = defaultdict(list)
    assertions = defaultdict(list)
    for e in kg.edges:
        eid = e.get("id")
        if eid:
            if eid in eids:
                errors.append(f"duplicate edge id {eid}")
            eids.add(eid)
        else:
            errors.append(f"edge {e.get('from')} -[{e.get('rel')}]-> {e.get('to')} has no id")
        for end in ("from", "to"):
            if e.get(end) not in kg.nodes:
                errors.append(f"edge {eid or '?'} {end}={e.get(end)!r} is not a node (dangling)")
        rel = e.get("rel")
        used_rels[rel] += 1
        if rel not in et:
            errors.append(f"edge {eid or '?'} uses undeclared relation {rel!r}")
        source = e.get("source")
        if not source:
            errors.append(f"edge {eid or '?'} has no source evidence")
        else:
            ok, reason = source_freshness(kg, source)
            if not ok:
                errors.append(f"edge {eid or '?'} source {source!r}: {reason}")
            expected_id = assertion_id(e.get("from", ""), rel or "", e.get("to", ""), source)
            if eid != expected_id:
                errors.append(f"edge {eid or '?'} id is not content-derived; expected {expected_id}")
            assertions[(e.get("from"), rel, e.get("to"), source)].append(eid)
        rec = e.get("recorded", "")
        if not rec or not parse_iso_datetime(rec):
            errors.append(f"edge {eid}: recorded={rec!r} is not ISO-8601")
        spec = et.get(rel) or {}
        if spec.get("functional"):
            key = (e.get("from"), rel)
            func_check[key].add(e.get("to"))
        for side, decl in (("from", "domain"), ("to", "range")):
            allowed = spec.get(decl) or []
            if allowed:
                node = kg.nodes.get(e.get(side))
                if node:
                    chain = kg.subtype_chain(node.get("type", ""))
                    if not any(c in allowed for c in chain):
                        errors.append(f"edge {eid}: {decl} of {rel} expects {allowed}, "
                                      f"got {node.get('type')} ({e.get(side)})")
        edge_pairs[(e.get("from"), rel, e.get("to"))].append(eid)
        if e.get("from") == e.get("to"):
            info.append(f"self-loop: {eid} on {e.get('from')}")
    for (frm, rel), targets in func_check.items():
        if len(targets) > 1:
            errors.append(f"functional relation conflict: {frm} has multiple {rel} targets {sorted(targets)}")
    for key, ids in assertions.items():
        if len(ids) > 1:
            errors.append(f"duplicate assertion {key}: {ids}")
    for (f_, r_, t_), ids in edge_pairs.items():
        spec = et.get(r_) or {}
        if spec.get("symmetric") and (t_, r_, f_) in edge_pairs and f_ < t_:
            errors.append(f"symmetric relation {r_} stored in both directions between {f_} and {t_}")
        inv = spec.get("inverse")
        if inv and (t_, inv, f_) in edge_pairs:
            errors.append(f"both {r_} and inverse {inv} stored between {f_} and {t_}")
    root = project_root(args.kg)
    fresh_sources = set()
    for src, meta in (kg.manifest.get("sources") or {}).items():
        try:
            key = normalize_source_path(src, root, kg.manifest)
        except ValueError as exc:
            errors.append(f"manifest source {src!r}: {exc}")
            continue
        p = source_file_path(root, key)
        if not os.path.isfile(p):
            errors.append(f"ingested source {src} no longer exists")
            continue
        expected = meta.get("sha256") or meta.get("sha1")
        actual = hash_file(p) if meta.get("sha256") else hashlib.sha1(open(p, "rb").read()).hexdigest()
        if not expected or actual != expected:
            errors.append(f"stale source: {src} changed since ingest")
            continue
        if meta.get("runtime"):
            ingested = parse_iso_datetime(meta.get("ingested"))
            max_age = int(meta.get("max_age_days") or 0)
            if not ingested or (datetime.now(timezone.utc) - ingested).days > max_age:
                errors.append(f"runtime source {src} exceeds its {max_age}-day freshness bound")
                continue
        fresh_sources.add(src)
    drifted = []
    for e in kg.edges:
        src = split_source(e.get("source"))[0]
        rec = str(e.get("recorded") or "")
        ing = ((kg.manifest.get("sources") or {}).get(src) or {}).get("ingested", "")
        if src and rec and ing and rec < ing and "#" in (e.get("source") or ""):
            drifted.append(e.get("id") or f"{e.get('from')}->{e.get('to')}")
    if drifted:
        warnings.append(f"possible anchor drift: {len(drifted)} edge(s) recorded before their source's "
                        f"latest re-ingest - re-verify anchors: {drifted[:6]}{'...' if len(drifted) > 6 else ''}")
    errors.extend(shape_errors(kg, fresh_sources))
    for index, cq in enumerate(kg.schema.get("competency_questions") or []):
        if not isinstance(cq, dict) or not cq.get("query"):
            errors.append(f"competency_questions[{index}] is prose-only; provide id, query, and assert")
    comps = kg.components()
    singles = [c[0] for c in comps if len(c) == 1]
    if singles:
        info.append(f"{len(singles)} orphan node(s): {singles[:8]}{'...' if len(singles) > 8 else ''}")
    if len(comps) > 1 + len(singles):
        info.append(f"{len([c for c in comps if len(c) > 1]) - 1} disconnected island(s) beyond the main component")
    placeholders = [nid for nid, n in kg.nodes.items() if (n.get("props") or {}).get("placeholder")]
    if placeholders:
        info.append(f"{len(placeholders)} unresolved placeholder node(s): {placeholders[:5]}")
    for name, items in (("ERROR", errors), ("WARN", warnings), ("INFO", info)):
        for msg in items:
            print(f"{name}: {msg}")
    print(f"\n{len(kg.nodes)} nodes, {len(kg.edges)} edges - "
          f"{len(errors)} errors, {len(warnings)} warnings, {len(info)} notes")
    if errors or (args.strict and warnings):
        sys.exit(1)
    print("OK" if not warnings else "OK (with warnings)")

# ------------------------------------------------------------ export

def cmd_export(args):
    kg = KG(args.kg).load()
    fmt = args.format
    out = args.out
    if fmt == "html":
        out = out or os.path.join(kg.dir, "graph.html")
        data = {
            "project": kg.manifest.get("project", "knowledge graph"),
            "nodes": [{"id": nid, "type": n.get("type", "?"), "label": n.get("label", nid),
                       "aliases": n.get("aliases") or [], "description": n.get("description", ""),
                       "props": n.get("props") or {},
                       "deg": len(kg.out.get(nid, [])) + len(kg.inc.get(nid, []))}
                      for nid, n in kg.nodes.items()],
            "edges": [{"from": e.get("from"), "to": e.get("to"), "rel": e.get("rel", ""),
                       "source": e.get("source", "")}
                      for e in kg.edges if e.get("from") in kg.nodes and e.get("to") in kg.nodes],
        }
        html = HTML_TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False))
        with open(out, "w", encoding="utf-8") as f:
            f.write(html)
    elif fmt == "graphml":
        out = out or os.path.join(kg.dir, "graph.graphml")
        def esc(s):
            return (str(s).replace("&", "&amp;").replace("<", "&lt;")
                    .replace(">", "&gt;").replace('"', "&quot;"))
        lines = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
                 '<key id="label" for="node" attr.name="label" attr.type="string"/>',
                 '<key id="type" for="node" attr.name="type" attr.type="string"/>',
                 '<key id="rel" for="edge" attr.name="rel" attr.type="string"/>',
                 '<graph edgedefault="directed">']
        for nid, n in kg.nodes.items():
            lines.append(f'<node id="{esc(nid)}"><data key="label">{esc(n.get("label", ""))}</data>'
                         f'<data key="type">{esc(n.get("type", ""))}</data></node>')
        for e in kg.edges:
            if e.get("from") in kg.nodes and e.get("to") in kg.nodes:
                lines.append(f'<edge source="{esc(e["from"])}" target="{esc(e["to"])}">'
                             f'<data key="rel">{esc(e.get("rel", ""))}</data></edge>')
        lines += ["</graph>", "</graphml>"]
        open(out, "w", encoding="utf-8").write("\n".join(lines))
    elif fmt == "mermaid":
        out = out or os.path.join(kg.dir, "graph.mmd")
        ids = {nid: f"n{i}" for i, nid in enumerate(kg.nodes)}
        lines = ["graph LR"]
        for nid, n in kg.nodes.items():
            lab = (n.get("label", nid)).replace('"', "'")
            lines.append(f'  {ids[nid]}["{lab}"]')
        cap = 300
        for e in kg.edges[:cap]:
            if e.get("from") in ids and e.get("to") in ids:
                lines.append(f'  {ids[e["from"]]} -->|{e.get("rel", "")}| {ids[e["to"]]}')
        if len(kg.edges) > cap:
            lines.append(f'  %% truncated: {len(kg.edges) - cap} more edges')
        open(out, "w", encoding="utf-8").write("\n".join(lines))
    elif fmt == "csv":
        outdir = out or kg.dir
        np_, ep_ = os.path.join(outdir, "nodes.csv"), os.path.join(outdir, "edges.csv")
        import csv
        with open(np_, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["id", "type", "label", "aliases", "description"])
            for nid, n in kg.nodes.items():
                w.writerow([nid, n.get("type", ""), n.get("label", ""),
                            "|".join(n.get("aliases") or []), n.get("description", "")])
        with open(ep_, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["id", "from", "rel", "to", "source", "recorded"])
            for e in kg.edges:
                w.writerow([e.get("id", ""), e.get("from", ""), e.get("rel", ""),
                            e.get("to", ""), e.get("source", ""), e.get("recorded", "")])
        print(f"wrote {np_} and {ep_}")
        return
    print(f"wrote {out}")

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Knowledge graph</title>
<style>
:root{--bg:#0f1419;--panel:#1a2129;--ink:#e6edf3;--mut:#8b98a5;--line:#2d3742}
*{box-sizing:border-box;margin:0}
body{background:var(--bg);color:var(--ink);font:14px/1.45 -apple-system,'Segoe UI',Roboto,sans-serif;overflow:hidden}
#top{position:fixed;inset:0 0 auto 0;display:flex;gap:10px;align-items:center;padding:10px 14px;background:linear-gradient(var(--bg) 70%,transparent);z-index:3}
#top h1{font-size:15px;font-weight:600;margin-right:6px}
#q{background:var(--panel);border:1px solid var(--line);color:var(--ink);border-radius:8px;padding:7px 10px;width:240px;outline:none}
#types{display:flex;gap:6px;flex-wrap:wrap}
.chip{border:1px solid var(--line);border-radius:20px;padding:3px 10px;cursor:pointer;font-size:12px;color:var(--mut);user-select:none}
.chip.on{color:var(--ink);border-color:currentColor}
canvas{display:block}
#panel{position:fixed;top:0;right:0;bottom:0;width:320px;background:var(--panel);border-left:1px solid var(--line);padding:52px 16px 16px;overflow:auto;transform:translateX(100%);transition:.18s;z-index:2}
#panel.open{transform:none}
#panel h2{font-size:16px;margin-bottom:2px}
#panel .id{color:var(--mut);font-size:12px;font-family:ui-monospace,monospace;word-break:break-all}
#panel .sec{margin-top:12px;font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--mut)}
#panel ul{list-style:none;margin-top:4px}
#panel li{padding:3px 0;border-bottom:1px solid var(--line);font-size:13px}
#panel li b{color:var(--mut);font-weight:500}
#panel a{color:#6cb6ff;cursor:pointer;text-decoration:none}
#hint{position:fixed;left:14px;bottom:12px;color:var(--mut);font-size:12px;z-index:2}
</style></head><body>
<div id="top"><h1 id="title"></h1><input id="q" placeholder="search nodes…"><div id="types"></div></div>
<canvas id="c"></canvas><div id="panel"></div>
<div id="hint">drag nodes · scroll to zoom · click for details</div>
<script>
const DATA=__DATA__;
const PAL=['#58a6ff','#3fb950','#d29922','#f778ba','#a371f7','#ff7b72','#39c5cf','#9e6a03','#6e7681','#bc8cff'];
const types=[...new Set(DATA.nodes.map(n=>n.type))].sort();
const tcol=Object.fromEntries(types.map((t,i)=>[t,PAL[i%PAL.length]]));
const on=Object.fromEntries(types.map(t=>[t,true]));
document.getElementById('title').textContent=DATA.project;
const tdiv=document.getElementById('types');
types.forEach(t=>{const c=document.createElement('div');c.className='chip on';c.textContent=t;
c.style.color=tcol[t];c.onclick=()=>{on[t]=!on[t];c.classList.toggle('on');};tdiv.appendChild(c);});
const cv=document.getElementById('c'),ctx=cv.getContext('2d');
let W,H;function rs(){W=cv.width=innerWidth*devicePixelRatio;H=cv.height=innerHeight*devicePixelRatio;
cv.style.width=innerWidth+'px';cv.style.height=innerHeight+'px';}rs();addEventListener('resize',rs);
const N=DATA.nodes.map((n,i)=>({...n,x:Math.cos(i*2.4)*(120+8*Math.sqrt(i)),y:Math.sin(i*2.4)*(120+8*Math.sqrt(i)),vx:0,vy:0}));
const byId=Object.fromEntries(N.map(n=>[n.id,n]));
const E=DATA.edges.filter(e=>byId[e.from]&&byId[e.to]);
const adj={};E.forEach(e=>{(adj[e.from]??=[]).push(e);(adj[e.to]??=[]).push(e);});
let cx=0,cy=0,scale=1,drag=null,pan=null,sel=null,hov=null,q='';
document.getElementById('q').oninput=e=>q=e.target.value.toLowerCase();
function vis(n){return on[n.type]&&(!q||n.label.toLowerCase().includes(q)||n.id.toLowerCase().includes(q)||(n.aliases||[]).some(a=>a.toLowerCase().includes(q)));}
function tick(){
 const vs=N.filter(vis);
 for(const n of vs){n.vx*=.85;n.vy*=.85;n.vx-=n.x*.0015;n.vy-=n.y*.0015;}
 for(let i=0;i<vs.length;i++)for(let j=i+1;j<vs.length;j++){const a=vs[i],b=vs[j];
  let dx=b.x-a.x,dy=b.y-a.y,d2=dx*dx+dy*dy||1;if(d2<40000){const f=1200/d2;const d=Math.sqrt(d2);
  dx/=d;dy/=d;a.vx-=dx*f;a.vy-=dy*f;b.vx+=dx*f;b.vy+=dy*f;}}
 for(const e of E){const a=byId[e.from],b=byId[e.to];if(!vis(a)||!vis(b))continue;
  let dx=b.x-a.x,dy=b.y-a.y;const d=Math.sqrt(dx*dx+dy*dy)||1;const f=(d-90)*.004;dx/=d;dy/=d;
  a.vx+=dx*f*d*.01;a.vy+=dy*f*d*.01;b.vx-=dx*f*d*.01;b.vy-=dy*f*d*.01;}
 for(const n of vs){if(n===drag)continue;n.x+=n.vx;n.y+=n.vy;}
 draw();requestAnimationFrame(tick);}
function draw(){ctx.setTransform(1,0,0,1,0,0);ctx.clearRect(0,0,W,H);
 ctx.setTransform(scale*devicePixelRatio,0,0,scale*devicePixelRatio,W/2+cx*devicePixelRatio,H/2+cy*devicePixelRatio);
 const hi=sel?new Set([sel.id,...(adj[sel.id]||[]).flatMap(e=>[e.from,e.to])]):null;
 for(const e of E){const a=byId[e.from],b=byId[e.to];if(!vis(a)||!vis(b))continue;
  const dim=hi&&!(hi.has(a.id)&&hi.has(b.id));ctx.strokeStyle=dim?'rgba(120,130,140,.08)':'rgba(120,130,140,.35)';
  ctx.lineWidth=dim?.5:1;ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke();
  if(!dim&&scale>0.7){const mx=(a.x+b.x)/2,my=(a.y+b.y)/2;ctx.fillStyle='rgba(139,152,165,.75)';
  ctx.font='9px sans-serif';ctx.textAlign='center';ctx.fillText(e.rel,mx,my-3);}}
 for(const n of N){if(!vis(n))continue;const r=4+Math.min(10,Math.sqrt(n.deg||0)*1.6);
  const dim=hi&&!hi.has(n.id);ctx.globalAlpha=dim?.15:1;
  ctx.fillStyle=tcol[n.type];ctx.beginPath();ctx.arc(n.x,n.y,r,0,7);ctx.fill();
  if(n===sel||n===hov){ctx.strokeStyle='#fff';ctx.lineWidth=1.5;ctx.stroke();}
  ctx.fillStyle=dim?'rgba(230,237,243,.25)':'#e6edf3';ctx.font=(n===sel?'600 ':'')+'11px sans-serif';
  ctx.textAlign='center';ctx.fillText(n.label,n.x,n.y+r+11);ctx.globalAlpha=1;}}
function pick(px,py){const x=(px*devicePixelRatio-W/2-cx*devicePixelRatio)/(scale*devicePixelRatio),
 y=(py*devicePixelRatio-H/2-cy*devicePixelRatio)/(scale*devicePixelRatio);
 return N.filter(vis).reverse().find(n=>{const r=6+Math.min(10,Math.sqrt(n.deg||0)*1.6);
 return (n.x-x)**2+(n.y-y)**2<r*r*1.8;});}
cv.onmousedown=e=>{const n=pick(e.clientX,e.clientY);if(n)drag=n;else pan={x:e.clientX-cx,y:e.clientY-cy};};
onmousemove=e=>{if(drag){drag.x=(e.clientX*devicePixelRatio-W/2-cx*devicePixelRatio)/(scale*devicePixelRatio);
 drag.y=(e.clientY*devicePixelRatio-H/2-cy*devicePixelRatio)/(scale*devicePixelRatio);drag.vx=drag.vy=0;}
 else if(pan){cx=e.clientX-pan.x;cy=e.clientY-pan.y;}else hov=pick(e.clientX,e.clientY);};
onmouseup=e=>{if(drag&&!e.movementX&&!e.movementY){}if(pan&&Math.abs(e.clientX-(pan.x+cx))<3){}
 if(drag){select(drag);}else if(pan){const n=pick(e.clientX,e.clientY);if(!n&&Math.abs(e.movementX)<2)select(null);}
 drag=null;pan=null;};
cv.onclick=e=>{const n=pick(e.clientX,e.clientY);select(n||null);};
addEventListener('wheel',e=>{scale=Math.max(.15,Math.min(4,scale*(e.deltaY<0?1.1:0.9)));},{passive:true});
const panel=document.getElementById('panel');
function esc(s){return String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
function select(n){sel=n;if(!n){panel.classList.remove('open');return;}
 const outs=(adj[n.id]||[]).filter(e=>e.from===n.id),ins=(adj[n.id]||[]).filter(e=>e.to===n.id&&e.from!==n.id);
 let h=`<h2>${esc(n.label)}</h2><div class="id">${esc(n.id)}</div>
 <div style="margin-top:6px"><span class="chip on" style="color:${tcol[n.type]}">${esc(n.type)}</span></div>`;
 if(n.description)h+=`<div class="sec">about</div><div>${esc(n.description)}</div>`;
 if((n.aliases||[]).length)h+=`<div class="sec">aka</div><div>${n.aliases.map(esc).join(', ')}</div>`;
 const pk=Object.keys(n.props||{});
 if(pk.length)h+=`<div class="sec">properties</div><ul>${pk.map(k=>`<li><b>${esc(k)}:</b> ${esc(n.props[k])}</li>`).join('')}</ul>`;
 if(outs.length)h+=`<div class="sec">outgoing (${outs.length})</div><ul>${outs.map(e=>`<li><b>${esc(e.rel)}</b> → <a onclick="jump('${e.to}')">${esc(byId[e.to].label)}</a></li>`).join('')}</ul>`;
 if(ins.length)h+=`<div class="sec">incoming (${ins.length})</div><ul>${ins.map(e=>`<li><b>${esc(e.rel)}</b> ← <a onclick="jump('${e.from}')">${esc(byId[e.from].label)}</a></li>`).join('')}</ul>`;
 panel.innerHTML=h;panel.classList.add('open');}
window.jump=id=>{const n=byId[id];if(n){select(n);cx=-n.x*scale;cy=-n.y*scale;}};
tick();
</script></body></html>"""

# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(prog="kg.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kg", default="kg", help="knowledge graph directory (default ./kg)")
    ap.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="scaffold a new knowledge graph directory")
    p.add_argument("--project", help="project name")
    p.add_argument("--profile", choices=["generic", "research"], default="generic")
    p.add_argument("--force", action="store_true", help="overwrite existing files")
    p.set_defaults(fn=cmd_init)

    p = sub.add_parser("stats", help="overview: counts by type/relation, components, vocabulary drift")
    p.set_defaults(fn=cmd_stats)

    p = sub.add_parser("find", help="locate nodes by label/alias substring")
    p.add_argument("text"); p.add_argument("--type"); p.add_argument("--limit", type=int, default=15)
    p.add_argument("--deep", action="store_true", help="also search descriptions and props")
    p.set_defaults(fn=cmd_find)

    p = sub.add_parser("show", help="one node with all its edges and provenance")
    p.add_argument("id"); p.set_defaults(fn=cmd_show)

    p = sub.add_parser("context", help="markdown briefing about a node (for dropping into agent context)")
    p.add_argument("id"); p.add_argument("--depth", type=int, default=2, choices=[1, 2])
    p.set_defaults(fn=cmd_context)

    p = sub.add_parser("neighbors", help="breadth-first neighborhood, schema-aware (symmetric/inverse)")
    p.add_argument("id"); p.add_argument("--rel"); p.add_argument("--depth", type=int, default=1)
    p.add_argument("--direction", choices=["in", "out", "both"], default="both")
    p.set_defaults(fn=cmd_neighbors)

    p = sub.add_parser("path", help="shortest path between two nodes")
    p.add_argument("a"); p.add_argument("b")
    p.add_argument("--rel", help="comma-separated relations to restrict traversal")
    p.add_argument("--directed", action="store_true", help="follow edge direction only")
    p.set_defaults(fn=cmd_path)

    p = sub.add_parser("query", help="triple patterns with ?vars, joined on shared vars. "
                                     "Supports optional, anti-join, property filters, and aggregation")
    p.add_argument("patterns", nargs="+", metavar='"?s rel ?o"')
    p.add_argument("--optional", action="append", default=[], metavar='"?s rel ?o"',
                   help="left-join an optional pattern (repeatable)")
    p.add_argument("--not", dest="negative", action="append", default=[], metavar='"?s rel ?o"',
                   help="anti-join: exclude bindings matching this pattern (repeatable)")
    p.add_argument("--filter", dest="filters", action="append", default=[],
                   help="'?var.type=Type' or '?var.props.status=open,closed'")
    p.add_argument("--count-by", metavar="?VAR", help="aggregate result counts by a bound variable")
    p.add_argument("--ids-only", action="store_true")
    p.set_defaults(fn=cmd_query)

    p = sub.add_parser("test-cq", help="execute structured competency questions from schema.json")
    p.set_defaults(fn=cmd_test_cq)

    p = sub.add_parser("important", help="key nodes by degree + PageRank")
    p.add_argument("--top", type=int, default=12); p.set_defaults(fn=cmd_important)

    p = sub.add_parser("communities", help="clusters via label propagation")
    p.add_argument("--min-size", type=int, default=2); p.set_defaults(fn=cmd_communities)

    p = sub.add_parser("orphans", help="disconnected nodes and islands")
    p.set_defaults(fn=cmd_orphans)

    p = sub.add_parser("similar", help="nodes sharing neighbors (missing-link / duplicate candidates)")
    p.add_argument("id"); p.add_argument("--top", type=int, default=8); p.set_defaults(fn=cmd_similar)

    p = sub.add_parser("dupes", help="duplicate-candidate scan across the whole graph")
    p.set_defaults(fn=cmd_dupes)

    p = sub.add_parser("validate", help="quality checks: integrity, schema conformance, staleness, "
                                        "orphans, duplicates")
    p.add_argument("--strict", action="store_true", help="non-zero exit on warnings too")
    p.set_defaults(fn=cmd_validate)

    p = sub.add_parser("add-node", help="add a node (refuses likely duplicates)")
    p.add_argument("--id", required=True); p.add_argument("--type", required=True)
    p.add_argument("--label", required=True); p.add_argument("--aliases")
    p.add_argument("--description"); p.add_argument("--props", help="JSON object")
    p.add_argument("--source", action="append", required=True,
                   help="repository path#anchor evidence (repeatable)")
    p.add_argument("--force", action="store_true"); p.set_defaults(fn=cmd_add_node)

    p = sub.add_parser("add-edge", help="add a source-scoped assertion (same triple may have multiple sources)")
    p.add_argument("--from", dest="frm", required=True); p.add_argument("--rel", required=True)
    p.add_argument("--to", required=True); p.add_argument("--source", required=True,
                                                         help="repository path#anchor evidence")
    p.add_argument("--props", help="JSON object")
    p.set_defaults(fn=cmd_add_edge)

    p = sub.add_parser("merge", help="consolidate a duplicate node into the canonical one")
    p.add_argument("dup"); p.add_argument("canon")
    p.add_argument("--prefer", choices=["canon", "dup"], help="resolve reported attribute conflicts")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_merge)

    p = sub.add_parser("mark-ingested", help="record source file hashes in the manifest after extraction")
    p.add_argument("paths", nargs="+")
    p.add_argument("--allow-external", action="store_true",
                   help="explicitly authorize a source outside the project root")
    p.add_argument("--allow-runtime", action="store_true",
                   help="deliberately ingest runtime state/log material with a freshness bound")
    p.add_argument("--max-age-days", type=int, default=1)
    p.set_defaults(fn=cmd_mark_ingested)

    p = sub.add_parser("remove-source", help="drop all edges recorded from a source file")
    p.add_argument("source"); p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_remove_source)

    p = sub.add_parser("refresh-source", help="validate and atomically replace one source's assertions")
    p.add_argument("source", help="repository-relative source path")
    p.add_argument("--nodes", required=True, help="staged nodes JSONL")
    p.add_argument("--edges", required=True, help="staged edges JSONL")
    p.add_argument("--prefer-staged", action="store_true",
                   help="resolve node attribute conflicts in favour of staged values")
    p.add_argument("--allow-runtime", action="store_true")
    p.add_argument("--max-age-days", type=int, default=1)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_refresh_source)

    p = sub.add_parser("migrate", help="migrate an older graph to the current format")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_migrate)

    p = sub.add_parser("export", help="html (interactive), graphml, mermaid, or csv")
    p.add_argument("--format", choices=["html", "graphml", "mermaid", "csv"], default="html")
    p.add_argument("--out"); p.set_defaults(fn=cmd_export)

    args = ap.parse_args()
    args.fn(args)

if __name__ == "__main__":
    main()
