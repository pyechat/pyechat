"""IRC message formatting utilities."""
import html
import re

# Standard mIRC colour codes
IRC_COLOURS = {
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

URL_PATTERN = re.compile(r'(https?://[^\s<>"]+)')

def irc_to_html(text):
    # Pre-parse HexChat style escapes to IRC control codes for unified handling
    # %Cnn -> \x03nn, %B -> \x02, %I -> \x1D, %U -> \x1F, %O -> \x0F
    text = re.sub(r'%C(\d{1,2})', lambda m: '\x03' + m.group(1), text)
    text = text.replace('%B', '\x02').replace('%I', '\x1D').replace('%U', '\x1F').replace('%O', '\x0F')

    text = html.escape(text)
    result = []
    state = {'bold': False, 'italic': False, 'underline': False, 'fg': None, 'bg': None}
    
    i = 0
    n = len(text)
    
    while i < n:
        char = text[i]
        
        if char == '\x02':
            result.append('</b>' if state['bold'] else '<b>')
            state['bold'] = not state['bold']
            i += 1
            
        elif char == '\x1D':
            result.append('</i>' if state['italic'] else '<i>')
            state['italic'] = not state['italic']
            i += 1
            
        elif char == '\x1F':
            result.append('</u>' if state['underline'] else '<u>')
            state['underline'] = not state['underline']
            i += 1
            
        elif char == '\x03':
            if state['fg'] is not None:
                result.append('</span>')
                state['fg'] = state['bg'] = None
            
            i += 1
            fg_code = bg_code = ''
            
            # Parse Foreground
            if i < n and text[i].isdigit():
                fg_code += text[i]; i += 1
                if i < n and text[i].isdigit():
                    fg_code += text[i]; i += 1
            
            # Parse Background
            if i < n and text[i] == ',':
                i += 1
                if i < n and text[i].isdigit():
                    bg_code += text[i]; i += 1
                    if i < n and text[i].isdigit():
                        bg_code += text[i]; i += 1
            
            if fg_code:
                state['fg'] = IRC_COLOURS.get(str(int(fg_code)), "#ffffff")
                style = f'color:{state["fg"]}'
                
                if bg_code:
                    state['bg'] = IRC_COLOURS.get(str(int(bg_code)), "#000000")
                    style += f';background-color:{state["bg"]}'
                
                result.append(f'<span style="{style}">')
                
        elif char == '\x0F':
            if state['fg']: result.append('</span>')
            if state['underline']: result.append('</u>')
            if state['italic']: result.append('</i>')
            if state['bold']: result.append('</b>')
            
            state = {'bold': False, 'italic': False, 'underline': False, 'fg': None, 'bg': None}
            i += 1
            
        else:
            result.append(char)
            i += 1
    
    # Close any open tags
    if state['fg']: result.append('</span>')
    if state['underline']: result.append('</u>')
    if state['italic']: result.append('</i>')
    if state['bold']: result.append('</b>')
    
    html_text = ''.join(result)
    html_text = URL_PATTERN.sub(r'<a href="\1" style="color: #3399ff;">\1</a>', html_text)
    
    return f'<span style="white-space: pre-wrap;">{html_text}</span>'

def format_text_event(fmt, args):
    """Parses HexChat style $1, $2 and $t variables."""
    for i, arg in enumerate(args, 1):
        fmt = fmt.replace(f'${i}', str(arg))
    return fmt.replace('$t', '')
