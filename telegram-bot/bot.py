import requests
import plotly.graph_objs as go
import io
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Функция для чтения токена из файла
def read_bot_token(file_path="token.bot"):
    try:
        with open(file_path, "r") as file:
            for line in file:
                if line.startswith("BOT_TOKEN="):
                    return line.strip().split("=")[1].strip('"')
    except FileNotFoundError:
        print(f"Файл {file_path} не найден.")
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
    return None

# Чтение токена из файла
bot_token = read_bot_token()
if not bot_token:
    raise ValueError("Не удалось прочитать токен бота из файла.")

# Функция для получения данных о книге ордеров через REST API Binance (спот)
def get_spot_order_book(pair):
    url = f"https://api.binance.com/api/v3/depth?symbol={pair.upper()}&limit=5000"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Функция для получения данных о книге ордеров через REST API Binance (фьючерсы)
def get_futures_order_book(pair):
    url = f"https://fapi.binance.com/fapi/v1/depth?symbol={pair.upper()}&limit=5000"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Функция для создания визуализации стакана ордеров (баров)
def create_order_book_bars(pair, order_book):
    if not order_book or 'bids' not in order_book or 'asks' not in order_book:
        raise ValueError("Некорректные данные о книге ордеров")

    bids = [[float(price), float(volume)] for price, volume in order_book['bids']]
    asks = [[float(price), float(volume)] for price, volume in order_book['asks']]
    
    bids = sorted(bids, key=lambda x: x[0], reverse=True)
    asks = sorted(asks, key=lambda x: x[0])

    bid_prices = [bid[0] for bid in bids]
    bid_volumes = [bid[1] for bid in bids]
    ask_prices = [ask[0] for ask in asks]
    ask_volumes = [ask[1] for ask in asks]

    # Текущая цена (средняя между лучшим бидом и аском)
    current_price = (bids[0][0] + asks[0][0]) / 2 if bids and asks else 0

    # Определяем количество знаков после запятой для форматирования
    if current_price < 0.01:
        price_format = "{:.5f}"  # 8 знаков после запятой для очень маленьких цен
    else:
        price_format = "{:.3f}"  # 2 знака после запятой для обычных цен

    # Игнорируем ордера, которые находятся слишком близко к текущей цене (в пределах 1%)
    price_threshold = current_price * 0.01  # 1% от текущей цены

    # Находим максимальный BID (цена с самым большим объемом ниже текущей цены, с учетом порога)
    filtered_bids = [bid for bid in bids if bid[0] < current_price - price_threshold]
    max_bid = max(filtered_bids, key=lambda x: x[1], default=None) if filtered_bids else None
    max_bid_price = max_bid[0] if max_bid else None

    # Находим максимальный ASK (цена с самым большим объемом выше текущей цены, с учетом порога)
    filtered_asks = [ask for ask in asks if ask[0] > current_price + price_threshold]
    max_ask = max(filtered_asks, key=lambda x: x[1], default=None) if filtered_asks else None
    max_ask_price = max_ask[0] if max_ask else None

    # Увеличиваем диапазон цен для BTC
    if pair.upper() == 'BTCUSDT':
        min_price = current_price - 10000  # Расширяем диапазон на $10,000 ниже текущей цены
        max_price = current_price + 10000  # Расширяем диапазон на $10,000 выше текущей цены
    else:
        # Для других монет используем стандартный диапазон
        min_price = min(bid_prices + ask_prices) if bid_prices and ask_prices else current_price - 1000
        max_price = max(bid_prices + ask_prices) if bid_prices and ask_prices else current_price + 1000

    # График для бидов
    trace_bids = go.Bar(
        x=bid_prices,
        y=bid_volumes,
        orientation='v',
        name='Bids',
        marker=dict(color='green', opacity=0.7)
    )

    # График для асков
    trace_asks = go.Bar(
        x=ask_prices,
        y=ask_volumes,
        orientation='v',
        name='Asks',
        marker=dict(color='red', opacity=0.7)
    )

    # Пунктирная линия для текущей цены
    current_price_line = go.Scatter(
        x=[current_price, current_price],
        y=[0, max(bid_volumes + ask_volumes) * 1.1] if bid_volumes and ask_volumes else [0, 1],
        mode='lines',
        line=dict(color='yellow', dash='dash'),
        name=f'Current Price: {price_format.format(current_price)}'
    )

    # Аннотации для максимального BID и ASK
    annotations = []
    if max_bid_price:
        annotations.append(
            dict(
                x=max_bid_price,
                y=max([bid[1] for bid in bids]) if bids else 0,
                xref='x',
                yref='y',
                text=f"Макс. покупка: {price_format.format(max_bid_price)}",
                showarrow=False,
                bgcolor='rgba(0, 0, 0, 0)',
                font=dict(color='green', size=12),
                xanchor='center',
                yanchor='bottom'
            )
        )
    if max_ask_price:
        annotations.append(
            dict(
                x=max_ask_price,
                y=max([ask[1] for ask in asks]) if asks else 0,
                xref='x',
                yref='y',
                text=f"Макс. продажа: {price_format.format(max_ask_price)}",
                showarrow=False,
                bgcolor='rgba(0, 0, 0, 0)',
                font=dict(color='red', size=12),
                xanchor='center',
                yanchor='bottom'
            )
        )

    layout = go.Layout(
        title=f'Order Book - {pair.upper()}',
        xaxis=dict(
            title='Price',
            title_font=dict(color='white'),
            tickfont=dict(color='white'),
            showgrid=False,  # Убираем сетку на оси X
            range=[min_price, max_price]  # Увеличенный диапазон цен
        ),
        yaxis=dict(
            title='Volume',
            title_font=dict(color='white'),
            tickfont=dict(color='white'),
            showgrid=False  # Убираем сетку на оси Y
        ),
        barmode='overlay',
        height=600,
        plot_bgcolor='black',
        paper_bgcolor='black',
        font=dict(color='white'),
        annotations=annotations
    )

    return go.Figure(data=[trace_bids, trace_asks, current_price_line], layout=layout)

