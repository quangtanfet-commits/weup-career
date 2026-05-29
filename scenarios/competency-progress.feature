# Mô hình năng lực 2 trục & tiến bộ K-A-R — Holdout
# Spec: docs/spec.md §3.3 (FR-20..FR-24), CP-8
# Build agent KHÔNG đọc file này.

Feature: Cây năng lực và tiến bộ trên trục độ sâu K-A-R

  Scenario: Cây 12 năng lực hiển thị đủ 3 lĩnh vực
    Given học sinh active
    When họ gọi GET /api/v1/competencies
    Then trả về 12 competency với code NL1…NL12 thuộc 3 area A/B/C
    And mỗi competency có dieu5_codes gắn kèm

  Scenario: Hoàn thành hoạt động nâng độ sâu từ K lên A
    Given học sinh đang ở depth_achieved="K" cho năng lực NL10
    When họ hoàn thành hoạt động được gắn nhãn (NL10, depth="A")
    Then GET /api/v1/me/progress cho thấy NL10 depth_achieved="A"
    And lịch sử learner_progress giữ cả bản ghi cũ (K) lẫn mới (A)

  Scenario: Độ sâu không bao giờ tụt lùi (CP-8)
    Given học sinh đã đạt depth_achieved="R" cho năng lực NL1
    When hệ thống xử lý một hoạt động gắn nhãn depth thấp hơn (K hoặc A) cho NL1
    Then depth_achieved hiển thị của NL1 vẫn là "R" (không giảm)
    And lịch sử vẫn append-only, không bản ghi nào bị xóa/sửa

  Scenario: Học sinh THCS mặc định ở giai đoạn Exploration nhưng cho phép lệch
    Given học sinh có school_level="lower_secondary"
    When họ xem dashboard tiến bộ
    Then dev_phase mặc định hiển thị "exploration"
    And học sinh vẫn có thể được đặt lệch sang phase khác cho một domain cụ thể

  Scenario: Người đi làm có nhiều giai đoạn phát triển song song (phi tuyến)
    Given người dùng user_type="working"
    When họ ở "planning" cho domain hiện tại và "awareness" cho một domain nghề mới
    Then GET /api/v1/me/progress trả về nhiều LearnerDomainPhase đồng thời cho cùng người dùng

  Scenario: Trục độ sâu hiển thị bằng ngôn ngữ CTGDPT 2018
    Given học sinh xem chi tiết một năng lực
    When giao diện render trục độ sâu
    Then nhãn hiển thị tương ứng "Nhận biết" (K), "Thực hiện/Vận dụng" (A), "Phản tư" (R)
