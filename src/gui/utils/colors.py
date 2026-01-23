"""Nick color utilities."""
import hashlib
from PyQt5.QtGui import QColor

def get_nick_colour(nick, bg_colour_hex="#ffffff"):
    hash_val = int(hashlib.md5(nick.encode()).hexdigest(), 16)
    hue = hash_val % 360
    is_dark_bg = QColor(bg_colour_hex).lightness() < 128
    lightness = 70 if is_dark_bg else 40
    return f"hsl({hue}, 70%, {lightness}%)"
