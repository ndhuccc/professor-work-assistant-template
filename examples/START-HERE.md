# 第一次任務示例

把以下文字交給 Agent：

> 請閱讀 AGENTS.md，使用 examples/demo-source.md，依 W02、W03 產出一個 KP 的 Markdown 講義與 HTML 投影片。程度為初學者，公式完整、附一個實算例子。產出放 workspace/public/demo/，依 QUALITY.md 驗證，沒有瀏覽器的項目標未執行，不推送或連線外部服務。

若要求原課程預設格式，預期檔案是 `kp01-lecture.md`、`kp01-slides.jbd.json`、`coverage.md`、`validation.md`。只有當次明確要求 HTML 才依 HTML 規格製作，不能把 HTML 假稱為簡報島檔。
接著可以要求：「依 W04 提取核心概念並規劃漫畫；若無生圖工具，先交付分鏡與提示詞，不宣稱已生成圖片。」
本示例不需要 GitHub 帳號、真實學生資料或外部課程設定。

## 原工具的可重現測試

```sh
python scripts/create_course.py --id DEMO --name Demo --demo
python examples/jbd_demo.py --course-root workspace/courses/DEMO --out workspace/demo/draft.jbd.json
python workspace/courses/DEMO/scripts/check_slides.py workspace/demo/draft.jbd.json
```

DEMO 已存在時請換一個新的 ID，不刪除或覆寫既有工作。完整測試命令為 `python -m unittest discover -s tests -v`；會使用合成資料，不連正式服務。
