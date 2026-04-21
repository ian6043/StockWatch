from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session

from frontend.app.database import Base, engine, get_db
from frontend.app.stock_service import get_stock_data, get_cache_status
from frontend.app.watchlist_service import (
    create_user,
    get_user,
    update_user_phone,
    add_stock_to_watchlist,
    list_watchlist,
    remove_stock_from_watchlist,
    add_rule_to_stock,
    get_stock_rules,
    get_rule_by_id,
    delete_rule,
)
from frontend.app.alert_service import check_user_alerts
from frontend.app.schemas import (
    CreateUserRequest,
    UpdatePhoneRequest,
    AddStockRequest,
    CreateRuleRequest,
)
from frontend.app.scheduler import start_scheduler, stop_scheduler, get_scheduler_status
from frontend.app.auth import require_api_key

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="Stock Watch API",
    lifespan=lifespan,
    dependencies=[Depends(require_api_key)],
)


@app.get("/")
def root():
    return {"message": "Stock API is running"}


@app.get("/stock/{symbol}")
def get_stock(symbol: str):
    try:
        return get_stock_data(symbol)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch stock data")


@app.get("/cache")
def cache_info():
    return get_cache_status()


@app.post("/users")
def create_user_route(payload: CreateUserRequest, db: Session = Depends(get_db)):
    return create_user(
        db=db,
        user_id=payload.user_id,
        phone_number=payload.phone_number,
    )


@app.get("/users/{user_id}")
def get_user_route(user_id: str, db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/users/{user_id}/phone")
def update_user_phone_route(
    user_id: str,
    payload: UpdatePhoneRequest,
    db: Session = Depends(get_db),
):
    try:
        return update_user_phone(db, user_id, payload.phone_number)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/users/{user_id}/watchlist")
def add_stock_route(
    user_id: str,
    payload: AddStockRequest,
    db: Session = Depends(get_db),
):
    try:
        return add_stock_to_watchlist(db, user_id, payload.symbol)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/users/{user_id}/watchlist")
def list_watchlist_route(user_id: str, db: Session = Depends(get_db)):
    try:
        return list_watchlist(db, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/users/{user_id}/watchlist/{symbol}")
def remove_stock_route(user_id: str, symbol: str, db: Session = Depends(get_db)):
    try:
        deleted = remove_stock_from_watchlist(db, user_id, symbol)
        if not deleted:
            raise HTTPException(status_code=404, detail="Stock not found in watchlist")
        return {"message": "Stock removed from watchlist"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/users/{user_id}/watchlist/{symbol}/rules")
def add_rule_route(
    user_id: str,
    symbol: str,
    payload: CreateRuleRequest,
    db: Session = Depends(get_db),
):
    try:
        return add_rule_to_stock(
            db=db,
            user_id=user_id,
            symbol=symbol,
            rule_type=payload.rule_type,
            condition=payload.condition,
            target_value=payload.target_value,
            cooldown_seconds=payload.cooldown_seconds,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/users/{user_id}/watchlist/{symbol}/rules")
def get_rules_route(user_id: str, symbol: str, db: Session = Depends(get_db)):
    try:
        return get_stock_rules(db, user_id, symbol)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/users/{user_id}/watchlist/{symbol}/rules/{rule_id}")
def get_rule_route(
    user_id: str,
    symbol: str,
    rule_id: int,
    db: Session = Depends(get_db),
):
    try:
        return get_rule_by_id(db, user_id, symbol, rule_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/users/{user_id}/watchlist/{symbol}/rules/{rule_id}")
def delete_rule_route(
    user_id: str,
    symbol: str,
    rule_id: int,
    db: Session = Depends(get_db),
):
    try:
        deleted = delete_rule(db, user_id, symbol, rule_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Rule not found")
        return {"message": "Rule deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/users/{user_id}/alerts/check")
def check_alerts_route(user_id: str, db: Session = Depends(get_db)):
    try:
        return check_user_alerts(db, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/scheduler/status")
def scheduler_status():
    return get_scheduler_status()
