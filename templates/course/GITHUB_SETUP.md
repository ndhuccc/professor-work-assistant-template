# 課程 GitHub 倉庫與 Actions 設定

這份指南供建立完成後的獨立課程目錄使用。開啟**課程目錄**的終端機，依序完成下列步驟；不要在教授助理範本目錄執行。建立器只建立檔案，尚未初始化 Git、建立遠端或部署網站。

Agent 應一次引導目前可做的步驟，讀回結果再繼續。先沿用使用者已指定的路徑、帳號、名稱與可見度，只詢問會影響下一步的缺項。建立倉庫、推送、開啟 Pages 與部署前，列出具體對象、內容及影響；已有當次同一動作的明確授權就繼續。

## 1. 確認這是獨立目錄

先核對課程 `course.json` 與實際路徑。在尚未初始化 Git 時執行：

```sh
git rev-parse --show-toplevel
```

預期為「not a git repository」。若顯示教授助理或其他倉庫的根目錄，先停止初始化，另選外部目錄。若已初始化，顯示的根目錄必須正好是本課程目錄；不要重建或覆寫既有倉庫。

正式課程與教授助理採同層或其他獨立目錄。技術上 Git 可形成巢狀倉庫，但外層推送不會把內層當成一般課程檔案一起管理，本流程不使用巢狀倉庫或 submodule。

## 2. 在本機先建置與審閱

需要 Python 3.11 以上。先確認環境，套件未備妥時經使用者同意後安裝；建議使用課程自己的虛擬環境。

```sh
python -m venv .venv
```

Windows PowerShell 啟用：`.\.venv\Scripts\Activate.ps1`；macOS／Linux 啟用：`source .venv/bin/activate`。若系統禁止啟用，Windows 可直接使用 `.\.venv\Scripts\python.exe` 取代以下的 `python`，不必變更全機執行政策。

```sh
python -m pip install -r requirements-site.txt
python scripts/check_slides.py
python scripts/build_docs.py
python -m mkdocs build --strict
```

`site/` 是建置結果，`.site_src/` 是中間產物，均不提交。用 `python -m mkdocs serve` 預覽並目視檢查後結束伺服器。預設 MathJax 使用 CDN，公式目視需有網路；建置通過不代表公式已渲染。

正式時程、配分與授權尚未決定的項目保持待設定。檢查所有預定提交檔案，確認無名冊、成績、評語、考題答案或憑證；Private 倉庫也不放這些資料。新課自製內容的授權由教師決定，上游條款保留於 `UPSTREAM_LICENSE`。

## 3. 建立本課程自己的 Git 歷史

只在步驟 1 確認尚未初始化時執行：

```sh
git init --initial-branch=main
```

若缺少 Git 作者資訊，填入使用者自己的名稱與 GitHub 認可的電子郵件；可選 GitHub 提供的隱私郵件。使用本倉庫設定即可，不代填或變更全機身分。

```sh
git config user.name "YOUR-NAME"
git config user.email "YOUR-VERIFIED-OR-NOREPLY-EMAIL"
git status --short
git add -- AGENTS.md README.md COURSE_STATE.md course.json mkdocs.yml GITHUB_SETUP.md LICENSE UPSTREAM_LICENSE .gitignore .agents .github scripts lectures assignments assets references projects exams labs notebooks study-guide FAQ.md glossary.md CHANGELOG.md CONTRIBUTING.md schedule.md syllabus.md "requirements*.txt"
git diff --cached --stat
git diff --cached
git commit -m "Initialize course workspace"
```

上述為新骨架的明確清單；教師後來加入檔案時需重新審閱，不直接用 `git add .` 或 `git add -A`。初始提交只存在本機。

## 4. 建立 GitHub 上的空白課程倉庫

先決定自己的 `OWNER/COURSE-REPO`、可見度與預設分支；公開範圍需具體核准。Agent 不預設使用範本作者帳號。

網頁方式：

1. 登入自己的 GitHub，點右上角 **＋ → New repository**。
2. 選擇擁有者，填入本課程倉庫名稱與說明。
3. 選擇 **Private** 或經核准的 **Public**。這是全新課程倉庫，無須啟用 Template repository。
4. **不要勾選新增 README、.gitignore 或 License**，保留空倉庫，避免與本機初始提交產生不同歷史。
5. 審閱後按 **Create repository**，記下實際 HTTPS URL。

若使用 GitHub CLI，可在確認工具可用後登入並核對帳號；已登入就不重做登入：

```sh
gh auth status
gh api user --jq .login
```

