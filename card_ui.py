import asyncio, json, re, urllib.parse, urllib.request
import ssl

from aqt.webview import WebContent
from aqt.reviewer import ReviewerBottomBar
from aqt.operations import QueryOp
from aqt.utils import showInfo

# from openai import *

from aqt import gui_hooks, mw

def is_lang_deck() -> bool:
    cfg = mw.addonManager.getConfig(__name__)
    return (str(mw.reviewer.card.did) in cfg["per_deck"])

async def fetch_sentence(word: str, difficulty: str, language: str, key) -> str:
    """
    *** stub *** – replace with your LLM call.
    Must return plain text, no HTML.
    """
    sentence = await _fetch_from_openai(word, language, difficulty, key)
    return sentence


OPENAI_URL = "https://api.openai.com/v1/chat/completions"

async def _fetch_from_openai(word: str, language: str, difficulty: str, key) -> str:
    prompt = (
        f"Give me ONE {difficulty}-level example sentence in {language} "
        f"that naturally uses the word “{word}”. "
        "Return only the sentence (no translation, no quotation marks)."
    )

    #client = OpenAI()

    body = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 60,
        "temperature": 0.7,
    }).encode("utf-8")

    req = urllib.request.Request(
        OPENAI_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )

    ctx = ssl.create_default_context()  # system CA bundle
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        data = json.load(resp)

    text = data["choices"][0]["message"]["content"].strip()
    return re.sub(r"\s+", " ", text)

# ---------- add to UI ----------
def add_button_html(web_content: WebContent, context) -> None:
    if not isinstance(context, ReviewerBottomBar) or not is_lang_deck():
        return
    web_content.head += """<style>#mybtn { margin-left:8px; padding:4px 8px; font-size:12px; }</style>"""
    web_content.body += """
        <button id="mybtn" onclick="pycmd('get_sentence_for_card')">get example sentence</button>
    """

def _inject_sentence_js(sentence: str) -> str:
    boxed = json.dumps(sentence)     # safe JS string
    return f"""
    (function () {{
        let box = document.getElementById('exampleSentenceBox');
        if (!box) {{
            box = document.createElement('div');
            box.id = 'exampleSentenceBox';
            Object.assign(box.style, {{
                border: '1px solid #ccc',
                borderRadius: '4px',
                padding: '8px',
                marginTop: '12px',
                background: '#300300',
                fontSize: '14px',
                lineHeight: '1.4',
            }});
            // add to the end of the *main* card
            document.body.appendChild(box);
        }}
        box.textContent = {boxed};
    }})();"""

def _run_in_worker(_, word, diff, lang, key):
    """Runs in worker thread – fetch and *return* sentence text."""
    print(word)
    print(diff)
    print(lang)
    return asyncio.run(fetch_sentence(word, diff, lang, key))

def _on_success(sent: str) -> None:
    """Runs on Qt thread – safe to touch the webview."""
    print(sent)
    mw.reviewer.web.eval(_inject_sentence_js(sent))

# ---------- Button Functionality ----------
def on_js_message(handled: bool, message: str, context):
    if not message == "get_sentence_for_card":
        return (False, None)
    cfg = mw.addonManager.getConfig(__name__)
    key = cfg["global"]["api_key"]
    deck = cfg["per_deck"][str(mw.reviewer.card.did)]
    used_word = mw.reviewer.card.note().fields[0 if (deck["mode"] == "front") else 1]
    diff, lang = deck["difficulty"], deck["language"]

    QueryOp(
        parent=mw,
        op=lambda col: _run_in_worker(col, used_word, diff, lang, key),
        success=_on_success,
    ).without_collection().run_in_background()

    return (True, None)

# 1. helper that nukes the box if it exists
def _reset_sentence_box(_: "Card") -> None:
    mw.reviewer.web.eval(
        """
    (function(){
        var el = document.getElementById('exampleSentenceBox');
        if (el) { el.remove(); }
    })();
"""
    )




def add_to_gui():
    gui_hooks.webview_will_set_content.append(add_button_html)
    gui_hooks.webview_did_receive_js_message.append(on_js_message)
    gui_hooks.reviewer_did_show_question.append(_reset_sentence_box)


