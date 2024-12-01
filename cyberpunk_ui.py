from PyQt6.QtWidgets import (QMainWindow, QApplication, QTableWidget, 
                           QTableWidgetItem, QVBoxLayout, QWidget, QLabel)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPalette, QColor, QFont
import json
import sys

class CyberpunkUI(QMainWindow):
    def __init__(self):
        super().__init__()
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
        
        # 创建新代币表格
        self.token_table = QTableWidget()
        self.token_table.setColumnCount(7)
        self.token_table.setHorizontalHeaderLabels([
            "时间", "代币名称", "符号", "地址", "市值(USD)", "增长率(%)", "净流入(USD)"
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
        
        # 设置定时器更新数据
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)  # 每秒更新一次
        
        # 初始化最后读取的位置
        self.last_token_position = 0
        self.last_trade_position = 0

    def update_data(self):
        # 更新代币数据
        try:
            with open('token_alerts.json', 'r') as f:
                lines = f.readlines()
                for line in lines[self.last_token_position:]:
                    data = json.loads(line)
                    row_position = self.token_table.rowCount()
                    self.token_table.insertRow(row_position)
                    
                    # 修改这里以匹配 token_info 的格式
                    items = [
                        data.get('timestamp', ''),
                        data.get('token_name', ''),
                        data.get('token_symbol', ''),
                        data.get('token_address', ''),
                        str(data.get('market_cap', 0)),
                        str(data.get('growth_rate', 0)) + '%',
                        str(data.get('net_inflow', 0))
                    ]
                    
                    for col, item in enumerate(items):
                        table_item = QTableWidgetItem(str(item))
                        table_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        
                        # 为增长率添加颜色
                        if col == 5:  # 增长率列
                            try:
                                growth = float(data.get('growth_rate', 0))
                                if growth > 0:
                                    table_item.setForeground(QColor('#00ff00'))
                                elif growth < 0:
                                    table_item.setForeground(QColor('#ff0000'))
                            except ValueError:
                                pass
                            
                        self.token_table.setItem(row_position, col, table_item)
                
                self.last_token_position = len(lines)
                # 自动滚动到最新数据
                self.token_table.scrollToBottom()
                
        except FileNotFoundError:
            print("token_alerts.json 文件不存在")
        except Exception as e:
            print(f"更新代币数据时出错: {e}")
        
        # 更新交易数据
        try:
            with open('trades.json', 'r') as f:
                lines = f.readlines()
                for line in lines[self.last_trade_position:]:
                    data = json.loads(line)
                    row_position = self.trades_table.rowCount()
                    self.trades_table.insertRow(row_position)
                    
                    items = [
                        data.get('timestamp', ''),
                        data.get('token_address', ''),
                        str(data.get('price', 0)),
                        str(data.get('amount', 0)),
                        data.get('type', '')
                    ]
                    
                    for col, item in enumerate(items):
                        table_item = QTableWidgetItem(str(item))
                        table_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        
                        # 为交易类型添加颜色
                        if col == 4:
                            if item.lower() == 'buy':
                                table_item.setForeground(QColor('#00ff00'))
                            elif item.lower() == 'sell':
                                table_item.setForeground(QColor('#ff0000'))
                            
                        self.trades_table.setItem(row_position, col, table_item)
                
                self.last_trade_position = len(lines)
                # 自动滚动到最新数据
                self.trades_table.scrollToBottom()
                
        except FileNotFoundError:
            print("trades.json 文件不存在")
        except Exception as e:
            print(f"更新交易数据时出错: {e}")