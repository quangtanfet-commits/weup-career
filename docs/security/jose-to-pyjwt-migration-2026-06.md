# JWT library migration: python-jose → PyJWT (N-5)

> Status: implemented 2026-06-02 · Scope: `backend/app/core/security.py` (sole JWT call site)
> Related: [ADR-008 Security Controls](../adr/ADR-008-security-controls.md), [auth-design.md](./auth-design.md), CP-7 (algorithm-confusion hardening)

## 1. Vì sao đổi thư viện

`python-jose` thực tế đã ngừng bảo trì (release cuối 3.5.0; nhiều issue/PR
tồn đọng nhiều năm) và đã dính các CVE liên quan trực tiếp tới phần ta dùng:

| CVE | Bản chất | Liên quan tới ta |
|---|---|---|
| CVE-2024-33663 | Algorithm confusion — JWS chấp nhận key sai loại trong một số đường đi | Ta dùng đúng path bị soi xét nhất: xác thực `alg` + chữ ký |
| CVE-2024-33664 | JWE decryption DoS (nén bom) | Không dùng JWE, nhưng cho thấy thư viện thiếu bảo trì |

`PyJWT` là thư viện JWT chuẩn de-facto của hệ sinh thái Python: được bảo trì
tích cực, có type hints sẵn (`py.typed`), API tối giản, và là phần phụ thuộc
nền của nhiều framework auth. Đổi sang PyJWT giảm bề mặt rủi ro chuỗi cung ứng
mà **không** thay đổi hành vi token đối ngoại.

Đây là khoản N-5 trong backlog hardening (sau N-2 coverage gate, N-6 SHA-pin).

## 2. Hợp đồng hành vi PHẢI giữ nguyên

`security.py` là **call site JWT duy nhất** của backend (xác nhận bằng grep
`jose`/`jwt.encode`/`jwt.decode`). Mọi hành vi đối ngoại của hai hàm dưới đây
phải bất biến qua migration — đây là các bất biến mà test khoá lại:

`create_access_token`:
- Trả về JWT ký HS256 (`settings.jwt_algorithm`), kiểu `str`.
- Claims: `sub, email, user_type, age_band, account_status, roles, sv, iat, exp, jti, iss`.
- `jti` mặc định ngẫu nhiên duy nhất mỗi lần; honor `jti` do caller truyền.

`decode_access_token` — raise `TokenError` cho MỌI lỗi, ngược lại trả claims:
- Xác minh chữ ký HS256.
- `exp` hết hạn → từ chối.
- `iss` phải khớp `settings.jwt_issuer` → sai issuer từ chối.
- Bắt buộc có claims `["exp", "sub", "iss"]` (thiếu → từ chối).
- `alg=none` (token không ký) → từ chối.
- Algorithm-substitution (header `alg` ngoài allow-list, vd HS512) → từ chối
  TRƯỚC khi so chữ ký.
- Chữ ký sai / token méo → từ chối.

Các test khoá hợp đồng này: `tests/unit/test_security.py` (expiry / bad-sig /
wrong-issuer / wrong-secret) và `tests/unit/test_token_algorithms.py`
(alg=none / algorithm-substitution / jti uniqueness / jti honored).

## 3. Ánh xạ API jose → PyJWT

| Việc | python-jose | PyJWT | Ghi chú |
|---|---|---|---|
| Import | `from jose import JWTError, jwt` | `import jwt` | Base exception là `jwt.PyJWTError` |
| Encode | `jwt.encode(claims, key, algorithm=alg)` | giống hệt | PyJWT 2.x trả `str` (jose cũng `str`) — không đổi kiểu |
| Decode | `jwt.decode(token, key, algorithms=[alg], issuer=iss, options={"require":[...]})` | giống hệt | PyJWT xác minh `iss` khi truyền `issuer=`; `require` ép có claim |
| Bắt lỗi | `except JWTError` | `except jwt.PyJWTError` | Mọi lỗi con (`ExpiredSignatureError`, `InvalidIssuerError`, `InvalidSignatureError`, `InvalidAlgorithmError`, `MissingRequiredClaimError`, `DecodeError`) đều kế thừa `PyJWTError` |

`options={"require": ["exp","sub","iss"]}` giữ nguyên ngữ nghĩa: PyJWT raise
`MissingRequiredClaimError` (⊂ `PyJWTError`) nếu thiếu. `alg=none` và HS512
ngoài allow-list → `InvalidAlgorithmError` (⊂ `PyJWTError`) → quy về `TokenError`.

## 4. Thay đổi phụ thuộc & typing

- `pyproject.toml`:
  - Bỏ `"python-jose[cryptography]>=3.3,<4"`.
  - Thêm `"pyjwt>=2.10,<3"`. HS256 (HMAC) **không** cần extra `crypto`
    (extra đó chỉ cho RSA/EC/PS); `cryptography` vẫn là direct dep cho field
    encryption, sẵn sàng nếu sau này chuyển RS256.
- Bỏ block mypy override `module = ["jose.*"]` — PyJWT ship type hints
  (`py.typed`), không cần `ignore_missing_imports`. mypy `--strict` phải xanh
  mà không cần override.
- `uv.lock`: regenerate (`uv lock`) — gỡ `python-jose` + `ecdsa`/`rsa`/`pyasn1`
  transitive nếu không còn ai dùng.

## 5. Kế hoạch kiểm chứng

1. `uv run pytest tests/unit/test_security.py tests/unit/test_token_algorithms.py -q`
   — tất cả pass, không đổi 1 dòng assert nào (chỉ sửa 1 comment nhắc tên thư viện).
2. Full suite `uv run pytest` — 436 test xanh, coverage không tụt (gate 95% +
   critical-layer 100% gồm `app/core/security.py`).
3. `uv run mypy app` `--strict` — xanh không cần override `jose.*`.
4. **Sabotage** (bắt buộc, theo /formal-verify Hard Rule 1): tạm thêm
   `"verify_signature": False` vào `options` của `decode_access_token`; chạy
   `test_token_algorithms.py` + `test_security.py` → 6 test PHẢI fail
   (`test_alg_none_*`, `test_algorithm_substitution_rejected`,
   `test_expired_token_rejected`, `test_tampered_signature_rejected`,
   `test_wrong_issuer_rejected`, `test_wrong_secret_rejected`). Hoàn tác.
   Chứng minh toàn bộ đường xác minh có răng.

   > Lưu ý đã đo: chỉ **nới allow-list** (thêm `"HS512"`/`"none"`) KHÔNG đủ làm
   > fail hai test forgery — đây là defense-in-depth của PyJWT: substitution
   > HS512 vẫn fail ở bước so chữ ký (attacker không có khoá), và PyJWT tự từ
   > chối `alg=none` khi có key. Vì vậy sabotage đúng là tắt
   > `verify_signature`, không phải nới allow-list.
5. `grep -rn "jose" backend/app backend/tests` → 0 kết quả.

## 6. Rủi ro & giảm thiểu

| Rủi ro | Giảm thiểu |
|---|---|
| PyJWT khác jose ở edge case alg | Sabotage check §5.4 chứng minh từ chối thật |
| Đổi kiểu trả về encode (bytes vs str) | PyJWT 2.x trả `str`; test round-trip decode xác nhận |
| Lỗi ẩn do bỏ mypy override | mypy `--strict` không override sẽ phát hiện mọi mismatch type |
| Phụ thuộc transitive còn sót | `uv lock` + grep xác nhận `python-jose` rời lockfile |
