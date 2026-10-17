---
name: pr2026-course-assistant
description: "Route course work to the original lecture, JianBauDau, diagram, assignment and LabTube skills. Use for PR, IDL, 課程, 教材, 作業, 測驗 or course maintenance requests."
---

# 課程助理：可攜式入口

原技能名稱保留；本版將原作者 PR／IDL 帳號與快照綁定改為使用者設定。歷史原文保存在 vendor/original-entries，不作為當前帳號或授權。

1. 先讀根目錄 AGENTS.md、config/project.local.json、config/workflows.json、docs/PORTABILITY.md。選擇當次明確指定的課程；有歧義只問課程，不預設 PR、IDL 或任何學號前綴。
2. 對既有課程讀取該課最新 AGENTS.md、COURSE_STATE.md、schedule.md、syllabus.md，記錄 branch／commit。重新發現該課 .agents/skills，不把範本快照當成目前進度。
3. 沒有課程工作副本時，可先做來源盤點。正式新課先讀 docs/NEW-COURSE.md，引導選本專案及其他 Git 工作樹外的新目錄，以 `python scripts/create_course.py --id YOUR-COURSE --name "課程名稱" --destination ../YOUR-COURSE` 建立。切到回傳的 course_root，依其 GITHUB_SETUP.md 逐步引導建置、獨立 Git、空白 GitHub Repo、推送與相同 commit 的 Actions；Pages 另行設定及核准，各階段如實記錄。--demo 僅供本專案內合成試跑，不可用來建立正式課程 Repo；不覆寫或搬動舊工作區。
4. 原始技能中的「Repo 根目錄」一律指所選 course_root，並讀取該工作區內的技能／相依規格。授權讀取既有遠端不等於已取得可執行的本機工作副本。
5. 依程序載入原始技能：講義用 textbook-lecture-notes；簡報島用 view-from-text；圖解用 diagram-design；作業用 assignment-design；作業初評用 assignment-grading；三題理解測驗用 assignment-quiz；四格漫畫用 slides-to-four-panel-comics。
6. 教材先決定程度、章級／KP 級知識地圖、因果鏈、來源盤點與批次規劃。原技能要求先審閱規劃時照做；當次已明確核准或指示直接做時不重問。沒有使用者明確同意不派子代理。
7. 預設一個 KP 一份講義、一份簡報；講義來源使用 Markdown，簡報島使用真正的 PresentationDocumentV3。原技能的 lecNN 示範命名可加 KP 尾碼，工具支援時以實際路徑執行，不能用合併檔取代所有單檔。
8. 來源、數值、公式、雙語、圖片覆蓋與版面逐項驗證，使用原稽核器與播放／目視工具。工具缺失標明未執行，不宣稱草稿已通過播放器驗證。
9. 作業、個人化測驗、初評與研究資料遵守私人輸出規範。LabTube 的資料契約與教師端查核工具已隨附 integrations/labtube，先讀其 README，再做格式驗證；匯入及對學生操作仍需具體核准。
10. 狀態、課綱、公告、考試、專題及封存工作先提出草稿與影響。每門課的學生、期限、規準、Repo 名稱、可見度各自查核。不要將原課程的示範日期或評分比例當成新課政策。
11. 收尾交付成果、驗證報告、來源位置、待決事項與下一步，使用 mission-log 記錄。遠端更動另走 repo-publish 的確認及讀回程序。
