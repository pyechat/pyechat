from PyQt5.QtWidgets import QPlainTextEdit
from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import Qt

INPUT_MIN_HEIGHT = 30
INPUT_MAX_HEIGHT = 85
INPUT_PADDING = 12

NICK_PREFIXES = ('~', '&', '@', '%', '+')

class ChatInput(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.setObjectName("chat_input")
        self.setPlaceholderText("Message...")
        self.setFixedHeight(INPUT_MIN_HEIGHT)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.textChanged.connect(self.adjust_height)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Tab:
            self.do_tab_completion()
            return
        
        if hasattr(self, '_tab_state'):
            delattr(self, '_tab_state')
        
        # Input history navigation (up/down)
        if event.key() == Qt.Key_Up:
            prev = None
            try:
                prev = self.main_window.history_prev()
            except Exception:
                prev = None
            if prev is not None:
                self.setPlainText(prev)
                cursor = self.textCursor()
                cursor.movePosition(QTextCursor.End)
                self.setTextCursor(cursor)
            return
        if event.key() == Qt.Key_Down:
            nxt = None
            try:
                nxt = self.main_window.history_next()
            except Exception:
                nxt = None
            if nxt is not None:
                self.setPlainText(nxt)
                cursor = self.textCursor()
                cursor.movePosition(QTextCursor.End)
                self.setTextCursor(cursor)
            return
        
        if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            if event.modifiers() & Qt.ShiftModifier:
                super().keyPressEvent(event)
                return
            self.main_window.on_send()
            return

        super().keyPressEvent(event)

    def adjust_height(self):
        doc = self.document()
        doc.setTextWidth(self.viewport().width())
        h = doc.size().height() + INPUT_PADDING
        self.setFixedHeight(int(min(max(h, INPUT_MIN_HEIGHT), INPUT_MAX_HEIGHT)))
        
        if h > INPUT_MAX_HEIGHT:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        else:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def do_tab_completion(self):
        cursor = self.textCursor()
        pos = cursor.position()
        text = self.toPlainText()
        
        if pos == 0: return
        
        if hasattr(self, '_tab_state') and self._tab_state['text'] == text and self._tab_state['pos'] == pos:
            state = self._tab_state
            idx = (state['idx'] + 1) % len(state['candidates'])
            state['idx'] = idx
            
            cursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, state['len'])
            new_val = state['candidates'][idx]
            
            comp_suffix = self.main_window.settings.get("completion_suffix", ":")
            suffix = (comp_suffix + " ") if state['start'] == 0 else " "
            if not comp_suffix and state['start'] == 0: suffix = " "
            
            cursor.insertText(new_val + suffix)
            
            state['text'] = self.toPlainText()
            state['pos'] = cursor.position()
            state['len'] = len(new_val + suffix)
            self.setTextCursor(cursor)
            return

        start = pos
        while start > 0 and not text[start-1].isspace():
            start -= 1
        
        word = text[start:pos]
        if not word: return
        word_lower = word.lower()
        
        candidates = []
        seen = set()
        prefix_chars = ''.join(NICK_PREFIXES) + ' '
        
        mw = self.main_window
        if mw.current_nw and mw.current_target:
            buf = mw.buffers.get((mw.current_nw, mw.current_target))
            if buf:
                for n in buf.get("nicks", []):
                    raw = n.lstrip(prefix_chars)
                    raw_l = raw.lower()
                    if raw_l.startswith(word_lower) and raw_l not in seen:
                        candidates.append(raw)
                        seen.add(raw_l)
        
        if mw.current_nw:
            nw_it = mw.find_item(mw.current_nw, "")
            if nw_it:
                for i in range(nw_it.childCount()):
                    chan = nw_it.child(i).text(0)
                    chan_l = chan.lower()
                    if chan_l.startswith(word_lower) and chan_l not in seen:
                        candidates.append(chan)
                        seen.add(chan_l)
                        
        if not candidates: return
        candidates.sort(key=lambda x: x.lower())
        
        completed = candidates[0]
        comp_suffix = mw.settings.get("completion_suffix", ":")
        suffix = (comp_suffix + " ") if start == 0 else " "
        if not comp_suffix and start == 0: suffix = " "
        
        cursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, len(word))
        cursor.insertText(completed + suffix)
        
        self._tab_state = {
            'candidates': candidates,
            'idx': 0,
            'word': word,
            'start': start,
            'len': len(completed + suffix),
            'text': self.toPlainText(),
            'pos': cursor.position()
        }
        self.setTextCursor(cursor)
