# UI package
"""PyQt6 User Interface components."""

__all__ = [
    'MainWindow',
]

def get_main_window():
    """Lazy import of MainWindow."""
    from ui.main_window import MainWindow
    return MainWindow
