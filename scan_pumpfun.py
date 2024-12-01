import websocket
import json
import time
from datetime import datetime
import threading
from database import TokenDatabase
import asyncio
from analyzer import TokenAnalyzer

class PumpFunScanner:
    def __init__(self):
        self.ws = None
        self.db = TokenDatabase()  # 初始化数据库连接
        
        # 监控的代币信息
        self.monitored_tokens = {}  # {token_address: TokenMonitor}
        
        # WebSocket连接URL
        self.ws_url = 'wss://pumpportal.fun/api/data'
        
        # 添加 TokenAnalyzer 实例
        self.analyzer = TokenAnalyzer()

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            print(f"收到WebSocket消息: {data}")  # 调试信息
            
            # 处理新代币创建事件
            if data.get('txType') == 'create':  # 修改这里，使用txType而不是type
                self.process_create(data)
            
            if data.get('txType') == 'buy' or data.get('txType') == 'sell':
                self.process_trade(data)

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

    async def should_monitor_token(self, token_info):
        """
        判断是否需要监控该代币
        基于 Google 搜索结果判断
        """
        try:
            # 获取代币的提及分析
            analysis = await self.analyzer.analyze_token_mentions(
                token_info['token_address'],
                token_info['token_name']
            )
            
            # 如果总提及次数超过10，则开始监控
            return analysis['total_score'] > 10
            
        except Exception as e:
            print(f"检查代币提及度时出错: {e}")
            return False

    def process_trade(self, data):
        """处理交易数据"""
        token_address = data.get('mint')
        if token_address in self.monitored_tokens:
            monitor = self.monitored_tokens[token_address]
            
            trade_info = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'token_address': token_address,
                'trader_address': data.get('traderPublicKey'),
                'token_amount': data.get('tokenAmount', 0),
                'sol_amount': data.get('vSolInBondingCurve', 0),
                'market_cap': data.get('marketCapSol', 0),
                'bonding_curve': data.get('bondingCurveKey'),
                'v_tokens': data.get('vTokensInBondingCurve', 0),
                'v_sol': data.get('vSolInBondingCurve', 0),
                'type': data.get('txType'),
                'signature': data.get('signature', '')  # 添加交易签名
            }
            
            # 存入数据库
            self.db.add_trade(trade_info)
            
            # 更新监控信息
            monitor = self.monitored_tokens[token_address]
            monitor.update_trade(trade_info)
            
            # 检查是否有异常交易
            if monitor.check_suspicious_activity():
                self.alert_suspicious_activity(token_address, monitor)

    def process_create(self, data):
        """处理新代币数据"""
        token_info = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'token_address': data.get('mint'),
            'token_name': data.get('name'),
            'token_symbol': data.get('symbol'),
            'market_cap': data.get('marketCapSol', 0),  # 使用marketCapSol
            'initial_buy': data.get('initialBuy', 0),   # 添加initialBuy
            'v_tokens': data.get('vTokensInBondingCurve', 0),  # 添加代币数量
            'v_sol': data.get('vSolInBondingCurve', 0)  # 添加SOL数量
        }
        
        print(f"处理新代币数据: {token_info}")
        
        # 存入数据库
        if self.db.add_new_token(token_info):
            print(f"新代币已添加到数据库: {token_info['token_name']}")
            
            # 使用异步方式调用 should_monitor_token
            loop = asyncio.get_event_loop()
            should_monitor = loop.run_until_complete(self.should_monitor_token(token_info))
            
            if should_monitor:
                self.monitored_tokens[token_info['token_address']] = TokenMonitor(token_info)
                print(f"开始监控代币: {token_info['token_name']}")

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

class TokenMonitor:
    def __init__(self, token_info):
        self.token_info = token_info
        self.market_cap = token_info['market_cap']
        self.trades = []
        self.trader_stats = {}  # {trader_address: TraderStats}
        self.last_update = datetime.now()
        
        # 警报阈值
        self.large_trade_threshold = 1000  # SOL
        self.rapid_trades_threshold = 3     # 次数
        self.rapid_trades_window = 300      # 5分钟
        
    def update_trade(self, trade_info):
        """更新交易信息"""
        self.trades.append(trade_info)
        self.market_cap = trade_info['market_cap']
        
        trader = trade_info['trader_address']
        if trader not in self.trader_stats:
            self.trader_stats[trader] = TraderStats()
            
        self.trader_stats[trader].add_trade(trade_info)
        self.last_update = datetime.now()
        
    def check_suspicious_activity(self):
        """检查可疑活动"""
        suspicious = False
        
        # 检查大额交易
        for trade in self.trades[-10:]:  # 只检查最近10笔交易
            if trade['token_amount'] * trade['market_cap'] > self.large_trade_threshold:
                suspicious = True
                break
        
        # 检查频繁交易
        for stats in self.trader_stats.values():
            if stats.check_rapid_trades(self.rapid_trades_threshold, self.rapid_trades_window):
                suspicious = True
                break
                
        return suspicious

class TraderStats:
    def __init__(self):
        self.trades = []
        self.total_buy_amount = 0
        self.total_sell_amount = 0
        self.last_trade_time = None
        
    def add_trade(self, trade_info):
        """添加新的交易记录"""
        self.trades.append(trade_info)
        self.last_trade_time = datetime.now()
        
        if trade_info['type'] == 'buy':
            self.total_buy_amount += trade_info['token_amount']
        else:
            self.total_sell_amount += trade_info['token_amount']
            
    def check_rapid_trades(self, threshold, window):
        """检查是否存在频繁交易"""
        if len(self.trades) < threshold:
            return False
            
        recent_trades = [t for t in self.trades 
                        if (datetime.now() - datetime.strptime(t['timestamp'], "%Y-%m-%d %H:%M:%S")).seconds < window]
        
        return len(recent_trades) >= threshold