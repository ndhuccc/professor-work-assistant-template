# 工作程序索引

先讀根目錄 AGENTS.md，再載入對應 SKILL.md。下表與 config/workflows.json 必須同步。
技能可組合；一條教材流程通常是 W01 → W02 → W03 → W04 → 共通品質稽核 → W13，最後用 W12 記錄。
W05、W06 可依教學需求加入。啟動某流程不代表同意對外操作。

| 編號 | 程序／技能 | 指令範例 |
|---|---|---|
| W01 | [課程進度盤點](../.agents/skills/course-status/SKILL.md) | PR：盤點 Ch03 教材目前完成哪些 KP。 |
| W02 | [來源轉講義](../.agents/skills/lecture-notes/SKILL.md) | 依這份來源製作初學者講義，一個 KP 一個 Markdown。 |
| W03 | [講義轉投影片](../.agents/skills/teaching-slides/SKILL.md) | 把這份講義製作成可教學的 HTML 投影片。 |
| W04 | [簡報加入四格漫畫](../.agents/skills/four-panel-comics/SKILL.md) | 逐一為簡報核心概念加入 16:9 四格漫畫。 |
| W05 | [圖解與互動教材](../.agents/skills/diagram-interactive/SKILL.md) | 用 HTML5 和 Canvas 製作可調整學習率的梯度下降教材。 |
| W06 | [自學指南與閱讀網頁](../.agents/skills/self-study-web/SKILL.md) | 把這份講義轉成自學指南與手機閱讀網頁。 |
| W07 | [作業設計與匯入](../.agents/skills/assignment-design/SKILL.md) | 根據這份教材設計作業，附評分標準。 |
| W08 | [學生作業初評](../.agents/skills/assignment-grading/SKILL.md) | 靜態初評指定學生 HW02 的指定繳交版本。 |
| W09 | [個人化理解測驗](../.agents/skills/assignment-quiz/SKILL.md) | 依這份學生作業設計三題簡答理解測驗。 |
| W10 | [研究生進度與論文審查](../.agents/skills/research-review/SKILL.md) | 對照教授上週建議，查核這週論文與實驗證據。 |
| W11 | [郵件期限與行政文件](../.agents/skills/admin-documents/SKILL.md) | 整理這些邀請信的截止日與待填推薦表。 |
| W12 | [任務紀錄與交接](../.agents/skills/mission-log/SKILL.md) | 整理這個任務的輸入輸出位置、狀態與下一步。 |
| W13 | [GitHub 同步發布與技能維護](../.agents/skills/repo-publish/SKILL.md) | 準備這批教材的 GitHub 變更與發布清單，先供我審閱。 |

## 所有程序共同的完成條件

1. 已讀來源並記錄版本／位置；讀不到的來源列為無法驗證。
2. 產出符合使用者指定格式，保留其手動修改及來源檔案。
3. 記錄適用驗證的通過、警告、未執行與失敗項目。
4. 成果可開啟，位置可追蹤，下一步具體。
5. 外部更動已獲具體核准且經實際結果查核，或明確標記為待確認／未發布。

## 跨程序工作

- 課綱、時程及公告：W01 查核現況，W11 準備通知草稿，W13 準備課程變更及同步。
- 考試與期末專題：W07 規劃題目、分組及評分，W08／W09 執行指定版本的初評與理解查核。
- 學期封存：W01 盤點成果，W12 記錄版本及未結事項，W13 準備可審閱封存清單及授權的外部操作。
