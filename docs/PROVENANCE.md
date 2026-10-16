# 來源與重用範圍

版本：0.2.0，建立日期：2026-10-17（Asia/Taipei）。

本版依使用者要求，補齊原專案的實際技能與執行資源。13 組程序對應 13 個主要入口，另有六個舊名稱相容入口，共 19 個技能入口。

## 已保留的原始技能

- 課程技能：textbook-lecture-notes、view-from-text、diagram-design、assignment-design、assignment-grading、assignment-quiz、slides-to-four-panel-comics。
- 協調、研究與紀錄入口：pr2026-course-assistant、review-graduate-research、mission-log。
- 自學網頁、行政文件與發布流程保留本範本的通用延伸，不假稱它們是其他個人技能的完整複製。

原課程七項技能與所有支援檔共 315 個；連同根目錄相依資源、IDL 差異腳本與 LabTube 契約／教師工具，共 340 個上游檔案可核對。
來源 repository、commit、Git blob SHA、目的地與適配資訊逐檔記於 config/source-bundle.json。
SKILL.md 啟用入口只正規化 YAML；原始正文保留，原入口另存在 vendor/original-entries。原個人技能入口亦保存雜湊及副本。

## 明確適配與限制

課程路由改為目前使用者設定，不預設擁有 PR／IDL 帳號權限。原課程 AGENTS 與政策來源保存在 course-support；新建課程使用可攜規範，不直接沿用原課正式日期、配分或教學進度。
研究與紀錄的個人名冊、服務目的地不散布。兩項個人技能的歷史 references 附件未能讀取；現有 references 是依主技能明文重建的可攜契約與模板，未宣稱是原附件。
本版不包含完整課程倉庫、原作者歷史任務、學生資料、參考答案、正式資料庫、憑證或所有平台技能；原課程工作副本的最新狀態仍需每次查核。

## 驗證意義

來源完整性檢查與本機流程測試可證明指定版本的工具已帶入並可在合成資料上執行，不代表所有教材內容、生圖、原生簡報島播放、正式 LabTube 匯入或外部連線都已驗證。
權限與帳號由下載者自己的環境提供。來源授權分別保留，詳 THIRD_PARTY_NOTICES.md；倉庫維持 Private，未取得改為 Public 的授權。
