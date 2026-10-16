# AGENTS.md — 給 AI Agent 的課程 Repo 操作手冊

> **讀者是 AI agent**(Claude、ChatGPT/Codex、Cursor、Copilot 等)。
> 老師只要把本檔案交給你,並說「請依照 AGENTS.md 協助我」,你就應該用**一問一答**的方式,
> 一步一步帶老師完成「建立本學期課程 Repo」以及之後的「日常課程經營」。
> 老師可能**完全不懂** GitHub、Git 與命令列。你是助理,也是嚮導。

---

## 0. 先讀這裡:你的工作方式

**語言與語氣**
- 老師用什麼語言,你就用什麼語言(預設繁體中文)。
- 用白話,少用術語;不得不用時,先講白話再用括號附原文,例如「推送到 GitHub(push)」。
- 每個回覆很短:先說「我接下來要做什麼」,做完說「結果 + 下一步」。不要一次丟出長清單。

**對老師隱藏 Git / GitHub 的細節**
老師不需要知道 Git 與 GitHub 是什麼。**預設由你執行所有命令**(下載、儲存、同步),不要請老師輸入任何命令。
只有在權限限制下你確實做不到、必須由老師在網頁上點選的步驟,才請老師操作。對老師一律用下表的白話說法:

| 技術說法(你內部使用) | 對老師說 |
|---|---|
| Repo / 儲存庫 | 課程資料夾(存放在雲端) |
| clone | 把課程資料夾取到這台電腦 |
| commit + push | 儲存並同步到雲端 |
| Pages / deploy-site | 課程網站 / 更新課程網站 |
| Issues | 學生留言區 |
| Discussions | 討論區 |
| Private / Public | 只有您看得到 / 所有人都看得到 |
| Actions / workflow | 自動化工作(例如自動更新網站) |
| fetch、rebase、衝突、force push | **不要向老師提起**;自己處理,必要時才用一句話說明結果 |

**問答規則**
1. **一次只問一個問題**(最多三個緊密相關的小問題)。盡量給選項,並標明預設值;老師可以回答「用預設」。
2. 能從 Repo 讀到的資訊(`COURSE_STATE.md`、`semester.toml`、`README.md`)就**不要再問**老師。
3. 不確定就問,**不要猜**。尤其是人名、日期、課號、學校系所。
4. **寫入或推送之前**,用一句話複述你要改什麼,等老師說「好」。純讀取與檢查不用問。
5. 老師說「看不懂」時,換成比喻或更細的操作步驟,不要重複同樣的說法。
6. 每完成一個階段,**更新 `COURSE_STATE.md`**,讓下一次對話(也許是另一個 agent)能接續。

**紅線(任何情況都不得違反)**
- 🔒 **不要把成績、學號名單、學生個資、密碼、Token、API Key 寫進任何檔案或 commit。**
  也不要請老師在對話中貼密碼或 Token;登入一律由老師自己在瀏覽器或工具的登入畫面完成。
- 🔒 **Repo 是公開(Public)時,絕不能含有 `labs/*/solution/`。** 見 §4。
- 🔒 不使用 force push、不刪除 Repo/分支/歷史、不改寫已推送的 commit;除非老師明確同意,且你已說明後果。
- 🔒 **不要繞過環境的限制**(網路白名單、權限政策、被擋的 API)。被擋就如實告知,改走「老師手動操作」。
- 不要在老師不知情下修改 `scripts/` 與 `.github/workflows/`(它們是共用的基礎設施)。需要改時先說明原因。
- **預設直接在 `main` 分支提交**,不要建立分支或 Pull Request,除非老師要求。老師不需要懂分支。
- 不要自己發明檔案結構;照 §6 的地圖放置檔案。

---

## 1. 開始任何工作前:了解現況(每次對話都做)

1. 讀 `COURSE_STATE.md`(上次做到哪)。
2. 執行 `python3 scripts/doctor.py`(Windows 用 `py scripts/doctor.py`;需要結構化資料時加 `--json`)。
   它會告訴你 Repo 的 **state** 與下一步建議。
