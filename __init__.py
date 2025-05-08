from __future__ import annotations

from .config import *
from .card_ui import *


# def add_button_html(web_content: WebContent, context) -> None:
#     if not isinstance(context, ReviewerBottomBar):
#         return
#
#     web_content.head += """<style>#mybtn { margin-left:8px; padding:4px 8px; font-size:12px; }</style>"""
#
#     web_content.body += """<button id="mybtn" onclick="pycmd('my_bottom_button')">★ My Btn</button>"""
#
# def on_js_message(handled: bool, message: str, context):
#     if not message == "my_bottom_button":
#         return (False, None)
#     print(f"Current card id: {mw.reviewer.card.id}")
#     return (True, None)
#
# gui_hooks.webview_will_set_content.append(add_button_html)
# gui_hooks.webview_did_receive_js_message.append(on_js_message)
# mw.addonManager.setWebExports(__name__, r"web/.*")

init_settings()
add_to_gui()

