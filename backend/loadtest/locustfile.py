"""N-1 load test harness (Gate C, NFR-01) — see docs/performance/n1-load-test-2026-06.md.

Drives the load-bearing read/write endpoints under a 200-VU concurrent mix to
turn NFR-01 (read p99<150ms, write p99<300ms, err<0.1% @ 200 users) from an
aspirational SLO into a measured single-node baseline.

Design notes
------------
* **Real authenticated + consented cohort, no faked tokens.** ``test_start``
  builds (or reuses) a pool of ADULT accounts by running the production
  register → verify (read the FileMailer outbox) → login → submit RIASEC →
  generate recommendation chain. Adults (age_band != UNDER_16) clear the
  consent gate without a guardian dance yet still exercise the sensitive read
  path (field-decrypt + append-only audit, CP-3) exactly as in production.
* **The cohort is persisted to a JSON file** so the warm-up phase builds it and
  the measured phase reuses it (the script runs Locust twice — see
  scripts/run-loadtest-native.sh). A run-scoped cohort is never reused across
  runs unless the same ``--cohort-file`` is passed.
* Path-param endpoints are reported under a stable ``name=`` so the percentile
  is per endpoint *group*, not per concrete id.

Run headless, e.g.::

    uv run locust -f backend/loadtest/locustfile.py --headless \\
        --host http://localhost:8000 -u 200 -r 4 -t 5m \\
        --csv report/<run-id>/loadtest/baseline
"""

from __future__ import annotations

import json
import os
import random
import time
from pathlib import Path
from typing import Any

import requests
from locust import HttpUser, between, events, task

# --- configuration -------------------------------------------------------

API = "/api/v1"
TEST_PASSWORD = "WeUpPass123"  # satisfies register schema (>=8, upper+lower+digit)
# RIASEC instrument item keys (backend/app/assessments/seed.py RIASEC_ITEMS).
RIASEC_ITEM_KEYS = [
    "R_1", "R_2", "I_1", "I_2", "A_1", "A_2",
    "S_1", "S_2", "E_1", "E_2", "C_1", "C_2",
]
# FileMailer outbox the native harness points the backend at (it exports
# WEUP_MAILER_OUTBOX before booting uvicorn). One NDJSON {to, verify_url, ts}
# line per "sent" verification email.
OUTBOX_PATH = os.environ.get("WEUP_MAILER_OUTBOX", "/tmp/weup-loadtest-outbox.ndjson")

# Populated once in test_start, read-only thereafter by every VU.
COHORT: list[dict[str, str]] = []
CAREER_IDS: list[str] = []


# --- custom CLI options --------------------------------------------------


@events.init_command_line_parser.add_listener
def _add_args(parser: Any) -> None:
    parser.add_argument(
        "--cohort-size",
        type=int,
        default=50,
        help="Number of real accounts to mint for the VU pool (default 50).",
    )
    parser.add_argument(
        "--cohort-file",
        type=str,
        default="",
        help="JSON file to load/persist the cohort (reused across the two-phase run).",
    )


# --- cohort builder (setup phase, plain requests) ------------------------


def _read_verify_token(email: str) -> str:
    """Scan the outbox newest-first for the latest verify token for ``email``."""
    lines = [
        ln for ln in Path(OUTBOX_PATH).read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]
    for line in reversed(lines):
        rec = json.loads(line)
        if rec.get("to") == email and rec.get("verify_url"):
            from urllib.parse import parse_qs, urlparse

            token = parse_qs(urlparse(rec["verify_url"]).query).get("token", [None])[0]
            if token:
                return token
    raise LookupError(f"no verification email for {email} in {OUTBOX_PATH}")


def _wait_for_token(email: str, *, attempts: int = 50, delay: float = 0.1) -> str:
    """Poll the outbox — the file write can lag the register response by a beat."""
    last: Exception | None = None
    for _ in range(attempts):
        try:
            return _read_verify_token(email)
        except (FileNotFoundError, LookupError) as exc:  # noqa: PERF203
            last = exc
            time.sleep(delay)
    raise RuntimeError(f"verify token never appeared for {email}") from last


def _post_expecting(
    session: requests.Session,
    url: str,
    *,
    json: dict[str, Any],
    expect: int,
    retry_on: tuple[int, ...] = (),
    attempts: int = 8,
    delay: float = 0.1,
) -> requests.Response:
    """POST, retrying while the status is a *transient* read-after-write miss.

    The cohort builder chains register→verify→login with no think-time. Under
    Locust's gevent monkey-patching, SQLite+aiosqlite pooled connections can
    briefly serve a request that has not yet observed the commit made
    microseconds earlier — verify-email transiently 401s (token row unseen) and
    login transiently 403s (``email_verified_at`` unseen). The final DB state is
    always consistent, so a short bounded retry resolves it. Setup-only: this
    never touches the measured NFR-01 request path. See README "Notes".
    """
    last: requests.Response | None = None
    for _ in range(attempts):
        last = session.post(url, json=json, timeout=30)
        if last.status_code == expect:
            return last
        if last.status_code not in retry_on:
            break
        time.sleep(delay)
    assert last is not None
    last.raise_for_status()
    raise RuntimeError(
        f"POST {url} expected {expect}, got {last.status_code} after {attempts} attempts"
    )