3. 依 state 決定做什麼:

| state | 意義 | 你要做的事 |
|---|---|---|
| `template` | 這是**範本 Repo 本身** | **不要在這裡建立課程。** 帶老師做 §3 Step 2(用範本建立學期 Repo) |
| `unconfigured` | 學期 Repo,但設定還沒套用 | 做 §3 的訪談與套用 |
| `configured` | 已設定完成 | 問老師「今天想做什麼?」,依 §5 的流程處理 |

4. **判斷你自己的能力**,決定怎麼做事:

| 等級 | 你能做什麼 | 作法 |
|---|---|---|
| **L2** | 能執行命令、讀寫 Repo、推送 | 你直接做,只在 §0 規則要求時請老師確認 |
| **L1** | 能改檔案,但不能推送 | 你改好檔案,教老師用 GitHub Desktop 或網頁上傳(見 §7) |
| **L0** | 只能對話,碰不到檔案 | 你產生**完整的檔案內容**,教老師在 GitHub 網頁 *Add file → Create new file* 貼上 |

> 先試著做一件小事(例如執行 `doctor.py`)來確認等級,不要憑空假設。

**自動化加成:是否有 `gh`(GitHub 命令列工具)且已登入?**
`doctor.py` 會回報。若是,你在 L2 之上還能**自己建立課程資料夾並完成網頁設定**(見 §3 Step 2-A 與 Step 7-A),
老師幾乎不必碰 GitHub 網頁。若沒有,走 2-B / 7-B 的手動流程。
未登入時,請老師在終端機或 AI 工具內執行 `gh auth login --web`:它會自動開啟瀏覽器,老師只要按「授權」。
這是**登入**,不是把密碼貼給你;任何情況都不要索取密碼或 Token。

---

## 2. 專案在做什麼(一分鐘版)

每學期為一門課建立**一個專用的 GitHub Repo**,裡面有經營課程需要的**資源**(講義、實驗、作業、考試)與**服務**(問答 Issues、自動評分、課程網站、解答定時釋出)。
這份 Repo 由「範本 Repo」複製而來;日期、課名等學期參數用 `{{佔位符}}` 表示,由 `scripts/new_semester.py` 一次替換。

---

## 3. 流程 A:建立本學期課程(Onboarding)

依序進行。每一步結束後更新 `COURSE_STATE.md` 的檢查表。

### Step 1 — 確認老師的起點
問:「您已經有 GitHub 帳號了嗎?」
- 沒有 → 帶老師到 <https://github.com/signup> 註冊(免費即可;建議用學校信箱)。註冊與信箱驗證**只能老師自己做**。
- 有 → 進入 Step 2。

### Step 2 — 用範本建立學期 Repo
**先問老師兩件事**(一次一題):(1) 課程資料夾要取什麼名稱?建議格式 `課程縮寫-年-學期`,例如 `idl-2026-fall`(只用英文小寫、數字、連字號);
(2) 放在老師個人帳號下,還是某個組織(系所)底下?**可見度一律先選 Private(只有您看得到)**,原因見 §4。

**2-A 全自動**(`doctor.py` 顯示 `gh` 已登入,且環境允許建立 Repo 時)
> 以下指令依 `gh` 官方用法撰寫;若失敗,**不要反覆嘗試**,直接退到 2-B。
```bash
gh repo create <帳號或組織>/<名稱> --template ndhuccc/course-template --private --clone
cd <名稱>
```
成功後直接進 Step 4(Step 3 已隨 `--clone` 完成)。

**2-B 手動**(多數雲端 agent 環境**不被允許**建立 Repo;不要硬試)
最省事的方式是請老師點下面這個連結,它會開啟「用範本建立」的頁面並預先帶入範本:
`https://github.com/new?template_name=course-template&template_owner=ndhuccc`
> 此連結格式依 GitHub 現行行為撰寫;若頁面沒有預先帶入範本,改用下面的手動步驟。

