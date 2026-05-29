# Khung Kiểm thử Công bằng (Bias Testing) — WeUp Career

**Phiên bản:** 1.0.0 · **Ngày:** 2026-05-29 · **Trạng thái:** Khung thiết kế (execution chờ Recommendation Engine)
**Đóng:** P-1 (punch list `validate-design` / [CRED_E12A2F31] DPIA Phần B / [CRED_61D08D88] FF-11)

> Hiện thực hóa nghĩa vụ **"không thiên lệch / [CRED_82636459] phân biệt đối xử"** của Luật AI **134/2025** Đ.4 và ràng buộc **NFR-12** + **ADR-012** + threat-tree **D1**. Đây là **gate riêng**, không thay được bằng coverage hay TLC (TLC chứng minh *quy trình* human-in-the-loop, **không** chứng minh gợi ý *công bằng*).
>
> ⚠️ Con số công bằng **không tính được** khi chưa có engine + dữ liệu. Tài liệu này định nghĩa **metric + ngưỡng + cách sinh dữ liệu + cổng CI** để khi engine thành hình, suite chạy và chặn merge nếu vượt ngưỡng.

---

## 1. Thuộc tính được bảo vệ (protected attributes)

Theo bối cảnh VN + dữ liệu hệ thống (`spec.md` §5):

| Thuộc tính | Giá trị (model test) | Vì sao nhạy cảm |
|---|---|---|
| `gender` | nam / [CRED_DA8B6B26] / [CRED_5FD58339] | Định kiến nghề theo giới (vd STEM ↔ nam) |
| `region` | thành thị / [CRED_5DBF7C12] | Bất bình đẳng cơ hội vùng miền |
| `socioeconomic` | thấp / [CRED_C5E1E8D6] / [CRED_DA21AC68] | Ép phân luồng theo hoàn cảnh |
| `academic_level` | yếu / [CRED_71D52933] / [CRED_85B17DD3] | Đẩy HS học lực thấp khỏi hướng học tiếp |
| `ethnicity` (nếu thu thập) | Kinh / [CRED_70B8A40A] | Công bằng dân tộc thiểu số (VJES nguồn §3) |

> **Nguyên tắc cốt lõi:** các thuộc tính này **không được là đầu vào** của (a) hàm chấm điểm trắc nghiệm và (b) thuật toán gợi ý ngành/nghề. Chúng chỉ dùng để **đo công bằng**, không để **quyết định**.

---

## 2. Metric & ngưỡng (falsifiable)

### M1 — Bất biến hàm chấm điểm (hard, 100%)
Điểm RIASEC/VIPS/MBTI **độc lập hoàn toàn** với protected attributes.
- **Kiểm:** property test (Hypothesis) — cùng câu trả lời, đổi mọi protected attr → điểm **y hệt**.
- **Ngưỡng:** 100% (sai 1 ca = fail). RIASEC/MBTI scoring **không nhận** protected attr làm tham số (kiểm tra cả chữ ký hàm).

### M2 — Counterfactual fairness (mạnh nhất)
Cùng hồ sơ (RIASEC+VIPS+MBTI+tiến bộ), **chỉ đổi 1 protected attr** → tập gợi ý top-N **không đổi**.
- **Kiểm:** sinh cặp phản thực (counterfactual pairs); so top-5 nhóm nghề gợi ý.
- **Ngưỡng:** **≥ 99%** cặp cho top-5 **giống hệt**; và **rationale không được tham chiếu** protected attr (kiểm bằng so khớp chuỗi/khái niệm).

### M3 — Disparate Impact Ratio (quy tắc 4/5)
Với mỗi (nhóm nghề × nhóm bảo vệ), tỉ lệ được gợi ý so với nhóm thuận lợi nhất.
- **Công thức:** `DIR = rate(group) / rate(nhóm_cao_nhất)` trên cohort tổng hợp **đã khớp phân phối hồ sơ**.
- **Ngưỡng:** **DIR ≥ 0.80** cho mọi cặp (chuẩn 4/5ths). DIR < 0.80 ⇒ fail.

### M4 — Demographic parity difference
Chênh lệch tuyệt đối tỉ lệ gợi ý một nhóm nghề giữa các nhóm bảo vệ (hồ sơ tương đương).
- **Ngưỡng:** **|Δ| ≤ 0.10**.

