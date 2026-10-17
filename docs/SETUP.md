# 初始化與個人設定

執行 `python scripts/bootstrap.py` 只建立 `config/project.local.json` 和 `workspace/` 下的 public、private、logs 目錄，不覆寫既有設定、不安裝工具、不連線。
可加 `--name "我的課程助理"`。設定內容不是憑證儲存區；密碼與 token 使用 Agent 平台本身的連線機制或本機秘密管理工具。

在 project.local.json 設定課程，例如：

```json
{
  "id": "DEMO",
  "name": "示範課程",
  "repository": "YOUR-ACCOUNT/YOUR-COURSE",
  "branch": "main",
  "local_root": "",
  "state_file": "COURSE_STATE.md",
  "timezone": "Asia/Taipei"
}
```

將這個物件加入設定的 `courses` 陣列；範例 owner/repo 是占位符，不是真實來源。
沒有課程倉庫時 repository 和 local_root 可留空，使用者直接提供來源即可；不能把空白當成已同步。
分支需依實際倉庫設定，不確定時先查核，不能將 main 當成已核實結果。
不同課程各自記錄狀態、時程、規範與版本。新增課程不需要改寫技能。

正式新課的 `local_root` 必須是本專案及其他 Git 工作樹外的獨立目錄；建議與 professor-assistent 同層。使用 `create_course.py --destination` 建立後，依 [新課指南](NEW-COURSE.md) 及課程內的 GITHUB_SETUP.md 逐步設定 GitHub 與 Actions，再把實際路徑、owner/repo、分支寫回本機設定。`workspace/courses/` 只用於明確 `--demo` 的合成試跑，不能當成正式課程 Repo。

`outputs.public_dir` 代表「可供公開審閱的草稿目錄」，不代表已公開或已授權發布。
`outputs.private_dir` 需填入使用者明確指定、位於所有已知 Git 工作樹以外的私人目錄，才可儲存評語、成績、推薦資料與學生測驗。
workspace/private 只是初始化占位目錄，不是合格的評閱目的地。檢查工具只能協助查核，無法替代使用者指定位置或確認雲端同步權限。

`integrations` 的 `unverified`、`available`、`unavailable` 是狀態註記。即使填 available，Agent 每次操作仍需確認當前工具與帳號；設定值不構成授權。
`logging.external_destination` 預設空白，外部紀錄須指定服務、工作區、目的地及授權範圍。

不支援自動讀取 AGENTS.md 的工具：把 AGENTS.md 加入對話並要求按連結讀取檔案。只支援單檔上傳的聊天介面：需另外上傳本次技能及相依文件，不能聲稱已讀整個倉庫。
