from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QGroupBox, QFormLayout
from config_manager import ConfigurationManager

class SettingsWindow(QDialog):
    def __init__(self, config_manager: ConfigurationManager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("設定")
        self.setGeometry(200, 200, 400, 450) # x, y, width, height

        self.config_manager = config_manager
        self.settings_fields = {}
        self._init_ui()
        self._load_settings_to_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        # Network Settings Group
        network_group = QGroupBox("網路設定")
        network_layout = QFormLayout()
        self.settings_fields['GatewayIP'] = QLineEdit()
        network_layout.addRow("預設閘道 IP:", self.settings_fields['GatewayIP'])
        self.settings_fields['PrimaryDNS'] = QLineEdit()
        network_layout.addRow("主要 DNS:", self.settings_fields['PrimaryDNS'])
        self.settings_fields['SecondaryDNS'] = QLineEdit()
        network_layout.addRow("次要 DNS:", self.settings_fields['SecondaryDNS'])
        self.settings_fields['InternalServerIP'] = QLineEdit()
        network_layout.addRow("校內測試伺服器 IP:", self.settings_fields['InternalServerIP'])
        self.settings_fields['TestWebsite'] = QLineEdit()
        network_layout.addRow("外部測試網站:", self.settings_fields['TestWebsite'])
        network_group.setLayout(network_layout)
        main_layout.addWidget(network_group)

        # Test Parameters Group
        test_params_group = QGroupBox("測試參數")
        test_params_layout = QFormLayout()
        self.settings_fields['PingCount'] = QLineEdit()
        test_params_layout.addRow("Ping 次數:", self.settings_fields['PingCount'])
        self.settings_fields['PingTimeout'] = QLineEdit()
        test_params_layout.addRow("Ping 逾時 (ms):", self.settings_fields['PingTimeout'])
        self.settings_fields['TracertMaxHops'] = QLineEdit()
        test_params_layout.addRow("Tracert 最大跳數:", self.settings_fields['TracertMaxHops'])
        test_params_group.setLayout(test_params_layout)
        main_layout.addWidget(test_params_group)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("儲存")
        save_button.clicked.connect(self._save_settings)
        button_layout.addWidget(save_button)

        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject) # reject closes the dialog with QDialog.Rejected
        button_layout.addWidget(cancel_button)

        main_layout.addLayout(button_layout)

    def _load_settings_to_ui(self):
        # Load Network Settings
        self.settings_fields['GatewayIP'].setText(self.config_manager.get_setting('NetworkSettings', 'GatewayIP'))
        self.settings_fields['PrimaryDNS'].setText(self.config_manager.get_setting('NetworkSettings', 'PrimaryDNS'))
        self.settings_fields['SecondaryDNS'].setText(self.config_manager.get_setting('NetworkSettings', 'SecondaryDNS'))
        self.settings_fields['InternalServerIP'].setText(self.config_manager.get_setting('NetworkSettings', 'InternalServerIP'))
        self.settings_fields['TestWebsite'].setText(self.config_manager.get_setting('NetworkSettings', 'TestWebsite'))

        # Load Test Parameters
        self.settings_fields['PingCount'].setText(self.config_manager.get_setting('TestParameters', 'PingCount'))
        self.settings_fields['PingTimeout'].setText(self.config_manager.get_setting('TestParameters', 'PingTimeout'))
        self.settings_fields['TracertMaxHops'].setText(self.config_manager.get_setting('TestParameters', 'TracertMaxHops'))

    def _save_settings(self):
        # Save Network Settings
        self.config_manager.set_setting('NetworkSettings', 'GatewayIP', self.settings_fields['GatewayIP'].text())
        self.config_manager.set_setting('NetworkSettings', 'PrimaryDNS', self.settings_fields['PrimaryDNS'].text())
        self.config_manager.set_setting('NetworkSettings', 'SecondaryDNS', self.settings_fields['SecondaryDNS'].text())
        self.config_manager.set_setting('NetworkSettings', 'InternalServerIP', self.settings_fields['InternalServerIP'].text())
        self.config_manager.set_setting('NetworkSettings', 'TestWebsite', self.settings_fields['TestWebsite'].text())

        # Save Test Parameters
        self.config_manager.set_setting('TestParameters', 'PingCount', self.settings_fields['PingCount'].text())
        self.config_manager.set_setting('TestParameters', 'PingTimeout', self.settings_fields['PingTimeout'].text())
        self.config_manager.set_setting('TestParameters', 'TracertMaxHops', self.settings_fields['TracertMaxHops'].text())

        self.config_manager.save_config()
        self.accept() # accept closes the dialog with QDialog.Accepted
