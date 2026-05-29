# Tư vấn học đường 3 tầng & RBAC quan hệ — Holdout
# Spec: docs/spec.md §3.9 (FR-80..FR-83), CP-4
# Build agent KHÔNG đọc file này.

Feature: Counselor, school admin và phân quyền theo trường

  Scenario: Counselor xem được học sinh trong trường mình
    Given counselor C thuộc school_id="S1"
    And học sinh H thuộc school_id="S1"
    When C gọi GET /api/v1/school/S1/students
    Then API trả 200 và danh sách chứa học sinh H

  Scenario: Counselor KHÔNG truy cập học sinh ngoài trường mình (CP-4)
    Given counselor C thuộc school_id="S1"
    And học sinh K thuộc school_id="S2"
    When C cố gọi GET /api/v1/school/S2/students
    Then API trả 403 Forbidden

  Scenario: Counselor chỉ thấy dữ liệu đã gỡ nhạy cảm theo quyền
    Given counselor C xem tiến bộ của học sinh H trong trường
    When C mở hồ sơ tiến bộ của H
    Then C thấy tiến bộ năng lực nhưng KHÔNG thấy payload kết quả trắc nghiệm thô nếu không được cấp quyền
    And mỗi lần truy cập dữ liệu nhạy cảm (nếu có) đều sinh audit (CP-3)

  Scenario: Ghi phiên tư vấn cá nhân (Tier 3)
    Given counselor C và học sinh H cùng school_id="S1"
    When C gọi POST /api/v1/counseling/sessions với student_id=H, tier=3, notes="..."
    Then API trả 201 và DB có counseling_session tier=3

  Scenario: School admin quản lý lớp/học sinh trong phạm vi trường
    Given school_admin A của school_id="S1"
    When A tạo lớp và gán học sinh trong S1
    Then thao tác thành công; A không thao tác được trên school_id="S2"

  Scenario: Guardian chỉ xem được trẻ đã liên kết & verified
    Given guardian G đã liên kết verified với trẻ T1, nhưng chưa liên kết trẻ T2
    When G gọi GET /api/v1/users/{T2}/progress
    Then API trả 403 hoặc 404 (không lộ dữ liệu T2)
