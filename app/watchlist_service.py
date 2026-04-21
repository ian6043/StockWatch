from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db_models import User, WatchlistItem, Rule


def create_user(db: Session, user_id: str, phone_number: str | None = None) -> User:
    existing = db.scalar(select(User).where(User.user_id == user_id))
    if existing:
        return existing

    user = User(user_id=user_id, phone_number=phone_number)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: str) -> User | None:
    return db.scalar(select(User).where(User.user_id == user_id))


def update_user_phone(db: Session, user_id: str, phone_number: str) -> User:
    user = db.scalar(select(User).where(User.user_id == user_id))
    if not user:
        raise ValueError("User not found")

    user.phone_number = phone_number
    db.commit()
    db.refresh(user)
    return user


def get_user_phone(db: Session, user_id: str) -> str | None:
    user = db.scalar(select(User).where(User.user_id == user_id))
    if not user:
        raise ValueError("User not found")
    return user.phone_number


def add_stock_to_watchlist(db: Session, user_id: str, symbol: str) -> WatchlistItem:
    user = db.scalar(select(User).where(User.user_id == user_id))
    if not user:
        raise ValueError("User not found")

    symbol = symbol.upper()

    existing = db.scalar(
        select(WatchlistItem).where(
            WatchlistItem.user_id == user.id,
            WatchlistItem.symbol == symbol,
        )
    )
    if existing:
        return existing

    item = WatchlistItem(user_id=user.id, symbol=symbol)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def list_watchlist(db: Session, user_id: str) -> list[WatchlistItem]:
    user = db.scalar(select(User).where(User.user_id == user_id))
    if not user:
        raise ValueError("User not found")

    return list(
        db.scalars(select(WatchlistItem).where(WatchlistItem.user_id == user.id)).all()
    )


def remove_stock_from_watchlist(db: Session, user_id: str, symbol: str) -> bool:
    user = db.scalar(select(User).where(User.user_id == user_id))
    if not user:
        raise ValueError("User not found")

    symbol = symbol.upper()
    item = db.scalar(
        select(WatchlistItem).where(
            WatchlistItem.user_id == user.id,
            WatchlistItem.symbol == symbol,
        )
    )
    if not item:
        return False

    db.delete(item)
    db.commit()
    return True


def add_rule_to_stock(
    db: Session,
    user_id: str,
    symbol: str,
    rule_type: str,
    condition: str,
    target_value: float,
    cooldown_seconds: int,
) -> Rule:
    user = db.scalar(select(User).where(User.user_id == user_id))
    if not user:
        raise ValueError("User not found")

    symbol = symbol.upper()

    item = db.scalar(
        select(WatchlistItem).where(
            WatchlistItem.user_id == user.id,
            WatchlistItem.symbol == symbol,
        )
    )
    if not item:
        item = WatchlistItem(user_id=user.id, symbol=symbol)
        db.add(item)
        db.commit()
        db.refresh(item)

    rule = Rule(
        watchlist_item_id=item.id,
        rule_type=rule_type,
        condition=condition,
        target_value=target_value,
        cooldown_seconds=cooldown_seconds,
        last_triggered_at=None,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def get_stock_rules(db: Session, user_id: str, symbol: str) -> list[Rule]:
    user = db.scalar(select(User).where(User.user_id == user_id))
    if not user:
        raise ValueError("User not found")

    symbol = symbol.upper()
    item = db.scalar(
        select(WatchlistItem).where(
            WatchlistItem.user_id == user.id,
            WatchlistItem.symbol == symbol,
        )
    )
    if not item:
        raise ValueError("Stock not in watchlist")

    return list(db.scalars(select(Rule).where(Rule.watchlist_item_id == item.id)).all())


def get_rule_by_id(db: Session, user_id: str, symbol: str, rule_id: int) -> Rule:
    user = db.scalar(select(User).where(User.user_id == user_id))
    if not user:
        raise ValueError("User not found")

    symbol = symbol.upper()
    item = db.scalar(
        select(WatchlistItem).where(
            WatchlistItem.user_id == user.id,
            WatchlistItem.symbol == symbol,
        )
    )
    if not item:
        raise ValueError("Stock not in watchlist")

    rule = db.scalar(
        select(Rule).where(
            Rule.watchlist_item_id == item.id,
            Rule.id == rule_id,
        )
    )
    if not rule:
        raise ValueError("Rule not found")

    return rule


def delete_rule(db: Session, user_id: str, symbol: str, rule_id: int) -> bool:
    rule = get_rule_by_id(db, user_id, symbol, rule_id)
    if not rule:
        return False

    db.delete(rule)
    db.commit()
    return True
