# gui/styles.py

class AppTheme:
    # Main Colors
    BG_DARK = "#23272e"
    BG_DARKER = "#1e2227"
    BG_LIGHT = "#2c313a"
    
    # Accents
    ACCENT_PRIMARY = "#61afef"   # Blue
    ACCENT_SUCCESS = "#98c379"   # Green
    ACCENT_WARNING = "#e5c07b"   # Yellow
    ACCENT_DANGER = "#e06c75"    # Red
    ACCENT_PURPLE = "#c678dd"
    
    # Text
    TEXT_MAIN = "#dcdcdc"
    TEXT_DIM = "#5c6370"
    
    # Borders
    BORDER = "#3e4451"

    @staticmethod
    def get_stylesheet():
        return f"""
        QMainWindow {{
            background-color: {AppTheme.BG_DARK};
        }}
        QWidget {{
            color: {AppTheme.TEXT_MAIN};
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 14px;
        }}
        QTabWidget::pane {{
            border: 1px solid {AppTheme.BORDER};
            background-color: {AppTheme.BG_DARKER};
        }}
        QTabBar::tab {{
            background: {AppTheme.BG_LIGHT};
            color: {AppTheme.TEXT_DIM};
            padding: 8px 20px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            margin-right: 2px;
        }}
        QTabBar::tab:selected {{
            background: {AppTheme.BG_DARKER};
            color: {AppTheme.ACCENT_PRIMARY};
            font-weight: bold;
            border-bottom: 2px solid {AppTheme.ACCENT_PRIMARY};
        }}
        QLineEdit, QSpinBox, QComboBox {{
            background-color: {AppTheme.BG_LIGHT};
            border: 1px solid {AppTheme.BORDER};
            padding: 5px;
            border-radius: 4px;
            color: {AppTheme.TEXT_MAIN};
        }}
        QPushButton {{
            background-color: {AppTheme.BG_LIGHT};
            border: 1px solid {AppTheme.BORDER};
            padding: 8px;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: #3e4451;
            border-color: {AppTheme.ACCENT_PRIMARY};
        }}
        QListWidget {{
            background-color: {AppTheme.BG_DARKER};
            border: 1px solid {AppTheme.BORDER};
            outline: none;
        }}
        QListWidget::item {{
            padding: 8px;
            border-bottom: 1px solid {AppTheme.BG_LIGHT};
        }}
        QListWidget::item:selected {{
            background-color: {AppTheme.BG_LIGHT};
            color: {AppTheme.ACCENT_PRIMARY};
            border-left: 3px solid {AppTheme.ACCENT_PRIMARY};
        }}
        QStatusBar {{
            background-color: {AppTheme.BG_DARKER};
            color: {AppTheme.TEXT_DIM};
        }}
        QMenuBar {{
            background-color: {AppTheme.BG_DARK};
            border-bottom: 1px solid {AppTheme.BORDER};
        }}
        QMenuBar::item:selected {{
            background-color: {AppTheme.BG_LIGHT};
        }}
        QMenu {{
            background-color: {AppTheme.BG_LIGHT};
            border: 1px solid {AppTheme.BORDER};
        }}
        """