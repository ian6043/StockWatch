from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas_market_calendars as mcal
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.alert_service import check_all_users_alerts
from app.database import SessionLocal

MARKET_TIMEZONE = "America/New_York"

scheduler = BackgroundScheduler(timezone=MARKET_TIMEZONE)
ny_tz = ZoneInfo(MARKET_TIMEZONE)
nyse = mcal.get_calendar("NYSE")

JOB_ID = "next_market_alert_check"

_last_run_at: datetime | None = None
_last_run_results: dict | None = None
_next_run_at: datetime | None = None


def _candidate_slots_for_session(
    market_open_et: datetime, market_close_et: datetime
) -> list[datetime]:
    slots = []

    # First check 5 minutes after open (9:35 for standard 9:30 sessions)
    first = market_open_et + timedelta(minutes=5)
    slots.append(first)

    # Next :00 or :30 boundary after the first slot
    if first.minute < 30:
        current = first.replace(minute=30, second=0, microsecond=0)
    else:
        current = first.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

    # Every 30 minutes through market close + 30 min (captures the 4:30 slot)
    while current <= market_close_et + timedelta(minutes=30):
        slots.append(current)
        current += timedelta(minutes=30)

    return slots


def _get_upcoming_schedule(now_et: datetime, days_ahead: int = 10):
    return nyse.schedule(
        start_date=now_et.date().isoformat(),
        end_date=(now_et.date() + timedelta(days=days_ahead)).isoformat(),
    )


def get_next_run_time(now_et: datetime) -> datetime | None:
    schedule = _get_upcoming_schedule(now_et)

    if schedule.empty:
        return None

    for _, row in schedule.iterrows():
        market_open_et = row["market_open"].tz_convert(MARKET_TIMEZONE).to_pydatetime()
        market_close_et = (
            row["market_close"].tz_convert(MARKET_TIMEZONE).to_pydatetime()
        )

        for slot in _candidate_slots_for_session(market_open_et, market_close_et):
            if slot > now_et:
                return slot

    return None


def is_trading_day(now_et: datetime) -> bool:
    schedule = nyse.schedule(
        start_date=now_et.date().isoformat(),
        end_date=now_et.date().isoformat(),
    )
    return not schedule.empty


def get_today_market_window(now_et: datetime) -> dict | None:
    schedule = nyse.schedule(
        start_date=now_et.date().isoformat(),
        end_date=now_et.date().isoformat(),
    )

    if schedule.empty:
        return None

    row = schedule.iloc[0]
    market_open_et = row["market_open"].tz_convert(MARKET_TIMEZONE).to_pydatetime()
    market_close_et = row["market_close"].tz_convert(MARKET_TIMEZONE).to_pydatetime()

    return {
        "market_open": market_open_et.isoformat(),
        "market_close": market_close_et.isoformat(),
    }


def schedule_next_run():
    global _next_run_at

    now_et = datetime.now(ny_tz)
    next_run = get_next_run_time(now_et)
    _next_run_at = next_run

    if next_run is None:
        print("[scheduler] no next trading slot found")
        return

    existing = scheduler.get_job(JOB_ID)
    if existing:
        scheduler.reschedule_job(JOB_ID, trigger="date", run_date=next_run)
    else:
        scheduler.add_job(
            run_alert_cycle,
            trigger="date",
            run_date=next_run,
            id=JOB_ID,
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )

    print(f"[scheduler] next run scheduled for {next_run.isoformat()}")


def run_alert_cycle():
    global _last_run_at, _last_run_results

    db: Session = SessionLocal()
    try:
        results = check_all_users_alerts(db)
        triggered_count = sum(1 for r in results if r.get("triggered"))
        now_et = datetime.now(ny_tz)

        _last_run_at = now_et
        _last_run_results = {
            "total_rules_checked": len(results),
            "triggered_count": triggered_count,
        }

        print(
            f"[scheduler] {now_et.isoformat()} checked alerts: "
            f"total={len(results)} triggered={triggered_count}"
        )
    except Exception as e:
        print(f"[scheduler] error during alert cycle: {e}")
    finally:
        db.close()

    schedule_next_run()


def get_scheduler_status() -> dict:
    now_et = datetime.now(ny_tz)
    today_window = get_today_market_window(now_et)

    return {
        "running": scheduler.running,
        "timezone": MARKET_TIMEZONE,
        "now": now_et.isoformat(),
        "is_trading_day": is_trading_day(now_et),
        "today_market_window": today_window,
        "last_run_at": _last_run_at.isoformat() if _last_run_at else None,
        "last_run_results": _last_run_results,
        "next_run_at": _next_run_at.isoformat() if _next_run_at else None,
    }


def start_scheduler():
    if scheduler.running:
        return

    scheduler.start()
    schedule_next_run()
    print("[scheduler] started")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        print("[scheduler] stopped")
