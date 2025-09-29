#!/usr/bin/env python3
# desktop_chat_qt.py
# ChatGPT-like native desktop app for your AutoGen-based ai_agent (PySide6 / Qt).

import os
import sys
import html
import re
import traceback
from typing import List, Dict, Tuple

from dotenv import load_dotenv

# Qt
from PySide6.QtCore import Qt, QThread, Signal, Slot, QUrl, QTimer
from PySide6.QtGui import QFont, QTextCursor, QIcon, QPixmap, QGuiApplication
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextBrowser, QPlainTextEdit, QPushButton, QLabel, QFrame, QSizePolicy
)

# ---- HiDPI crisp icons/pixmaps (set BEFORE QApplication is constructed) ----
QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

# --- Your project imports (UNCHANGED) ---
from ai_agents import create_geom_assistant
from ai_runner import run_geom_command
from ai_validator import make_hooked_reply

APP_TITLE = "GEOM AI Assistant"


# ---------- helpers ----------
def escape(s: str) -> str:
    return html.escape(s, quote=True).replace("\n", "<br>")


def render_msg(role: str, content: str) -> str:
    """
    Message bubbles via a two-cell table for rock-solid alignment in QTextBrowser:
    - Assistant: LEFT (pale blue)
    - User: RIGHT (pale blue)
    """
    is_user = (role == "user")
    bubble_bg = "#E7F0FF"                  # same hue as the banner
    border = "#D8E3F8"
    outer_margin = "26px 0"                # more vertical space

    bubble_html = f"""
<span style="
  display:inline-block;
  text-align:left;
  background-color:{bubble_bg};
  border: 1px solid {border};
  border-radius:22px;          /* rounder corners */
  padding:16px 20px;           /* extra spacing to the text */
  max-width: 96%;              /* wider bubble */
  line-height:1.7;
  font-size:17px;
  color:#0B0F19;
  white-space:normal;
  word-wrap:break-word;
">{escape(content)}</span>
"""

    # Assistant on LEFT, User on RIGHT
    left_cell  = bubble_html if not is_user else "&nbsp;"
    right_cell = bubble_html if is_user else "&nbsp;"

    return f"""
<table width="100%" cellspacing="0" cellpadding="0" style="margin:{outer_margin};">
  <tr>
    <td align="left"  style="width:50%; vertical-align:top;">{left_cell}</td>
    <td align="right" style="width:50%; vertical-align:top;">{right_cell}</td>
  </tr>
</table>
"""


def make_acknowledgement(user_text: str) -> str:
    t = user_text.lower()
    mapping = [
        (["sphere", "sfera"], "Sure — here is your sphere."),
        (["rod", "nanorod", "cylinder"], "I have created the rod for you."),
        (["cube", "box"], "Got it — here's your cube."),
        (["graphene", "sheet", "slab"], "Understood — the sheet is ready."),
        (["surface", "facet"], "Done — I prepared the surface."),
        (["lattice", "cell"], "Okay — I set up the lattice."),
        (["cone"], "Sure — here is your cone."),
        (["tube", "nanotube"], "All set — the tube is generated."),
        (["radius"], "Sure — here is your result."),
    ]
    for keys, sentence in mapping:
        if any(k in t for k in keys):
            return sentence + "\n\nExecuted geom command:"
    return "Done — here is the result.\n\nExecuted geom command:"


# Detect fenced code blocks OR single-line commands
_CODE_FENCE_GENERIC = re.compile(r"```(?:\s*\w+)?\s*\n(?P<code>[\s\S]*?)```", re.IGNORECASE)
_GEOM_LINE = re.compile(r"^\s*(?:\$+\s*)?(geom\s+[^\n\r]+)", re.IGNORECASE | re.MULTILINE)

def extract_geom_command(text: str) -> Tuple[str, str | None]:
    """
    Find command-like content in assistant text; remove from visible message.
    Priority:
      1) First fenced code block
      2) First 'geom ...' line (optional leading $)
    Returns (cleaned_text, command_or_None).
    """
    m = _CODE_FENCE_GENERIC.search(text)
    if m:
        cmd = m.group("code").strip()
        cleaned = (text[:m.start()] + text[m.end():]).strip()
        return cleaned, cmd
    m2 = _GEOM_LINE.search(text)
    if m2:
        cmd = m2.group(1).strip()
        cleaned = _GEOM_LINE.sub("", text, count=1).strip()
        return cleaned, cmd
    return text, None


