# settings_ui.py  – drop into your add-on
from __future__ import annotations
from aqt import mw
from aqt.qt import Qt
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QAbstractItemView, QSpinBox
)

DIFF_LEVELS = ["A1", "A2", "B1", "B2", "C1"]
MODE_LEVELS = ["front", "back"]            # “word target word is on … side”

# ---------- helpers ----------

def deck_dict() -> dict[str, int]:
    """name → id for all decks in the collection."""
    return {d.name: d.id for d in mw.col.decks.all_names_and_ids()}

def add_row(tbl: QTableWidget, deck_name: str, lang: str,
            diff: str, mode: str) -> None:
    r = tbl.rowCount()
    tbl.insertRow(r)

    # deck name (read-only)
    item = QTableWidgetItem(deck_name)
    item.setFlags(item.flags() ^ ~Qt.ItemFlag.ItemIsEditable)
    tbl.setItem(r, 0, item)

    # language
    lang_edit = QLineEdit(lang)
    tbl.setCellWidget(r, 1, lang_edit)

    # difficulty
    diff_box = QComboBox(); diff_box.addItems(DIFF_LEVELS)
    diff_box.setCurrentText(diff)
    tbl.setCellWidget(r, 2, diff_box)

    # mode
    mode_box = QComboBox(); mode_box.addItems(MODE_LEVELS)
    mode_box.setCurrentText(mode)
    tbl.setCellWidget(r, 3, mode_box)

def open_settings() -> None:
    cfg = mw.addonManager.getConfig(__name__)
    decks_all = deck_dict()                      # snapshot

    dlg  = QDialog(mw); dlg.setWindowTitle("Reibun settings")
    vbox = QVBoxLayout(dlg)

    # ---------- API key ----------
    api_row = QHBoxLayout()
    api_row.addWidget(QLabel("OpenAI API key:"))
    api_edit = QLineEdit(cfg["global"]["api_key"])
    api_row.addWidget(api_edit)
    vbox.addLayout(api_row)

    # ---------- per-deck table ----------
    tbl = QTableWidget(0, 4)
    tbl.setHorizontalHeaderLabels(["Deck", "Language", "Difficulty", "Mode"])
    tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # except widgets
    vbox.addWidget(tbl, 1)

    # preload rows from cfg
    for did_str, opts in cfg["per_deck"].items():
        name = mw.col.decks.name(int(did_str)) or f"(deck {did_str})"
        add_row(
            tbl,
            name,
            opts.get("language", cfg["global"]["default_language"]),
            opts.get("difficulty", cfg["global"].get("difficulty", "B1")),
            opts.get("mode", "front"),
        )

    # ---------- add / delete buttons ----------
    btn_row = QHBoxLayout()

    def choose_and_add() -> None:
        remaining = {n: i for n, i in decks_all.items()
                     if str(i) not in cfg["per_deck"]}
        if not remaining:
            return
        picker = QComboBox(); picker.addItems(sorted(remaining))
        sub = QDialog(dlg); sub.setWindowTitle("Add deck")
        sub_box = QVBoxLayout(sub); sub_box.addWidget(picker)
        ok = QPushButton("Add"); sub_box.addWidget(ok)
        ok.clicked.connect(sub.accept)
        if sub.exec():                                # user pressed Add
            name = picker.currentText()
            did  = remaining[name]
            add_row(tbl, name,
                    cfg["global"]["default_language"],
                    cfg["global"].get("difficulty", "B1"),
                    "front")
            cfg["per_deck"][str(did)] = {}            # placeholder

    add_btn = QPushButton("Add deck"); add_btn.clicked.connect(choose_and_add)
    btn_row.addWidget(add_btn)

    def delete_selected() -> None:
        # rows currently highlighted by the user
        rows = sorted(
            {idx.row() for idx in tbl.selectionModel().selectedRows()},
            reverse=True
        )
        if not rows:
            return

        for r in rows:
            name = tbl.item(r, 0).text()  # deck name in column 0
            did = decks_all[name]
            tbl.removeRow(r)
            cfg["per_deck"].pop(str(did), None)  # drop from config

    del_btn = QPushButton("Delete selected"); del_btn.clicked.connect(delete_selected)
    btn_row.addWidget(del_btn)

    btn_row.addStretch()
    vbox.addLayout(btn_row)

    # ---------- save ----------
    save_btn = QPushButton("Save")
    def save() -> None:
        cfg["global"]["api_key"] = api_edit.text().strip()

        # rebuild per_deck from table rows
        new_per = {}
        for r in range(tbl.rowCount()):
            name = tbl.item(r, 0).text()
            did  = decks_all[name]
            lang = tbl.cellWidget(r, 1).text().strip()
            diff = tbl.cellWidget(r, 2).currentText()
            mode = tbl.cellWidget(r, 3).currentText()
            new_per[str(did)] = {
                "language": lang,
                "difficulty": diff,
                "mode": mode,
            }
        cfg["per_deck"] = new_per

        mw.addonManager.writeConfig(__name__, cfg)
        dlg.accept()

    save_btn.clicked.connect(save)
    vbox.addWidget(save_btn)

    dlg.exec()

def init_settings() -> None:
    mw.addonManager.setConfigAction(__name__, open_settings)

init_settings()          # register on import