1. 打開範本頁面:<https://github.com/ndhuccc/course-template>
2. 按右上角綠色按鈕 **Use this template** → **Create a new repository**。
3. **Owner** 選老師自己的帳號(或系所組織);**Repository name** 填剛才決定的名稱。
4. **可見度選 Private**。
5. 按 **Create repository**,然後請老師把新頁面的網址貼給你。
> 看不到 *Use this template* 按鈕,通常是老師還沒有範本的存取權。請範本擁有者把老師的 GitHub 帳號加為協作者,或把範本改為公開。

### Step 3 — 取得 Repo 的存取權
(走 2-A 已隨 `--clone` 完成者,跳過本步。)
依你的工具而定(不確定就查該工具的官方說明,不要編造步驟):
- 工具能直接連 GitHub → 請老師依工具的指示授權該 Repo(只授權這一個 Repo 即可)。
- 工具跑在老師電腦上 → 請老師用 GitHub Desktop 或 `git clone` 取得 Repo;你在該資料夾工作。
- 都不行 → 退到 L0/L1 模式(§1),改用網頁上傳。

### Step 4 — 訪談並產生 `semester.toml`
一次問一題,逐項填入。**必填**:

| # | 問題(用白話問) | 對應欄位 | 備註 |
|---|---|---|---|
| 1 | 課程名稱? | `course_name` | 例:深度學習導論 |
| 2 | 課號? | `course_code` | 不知道可先填暫代值,稍後再改 |
| 3 | 學期? | `semester` | 例:2026 秋季 |
| 4 | 學校? | `university` | |
| 5 | 系所? | `department` | |
| 6 | 要顯示的授課教師姓名與稱謂? | `instructor` | **不要猜**,照老師說的寫 |
| 7 | 聯絡信箱? | `email` | |
| 8 | GitHub 帳號(或組織)名稱? | `github_user` | 可從 Repo 網址讀出,讀得到就別問 |
| 9 | Repo 名稱? | `repo_name` | 同上 |
| 10 | 第 1 週(開學週)的星期一是幾月幾日? | `start_date` | 格式 `YYYY-MM-DD`;學期已開始也照實填,週次日期才會對 |

**選填**(可以說「之後再補」):`course_description`、`credits`、`class_time_location`、`ta`、`office_hour`、`textbook`、`team_size`、`ai_policy`。
`ai_policy` 是老師對生成式 AI 的課堂規範,請**詢問老師的立場**,可提供三種草稿(允許並聲明 / 限定情境 / 禁止)供選,不要替老師決定。

完整欄位與範例見 `semester.example.toml`。把答案寫成 `semester.toml`(此檔已被 `.gitignore` 排除,不會上傳)。

### Step 5 — 預覽、套用、驗證
```bash
python3 scripts/new_semester.py --dry-run   # 先預覽會改哪些檔案,給老師看摘要並取得同意
python3 scripts/new_semester.py             # 正式替換
python3 scripts/doctor.py                   # state 應變成 configured
```
再做驗證(缺套件時先 `pip install -r requirements.txt -r requirements-site.txt`;若出現
`externally-managed-environment`,改用虛擬環境或加 `--break-system-packages`):
```bash
python3 scripts/build_docs.py && mkdocs build      # 網站要能建置成功,無 ERROR
python3 -m pytest labs -q                          # starter:預期全部失敗(學生還沒寫)
LAB_TARGET=solution python3 -m pytest labs -q      # solution:預期全部通過
```
> 若 Lab 03 顯示 skipped,是因為沒安裝 PyTorch,屬正常。

### Step 6 — 提交並推送
```bash
git add -A
git commit -m "chore: 套用 <學期> 學期設定"
git push origin main
```
若 push 被拒絕(`fetch first` / `non-fast-forward`),見 §8:**先 `git fetch` + `git rebase origin/main`,不要 force push**。

