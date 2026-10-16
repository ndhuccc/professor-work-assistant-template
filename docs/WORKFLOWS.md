# 原始技能與工作程序

先讀 AGENTS.md，再讀 config/workflows.json 指定的完整技能。版本 0.2.0 保留原課程七項技能及三個個人工作入口的原名稱，並保留六個舊名稱作相容入口。

| 編號 | 實際技能 | 用途 |
|---|---|---|
| W01 | `pr2026-course-assistant` | 課程進度盤點 |
| W02 | `textbook-lecture-notes` | 來源轉講義 |
| W03 | `view-from-text` | 講義轉簡報島投影片 |
| W04 | `slides-to-four-panel-comics` | 簡報加入四格漫畫 |
| W05 | `diagram-design` | 圖解與互動教材 |
| W06 | `self-study-web` | 自學指南與閱讀網頁 |
| W07 | `assignment-design` | 作業設計與匯入 |
| W08 | `assignment-grading` | 學生作業初評 |
| W09 | `assignment-quiz` | 個人化理解測驗 |
| W10 | `review-graduate-research` | 研究生進度與論文審查 |
| W11 | `admin-documents` | 郵件期限與行政文件 |
| W12 | `mission-log` | 任務紀錄與交接 |
| W13 | `repo-publish` | GitHub 同步發布與技能維護 |

原課程七項技能與全部相依資源在 .agents/skills；根目錄共用 LEVELS.md、NARRATIVE.md、INVENTORY_FORMAT.md 也保留。
原版 skill 入口保存在 vendor/original-entries，各檔來源版本與完整性記於 config/source-bundle.json。
新使用者先依 docs/PORTABILITY.md 建立課程工作區；只有實際課程根目錄才是原技能所指的 Repo 根目錄。
教材使用 W01 → W02 → W03 → W04 → 稽核 → W13；紀錄使用 W12。W05、W06 視需要加入。
課程維護／封存結合 W01、W11、W12、W13；考試與專題結合 W07–W09。
外部更動必須依使用者具體授權執行及讀回；流程選取不代表已連線或已發布。
