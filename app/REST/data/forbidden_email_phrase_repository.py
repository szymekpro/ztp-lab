from sqlalchemy.orm import Session
from sqlalchemy import select

from app.REST.model.forbidden_email_phrase_orm import ForbiddenEmailPhraseORM


def get_forbidden_email_phrases(db: Session):
    query = select(ForbiddenEmailPhraseORM)
    result = db.execute(query)
    return [row.phrase for row in result.scalars().all()]