import logging

logger = logging.getLogger(__name__)


async def notify_mechaniks_new_card(
    card_title: str,
    equipment_code: str,
) -> None:
    logger.debug("notify skipped: %s / %s", card_title, equipment_code)


async def notify_card_done(card_title: str, _office_chat_ids: list[int]) -> None:
    logger.debug("notify_card_done skipped: %s", card_title)
