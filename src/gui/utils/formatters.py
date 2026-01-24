"""IRC message formatting."""
import html
import re

def irc_to_html(text):
    colours = {
        "0": "#ffffff", "1": "#000000", "2": "#00007f", "3": "#009300",
        "4": "#ff0000", "5": "#7f0000", "6": "#9c009c", "7": "#fc7f00",
        "8": "#ffff00", "9": "#00fc00", "10": "#009393", "11": "#00ffff",
        "12": "#0000fc", "13": "#ff00ff", "14": "#7f7f7f", "15": "#d2d2d2",
        "16": "#470000", "17": "#472100", "18": "#474700", "19": "#324700",
        "20": "#004700", "21": "#00472c", "22": "#004747", "23": "#002747",
        "24": "#000047", "25": "#2e0047", "26": "#470047", "27": "#47002a",
        "28": "#740000", "29": "#743a00", "30": "#747400", "31": "#517400",
        "32": "#007400", "33": "#007449", "34": "#007474", "35": "#004074",
        "36": "#000074", "37": "#4b0074", "38": "#740074", "39": "#740045",
        "40": "#b50000", "41": "#b56300", "42": "#b5b500", "43": "#7db500",
        "44": "#00b500", "45": "#00b571", "46": "#00b5b5", "47": "#0063b5",
        "48": "#0000b5", "49": "#7500b5", "50": "#b500b5", "51": "#b5006b",
        "52": "#ff0000", "53": "#ff8c00", "54": "#ffff00", "55": "#b2ff00",
        "56": "#00ff00", "57": "#00ffa0", "58": "#00ffff", "59": "#008cff",
        "60": "#0000ff", "61": "#a500ff", "62": "#ff00ff", "63": "#ff0098",
        "64": "#ff5959", "65": "#ffb459", "66": "#ffff71", "67": "#cfff60",
        "68": "#6fff6f", "69": "#65ffc9", "70": "#6dffff", "71": "#59b4ff",
        "72": "#5959ff", "73": "#c459ff", "74": "#ff66ff", "75": "#ff59bc",
        "76": "#ff9c9c", "77": "#ffd39c", "78": "#ffff9c", "79": "#e2ff9c",
        "80": "#9cff9c", "81": "#9cffdb", "82": "#9cffff", "83": "#9cd3ff",
        "84": "#9c9cff", "85": "#dc9cff", "86": "#ff9cff", "87": "#ff94d3",
        "88": "#000000", "89": "#131313", "90": "#282828", "91": "#3c3c3c",
        "92": "#545454", "93": "#6abc6a", "94": "#8a8a8a", "95": "#9f9f9f",
        "96": "#bababa", "97": "#d1d1d1", "98": "#e9e9e9", "99": "#ffffff"
    }
    
    # Pre-parse HexChat style escapes to IRC control codes for unified handling
    # %Cnn -> \x03nn, %B -> \x02, %I -> \x1D, %U -> \x1F, %O -> \x0F
    text = re.sub(r'%C(\d{1,2})', r'\x03\1', text)
    text = text.replace('%B', '\x02').replace('%I', '\x1D').replace('%U', '\x1F').replace('%O', '\x0F')

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
            # Handle 1 or 2 digits
            while i < len(text) and len(fg_code) < 2 and text[i].isdigit():
                fg_code += text[i]
                i += 1
            if i < len(text) and text[i] == ',':
                i += 1
                while i < len(text) and len(bg_code) < 2 and text[i].isdigit():
                    bg_code += text[i]
                    i += 1
            if fg_code:
                # Normalize code to string matching our dictionary keys
                code_key = str(int(fg_code))
                color_fg = colours.get(code_key, "#ffffff")
                style = f'color:{color_fg}'
                if bg_code:
                    bg_key = str(int(bg_code))
                    color_bg = colours.get(bg_key, "#000000")
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

def format_text_event(fmt, args):
    """Parses HexChat style $1, $2 and $t variables."""
    # $1 - $9
    for i, arg in enumerate(args, 1):
        fmt = fmt.replace(f'${i}', str(arg))
    # $t - timestamp (handled by main window generally, but if present here...)
    # In HexChat, $t is often just a placeholder that the UI fills.
    # We'll just strip it or replace with nothing if it gets here, 
    # as PyeChat adds timestamps at the line level.
    fmt = fmt.replace('$t', '')
    return fmt