# Функция для отправки изображения в Telegram
async def send_image_to_telegram(chat_id, fig, pair):
    try:
        buf = io.BytesIO()
        fig.write_image(buf, format='png')
        buf.seek(0)
        await application.bot.send_photo(chat_id=chat_id, photo=buf)
        print(f"Image for {pair} sent successfully to Telegram.")  # Отладочное сообщение
    except Exception as e:
        print(f"Error sending image to Telegram: {e}")  # Сообщение об ошибке

# Обработчик команды /orderbook
async def orderbook_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        pair = context.args[0].lower()  # Получаем пару из аргумента команды
        order_book = get_spot_order_book(pair) or get_futures_order_book(pair)
        
        if order_book:
            fig = create_order_book_bars(pair, order_book)
            await send_image_to_telegram(update.message.chat_id, fig, pair)
        else:
            await update.message.reply_text(f"Не удалось получить данные для пары {pair}.")
    except IndexError:
        await update.message.reply_text("Используйте команду в формате: /orderbook <пара>, например /orderbook btcusdt")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

# Обработчик сообщений с тикером
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    
    # Проверяем, заканчивается ли сообщение на "usdt"
    if text.endswith('usdt'):
        pair = text.upper()
        order_book = get_spot_order_book(pair) or get_futures_order_book(pair)
        
        if order_book:
            fig = create_order_book_bars(pair, order_book)
            await send_image_to_telegram(update.message.chat_id, fig, pair)
        else:
            await update.message.reply_text(f"Не удалось получить данные для пары {pair}.")
    else:
        # Игнорируем сообщения, которые не заканчиваются на "usdt"
        return

# Создание приложения Telegram-бота
application = ApplicationBuilder().token(bot_token).build()

# Регистрация обработчиков команд и сообщений
application.add_handler(CommandHandler("orderbook", orderbook_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Запуск бота
print("Bot is running...")
application.run_polling()
