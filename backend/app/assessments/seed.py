"""Seed data for the MVP assessment instruments (FR-10, FR-13).

A small, deterministic item bank for RIASEC / [CRED_AECCE12B] / [CRED_BB31C5D7] so the
submit/score/read flow is exercisable end-to-end. Items are tagged with
``competency_code``
(mainly NL1, ADR-013) and ``dieu5_code='b'`` (TT 16/2026 Điều 5(b)). Prompts are
placeholders pending the ILO Việt Nam item set (sources.md §2) — content is
versioned, so swapping in the real bank is a new instrument version, not a code
change.

``item_key`` prefixes encode the scoring dimension (see scoring.py): RIASEC
keys start with R/I/A/S/E/C; VIPS with V/I/P/S; MBTI with one of the 8 poles.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import InstrumentType

INSTRUMENT_VERSION = "mvp-1"

# item_key -> Vietnamese prompt. Two items per dimension keeps the bank small
# but lets every dimension accumulate a score.
RIASEC_ITEMS: dict[str, str] = {
    "R_1": "Tôi thích làm việc với máy móc, công cụ hoặc ngoài trời.",
    "R_2": "Tôi thích các hoạt động thực hành, lắp ráp, sửa chữa.",
    "I_1": "Tôi thích tìm hiểu, phân tích và giải quyết vấn đề.",
    "I_2": "Tôi tò mò về cách mọi thứ vận hành.",
    "A_1": "Tôi thích sáng tạo, vẽ, viết hoặc biểu diễn.",
    "A_2": "Tôi thích thể hiện ý tưởng theo cách riêng của mình.",
    "S_1": "Tôi thích giúp đỡ, hướng dẫn và làm việc với người khác.",
    "S_2": "Tôi quan tâm đến cảm xúc và nhu cầu của người khác.",
    "E_1": "Tôi thích thuyết phục, lãnh đạo và khởi xướng dự án.",
    "E_2": "Tôi thích đặt mục tiêu và tổ chức người khác cùng đạt được.",
    "C_1": "Tôi thích làm việc có quy trình, dữ liệu và sự chính xác.",
    "C_2": "Tôi thích sắp xếp, kiểm tra và tuân thủ quy tắc.",
}

VIPS_ITEMS: dict[str, str] = {
    "V_1": "Giá trị và ý nghĩa công việc rất quan trọng với tôi.",
    "V_2": "Tôi chọn việc dựa trên điều tôi cho là đúng đắn.",
    "I_1": "Tôi theo đuổi những lĩnh vực mình thực sự hứng thú.",
    "I_2": "Sở thích cá nhân ảnh hưởng lớn đến lựa chọn của tôi.",
    "P_1": "Tôi hiểu rõ tính cách và phong cách làm việc của mình.",
    "P_2": "Tôi biết mình hợp với môi trường làm việc nào.",
    "S_1": "Tôi tự tin vào các kỹ năng mình đã rèn luyện.",
    "S_2": "Tôi biết điểm mạnh kỹ năng của bản thân.",
}

MBTI_ITEMS: dict[str, str] = {
    "E_1": "Tôi lấy lại năng lượng khi ở cùng nhiều người.",
    "I_1": "Tôi cần thời gian một mình để nạp lại năng lượng.",
    "S_1": "Tôi chú ý đến chi tiết cụ thể và thực tế.",
    "N_1": "Tôi chú ý đến ý tưởng tổng thể và khả năng.",
    "T_1": "Tôi ra quyết định dựa trên logic và phân tích.",
    "F_1": "Tôi ra quyết định dựa trên giá trị và con người.",
    "J_1": "Tôi thích kế hoạch rõ ràng và quyết định sớm.",
    "P_1": "Tôi thích linh hoạt và để ngỏ các lựa chọn.",
}

ITEMS_BY_TYPE: dict[InstrumentType, dict[str, str]] = {
    InstrumentType.RIASEC: RIASEC_ITEMS,
    InstrumentType.VIPS: VIPS_ITEMS,
    InstrumentType.MBTI: MBTI_ITEMS,
}


async def seed_instruments(session: AsyncSession) -> dict[str, str]:
    """Idempotently create one active instrument per type (version
    ``INSTRUMENT_VERSION``) with its items. Returns ``{type_value: instrument_id}``.

    Idempotent: an instrument of the same (type, version) already present is left
    untouched — re-running is safe (deploy / [CRED_36DC2A53] runs). Closes gap G-1:
    a fresh DB had no instruments, so submit returned 404. Caller commits.
    """
    from app.assessments.models import AssessmentInstrument, AssessmentItem
    from app.core.models import new_uuid

    ids: dict[str, str] = {}
    for itype in InstrumentType:
        existing = (
            await session.execute(
                select(AssessmentInstrument).where(
                    AssessmentInstrument.type == itype,
                    AssessmentInstrument.version == INSTRUMENT_VERSION,
                )
            )
        ).scalars().first()
        if existing is not None:
            ids[itype.value] = existing.id
            continue
        inst = AssessmentInstrument(
            id=new_uuid(), type=itype, version=INSTRUMENT_VERSION, is_active=True
        )
        session.add(inst)
        await session.flush()
        for key, prompt in ITEMS_BY_TYPE[itype].items():
            session.add(
                AssessmentItem(
                    id=new_uuid(),
                    instrument_id=inst.id,
                    item_key=key,
                    competency_code="NL1",
                    dieu5_code="b",
                    prompt_vi=prompt,
                )
            )
        ids[itype.value] = inst.id
    return ids


async def _run() -> None:  # pragma: no cover - CLI entry point
    """CLI: `python -m app.assessments.seed` — seed instruments into the live DB."""
    from app.core.config import get_settings
    from app.core.database import Database

    db = Database(get_settings())
    try:
        async with db.session_factory() as session:
            ids = await seed_instruments(session)
            await session.commit()
        print(f"[seed] instruments ready: {sorted(ids)}")
    finally:
        await db.dispose()


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    import asyncio

    asyncio.run(_run())
