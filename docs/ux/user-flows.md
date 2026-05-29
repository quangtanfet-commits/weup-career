# Thiết kế UX: Luồng Người dùng — WeUp Career

**Phiên bản:** 2.0.0 | **Ngày:** 2026-05-29
**Triết lý:** Rõ ràng, an toàn, tôn trọng quyền tự quyết. Hướng nghiệp là **đồng hành**, không phán xử.
**Thay thế:** v1.0.0 (UX Todo app)

---

## Nguyên tắc thiết kế (ràng buộc sản phẩm, không phải gợi ý)

1. **An toàn & hợp pháp trước tiên:** trẻ <16 không vào được nội dung hướng nghiệp đến khi có **đồng ý giám hộ** — và điều này được giải thích rõ ràng, không gây hoang mang.
2. **Không ép buộc:** mọi gợi ý ngành/nghề/phân luồng đều **kèm lý do** và nhấn mạnh "quyết định thuộc về bạn / giám hộ / giáo viên" (TT 16/2026, Luật 134/2025).
3. **Tôn trọng riêng tư:** kết quả trắc nghiệm là **nhạy cảm** — luôn có chỉ dẫn về ai xem được, và lối tắt **xuất/xóa** dữ liệu của mình.
4. **Phù hợp lứa tuổi:** ngôn ngữ & độ phức tạp phân tầng theo `school_level` (Tiểu học → người đi làm).
5. **Phản hồi tức thì** cho thao tác không nhạy cảm (điều hướng, lọc nghề); **không** optimistic cho gợi ý phân luồng.
6. **Keyboard-first & WCAG 2.1 AA** xuyên suốt.

---

## Luồng 1: Onboarding + Cổng tuổi & Đồng ý giám hộ

```mermaid
flowchart TD
    START([Mở app]) --> LOGIN["/login\nEmail + Password\nLink: 'Tạo tài khoản'"]
    LOGIN --> NEW{Người mới?}
    NEW -->|Có| REG["/register\nEmail + Password + Ngày sinh\n(password strength)"]
    REG --> AGE{age_band?}
    AGE -->|"≥16"| ACTIVE["account=active\n→ Dashboard hướng nghiệp"]
    AGE -->|"<16"| GATE["account=pending_guardian_consent\nMàn hình thân thiện:\n'Cần người thân đồng ý để bắt đầu'"]
    GATE --> INVITE["Nhập email/SĐT người giám hộ\n→ gửi lời mời"]
    INVITE --> WAIT["Trạng thái chờ\n(có thể khám phá nội dung CÔNG KHAI:\nthư viện nghề — không cần dữ liệu cá nhân)"]
    WAIT --> CONSENT["Giám hộ xác nhận (email/VNeID)"]
    CONSENT --> UNLOCK["account=active\n→ mở khóa trắc nghiệm & gợi ý"]
    NEW -->|Không| FILL["Đăng nhập"]
    FILL --> ROUTE{account_status}
    ROUTE -->|active| DASH["Dashboard"]
    ROUTE -->|pending| GATE
    FILL --> ERR["Lỗi inline: 'Email hoặc mật khẩu không đúng' (generic)"]
```

> Trẻ <16 **vẫn xem được nội dung công khai** (thư viện nghề) khi chờ consent — chỉ phần xử lý dữ liệu cá nhân (trắc nghiệm/gợi ý) bị khóa. Tránh cảm giác "bị chặn cụt".

---

## Luồng 2: Làm trắc nghiệm định hướng (RIASEC / VIPS / MBTI)

