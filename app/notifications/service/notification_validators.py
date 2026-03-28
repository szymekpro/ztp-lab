from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def validate_content(content: str):
    if not content or not content.strip():
        raise ValueError("Treść powiadomienia nie może być pusta.")


def validate_recipient(recipient: str):
    if not recipient or not recipient.strip():
        raise ValueError("Odbiorca nie może być pusty.")


def validate_timezone(timezone_name: str):
    if not timezone_name or not timezone_name.strip():
        raise ValueError("Strefa czasowa jest wymagana.")

    try:
        ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError("Podana strefa czasowa jest nieprawidłowa.") from exc


def convert_to_utc(scheduled_at: datetime, timezone_name: str) -> datetime:
    """
    Przyjmuje datę planowanej wysyłki oraz nazwę strefy czasowej.
    Zwraca datę przekonwertowaną do UTC.
    """
    zone = ZoneInfo(timezone_name)

    # Jeżeli użytkownik podał czas bez strefy, traktujemy go jako czas lokalny
    # w strefie wskazanej w polu timezone.
    if scheduled_at.tzinfo is None:
        local_dt = scheduled_at.replace(tzinfo=zone)
    else:
        local_dt = scheduled_at.astimezone(zone)

    return local_dt.astimezone(timezone.utc)


def validate_scheduled_at(scheduled_at: datetime, timezone_name: str):
    scheduled_at_utc = convert_to_utc(scheduled_at, timezone_name)

    if scheduled_at_utc <= datetime.now(timezone.utc):
        raise ValueError("Planowana data wysyłki musi wskazywać przyszły moment.")