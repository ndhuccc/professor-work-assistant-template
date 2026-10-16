# LabTube 作業系統:老師導覽

> 本頁是**簡短導覽**。完整步驟與畫面請看《LabTube 教授使用手冊》(位於 LabTube 專案 `docs/manual/manual-teacher.pdf`)。
> 學生看的是另一份《LabTube 學生使用手冊》,見下方「給學生的資料」。

## 一份作業怎麼進行

| 階段 | 學生做什麼 | 老師做什麼 |
|---|---|---|
| ① 發佈 | 看作業說明 | 把作業建進 LabTube(單元 → 作業),設定發佈與截止時間 |
| ② 繳交 | 把程式放進**自己的作業 Repo**,截止前打標籤 `hwNN-submit` | 用 Repo 查核工具看誰準時、commit 是否有疑慮 |
| ③ 分享 | 在 LabTube 上傳**程式執行結果**(圖、GIF、短片;不傳程式碼) | 審閱執行結果 |
| ④ 口試 | 截止後約 8 分鐘,用手機回答 3 題針對自己程式的簡答 | 在本機用 AI 技能產生題目、開場、監看 |
| ⑤ 評分 | 看成績、必要時申請複核 | AI 評分後逐人複核,定案並公布 |

最終分數 = Rubric 分數 × ((1 − 比重) + 比重 × 口試得分率)。比重預設 0.5,可在「編輯課程」調整。

## 開學前,老師要做一次的事

1. **在 LabTube 建立本課程**,匯入修課名單。
2. **設定學生作業 Repo 的名稱前綴**:LabTube →課程節點按右鍵 → 編輯課程 →「學生作業 Repo 名稱前綴」,建議用課程縮寫加學年,例如 `pr-2026`。學生登記的 Repo 名稱必須是「前綴-hw-學號」,不符會被拒絕。
3. **建立學生作業 Repo 範本**:照 `SETUP.md` 步驟 4,把 `student-template/` 做成獨立的 GitHub 範本 Repo,名稱建議用同一個前綴,例如 `<前綴>-hw-template`。
4. 把以下網址公告給學生:作業 Repo 範本網址、LabTube 網址(<http://134.208.2.44:5005>)、學生手冊網址。
5. 在 GitHub 接受學生的協作者邀請(教師帳號 `ndhuccc`);用 Repo 查核工具時需要讀得到學生的 Repo。

## 每份新作業

1. 依 `.agents/skills/assignment-design/SKILL.md` 設計作業,產生 LabTube 匯入檔(`labtube.assignments.v1`,內含作業說明與 Rubric)。
2. LabTube → 課程 → 匯入作業:先「驗證並預覽」,確認後匯入。
3. 截止後:Repo 查核 → 產生口試題目(`.agents/skills/assignment-quiz/SKILL.md`)→ 開場 → AI 評分(`.agents/skills/assignment-grading/SKILL.md`)→ 複核 → 定案。

## 給學生的資料

- **作業 Repo 範本**:`student-template/` 的內容,做成獨立範本 Repo 後把網址公告給學生。
- **學生手冊**:[《LabTube 學生使用手冊》](labtube-student-manual/index.md)(課程網站上有網頁版與 [PDF](labtube-student-manual/LabTube-學生使用手冊.pdf))。
- 手冊中的課程名稱、Repo 前綴與教師帳號是 pr-2026 的範例,**換課程時請對照本學期設定**。

- **AI agent 提示詞**:[ai-agent-prompt.md](ai-agent-prompt.md)。學生複製貼給自己的 AI,它會依規範協助建立 Repo、記錄 AI 使用、準備文件與繳交。

## 注意

- 學生姓名、學號、成績**只留在 LabTube**,不要寫進這個 Repo。
- 口試題目與標準答案不要放進公開 Repo(見 AGENTS.md §5.8)。