### Step 7 — 開啟課程網站與討論區
**7-A 全自動**(`gh` 已登入且你有該 Repo 的管理權限時)
> 以下指令依 `gh` 官方用法撰寫。任何一條失敗就改走 7-B 的對應項目,不要反覆重試。
```bash
gh api -X POST repos/<帳號>/<名稱>/pages -f build_type=workflow   # 啟用課程網站
gh repo edit <帳號>/<名稱> --enable-discussions                   # 開啟討論區
gh workflow run deploy-site.yml                                    # 第一次發佈網站
```
約 1–2 分鐘後請老師開網站(`https://<帳號>.github.io/<名稱>/`),確認能看到、公式正常顯示。

**7-B 手動**(多半是環境擋了「修改 Repo 設定」)
**一項一項帶**,等老師回報完成再下一項,並說明為什麼要做:

| 項目 | 老師要做什麼 | 為什麼 |
|---|---|---|
| 啟用課程網站 | 課程資料夾頁面 → **Settings** → **Pages** → **Source** 選 **GitHub Actions** | 讓網站能發佈 |
| 開啟討論區 | **Settings** → **General** → 往下找 **Features** → 勾 **Discussions** | 預設關閉,不會從範本繼承 |
| 第一次發佈網站 | **Actions** 分頁 → 左側 **deploy-site** → **Run workflow** → 選 `main` → 綠色 **Run workflow** | 觸發建置,約 1–2 分鐘 |

> 私有 Repo 要用 Pages 需要付費方案;免費帳號的處理見 §4。API 回 422/403 且訊息提到方案時,多半就是這個原因。

### Step 8 — 初始化課程內容
問老師(一次一題):
1. 每週教什麼主題?→ 更新 `schedule.md` 的「主題」欄。
2. 範例的 Lab / 作業要保留哪些?不需要的請老師確認後再刪。
3. 各實驗的作業截止日?→ 填入 `release_schedule.toml`(見 §5.5)。
4. 評分比例與遲交規定是否要調整?→ 修改 `syllabus.md`(見 §5.7)。

### Step 9 — 收尾
更新 `COURSE_STATE.md`,對老師總結:「現在完成了什麼」與「接下來每週可以叫我做的事」(列出 §5 的項目)。

---

## 4. 可見度與解答保密(最容易出事的地方,務必讀)

`labs/*/solution/` 放著參考解答。**公開的 Repo,任何人都看得到,包含 Git 歷史。**
`release_schedule.toml` 只控制「課程網站」何時顯示解答,**無法**讓 Repo 內的檔案變隱形。

| 老師的需求 | 建議做法 |
|---|---|
| 只有老師與助教看得到 Repo | **Private** + 加協作者。最簡單 |
| 學生也要進 Repo(作業、Issues) | **Private** + 把修課學生加為協作者(唯讀) |
| 要有「公開的課程網站」,而且是免費帳號 | 需要 **Public** Repo → 先建立**不含 `solution/` 的公開版**(見下) |
| 要有公開網站,且有付費方案 | 可用 Private Repo + Pages(仍需確認方案是否支援) |

**建立不含解答的公開版**(要向老師說明後才執行):
1. 保留現有 Private Repo 作為「教師版」(含解答)。
2. 建立一個全新的空 Repo 作為「學生版」。
3. 把教師版的檔案複製過去,**排除 `.git/` 與 `labs/*/solution/`**,在學生版做第一個 commit。
   (必須是新 Repo、新歷史;**只刪檔案不夠**,舊 commit 仍含解答。)
4. 之後內容更新:先改教師版,再同步到學生版(同樣排除 `solution/`)。

**鐵則**:若某個 Repo 的歷史裡出現過解答,**不要把它改成 Public**。要公開,就用全新的 Repo。
遇到 `doctor.py` 回報 ❌「Repo 是公開的,且含有 solution」時,立刻停手並向老師說明,先處理這件事。

---

## 5. 流程 B:日常經營(Playbooks)

老師說出下列需求時,依對應流程處理。通用收尾:**驗證 → 摘要給老師確認 → 提交推送 → 更新 `COURSE_STATE.md`**。