def _build_member(base: str, idx: int) -> dict[str, str]:
    """Run the full register→verify→login→submit→reco chain for one adult."""
    email = f"loadtest-{int(time.time())}-{idx}-{random.randint(0, 1_000_000)}@example.vn"
    s = requests.Session()

    r = s.post(
        f"{base}{API}/auth/register",
        json={
            "email": email,
            "password": TEST_PASSWORD,
            "date_of_birth": "1995-01-01",  # adult → clears consent gate, no guardian
            "user_type": "working",
            "school_level": "none",
        },
        timeout=30,
    )
    r.raise_for_status()

    token = _wait_for_token(email)
    # verify-email can transiently 401 (token row not yet visible under gevent).
    _post_expecting(
        s,
        f"{base}{API}/auth/verify-email",
        json={"token": token},
        expect=204,
        retry_on=(401,),
    )

    # login can transiently 403 (email_verified_at not yet visible under gevent).
    r = _post_expecting(
        s,
        f"{base}{API}/auth/login",
        json={"email": email, "password": TEST_PASSWORD},
        expect=200,
        retry_on=(403,),
    )
    access = r.json()["access_token"]
    auth = {"Authorization": f"Bearer {access}"}

    r = s.post(
        f"{base}{API}/assessments/riasec/submit",
        json={"answers": {k: random.randint(1, 5) for k in RIASEC_ITEM_KEYS}},
        headers=auth,
        timeout=30,
    )
    r.raise_for_status()
    result_id = r.json()["id"]

    r = s.post(f"{base}{API}/recommendations", headers=auth, timeout=30)
    r.raise_for_status()
    reco_id = r.json()["id"]

    return {"token": access, "result_id": result_id, "reco_id": reco_id}


@events.test_start.add_listener
def _on_test_start(environment: Any, **_: Any) -> None:
    """Load-or-build the cohort and discover career ids before VUs spawn."""
    global COHORT, CAREER_IDS
    base = environment.host.rstrip("/")
    opts = environment.parsed_options
    size = opts.cohort_size
    cohort_file = opts.cohort_file

    if cohort_file and Path(cohort_file).is_file():
        COHORT = json.loads(Path(cohort_file).read_text(encoding="utf-8"))
        print(f"[cohort] reused {len(COHORT)} members from {cohort_file}")
    else:
        print(f"[cohort] building {size} real accounts against {base} ...")
        built: list[dict[str, str]] = []
        for i in range(size):
            built.append(_build_member(base, i))
            if (i + 1) % 10 == 0:
                print(f"[cohort]   {i + 1}/{size}")
        COHORT = built
        if cohort_file:
            Path(cohort_file).parent.mkdir(parents=True, exist_ok=True)
            Path(cohort_file).write_text(json.dumps(COHORT), encoding="utf-8")
            print(f"[cohort] persisted {len(COHORT)} members to {cohort_file}")

    # Discover real career ids for the browse-detail read.
    resp = requests.get(f"{base}{API}/careers", timeout=30)
    resp.raise_for_status()
    CAREER_IDS = [c["id"] for c in resp.json()]
    print(f"[cohort] discovered {len(CAREER_IDS)} careers")
    if not COHORT or not CAREER_IDS:
        raise RuntimeError("cohort/career setup produced an empty pool — aborting run")


# --- the load profile ----------------------------------------------------


class WeUpUser(HttpUser):
    """One concurrent career-platform user (read-heavy 85/15 mix)."""

    # Models browse think-time between requests; latency percentiles are
    # per-request and independent of this, but it keeps RPS realistic.
    wait_time = between(0.5, 2.0)

    def on_start(self) -> None:
        member = random.choice(COHORT)
        self.result_id = member["result_id"]
        self.reco_id = member["reco_id"]
        self.client.headers["Authorization"] = f"Bearer {member['token']}"

    # ---- read group (gate: p99 < 150 ms) --------------------------------

    @task(35)
    def me_assessment_read(self) -> None:
        """PRIMARY read: decrypt + append-only audit inside the read txn (CP-3)."""
        self.client.get(
            f"{API}/me/assessments/{self.result_id}",
            name="GET /me/assessments/[id]",
        )

    @task(25)
    def careers_browse(self) -> None:
        self.client.get(f"{API}/careers", name="GET /careers")
        if CAREER_IDS:
            self.client.get(
                f"{API}/careers/{random.choice(CAREER_IDS)}",
                name="GET /careers/[id]",
            )

    @task(15)
    def reco_read(self) -> None:
        self.client.get(
            f"{API}/recommendations/{self.reco_id}",
            name="GET /recommendations/[id]",
        )

    @task(10)
    def auth_me(self) -> None:
        self.client.get(f"{API}/auth/me", name="GET /auth/me")

    # ---- write group (gate: p99 < 300 ms) -------------------------------

    @task(10)
    def riasec_submit(self) -> None:
        """PRIMARY write: field-encrypt + audit write."""
        self.client.post(
            f"{API}/assessments/riasec/submit",
            json={"answers": {k: random.randint(1, 5) for k in RIASEC_ITEM_KEYS}},
            name="POST /assessments/riasec/submit",
        )

    @task(5)
    def reco_generate(self) -> None:
        """Recommendation generation with rationale — heaviest sync compute."""
        self.client.post(f"{API}/recommendations", name="POST /recommendations")