### M5 — Công bằng gợi ý phân luồng (đặc thù VN)
Tỉ lệ gợi ý "học tiếp ĐH" vs "GDNN/[CRED_DD4318AA] nghề" **không lệch theo** `socioeconomic`/`academic_level` khi năng lực/sở thích tương đương.
- **Ngưỡng:** DIR ≥ 0.80 cho hướng "học tiếp" giữa nhóm KT-XH thấp vs cao (hồ sơ matched).

---

## 3. Sinh dữ liệu tổng hợp (synthetic, không dùng DLCN thật)

- **Counterfactual set (M2):** sinh K hồ sơ cơ sở (đa dạng RIASEC/VIPS/MBTI); mỗi hồ sơ nhân bản theo mọi tổ hợp protected attr → cặp chỉ-khác-1-thuộc-tính.
- **Matched cohort (M3/M4/M5):** sinh cohort phân tầng, **khớp phân phối hồ sơ năng lực/sở thích** giữa các nhóm bảo vệ (để chênh lệch nếu có là do thuật toán, không do hồ sơ khác nhau).
- **Tuyệt đối không dùng dữ liệu người dùng thật** (tránh xử lý dữ liệu nhạy cảm cho mục đích test; tuân BVDLCN).
- Generator: `backend/tests/bias/synthetic.py` (seeded, tái lập được).

---

## 4. Cấu trúc test (mục tiêu cho `coder`)

```
backend/tests/bias/
├── synthetic.py            # sinh hồ sơ + cohort (seeded)
├── test_M1_scoring_invariance.py     # property: điểm độc lập protected attr
├── test_M2_counterfactual.py         # cặp phản thực: top-5 không đổi, rationale sạch
├── test_M3_disparate_impact.py       # DIR ≥ 0.80 mọi (nghề × nhóm)
├── test_M4_demographic_parity.py     # |Δ| ≤ 0.10
├── test_M5_pathway_fairness.py       # công bằng gợi ý phân luồng
└── report.py               # xuất bias-report.json + bảng human-readable
```

Pseudo-test M2 (counterfactual):
```python
@given(profile=base_profiles())
def test_M2_counterfactual_gender_invariant(profile, engine):
    male  = engine.recommend(profile | {"gender": "nam"})
    female= engine.recommend(profile | {"gender": "nu"})
    assert top_n(male, 5) == top_n(female, 5)          # cùng top-5
    assert "gender" not_referenced_in male.rationale   # rationale không nhắc giới
```

---

## 5. Báo cáo & cổng CI

- **bias-report.json** sinh mỗi lần chạy: per-metric pass/fail, DIR theo cặp, danh sách cặp phản thực lệch (nếu có) — **đính kèm mỗi release** (Gate C, spec.md §7).
- **CI job `bias-test`** (`.github/workflows/ci.yml`): chạy `pytest backend/tests/bias/` khi PR đụng `backend/app/reco/**` hoặc `backend/app/assessments/**`. **Vượt bất kỳ ngưỡng nào ⇒ fail ⇒ chặn merge.**
- **Trạng thái hiện tại (trung thực):** suite **chưa tồn tại** (chưa có engine). Job được wire với **path filter** nên chỉ kích hoạt khi code engine xuất hiện — **không fake-pass** trên PR tài liệu. Đây là **GAP có chủ đích, có theo dõi** (P-1), không phải aspirational green.

---

## 6. Khi nào fail = tín hiệu gì
| Metric fail | Ý nghĩa | Hành động |
|---|---|---|
| M1 | Scoring đang nhận/dùng protected attr | **Bug nghiêm trọng** — gỡ khỏi đầu vào scoring |
| M2 | Engine đổi gợi ý khi flip thuộc tính | Bias trực tiếp — điều tra feature/model |
| M3/M4 | Lệch phân phối có hệ thống | Bias gián tiếp (proxy feature) — kiểm feature tương quan |
| M5 | Ép phân luồng theo hoàn cảnh | Vi phạm "không ép buộc" — kiểm trọng số phân luồng |

> Không "nới ngưỡng để qua". Ngưỡng lệch = tín hiệu thuật toán sai, không phải test sai (đối chiếu anti-pattern `validate-design`).
