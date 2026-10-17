# 建立獨立課程與 GitHub 倉庫

正式課程必須放在本專案之外，並位於其他 Git 工作樹之外。建議把教授助理與每門課並排放在同一個專案資料夾，例如：

```text
Projects/
├── professor-assistent/   教授助理範本，有自己的 .git
├── YOUR-COURSE/           課程工作區，之後建立自己的 .git
└── ANOTHER-COURSE/        另一門課的獨立工作區
```

## Agent 引導順序

1. 載入 W01 的完整流程、pr2026-course-assistant 及本文件。先確認課程代號、名稱、獨立本機路徑；後續 GitHub 步驟再確認帳號、倉庫名稱、可見度及是否發布 Pages。不一次追問與目前步驟無關的資訊。
2. 說明並提供本專案同層的新目錄建議；使用者已有明確路徑就沿用。解析實際路徑、檢查目的地不存在、父層沒有 `.git` 目錄或檔案；ZIP 副本也不能在本範本內建立正式課程。
3. 從本範本根目錄執行建立器，必須明確指定 `--destination`。下列路徑僅示意；換成目前使用者選定的位置，不繼承作者電腦路徑：

   ```sh
   python scripts/create_course.py --id YOUR-COURSE --name "課程名稱" --destination ../YOUR-COURSE
   ```

   若已決定正式網站，可加 `--site-url https://YOUR-ACCOUNT.github.io/YOUR-COURSE/`；否則保留待設定。程式拒絕覆寫、範本內正式目錄與其他 Git 工作樹內的目的地；拒絕後不以 `--demo` 繞過正式課程的限制。
4. 讀回實際 `course_root` 及 `GITHUB_SETUP.md`；建立器會複製七項原技能、支援工具、可建置的 MkDocs 骨架、推送時的 Course checks 與手動 Pages 部署 workflow。這時尚無 `.git`、遠端倉庫或部署；正式課綱、日期、配分、授權仍待教師決定。
5. **切到新課程工作目錄**，依附帶的[GitHub 逐步指南](../templates/course/GITHUB_SETUP.md)一次處理一個階段：本機建置及審閱 → Git 初始提交 → 新建空白 GitHub Repo → 連接及推送 → 核對相同 commit 的 Actions → 選用 Pages 與目視驗證。外部動作另依 W13；已有本次具體核准不重問。
6. 將已驗證的獨立路徑與遠端記入本機課程設定，保留原設定及其他課程。交付時分別報告每個階段，不把建立目錄說成已發布。缺帳號／網路時繼續完成本機可驗證部分，提供確切待執行步驟。

## 示範模式

只有合成示範與測試可使用：

```sh
python scripts/create_course.py --id DEMO --name "示範課程" --demo
```

它仍可放在忽略追蹤的 `workspace/courses/DEMO`，包含合成作業及講義，不附對外發布 workflow。不得把這裡直接初始化成正式課程 Repo。若先前已在本專案內製作正式資料，先盤點未提交修改、私人資料及實際檔案清單，再規劃複製到全新外部目錄；不要自動移動、刪除或初始化巢狀倉庫，也不搬運本範本 `.git`。