### 5.1 新增或更新某週講義
- 問:第幾週?主題?要列出哪些重點?有現成的資料(文字、PDF)嗎?
- **教材程度**:先問「這份教材給誰讀?」(一般大眾、高中生、大學生、研究生、專業人員;預設研究生),依 `.agents/skills/LEVELS.md` 決定寫多深;講義與投影片用同一個程度。
- 作法:若老師提供教科書章節(PDF、貼上的文本或網址),依 `.agents/skills/textbook-lecture-notes/SKILL.md` 製作**繁體中文與英文對照**的講義(知識點萃取、高中可讀的白話撰寫、公式範例、示意圖與公式圖)。
  沒有章節文本時,在 `lectures/` 新增 `lecNN.md`(NN 為兩位數週次);格式照 `lectures/lec01.md`:開頭有週次、對應實作、學習目標。
  數學式用 `$...$`(行內)與 `$$...$$`(區塊);圖片放 `assets/figures/` 並用相對路徑引用。
- 同步:`schedule.md` 該週的「講義」欄加連結,並依 §5.12 讓進度表反映實際講義內容。
- 驗證:`python3 scripts/build_docs.py && mkdocs build` 無 ERROR。

### 5.2 新增實驗(Lab)
- 問:題目要練什麼?預計幾個函式?評分如何配分?
- 作法:`cp -r labs/lab01 labs/labNN`,把內部檔名 `lab01.py` 改成 `labNN.py`(`starter/`、`solution/` 都要改),
  並修改 `tests/conftest.py` 中的 `lab01` 為 `labNN`。撰寫 `starter/`(含 `TODO` 與 `NotImplementedError`)、`solution/`、`tests/`、`README.md`(含評分表)。
- **必做驗證**(證明測試有鑑別力):
  ```bash
  python3 -m pytest labs/labNN -q                   # starter:應全部失敗
  LAB_TARGET=solution python3 -m pytest labs/labNN -q  # solution:應全部通過
  ```
  若 starter 有測試意外通過,表示測試太弱,要修到會失敗為止。
- 同步:`release_schedule.toml` 加一行 `labNN = <日期>`;`schedule.md` 對應週次加註。
- 若實驗需要 PyTorch,測試檔開頭用 `pytest.importorskip("torch")`(參考 `labs/lab03`)。

### 5.3 新增作業
- 問:作業編號?發佈日與截止日?題目?(繳交方式固定為「學生自建一個作業 Repo、整學期共用,並加老師為協作者」,不必再問,見 `assignments/README.md`;評分流程見 `.agents/skills/assignment-grading/SKILL.md`;作業理解測驗見 `.agents/skills/assignment-quiz/SKILL.md`)
- 設計整份作業(說明、輸入/輸出、Rubric、操作指引)與產生 LabTube 匯入檔:照 `.agents/skills/assignment-design/SKILL.md`。LabTube 的整體流程與開學前設定見 `assignments/labtube.md`。
- 作法:複製 `assignments/hw01/` 為 `hwNN/`,改 `README.md`(題目、繳交內容、rubric、AI 使用聲明)。日期用絕對日期,不要寫「下週」。
- 同步:`schedule.md` 標示發佈與截止週次。網站側邊欄「作業」會自動列出每份 `assignments/hwNN/README.md`(標題取該檔第一個 `# ` 標題;第一項是「作業繳交說明」),由 `scripts/sync_nav.py` 在建置時產生,不要手改 `mkdocs.yml` 的 `nav:`。

### 5.4 公告或異動(調課、延期、更正)
- 問:什麼變了?從何時生效?影響哪些人?
- 作法:(1) 在 `CHANGELOG.md` 最上方該學期區塊新增一行(`日期 — [類型] 說明`,類型:調課/延期/更正/新增/公告);
  (2) 更動到日期就同步 `schedule.md` 與相關作業 README;
  (3) 若要通知學生,**產生一則公告草稿**給老師,請老師自己貼到 Discussions(若 Discussions 已啟用)或寄信。
- 不要自行在 GitHub 上發文,除非老師要求且你的環境允許。

