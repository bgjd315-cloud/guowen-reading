#!/usr/bin/env python3
"""把逐題判讀（reading_cls.py）與 data/ 的題目合成閱讀理解頁面用的資料。

由 build.py 呼叫：build_reading(root) 回傳
  {"items": [[考試, 年度, 題號, 考點, 答案, 能力, 陷阱, 提示, 題目文字], ...]}
考試：0 = 會考國文（data/guowen），1 = 學測國文（data/xuece）。
"""
import json
import re
import sys
from pathlib import Path

EXAMS = ["guowen", "xuece"]
MAXLEN = 240


def build_reading(root):
    root = Path(root)
    sys.path.insert(0, str(root / "tools"))
    from reading_cls import CLS

    items = []
    for ei, subj in enumerate(EXAMS):
        for f in sorted((root / "data" / subj).glob("1[0-9][0-9].json")):
            y = int(f.stem)
            d = json.loads(f.read_text("utf-8"))
            qs, rows = d["json:examData"]["q"], d["js:Q"]
            ans = d["js:ANS"]
            hints = CLS[subj][y].split("｜")
            if not (len(qs) == len(rows) == len(hints)):
                raise SystemExit(f"[錯誤] {subj} {y}：題數 {len(qs)}、分類 {len(rows)}、判讀 {len(hints)} 不一致")
            for i, (q, (_, lab), h) in enumerate(zip(qs, rows, hints)):
                skill, trap, hint = h.split(" ", 2)
                a = ans[i] if i < len(ans) else ""
                if str(q["n"]) in d.get("js:NS", {}):
                    a = "非選"
                text = re.sub(r"\s+", "", q.get("t", ""))
                text = re.sub(r"^\d+\.", "", text)[:MAXLEN]
                items.append([ei, y, q["n"], lab.replace("非選：", ""), a, skill, trap, hint, text])
    return {"items": items}


def build_practice(root):
    """練習卷用資料：只收選擇題，附題目與題組選文在試卷圖片上的裁切範圍。

    回傳 {"pages": {"e-y": [w, h]}, "groups": {"e-y-a": slices}, "items": [...]}，
    item = [考試, 年度, 題號, 答案, 能力, 陷阱, 提示, 考點, 題目裁切, 題組代號或"", 選項數]。
    """
    root = Path(root)
    reading = {(it[0], it[1], it[2]): it for it in build_reading(root)["items"]}
    pages, groups, items = {}, {}, []
    for ei, subj in enumerate(EXAMS):
        for f in sorted((root / "data" / subj).glob("1[0-9][0-9].json")):
            y = int(f.stem)
            ex = json.loads(f.read_text("utf-8"))["json:examData"]
            pages[f"{ei}-{y}"] = [ex["w"], ex["h"]]
            for q in ex["q"]:
                it = reading[(ei, y, q["n"])]
                ans = it[4]
                if not re.fullmatch(r"[A-E]+", ans):
                    continue  # 非選擇題不收
                g = next((g for g in ex["g"] if g["a"] <= q["n"] <= g["b"]), None)
                gid = ""
                if g:
                    gid = f"{ei}-{y}-{g['a']}"
                    groups[gid] = g["s"]
                nopt = 5 if len(ans) > 1 or "(E)" in q.get("t", "") else 4
                items.append([ei, y, q["n"], ans, it[5], it[6], it[7], it[3], q["s"], gid, nopt])
    return {"pages": pages, "groups": groups, "items": items}


if __name__ == "__main__":
    from collections import Counter
    idx = build_reading(Path(__file__).resolve().parents[1])
    print(len(idx["items"]), "題")
    print(Counter((it[0], it[5]) for it in idx["items"]))
