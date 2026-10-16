---
name: course-status
description: "Portable workflow for 課程進度盤點. Use when the user requests PR：盤點 Ch03 教材目前完成哪些 KP。"
---

# 課程進度盤點

## 輸入
課程 ID、當前來源或本機副本，以及盤點範圍；缺課程時依根目錄入口消歧義。

## 程序
1. 讀根目錄 AGENTS.md、docs/QUALITY.md、docs/PRIVACY.md。從設定選課，讀該課自己的 AGENTS.md、COURSE_STATE.md、schedule.md、syllabus.md；缺檔列明，不能當成沒有規範。
2. 遠端可讀時先取得目前 branch 與 commit，列出該版本完整檔案樹並遞迴發現技能。讀任務相關規範；本機副本記錄 dirty 狀態，不能冒充遠端最新版本。
3. 逐一核對 KP／單元的來源、講義、投影片、圖片及驗證報告；檢查實際內容與連結，不只看檔名。
4. 依證據區分已完成、部分完成、待驗證與無法讀取。來源中出現檔名但讀不到，記錄「無法存取」，不要直接說不存在。
5. 比較前次已確認狀態與正式期限，提出後續製作順序及待教師決定事項。

## 輸出與驗收
產出狀態表、來源版本、證據位置、缺項及下一步。可用 templates/course-state.md 準備狀態草稿。
唯讀盤點不修改遠端 COURSE_STATE.md；沒有遠端查核就不能宣稱 GitHub 已同步。