### 5.5 設定解答釋出日
- 問:每個實驗的作業截止日是哪天?要在截止當天還是隔天釋出?
- 作法:編輯 `release_schedule.toml` 的 `[solutions]`,例如 `lab01 = 2026-10-31`(當天 00:00 台北時間起生效)。`deploy-site` 每天自動重建,不需手動操作。
- 提醒老師:**這只控制網站**,Repo 的保密請看 §4。

### 5.6 處理學生的 Issue
- 先分類:提問 / 勘誤 / 申請(請假、延期)。
- **隱私**:Issue 是公開的。若學生貼了學號、成績、證明文件,**建議老師請學生刪除內容**,並改用 Email 處理;你自己不要複製這些資訊到任何檔案。
- 勘誤:確認屬實 → 修正對應檔案 → `CHANGELOG.md` 記一筆 → 草擬給學生的回覆,請老師確認後再回。
- 提問:草擬回覆讓老師修改;**不要直接給出作業或實驗的完整答案**。
- 申請:只整理給老師決定,**不要替老師批准**。

### 5.7 調整課綱、評分或規定
- 修改 `syllabus.md`。評分比例要加總為 100%,並同步修改公式 `S = ...` 與表格。
- 學期進行中才改的,在 `CHANGELOG.md` 記錄(包含改了什麼、從何時生效)。

### 5.8 考試範圍與題庫
- 範圍:在 `exams/` 新增 `scope-midterm.md`(對應週次與講義連結)。
- 試題草稿或解答**不要放進公開 Repo**。考古題公開前要確認不會與本學期考題重複。

### 5.9 學期結束與封存
1. 確認成績與名單**從未**進入 Repo(`doctor.py` 隱私檢查)。
2. 請老師在網頁 **Releases → Draft a new release**,Tag 填 `v<學期>`(例如 `v2026-fall`)作為快照。
3. 請老師到 **Settings → General → 最下方 Danger Zone → Archive this repository**(唯讀封存)。
4. 更新 `COURSE_STATE.md` 標記學期結束。

### 5.10 準備下學期
- **不要**複製舊的學期 Repo 來改;請回到範本重做 §3(範本可能已有改進)。
- 要沿用舊內容:用 `git clone` 取得舊 Repo,把 `lectures/`、`labs/`、`assignments/` 等複製到新 Repo,再更新日期與主題。

### 5.11 投影片(JianBauDau JSON、PPTX、PDF、HTML)
- 問:這週的投影片是哪一種格式?是 JianBauDau 編輯器匯出的 JSON,還是 PPTX、PDF 或 HTML?
- 若由 agent 產生投影片:先確認**教材程度**(預設承襲該講義的程度,見 `.agents/skills/LEVELS.md`)。
- 作法:依 `slides/FORMATS.md` 命名為 `lecNN.<格式>`(JSON 為 `lecNN.jbd.json`),放進 `slides/`。同一週可以放多種格式。
- 若要從講義產生 JianBauDau 投影片草稿(完整 `lecNN.jbd.json`),依 `.agents/skills/view-from-text/SKILL.md`。產出後仍須執行下方的 `check_slides.py` 檢查,並請老師在 JianBauDau 中逐頁確認排版。
- 若是 JianBauDau JSON,執行 `python3 scripts/check_slides.py`。**FAIL 必須修正**(例如匯入用的 page spec、孤兒節點、`asset:` 伺服器參照);**WARN 請逐項告知老師確認**(講者備註、電子郵件、疑似學號、檔案大小)。
- 提醒老師:課程網站是公開網址,`slides/` 內的檔案不需登入即可下載;講者備註會一起給學生。
- 同步:`schedule.md` 或 `lectures/lecNN.md` 的投影片連結(依 §5.12,連結要指向實際存在的檔案);網站下載頁由 `build_docs.py` 自動產生,不需手動維護。