尚未登入時由使用者執行 `gh auth login`。取得具體核准後，可用下列指令代替網頁建立（將參數換成實際值；Public 必須明確改成 `--public`）：

```sh
gh repo create YOUR-ACCOUNT/YOUR-COURSE --private --source . --remote origin
```

不要套用本範本的 `publish-private-template.ps1`，它處理的是教授助理範本自身。建立失敗或結果不明時先檢查目標是否已存在，不盲目重試。

## 5. 連接遠端並推送

```sh
git remote -v
```

若尚無 origin，使用步驟 4 的實際 URL：

```sh
git remote add origin https://github.com/YOUR-ACCOUNT/YOUR-COURSE.git
```

CLI 建立時已設 origin 就跳過新增。若 origin 指到其他倉庫，先核對，不直接覆寫。

具體核准本次課程提交與目標後：

```sh
git push -u origin main
git rev-parse HEAD
git ls-remote origin refs/heads/main
git status --short --branch
```

本機與遠端 SHA 必須一致，工作樹乾淨，GitHub Code 頁也須看得到 `.github/workflows/` 與課程檔案。若遠端已有不同內容，停止比較，不使用 force push，也不把它當空倉庫處理。

## 6. 確認 GitHub Actions 自動檢查

本課程附 `check-course.yml`：推送、Pull request 或手動執行時，檢查簡報並嚴格建置網站。

1. 開啟課程倉庫 **Actions**，找到 **Course checks**。
2. 若 Actions 被停用，到 **Settings → Actions → General** 檢查目前帳號／組織政策；只在獲准範圍啟用所需官方 actions，不放寬不相關設定。
3. 開啟對應本次 commit 的執行紀錄，確認所有步驟成功；失敗時讀該步日誌修正後再提交推送。
4. 有 CLI 時可用 `gh run list --workflow check-course.yml --limit 5` 找到 run ID，再用 `gh run view RUN-ID` 或 `gh run watch RUN-ID`。核對其 commit，不能只看任意一次綠勾。

這個檢查只有 `contents: read`，不會發布網站。推送至 GitHub Repo 才會觸發 Actions；Actions 不是另一個 Git 遠端。

## 7. 選擇是否發布 GitHub Pages

本課程另附 `deploy-site.yml`，預設**僅手動觸發**。CI 檢查成功與網站公開是兩項不同狀態。

1. 確認目前帳號方案與倉庫可見度支援 Pages，並審閱網站內容、來源條款及可見對象。Private Repo 不代表網站必定只有教師可見；沒有支援時仍可使用 Actions 檢查，不能自動改成 Public。
2. 確認實際網站 URL，把 `mkdocs.yml` 的 `site_url` 與 `course.json` 的 `site_url` 更新為正式網址；不得繼續把 `example.invalid` 當成已設定。網站設定與推送均依本次具體授權執行。
3. 在 **Settings → Pages → Build and deployment → Source** 選 **GitHub Actions**。若有 environment 的分支保護或審核規則，保留並由有權限的人處理。
4. 在 **Actions → Deploy course site → Run workflow** 選 `main`，取得部署核准後執行。流程僅上傳 `site/`，部署工作使用 `pages: write`、`id-token: write` 及 `github-pages` environment。
5. 核對本次 commit 的 build、deploy 狀態與 Pages 實際 URL，開啟首頁、講義、下載與公式驗證；工作流程成功不替代目視。

若教師明確要求之後每次 main 推送都自動部署，在 `deploy-site.yml` 的既有 `'on'` 區塊改為以下內容，審閱後提交推送：

```yaml
'on':
  push:
    branches: [main]
  workflow_dispatch:
```

不要加入 `pull_request` 部署，也不另加每日排程。使用其他預設分支時，須同步修改上述分支與 deploy-site.yml 的 `if` 條件。

## 8. 記錄與後續使用

回到教授助理範本的 `config/project.local.json`，只更新本課對應項目的 `local_root`、`repository`、`branch` 與課程代號／名稱；保留其他課程及使用者設定。之後課程工具、Git 提交與網站建置都在本課程目錄執行。

分別記錄：本機骨架已建立、Git 已初始化、本機 commit、遠端 SHA 已核對、Course checks 通過、Pages 待設定／已部署、目視結果及下一步。任何未實測項目保留未驗證狀態。

官方參考（2026-10-17 查核）：[建立新倉庫](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository)、[GitHub CLI 建立倉庫](https://cli.github.com/manual/gh_repo_create)、[以自訂 workflow 發布 Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)、[Python 設定 action](https://github.com/actions/setup-python)。方案、權限與介面仍以實際帳號現況為準。
