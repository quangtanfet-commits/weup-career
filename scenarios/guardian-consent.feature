# Đồng ý giám hộ (<16) — Holdout
# Spec: docs/spec.md §3.1 (FR-02..FR-04), CP-1, CP-2
# Build agent KHÔNG đọc file này.

Feature: Vòng đời đồng ý của người giám hộ cho trẻ <16

  Scenario: Giám hộ xác nhận mở khóa xử lý dữ liệu (CP-1)
    Given học sinh <16 email="bao.tran@example.com" đang ở account_status="pending_guardian_consent"
    And học sinh đã mời giám hộ qua POST /api/v1/guardians/invite với guardian_email="me.tran@example.com"
    When người giám hộ xác nhận qua POST /api/v1/guardians/consent (đã verify qua email)
    Then DB có row guardian_consent với status="active" cho học sinh này
    And user của học sinh chuyển account_status="active"
    And học sinh submit RIASEC sau đó nhận 201 (không còn 403)

  Scenario: Thu hồi đồng ý dừng xử lý dữ liệu mới (CP-2)
    Given học sinh <16 đang active nhờ guardian_consent status="active"
    When người giám hộ gọi POST /api/v1/guardians/consent/revoke
    Then DB có guardian_consent status="revoked" và user về account_status="pending_guardian_consent"
    And lần submit trắc nghiệm tiếp theo của học sinh trả 403 GUARDIAN_CONSENT_REQUIRED
    And các assessment_result đã tạo trước đó vẫn còn (thu hồi ≠ xóa)

  Scenario: Không cho phép tự đồng ý (self-consent)
    Given học sinh <16 cố nhập chính email của mình làm email giám hộ
    When họ gọi POST /api/v1/guardians/invite với guardian_email = email của chính mình
    Then API từ chối (4xx) và không tạo guardian_link verified
    And account_status vẫn "pending_guardian_consent"

  Scenario: Mọi thay đổi consent đều ghi audit
    Given học sinh <16 và một người giám hộ đã liên kết
    When giám hộ cấp rồi thu hồi đồng ý
    Then audit_log có các bản ghi action="guardian.consent.granted" và "guardian.consent.revoked" kèm actor và thời điểm

  Scenario: Cấp lại đồng ý sau khi thu hồi mở khóa trở lại
    Given guardian_consent đang ở status="revoked"
    When người giám hộ cấp lại đồng ý
    Then guardian_consent trở về status="active"
    And học sinh submit trắc nghiệm nhận 201

  Scenario: Trẻ <16 chờ consent vẫn xem được nội dung công khai
    Given học sinh <16 ở account_status="pending_guardian_consent"
    When họ gọi GET /api/v1/careers (thư viện nghề — nội dung công khai)
    Then API trả 200 với danh sách nghề
    And KHÔNG có dữ liệu cá nhân nào được xử lý