def strip_terminate_tokens(text: str) -> str:
    return re.sub(r"\bTERMINATE\b", "", text, flags=re.IGNORECASE).strip()


# ---------- background worker that queries your agent ----------
class AgentWorker(QThread):
    finished_with_reply = Signal(dict)  # {"role":"assistant","content": ...}

    def __init__(self, assistant, messages: List[Dict], parent=None):
        super().__init__(parent)
        self.assistant = assistant
        self.messages = messages

    def run(self):
        try:
            reply = self.assistant.generate_reply(self.messages)
            if isinstance(reply, dict) and "content" in reply:
                content = reply["content"]
            else:
                content = str(reply)
            self.finished_with_reply.emit({"role": "assistant", "content": content})
        except Exception as e:
            err = f"{type(e).__name__}: {e}\n\n" + traceback.format_exc()
            self.finished_with_reply.emit({"role": "assistant", "content": f"⚠️ {err}"})


# ---------- main window ----------
class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1000, 800)

        load_dotenv()  # picks up OPENAI_API_KEY / OPENAI_BASE_URL if present

        # Build your AutoGen assistant and hook command execution (UNCHANGED)
        self.assistant = create_geom_assistant()
        original_reply = self.assistant.generate_reply
        self.assistant.generate_reply = make_hooked_reply(run_geom_command, original_reply)

        # Chat state
        self.messages: List[Dict[str, str]] = []
        self.system_prompt = (
            "You are a helpful assistant for GEOM. "
            "Propose safe shell commands only when appropriate; when you do, execute them."
        )
        if self.system_prompt:
            self.messages.append({"role": "system", "content": self.system_prompt})

        # Global font
        app_font = QFont()
        app_font.setFamily("system-ui")
        app_font.setPointSize(16)
        self.setFont(app_font)

        # Root with pale-blue background
        root = QWidget(self)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(16, 14, 16, 14)
        root_layout.setSpacing(14)
        self.setCentralWidget(root)
        root.setStyleSheet("QWidget { background: #EDF5FF; }")

        # ---- Header (logo + title + one-line typewriter) ----
        header = QFrame()
        header.setStyleSheet("QFrame { background: transparent; }")
        hbox = QVBoxLayout(header)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(6)

        # Logo (QLabel + DPR-aware scaling to avoid blur/clipping)
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.logo_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../docs/_static/geom-logo-desktop.png"))
        self._set_logo_pixmap(self.logo_label, logo_path, target_height_css=400)
        hbox.addWidget(self.logo_label, 0, Qt.AlignHCenter)

        # Title (closer to logo)
        self.title_label = QLabel("Welcome to GEOM AI assistant\n")
        self.title_label.setAlignment(Qt.AlignHCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #0B0F19;
                font-size: 20px;
                font-weight: 700;
                background: transparent;
            }
        """)
        hbox.addWidget(self.title_label, 0, Qt.AlignHCenter)

        # One-line typewriter (no “Try:”, slower, stops on last)
        self.type_label = QLabel("")
        mono = QFont("monospace")
        mono.setStyleHint(QFont.Monospace)
        mono.setPointSize(14)
        self.type_label.setFont(mono)
        self.type_label.setAlignment(Qt.AlignHCenter)
        self.type_label.setStyleSheet("""
            QLabel {
                background: #E7F0FF;
                border: 1px solid #D8E3F8;
                border-radius: 10px;
                padding: 8px 12px;
                color: #0B0F19;
            }
        """)
        hbox.addWidget(self.type_label, 0, Qt.AlignHCenter)

        # Typewriter settings (slow + stop)
        self._samples = [
            '"Create a silver sphere with 20 angstroms radius"',
            '"Create a gold nanorod"',
        ]
        self._sample_index = 0
        self._type_pos = 0
        self._type_timer = QTimer(self)
        self._type_timer.timeout.connect(self._typewriter_tick)
        self._type_timer.start(120)  # slower typing: 120ms per character
        self._typewriter_running = True

        # ---- Chat container (pale blue) ----
        self.chat_frame = QFrame()
        self.chat_frame.setObjectName("chatFrame")
        self.chat_frame.setStyleSheet("""
            #chatFrame {
                background: #EDF5FF;
                border: none;
                border-radius: 16px;
            }
        """)
        chat_layout = QVBoxLayout(self.chat_frame)
        chat_layout.setContentsMargins(12, 12, 12, 12)
        chat_layout.setSpacing(0)

        self.chat_view = QTextBrowser()
        # IMPORTANT for toggle links
        self.chat_view.setOpenExternalLinks(False)
        self.chat_view.setOpenLinks(False)
        self.chat_view.anchorClicked.connect(self.on_anchor_clicked)
        self.chat_view.setStyleSheet("""
            QTextBrowser {
                border: none;
                background: #EDF5FF;  /* pale blue */
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Ubuntu, "Helvetica Neue", Arial, "Noto Sans", "Apple Color Emoji", "Segoe UI Emoji";
                font-size: 17px;
                color: #0B0F19;
            }
            a.toggle {
                color: #6B7280;                 /* pale gray text */
                text-decoration: none;
                border: 1px solid #E5E7EB;
                background: #F9FAFB;
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 13px;
            }
            a.toggle:hover { background: #F3F4F6; }
            /* Command box (has its own scrollbar) */
            div.cmdwrap {
                max-height: 180px;
                overflow: auto;
                background: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 10px;
            }
            pre.codebox {
                margin: 0;
                font-size: 13px;
                white-space: pre-wrap;
            }
        """)
        # Hide main scrollbars (scroll via wheel/trackpad still works)
        self.chat_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        chat_layout.addWidget(self.chat_view)

        # ---- Input container (white with subtle border) ----
        self.input_frame = QFrame()
        self.input_frame.setObjectName("inputFrame")
        self.input_frame.setStyleSheet("""
            #inputFrame {
                background: #FFFFFF;             /* stays white */
                border: 1px solid #E5E7EB;       /* subtle grey border */
                border-radius: 14px;
            }
        """)
        input_layout = QHBoxLayout(self.input_frame)
        input_layout.setContentsMargins(12, 10, 12, 10)
        input_layout.setSpacing(8)

        self.input_box = QPlainTextEdit()
        self.input_box.setPlaceholderText("Type your request…")
        self.input_box.setStyleSheet("""
            QPlainTextEdit {
                border: none;
                background: transparent;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Ubuntu, "Helvetica Neue", Arial, "Noto Sans";
                font-size: 15px;
                color:#0B0F19;
            }
        """)
        self.input_box.setFixedHeight(78)
        self.input_box.installEventFilter(self)

        self.send_btn = QPushButton("Send")
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background: #10A37F;
                color: white;
                border: none;
                border-radius: 12px;
                padding: 12px 18px;
                font-weight: 600;
                font-size: 15px;
            }
            QPushButton:hover { background: #0E906F; }
            QPushButton:pressed { background: #0C7F61; }
        """)
        self.send_btn.clicked.connect(self.send_message)

        input_layout.addWidget(self.input_box, 1)
        input_layout.addWidget(self.send_btn, 0, Qt.AlignBottom)

        # ---- Layout stacking ----
        root_layout.addWidget(header, 0)
        root_layout.addSpacing(10)                 # space between header and chat
        root_layout.addWidget(self.chat_frame, 1)
        root_layout.addSpacing(12)                 # extra gap before input
        root_layout.addWidget(self.input_frame, 0)

        # App & window icon (macOS Dock needs .app bundle to fully change)
        if os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))
            QApplication.instance().setWindowIcon(QIcon(logo_path))

        # Track last user text + toggle state
        self._last_user_text = ""
        self._toggle_counter = 0
        self._toggles: Dict[str, Dict[str, str]] = {}  # id -> {"shown": "0/1", "content": html}

    # ----- DPR-aware logo rendering (crisp on Retina/HiDPI) -----
    def _set_logo_pixmap(self, label: QLabel, path: str, target_height_css: int = 56):
        if not os.path.exists(path):
            return
        pm = QPixmap(path)
        if pm.isNull():
            return
        screen = self.screen() or QApplication.primaryScreen()
        dpr = screen.devicePixelRatio() if screen else 1.0
        pm_hd = pm.scaledToHeight(int(target_height_css * dpr), Qt.SmoothTransformation)
        pm_hd.setDevicePixelRatio(dpr)
        label.setPixmap(pm_hd)
        label.setFixedHeight(target_height_css + 6)  # give a bit more room

    # ----- Typewriter animation (slow + stops on last) -----
    def _typewriter_tick(self):
        if not self._typewriter_running:
            return

        full = self._samples[self._sample_index]
        self._type_pos += 1
        if self._type_pos >= len(full):
            self._type_pos = len(full)
            self.type_label.setText(full[:self._type_pos])
            # Move to next sample OR stop if last
            if self._sample_index + 1 < len(self._samples):
                self._typewriter_running = False
                QTimer.singleShot(900, self._advance_sample)
            else:
                self._type_timer.stop()      # stop permanently
                self._typewriter_running = False
            return

        self.type_label.setText(full[:self._type_pos])

    def _advance_sample(self):
        self._sample_index += 1
        if self._sample_index >= len(self._samples):
            return
        self._type_pos = 0
        self._typewriter_running = True

    # ----- Toggle link handling for "show GEOM command" -----
    @Slot(QUrl)
    def on_anchor_clicked(self, url: QUrl):
        href = url.toString()
        if href.startswith("toggle:"):
            tid = href.split(":", 1)[1]
            entry = self._toggles.get(tid)
            if not entry:
                return
            shown = entry.get("shown") == "1"
            entry["shown"] = "0" if shown else "1"
            link_txt = "hide GEOM command" if entry["shown"] == "1" else "show GEOM command"
            link_html = f'<a href="toggle:{tid}" class="toggle">{link_txt}</a>'
            # Re-append link (right-aligned), then conditionally the command box
            self.chat_view.append(f'<div style="width:100%; text-align:right; margin-top:8px;">{link_html}</div>')
            if entry["shown"] == "1":
                self.chat_view.append(entry["content"])
            self.chat_view.moveCursor(QTextCursor.End)
            self.chat_view.ensureCursorVisible()

    # ----- UI behavior -----
    def eventFilter(self, obj, event):
        if obj is self.input_box and event.type() == event.Type.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if event.modifiers() & Qt.ShiftModifier:
                    return False  # newline
                else:
                    self.send_message()
                    return True
        return super().eventFilter(obj, event)

    def append_chat(self, message: Dict[str, str]):
        role = message.get("role", "assistant")
        content = message.get("content", "")
        html_chunk = render_msg(role, content)
        self.chat_view.append(html_chunk)
        self.chat_view.moveCursor(QTextCursor.End)
        self.chat_view.ensureCursorVisible()
        self.messages.append({"role": role, "content": content})

    @Slot()
    def send_message(self):
        user_text = self.input_box.toPlainText().strip()
        if not user_text:
            return
        # Hide typewriter after first user message
        if self._last_user_text == "":
            self.type_label.setVisible(False)

        self.input_box.clear()
        self._last_user_text = user_text
        self.append_chat({"role": "user", "content": user_text})

        ctx = list(self.messages)  # include system + history + latest user
        self.worker = AgentWorker(self.assistant, ctx, self)
        self.worker.finished_with_reply.connect(self.on_agent_reply)
        self.worker.start()

    @Slot(dict)
    def on_agent_reply(self, reply_message: Dict[str, str]):
        # Remove "TERMINATE"
        content = strip_terminate_tokens(reply_message.get("content", ""))

        # Friendly acknowledgement
        if self._last_user_text:
            ack = make_acknowledgement(self._last_user_text)
            if ack.lower() not in content.lower():
                content = f"{ack}\n\n{content}"

        # Extract & hide command if present
        cleaned, cmd = extract_geom_command(content)
        visible_text = cleaned.strip() if cleaned.strip() else content

        # Assistant bubble (LEFT)
        self.append_chat({"role": "assistant", "content": visible_text})

        # If a command exists, add toggle with a compact scrollable box
        if cmd:
            self._toggle_counter += 1
            tid = f"g{self._toggle_counter}"
            link_html = f'<a href="toggle:{tid}" class="toggle">show GEOM command</a>'
            cmd_html = f'<div class="cmdwrap"><pre class="codebox">{escape(cmd)}</pre></div>'
            self._toggles[tid] = {"shown": "0", "content": cmd_html}
            self.chat_view.append(f'<div style="width:100%; text-align:right; margin-top:-6px;">{link_html}</div>')
            self.chat_view.moveCursor(QTextCursor.End)
            self.chat_view.ensureCursorVisible()


def main():
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
    app = QApplication(sys.argv)

    # App-wide icon (macOS Dock replacement still requires bundling .app)
    logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../docs/_static/geom-logo-desktop.png"))
    if os.path.exists(logo_path):
        app.setWindowIcon(QIcon(logo_path))

    win = ChatWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

