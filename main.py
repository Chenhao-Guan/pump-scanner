from scan_pumpfun import PumpFunScanner
from cyberpunk_ui import CyberpunkUI
from PyQt6.QtWidgets import QApplication
import sys
import threading

if __name__ == "__main__":
    # 创建 Qt 应用
    app = QApplication(sys.argv)
    
    # 创建并启动扫描器
    scanner = PumpFunScanner()
    scanner.start_scanning()
    
    # 创建并显示 UI
    window = CyberpunkUI()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())