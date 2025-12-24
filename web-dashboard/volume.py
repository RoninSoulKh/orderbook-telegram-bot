import json
import websocket
import dash
from dash import dcc, html
from dash.dependencies import Output, Input
import plotly.graph_objs as go
from collections import defaultdict
import threading
from queue import Queue
import time

# URL WebSocket API для получения данных глубины ордеров для BTC/USDT
ws_url_btcusdt = "wss://fstream.binance.com/ws/btcusdt@depth"

# Глобальные переменные для хранения данных
order_book_bids = defaultdict(float)
order_book_asks = defaultdict(float)
current_price = 0  # Переменная для хранения текущей цены

data_queue = Queue()  # Очередь для получения данных от WebSocket

# Функция для обработки сообщений WebSocket
def on_message(ws, message):
    data_queue.put(message)

# Настройка WebSocket
def setup_websocket():
    try:
        ws = websocket.WebSocketApp(ws_url_btcusdt,
                                    on_message=on_message,
                                    on_error=lambda ws, error: print(f"WebSocket error: {error}"),
                                    on_close=lambda ws: print("WebSocket closed"))
        ws.run_forever()
    except Exception as e:
        print(f"WebSocket setup error: {e}")
        time.sleep(5)  # Подождать 5 секунд перед повторной попыткой
        setup_websocket()

# Запуск WebSocket в фоновом потоке
ws_thread = threading.Thread(target=setup_websocket)
ws_thread.start()

# Запуск потока для обновления данных
def update_data():
    global order_book_bids, order_book_asks, current_price
    while True:
        try:
            message = data_queue.get()
            data = json.loads(message)
            
            # Обновление данных о бид и аск ордерах
            for bid in data['b']:
                price = float(bid[0])
                volume = float(bid[1])
                order_book_bids[price] = volume
            
            for ask in data['a']:
                price = float(ask[0])
                volume = float(ask[1])
                order_book_asks[price] = volume
            
            # Обновление текущей цены на основе средней цены между наименьшей аской и наибольшим бидом
            if order_book_bids and order_book_asks:
                current_price = (max(order_book_bids.keys()) + min(order_book_asks.keys())) / 2
        
        except Exception as e:
            print(f"Error updating data: {e}")

data_thread = threading.Thread(target=update_data)
data_thread.start()

# Настройка Dash
app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Graph(id='order-book-bars'),
    dcc.Interval(
        id='interval-component',
        interval=1*1000,  # обновление каждую секунду
        n_intervals=0
    )
])

# Функция для создания визуализации стакана ордеров (баров)
def create_order_book_bars():
    # Получаем только ближайшие к текущей цене уровни цен
    price_range = 10000  # Диапазон цен, который мы будем показывать

    bids = [{'price': price, 'volume': volume} for price, volume in order_book_bids.items()
            if current_price - price_range <= price <= current_price]
    asks = [{'price': price, 'volume': volume} for price, volume in order_book_asks.items()
            if current_price <= price <= current_price + price_range]
    
    # Сортировка бидов и асков для корректного отображения
    bids = sorted(bids, key=lambda x: x['price'], reverse=True)
    asks = sorted(asks, key=lambda x: x['price'])

    bid_prices = [bid['price'] for bid in bids]
    bid_volumes = [bid['volume'] for bid in bids]
    ask_prices = [ask['price'] for ask in asks]
    ask_volumes = [ask['volume'] for ask in asks]
    
    trace_bids = go.Bar(
        x=bid_volumes,
        y=bid_prices,
        orientation='h',
        name='Bids',
        text=bid_volumes,  # отображение объемов по центру
        textposition='auto',  # автоматическое позиционирование текста
        marker=dict(color='green')
    )

    trace_asks = go.Bar(
        x=ask_volumes,
        y=ask_prices,
        orientation='h',
        name='Asks',
        text=ask_volumes,  # отображение объемов по центру
        textposition='auto',  # автоматическое позиционирование текста
        marker=dict(color='red')
    )

    layout = go.Layout(
        title=f'Order Book - BTC/USDT (Price: {current_price:.2f})',
        xaxis=dict(title='Volume'),
        yaxis=dict(title='Price'),
        barmode='overlay',
        height=600
    )

    return {'data': [trace_bids, trace_asks], 'layout': layout}

# Обновление графика стакана ордеров
@app.callback(
    Output('order-book-bars', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_order_book_bars(n):
    return create_order_book_bars()

if __name__ == '__main__':
    app.run_server(debug=True, host='127.0.0.1', port=8050)
