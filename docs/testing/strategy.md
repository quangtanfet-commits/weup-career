# Testing Strategy

**Version:** 1.0.0 | **Date:** 2026-05-27  
**Target Coverage:** ≥95% lines, 100% on auth + data-access layers

---

## Testing Philosophy

> "Tests are not a quality gate bolted on afterward. They are the **specification made executable**."

1. **Test behaviour, not implementation**: tests assert what the system does, not how it does it
2. **Tests as documentation**: a failing test should tell you exactly what invariant broke
3. **No mocking the DB in integration tests**: use an in-memory SQLite instance; mocks lie
4. **Fast feedback loop**: unit tests < 1s total; integration tests < 30s; E2E < 3min
5. **Meaningful coverage**: 95% line coverage with real assertions; zero coverage padding

---

## Testing Pyramid

```
                    ┌──────────────────┐
                    │   E2E Tests      │  3-5% of tests
                    │  (Playwright)    │  Slow, high confidence
                    │  ~20 scenarios   │  Test full user flows
                    ├──────────────────┤
                    │ Integration Tests│  25% of tests
                    │  (httpx + DB)    │  Medium speed
                    │  ~150 tests      │  Test API + DB together
                    ├──────────────────┤
                    │   Unit Tests     │  70% of tests
                    │  (pytest/vitest) │  Fast, isolated
                    │  ~500 tests      │  Test business logic
                    └──────────────────┘
```

---

## Backend Testing

### Unit Tests (pytest)

**Location:** `backend/tests/unit/`

**What to test:**
- Service layer: all business logic branches
- Repository layer: query building (with in-memory SQLite)
- Auth service: token generation, validation, password hashing
- Schema validation: Pydantic models with edge cases
- Utility functions: date formatting, pagination logic

**Test structure:**
```python
# backend/tests/unit/auth/test_auth_service.py

class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        hashed = hash_password("MyPassword123")
        assert hashed != "MyPassword123"

    def test_verify_correct_password(self):
        hashed = hash_password("MyPassword123")
        assert verify_password("MyPassword123", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("MyPassword123")
        assert verify_password("WrongPassword", hashed) is False

    @given(password=st.text(min_size=8, max_size=128))
    @settings(max_examples=500)
    def test_hash_verify_roundtrip(self, password: str):
        # Property: any valid password can be hashed and verified
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

class TestTokenGeneration:
    def test_access_token_contains_expected_claims(self):
        token = create_access_token(subject="usr_123", email="a@b.com")
        claims = decode_token(token)
        assert claims["sub"] == "usr_123"
        assert claims["iss"] == "todo-api"
        assert "jti" in claims
        assert claims["exp"] > claims["iat"]

    def test_expired_token_raises(self):
        token = create_access_token(subject="usr_123", expire_delta=timedelta(seconds=-1))
        with pytest.raises(TokenExpiredError):
            decode_token(token)
```

**Hypothesis property-based tests:**
- Password hash/verify roundtrip (500+ cases)
- JWT encode/decode roundtrip
- Pydantic schema fuzz (arbitrary strings for title, description)
- SQL injection attempts in search queries (assert no crash, sanitized output)
- Sort order invariant after arbitrary reorder sequences

### Integration Tests (pytest + httpx + SQLite in-memory)

**Location:** `backend/tests/integration/`

**Setup:**
```python
# conftest.py
@pytest.fixture
async def db():
    # Fresh in-memory SQLite per test
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine) as session:
        yield session
    await engine.dispose()

@pytest.fixture
async def client(db):
    app.dependency_overrides[get_db] = lambda: db
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c
```

