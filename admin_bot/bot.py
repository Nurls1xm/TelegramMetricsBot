import os
import requests
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_BOT_TOKEN")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")

def query_prometheus(promql: str) -> float:
    """Prometheus-тен метрика алу"""
    try:
        resp = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": promql},
            timeout=5
        )
        resp.raise_for_status()
        result = resp.json()["data"]["result"]
        if result:
            return float(result[0]["value"][1])
    except Exception as e:
        logger.error(f"Prometheus error: {e}")
    return None

def get_icon(val, warn=70, crit=90):
    """Status icon based on value"""
    if val is None: return "❓"
    if val >= crit: return "🔴"
    if val >= warn: return "🟡"
    return "🟢"

def get_keyboard():
    """Получить кнопки"""
    keyboard = [
        [KeyboardButton("📊 Status"), KeyboardButton("📈 Metrics")],
        [KeyboardButton("❤️ Health"), KeyboardButton("❓ Help")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start"""
    await update.message.reply_text(
        "👋 Қош келдіңіз! Сервер мониторинг ботына!\n\n"
        "📋 *Қолданылатын командалар:*\n"
        "/status — сервер жағдайы\n"
        "/metrics — толық метрикалар\n"
        "/health — құндылық тексеру\n"
        "/help — көмек",
        parse_mode="Markdown",
        reply_markup=get_keyboard()
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/status"""
    logger.info(f"Status: {update.effective_user.id}")
    
    cpu = query_prometheus('100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[2m])) * 100)')
    ram = query_prometheus('(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100')
    disk = query_prometheus('(1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})) * 100')

    cpu_str  = f"{cpu:.1f}%" if cpu is not None else "N/A"
    ram_str  = f"{ram:.1f}%" if ram is not None else "N/A"
    disk_str = f"{disk:.1f}%" if disk is not None else "N/A"

    # Определяем статус каждого показателя
    def get_status(val):
        if val is None: return None
        if val >= 90: return "critical"
        if val >= 70: return "warning"
        return "ok"

    cpu_status = get_status(cpu)
    ram_status = get_status(ram)
    disk_status = get_status(disk)

    # Логика статуса
    # 1) Если CPU зеленый = Қалыпты
    if cpu_status == "ok":
        status_msg = "✅ Сервер қалыпты жұмыс істейді"
    # 2) Если ВСЕ три желтые = Назар аударыңыз
    elif cpu_status == "warning" and ram_status == "warning" and disk_status == "warning":
        status_msg = "🟡 Назар аударыңыз"
    # 3) Если хоть один красный = Мәселелері бар
    elif cpu_status == "critical" or ram_status == "critical" or disk_status == "critical":
        status_msg = "🚨 Сервердің мәселелері бар!"
    else:
        status_msg = "⚠️ Кейбір метрикалар қолжетімсіз"

    msg = (
        f"📊 *Server Status*\n\n"
        f"{get_icon(cpu)}  CPU:  `{cpu_str}`\n"
        f"{get_icon(ram)}  RAM:  `{ram_str}`\n"
        f"{get_icon(disk, 75, 85)}  Disk: `{disk_str}`\n\n"
        f"{status_msg}"
    )

    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_keyboard())

async def metrics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/metrics"""
    logger.info(f"Metrics: {update.effective_user.id}")
    
    cpu = query_prometheus('100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)')
    ram_used = query_prometheus('node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes')
    ram_total = query_prometheus('node_memory_MemTotal_bytes')
    ram_available = query_prometheus('node_memory_MemAvailable_bytes')
    disk_used = query_prometheus('node_filesystem_size_bytes{mountpoint="/"} - node_filesystem_avail_bytes{mountpoint="/"}')
    disk_total = query_prometheus('node_filesystem_size_bytes{mountpoint="/"}')
    disk = query_prometheus('(1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})) * 100')
    load1 = query_prometheus('node_load1')
    load5 = query_prometheus('node_load5')
    load15 = query_prometheus('node_load15')

    cpu_str = f"{cpu:.1f}" if cpu is not None else "N/A"
    load1_str = f"{load1:.2f}" if load1 is not None else "N/A"
    load5_str = f"{load5:.2f}" if load5 is not None else "N/A"
    load15_str = f"{load15:.2f}" if load15 is not None else "N/A"
    ram_used_gb = (ram_used / 1024 / 1024 / 1024) if ram_used is not None else None
    ram_total_gb = (ram_total / 1024 / 1024 / 1024) if ram_total is not None else None
    ram_available_gb = (ram_available / 1024 / 1024 / 1024) if ram_available is not None else None
    ram_used_str = f"{ram_used_gb:.2f}" if ram_used_gb is not None else "N/A"
    ram_total_str = f"{ram_total_gb:.2f}" if ram_total_gb is not None else "N/A"
    ram_available_str = f"{ram_available_gb:.2f}" if ram_available_gb is not None else "N/A"
    disk_used_gb = (disk_used / 1024 / 1024 / 1024) if disk_used is not None else None
    disk_total_gb = (disk_total / 1024 / 1024 / 1024) if disk_total is not None else None
    disk_used_str = f"{disk_used_gb:.2f}" if disk_used_gb is not None else "N/A"
    disk_total_str = f"{disk_total_gb:.2f}" if disk_total_gb is not None else "N/A"
    disk_str = f"{disk:.1f}" if disk is not None else "N/A"

    msg = (
        f"📈 *Detailed Metrics*\n\n"
        f"🔧 *Процессор*\n"
        f"{get_icon(cpu)} CPU: `{cpu_str}%`\n"
        f"📊 Load 1м: `{load1_str}`\n"
        f"📊 Load 5м: `{load5_str}`\n"
        f"📊 Load 15м: `{load15_str}`\n\n"
        f"💾 *Жадтама (RAM)*\n"
        f"{get_icon(float(ram_used_gb/ram_total_gb*100) if ram_used_gb and ram_total_gb else None)} Пайдаланылған: `{ram_used_str} GB`\n"
        f"✅ Қолжетімді: `{ram_available_str} GB`\n"
        f"📦 Барлығы: `{ram_total_str} GB`\n\n"
        f"💿 *Диск Сақтағыш (Storage)*\n"
        f"{get_icon(disk, 75, 85)} Пайдаланылған: `{disk_used_str} GB`\n"
        f"📦 Барлығы: `{disk_total_str} GB`\n"
        f"{get_icon(disk, 75, 85)} Толу: `{disk_str}%`"
    )

    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_keyboard())

async def health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/health"""
    logger.info(f"Health: {update.effective_user.id}")
    
    checks = {}
    details = {}
    
    try:
        resp = requests.get(f"{PROMETHEUS_URL}/-/healthy", timeout=5)
        checks["Prometheus"] = "✅" if resp.status_code == 200 else "❌"
        details["Prometheus"] = "Метрикалар жиналуы" if resp.status_code == 200 else "Байланысқа шықты"
    except:
        checks["Prometheus"] = "❌"
        details["Prometheus"] = "Қосыла алмады"
    
    try:
        resp = requests.get(f"http://alertmanager:9093/-/healthy", timeout=5)
        checks["AlertManager"] = "✅" if resp.status_code == 200 else "❌"
        details["AlertManager"] = "Ескертулер жіберілуде" if resp.status_code == 200 else "Өшік"
    except:
        checks["AlertManager"] = "❓"
        details["AlertManager"] = "Қосыла алмады"
    
    try:
        resp = requests.get("http://node_exporter:9100/metrics", timeout=5)
        checks["Node Exporter"] = "✅" if resp.status_code == 200 else "❌"
        details["Node Exporter"] = "Метрикалар түсіндіріліп тұр" if resp.status_code == 200 else "Өшік"
    except:
        checks["Node Exporter"] = "❌"
        details["Node Exporter"] = "Қосыла алмады"

    try:
        resp = requests.get(f"{PROMETHEUS_URL}/api/v1/query?query=up", timeout=5)
        checks["Prometheus API"] = "✅" if resp.status_code == 200 else "❌"
        details["Prometheus API"] = "API жұмыс істейді" if resp.status_code == 200 else "API қосыла алмады"
    except:
        checks["Prometheus API"] = "❌"
        details["Prometheus API"] = "Қосыла алмады"

    try:
        resp = requests.get(f"http://grafana:3000/api/health", timeout=5)
        checks["Grafana"] = "✅" if resp.status_code == 200 else "❌"
        details["Grafana"] = "Графика жүзегі істейді" if resp.status_code == 200 else "Өшік"
    except:
        checks["Grafana"] = "❌"
        details["Grafana"] = "Қосыла алмады"

    msg = "❤️ *Health Check*\n\n"
    for service in checks:
        msg += f"{checks[service]} *{service}*\n   {details[service]}\n\n"

    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_keyboard())

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/help"""
    await update.message.reply_text(
        "🤖 *Admin Bot* — Сервер мониторинг ботының көмегі\n\n"
        "📋 *Командалар:*\n"
        "`/start`   — қарсы алу\n"
        "`/status`  — сервер жағдайы (орташа)\n"
        "`/metrics` — толық метрикалар (ішінара сипаттамасы)\n"
        "`/health`  — барлық сервистердің құндылығы\n"
        "`/help`    — бұл көмек\n\n"
        "💡 *Ескерту:*\n"
        "• Алерттар автоматты түрде Telegram-ға жіберіледі\n"
        "• Grafana: http://localhost:3000\n"
        "• Prometheus: http://localhost:9090",
        parse_mode="Markdown",
        reply_markup=get_keyboard()
    )

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатия кнопок"""
    text = update.message.text
    
    if text == "📊 Status":
        await status(update, context)
    elif text == "📈 Metrics":
        await metrics(update, context)
    elif text == "❤️ Health":
        await health(update, context)
    elif text == "❓ Help":
        await help_cmd(update, context)

if __name__ == "__main__":
    if TELEGRAM_TOKEN == "YOUR_BOT_TOKEN":
        print("❌ TELEGRAM_TOKEN орнатылмаған!")
        exit(1)
    
    logger.info(f"🤖 Admin Bot іске қосылды...")
    
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("metrics", metrics))
    app.add_handler(CommandHandler("health", health))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_button))
    
    logger.info("✅ Бот дайын. Polling режимінде іске қосылды...")
    app.run_polling()
