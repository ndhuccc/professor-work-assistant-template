# LabTube 檔案交換與驗證

已隨附原版 contracts.py、timeutil.py、scoring.py 及教師端 repo 查核、表單轉檔、排程工具，來源 commit 記於 config/source-bundle.json。
不包含 LabTube 網站、資料庫、學生資料或任何憑證；可在本機驗證資料，不需要連正式伺服器。

| schema | 用途 |
|---|---|
| labtube.assignments.v1 | 作業說明、日期、單元、Markdown sections |
| labtube.quiz.v1 | 三題 explain/change/reason，不含答案或選項 |
| labtube.answers.v1 | 學生作答匯出，不含姓名／email |
| labtube.grades.v1 | 每題 0/1/2 初評、理由與複核標記 |
| labtube.rubric.v1 | 作業分數與 evaluated_sha |
| labtube.repocheck.v1 | 版本與 commit 觀察中繼資料，不含原始程式 |

驗證命令：`python scripts/validate_labtube.py FILE --assignment hw01 --course YOUR-CODE`。
可驗證本機檔案內容；實際匯入仍需伺服器端依正式學生、作答鍵值、繳交 SHA、作業滿分與鎖定狀態再驗證，不能把本機通過說成已能安全寫入正式資料。
作業轉檔器在建立後的 course_root 內執行：`python .agents/skills/assignment-design/build_labtube_import.py hw01 --course YOUR-CODE`。
所有含個資或測驗的檔案存放教授指定且在 Git 工作樹以外的私人位置；只可用本 repo 的虛構示例做測試。
登入、匯入、施測、通知、定案與排程不是預設動作。原教師工具中任何排程命令都須先讀取並取得當前使用者明確授權。
