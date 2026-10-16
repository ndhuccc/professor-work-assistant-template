# Professor Work Assistant Template｜教授工作助理範本

將 AI Agent 變成可依程序工作的課程與研究助理。下載後，先請 Agent 閱讀 [AGENTS.md](AGENTS.md)。
本倉庫提供 13 組可直接閱讀的流程模組、設定樣板、驗證腳本與示例，不依賴原作者的 ChatGPT 對話或私人帳號。

## 第一次使用

1. 使用 GitHub 的 **Use this template** 建立自己的倉庫，或下載 ZIP 並解壓縮。請保留 `.agents`、`.github` 等目錄。
2. 用能讀取該目錄的 AI Agent 開啟專案。若工具不自動讀取 `AGENTS.md`，把它加入對話或明確要求讀取。
3. 對 Agent 說：「請先閱讀 AGENTS.md，初始化這個專案並檢查可用功能；不要連線或修改外部服務。」
4. Agent 可執行以下指令；也可手動複製 `config/project.example.json` 為 `config/project.local.json`。

```sh
python scripts/bootstrap.py
python scripts/doctor.py
```

`python` 需 Python 3.10 以上；部分 macOS／Linux 環境改用 `python3`。腳本僅使用標準函式庫。
不使用 Python 仍能請 Agent 直接讀取流程及處理文件；自動檢查須標示未執行。

5. 在本機設定填入您自己的課程與輸出位置，然後用自然語言交辦。
課程設定範例在 [設定說明](docs/SETUP.md)，所有工作入口在 [流程索引](docs/WORKFLOWS.md)。

## 可以如何交辦

- 「先列出目前可執行的工作程序，以及需要額外工具的部分。」
- 「依 examples/demo-source.md 製作一個 KP 的講義及 HTML 投影片，先不發布。」
- 「把這份簡報的每個核心觀念加入四格漫畫，保留原頁，完成後檢查沒有重疊。」
- 「對照我上週的建議，查核指定週報與實驗證據。」
- 「整理這些邀請信的正式截止日，列出需要我處理的事項。」

## 下載後有哪些能力

能閱讀與撰寫檔案的 Agent 可使用本機來源完成盤點、講義、HTML 教材、草稿與紀錄。
GitHub、信箱、雲端硬碟、行事曆、Notion、瀏覽器及生圖能力取決於您所使用的 Agent 與自己的授權；下載倉庫不會自動取得這些服務。
本範本不包含簡報島專有格式的完整 schema 或 LabTube 匯入契約；指定這兩種格式時須提供該版本的規格／可用範例，再依技能驗證，不編造格式。
未提供生圖工具時只交付漫畫分鏡與提示詞，不把提示詞稱為已生成漫畫。
參見 [能力與降級方式](docs/CAPABILITIES.md)。

## 核心檔案

| 路徑 | 用途 |
|---|---|
| [AGENTS.md](AGENTS.md) | Agent 啟動、路由、共同規範 |
| [docs/WORKFLOWS.md](docs/WORKFLOWS.md) | 人可閱讀的 13 項程序 |
| [config/workflows.json](config/workflows.json) | Agent／腳本可讀取的流程清單 |
| `.agents/skills/*/SKILL.md` | 每項任務的輸入、步驟、輸出與驗收 |
| [docs/QUALITY.md](docs/QUALITY.md) | 來源、公式、版面與互動稽核 |
| [docs/PUBLISHING.md](docs/PUBLISHING.md) | 建立 GitHub 範本及發布前確認 |
| [templates/task-record.md](templates/task-record.md) | 任務與交接紀錄 |

## 驗證與維護

```sh
python scripts/doctor.py --template
python -m unittest discover -s tests -v
```

結構檢查只確認檔案、連結、設定與流程一致性，不代表信箱已連線、所有教材正確或已通過目視檢查。
新增程序時同步技能、JSON 索引、流程說明與測試。不要把原作者私人資料或第三方閉源技能整包複製進來。
[來源與重用範圍](docs/PROVENANCE.md) 說明本版本的界線。

GitHub 官方說明：[建立範本倉庫](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-template-repository)、[從範本建立倉庫](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template)。
本地檔案完成不等於 GitHub 的 Template repository 已啟用；後者需倉庫管理者設定及核實。

本版本採 [MIT 授權](LICENSE)。另附 [Private 範本建立腳本](scripts/publish-private-template.ps1)，使用方式見發布文件；預設只預覽，必須明確加上 `-Execute` 才執行。