```mermaid
flowchart TD
    DASH[Dashboard] --> PICK["Chọn bộ test:\nRIASEC · VIPS · MBTI"]
    PICK --> GATE{consent OK?}
    GATE -->|"<16 chưa consent"| BLOCK["Màn hình: cần đồng ý giám hộ\n(nút gửi lại lời mời)"]
    GATE -->|OK| INTRO["Giới thiệu: mục đích, ~thời lượng,\nlưu ý 'kết quả là để hiểu bản thân, không phán xử'"]
    INTRO --> DOING["Làm bài (progress bar, lưu nháp)"]
    DOING --> SUBMIT["Nộp bài"]
    SUBMIT --> RESULT["Kết quả + GIẢI THÍCH\n• nhóm RIASEC nổi trội\n• liên hệ nhóm nghề (gợi mở, không chốt 1 nghề)\n• badge 'Dữ liệu riêng tư của bạn'"]
    RESULT --> ACTIONS["Hành động: Xem nghề liên quan ·\nLưu vào hồ sơ · Xuất · Xóa"]
    RESULT --> SENS["Chỉ dẫn quyền riêng tư:\n'Ai xem được kết quả này?'\n(bạn; giám hộ nếu <16; counselor nếu bạn cho phép)"]
```

---

## Luồng 3: Khám phá thư viện nghề (Điều 5a)

```mermaid
flowchart TD
    LIB["Thư viện nghề"] --> FILTER["Lọc: nhóm RIASEC · lĩnh vực · trình độ đào tạo\n(THPT/GDNN/trường trung học nghề/ĐH)"]
    FILTER --> RESULT["Danh sách nghề (tức thì, cache công khai)"]
    RESULT --> DETAIL["Chi tiết nghề:\nmô tả · năng lực & phẩm chất cần\nđiều kiện đào tạo · cơ hội việc làm · xu hướng"]
    DETAIL --> LINK["Liên kết: 'Nghề này hợp với hồ sơ của bạn?'\n→ đối chiếu kết quả test (nếu có)"]
    DETAIL --> RELATED["Nghề liên quan · con đường học tập"]
```

---

## Luồng 4: Bảng tiến bộ năng lực (2 trục K-A-R × giai đoạn)

```mermaid
flowchart TD
    PROG["Dashboard tiến bộ"] --> TREE["Cây 12 năng lực (3 lĩnh vực ABCD)"]
    TREE --> CELL["Mỗi năng lực hiển thị:\n• giai đoạn phát triển (Awareness/Exploration/Planning)\n• độ sâu đạt được (K → A → R)"]
    CELL --> DETAIL["Chi tiết năng lực:\nchỉ báo đã đạt · hoạt động gợi ý để tiến mức"]
    PROG --> PHASE["Thanh giai đoạn theo cấp lớp\n(học sinh: gắn school_level;\nngười đi làm: nhiều giai đoạn song song)"]
```

> Trục độ sâu hiển thị theo ngôn ngữ VN: **Nhận biết → Thực hiện/Vận dụng → Phản tư** (khớp CTGDPT 2018).

---

## Luồng 5: Xem gợi ý nghề/lộ trình (Human-in-the-loop)

```mermaid
flowchart TD
    REQ["Yêu cầu gợi ý lộ trình"] --> CARD["Thẻ gợi ý:\n• đề xuất ngành/nghề/hướng phân luồng\n• ⭐ LÝ DO (dựa trên test + tiến bộ + sở thích)\n• nhãn: 'Đây là gợi ý — quyết định thuộc về bạn'"]
    CARD --> CHOICE{"Người xem quyết định"}
    CHOICE -->|Chấp nhận| ACCEPT["Đưa vào lộ trình cá nhân\n(ghi confirmed_by)"]
    CHOICE -->|Từ chối| REJECT["Ẩn; có thể yêu cầu gợi ý khác"]
    CHOICE -->|Để sau| DEFER["Lưu lại xem sau"]
    CARD --> WHO["Nếu <16: gợi ý cũng hiển thị cho giám hộ\nNếu trong trường: có thể chia sẻ với counselor"]
```

> ⛔ Không có nút "tự động áp dụng". Hệ thống **không** chuyển gợi ý thành lộ trình khi chưa có người xác nhận (CP-5).

---

## Luồng 6: Counselor — tư vấn 3 tầng

