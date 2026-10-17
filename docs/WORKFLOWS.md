# 工作程序與技能索引

版本 0.4.0：14 組程序、20 個技能入口（含六個相容別名），對應七份端到端流程文件。
先讀 AGENTS.md，依任務選定下列程序，再從範本根目錄執行 `python scripts/read_workflow.py W02`（換成當次 ID／技能名／別名）。工具會依序輸出完整 workflow 與原主技能；Agent 需讀取其內容及要求的參考資料，再開始工作。無 Python 時手動依同一順序完整讀檔，標示讀取工具未執行。

| 編號 | 用途 | 完整流程 | 主技能 |
|---|---|---|---|
| W01 | 課程進度盤點 | [course-management.md](../workflows/course-management.md) | [pr2026-course-assistant](../.agents/skills/pr2026-course-assistant/SKILL.md) |
| W02 | 來源轉講義 | [course-materials.md](../workflows/course-materials.md) | [textbook-lecture-notes](../.agents/skills/textbook-lecture-notes/SKILL.md) |
| W03 | 講義轉簡報島投影片 | [course-materials.md](../workflows/course-materials.md) | [view-from-text](../.agents/skills/view-from-text/SKILL.md) |
| W04 | 簡報加入四格漫畫 | [course-materials.md](../workflows/course-materials.md) | [slides-to-four-panel-comics](../.agents/skills/slides-to-four-panel-comics/SKILL.md) |
| W05 | 圖解與互動教材 | [course-materials.md](../workflows/course-materials.md) | [diagram-design](../.agents/skills/diagram-design/SKILL.md) |
| W06 | 自學指南與閱讀網頁 | [course-materials.md](../workflows/course-materials.md) | [self-study-web](../.agents/skills/self-study-web/SKILL.md) |
| W07 | 作業設計與匯入 | [assignment-labtube.md](../workflows/assignment-labtube.md) | [assignment-design](../.agents/skills/assignment-design/SKILL.md) |
| W08 | 學生作業初評 | [assignment-labtube.md](../workflows/assignment-labtube.md) | [assignment-grading](../.agents/skills/assignment-grading/SKILL.md) |
| W09 | 個人化理解測驗 | [assignment-labtube.md](../workflows/assignment-labtube.md) | [assignment-quiz](../.agents/skills/assignment-quiz/SKILL.md) |
| W10 | 研究生進度與論文審查 | [research-review.md](../workflows/research-review.md) | [review-graduate-research](../.agents/skills/review-graduate-research/SKILL.md) |
| W11 | 郵件期限與行政文件 | [admin-documents.md](../workflows/admin-documents.md) | [admin-documents](../.agents/skills/admin-documents/SKILL.md) |
| W12 | 任務紀錄與交接 | [repo-maintenance.md](../workflows/repo-maintenance.md) | [mission-log](../.agents/skills/mission-log/SKILL.md) |
| W13 | GitHub 同步發布與技能維護 | [repo-maintenance.md](../workflows/repo-maintenance.md) | [repo-publish](../.agents/skills/repo-publish/SKILL.md) |
| W14 | Bloom 命題與 OnlineQuiz 題庫匯入 | [onlinequiz-question-bank.md](../workflows/onlinequiz-question-bank.md) | [bloom-exam-designer](../.agents/skills/bloom-exam-designer/SKILL.md) |

## 依任務進入

- 課程盤點／新課／課務與封存：W01；需要教材製作時轉到 W02–W06。
- 講義、簡報、漫畫、圖解、自學閱讀頁：W02–W06 共享教材流程，直接從要求的分支開始；發布另走 W13。
- 作業設計、靜態初評、個人化簡答出題／批改：W07–W09 共享作業流程，嚴格保留不同資料格式與私人輸出。
- 研究審查 W10、行政 W11、一般課堂選擇題庫 W14，各有獨立流程。
- 任務紀錄／查詢／交接 W12 可獨立使用；W13 處理 Repo／技能維護與發布。兩者共享文件但各有獨立章節，紀錄不需要 GitHub。

## 層次與路由

AGENTS.md 規定入口與共同契約；本索引供人查找；config/workflows.json 的 workflow_path 與 path 分別指向流程文件及原主技能。
workflow 說明技能之間如何串接、必要輸入、執行順序、確認、輸出、驗收與失敗交接；SKILL.md 保留詳細專業規格，不能只依 workflow 摘要取代原技能。
六個舊通用名稱由 aliases 解析到正式程序，沿用同一 workflow_path；不為別名建立重複流程。W01–W14 的路徑、文件編號、主技能連結及本索引均由 doctor.py 檢查，未索引的流程文件也會報錯。

## 可攜性與驗證邊界

課程工作根目錄與範本根目錄依 docs/PORTABILITY.md 區分。原課程七項技能、共用 LEVELS／NARRATIVE／INVENTORY_FORMAT、來源快照與契約仍完整保留；來源版本記於 config/source-bundle.json。
流程中的正式日期、配分、人物、站台及私人目的地由目前使用者提供；不繼承原作者範例或歷史授權。不自動派遣子代理。
doctor 的結構通過與 reader 的文件讀入，不代表已執行業務、生圖、寄送、匯入、發布或完成目視；實際證據與缺項依各流程分別記錄。
