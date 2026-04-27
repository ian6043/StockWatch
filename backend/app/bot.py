import asyncio
import discord
from discord import app_commands
from discord.app_commands import Choice

from app.settings import DISCORD_BOT_TOKEN, DISCORD_GUILD_ID, BOT_USER_ID
from app.watchlist_service import (
    list_watchlist,
    add_stock_to_watchlist,
    remove_stock_from_watchlist,
    get_stock_rules,
    add_rule_to_stock,
    delete_rule_by_id,
)
from app.stock_service import get_stock_data
from app.alert_service import check_user_alerts
from app.database import SessionLocal

DEBUG = True

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
_guild = discord.Object(id=int(DISCORD_GUILD_ID)) if DISCORD_GUILD_ID else None

COOLDOWN_CHOICES = [
    Choice(name="5 minutes", value=300),
    Choice(name="15 minutes", value=900),
    Choice(name="30 minutes", value=1800),
    Choice(name="1 hour", value=3600),
    Choice(name="1 day", value=86400),
]


def _fmt_cooldown(seconds: int) -> str:
    if seconds < 3600:
        return f"{seconds // 60}m"
    if seconds < 86400:
        return f"{seconds // 3600}h"
    return f"{seconds // 86400}d"


@client.event
async def on_ready():
    # Clear any stale global commands
    tree.clear_commands(guild=None)
    await tree.sync()

    if _guild:
        tree.copy_global_to(guild=_guild)
        await tree.sync(guild=_guild)
    else:
        await tree.sync()
    if DEBUG: print(f"[bot] logged in as {client.user}")


@tree.command(
    name="watchlist",
    description="Show your stock watchlist with current prices",
    guild=_guild,
)
async def cmd_watchlist(interaction: discord.Interaction):
    if DEBUG: print(f"[cmd] /watchlist called by {interaction.user}")
    await interaction.response.defer()
    db = SessionLocal()
    try:
        if DEBUG: print(f"[service] list_watchlist(user={BOT_USER_ID})")
        items = await asyncio.to_thread(list_watchlist, db, BOT_USER_ID)
        if DEBUG: print(f"[service] list_watchlist → {len(items)} item(s)")
        if not items:
            await interaction.followup.send(
                "Your watchlist is empty. Use `/add` to add stocks."
            )
            return

        lines = []
        for item in items:
            try:
                if DEBUG: print(f"[service] get_stock_data({item.symbol})")
                data = await asyncio.to_thread(get_stock_data, item.symbol)
                price = f"${data['price']:.2f}" if data.get("price") else "N/A"
                pct = data.get("day_percent_change")
                change = (
                    f" ({'+' if pct >= 0 else ''}{pct:.2f}%)" if pct is not None else ""
                )
            except Exception as e:
                if DEBUG: print(f"[service] get_stock_data({item.symbol}) error: {e}")
                price, change = "N/A", ""
            lines.append(f"**{item.symbol}** — {price}{change}")
            for rule in item.rules:
                if rule.rule_type == "percent_change":
                    direction = "drops" if rule.condition == "below" else "rises"
                    val = f"{abs(rule.target_value):.2f}%"
                else:
                    direction = "above" if rule.condition == "above" else "below"
                    val = f"${rule.target_value:.2f}"
                lines.append(
                    f"  `#{rule.id}` {rule.rule_type.replace('_', ' ')} {direction} {val} · {_fmt_cooldown(rule.cooldown_seconds)} cooldown"
                )

        embed = discord.Embed(
            title="📈 Watchlist", description="\n".join(lines), color=0x2ECC71
        )
        await interaction.followup.send(embed=embed)
        if DEBUG: print(f"[cmd] /watchlist done")
    finally:
        db.close()


@tree.command(name="add", description="Add a stock to your watchlist", guild=_guild)
@app_commands.describe(symbol="Ticker symbol e.g. AAPL")
async def cmd_add(interaction: discord.Interaction, symbol: str):
    if DEBUG: print(f"[cmd] /add symbol={symbol.upper()} called by {interaction.user}")
    await interaction.response.defer()
    db = SessionLocal()
    try:
        if DEBUG: print(f"[service] add_stock_to_watchlist(user={BOT_USER_ID}, symbol={symbol.upper()})")
        item = await asyncio.to_thread(
            add_stock_to_watchlist, db, BOT_USER_ID, symbol.upper()
        )
        if DEBUG: print(f"[service] add_stock_to_watchlist → added {item.symbol}")
        await interaction.followup.send(
            f"✅ **{item.symbol}** added to your watchlist."
        )
    except ValueError as e:
        if DEBUG: print(f"[service] add_stock_to_watchlist error: {e}")
        await interaction.followup.send(f"❌ {e}")
    finally:
        db.close()


