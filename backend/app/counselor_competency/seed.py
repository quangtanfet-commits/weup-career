"""Seed the counselor-competency framework with TT 18/2025-grounded entries.

Six competency codes (CC-01..CC-06) covering the counseling-practice framework
for school guidance counselors (tư vấn tâm lý/hướng nghiệp học đường):
  1. Professional ethics and boundaries
  2. Listening and counseling skills
  3. Understanding and applying assessment tools (RIASEC, VIPS, MBTI)
  4. Data safety and BVDLCN compliance
  5. Recognizing referral signals
  6. Career information and pathway knowledge

Source: TT 18/2025/TT-BGDĐT — Quy định công tác tư vấn tâm lý, hướng nghiệp
học đường.

Idempotent: skips any code already present. CLI: ``python -m app.counselor_competency.seed``.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

SOURCE = "TT 18/2025/TT-BGDĐT"

FRAMEWORK: list[dict[str, str]] = [
    {
        "code": "CC-01",
        "name_vi": "Đạo đức nghề và ranh giới chuyên môn",
        "name_en": "Professional Ethics and Boundaries",
        "description": (
            "Hiểu và thực hành các nguyên tắc đạo đức nghề tư vấn học đường: bảo mật, "
            "không phán xét, không tạo phụ thuộc, nhận diện xung đột lợi ích và duy trì "
            "ranh giới chuyên môn rõ ràng."
        ),
        "source_ref": SOURCE,
    },
    {
        "code": "CC-02",
        "name_vi": "Kỹ năng lắng nghe và tư vấn",
        "name_en": "Listening and Counseling Skills",
        "description": (
            "Sử dụng thành thạo kỹ thuật lắng nghe tích cực, đặt câu hỏi mở, phản chiếu, "
            "tóm lược và điều phối cảm xúc trong buổi tư vấn cá nhân và nhóm."
        ),
        "source_ref": SOURCE,
    },
    {
        "code": "CC-03",
        "name_vi": "Hiểu và sử dụng công cụ trắc nghiệm",
        "name_en": "Assessment Tool Literacy",
        "description": (
            "Có kiến thức về lý thuyết nền (Holland RIASEC, VIPS, MBTI) và biết giải thích "
            "kết quả trắc nghiệm một cách khách quan, đặt trong bối cảnh phát triển của "
            "học sinh, không tuyệt đối hóa kết quả."
        ),
        "source_ref": SOURCE,
    },
    {
        "code": "CC-04",
        "name_vi": "An toàn dữ liệu và tuân thủ BVDLCN",
        "name_en": "Data Safety and Personal Data Protection (BVDLCN)",
        "description": (
            "Nắm vững quy định Luật BVDLCN 2023, Luật Việc làm 2025 (hiệu lực 2026) và "
            "TT 18/2025 liên quan đến bảo mật hồ sơ học sinh, quy trình xử lý dữ liệu "
            "nhạy cảm, giới hạn tiếp cận và nghĩa vụ thông báo."
        ),
        "source_ref": SOURCE,
    },
    {
        "code": "CC-05",
        "name_vi": "Nhận biết dấu hiệu cần chuyển tuyến",
        "name_en": "Referral Signal Recognition",
        "description": (
            "Phát hiện sớm các dấu hiệu cần chuyển tuyến: vấn đề sức khỏe tâm thần nghiêm trọng, "
            "nguy cơ tự hại, bạo lực, lạm dụng — và thực hiện quy trình chuyển tuyến đúng "
            "theo hướng dẫn của TT 18/2025."
        ),
        "source_ref": SOURCE,
    },
    {
        "code": "CC-06",
        "name_vi": "Kiến thức thông tin nghề nghiệp và phân luồng",
        "name_en": "Career Information and Pathway Knowledge",
        "description": (
            "Cập nhật thông tin về ngành nghề, xu hướng thị trường lao động, các con đường "
            "phân luồng sau THCS/THPT (học thuật, GDNN, GDNN trung học nghề), và thông tin "
            "cơ sở đào tạo — cơ sở tư vấn hướng nghiệp theo TT 16/2026."
        ),
        "source_ref": SOURCE,
    },
]


async def seed_counselor_competencies(session: AsyncSession) -> dict[str, str]:
    """Idempotently seed the framework. Returns {code: id} for all entries.

    Caller commits.
    """
    from app.core.models import new_uuid
    from app.counselor_competency.models import CounselorCompetency

    result: dict[str, str] = {}
    for entry in FRAMEWORK:
        existing = (
            (
                await session.execute(
                    select(CounselorCompetency).where(
                        CounselorCompetency.code == entry["code"]
                    )
                )
            )
            .scalars()
            .first()
        )
        if existing is not None:
            result[existing.code] = existing.id
            continue

        row = CounselorCompetency(
            id=new_uuid(),
            code=entry["code"],
            name_vi=entry["name_vi"],
            name_en=entry["name_en"],
            description=entry["description"],
            source_ref=entry["source_ref"],
        )
        session.add(row)
        await session.flush()
        result[row.code] = row.id

    return result


async def _run() -> None:  # pragma: no cover - CLI entry point
    """CLI: `python -m app.counselor_competency.seed`"""
    from app.core.config import get_settings
    from app.core.database import Database

    db = Database(get_settings())
    try:
        async with db.session_factory() as session:
            ids = await seed_counselor_competencies(session)
            await session.commit()
        print(f"[seed] counselor_competency ready: {sorted(ids.keys())}")
    finally:
        await db.dispose()


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    import asyncio

    asyncio.run(_run())