**Auth integration tests:**
```python
class TestAuthEndpoints:
    async def test_register_creates_user(self, client):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "SecurePass123"
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "test@example.com"
        assert "hashed_password" not in data  # Never leaked

    async def test_register_duplicate_email_returns_409(self, client):
        payload = {"email": "dup@example.com", "password": "SecurePass123"}
        await client.post("/api/v1/auth/register", json=payload)
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 409

    async def test_login_sets_httponly_cookie(self, client, registered_user):
        resp = await client.post("/api/v1/auth/login", json={
            "email": registered_user.email,
            "password": "SecurePass123"
        })
        assert resp.status_code == 200
        cookie = resp.cookies.get("refresh_token")
        assert cookie is not None
        # Verify httpOnly flag set (httpx exposes headers)
        set_cookie_header = resp.headers.get("set-cookie", "")
        assert "HttpOnly" in set_cookie_header
        assert "Secure" in set_cookie_header
        assert "SameSite=Strict" in set_cookie_header

    async def test_invalid_credentials_return_401(self, client, registered_user):
        resp = await client.post("/api/v1/auth/login", json={
            "email": registered_user.email,
            "password": "WrongPassword"
        })
        assert resp.status_code == 401
        # Generic message — no enumeration
        assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"
```

**Authorization integration tests (CRITICAL — 100% branch coverage required):**
```python
class TestTodoOwnership:
    async def test_user_cannot_read_another_users_todo(
        self, client, user1_token, user2_todo
    ):
        resp = await client.get(
            f"/api/v1/todos/{user2_todo.id}",
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        # Returns 404 — not even 403 (don't confirm existence)
        assert resp.status_code == 404

    async def test_user_cannot_delete_another_users_todo(
        self, client, user1_token, user2_todo
    ):
        resp = await client.delete(
            f"/api/v1/todos/{user2_todo.id}",
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        assert resp.status_code == 404

    async def test_user_cannot_update_another_users_todo(
        self, client, user1_token, user2_todo
    ):
        resp = await client.patch(
            f"/api/v1/todos/{user2_todo.id}",
            json={"title": "Hijacked"},
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        assert resp.status_code == 404
```

**Coverage targets for integration tests:**
- All happy paths: 100%
- All 4xx error paths: 100%
- All ownership check branches: 100%
- All status transition paths: 100%

---

## Frontend Testing

### Unit Tests (Vitest + React Testing Library)

**Location:** `frontend/src/**/*.test.tsx` (colocated)

**What to test:**
- Custom hooks: `useAuth`, `useTodos`, `useOptimisticTodo`
- Form validation: Zod schemas with edge cases
- Utility functions: date formatters, priority comparators
- API client: request/response transformations
- Component rendering: key UI states (loading, error, empty, populated)

**MSW handlers for API mocking:**
```typescript
// src/mocks/handlers.ts
export const handlers = [
  http.get('/api/v1/todos', ({ request }) => {
    const url = new URL(request.url)
    const status = url.searchParams.get('status')
    return HttpResponse.json({
      items: mockTodos.filter(t => !status || t.status === status),
      total: mockTodos.length,
      page: 1,
      per_page: 50
    })
  }),
  http.post('/api/v1/todos', async ({ request }) => {
    const body = await request.json()
    return HttpResponse.json(createMockTodo(body), { status: 201 })
  }),
  // ... all handlers
]
```

**Component test example:**
```typescript
// src/features/todos/TodoItem.test.tsx
describe('TodoItem', () => {
  it('renders todo title and status badge', async () => {
    renderWithProviders(<TodoItem todo={mockTodo} />)
    expect(screen.getByText('Buy groceries')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /complete/i })).toBeInTheDocument()
  })

  it('calls onDelete when delete button clicked and confirmed', async () => {
    const onDelete = vi.fn()
    renderWithProviders(<TodoItem todo={mockTodo} onDelete={onDelete} />)
    await userEvent.click(screen.getByRole('button', { name: /delete/i }))
    // Undo toast appears — delete triggered but not confirmed deletion
    expect(screen.getByText(/undo/i)).toBeInTheDocument()
    expect(onDelete).toHaveBeenCalledWith(mockTodo.id)
  })

  it('shows loading skeleton while fetching', () => {
    renderWithProviders(<TodoItem todo={undefined} isLoading />)
    expect(screen.getByTestId('todo-skeleton')).toBeInTheDocument()
  })
})
```

### E2E Tests (Playwright)

**Location:** `e2e/`

