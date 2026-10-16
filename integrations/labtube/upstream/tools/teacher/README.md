# 老師本機工具(只在老師的電腦上執行,不放在伺服器)

伺服器**不保存任何 GitHub 憑證**。需要讀取學生 Repo 的動作,都由老師電腦上已登入的 `gh`(GitHub CLI)完成,結果檔再上傳到 LabTube。

| 工具 | 用途 |
|---|---|
| `repo_check.py` | 讀取學生作業 Repo 的標籤、事件與 commit 摘要,產生 `labtube.repocheck.v1` |
| `schedule_repo_check.ps1` | 在 Windows 工作排程器登記截止前後的查核時間 |
| `form_to_answers.py` | 過渡方案:把表單匯出的 CSV 轉成 `labtube.answers.v1`,讓 AI 照常評分 |

## 學生的 Repo 與目錄

每位學生每門課只有**一個** Repo,各作業放在 Repo 內不同的目錄。學生在 LabTube 登記 Repo 一次,再為每份作業登記目錄(預設是作業代號,例如 `hw01`)。
`roster_hwNN.json` 會帶上每位學生的目錄,`repo_check.py` 只讀取該目錄底下的 commit,並把目錄寫回結果檔。

## 事前準備

1. 安裝 [GitHub CLI](https://cli.github.com/) 並登入教師帳號:`gh auth login`(登入由你自己在瀏覽器完成,不要把密碼或 token 貼給任何人或工具)。
2. 學生已把教師帳號邀請為作業 Repo 的協作者,且你已接受邀請。

## 截止前後的查核流程

1. 在 LabTube:**作業 → Repo → 下載查核清單**,得到 `roster_hwNN.json`(只含學號與 Repo 名稱)。
2. 登記排程(只需一次):

   ```powershell
   .\schedule_repo_check.ps1 -Roster C:\labtube\roster_hw01.json -DueLocal "2026-10-20 23:59" -OutDir C:\labtube\outbox
   ```

   會在截止前 10 分鐘起每 5 分鐘、截止時、截止後 5 分鐘與 6 小時各執行一次。**那些時間電腦要開機並連網**;漏掉的時段在 LabTube 總表會顯示為「尚未查核」。
3. 也可以隨時手動執行:

   ```bash
   python repo_check.py --roster roster_hw01.json --out C:\labtube\outbox
   ```

4. 截止後把 `outbox` 裡的結果檔一次上傳到 LabTube(可多選,整批驗證;順序不影響結果,系統依觀察時間排序)。

## 為什麼要多次查核?

- 標籤時間以 **GitHub 的事件紀錄**為準,但事件有延遲(30 秒到 6 小時)且只保留 30 天。
- 因此同時記錄「我們第一次看到標籤時的 SHA」:之後標籤被移到新版本、或被刪除,LabTube 會標示「標籤被移動」。
- commit 的時間是學生電腦填的,可以偽造;只當佐證,不當證據。

## 隱私與安全

- 結果檔**只含中繼資料**(短 SHA、日期、訊息第一行、變更檔數),不含任何程式或檔案內容。
- `repo_check.py` 拒絕把結果寫進 git 倉庫內的資料夾;`.gitignore` 也已排除 `repocheck_*.json`。
- 腳本不讀取、不印出任何 token。

## 過渡方案:系統完成前的口試

```bash
python form_to_answers.py --csv responses.csv --quiz quiz_hw01.json --out answers_hw01.json
```

CSV 需有「學號」欄,以及依序的三個答案欄(可選「提交時間」)。轉出的檔案可直接交給本機 AI 評分(`assignment-quiz` 階段 B)。這個方案**沒有**加入碼輪替、開始時限、裝置綁定與 IP 記錄,公平性較低,請在公告中說明。
