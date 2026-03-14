import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_BOT_TOKEN")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")

def query_prometheus(promql: str) -> str:
    """Prometheus-тен метрика алу"""
    try:
        resp = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": promql}, timeout=5)
        result = resp.json()["data"]["result"]
        if result:
            return float(result[0]["value"][1])
    except Exception:
        pass
    return None

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/status — сервер жағдайын көрсету"""
    cpu = query_prometheus('100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[2m])) * 100)')
    ram = query_prometheus('(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100')
    disk = query_prometheus('(1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})) * 100')

    cpu_str  = f"{cpu:.1f}%"  if cpu  is not None else "N/A"
    ram_str  = f"{ram:.1f}%"  if ram  is not None else "N/A"
    disk_str = f"{disk:.1f}%" if disk is not None else "N/A"

    # Жағдай белгісі
    def icon(val, warn=70, crit=90):
        if val is None: return "❓"
        if val >= crit: return "🔴"
        if val >= warn: return "🟡"
        return "🟢"

    msg = (
        f"📊 *Server Status*\n\n"
        f"{icon(cpu)}  CPU:  `{cpu_str}`\n"
        f"{icon(ram)}  RAM:  `{ram_str}`\n"
        f"{icon(disk, 75, 85)}  Disk: `{disk_str}`\n\n"
        f"✅ Server OK" if all(v is not None for v in [cpu, ram, disk]) else "⚠️ Кейбір метрикалар қолжетімсіз"
    )

    await update.message.reply_text(msg, parse_mode="Markdown")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/help — командалар тізімі"""
    await update.message.reply_text(
        "🤖 *Admin Bot*\n\n"
        "/status — сервер жағдайы\n"
        "/help   — командалар тізімі",
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("help", help_cmd))
    print("Admin bot іске қосылды...")
    app.run_polling()
