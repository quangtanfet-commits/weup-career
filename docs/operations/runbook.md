# Operations Runbook — WeUp Career

**Phiên bản:** 2.0.0 | **Ngày:** 2026-05-29
**Đối tượng:** Operators, On-call Engineers
**Thay thế:** v1.0.0 (runbook Todo app)

> Lưu ý đặc thù: dữ liệu nhạy cảm (kết quả trắc nghiệm) **mã hóa bằng `FIELD_ENCRYPTION_KEY`**; **audit store append-only** (CP-3); xử lý **yêu cầu chủ thể dữ liệu** & **đồng ý giám hộ** là nghĩa vụ pháp lý. Đường dẫn dữ liệu: `/var/lib/weup`.

---

## Tham chiếu nhanh
```bash
docker compose ps
docker compose logs -f backend
curl http://localhost/api/v1/health
curl http://localhost/api/v1/ready
docker compose restart backend
docker compose down && docker compose up -d        # giữ data
docker compose pull && docker compose up -d         # cập nhật image
```

---

## Runbook 1: Triển khai phiên bản mới
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps backend  # rolling, downtime <30s
./scripts/smoke-test.sh
# Nếu fail — rollback:
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps backend \
  --image ghcr.io/org/weup-career-backend:PREVIOUS_SHA
