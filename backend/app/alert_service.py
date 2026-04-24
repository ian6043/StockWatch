import time
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.stock_service import get_stock_data
from app.db_models import User, WatchlistItem, Rule, AlertEvent
from app.notification_service import send_discord_alert


def _compare(condition: str, actual_value: float, target_value: float) -> bool:
    if condition == "above":
        return actual_value > target_value
    if condition == "below":
        return actual_value < target_value
    return False


def _is_on_cooldown(rule: Rule) -> bool:
    if rule.last_triggered_at is None:
        return False
    return (time.time() - rule.last_triggered_at) < rule.cooldown_seconds


def _seconds_remaining(rule: Rule) -> int:
    if rule.last_triggered_at is None:
        return 0
    remaining = rule.cooldown_seconds - (time.time() - rule.last_triggered_at)
    return max(0, int(remaining))



def evaluate_rule(db: Session, user_id: str, symbol: str, rule: Rule) -> dict:
    stock = get_stock_data(symbol)

    actual_value = None
    if rule.rule_type == "price":
        actual_value = stock.get("price")
    elif rule.rule_type == "percent_change":
        actual_value = stock.get("day_percent_change")

    if actual_value is None:
        return {
            "rule_id": rule.id,
            "symbol": symbol,
            "triggered": False,
            "message": "Could not evaluate rule",
        }

    if _is_on_cooldown(rule):
        print(
            f"[alert] {symbol} rule#{rule.id} skipped — on cooldown, "
            f"{_seconds_remaining(rule)}s remaining"
        )
        return {
            "rule_id": rule.id,
            "symbol": symbol,
            "rule_type": rule.rule_type,
            "condition": rule.condition,
            "target_value": rule.target_value,
            "actual_value": actual_value,
            "triggered": False,
            "notification_status": "on_cooldown",
            "on_cooldown": True,
            "cooldown_remaining_seconds": _seconds_remaining(rule),
            "message": "Rule is on cooldown",
        }

    triggered = _compare(
        condition=rule.condition,
        actual_value=actual_value,
        target_value=rule.target_value,
    )

    print(
        f"[alert] {symbol} rule#{rule.id} ({rule.rule_type} {rule.condition} {rule.target_value}): "
        f"actual={actual_value:.4f} triggered={triggered}"
    )

    notification_result = None
    notification_status = None

    if triggered:
        rule.last_triggered_at = time.time()

        try:
            notification_result = send_discord_alert(symbol, rule, actual_value)
            notification_status = "discord_sent"
        except Exception as e:
            notification_result = {"error": str(e)}
            notification_status = "discord_failed"

        event = AlertEvent(
            rule_id=rule.id,
            triggered_at=rule.last_triggered_at,
            actual_value=actual_value,
            notification_status=notification_status,
        )
        db.add(event)
        db.commit()
        db.refresh(rule)

    return {
        "rule_id": rule.id,
        "symbol": symbol,
        "rule_type": rule.rule_type,
        "condition": rule.condition,
        "target_value": rule.target_value,
        "actual_value": actual_value,
        "triggered": triggered,
        "notification_status": notification_status,
        "notification_result": notification_result,
        "on_cooldown": False,
        "cooldown_remaining_seconds": 0,
        "message": "Triggered" if triggered else "Not triggered",
    }


def check_user_alerts(db: Session, user_id: str) -> list[dict]:
    user = db.scalar(select(User).where(User.user_id == user_id))
    if not user:
        raise ValueError("User not found")

    items = list(
        db.scalars(select(WatchlistItem).where(WatchlistItem.user_id == user.id)).all()
    )

    results = []
    for item in items:
        rules = list(
            db.scalars(select(Rule).where(Rule.watchlist_item_id == item.id)).all()
        )
        for rule in rules:
            results.append(evaluate_rule(db, user_id, item.symbol, rule))

    return results


def check_all_users_alerts(db: Session) -> list[dict]:
    users = list(db.scalars(select(User)).all())
    all_results = []

    for user in users:
        results = check_user_alerts(db, user.user_id)
        all_results.extend(results)

    return all_results
