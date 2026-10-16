# deckkit — 版面流程工具(給大量 KP 簡報用)

把「頁面 = 一組卡片/表格/圖」寫成 Python,自動排版、超出就切「(續)」頁,用 `preview_deck.py` 量到的內容高度回灌,避免溢出。

檔案:`kit.py`(頁面、單元、組裝)、`flow.py`(Card/Row/Col/Table/Fig 流式版面)、`fit.py`(迭代量測)、`add_fig.py`(登錄圖)。

## 流程(在你自己的工作資料夾 W,不要放進 repo)
1. 圖腳本先產生 `assets/figures/<id>.svg`(深色)與 `.png`(淺色)。登錄:
   `py add_fig.py W <id> "<alt 文字>" <repo_root>`  → 寫入 `W/figs.json`
2. 寫 `W/deck_kpNN.py`(範本:`example_deck.py`),設 `DECK_PFX`(每個 KP 唯一,如 `lec03kp09`)。
3. `cd W; rm -f need.json; py <skill>/tools/deckkit/fit.py W deck_kpNN.py`(迭代到 grown 0,產生 `W/draft.jbd.json` 與 `W/prev/`)。
4. 稽核:`py tools/audit_deck.py W/draft.jbd.json ...`;縮圖:`preview_deck.py W/draft.jbd.json --sheets`;看 `W/prev/sheet_1.png`。
5. 通過後複製 `W/draft.jbd.json` 到 `slides/<name>.jbd.json`。

## 常用語法
`u = kit.Unit("u01", 標題, 0, 0)`;`u.flow(label, zh標題, en標題, 講稿, bridge(...), C(...), Table(...), Row(...))`;
手排頁:`p=u.page(label, zh, en)`、`p.card(key,x,y,w,h,text,c=色)`、`p.conn(a,hook,b,hook)`、`p.figure(id,x,y,w)`、`p.step(講稿)`。
色:`MAIN REF EDGE AUX WARN OK`。`T(zh, en(en_))` 組雙語行。第一個 step 的 speakerNotes 要記錄教材程度與時長。