@tree.command(
    name="remove", description="Remove a stock from your watchlist", guild=_guild
)
@app_commands.describe(symbol="Ticker symbol e.g. AAPL")
async def cmd_remove(interaction: discord.Interaction, symbol: str):
    if DEBUG: print(f"[cmd] /remove symbol={symbol.upper()} called by {interaction.user}")
    await interaction.response.defer()
    db = SessionLocal()
    try:
        if DEBUG: print(f"[service] remove_stock_from_watchlist(user={BOT_USER_ID}, symbol={symbol.upper()})")
        removed = await asyncio.to_thread(
            remove_stock_from_watchlist, db, BOT_USER_ID, symbol.upper()
        )
        if DEBUG: print(f"[service] remove_stock_from_watchlist → removed={removed}")
        if removed:
            await interaction.followup.send(
                f"✅ **{symbol.upper()}** removed from your watchlist."
            )
        else:
            await interaction.followup.send(
                f"❌ **{symbol.upper()}** is not in your watchlist."
            )
    except ValueError as e:
        if DEBUG: print(f"[service] remove_stock_from_watchlist error: {e}")
        await interaction.followup.send(f"❌ {e}")
    finally:
        db.close()


@tree.command(name="rules", description="Show alert rules for a stock", guild=_guild)
@app_commands.describe(symbol="Ticker symbol e.g. AAPL")
async def cmd_rules(interaction: discord.Interaction, symbol: str):
    if DEBUG: print(f"[cmd] /rules symbol={symbol.upper()} called by {interaction.user}")
    await interaction.response.defer()
    db = SessionLocal()
    try:
        if DEBUG: print(f"[service] get_stock_rules(user={BOT_USER_ID}, symbol={symbol.upper()})")
        rules = await asyncio.to_thread(
            get_stock_rules, db, BOT_USER_ID, symbol.upper()
        )
        if DEBUG: print(f"[service] get_stock_rules → {len(rules)} rule(s)")
        if not rules:
            await interaction.followup.send(
                f"No rules set for **{symbol.upper()}**. Use `/add-rule` to create one."
            )
            return

        lines = []
        for rule in rules:
            if rule.rule_type == "percent_change":
                direction = "drops" if rule.condition == "below" else "rises"
                val = f"{abs(rule.target_value):.2f}%"
            else:
                direction = "above" if rule.condition == "above" else "below"
                val = f"${rule.target_value:.2f}"
            lines.append(
                f"`#{rule.id}` {rule.rule_type.replace('_', ' ')} {direction} {val} · {_fmt_cooldown(rule.cooldown_seconds)} cooldown"
            )

        embed = discord.Embed(
            title=f"🔔 Rules for {symbol.upper()}",
            description="\n".join(lines),
            color=0x3498DB,
        )
        await interaction.followup.send(embed=embed)
        if DEBUG: print(f"[cmd] /rules done")
    except ValueError as e:
        if DEBUG: print(f"[service] get_stock_rules error: {e}")
        await interaction.followup.send(f"❌ {e}")
    finally:
        db.close()


