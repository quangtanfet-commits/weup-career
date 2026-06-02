# SHA-pin third-party GitHub Actions (N-6)

**Phiên bản:** 1.0.0 | **Ngày:** 2026-06-02
**Liên quan:** [threat-model.md](./threat-model.md), [dependabot-2026-06.md](./dependabot-2026-06.md), `.github/dependabot.yml`, `.github/workflows/*`
**Trạng thái:** spec → pin + enforcement gate (PR N-6)

> Một `uses: owner/action@v1` trỏ tới một **tag di động**. Chủ repo (hoặc kẻ chiếm được nó) có thể trỏ lại `v1` sang commit chứa mã độc bất kỳ lúc nào, và workflow của ta sẽ chạy mã đó với secrets của ta ở lần CI kế tiếp — **không có PR, không có review, không có cảnh báo**. Đây chính là vụ **`tj-actions/changed-files` (tháng 3/2025)**: tag bị viết đè để rò secrets của hàng nghìn repo. Tài liệu này pin **mọi action bên thứ ba** về **commit SHA 40 ký tự** (bất biến) và lắp một **CI gate** để một ref bên thứ ba chưa pin không thể lọt vào lại.

---

## 1. Vì sao SHA, không phải tag

| Dạng ref | Bất biến? | Rủi ro |
|---|---|---|
| `@v1`, `@v6` (major di động) | ❌ | Bị viết đè bất cứ lúc nào → thực thi mã tùy ý với secrets CI |
| `@v1.2.5` (semver chính xác) | ❌ trên thực tế | Tag vẫn có thể bị xóa + tạo lại trỏ commit khác (Git tag không ký là khả biến) |
| `@<40-hex SHA>` | ✅ | SHA = nội dung commit; không thể giả mạo mà không đổi SHA |

SHA-pin biến "tin tưởng chủ action **mãi mãi**" thành "tin tưởng **đúng một commit ta đã xem**". Nâng cấp về sau là một **PR có diff** (Dependabot lo, xem §5) — tức là quay lại đúng quy trình review.

---

## 2. Phạm vi: pin bên thứ ba, giữ tag cho first-party

**Quyết định:** pin về SHA mọi action **không thuộc** `actions/*` và `github/*`. First-party (`actions/checkout`, `actions/setup-*`, `github/codeql-action/*`, …) **giữ major tag**, do Dependabot quản.

**Lý do:**
- `actions/*` và `github/*` do **chính GitHub** sở hữu và vận hành trên cùng nền tảng đang chạy CI — nếu chúng bị chiếm thì SHA-pin cũng không cứu được (kẻ tấn công đã ở trong nền tảng). Rủi ro chuỗi cung của chúng ở mức nền tảng, khác hẳn action cộng đồng của một maintainer cá nhân.
- Pin toàn bộ first-party tạo **churn** lớn (mỗi patch của checkout/setup-node thành một SHA bump) mà lợi ích biên thấp.
- Posture hiện hành của repo đã là: first-party theo major tag + Dependabot bump (đang có các PR `checkout-6`, `setup-node-6`, `dependency-review-action-5`, `upload-artifact-7`). N-6 **không** đụng vào nhóm này.
- `tj-actions/changed-files` **đã** được pin SHA từ trước (`9426d40…962ed5378 # v47.0.6`) — đúng tiền lệ, giữ nguyên.

Có thể siết first-party về SHA sau (escalation), nhưng không thuộc phạm vi N-6.

---

## 3. Bảng pin (đo 2026-06-02)

11 ref bên thứ ba, mỗi cái resolve `tag → commit SHA` qua `gh api repos/<owner>/<repo>/commits/<tag>`, kèm comment semver chính xác:

