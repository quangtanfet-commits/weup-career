# Thư viện nghề, kỹ năng chọn nghề & trải nghiệm — Holdout
# Spec: docs/spec.md §3.4–3.6 (FR-30..FR-33, FR-40..FR-42, FR-50) — Điều 5 a/c/d
# Build agent KHÔNG đọc file này.

Feature: Thông tin nghề nghiệp, ra quyết định và trải nghiệm nghề

  Scenario: Xem chi tiết một nghề đầy đủ thông tin Điều 5a
    Given thư viện nghề có nghề "Kỹ sư phần mềm"
    When người dùng gọi GET /api/v1/careers/{id}
    Then trả về mô tả, năng lực & phẩm chất cần, điều kiện đào tạo, cơ hội việc làm, xu hướng thị trường
    And dữ liệu gắn dieu5_code="a" và có nguồn minh bạch (source_ref)

  Scenario: Lọc nghề theo nhóm RIASEC
    Given người dùng đã có kết quả RIASEC nổi trội nhóm "Investigative"
    When họ gọi GET /api/v1/careers?riasec=I
    Then danh sách trả về chỉ gồm các nghề có riasec_codes chứa "I"

  Scenario: Thư viện nghề bao gồm nhánh GDNN và trường trung học nghề
    Given người dùng xem các hướng đào tạo sau THCS
    When họ lọc theo trình độ đào tạo
    Then kết quả có nhánh "GDNN" và loại cơ sở "trường trung học nghề" (Luật GDNN 124/2025)

  Scenario: Công cụ so sánh ngành theo tiêu chí cá nhân (Điều 5c)
    Given người dùng chọn 2 nghề để so sánh
    When họ mở công cụ so sánh theo giá trị/sở thích/năng lực/điều kiện
    Then giao diện hiển thị bảng đối chiếu 2 nghề theo từng tiêu chí

  Scenario: Hoàn thành bài ra quyết định ghi nhận tiến bộ năng lực NL10
    Given người dùng làm bài tập tình huống ra quyết định nghề
    When họ hoàn thành
    Then learner_progress cập nhật cho năng lực NL10 (dieu5_code="c")

  Scenario: Nội dung trải nghiệm "một ngày làm nghề" (Điều 5d)
    Given thư viện có nội dung trải nghiệm cho nghề "Điều dưỡng"
    When người dùng mở nội dung trải nghiệm
    Then nội dung gắn dieu5_code="d" và liên kết năng lực NL5/NL9

  Scenario: Nội dung nghề có phiên bản (versioned)
    Given một CareerProfile được cập nhật
    When biên tập viên xuất bản phiên bản mới
    Then phiên bản cũ vẫn truy vết được; bản hiển thị là bản published mới nhất
