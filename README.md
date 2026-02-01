# 📊 Crypto OrderBook Tools

<div align="center">

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue)
![Binance](https://img.shields.io/badge/Binance-API-yellow)
![License](https://img.shields.io/badge/license-MIT-green)

**Telegram бот и веб-дашборд для визуального анализа стакана ордеров криптовалют (Binance)**

</div>

---

## 📌 О проекте

Набор инструментов для анализа стакана ордеров в стиле CoinGlass.

Проект состоит из двух независимых частей:

1. **🤖 Telegram Bot**  
   Быстро отправляет визуализацию стакана ордеров прямо в Telegram в виде PNG-изображения.

2. **🌐 Web Dashboard**  
   Веб-интерфейс на Dash для анализа стакана ордеров в реальном времени (BTC/USDT).

Проект создан как учебный и портфолио-проект с упором на:
- чистую структуру
- безопасность (без токенов в репозитории)
- понятный запуск

---

## 🤖 Telegram Bot

### Возможности
- Получение стакана ордеров с Binance (spot / futures)
- Визуализация bid / ask объёмов
- Отправка графика **в виде PNG прямо в чат**
- Поддержка команд и текстовых тикеров

### Примеры
![Image](https://github.com/user-attachments/assets/6b838e81-de1d-470e-b29b-5d9f7205012b)
![Image](https://github.com/user-attachments/assets/b16ef0d6-e821-4c0e-af51-0fd6e328ac6f)
![Image](https://github.com/user-attachments/assets/8efea495-fd1a-4cfb-81d0-e01ce01f00b5)

### Использование
- Команда:
/orderbook btcusdt

- Или просто отправь тикер текстом:
ethusdt

Бот автоматически:
- запрашивает стакан ордеров с Binance (spot / futures)
- строит визуализацию bid / ask объёмов
- отправляет PNG-изображение прямо в чат

---

## ⚙️ Установка и запуск

### 1. Клонировать репозиторий
git clone https://github.com/RoninSoulKh/orderbook-telegram-bot.git
cd orderbook-telegram-bot

### 2. Telegram Bot
cd telegram-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

Создай файл .env на основе примера:
cp .env.example .env

Укажи токен Telegram-бота:
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN

Запуск бота:
python bot.py

---

## 🌐 Web Dashboard

Веб-дашборд для отображения стакана ордеров BTC/USDT в реальном времени.

cd web-dashboard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python volume.py

После запуска открой в браузере:
http://127.0.0.1:8050