./scripts/smoke-test.sh
```

---

## Runbook 2: Phục hồi CSDL

### Triệu chứng: backend trả 503
```bash
ls -la /var/lib/weup/data/app.db
sqlite3 /var/lib/weup/data/app.db "PRAGMA integrity_check;"   # mong đợi: ok
# Nếu hỏng — phục hồi từ backup:
cp /var/lib/weup/backup/app.db.latest /var/lib/weup/data/app.db
docker compose restart backend
curl http://localhost/api/v1/ready
```

> ⚠️ **Phục hồi DB phải đồng bộ phiên bản với `FIELD_ENCRYPTION_KEY`.** Nếu backup DB cũ hơn lần xoay khóa, kết quả trắc nghiệm nhạy cảm có thể **không giải mã được**. Luôn ghi `key_version` cùng backup (xem Runbook 5).

### Triệu chứng: SQLite locked
```bash
lsof /var/lib/weup/data/app.db
docker compose restart backend   # nếu là stale lock từ process crash
```

---

## Runbook 3: Tỉ lệ lỗi 5xx cao
```bash
docker compose logs --since=15m backend | grep '"level":"error"' | jq .
docker stats --no-stream
docker inspect weup_backend_1 | jq '.[0].State'
# Nếu OOM — tăng memory limit trong docker-compose.prod.yml (512MB → 1GB)
docker compose restart backend
```
> ⚠️ Nếu log cho thấy **lỗi ghi audit** khi đọc dữ liệu nhạy cảm: hệ thống **fail-closed** (từ chối đọc để giữ CP-3) — đây là hành vi đúng, **không** vô hiệu hóa audit để "chữa". Điều tra audit store/disk.

---

## Runbook 4: Xoay `SECRET_KEY` (JWT)
**Tác động:** mọi access token hiện tại vô hiệu; người dùng phải đăng nhập lại.
```bash
openssl rand -hex 32 > /var/lib/weup/secrets/secret_key.txt
chmod 600 /var/lib/weup/secrets/secret_key.txt
docker compose restart backend
curl http://localhost/api/v1/health
# Thông báo người dùng: "Chúng tôi đã cập nhật bảo mật, vui lòng đăng nhập lại."
```

---

## ⭐ Runbook 5: Xoay `FIELD_ENCRYPTION_KEY` (dữ liệu nhạy cảm)
**Tác động:** khóa giải mã kết quả trắc nghiệm — **không xoay tùy tiện**. Cần chiến lược re-encrypt versioned.
```bash
# 1. Sinh khóa mới + gán key_version mới
openssl rand -hex 32 > /var/lib/weup/secrets/field_encryption_key.v2.txt
# 2. Chạy job re-encrypt: giải mã bằng key cũ (theo key_version trên bản ghi) → mã hóa lại bằng key mới
docker compose exec backend python -m app.tools.reencrypt --from v1 --to v2
# 3. Xác minh: mọi AssessmentResult đã key_version=v2 và giải mã được
docker compose exec backend python -m app.tools.verify_encryption --key-version v2
# 4. Lưu trữ AN TOÀN cả 2 khóa cho tới khi chắc chắn (rollback); chỉ hủy key cũ sau khi verify
```
> Khóa lưu ở secret manager/HSM; backup khóa **độc lập** với backup DB nhưng **ghi nhận key_version** để khớp khi phục hồi.

---

## ⭐ Runbook 6: Yêu cầu chủ thể dữ liệu (Luật 91/2025)
Truy cập / xuất / xóa dữ liệu cá nhân — với trẻ <16 do **người giám hộ** thực hiện.
```bash
# Xuất dữ liệu cá nhân của 1 user (gồm kết quả đã giải mã, có audit)
docker compose exec backend python -m app.tools.export_user --user-id <UUID> --requested-by <actor>
# Xóa (soft → purge sau cửa sổ khôi phục); ghi audit
docker compose exec backend python -m app.tools.delete_user --user-id <UUID> --requested-by <actor>
```
> Mọi thao tác này **bắt buộc ghi audit** (actor, lý do, thời điểm). Xác minh quyền: chủ thể hoặc giám hộ đã verified.

---

## Runbook 7: Rate limit dương tính giả
```bash
docker compose logs --since=15m nginx | grep "limiting requests"
# NAT/proxy trường học dùng chung IP → cân nhắc per-user limit thay per-IP
# (trường học là kênh B2B2C — nhiều HS sau 1 IP)
```
> Lưu ý: trường học truy cập đồng loạt (1 lớp làm trắc nghiệm cùng lúc) dễ chạm per-IP limit — ưu tiên **per-user** cho route hướng nghiệp.

---

## Runbook 8: Sao lưu
```bash
#!/bin/bash  # scripts/backup.sh — cron hằng ngày
DATE=$(date +%Y%m%d-%H%M%S)
SRC=/var/lib/weup/data/app.db
BACKUP_DIR=/var/lib/weup/backup
sqlite3 $SRC ".backup '$BACKUP_DIR/app.db.$DATE'"
# Ghi kèm key_version hiện hành để khớp khi phục hồi
cat /var/lib/weup/secrets/field_encryption_key.version > "$BACKUP_DIR/app.db.$DATE.keyver"
# Backup audit store RIÊNG, immutable
sqlite3 /var/lib/weup/data/audit.db ".backup '$BACKUP_DIR/audit.db.$DATE'"
ls -t $BACKUP_DIR/app.db.* | tail -n +8 | xargs rm -f   # giữ 7 bản
```

---

## Checklist giám sát hằng ngày
```bash
docker compose ps | grep -v "Up"                                   # rỗng = ok
df -h /var/lib/weup/data/
docker compose logs --since=24h backend | grep '"level":"error"' | wc -l   # alert nếu >100
curl -f http://localhost/api/v1/health && curl -f http://localhost/api/v1/ready
ls -la /var/lib/weup/backup/ | head -5
# Đối chiếu CP-3: sensitive_access_total == audit_writes_total (Prometheus)
curl -s http://localhost/metrics | grep -E 'sensitive_access_total|audit_writes_total'
```

---

## Ngưỡng cảnh báo
| Metric | Warning | Critical | Hành động |
|---|---|---|---|
| 5xx rate | >0.1% | >1% | Xem log, restart nếu treo |
| p99 latency | >500ms | >2000ms | Kiểm tra query DB / [CRED_F4ECCB8A] |
| Memory | >400MB | >500MB | Restart, kiểm tra leak |
| Disk | >70% | >85% | Rotate log, dọn backup cũ |
| Health fail | 2 liên tiếp | 5 liên tiếp | Page on-call |
| **sensitive_access ≠ audit_writes** | bất kỳ lệch | lệch kéo dài | **Điều tra ngay (vi phạm CP-3)** |
| **Lỗi ghi audit** | >0 | kéo dài | Fail-closed đang chặn đọc — điều tra audit store |
