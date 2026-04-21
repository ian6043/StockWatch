from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from frontend.app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, nullable=True)

    watchlist_items = relationship(
        "WatchlistItem",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    __table_args__ = (UniqueConstraint("user_id", "symbol", name="uq_user_symbol"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String, index=True, nullable=False)

    user = relationship("User", back_populates="watchlist_items")
    rules = relationship(
        "Rule",
        back_populates="watchlist_item",
        cascade="all, delete-orphan",
    )


class Rule(Base):
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True)
    watchlist_item_id = Column(
        Integer, ForeignKey("watchlist_items.id"), nullable=False
    )

    rule_type = Column(String, nullable=False)  # "price" | "percent_change"
    condition = Column(String, nullable=False)  # "above" | "below"
    target_value = Column(Float, nullable=False)
    cooldown_seconds = Column(Integer, nullable=False, default=300)
    last_triggered_at = Column(Float, nullable=True)

    watchlist_item = relationship("WatchlistItem", back_populates="rules")
    alert_events = relationship(
        "AlertEvent",
        back_populates="rule",
        cascade="all, delete-orphan",
    )


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("rules.id"), nullable=False)

    triggered_at = Column(Float, nullable=False)
    actual_value = Column(Float, nullable=True)
    notification_status = Column(String, nullable=True)

    rule = relationship("Rule", back_populates="alert_events")
