from database import TokenDatabase
from PyQt6.QtWidgets import (QMainWindow, QApplication, QTableWidget, 
                           QTableWidgetItem, QVBoxLayout, QHBoxLayout, 
                           QWidget, QLabel, QLineEdit, QPushButton)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPalette, QColor, QFont
import sys
from datetime import datetime

class CyberpunkUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = TokenDatabase()
        self.start_time = datetime.now()  # 记录程序启动时间
        self.last_trade_id = 0  # 只需要记录最后的交易ID
        self.last_monitor_id = 0  # 监控的最后ID
        self.setWindowTitle("Pump.fun Token Scanner - Cyberpunk Edition")
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0a0a0f;
            }
            QTableWidget {
                background-color: #1a1a2e;
                color: #00ff9f;
                gridline-color: #ff0055;
                border: 2px solid #ff0055;
                border-radius: 5px;
            }
            QTableWidget::item {
                border-bottom: 1px solid #ff0055;
            }
            QTableWidget::item:selected {
                background-color: #ff005577;
            }
            QHeaderView::section {
                background-color: #ff0055;
                color: #000000;
                font-weight: bold;
                border: 2px solid #ff0055;
            }
            QLabel {
                color: #00ff9f;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        
        # 设置窗口大小
        self.setMinimumSize(1200, 800)
        
        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 创建标题标签
        title = QLabel("PUMP.FUN MEME TOKEN RADAR")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 24px;
            color: #ff0055;
            margin: 20px;
            font-family: 'Courier New';
            text-shadow: 0 0 10px #ff0055;
        """)
        layout.addWidget(title)
        
        # 添加搜索区域
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入代币地址...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a2e;
                color: #00ff9f;
                border: 2px solid #ff0055;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
        """)
        
        self.monitor_button = QPushButton("监控")
        self.monitor_button.setStyleSheet("""
            QPushButton {
                background-color: #ff0055;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff3377;
            }
        """)
        self.monitor_button.clicked.connect(self.start_monitoring)
        
        search_layout.addWidget(QLabel("代币监控:"))
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.monitor_button)
        
        # 在标题下方添加搜索区域
        layout.insertLayout(1, search_layout)
        
        # 添加监控信息表格
        monitor_label = QLabel("代币监控信息")
        monitor_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(monitor_label)
        
        self.monitor_table = QTableWidget()
        self.monitor_table.setColumnCount(8)
        self.monitor_table.setHorizontalHeaderLabels([
            "时间", "代币地址", "交易类型", "价格(SOL)", 
            "数量", "交易额(SOL)", "交易者地址", "持仓变化"
        ])
        layout.addWidget(self.monitor_table)
        
        # 设置监控表格列宽
        header = self.monitor_table.horizontalHeader()
        for i in range(self.monitor_table.columnCount()):
            header.setSectionResizeMode(i, header.ResizeMode.Stretch)
        
        # 存储当前监控的代币
        self.monitored_tokens = set()
        
        # 创建新代币表格
        self.token_table = QTableWidget()
        self.token_table.setColumnCount(5)
        self.token_table.setHorizontalHeaderLabels([
            "时间", "代币名称", "符号", "地址", "市值(SOL)"
        ])
        layout.addWidget(self.token_table)
        
        # 创建交易表格标题
        trades_label = QLabel("最新交易记录")
        trades_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(trades_label)
        
        # 创建交易表格
        self.trades_table = QTableWidget()
        self.trades_table.setColumnCount(5)
        self.trades_table.setHorizontalHeaderLabels([
            "时间", "代币地址", "价格", "数量", "类型"
        ])
        layout.addWidget(self.trades_table)
        
        # 设置表格列宽
        for table in [self.token_table, self.trades_table]:
            header = table.horizontalHeader()
            for i in range(table.columnCount()):
                header.setSectionResizeMode(i, header.ResizeMode.Stretch)
                
        # 使用字典来存储最后读取的ID和时间戳
        self.last_read = {
            'tokens': {'id': 0, 'timestamp': None},
            'trades': {'id': 0, 'timestamp': None},
            'monitors': {}  # {token_address: last_id}
        }
        
        # 设置更新间隔为1秒
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)

    def start_monitoring(self):
        """开始监控指定代币"""
        token_address = self.search_input.text().strip()
        if token_address:
            if token_address not in self.monitored_tokens:
                self.monitored_tokens.add(token_address)
                print(f"开始监控代币: {token_address}")
                # 清空上次的监控数据
                self.last_monitor_id = 0
                self.monitor_table.setRowCount(0)
            else:
                print(f"已在监控此代币: {token_address}")

    def update_data(self):
        try:
            current_time = datetime.now()
            
            # 获取新的代币数据
            new_tokens = self.db.get_new_tokens(
                self.last_read['tokens']['id'],
                self.last_read['tokens'].get('timestamp')
            )
            
            if new_tokens:
                print(f"UI: 读取到 {len(new_tokens)} 条新代币数据")
                for token in new_tokens:
                    row_position = self.token_table.rowCount()
                    self.token_table.insertRow(row_position)
                    
                    items = [
                        token[4],  # creation_time
                        token[2],  # token_name
                        token[3],  # token_symbol
                        token[1],  # token_address
                        str(token[5]),  # market_cap
                    ]
                    
                    for col, item in enumerate(items):
                        table_item = QTableWidgetItem(str(item))
                        table_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.token_table.setItem(row_position, col, table_item)
                    
                    self.last_read['tokens']['id'] = token[0]  # rowid
                    self.last_read['tokens']['timestamp'] = token[4]  # creation_time
                
                self.token_table.scrollToBottom()
            
            # 获取新的交易数据
            new_trades = self.db.get_new_trades(
                self.last_read['trades']['id'],
                self.last_read['trades'].get('timestamp')
            )
            
            if new_trades:
                print(f"UI: 读取到 {len(new_trades)} 条新交易数据")
                for trade in new_trades:
                    row_position = self.trades_table.rowCount()
                    self.trades_table.insertRow(row_position)
                    
                    items = [
                        trade[3],  # timestamp
                        trade[1],  # token_address
                        str(trade[6]),  # sol_amount
                        str(trade[5]),  # token_amount
                        trade[4]   # type
                    ]
                    
                    for col, item in enumerate(items):
                        table_item = QTableWidgetItem(str(item))
                        table_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        
                        if col == 4:  # 交易类型列
                            if item.lower() == 'buy':
                                table_item.setForeground(QColor('#00ff00'))
                            elif item.lower() == 'sell':
                                table_item.setForeground(QColor('#ff0000'))
                                
                        self.trades_table.setItem(row_position, col, table_item)
                    
                    self.last_read['trades']['id'] = trade[0]  # id
                    self.last_read['trades']['timestamp'] = trade[3]  # timestamp
                
                self.trades_table.scrollToBottom()
            
            # 更新监控数据
            for token_address in self.monitored_tokens:
                if token_address not in self.last_read['monitors']:
                    self.last_read['monitors'][token_address] = 0
                
                trades = self.db.get_token_trades(
                    token_address,
                    self.last_read['monitors'][token_address]
                )
                
                if trades:
                    print(f"UI: 读取到 {len(trades)} 条监控数据")
                    for trade in trades:
                        row_position = self.monitor_table.rowCount()
                        self.monitor_table.insertRow(row_position)
                        
                        trade_value = float(trade[5]) * float(trade[6])
                        
                        items = [
                            trade[3],  # timestamp
                            trade[1],  # token_address
                            trade[4],  # type
                            str(trade[6]),  # sol_amount
                            str(trade[5]),  # token_amount
                            f"{trade_value:.4f}",
                            trade[2],  # trader_address
                            str(trade[8] if len(trade) > 8 else '')
                        ]
                        
                        for col, item in enumerate(items):
                            table_item = QTableWidgetItem(str(item))
                            table_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                            
                            if col == 2:  # 交易类型列
                                if item.lower() == 'buy':
                                    table_item.setForeground(QColor('#00ff00'))
                                elif item.lower() == 'sell':
                                    table_item.setForeground(QColor('#ff0000'))
                            
                            self.monitor_table.setItem(row_position, col, table_item)
                        
                        self.last_read['monitors'][token_address] = trade[0]
                    
                    self.monitor_table.scrollToBottom()
                    
        except Exception as e:
            print(f"更新数据时出错: {e}")