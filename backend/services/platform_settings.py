from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import PlatformSetting
from backend.services.legal_documents import CROSS_BORDER_VERSION


CROSS_BORDER_SETTING_KEY = "legal.cross_border"
DEFAULT_CROSS_BORDER_CONFIG = {
    "visible": False,
    "activation": 0,
    "consent_version": None,
}


def _normalized_cross_border_config(setting: PlatformSetting | None) -> dict:
    value = setting.value if setting is not None and isinstance(setting.value, dict) else {}
    return {
        "visible": bool(value.get("visible", False)),
        "activation": max(0, int(value.get("activation", 0))),
        "consent_version": value.get("consent_version"),
        "updated_at": setting.updated_at if setting is not None else None,
    }


async def get_cross_border_config(db: AsyncSession, *, lock: bool = False) -> dict:
    statement = select(PlatformSetting).where(PlatformSetting.key == CROSS_BORDER_SETTING_KEY)
    if lock:
        statement = statement.with_for_update()
    return _normalized_cross_border_config(await db.scalar(statement))


async def update_cross_border_visibility(db: AsyncSession, visible: bool, admin_id: UUID) -> dict:
    setting = await db.scalar(
        select(PlatformSetting)
        .where(PlatformSetting.key == CROSS_BORDER_SETTING_KEY)
        .with_for_update()
    )
    if setting is None:
        setting = PlatformSetting(
            key=CROSS_BORDER_SETTING_KEY,
            value=dict(DEFAULT_CROSS_BORDER_CONFIG),
            updated_by=admin_id,
        )
        db.add(setting)
        await db.flush()

    current = _normalized_cross_border_config(setting)
    activation = current["activation"]
    consent_version = current["consent_version"]
    if visible and not current["visible"]:
        activation += 1
        consent_version = f"{CROSS_BORDER_VERSION}.r{activation}"

    setting.value = {
        "visible": visible,
        "activation": activation,
        "consent_version": consent_version,
    }
    setting.updated_by = admin_id
    setting.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return _normalized_cross_border_config(setting)
