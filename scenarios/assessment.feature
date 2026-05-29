# Trắc nghiệm định hướng (RIASEC/VIPS/MBTI) — Holdout
# Spec: docs/spec.md §3.2 (FR-10..FR-15), CP-3 (dữ liệu nhạy cảm + audit)
# Build agent KHÔNG đọc file này.

Feature: Làm trắc nghiệm và xử lý dữ liệu nhạy cảm

  Scenario: Học sinh hoàn thành RIASEC và nhận kết quả kèm giải thích
    Given học sinh active đang ở /assessments/riasec
    When họ nộp đầy đủ câu trả lời qua POST /api/v1/assessments/riasec/submit
    Then API trả 201 với kết quả gồm nhóm RIASEC nổi trội và phần giải thích
    And kết quả KHÔNG kết luận cứng một nghề duy nhất (không có câu kiểu "bạn phải làm nghề X")
    And DB có row assessment_result với is_sensitive=true

  Scenario: Kết quả trắc nghiệm được mã hóa at-rest (không lưu plaintext)
    Given học sinh vừa nộp bài VIPS
    When đọc trực tiếp cột result_payload trong DB
    Then giá trị là ciphertext, không chứa nhãn kết quả ở dạng chữ thường đọc được (vd không thấy "realistic"/"investigative")

  Scenario: Mỗi lần đọc kết quả sinh đúng một bản ghi audit (CP-3)
    Given tồn tại một assessment_result của học sinh
    And số bản ghi audit nhạy cảm hiện tại là N
    When học sinh gọi GET /api/v1/me/assessments/{id}
    Then API trả 200 với kết quả đã giải mã
    And số bản ghi audit nhạy cảm trở thành N+1 với is_sensitive_access=true

  Scenario: Người dùng khác không đọc được kết quả của mình (trả 404)
    Given assessment_result thuộc về user U2
    When user U1 (khác) gọi GET /api/v1/me/assessments/{id_của_U2}
    Then API trả 404 (không xác nhận tồn tại)
    And không sinh bản ghi audit đọc-thành-công cho U1

  Scenario: Làm lại bài tạo phiên bản mới, không ghi đè bản cũ
    Given học sinh đã có một assessment_result RIASEC version=1
    When họ làm lại bài RIASEC và nộp
    Then DB có thêm row version=2
    And row version=1 vẫn còn nguyên (versioned, không ghi đè)

  Scenario: Ba bộ instrument đều khả dụng và phân biệt
    Given học sinh active
    When họ gọi GET /api/v1/assessments
    Then danh sách chứa các instrument type "riasec", "vips", "mbti"

  Scenario: Kết quả trắc nghiệm không xuất hiện trong log ứng dụng
    Given học sinh nộp bài MBTI
    When kiểm tra log NDJSON của backend cho request này
    Then log chỉ có metadata (event="assessment.submitted", loại, thời điểm)
    And log KHÔNG chứa nội dung kết quả hay điểm chi tiết
