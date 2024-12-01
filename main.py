from scan_pumpfun import PumpFunScanner
from cyberpunk_ui import CyberpunkUI
from PyQt6.QtWidgets import QApplication
import sys
import threading
import os

if __name__ == "__main__":
    print("正在启动应用程序...")
    
    # 创建 Qt 应用
    app = QApplication(sys.argv)
    
    print("正在创建扫描器...")
    # 创建并启动扫描器
    scanner = PumpFunScanner()
    scanner.start_scanning()
    
    print("正在创建UI界面...")
    # 创建并显示 UI
    window = CyberpunkUI()
    window.show()
    
    print("应用程序开始运行...")
    # 运行应用
    sys.exit(app.exec())