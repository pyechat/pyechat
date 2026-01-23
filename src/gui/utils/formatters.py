"""IRC message formatting."""
import html
import re

def irc_to_html(text):
    colours = {
        "0": "#ffffff", "1": "#000000", "2": "#000080", "3": "#008000",
        "4": "#ff0000", "5": "#800000", "6": "#800080", "7": "#ff8000",
        "8": "#ffff00", "9": "#00ff00", "10": "#008080", "11": "#00ffff",
        "12": "#0000ff", "13": "#ff00ff", "14": "#808080", "15": "#c0c0c0"
    }
    
    text = html.escape(text)
    result = []
    bold = italic = underline = False
    color_fg = color_bg = None
    
    i = 0
    while i < len(text):
        char = text[i]
        if char == '\x02':
            result.append('</b>' if bold else '<b>')
            bold = not bold
            i += 1
        elif char == '\x1D':
            result.append('</i>' if italic else '<i>')
            italic = not italic
            i += 1
        elif char == '\x1F':
            result.append('</u>' if underline else '<u>')
            underline = not underline
            i += 1
        elif char == '\x03':
            if color_fg is not None:
                result.append('</span>')
                color_fg = color_bg = None
            i += 1
            fg_code = bg_code = ''
            while i < len(text) and len(fg_code) < 2 and text[i].isdigit():
                fg_code += text[i]
                i += 1
            if i < len(text) and text[i] == ',':
                i += 1
                while i < len(text) and len(bg_code) < 2 and text[i].isdigit():
                    bg_code += text[i]
                    i += 1
            if fg_code:
                color_fg = colours.get(fg_code, "#ffffff")
                style = f'color:{color_fg}'
                if bg_code:
                    color_bg = colours.get(bg_code, "#000000")
                    style += f';background-color:{color_bg}'
                result.append(f'<span style="{style}">')
        elif char == '\x0F':
            if color_fg is not None: result.append('</span>')
            if underline: result.append('</u>')
            if italic: result.append('</i>')
            if bold: result.append('</b>')
            color_fg = color_bg = None
            bold = italic = underline = False
            i += 1
        else:
            result.append(char)
            i += 1
    
    if color_fg is not None: result.append('</span>')
    if underline: result.append('</u>')
    if italic: result.append('</i>')
    if bold: result.append('</b>')
    
    html_text = ''.join(result)
    url_pattern = r'(https?://[^\s<>"]+)'
    html_text = re.sub(url_pattern, r'<a href="\1" style="color: #3399ff;">\1</a>', html_text)
    return f'<span style="white-space: pre-wrap;">{html_text}</span>'
