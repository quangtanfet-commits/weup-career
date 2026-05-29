# Phiên đăng nhập & token — Holdout
# Spec: docs/spec.md §3.1 (FR-05, FR-06), CP-7
# Build agent KHÔNG đọc file này.

Feature: Đăng nhập, làm mới và thu hồi token

  Scenario: Đăng nhập cấp access token + refresh cookie httpOnly
    Given tài khoản active email="an.le@example.com", password="Matkhau123"
    When người dùng POST /api/v1/auth/login với đúng thông tin
    Then API trả 200 với access_token trong body
    And response có Set-Cookie refresh_token kèm HttpOnly, Secure, SameSite=Strict
    And DB lưu refresh token dưới dạng hash SHA-256 (không lưu giá trị thô)

  Scenario: Sai mật khẩu trả lỗi generic (chống enumeration)
    Given tài khoản email="an.le@example.com" tồn tại
    When người dùng đăng nhập với password="SaiMatKhau"
    Then API trả 401 với error.code="INVALID_CREDENTIALS"
    And thông báo không tiết lộ email có tồn tại hay không

  Scenario: Refresh token đã thu hồi không lấy được access token mới (CP-7)
    Given một refresh token RT_OLD đã bị thu hồi do logout
    When client gọi POST /api/v1/auth/refresh với cookie RT_OLD
    Then API trả 401 TOKEN_EXPIRED
    And không cấp access token mới

  Scenario: Refresh xoay vòng — token cũ chết ngay khi token mới ra đời (CP-7)
    Given client có refresh token RT_OLD hợp lệ
    When client gọi /api/v1/auth/refresh thành công, nhận RT_NEW
    Then RT_OLD ở DB có revoked_at khác null
    And gọi /auth/refresh lại bằng RT_OLD trả 401
    And không có thời điểm nào hai refresh token cùng active cho phiên này

  Scenario: Access token hết hạn bị từ chối
    Given một access token đã quá 15 phút
    When client gọi GET /api/v1/auth/me bằng token đó
    Then API trả 401

  Scenario: Logout thu hồi refresh token phía server
    Given người dùng đang đăng nhập
    When họ gọi POST /api/v1/auth/logout
    Then refresh token tương ứng ở DB có revoked_at khác null
    And lần refresh kế tiếp bằng token đó trả 401
