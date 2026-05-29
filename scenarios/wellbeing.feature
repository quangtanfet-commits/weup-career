# Module Sức khỏe tinh thần (ABCD NL4) — Holdout
# Spec: docs/spec.md §3.8 (FR-70, FR-71)
# Build agent KHÔNG đọc file này.

Feature: Sức khỏe tinh thần và đường dẫn tới hỗ trợ

  Scenario: Truy cập nội dung quản lý stress gắn năng lực NL4
    Given học sinh active
    When họ mở module sức khỏe tinh thần
    Then nội dung hiển thị (quản lý stress, cân bằng, nhận biết khi cần hỗ trợ) gắn năng lực NL4, dieu5_code="b"

  Scenario: Có đường dẫn an toàn tới counselor (Tier 3)
    Given học sinh đang xem module sức khỏe tinh thần
    When họ chọn "Cần được hỗ trợ"
    Then hệ thống cung cấp đường dẫn tới tư vấn học đường (Tier 3)
    And hệ thống KHÔNG đưa ra chẩn đoán y tế

  Scenario: Hoàn thành nội dung ghi nhận tiến bộ NL4
    Given học sinh hoàn thành một hoạt động NL4 ở mức "Nhận biết"
    When họ kết thúc hoạt động
    Then learner_progress cập nhật năng lực NL4 depth_achieved="K"

  Scenario: Nội dung phù hợp lứa tuổi theo school_level
    Given học sinh Tiểu học (school_level="primary") và học sinh THPT (school_level="upper_secondary")
    When mỗi người mở module NL4
    Then nội dung hiển thị được phân tầng theo school_level tương ứng

  Scenario: Không thu thập dữ liệu sức khỏe như dữ liệu y tế
    Given học sinh tương tác với module sức khỏe tinh thần
    When kiểm tra dữ liệu lưu
    Then hệ thống không lưu chẩn đoán/hồ sơ y tế; chỉ ghi tiến bộ năng lực NL4