@tree.command(
    name="add-rule", description="Add an alert rule for a stock", guild=_guild
)
@app_commands.describe(
    symbol="Ticker symbol e.g. AAPL",
    rule_type="Price or % change",
    direction="Above/rise or below/drop",
    value="Target value as a positive number",
    cooldown="How long before the rule can trigger again",
)
@app_commands.choices(
    rule_type=[
        Choice(name="Price", value="price"),
        Choice(name="% Change", value="percent_change"),
    ],
    direction=[
        Choice(name="Above / Rise", value="above"),
        Choice(name="Below / Drop", value="below"),
    ],
    cooldown=COOLDOWN_CHOICES,
)
async def cmd_add_rule(
    interaction: discord.Interaction,
    symbol: str,
    rule_type: str,
    direction: str,
    value: float,
    cooldown: int,
):
    if DEBUG: print(f"[cmd] /add-rule symbol={symbol.upper()} rule_type={rule_type} direction={direction} value={value} cooldown={cooldown} called by {interaction.user}")
    await interaction.response.defer()
    db = SessionLocal()
    try:
        target = (
            -abs(value)
            if rule_type == "percent_change" and direction == "below"
            else abs(value)
        )
        if DEBUG: print(f"[service] add_rule_to_stock(user={BOT_USER_ID}, symbol={symbol.upper()}, type={rule_type}, condition={direction}, target={target}, cooldown={cooldown})")
        rule = await asyncio.to_thread(
            add_rule_to_stock,
            db,
            BOT_USER_ID,
            symbol.upper(),
            rule_type,
            direction,
            target,
            cooldown,
        )
        if DEBUG: print(f"[service] add_rule_to_stock → rule #{rule.id}")
        if rule_type == "percent_change":
            desc = f"{'drops' if direction == 'below' else 'rises'} above {abs(target):.2f}%"
        else:
            desc = f"{'above' if direction == 'above' else 'below'} ${target:.2f}"
        await interaction.followup.send(
            f"✅ Rule `#{rule.id}` added for **{symbol.upper()}**: {rule_type.replace('_', ' ')} {desc} · {_fmt_cooldown(cooldown)} cooldown"
        )
    except ValueError as e:
        if DEBUG: print(f"[service] add_rule_to_stock error: {e}")
        await interaction.followup.send(f"❌ {e}")
    finally:
        db.close()


@tree.command(
    name="delete-rule", description="Delete an alert rule by ID", guild=_guild
)
@app_commands.describe(rule_id="Rule ID shown in /watchlist or /rules")
async def cmd_delete_rule(interaction: discord.Interaction, rule_id: int):
    if DEBUG: print(f"[cmd] /delete-rule rule_id={rule_id} called by {interaction.user}")
    await interaction.response.defer()
    db = SessionLocal()
    try:
        if DEBUG: print(f"[service] delete_rule_by_id(user={BOT_USER_ID}, rule_id={rule_id})")
        await asyncio.to_thread(delete_rule_by_id, db, BOT_USER_ID, rule_id)
        if DEBUG: print(f"[service] delete_rule_by_id → deleted rule #{rule_id}")
        await interaction.followup.send(f"✅ Rule `#{rule_id}` deleted.")
    except ValueError as e:
        if DEBUG: print(f"[service] delete_rule_by_id error: {e}")
        await interaction.followup.send(f"❌ {e}")
    finally:
        db.close()


@tree.command(
    name="check",
    description="Manually trigger an alert check for all your rules",
    guild=_guild,
)
async def cmd_check(interaction: discord.Interaction):
    if DEBUG: print(f"[cmd] /check called by {interaction.user}")
    await interaction.response.defer()
    db = SessionLocal()
    try:
        if DEBUG: print(f"[service] check_user_alerts(user={BOT_USER_ID})")
        results = await asyncio.to_thread(check_user_alerts, db, BOT_USER_ID)
        if DEBUG: print(f"[service] check_user_alerts → {len(results)} result(s)")
        if not results:
            await interaction.followup.send("No rules to check.")
            return

        triggered = [r for r in results if r.get("triggered")]
        on_cooldown = [r for r in results if r.get("on_cooldown")]
        not_met = [
            r for r in results if not r.get("triggered") and not r.get("on_cooldown")
        ]

        lines = []
        for r in triggered:
            lines.append(
                f"🔴 **{r['symbol']}** rule `#{r['rule_id']}` triggered — actual: {r['actual_value']:.4f}"
            )
        for r in not_met:
            lines.append(
                f"⚪ **{r['symbol']}** rule `#{r['rule_id']}` not met — actual: {r['actual_value']:.4f}"
            )
        for r in on_cooldown:
            lines.append(
                f"⏳ **{r['symbol']}** rule `#{r['rule_id']}` on cooldown — {r['cooldown_remaining_seconds']}s left"
            )

        embed = discord.Embed(
            title="🔍 Alert Check",
            description="\n".join(lines),
            color=0xE74C3C if triggered else 0x95A5A6,
        )
        await interaction.followup.send(embed=embed)
        if DEBUG: print(f"[cmd] /check done — {len(triggered)} triggered, {len(on_cooldown)} on cooldown, {len(not_met)} not met")
    except ValueError as e:
        if DEBUG: print(f"[service] check_user_alerts error: {e}")
        await interaction.followup.send(f"❌ {e}")
    finally:
        db.close()


async def start():
    await client.start(DISCORD_BOT_TOKEN)
