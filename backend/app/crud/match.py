from typing import Optional, List

from sqlalchemy.orm import Session

from backend.app.models.match import Match


def create_match(
    db: Session,
    lost_item_id: int,
    found_item_id: int,
    similarity: Optional[float] = None,
) -> Match:
    match = Match(
        lost_item_id=lost_item_id,
        found_item_id=found_item_id,
        similarity=similarity,
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


def get_match_by_id(db: Session, match_id: int) -> Optional[Match]:
    return db.query(Match).filter(Match.id == match_id).first()


def get_matches_by_lost_item(db: Session, lost_item_id: int) -> List[Match]:
    return db.query(Match).filter(Match.lost_item_id == lost_item_id).all()


def get_matches_by_found_item(db: Session, found_item_id: int) -> List[Match]:
    return db.query(Match).filter(Match.found_item_id == found_item_id).all()


def update_match_status(db: Session, match: Match, status: str) -> Match:
    match.status = status
    db.commit()
    db.refresh(match)
    return match