**Browser matrix:** Chromium + Firefox + WebKit

**Critical user flows to cover:**

```gherkin
# Registration and login flow
Feature: Authentication
  Scenario: User registers and is automatically logged in
  Scenario: User with existing account logs in successfully
  Scenario: Login with wrong password shows error
  Scenario: Refresh token silently renews session

# Core todo operations
Feature: Todo Management
  Scenario: User creates a todo and it appears in the list
  Scenario: User completes a todo and sees status change
  Scenario: User deletes a todo and can undo within 5 seconds
  Scenario: User filters todos by status
  Scenario: User searches todos by text
  Scenario: User reorders todos by drag and drop

# Tag management
Feature: Tags
  Scenario: User creates a tag and assigns it to a todo
  Scenario: User filters todos by tag

# Error handling
Feature: Error Handling
  Scenario: Expired session redirects to login
  Scenario: Offline state shows appropriate feedback
```

**Playwright setup:**
```typescript
// playwright.config.ts
export default defineConfig({
  testDir: './e2e',
  use: {
    baseURL: 'http://localhost:80',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox',  use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit',   use: { ...devices['Desktop Safari'] } },
    { name: 'mobile',   use: { ...devices['iPhone 13'] } },
  ],
  webServer: {
    command: 'docker compose -f docker-compose.test.yml up',
    url: 'http://localhost:80/api/v1/health',
    reuseExistingServer: false,
  },
})
```

---

## Security Tests

| Test | Tool | Threshold |
|------|------|-----------|
| SAST | Semgrep (`p/python`, `p/react`, `p/security`) | Zero findings |
| Container CVE scan | Trivy | Zero HIGH/CRITICAL |
| Dependency audit | pip-audit + npm audit | Zero HIGH+ |
| DAST baseline | OWASP ZAP (`zap-baseline.py`) | Zero HIGH findings |
| Security headers | `securityheaders.com` equivalent | A+ grade |

---

## Load/Performance Tests

**Tool:** k6 (JavaScript-based load testing)

**Scenarios:**
```javascript
// k6/scenarios/baseline.js
export const options = {
  scenarios: {
    steady_load: {
      executor: 'constant-vus',
      vus: 50,
      duration: '5m',
    },
    spike: {
      executor: 'ramping-vus',
      stages: [
        { duration: '30s', target: 0 },
        { duration: '30s', target: 200 },  // Spike
        { duration: '1m',  target: 200 },
        { duration: '30s', target: 0 },
      ],
    },
  },
  thresholds: {
    http_req_duration: ['p(99)<100'],   // p99 < 100ms for reads
    http_req_failed: ['rate<0.01'],     // <1% error rate
  },
}
```

---

## Coverage Configuration

### Backend (pytest-cov)

```toml
# pyproject.toml
[tool.coverage.run]
source = ["app"]
branch = true
omit = ["*/tests/*", "*/migrations/*", "app/main.py"]

[tool.coverage.report]
fail_under = 95
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "class.*Protocol.*:",
    "@(abc\\.)?abstractmethod",
]
```

**100% branch coverage required for:**
- `app/auth/service.py`
- `app/auth/router.py`
- `app/todos/repository.py`
- `app/core/security.py`

### Frontend (Vitest)

```typescript
// vitest.config.ts
export default {
  test: {
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov', 'html'],
      thresholds: {
        lines: 95,
        branches: 90,
        functions: 95,
      },
      exclude: ['src/main.tsx', 'src/mocks/**', '**/*.stories.tsx'],
    },
  },
}
```

---

## CI Quality Gate Summary

```yaml
# CI fails if ANY of these thresholds are not met:
backend_coverage: >= 95%        # pytest --cov-fail-under=95
frontend_coverage: >= 95%       # vitest --coverage
type_errors: 0                  # mypy --strict && tsc --noEmit
lint_errors: 0                  # ruff + eslint --max-warnings 0
e2e_failures: 0                 # playwright across 3 browsers
security_findings: 0            # trivy + semgrep + zap
tla_invariants: all_pass        # TLC model checker
```
