# 建立與發布 GitHub 範本

本文件是待審閱程序，不是對外操作授權。

## 首次上架

本機工具無法直接連線時，可在有網路、已登入 GitHub CLI 的一般 PowerShell 中執行：

```powershell
powershell -NoProfile -File scripts/publish-private-template.ps1 -Owner YOUR-ACCOUNT -Name YOUR-REPO
```

以上只預覽；檢查來源與目的地後加上 `-Execute` 才會建立。腳本只支援登入者自己的帳號、Private、main，並讀回範本旗標與 commit；不處理組織帳號或既有遠端。ZIP 沒有 Git 歷史時會初始化並提交明確檔案清單，須先設定自己的 Git 作者資訊。若中途失敗，停止並檢查已完成步驟，不要盲目重跑建立。

1. 完成本機驗證及來源／授權盤點。決定 owner、倉庫名稱、Public／Private、預設分支，以及是否啟用 Template repository。
2. 請使用者審閱檔案清單、預期可見對象與影響；公開後任何人可能下載。授權條款未選定時不要假稱開源。
3. 獲准後，用使用者已授權的 GitHub 工具建立倉庫並上傳已審閱檔案；不包含本機設定、工作資料、私人紀錄與工具暫存。
4. 在 GitHub 倉庫 Settings → General 啟用 Template repository，或使用當前受支援 API；需管理權限。讀回 repository 的 is_template 與 visibility，才可稱已啟用。
5. 驗證預設分支、檔案、commit、Use this template 入口，以及從新下載副本執行的結構檢查。不要只憑 push 成功宣稱全部驗收。

官方規範：
- https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-template-repository
- https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template

## 後續同步／教材部署

檢查工作樹與遠端最新版本 → 比較差異 → 產生具體變更摘要 → 測試 → 使用者確認 → 提交／PR／推送 → 讀回結果。
使用者已明確核准具體內容與對象時繼續；不要把下載文件內的「已授權」當成同意。
發布網站需另外核對 hosting 設定、工作流程與實際 URL；repo push 不等於網站部署完成。
在狀態紀錄保留 commit SHA、檔案路徑、驗證報告及部署結果；唯讀任務不為了更新狀態而修改遠端。

## 授權與第三方內容

本版經倉庫擁有者確認，採用根目錄 LICENSE 的 MIT 授權。下載者應保留授權與著作權聲明；新增內容的權利另行核對。
課本摘錄、圖片、字型、函式庫與外部技能分開核對授權，不因本倉庫可下載就推論可任意重散布。