```mermaid
flowchart TD
    CONSOLE["Bảng counselor (theo trường)"] --> LIST["DS học sinh được phân công\n(chỉ trong school_id của mình)"]
    LIST --> VIEW["Xem tiến bộ năng lực (đã gỡ chi tiết nhạy cảm theo quyền)"]
    VIEW --> TIER{"Mức hỗ trợ"}
    TIER -->|Tier 1| MASS["Nội dung đại trà / lớp"]
    TIER -->|Tier 2| GROUP["Hoạt động nhóm mục tiêu"]
    TIER -->|Tier 3| INDIV["Phiên tư vấn cá nhân\n(ghi CounselingSession)"]
    INDIV --> WELLBEING["Liên kết module sức khỏe tinh thần (NL4)\nkhi học sinh có dấu hiệu cần hỗ trợ"]
```

---

## Bố cục trang

### Trang Đăng nhập / Đăng ký
```
┌───────────────────────────────────────────┐
│              WeUp Career                    │
│         (Hướng nghiệp cùng bạn)            │
│        ┌──────────────────────┐            │
│        │  Chào mừng trở lại    │            │
│        │  Email  [__________]  │            │
│        │  Mật khẩu [________]  │            │
│        │  [     Đăng nhập    ] │            │
│        │  Chưa có tài khoản?   │            │
│        │  Tạo tài khoản        │            │
│        └──────────────────────┘            │
└───────────────────────────────────────────┘
```

### Dashboard học sinh
```
┌───────────────────────────────────────────────────────────┐
│  WeUp Career                         hocsinh@email  ▾       │
├───────────────────────────────────────────────────────────┤
│  Tôi là ai?   │  Tôi muốn đi đâu?  │  Đến đó bằng cách nào? │
│  (trắc nghiệm)│  (khám phá nghề)   │  (lộ trình & gợi ý)   │
├───────────────────────────────────────────────────────────┤
│  Tiến bộ năng lực:  [▓▓▓░░] Khám phá bản thân (A)           │
│                     [▓▓░░░] Thông tin nghề (K)              │
│  Gợi ý gần đây:  "Nhóm Investigative nổi trội — xem ngành…" │
│                  [Xem lý do]  [Chấp nhận] [Để sau]          │
│  🔒 Kết quả trắc nghiệm là dữ liệu riêng tư của bạn.        │
└───────────────────────────────────────────────────────────┘
```

---

## Thiết kế khả năng tiếp cận (Accessibility — WCAG 2.1 AA)

| Yêu cầu | Hiện thực |
|---|---|
| Tương phản ≥4.5:1 | Tailwind tokens đã test |
| Điều hướng bàn phím | Mọi phần tử reachable bằng Tab; focus ring rõ |
| Screen reader | Radix UI + `aria-*` |
| Không dùng màu đơn lẻ truyền tin | Giai đoạn/độ sâu hiển thị bằng text + icon + màu |
| Lỗi gắn với field | `aria-describedby` |
| Giảm chuyển động | `prefers-reduced-motion` tắt animation |
| Ngôn ngữ phù hợp lứa tuổi | Nội dung phân tầng theo `school_level` |

### Phím tắt
| Phím | Hành động |
|---|---|
| `/` | Focus ô tìm kiếm nghề |
| `Escape` | Hủy/đóng panel hiện tại |
| `g` rồi `a` | Tới Trắc nghiệm |
| `g` rồi `c` | Tới Thư viện nghề |
| `g` rồi `p` | Tới Tiến bộ |

---

## Responsive
| Breakpoint | Layout |
|---|---|
| Mobile (<640px) | 1 cột; 3 câu hỏi ECG xếp dọc; filter nghề thu gọn |
| Tablet (640–1024px) | Như desktop, spacing chặt hơn |
| Desktop (>1024px) | Layout đầy đủ; max-width nội dung đọc tốt |
| Wide (>1280px) | Sidebar cây năng lực (tùy chọn) |

---

## Micro-interactions
| Tương tác | Animation | Thời lượng |
|---|---|---|
| Hoàn thành 1 bước test | progress fill | 200ms |
| Đạt mức năng lực mới (K→A→R) | badge pop + confetti nhẹ | 250ms |
| Mở thẻ gợi ý | slide + fade | 150ms |
| Lọc nghề | list reposition | 200ms |
| Toast | slide up | 150ms |

Tôn trọng `prefers-reduced-motion: reduce` — chuyển thành đổi trạng thái tức thì.
