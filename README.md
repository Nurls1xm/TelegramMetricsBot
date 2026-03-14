# 📊 TelegramMetricsBot

Server monitoring system with Prometheus, Grafana, AlertManager and Telegram bot.

## 🚀 Features

- ✅ Real-time metrics collection (CPU, RAM, Disk, Network)
- ✅ Beautiful Grafana dashboards
- ✅ Alert notifications in Telegram
- ✅ Telegram bot with `/status` and `/metrics` commands
- ✅ Full Docker Compose setup

## 📋 Quick Start
```bash
git clone https://github.com/Nurls1xm/TelegramMetricsBot.git
cd TelegramMetricsBot

# Update configs with your Telegram bot token and chat_id
nano docker-compose.yml
nano alertmanager/alertmanager.yml

# Run
docker-compose up -d

# Check
docker-compose ps
```

## 🌐 Access

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin2747)
- **AlertManager**: http://localhost:9093
- **Telegram Bot**: Send `/status` to your bot

## 📝 Configuration

See `docker-compose.yml`, `prometheus/prometheus.yml`, `alertmanager/alertmanager.yml`

