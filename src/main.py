import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton, QDialog, QScrollArea, QGroupBox, QFormLayout, QTextEdit
from PySide6.QtCore import Qt, QThread, Signal
from config_manager import ConfigurationManager
from settings_window import SettingsWindow
from network_diagnostics import get_network_info, ping_host, tracert_host

class DiagnosticWorker(QThread):
    # Signals to communicate with the main thread
    info_update = Signal(str)
    result_update = Signal(str)
    finished = Signal()

    def __init__(self, config_manager: ConfigurationManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager

    def run(self):
        self.result_update.emit("診斷開始...<br>")
        self.info_update.emit("正在獲取網路資訊...")
        net_info = get_network_info()
        self.result_update.emit(f"--- 網路資訊 ---<br>")
        self.result_update.emit(f"介面卡名稱: {net_info.get('adapter_name')}<br>")
        self.result_update.emit(f"連線狀態: {net_info.get('status')}<br>")
        self.result_update.emit(f"連線類型: {net_info.get('connection_type')}<br>")
        self.result_update.emit(f"IP 位址: {net_info.get('ip_address')}<br>")
        self.result_update.emit(f"子網路遮罩: {net_info.get('subnet_mask')}<br>")
        self.result_update.emit(f"預設閘道: {net_info.get('default_gateway')}<br>")
        self.result_update.emit(f"DNS 伺服器: {', '.join(net_info.get('dns_servers'))}<br><br>")

        # Get settings for tests
        gateway_ip = self.config_manager.get_setting('NetworkSettings', 'GatewayIP')
        internal_server_ip = self.config_manager.get_setting('NetworkSettings', 'InternalServerIP')
        test_website = self.config_manager.get_setting('NetworkSettings', 'TestWebsite')
        ping_count = int(self.config_manager.get_setting('TestParameters', 'PingCount'))
        ping_timeout = int(self.config_manager.get_setting('TestParameters', 'PingTimeout'))
        tracert_max_hops = int(self.config_manager.get_setting('TestParameters', 'TracertMaxHops'))

        # --- Test 1: Ping Gateway ---
        self.info_update.emit(f"正在 Ping 預設閘道 ({gateway_ip})...")
        ping_gw_result = ping_host(gateway_ip, count=ping_count, timeout=ping_timeout)
        self.result_update.emit(f"--- Ping 預設閘道 ({gateway_ip}) ---<br>")
        if ping_gw_result["success"]:
            self.result_update.emit(f"<font color=\"green\">成功！</font>延遲: {ping_gw_result['latency']}。連接對外出口正常。<br><br>")
        else:
            self.result_update.emit(f"<font color=\"red\">失敗！</font>錯誤: {ping_gw_result['error']}。可能無法連接到路由器或內部網路。<br><br>")

        # --- Test 2: Ping Internal Server ---
        self.info_update.emit(f"正在 Ping 校內測試伺服器 ({internal_server_ip})...")
        ping_internal_result = ping_host(internal_server_ip, count=ping_count, timeout=ping_timeout)
        self.result_update.emit(f"--- Ping 校內測試伺服器 ({internal_server_ip}) ---<br>")
        if ping_internal_result["success"]:
            self.result_update.emit(f"<font color=\"green\">成功！</font>延遲: {ping_internal_result['latency']}。校內網路連線正常。<br><br>")
        else:
            self.result_update.emit(f"<font color=\"red\">失敗！</font>錯誤: {ping_internal_result['error']}。可能無法連接到校內伺服器，請檢查校內網路。<br><br>")

        # --- Test 3: Ping External IP (e.g., 8.8.8.8) ---
        self.info_update.emit("正在 Ping 外部 IP (8.8.8.8)...")
        ping_external_ip_result = ping_host("8.8.8.8", count=ping_count, timeout=ping_timeout)
        self.result_update.emit(f"--- Ping 外部 IP (8.8.8.8) ---<br>")
        if ping_external_ip_result["success"]:
            self.result_update.emit(f"<font color=\"green\">成功！</font>延遲: {ping_external_ip_result['latency']}。可連線到網際網路。<br><br>")
        else:
            self.result_update.emit(f"<font color=\"red\">失敗！</font>錯誤: {ping_external_ip_result['error']}。可能無法連線到網際網路，請檢查網路連線。<br><br>")

        # --- Test 4: Ping External Website (DNS Test) ---
        self.info_update.emit(f"正在 Ping 外部網站 ({test_website})...")
        ping_website_result = ping_host(test_website, count=ping_count, timeout=ping_timeout)
        self.result_update.emit(f"--- Ping 外部網站 ({test_website}) ---<br>")
        if ping_website_result["success"]:
            self.result_update.emit(f"<font color=\"green\">成功！</font>延遲: {ping_website_result['latency']}。DNS 解析及網站連線正常。<br><br>")
        else:
            self.result_update.emit(f"<font color=\"red\">失敗！</font>錯誤: {ping_website_result['error']}。可能無法解析網域名稱或網站無法連線。<br><br>")

        # --- Test 5: Tracert External Website ---
        self.info_update.emit(f"正在追蹤到外部網站 ({test_website}) 的路徑...")
        tracert_result = tracert_host(test_website, max_hops=tracert_max_hops)
        self.result_update.emit(f"--- 追蹤到外部網站 ({test_website}) 的路徑 ---<br>")
        if tracert_result and not tracert_result[0].get("ip") == "Error":
            for hop in tracert_result:
                self.result_update.emit(f"  {hop.get('num')}. {hop.get('ip')} ({hop.get('latency')})<br>")
            self.result_update.emit("路徑追蹤完成，顯示網路封包經過的節點。<br><br>")
        else:
            self.result_update.emit(f"<font color=\"red\">追蹤路徑失敗！</font>錯誤: {tracert_result[0].get('ip')}。可能無法到達目標網站。<br><br>")

        self.info_update.emit("診斷完成！")
        self.finished.emit()


class NetworkDiagnosticTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("校園網路診斷工具")
        self.setGeometry(100, 100, 750, 650) # Adjusted size for more content

        self.config_manager = ConfigurationManager()
        self.diagnostic_worker = None # Initialize worker as None
        self._init_ui()
        self._refresh_settings_display() # Initial display of settings

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Current Settings Group ---
        settings_group = QGroupBox("當前設定")
        settings_layout = QFormLayout()
        self.gateway_label = QLabel()
        self.dns_label = QLabel()
        self.test_website_label = QLabel()
        self.internal_server_ip_label = QLabel() # New label for internal server IP

        # Set font for current settings labels
        font = self.gateway_label.font()
        font.setPointSize(12)
        self.gateway_label.setFont(font)
        self.dns_label.setFont(font)
        self.test_website_label.setFont(font)
        self.internal_server_ip_label.setFont(font) # Apply font to new label

        settings_layout.addRow("預設閘道:", self.gateway_label)
        settings_layout.addRow("主要 DNS:", self.dns_label)
        settings_layout.addRow("校內測試伺服器:", self.internal_server_ip_label) # Moved above Test Website
        settings_layout.addRow("測試網站:", self.test_website_label)
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)

        # Status/Progress Label
        self.status_label = QLabel("準備就緒，請點擊 '開始診斷'。")
        main_layout.addWidget(self.status_label)

        # --- Diagnostic Results Group ---
        results_group = QGroupBox("診斷結果")
        results_layout = QVBoxLayout()
        self.results_text_area = QTextEdit("診斷結果將顯示在此...") # Changed to QTextEdit
        self.results_text_area.setReadOnly(True) # Make it read-only
        
        # Increase font size for results_text_area
        font = self.results_text_area.font()
        font.setPointSize(12) # Adjust font size as needed
        self.results_text_area.setFont(font)

        # QTextEdit does not need QScrollArea directly, it's scrollable by default
        results_layout.addWidget(self.results_text_area)
        results_group.setLayout(results_layout)
        main_layout.addWidget(results_group)

        # --- Buttons ---
        button_layout = QHBoxLayout() # Use QHBoxLayout for buttons
        settings_button = QPushButton("設定")
        settings_button.clicked.connect(self._open_settings)
        button_layout.addWidget(settings_button)

        self.start_diagnosis_button = QPushButton("開始診斷")
        self.start_diagnosis_button.clicked.connect(self._start_diagnosis)
        button_layout.addWidget(self.start_diagnosis_button)

        copy_button = QPushButton("複製結果")
        copy_button.clicked.connect(self._copy_results_to_clipboard)
        button_layout.addWidget(copy_button)

        main_layout.addLayout(button_layout)

    def _refresh_settings_display(self):
        """Refreshes the settings displayed on the main window."""
        self.gateway_label.setText(
            f"{self.config_manager.get_setting('NetworkSettings', 'GatewayIP')}"
        )
        self.dns_label.setText(
            f"{self.config_manager.get_setting('NetworkSettings', 'PrimaryDNS')}"
        )
        self.test_website_label.setText(
            f"{self.config_manager.get_setting('NetworkSettings', 'TestWebsite')}"
        )
        self.internal_server_ip_label.setText(
            f"{self.config_manager.get_setting('NetworkSettings', 'InternalServerIP')}"
        )

    def _open_settings(self):
        settings_dialog = SettingsWindow(self.config_manager, self)
        if settings_dialog.exec() == QDialog.Accepted:
            self._refresh_settings_display() # Refresh display if settings were saved

    def _start_diagnosis(self):
        self.start_diagnosis_button.setEnabled(False) # Disable button during diagnosis
        self.results_text_area.clear()
        self.status_label.setText("正在啟動診斷...")

        self.diagnostic_worker = DiagnosticWorker(self.config_manager)
        self.diagnostic_worker.info_update.connect(self.status_label.setText)
        self.diagnostic_worker.result_update.connect(self._append_result_text)
        self.diagnostic_worker.finished.connect(self._diagnosis_finished)
        self.diagnostic_worker.start()

    def _append_result_text(self, text):
        self.results_text_area.append(text) # Changed to append for QTextEdit

    def _diagnosis_finished(self):
        self.start_diagnosis_button.setEnabled(True) # Re-enable button
        self.status_label.setText("診斷完成！")

    def _copy_results_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.results_text_area.toPlainText())
        self.status_label.setText("診斷結果已複製到剪貼簿！")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NetworkDiagnosticTool()
    window.show()
    sys.exit(app.exec())