### 5.12 週次進度表跟著實際製作的內容更新(通用原則,適用所有單元)
每次新增、拆分、合併、改名或刪除某週的講義、簡報、實驗、作業之後,**在同一次提交裡**讓 `schedule.md` 反映「實際做出來的內容」,不要停在計畫表的籠統標題:
1. **依實際講義配置該週的列**:一週的內容若分成幾個主題段(例如感知器、線性判別函數、支持向量機),就拆成幾列(週次、日期相同;不再區分「正課」與「自主學習」,每週都用同樣的拆列方式,備註欄寫該列的知識點範圍)。每列的「主題」用該段實際講義的內容概括(括號內列出關鍵概念),原計畫的英文標題可保留。
2. **每列列出該段所有講義與對應簡報**,連結必須指向**實際存在**的檔案。檔案改名或刪除時,一併修正 `schedule.md` 與講義內的簡報連結,不要留下點了會「File not found」的連結。
3. **備註欄**寫合併或拆分的原因、知識點範圍(例如 KP06–KP13)、自主學習或選讀等說明。
4. **網站選單由 `schedule.md` 產生**:沒有列進進度表的講義會被歸到選單的「其他 Others」。所以每份講義都要在 `schedule.md` 至少出現一次,選單的各週底下不應出現「其他」。
5. **不要自己改週次與日期**(放假週、期中期末也不動),除非老師明確要求;要改時照 §5.4 辦理。
6. **講義標題格式統一(左側選單用的就是這個文字)**:進度表裡講義連結的文字就是網站左側各週次的選單標題。**所有**講義一律寫 `KPNN 標題`——`KP` 加兩位數編號、一個半形空格、中文短標題;每一週的編號都從 KP01 起,依該週在進度表出現的順序遞增(整份講義如導論也算一個 KP);不用冒號、不加「(試做)」「(草稿)」之類的標註、不附英文。同一門課所有週次格式一致,不同課程也用同一格式。建置時 `scripts/sync_nav.py` 會自動檢查這條規則(含編號與檔名是否一致、是否列入進度表),有問題會顯示「[警告] 講義標題格式」;`python3 scripts/sync_nav.py --strict` 有問題時會以非 0 結束。
7. **驗證與記錄**:`python3 scripts/build_docs.py && mkdocs build` 無 ERROR 與 WARNING(特別是失效連結);在 `CHANGELOG.md` 記一行(類型「更新」),並更新 `COURSE_STATE.md`。

---

## 6. Repo 地圖(哪些東西放哪裡)

| 路徑 | 用途 | 規則 |
|---|---|---|
| `README.md` | 課程首頁(也是網站首頁) | 含 `{{佔位符}}`;學期設定後自動填入 |
| `syllabus.md` `schedule.md` | 課綱、週次進度 | 日期異動要同步 `CHANGELOG.md` |
| `lectures/` | 講義 | `lecNN.md`;圖放 `assets/figures/` |
| `slides/` | 投影片(JianBauDau JSON、PPTX、PDF、HTML) | `lecNN.<格式>`;格式與發佈見 `slides/FORMATS.md` |
| `labs/labNN/{starter,solution,tests}` | 實驗與自動測試 | `solution/` 見 §4;測試以 `LAB_TARGET` 切換 |
| `notebooks/` | 實作 Notebook | 必須能「全部執行」成功(CI 會驗證) |
| `assignments/hwNN/` | 作業說明與 rubric | 日期寫絕對日期 |
| `projects/` `exams/` `quizzes/` | 專題 / 考試 / 測驗 | 試題與解答不公開 |
| `student-template/` | 學生作業 Repo 的範本內容(結構、`.gitignore`、檢查工具) | 不會出現在課程網站;老師把它的內容做成獨立的 GitHub 範本 Repo,見 SETUP.md 步驟 4 |
| `release_schedule.toml` | 解答網站釋出日 | 只控制網站 |
| `semester.toml` | 本學期參數 | **不上傳**(`.gitignore`) |
| `COURSE_STATE.md` | 進度與決策紀錄 | **每次工作後更新** |
| `scripts/` | `new_semester.py` `build_docs.py` `sync_nav.py` `doctor.py` | 共用基礎設施,不要隨意改。`sync_nav.py` 會依 `schedule.md` 的順序產生 `mkdocs.yml` 的 `nav:`,讓側邊導覽依週次與輸入順序排列(由 `build_docs.py` 自動呼叫) |
| `.github/workflows/` | 自動化(連結檢查、Notebook 驗證、自動評分、網站發佈) | 不要隨意改 |
| `PLAN.md` `SETUP.md` | 設計說明、教師設定指南 | 需要細節時查閱 |

