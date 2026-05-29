# Gợi ý nghề/lộ trình — Human-in-the-loop — Holdout
# Spec: docs/spec.md §3.7 (FR-60..FR-63), CP-5, CP-6
# Build agent KHÔNG đọc file này.

Feature: Gợi ý có giải thích và con người ra quyết định

  Scenario: Gợi ý luôn kèm lý do và cần xác nhận của người (CP-6)
    Given học sinh active đã có kết quả RIASEC và tiến bộ năng lực
    When họ gọi POST /api/v1/recommendations
    Then API trả 201 với recommendation có rationale khác rỗng
    And requires_human_confirmation=true và status="proposed"
    And giao diện hiển thị câu "Đây là gợi ý — quyết định thuộc về bạn/giám hộ/giáo viên"

  Scenario: Không tạo được gợi ý nếu thiếu lý do (CP-6)
    Given engine sinh ra một đề xuất nhưng rationale rỗng
    When hệ thống cố lưu recommendation
    Then thao tác bị từ chối (4xx/không tạo row)
    And không có recommendation nào với rationale rỗng tồn tại trong DB

  Scenario: Hệ thống không tự áp dụng phân luйổng (CP-5)
    Given một recommendation đang ở status="proposed"
    When không có người nào xác nhận
    Then lộ trình cá nhân của học sinh KHÔNG được hệ thống tự động thay đổi
    And không tồn tại endpoint cho phép tự áp dụng khi chưa confirmed_by

  Scenario: Người dùng chấp nhận gợi ý thì mới đưa vào lộ trình (CP-5)
    Given recommendation status="proposed"
    When người dùng gọi POST /api/v1/recommendations/{id}/confirm với decision="accepted"
    Then status chuyển "accepted" và confirmed_by là id người dùng
    And gợi ý được đưa vào lộ trình cá nhân

  Scenario: Người dùng từ chối gợi ý
    Given recommendation status="proposed"
    When người dùng confirm với decision="rejected"
    Then status="rejected" và gợi ý không vào lộ trình

  Scenario: Lưu vết đầy đủ để giải trình AI
    Given một chu trình gợi ý → xác nhận
    When kiểm tra audit_log
    Then có bản ghi "recommendation.created" và "recommendation.confirmed" kèm confirmed_by và decision

  Scenario: Gợi ý của trẻ <16 cũng hiển thị cho người giám hộ
    Given học sinh <16 active nhận một gợi ý
    When người giám hộ đã liên kết mở hồ sơ của trẻ
    Then người giám hộ xem được gợi ý kèm lý do và có thể tham gia xác nhận
