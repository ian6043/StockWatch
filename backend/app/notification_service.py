import httpx
from app.settings import DISCORD_WEBHOOK_URL


def send_discord_alert(symbol: str, rule, actual_value: float) -> dict:
    if not DISCORD_WEBHOOK_URL:
        raise ValueError("DISCORD_WEBHOOK_URL is not configured")

    if rule.rule_type == "percent_change":
        direction = "dropped" if rule.condition == "below" else "rose"
        threshold = f"{abs(rule.target_value):.2f}%"
        actual_str = f"{actual_value:.2f}%"
        description = f"**{symbol}** {direction} **{actual_str}** (threshold: {threshold})"
        color = 0xE74C3C if rule.condition == "below" else 0x2ECC71
    else:
        direction = "below" if rule.condition == "below" else "above"
        threshold = f"${rule.target_value:.2f}"
        actual_str = f"${actual_value:.2f}"
        description = f"**{symbol}** price is **{actual_str}**, {direction} your threshold of {threshold}"
        color = 0xE74C3C if rule.condition == "below" else 0x2ECC71

    payload = {
        "embeds": [
            {
                "title": "🔔 Stock Alert Triggered",
                "description": description,
                "color": color,
            }
        ]
    }

    with httpx.Client() as client:
        response = client.post(DISCORD_WEBHOOK_URL, json=payload)
        response.raise_for_status()

    return {"status": "sent", "platform": "discord"}
