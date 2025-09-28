#!/usr/bin/env python3
# desktop_chat_qt.py
# ChatGPT-like native desktop app for your AutoGen-based ai_agent (PySide6 / Qt).

import os
import sys
import html
import traceback
from typing import List, Dict

from dotenv import load_dotenv

# Qt
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QAction, QFont, QTextCursor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextBrowser, QPlainTextEdit, QPushButton, QLabel, QFrame,
    QFileDialog, QMessageBox
)

# --- Your project imports ---
from ai_agents import create_geom_assistant
from ai_runner import run_geom_command
from ai_validator import make_hooked_reply

APP_TITLE = "GEOM AI Assistant"

# ---------- helpers ----------
def escape(s: str) -> str:
    # Keep basic markdown code fences readable; we’ll rely on QTextBrowser for monospace rendering
    return html.escape(s, quote=True).replace("\n", "<br>")

def render_msg(role: str, content: str) -> str:
    # Qt's HTML/CSS support is limited: avoid flexbox, rely on text-align.
    is_user = (role == "user")
    align = "right" if is_user else "left"
    bg = "#E8F0FF" if is_user else "#F7F7F8"

    # Note: Qt accepts background-color, padding, border; border-radius support varies by platform/theme.
    # We still include it because it often works; worst-case you'll just get square corners.
    return f"""
<div style="text-align:{align}; margin:8px 0;">
  <span style="
    display:inline-block;
    text-align:left;
    background-color:{bg};
    border: 1px solid #E5E7EB;
    border-radius:12px;
    padding:10px 12px;
    max-width: 90%;
    line-height:1.5;
    font-size:16px;
    color:#0B0F19;
    white-space:normal;
    word-wrap:break-word;
  ">{escape(content)}</span>
</div>
"""


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
        self.resize(1000, 760)

        load_dotenv()  # picks up OPENAI_API_KEY / OPENAI_BASE_URL if you use a .env

        # Build your AutoGen assistant and hook command execution
        self.assistant = create_geom_assistant()
        original_reply = self.assistant.generate_reply
        self.assistant.generate_reply = make_hooked_reply(run_geom_command, original_reply)

        # Chat state (OpenAI-style role/content)
        self.messages: List[Dict[str, str]] = []
        self.system_prompt = (
            "You are a helpful assistant for GEOM. "
            "Propose safe shell commands only when appropriate; when you do, execute them."
        )
        if self.system_prompt:
            self.messages.append({"role": "system", "content": self.system_prompt})

        # Global font (ChatGPT-ish)
        app_font = QFont()
        app_font.setFamily("system-ui")  # Qt will fall back sensibly on each OS
        app_font.setPointSize(12)        # base font; content areas override to 15–16px via CSS
        self.setFont(app_font)

        # Root container
        root = QWidget(self)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(16, 14, 16, 14)
        root_layout.setSpacing(12)
        self.setCentralWidget(root)

        # --- Conversation container (rounded frame) ---
        self.chat_frame = QFrame()
        self.chat_frame.setObjectName("chatFrame")
        self.chat_frame.setStyleSheet("""
            #chatFrame {
                background: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
            }
        """)
        chat_layout = QVBoxLayout(self.chat_frame)
        chat_layout.setContentsMargins(16, 16, 16, 16)
        chat_layout.setSpacing(0)

        self.chat_view = QTextBrowser()
        self.chat_view.setOpenExternalLinks(True)
        self.chat_view.setStyleSheet("""
            QTextBrowser {
                border: none;
                background: transparent;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Ubuntu, "Helvetica Neue", Arial, "Noto Sans", "Apple Color Emoji", "Segoe UI Emoji";
                font-size: 17px;  /* 16 -> 17 for readability */
                color: #0B0F19;
            }
        """)
        chat_layout.addWidget(self.chat_view)

        # --- Input container (rounded frame) ---
        self.input_frame = QFrame()
        self.input_frame.setObjectName("inputFrame")
        self.input_frame.setStyleSheet("""
            #inputFrame {
                background: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 14px;
            }
        """)
        input_layout = QHBoxLayout(self.input_frame)
        input_layout.setContentsMargins(12, 10, 12, 10)
        input_layout.setSpacing(8)

        self.input_box = QPlainTextEdit()
        self.input_box.setPlaceholderText("Type your request…  (Enter to send, Shift+Enter for newline)")
        self.input_box.setStyleSheet("""
            QPlainTextEdit {
                border: none;
                background: transparent;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Ubuntu, "Helvetica Neue", Arial, "Noto Sans";
                font-size: 15px;
                color: #0B0F19;
            }
        """)
        # nicer initial height
        self.input_box.setFixedHeight(72)
        self.input_box.installEventFilter(self)

        self.send_btn = QPushButton("Send")
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background: #10A37F;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 16px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #0E906F;
            }
            QPushButton:pressed {
                background: #0C7F61;
            }
        """)
        self.send_btn.clicked.connect(self.send_message)

        input_layout.addWidget(self.input_box, 1)
        input_layout.addWidget(self.send_btn, 0, Qt.AlignBottom)

        # Add to root: conversation (big) then input (small)
        root_layout.addWidget(self.chat_frame, 1)
        root_layout.addWidget(self.input_frame, 0)

        # Menu (Save / Load chat)
        bar = self.menuBar()
        file_menu = bar.addMenu("&File")
        save_action = QAction("Save Chat…", self)
        load_action = QAction("Load Chat…", self)
        file_menu.addAction(save_action)
        file_menu.addAction(load_action)
        save_action.triggered.connect(self.save_chat)
        load_action.triggered.connect(self.load_chat)

        # Welcome message
        self.append_chat({"role": "assistant", "content": "Hi! I’m ready. Try: “create a silver sphere of radius 10”. 👋"})

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
        # append() adds a new paragraph; this fixes the “same line” effect
        self.chat_view.append(html_chunk)
        self.chat_view.moveCursor(QTextCursor.End)
        self.chat_view.ensureCursorVisible()
        self.messages.append({"role": role, "content": content})

    @Slot()
    def send_message(self):
        user_text = self.input_box.toPlainText().strip()
        if not user_text:
            return
        self.input_box.clear()
        self.append_chat({"role": "user", "content": user_text})

        ctx = list(self.messages)  # include system + history + latest user
        self.worker = AgentWorker(self.assistant, ctx, self)
        self.worker.finished_with_reply.connect(self.on_agent_reply)
        self.worker.start()

    @Slot(dict)
    def on_agent_reply(self, reply_message: Dict[str, str]):
        self.append_chat(reply_message)

    # ----- Save / Load -----
    def save_chat(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Chat", "chat.json", "JSON (*.json)")
        if not path:
            return
        import json
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.messages, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save chat:\n{e}")

    def load_chat(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Chat", "", "JSON (*.json)")
        if not path:
            return
        import json
        try:
            with open(path, "r", encoding="utf-8") as f:
                msgs = json.load(f)
            # Reset
            self.messages = []
            self.chat_view.clear()
            # Rebuild UI; system messages are kept in state but not rendered
            for m in msgs:
                if m.get("role") == "system":
                    self.messages.append(m)
                else:
                    self.append_chat(m)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load chat:\n{e}")

def main():
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
    app = QApplication(sys.argv)
    win = ChatWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

