# 可攜執行與相依資源

下載者需有能讀寫檔案的 AI Agent，完整原工具鏈建議 Python 3.11+（包含使用 tomllib 的學期／網站工具），並使用自己的必要工具與帳號授權。部分基本腳本仍可用 Python 3.10。
本次保留的是原課程七項技能及核心課程路由、研究審查、任務紀錄流程；不是匯出所有 ChatGPT 平台技能、記憶或連線。

## 第一次執行

1. 讀 AGENTS.md，執行 `python scripts/bootstrap.py`。
2. 正式課程先依 [獨立課程建立指南](NEW-COURSE.md) 選擇本專案及其他 Git 工作樹外的新目錄，執行 `python scripts/create_course.py --id YOUR-COURSE --name "課程名稱" --destination ../YOUR-COURSE`。複製完整七項技能、共用資源、檢查工具、格式規格、需求檔及可建置的網站骨架；不帶入原作者課程進度、學生名冊或正式作業。只有明確加 `--demo` 的合成試跑才預設建立 workspace/courses/DEMO，不附發布 workflow，也不作正式 Repo。
3. 在回傳的 course_root 內執行工具，依其 GITHUB_SETUP.md 逐步建置、初始化獨立 Git、建立空白 GitHub Repo、推送並查核同一 commit 的 Actions；Pages 另行設定與核准。把已核實路徑加入 config/project.local.json 的 courses 設定，保留其他課程。建立器不初始化 Git、不建立遠端或變更全域設定。
4. 貼上文本可先執行純文字盤點；PDF、圖像、公式預覽依需求安裝 `python -m pip install -r requirements-lecture.txt`。安裝屬環境修改，先依使用者授權執行。
5. 原始投影片格式與所有稽核器已隨附。圖像生成與原生簡報島播放器仍由下載者自己的環境提供，缺少時誠實列未執行。

用 `python scripts/doctor.py --template --capabilities` 查核本機可用模組。套件已安裝不等於瀏覽器可啟動、公式 CDN 可連線或帳號可操作；必要時分別實測，不把模組存在視為整條流程通過。

## 工具位置與工作根目錄

`.agents/skills/` 保留完整原始技能資源。`course-support/` 保存它們需要的 root scripts、格式文件、需求檔與原課程規範來源。
原課程 AGENTS.md 及 assignments 說明供來源追蹤；新工作區使用 COURSE_AGENTS.portable.md，正式政策由當前教師設定。
原版的固定 lecNN 路徑在批次 KP 工作時可加 KP 尾碼，維持一個 KP 一個檔案；可執行工具依實際檔名傳入。
原 deckkit 從 DECK_WORK（預設目前目錄）讀取 figs.json；沒有附圖的測試教材也需建立內容為 `{}` 的 figures registry。以 DECK_KIT 指向課程副本內的 tools/deckkit，DECK_PFX 為每個 KP 的唯一前綴。這些是工作資料，放在該課 workspace／暫存目錄，不改原技能工具。
上游 example_deck.py 是特定課程的示例，需要該課的圖資，不是自足的最小示例。本範本另提供 `python examples/jbd_demo.py --course-root workspace/courses/DEMO --out workspace/demo/draft.jbd.json`，會初始化獨立的空圖資表，使用原版 deckkit 產生可檢查的合成簡報；不要把格式示例當作正式教材已驗收。
同一套完整技能複製到選定課程工作區後，腳本內以 __file__ 推得的根目錄才會正確，不需要原作者電腦或私人絕對路徑。
IDL 的上游轉檔器只有示範課號文字不同，原版差異檔保存在 profiles/idl/overrides；一般使用者以 --course 傳入自己的已核准代號。

## 來源與個人資料

原課程技能與資源逐檔保存來源 commit 及 Git blob SHA。只正規化部分 SKILL.md 的 YAML，正文保留；原檔另存 SOURCE.md 並核對。
個人課程路由改為設定驅動。研究審查與任務紀錄的核心原文保留，私人名冊與 Notion 目的地改由使用者提供。
原個人技能的歷史 references 附件目前無法取得；已依其主技能明文建立完整的可攜模板與契約，並明列為重建文件，不宣稱逐字原件。
未附任何真實學生名冊、考題、答案、成績、私人服務 ID、帳號授權與憑證。既有個人技能庫不會被此 repo 修改。

## 選用整合

LabTube 完整資料驗證器與教師端查核工具位於 integrations/labtube；先讀其 README。
郵件、Notion、Drive、GitHub、生圖與播放器使用目前 Agent 環境的工具，不能把可讀規範當成已連線或已完成。

OnlineQuiz 的第八項原技能 bloom-exam-designer 為 W14，保留完整正文與兩份參考資料，另見 integrations/onlinequiz/README.md。create_course.py 仍複製原課程七項工具；W14 從本範本根目錄執行，不需要改動課程副本。
