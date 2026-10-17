# 來源、授權與改動聲明

本範本自行撰寫程式與文件採根目錄 MIT。從原課程與 LabTube 帶入的檔案保留其來源與原授權，不因根目錄 MIT 而重新授權全部內容。
原課程授權全文保存在 course-support/LICENSE：程式碼為 MIT；教學內容為 CC BY-NC-SA 4.0。diagram-design 入口原文明列 MIT。各來源的具體適用範圍仍依其原授權。
來源與版本見 config/source-bundle.json；保留原作者署名與原授權。LabTube 本次只帶入資料格式與教師工具，不包含正式資料庫或服務憑證，其來源未見獨立 LICENSE，故保留來源標示，不宣稱這部分已取得額外公開再散布授權；目前目標 repo 維持 Private。
原始技能入口保存在 vendor/original-entries；啟用入口僅調整可解析 frontmatter、帳號設定與私人目的地，不刪減教材或評閱核心程序。
個人技能 references 的重建範圍詳 docs/PORTABILITY.md。公開發行前請擁有者核對混合來源的散布條款，本次不改可見度。

0.3.0 增補：bloom-exam-designer 來自 ndhuccc/claude-skills-pipelines@58d6fc14769b82867aa3e53a7bef6969ee9e8f8a；三份原文與來源標示保留。OnlineQuiz 原 schema、純驗證及計分程式來自 ndhuccc/OnlineQuiz-v2@5f81609e0fb9ebaa1536384f6e4d58c9f2d90f17。所取來源未提供可直接套用的獨立授權聲明，不將其宣稱為本範本 MIT，倉庫維持 Private。增補包由使用者提供，八個原檔完整保存；其中歷史驗證報告不當作本次驗證結果。

0.3.1 同步：OnlineQuiz 的 schema、匯入及計分原碼快照改為 32e27e422148e32c909f26a7b6f4cc5651bba5d4，保留原始位元組並更新逐檔 Git blob SHA。轉檔工具僅適配來源版本與 60 秒預設，原增補包不改動；兩者 SHA-256 及改動原因記於 config/source-bundle.json 的 local_adaptations。
