#!/usr/bin/env python3
# desktop_chat_qt.py
# Native ChatGPT-like desktop app (Qt) for your AutoGen-based ai_agent.

import os
import sys
import html
import traceback
from typing import List, Dict

from dotenv import load_dotenv

# Qt
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QAction, QIcon, QTextCursor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextBrowser, QPlainTextEdit, QPushButton, QLabel, QSplitter, QFileDialog,
    QMessageBox
)

# Your project imports
from ai_agents import create_geom_assistant
from ai_runner import run_geom_command
from ai_validator import make_hooked_reply

# ------------- Utilities -------------
def escape(s: str) -> str:
    return html.escape(s, quote=True).replace("\n", "<br>")

def role_color(role: str) -> str:
    return {"user": "#1f6feb", "assistant": "#16a34a", "system": "#6b7280"}.get(role, "#374151")

def render_msg(role: str, content: str) -> str:
    # minimal HTML message bubble
    color = role_color(role)
    who = role.capitalize()
    return f"""
    <div style="margin:8px 0; padding:10px; border-radius:12px; background:#f8fafc;">
      <div style="font-weight:600; color:{color}; margin-bottom:6px;">{who}</div>
      <div style="white-space:wrap; line-height:1.45; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu;">
        {escape(content)}
      </div>
    </div>
    """

# ------------- Worker thread that calls your assistant -------------
class AgentWorker(QThread):
    finished_with_reply = Signal(dict, str)  # reply_message (role/content), tool_output

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
            # tool output captured by your hook, if set that way
            tool_output = getattr(self.assistant, "last_tool_output", "")
            self.finished_with_reply.emit({"role": "assistant", "content": content}, tool_output)
        except Exception as e:
            err = f"{type(e).__name__}: {e}\n\n" + traceback.format_exc()
            self.finished_with_reply.emit({"role": "assistant", "content": f"⚠️ {err}"}, "")

# ------------- Main Window -------------
class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GEOM AI Assistant (Desktop)")
        self.resize(1100, 720)

        load_dotenv()  # load OPENAI_API_KEY, OPENAI_BASE_URL, etc.

        # Build assistant and hook command execution the same way as console
        self.assistant = create_geom_assistant()
        original_reply = self.assistant.generate_reply
        self.assistant.generate_reply = make_hooked_reply(run_geom_command, original_reply)

        # State: OpenAI-style messages
        self.messages: List[Dict[str, str]] = []
        self.system_prompt = "You are a helpful assistant for GEOM. Propose safe shell commands only when appropriate."

        # UI
        central = QWidget(self)
        root = QVBoxLayout(central)
        self.setCentralWidget(central)

        # Splitter: chat (left) and tool output (right)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: conversation
        left = QWidget()
        lv = QVBoxLayout(left)
        self.chat_view = QTextBrowser()
        self.chat_view.setOpenExternalLinks(True)
        self.chat_view.setStyleSheet("QTextBrowser { background: #ffffff; padding: 10px; }")
        lv.addWidget(self.chat_view)
        splitter.addWidget(left)

        # Right: tool output
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.addWidget(QLabel("Last Tool Output"))
        self.tool_out = QPlainTextEdit()
        self.tool_out.setReadOnly(True)
        self.tool_out.setStyleSheet("QPlainTextEdit { background: #0b1020; color: #e5e7eb; font-family: Menlo, Consolas, monospace; }")
        rv.addWidget(self.tool_out)
        splitter.addWidget(right)
        splitter.setSizes([700, 400])

        root.addWidget(splitter)

        # Input row
        input_row = QHBoxLayout()
        self.input_box = QPlainTextEdit()
        self.input_box.setPlaceholderText("Type your request… (Shift+Enter for newline, Enter to send)")
        self.input_box.installEventFilter(self)
        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self.send_message)

        input_row.addWidget(self.input_box, 1)
        input_row.addWidget(send_btn, 0)
        root.addLayout(input_row)

        # Menus: Save/Load chat
        bar = self.menuBar()
        file_menu = bar.addMenu("&File")
        save_action = QAction("Save Chat…", self)
        load_action = QAction("Load Chat…", self)
        file_menu.addAction(save_action)
        file_menu.addAction(load_action)
        save_action.triggered.connect(self.save_chat)
        load_action.triggered.connect(self.load_chat)

        # Seed with a system message (not rendered, but used in context)
        if self.system_prompt:
            self.messages.append({"role": "system", "content": self.system_prompt})

        # Welcome message
        self.append_chat({"role": "assistant", "content": "Hi! I’m ready. Try: `create a silver sphere of radius 10`."})

    # Intercept Enter vs Shift+Enter in the input
    def eventFilter(self, obj, event):
        if obj is self.input_box and event.type() == event.Type.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if event.modifiers() & Qt.ShiftModifier:
                    return False  # allow newline
                else:
                    self.send_message()
                    return True
        return super().eventFilter(obj, event)

    def append_chat(self, message: Dict[str, str]):
        # Render to chat_view
        role = message.get("role", "assistant")
        content = message.get("content", "")
        html_chunk = render_msg(role, content)
        self.chat_view.moveCursor(QTextCursor.End)
        self.chat_view.insertHtml(html_chunk)
        self.chat_view.moveCursor(QTextCursor.End)
        self.chat_view.ensureCursorVisible()

        # Keep in memory (do not duplicate assistant welcome if already added)
        if not (self.messages and self.messages[-1] is message):
            self.messages.append({"role": role, "content": content})

    @Slot()
    def send_message(self):
        user_text = self.input_box.toPlainText().strip()
        if not user_text:
            return
        self.input_box.clear()

        user_msg = {"role": "user", "content": user_text}
        self.append_chat(user_msg)

        # Launch worker thread to avoid blocking UI
        # Build context: include system prompt (already in self.messages[0] if set)
        # and current chat including the latest user message (now appended).
        ctx = list(self.messages)

        self.worker = AgentWorker(self.assistant, ctx, self)
        self.worker.finished_with_reply.connect(self.on_agent_reply)
        self.worker.start()

    @Slot(dict, str)
    def on_agent_reply(self, reply_message: Dict[str, str], tool_output: str):
        self.append_chat(reply_message)
        if tool_output:
            self.tool_out.setPlainText(tool_output)
        else:
            # Don't clear useful logs accidentally; append a divider
            current = self.tool_out.toPlainText().strip()
            if current:
                self.tool_out.appendPlainText("\n---\n(no new tool output)")

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
            # reset UI
            self.messages = []
            self.chat_view.clear()
            self.tool_out.clear()
            for m in msgs:
                if m.get("role") == "system":
                    # keep as context but don't render
                    self.messages.append(m)
                else:
                    self.append_chat(m)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load chat:\n{e}")

def main():
    # macOS: high-DPI / menu fixes
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
    app = QApplication(sys.argv)
    win = ChatWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

