# v0.3.1 OnlineQuiz 整合紀錄

輸入：使用者提供 OnlineQuiz-Bloom-workflow-v1.0(2).zip（八個檔案）。原包 SHA-256：`99967c84bd6c6923613b1869742bfdfc297c8134803521959cdd837e16077200`。用途為一般課堂測驗的 Bloom 命題與 OnlineQuiz 題庫匯入；不取代學生作業個人化簡答的 assignment-quiz。

## 可審閱的變更

- 新增 W14 與原名 bloom-exam-designer；14 組工作程序、20 個技能入口（含六個相容別名）。
- 原技能全文、Bloom 指南與題幹技巧均內附；新增 OnlineQuiz 適配注意事項，原始入口另存 SOURCE.md。
- 保留原增補包八個檔案；其歷史「22 項通過」報告屬來源紀錄，不作為本次結果。
- 內附原轉檔腳本、OnlineQuiz 原 schema／匯入／計分程式，以及隔離執行原驗證碼的本機工具。
- 更新 AGENTS、README、流程索引、範例設定、能力與來源表。既有 13 項工作程序持續保留。
- 不附正式試題、學生資料、帳密或實際站台；私人輸出位置由當前使用者指定。

## 固定來源與適配

Bloom：ndhuccc/claude-skills-pipelines@58d6fc14769b82867aa3e53a7bef6969ee9e8f8a。已讀回正式 skills/bloom-exam-designer 及 references 的目錄，三檔 Git blob 與附檔一致。啟用入口正規化 YAML 並加入工作程序連結；原正文保留。

OnlineQuiz 目前固定版本：ndhuccc/OnlineQuiz-v2@32e27e422148e32c909f26a7b6f4cc5651bba5d4。v0.3.0 原先固定 5f81609e0fb9ebaa1536384f6e4d58c9f2d90f17，來源歷史已記錄於 config/source-bundle.json。以實際 schemas.py、import_json.py、grading.py 為契約；文件中的「必須 A. 前綴」及「同名提示覆蓋」不當成現行程式行為。

原生格式檢查執行原 ImportPayload 與原 validate_question_row 等四個純函式。以 AST 僅載入指定函式及兩個常數，使用 single／multiple 型別標籤，不載入 Django ORM、不連線、不寫資料庫。此驗證不等於完整後端或正式站台驗證。

## v0.3.0 初次整合驗證紀錄

以下為初次整合時執行結果，v0.3.1 驗證另列於後：

| 檢查 | 結果 |
|---|---|
| 原技能 metadata | quick_validate 通過 |
| 範本結構、索引、連結、設定與來源 | doctor --template --capabilities 通過；346 個固定來源檔與個人入口快照一致 |
| 完整回歸測試 | 30/30 通過，99.819 秒；原有 20 項與新增 10 項均完成 |
| 新增流程測試 | 答案位置、錯位字母、無效正解、題數、重複題幹／JSON key、計時／配分、未支援欄位均依契約處理 |
| CLI 與原碼驗證 | 轉檔及隔離原生驗證 CLI 實際執行；UTF-8 與 SHA 一致，拒絕覆寫，明確回報 imported=false |
| 原流程回歸 | 新課程複製、JBD 產生／稽核、JPEG 插頁及 LabTube 契約繼續通過 |

測試使用合成格式資料；未生成正式試卷。Windows 受限環境的預設暫存路徑無法寫入，改將測試暫存目錄指定到忽略追蹤的 workspace/test-temp 後完成全部測試，沒有修改正式工具以繞過檢查。

## v0.3.1 計分修正同步

使用者已修正並推送 OnlineQuiz-v2，本次讀回 master 的 32e27e422148e32c909f26a7b6f4cc5651bba5d4。其計分修正提交為 3fdc7eaa99a374fa82df75f980591d997cf486cd，最新提交另將匯入預設改為 60 秒。
同步 grading.py、schemas.py、import_json.py 三份原碼快照、來源 commit／blob SHA／位元組數；轉檔與驗證報告的 profile 同步新版。保留 source-package/ 八份原檔與舊來源歷史；適配轉檔工具的雙份雜湊另行記錄並驗證。
計分說明改為：空白一律 0；單選全對滿分，否則 0；已作答多選保留原公式。原生後端 answers.py 已讀回，確認依實際 Question.Type.MULTIPLE 傳入 is_multiple，而非依正解個數決定。

本次實際驗證結果：

| 檢查 | 結果 |
|---|---|
| 完整範本測試 | 35/35 通過，117.981 秒 |
| OnlineQuiz 相關測試 | 14 項通過，包含空白 0 分、單選全有全無、多選部分給分及單一正解的明確多選型別 |
| 計時與版本 | 轉檔預設 60 秒與原 schema 一致；明確 150 秒設定保留，兩支工具 profile 與來源 commit 一致 |
| 來源完整性 | doctor 通過；346 個固定來源、個人入口及本機適配雜湊一致；篡改適配工具會被拒絕 |
| 原包保存 | source-package/ 八個原檔未更動；舊來源 commit 保存在 source_history |

測試使用本機合成資料及固定原碼，不載入正式 ORM 或寫入正式題庫。站台部署與實際線上計分未在本次執行。

## 外部狀態與限制

執行 Agent：Codex（本次對話）。本次輸入為新版 OnlineQuiz 原始碼；輸出為 sync-onlinequiz-scoring 分支的 v0.3.1 快照、說明與來源紀錄。
GitHub 目標：ndhuccc/professor-work-assistant-template；依使用者要求同步最新快照、說明與來源紀錄，維持 Private 與 Template。發布驗收以本版 GitHub 提交及遠端回讀結果為準。不包含正式題庫匯入授權。
沒有針對真實教材命題、瀏覽器／KaTeX 目視、教師登入或正式資料庫匯入；沒有修改 OnlineQuiz、LabTube、PR、IDL 或個人技能庫。
難度／鑑別度僅能標示未施測預估。現行 OnlineQuiz 計分與可選 HTML 不同，學生版不得含可讀正解；執行規範見工作程序。
