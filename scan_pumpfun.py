import websocket
import json
import time
from datetime import datetime
import threading

class PumpFunScanner:
    def __init__(self):
        self.ws = None
        self.scanned_tokens = set()
        
        # 设置筛选条件
        self.min_market_cap = 50000  # 最小市值(USD)
        self.min_growth_rate = 20    # 最小增长率(%)
        self.min_inflow = 10000      # 最小净流入(USD)
        
        # WebSocket连接URL
        self.ws_url = 'wss://pumpportal.fun/api/data'
        
        # 创建必要的文件
        for filename in ['token_alerts.json', 'trades.json']:
            try:
                with open(filename, 'a') as f:
                    pass
            except Exception as e:
                print(f"创建文件失败: {e}")

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            print(f"收到WebSocket消息: {data}")  # 调试信息
            
            # 处理新代币事件
            if data.get('type') == 'newToken':
                token_info = {
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'token_address': data.get('mint'),
                    'token_name': data.get('name'),
                    'token_symbol': data.get('symbol'),
                    'market_cap': data.get('marketCap', 0),
                    'growth_rate': data.get('priceChange24h', 0),
                    'net_inflow': data.get('volume24h', 0)
                }
                
                print(f"处理新代币数据: {token_info}")  # 调试信息
                
                # 直接写入文件，不进行筛选
                with open('token_alerts.json', 'a') as f:
                    json.dump(token_info, f)
                    f.write('\n')
                    f.flush()  # 确保立即写入
                print(f"数据已写入文件")  # 调试信息
                
                # 如果需要筛选，可以在写入后再进行
                if self.analyze_token(token_info):
                    self.scanned_tokens.add(token_info.get('token_address'))
                    print(f"代币已添加到已扫描集合")  # 调试信息
            
            # 处理交易事件
            elif data.get('type') == 'trade':
                trade_info = {
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'token_address': data.get('mint'),
                    'price': data.get('price'),
                    'amount': data.get('amount'),
                    'type': data.get('side')
                }
                
                with open('trades.json', 'a') as f:
                    json.dump(trade_info, f)
                    f.write('\n')
                    f.flush()  # 确保立即写入
                
        except Exception as e:
            print(f"处理WebSocket消息时出错: {e}")

    def on_error(self, ws, error):
        print(f"WebSocket错误: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("WebSocket连接关闭")
        # 尝试重新连接
        time.sleep(5)
        self.start_scanning()

    def on_open(self, ws):
        print("WebSocket连接已建立")
        # 订阅新代币事件
        subscribe_msg = {
            "method": "subscribeNewToken"
        }
        ws.send(json.dumps(subscribe_msg))

    def analyze_token(self, token_info):
        """分析代币是否满足条件"""
        if not token_info:
            return False
            
        market_cap = token_info.get('market_cap', 0)
        growth_rate = token_info.get('growth_rate', 0)
        inflow = token_info.get('net_inflow', 0)
        
        return (market_cap >= self.min_market_cap and 
                growth_rate >= self.min_growth_rate and 
                inflow >= self.min_inflow)

    def process_trade(self, trade_data):
        """处理交易数据"""
        if trade_data.get('mint') not in self.scanned_tokens:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            trade_info = {
                'timestamp': timestamp,
                'token_address': trade_data.get('mint'),
                'price': trade_data.get('price'),
                'amount': trade_data.get('amount'),
                'type': trade_data.get('side')  # buy/sell
            }
            
            with open('trades.json', 'a') as f:
                json.dump(trade_info, f)
                f.write('\n')

    def log_token(self, token_info):
        """记录符合条件的代币"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            'timestamp': timestamp,
            'token_address': token_info.get('address'),
            'token_name': token_info.get('name'),
            'token_symbol': token_info.get('symbol'),
            'market_cap': token_info.get('market_cap'),
            'growth_rate': token_info.get('growth_rate'),
            'net_inflow': token_info.get('net_inflow')
        }
        
        with open('token_alerts.json', 'a') as f:
            json.dump(log_entry, f)
            f.write('\n')
            
        print(f"发现新代币: {log_entry}")
        self.scanned_tokens.add(token_info.get('address'))

    def start_scanning(self):
        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        
        # 在单独的线程中运行WebSocket
        wst = threading.Thread(target=self.ws.run_forever)
        wst.daemon = True
        wst.start()