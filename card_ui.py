import asyncio, json

from aqt.webview import WebContent
from aqt.reviewer import ReviewerBottomBar
from aqt.operations import QueryOp
from aqt.utils import showInfo

from aqt import gui_hooks, mw

def is_lang_deck() -> bool:
    cfg = mw.addonManager.getConfig(__name__)
    return (str(mw.reviewer.card.did) in cfg["per_deck"])

async def fetch_sentence(word: str, difficulty: str, language: str) -> str:
    """
    *** stub *** – replace with your LLM call.
    Must return plain text, no HTML.
    """
    await asyncio.sleep(0.1)
    return f"This is an example sentence using {word}."

# ---------- add to UI ----------
def add_button_html(web_content: WebContent, context) -> None:
    if not isinstance(context, ReviewerBottomBar) or not is_lang_deck():
        return
    web_content.head += """<style>#mybtn { margin-left:8px; padding:4px 8px; font-size:12px; }</style>"""
    web_content.body += """
        <button id="mybtn" onclick="pycmd('get_sentence_for_card')">get example sentence</button>
        <div id="exampleSentence"></div>
    """

def _run_in_worker(_, word, diff, lang):
    """Runs in worker thread – fetch and *return* sentence text."""
    print(word)
    print(diff)
    print(lang)
    return asyncio.run(fetch_sentence(word, diff, lang))

def _on_success(sent: str) -> None:
    """Runs on Qt thread – safe to touch the webview."""
    print(sent)
    js = (
        "const d=document.getElementById('exampleSentence');"
        f"if(d){{d.textContent={json.dumps(sent)};}}"
    )
    mw.reviewer.web.eval(js)

# ---------- Button Functionality ----------
def on_js_message(handled: bool, message: str, context):
    if not message == "get_sentence_for_card":
        return (False, None)
    cfg = mw.addonManager.getConfig(__name__)
    deck = cfg["per_deck"][str(mw.reviewer.card.did)]
    used_word = mw.reviewer.card.note().fields[0 if (deck["mode"] == "front") else 1]
    diff, lang = deck["difficulty"], deck["language"]

    QueryOp(
        parent=mw,
        op=lambda col: _run_in_worker(col, used_word, diff, lang),
        success=_on_success,
    ).without_collection().run_in_background()

    return (True, None)



def add_to_gui():
    gui_hooks.webview_will_set_content.append(add_button_html)
    gui_hooks.webview_did_receive_js_message.append(on_js_message)