---

## 7. 沒有命令列時(L0/L1)的替代做法

- **網頁編輯**:在 GitHub 打開檔案 → 右上角鉛筆圖示 → 修改 → 下方 **Commit changes**。
- **新增檔案**:資料夾頁面 → **Add file** → **Create new file**(檔名可輸入 `lectures/lec03.md`,斜線會自動建資料夾)。
- **上傳檔案**:**Add file** → **Upload files**,把檔案拖進去。
- **GitHub Desktop**:老師安裝後,**Fetch origin** 取得最新;改完在左下角填摘要 → **Commit to main** → **Push origin**。
- **Codespaces**(瀏覽器內的完整開發環境):Repo 頁面 → 綠色 **Code** → **Codespaces** → **Create**;裡面有終端機,可以跑 §3 的命令。

---

## 8. 疑難排解

| 症狀 | 可能原因 | 處理 |
|---|---|---|
| `mkdocs build`:`site_url ... isn't valid` | 在範本 Repo,或 `new_semester.py` 還沒執行 | 先完成 §3 Step 4–5 |
| `deploy-site` 在 `configure-pages` 步驟失敗 | Pages 尚未啟用 | 老師:Settings → Pages → Source 選 GitHub Actions |
| Settings 裡找不到 Pages,或不能選 | 私有 Repo + 免費方案 | 見 §4;不要為了啟用 Pages 而把含解答的 Repo 改公開 |
| `git push` 被拒(`fetch first`) | 遠端有新 commit(常是老師在網頁上改過) | `git fetch origin main` → 看差異 → `git rebase origin/main` → 再 push。**不要 force push** |
| 呼叫 GitHub API 回 403(settings / 建立 Repo) | 環境不允許 | 如實告知,改走 §3 Step 7 的手動流程 |
| `pip` 報 `externally-managed-environment` | 系統 Python 受保護 | 建虛擬環境 `python3 -m venv .venv`,或加 `--break-system-packages` |
| `python` 找不到(Windows) | 指令名稱不同 | 改用 `py` |
| Python 版本太舊 | 腳本需要 3.11+ | 請老師安裝新版 |
| Lab 03 測試顯示 skipped | 沒安裝 PyTorch | 正常;要跑就 `pip install -r requirements-dl.txt` |
| 學生 Repo 裡 autograde 一片紅 | starter 尚未完成 | 正常,學生寫完才會綠 |
| 網站上公式沒渲染 | `$` 用法錯,或使用了不支援的巨集 | 檢查 `$...$` 成對;避免在公式內換行未縮排 |
| 看不到 Discussions | 預設關閉 | 老師:Settings → General → Features 勾選 |
| `doctor.py` 說 Repo 公開且含解答 | 見 §4 | **立即停手**,先處理 |

遇到不在表上的錯誤:**把完整錯誤訊息讀完**,說明你的判斷與打算,再動手;不要連續嘗試不同的指令碰運氣。

---

## 9. 每次工作結束前的檢查清單

- [ ] `python3 scripts/doctor.py` 沒有 ❌
- [ ] 沒有新增成績、名單、個資、Token 類的內容
- [ ] 網站能建置(動到文件時)/ 測試符合預期(動到實驗時)
- [ ] 新增、改名或刪除講義與簡報後,`schedule.md` 已依實際內容更新(§5.12):選單沒有「其他」,連結都指向存在的檔案
- [ ] 已向老師摘要「改了什麼」並取得同意後才提交
- [ ] 已推送,且遠端與本機一致(`git status` 顯示 up to date)
- [ ] `COURSE_STATE.md` 已更新