| Action | Tag cũ | SHA pin | Comment | File |
|---|---|---|---|---|
| `appleboy/ssh-action` | `v1` | `0ff4204d59e8e51228ff73bce53f80d53301dee2` | `# v1.2.5` | deploy-staging, deploy-production |
| `zaproxy/action-baseline` | `v0.15.0` | `de8ad967d3548d44ef623df22cf95c3b0baf8b25` | `# v0.15.0` | security-scan |
| `codecov/codecov-action` | `v6` | `e79a6962e0d4c0c17b229090214935d2e33f8354` | `# v6.0.1` | ci (×2) |
| `chromaui/action` | `v17` | `d92ea1ce501f70e8c34745b2c7888648150a368a` | `# v17.2.0` | ci |
| `docker/setup-buildx-action` | `v4` | `d7f5e7f509e45cec5c76c4d5afdd7de93d0b3df5` | `# v4.1.0` | ci |
| `docker/login-action` | `v3` | `c94ce9fb468520275223c153574b00df6fe4bcc9` | `# v3.7.0` | ci |
| `docker/metadata-action` | `v5` | `c299e40c65443455700f0fdfc63efafe5b349051` | `# v5.10.0` | ci (×2) |
| `docker/build-push-action` | `v7` | `f9f3042f7e2789586610d6e8b85c8f03e5195baf` | `# v7.2.0` | ci (×2) |
| `aquasecurity/trivy-action` | `v0.36.0` | `ed142fd0673e97e23eac54620cfb913e5ce36c25` | `# v0.36.0` | ci (×4) |
| `softprops/action-gh-release` | `v2` | `3bb12739c298aeb8a4eeaf626c5b8d85266b0e65` | `# v2.6.2` | deploy-production |
| `grafana/k6-action` | `v0.3.1` | `e4714b734f2b0afaabeb7b4a69142745548ab9ec` | `# v0.3.1` | load-test |

Quy ước comment giống tiền lệ `tj-actions`: `@<sha> # <semver>` — semver để người đọc và Dependabot biết SHA tương ứng phiên bản nào.

---

## 4. Enforcement gate (chống tụt lại)

Pin một lần là chưa đủ — một PR sau có thể vô tình thêm `uses: some/action@v1`. Thêm một job CI **`actions-pinning`** chặn merge nếu **bất kỳ** action bên thứ ba được tham chiếu mà **không** có SHA 40-hex:

```bash
# Quét mọi `uses:` trong .github/workflows; bỏ qua local (./) và first-party
# (actions/*, github/*); mọi ref còn lại PHẢI có @<40 hex>.
```

- Cho phép `actions/*`, `github/*` theo tag (đúng quyết định §2).
- Cho phép local action `./…` (không phải chuỗi cung bên ngoài).
- Mọi ref khác thiếu `@<40-hex>` → in vi phạm + exit 1.
- Wire vào `ci-summary` (job "✅ CI Gate — All Passed") qua `needs:` để **chặn merge** thật sự, đồng bộ với cơ chế của các gate khác.

**Sabotage check (bắt buộc, giống N-2):** tạm thêm một ref bên thứ ba theo tag → gate phải **fail**; gỡ ra → pass. Ghi lại trong PR body.

---

## 5. Quan hệ với Dependabot

SHA-pin **không** vô hiệu Dependabot — ngược lại, hai cái bổ trợ:

- `.github/dependabot.yml` đã theo dõi ecosystem `github-actions` (weekly).
- Khi action được pin dạng `@<sha> # vX.Y.Z`, Dependabot cập nhật **cả SHA lẫn comment** trong một PR có diff → nâng cấp lại đi qua review thay vì âm thầm.
- Vì vậy chuỗi đúng là: **pin SHA (an toàn) + Dependabot (cập nhật có kiểm soát)**, không phải chọn một trong hai.

---

## 6. Bảo trì

- **Thêm action bên thứ ba mới:** phải pin SHA + comment semver ngay; gate sẽ chặn nếu quên.
- **Nâng cấp:** ưu tiên merge PR Dependabot (đã có diff SHA). Nếu pin tay, resolve qua `gh api repos/<owner>/<repo>/commits/<tag> --jq .sha` rồi cập nhật cả comment.
- **Thêm first-party mới** (`actions/*`, `github/*`): được phép theo tag (gate bỏ qua).
- **Xét siết first-party về SHA:** nếu sau này muốn đạt OpenSSF Scorecard "Pinned-Dependencies" tuyệt đối, mở rộng gate bỏ phần allowlist first-party và pin nốt — ghi nhận là escalation ngoài N-6.
