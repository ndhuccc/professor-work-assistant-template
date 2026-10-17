# OnlineQuiz：Bloom 命題與題庫匯入

此整合把教授指定的主題、文本、PDF 或教材網址，轉成命題藍圖、教師版、學生版、品質報告與 OnlineQuiz JSON。AI Agent 先讀 AGENTS.md，再載入 W14 的完整原技能與 [工作程序](../../workflows/onlinequiz-question-bank.md)。

## 包含的技能與程式

| 檔案 | 用途 |
|---|---|
| [bloom-exam-designer](../../.agents/skills/bloom-exam-designer/SKILL.md) | 原始命題正文與兩份參考文件，無須另安裝個人技能 |
| [prepare_onlinequiz_bank.py](../../scripts/prepare_onlinequiz_bank.py) | 增補包轉檔工具的適配版；已同步新版來源與 60 秒預設，僅需標準函式庫 |
| [validate_onlinequiz_bank.py](../../scripts/validate_onlinequiz_bank.py) | 執行固定版本的原 schema 與純逐題驗證碼；需 Pydantic 2 |
| `upstream/` | OnlineQuiz 原 schema、匯入程式與計分程式，附來源雜湊；不啟動服務 |
| `source-package/` | 使用者提供增補包的八個原檔，含歷史驗證報告 |

## 自然語言交辦

> OnlineQuiz：根據這份教材設計 10 題多選題，大二程度，偏重應用與分析，先給命題藍圖。

> OnlineQuiz：沿用已核准藍圖，完成教師版、無答案學生版、品質報告及待審匯入 JSON，存到我指定的私人目錄。

> OnlineQuiz：第 4 題重新設計，保留其他題目並更新品質報告及匯入檔。

## 執行腳本

以下從範本根目錄執行，檔案參數換成使用者核准且在 Git 工作樹外的私人路徑。工具不呼叫 AI，也不下載教材：AI Agent 先依技能完成命題與答案查核，再把 JSON 交給工具。

```sh
python scripts/prepare_onlinequiz_bank.py bloom-output.json --name Demo-v1 --points 1 --seconds 150 --expected-count 10 --output onlinequiz-bank.json
python scripts/validate_onlinequiz_bank.py onlinequiz-bank.json --expected-count 10
```

第一支程式拒絕覆寫輸出、錯位選項字母、無效答案及重複題幹，回報檔案 SHA-256。第二支只載入原 schema 與四個純驗證函式；ORM／資料庫寫入程式不執行。缺 Pydantic 2 時依授權安裝 requirements.txt，或標示原生格式檢查未執行；基本轉檔仍可使用。

## 真正匯入

先列實際站台 URL、題庫版本、題數、JSON SHA、配分、秒數、計分差異與影響，取得核准後透過自己的教師介面／經授權連線新增題庫，再核對 imported_count、error_count、errors 及實際題數。

推送 JSON 到 GitHub 不會寫入線上資料庫。此範本沒有自動上傳、登入或正式題庫資料；正常教師介面與站台由下載者提供。若只提供 repo 而沒有站台，完成離線成果並標「待匯入」。不修改 OnlineQuiz-v2 本身，也不開場施測。

## v0.3.1 計分與計時

快照來自 OnlineQuiz-v2@32e27e422148e32c909f26a7b6f4cc5651bba5d4：

- 未作答或逾時空白：一律 0 分。
- 單選：選答與正解完全一致得滿分，其他情況 0 分。
- 多選：先排除空白，再依 max(0, (n - 2k)/n) × 配分部分給分；n 是全部選項數，k 是誤選加漏選的總數。這與 Bloom 可選 HTML 的算法仍不同。
- 新版匯入與本範本轉檔預設為每題 60 秒；明確設定的 --seconds／default_timer_seconds 優先，例如上述命令仍為 150 秒。

四選一滿分 10 分的空白答案現在為 0 分。正式施測前另核對實際站台的部署版本；複製快照不會更新站台。source-package/ 保留原增補包及舊報告，僅供歷史追溯。
學生純題目版不得在 HTML／JavaScript 包入正解；正式教師版及含答案 JSON 放私人位置。

來源固定版本、適配及驗證範圍見 [整合報告](../../docs/ONLINEQUIZ-INTEGRATION.md)。
