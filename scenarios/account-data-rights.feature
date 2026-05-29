# Quyền chủ thể dữ liệu & quản lý tài khoản — Holdout
# Spec: docs/spec.md §3.2/§3.10 (FR-14, FR-91, FR-92) — Luật 91/2025
# Build agent KHÔNG đọc file này.

Feature: Xuất/xóa dữ liệu cá nhân và quản lý tài khoản

  Scenario: Người dùng xuất dữ liệu cá nhân của mình
    Given người dùng active có kết quả trắc nghiệm và tiến bộ năng lực
    When họ yêu cầu xuất dữ liệu cá nhân
    Then hệ thống cung cấp bản xuất gồm hồ sơ + kết quả (đã giải mã) + tiến bộ
    And thao tác xuất được ghi audit

  Scenario: Người dùng xóa kết quả trắc nghiệm của mình (FR-14)
    Given người dùng có một assessment_result
    When họ gọi DELETE /api/v1/me/assessments/{id}
    Then kết quả không còn truy cập được qua API
    And thao tác xóa được ghi audit

  Scenario: Đổi mật khẩu yêu cầu mật khẩu hiện tại (FR-91)
    Given người dùng đang đăng nhập
    When họ đổi mật khẩu nhưng nhập sai mật khẩu hiện tại
    Then API trả 4xx và mật khẩu không thay đổi

  Scenario: Yêu cầu xóa tài khoản là soft delete có cửa sổ khôi phục (FR-92)
    Given người dùng yêu cầu xóa tài khoản
    When hệ thống xử lý
    Then user chuyển account_status="deleted" (soft) với cửa sổ khôi phục
    And dữ liệu bị purge cứng sau khi hết cửa sổ khôi phục

  Scenario: Với trẻ <16, người giám hộ thực hiện quyền xuất/xóa thay trẻ
    Given trẻ <16 đã liên kết giám hộ verified
    When người giám hộ yêu cầu xuất/xóa dữ liệu của trẻ
    Then hệ thống cho phép và ghi audit với actor là người giám hộ

  Scenario: Mọi thao tác quyền chủ thể dữ liệu đều ghi audit
    Given chuỗi thao tác xuất + xóa
    When kiểm tra audit_log
    Then có các bản ghi tương ứng kèm actor, lý do và thời điểm
