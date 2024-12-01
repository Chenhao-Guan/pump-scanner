import sqlite3
from datetime import datetime
import threading
import queue

class TokenDatabase:
    def __init__(self):
        self.db_queue = queue.Queue()
        self._local = threading.local()
        self.init_database()
        
    def get_connection(self):
        """为每个线程获取独立的数据库连接"""
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect('pump_fun.db')
            self._local.cursor = self._local.conn.cursor()
        return self._local.conn, self._local.cursor

    def init_database(self):
        """初始化数据库表"""
        conn, cursor = self.get_connection()
        # 代币基本信息表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            token_address TEXT PRIMARY KEY,
            token_name TEXT,
            token_symbol TEXT,
            creation_time TIMESTAMP,
            market_cap REAL,
            initial_buy REAL,
            v_tokens REAL,
            v_sol REAL,
            UNIQUE(token_address)
        )
        ''')
        
        # 交易记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_address TEXT,
            trader_address TEXT,
            timestamp TIMESTAMP,
            type TEXT,  -- 'buy' or 'sell'
            token_amount REAL,
            sol_amount REAL,
            market_cap REAL,
            bonding_curve TEXT,
            v_tokens REAL,
            v_sol REAL,
            transaction_signature TEXT UNIQUE,  -- 添加交易签名作为唯一标识
            FOREIGN KEY (token_address) REFERENCES tokens(token_address)
        )
        ''')
        
        # 交易者统计表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS trader_stats (
            trader_address TEXT,
            token_address TEXT,
            total_buy_amount REAL,
            total_sell_amount REAL,
            trade_count INTEGER,
            last_trade_time TIMESTAMP,
            PRIMARY KEY (trader_address, token_address),
            FOREIGN KEY (token_address) REFERENCES tokens(token_address)
        )
        ''')
        
        # 可疑活动记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS suspicious_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_address TEXT,
            timestamp TIMESTAMP,
            activity_type TEXT,  -- 'large_trade', 'rapid_trades', 'price_manipulation'
            description TEXT,
            severity INTEGER,  -- 1-5
            FOREIGN KEY (token_address) REFERENCES tokens(token_address)
        )
        ''')
        
        conn.commit()

    def add_new_token(self, token_info):
        """添加新代币"""
        try:
            conn, cursor = self.get_connection()
            print(f"数据库: 尝试添加新代币 {token_info['token_address']}")
            
            # 首先检查是否已存在
            cursor.execute('SELECT 1 FROM tokens WHERE token_address = ?', 
                          (token_info['token_address'],))
            if cursor.fetchone():
                print(f"数据库: 代币已存在，跳过添加")
                return False
            
            cursor.execute('''
            INSERT OR IGNORE INTO tokens (
                token_address, token_name, token_symbol, creation_time,
                market_cap, initial_buy, v_tokens, v_sol
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                token_info['token_address'],
                token_info['token_name'],
                token_info['token_symbol'],
                token_info['timestamp'],
                token_info['market_cap'],
                token_info['initial_buy'],
                token_info['v_tokens'],
                token_info['v_sol']
            ))
            conn.commit()
            success = cursor.rowcount > 0
            print(f"数据库: {'成功' if success else '失败'}添加新代币")
            return success
        except Exception as e:
            print(f"添加新代币失败: {e}")
            return False

    def add_trade(self, trade_info):
        """记录交易"""
        try:
            conn, cursor = self.get_connection()
            print(f"数据库: 尝试添加新交易 {trade_info.get('signature', '')}")
            
            # 首先检查是否已存在
            cursor.execute('SELECT 1 FROM trades WHERE transaction_signature = ?', 
                          (trade_info.get('signature', ''),))
            if cursor.fetchone():
                print(f"数据库: 交易已存在，跳过添加")
                return
            
            cursor.execute('''
            INSERT OR IGNORE INTO trades (
                token_address, trader_address, timestamp, type,
                token_amount, sol_amount, market_cap, bonding_curve,
                v_tokens, v_sol, transaction_signature
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade_info['token_address'],
                trade_info['trader_address'],
                trade_info['timestamp'],
                trade_info['type'],
                trade_info['token_amount'],
                trade_info['sol_amount'],
                trade_info['market_cap'],
                trade_info['bonding_curve'],
                trade_info['v_tokens'],
                trade_info['v_sol'],
                trade_info.get('signature', '')
            ))
            conn.commit()
            print(f"数据库: {'成功' if cursor.rowcount > 0 else '失败'}添加新交易")
        except Exception as e:
            print(f"记录交易失败: {e}")

    def get_new_tokens(self, last_id, last_timestamp=None):
        """获取新代币数据"""
        conn, cursor = self.get_connection()
        if last_timestamp:
            cursor.execute('''
                SELECT rowid, *
                FROM tokens
                WHERE rowid > ? AND creation_time > ?
                ORDER BY creation_time DESC
            ''', (last_id, last_timestamp))
        else:
            cursor.execute('''
                SELECT rowid, *
                FROM tokens
                WHERE rowid > ?
                ORDER BY creation_time DESC
            ''', (last_id,))
        return cursor.fetchall()

    def get_new_trades(self, last_id, last_timestamp=None):
        """获取新交易数据"""
        conn, cursor = self.get_connection()
        if last_timestamp:
            cursor.execute('''
                SELECT *
                FROM trades
                WHERE id > ? AND timestamp > ?
                ORDER BY timestamp DESC
            ''', (last_id, last_timestamp))
        else:
            cursor.execute('''
                SELECT *
                FROM trades
                WHERE id > ?
                ORDER BY timestamp DESC
            ''', (last_id,))
        return cursor.fetchall()

    def get_token_trades(self, token_address, last_id=0):
        """获取指定代币的交易记录"""
        try:
            conn, cursor = self.get_connection()
            cursor.execute('''
                SELECT id, token_address, trader_address, timestamp, type,
                       token_amount, sol_amount, market_cap,
                       CASE 
                           WHEN type = 'buy' THEN token_amount
                           WHEN type = 'sell' THEN -token_amount
                           ELSE 0
                       END as balance_change
                FROM trades
                WHERE token_address = ? AND id > ?
                ORDER BY timestamp DESC
            ''', (token_address, last_id))
            return cursor.fetchall()
        except Exception as e:
            print(f"获取代币交易记录失败: {e}")
            return []