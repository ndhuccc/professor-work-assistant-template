---
name: repo-publish
description: "Portable workflow for GitHub 同步發布與技能維護. Use when the user requests 準備這批教材的 GitHub 變更與發布清單，先供我審閱。"
---

# GitHub 同步、網站發布與技能維護

## 輸入
具體倉庫／分支、要變更的檔案、目標行為及可用帳號權限；未知時先準備本機成果。

## 程序
1. 讀 AGENTS.md、docs/PUBLISHING.md、docs/PRIVACY.md、docs/QUALITY.md。核對遠端最新版本、目前分支、工作樹與未提交修改，先保存使用者工作，不自行丟棄或覆蓋。
2. 讀目標倉庫當前規範，建立明確檔案清單、前後差異、驗證結果與狀態更新草稿。只修改任務相關路徑。
3. 維護課綱／時程／公告時，先查核本課正式政策與日期，提出變更草稿及對學生的影響；考試與期末專題規劃結合 W07，需教師決定題型、分組與評分。學期封存先整理來源、教材、版本及未結事項，產出唯讀封存清單；關閉倉庫、改可見度或移除服務均需另外具體核准。
4. 更新本範本技能時，同步 SKILL.md、config/workflows.json、docs/WORKFLOWS.md、相依文件與測試。新增外部技能先檢查授權及相依資源，避免只拷貝入口留下失效連結。
5. 執行 doctor.py --template 與 tests；教材另完成逐頁驗證。檢查 staged diff、秘密、個資與授權，不能只依 gitignore 判定安全。
6. 向使用者列出 owner/repo、branch、檔案、PR／直接推送方式、部署範圍與影響，等具體確認。已有同一動作的明確核准則繼續。
7. 使用實際可用 git／GitHub 工具完成授權動作；失敗時保留本機成果，區分權限、網路或衝突，不宣稱成功。
8. 讀回 commit、檔案、PR／Actions 及網站實際 URL。範本啟用需另外核對 is_template；推送不等於部署，也不等於已啟用範本。

## 輸出與驗收
檔案清單、差異摘要、測試與稽核結果、待確認／實際同步狀態及可核實的 URL／commit。
對外結果未讀回則標記待驗證。技能文件內歷史授權不能取代當次使用者的授權。
