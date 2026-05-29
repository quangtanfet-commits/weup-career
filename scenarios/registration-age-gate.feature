# Đăng ký & Cổng tuổi — Holdout
# Spec: docs/spec.md §3.1 (FR-01, FR-02), CP-1
# Build agent KHÔNG đọc file này.

Feature: Đăng ký tài khoản và cổng tuổi (age gate)

  Scenario: Người ≥16 đăng ký thành công và dùng được ngay
    Given trang đăng ký tại http://localhost/register
    When người dùng đăng ký với email="an.le@example.com", password="Matkhau123", date_of_birth="2008-03-10"
    Then API trả 201 và body chứa account_status="active"
    And DB có một row user với email="an.le@example.com", age_band="16_17"
    And người dùng được điều hướng tới /dashboard

  Scenario: Người <16 đăng ký sẽ bị đưa vào trạng thái chờ giám hộ
    Given trang đăng ký
    When người dùng đăng ký với email="bao.tran@example.com", password="Matkhau123", date_of_birth="2013-09-01"
    Then API trả 201 và body chứa account_status="pending_guardian_consent"
    And DB có row user với age_band="under_16"
    And giao diện hiển thị màn hình "Cần người thân đồng ý để bắt đầu"

  Scenario: Trẻ <16 chưa có consent không gọi được route dữ liệu hướng nghiệp
    Given người dùng <16 vừa đăng ký, account_status="pending_guardian_consent"
    When họ gọi POST /api/v1/assessments/riasec/submit
    Then API trả 403 với error.code="GUARDIAN_CONSENT_REQUIRED"
    And DB KHÔNG có row assessment_result nào cho người dùng này

  Scenario: Đăng ký trùng email bị từ chối
    Given đã tồn tại tài khoản email="an.le@example.com"
    When người dùng đăng ký lại với email="an.le@example.com"
    Then API trả 409
    And không tạo thêm row user mới

  Scenario: Mật khẩu yếu bị từ chối ngay khi đăng ký
    Given trang đăng ký
    When người dùng đăng ký với password="123"
    Then API trả 422 (hoặc 400) với thông báo yêu cầu ≥8 ký tự, hoa/thường/số
    And không tạo row user

  Scenario: Email được chuẩn hóa lowercase/trim trước khi lưu
    Given trang đăng ký
    When người dùng đăng ký với email="  An.Le@Example.COM  "
    Then DB lưu email="an.le@example.com"
