# JianBauDau 簡報檔案格式說明書（給 AI Agent 讀的版本）

## 這份文件是給誰、做什麼用的

這份文件的讀者是 **AI agent**，不是人類使用者。目的是讓 agent 在讀完一段使用者提供的文本內容之後，能夠**獨立產生一份符合 JianBauDau 格式的 JSON 檔案**，這份 JSON 檔案可以直接被 App 的「Open」功能匯入，變成一張或多張可導覽、可播放的簡報投影片。

這份文件只講**檔案格式本身**（schema、欄位、型別、合法值、驗證規則）。至於「怎麼把內容設計得好看、好懂、有結構」，請一併參考同目錄下的 [`PRESENTATION_DESIGN_GUIDE.md`](PRESENTATION_DESIGN_GUIDE.md)——那份文件講的是設計原則（一個 Frame = 一個知識單元、巢狀深度、Connector 表達關聯、配色對比、版面多樣性等），兩份文件搭配使用。也可以直接參考 [`examples/photosynthesis-knowledge-units.json`](examples/photosynthesis-knowledge-units.json) 這個完整範例檔案。

**產生檔案後，agent 必須自我檢查**本文件「驗證規則與常見錯誤」一節列出的每一條規則，確認輸出的 JSON 不會被 App 的驗證器拒絕。

---

## 核心心智模型：這是什麼樣的資料結構

JianBauDau 不是「一張一張投影片」的線性模型，而是：

1. 有很多個 **Scene（場景）**，每個 Scene 是一塊獨立、無邊界的 2D 畫布，有自己的座標系統。
2. 每個 Scene 裡放很多個 **Node（物件節點）**：文字、圖形、圖片、影片、嵌入內容、群組、連接線，以及一種特殊節點——**Frame（畫框）**。
3. 一個 Frame 節點本身長得像畫布上的一個矩形物件，但它同時**指向另一個獨立的 Scene**（`frame.childSceneId`）。「進入」一個 Frame，就是把攝影機從目前的 Scene 換到那個子 Scene，形成**無限巢狀**的空間（子 Scene 裡還可以再放 Frame，指向孫 Scene，沒有深度限制）。
4. 簡報的「播放順序」是一份全域、扁平的 **Step（鏡頭步驟）陣列**——不管內容散落在多深的巢狀 Scene 裡，Step 陣列用 `order` 欄位決定攝影機依序移動、縮放、進入哪個 Frame、揭示哪些物件。**Step 是唯一決定「投影片先後順序」的東西**，Scene/Node 本身沒有順序概念。

一句話總結給 agent：**先把文本內容拆成一群「知識單元」，每個知識單元變成一個 Scene（通常透過一個 Frame 節點掛在上層 Scene 上），單元內部的文字/圖形變成該 Scene 裡的 Node；接著寫一串 Step，決定攝影機依序帶觀眾看過這些內容。**

---

## 檔案頂層結構（PresentationDocumentV3）

```jsonc
{
  "schemaVersion": 3,
  "rootSceneId": "scene-root",
  "scenes": { "<sceneId>": SceneRecord, ... },
  "nodes": { "<nodeId>": SceneNode, ... },
  "steps": [ CameraStepV3, ... ],
  "metadata": {
    "title": "簡報標題",
    "createdAt": "2026-09-26T00:00:00.000Z",
    "updatedAt": "2026-09-26T00:00:00.000Z",
    "aspectRatio": "16:9"
  }
}
```

- `schemaVersion` 必須是數字 `3`（本文件只講 v3 格式；v2 是舊格式，App 會自動把 v2 遷移成 v3，但 agent 不需要輸出 v2）。
- `rootSceneId`：字串，必須等於 `scenes` 裡某一個 key（通常固定用 `"scene-root"`）。整份文件一定要有一個根 Scene，觀眾一開始看到的就是它。
- `scenes` / `nodes`：以 id 為 key 的物件（不是陣列）。**每個 id 在整份文件裡必須是全域唯一的字串**（Scene id 和 Node id 各自的命名空間也不能互相撞名，建議都用有語意的 kebab-case，例如 `frame-input`、`scene-input`、`input-title`）。
- `steps`：陣列，見下方「Step」一節。
- `metadata.aspectRatio`：只能是 `"16:9"` 或 `"4:3"`，決定 Present 模式播放時的畫面比例。**沒有特別理由就用 `"16:9"`**。
- `metadata.createdAt` / `updatedAt`：ISO 8601 時間字串，agent 可以直接填當下時間，格式錯誤不會擋掉檔案匯入（有預設值），但建議填正確格式。

---

## Scene（場景）— SceneRecord

```jsonc
{
  "id": "scene-input",
  "name": "輸入單元",
  "parentFrameId": "frame-input",
  "nodeIds": ["input-title", "input-sunlight-icon", "..."],
  "camera": { "x": 240, "y": 240, "zoom": 0.95, "rotation": 0 }
}
```

| 欄位 | 型別 | 說明 |
|---|---|---|
| `id` | string | 必須跟這個 Scene 在 `scenes` 物件裡的 key 完全一致。 |
| `name` | string | 給人看的名稱，隨意填，不影響播放。 |
| `parentFrameId` | string \| null | 如果這個 Scene 是某個 Frame 節點的子場景，填那個 Frame 節點的 `id`；根場景（`rootSceneId` 指到的那個）**必須是 `null`**。 |
| `nodeIds` | string[] | 這個 Scene 底下、直屬於它的 Node id 清單。**這個清單必須跟 `nodes` 裡實際 `sceneId === 這個 scene.id` 的節點完全對應**（見下方驗證規則）——加了節點記得同時把它的 id 塞進對應 Scene 的 `nodeIds`，兩邊要一致。 |
| `camera` | Camera | 這個 Scene 被獨立檢視時的預設鏡頭（例如剛進入這個 Frame 時的畫面）。`zoom` 必須 > 0。 |

**Frame 與子 Scene 是一一對應、雙向連結的一組物件：**
- Scene A 裡有一個 `type: "frame"` 的節點 F，`F.frame.childSceneId = "scene-B"`。
- `scenes["scene-B"].parentFrameId` 必須等於 `F.id`。
- 這兩件事任一邊漏掉、對不上，App 的驗證器都會回報錯誤（`frame child scene missing` / `child scene parent mismatch`）。**每建立一個 Frame 節點，就要同時建立它指向的那個 Scene，兩邊互相對好 id。**

---

## 座標系統（每個 Scene 各自獨立）

- 每個 Scene 都有自己的、**無邊界、任意單位**的 2D 座標系統，跟其他 Scene 完全無關（子 Scene 不是「父 Scene 座標的一部分」，而是全新的一塊畫布）。
- 座標單位沒有強制的物理意義，習慣上可以把 1 單位想成大約 1px，一個 16:9 的「一屏內容」大約落在寬 1200～1300、高 700～800 這個數量級（可參考範例檔案：一個 Frame 常見尺寸是幾百 x 幾百，內部子場景的內容也差不多這個量級）。**不需要精算，只要維持同一個 Scene 內物件之間的相對大小、間距合理即可。**
- `y` 軸方向：正值向下（跟一般螢幕座標系一致，不是數學座標系）。
- 一個 Scene 裡的物件座標**沒有畫布邊界限制**，可以是負數，可以超出「看得到的範圍」——因為攝影機（Camera / Step 的 `scene-point`）才決定最後畫面看到哪一塊區域，物件本身怎麼擺都合法。

---

## Node（物件節點）— SceneNode

所有節點共用的欄位：

```jsonc
{
  "id": "input-title",
  "type": "text",
  "name": "輸入單元標題",
  "sceneId": "scene-input",
  "transform": { "x": 40, "y": 30, "scaleX": 1, "scaleY": 1, "rotation": 0 },
  "width": 420,
  "height": 80,
  "zIndex": 2,
  "locked": false,
  "style": { "...": "見下方 NodeStyle" },
  "text": "顯示的文字內容（見下方文字內容格式）",
  "initiallyHidden": false
}
```

| 欄位 | 型別 | 說明 |
|---|---|---|
| `id` | string | 全域唯一。 |
| `type` | `"text" \| "shape" \| "image" \| "video" \| "embed" \| "frame" \| "group" \| "connector"` | 決定這個節點是什麼、要不要填對應的內容欄位（`image` / `video` / `embed` / `frame` / `connector`，見下方各節）。 |
| `name` | string | 給人看的名稱，不影響播放。 |
| `sceneId` | string | **必須**等於這個節點所屬 Scene 的 `id`，並且這個 id 要出現在該 Scene 的 `nodeIds` 裡（雙向一致）。 |
| `transform.x` / `transform.y` | number | 節點左上角在該 Scene 座標系裡的位置（不是中心點）。 |
| `transform.scaleX` / `transform.scaleY` | number | 額外縮放倍率，預設 `1`，不能是 `0`。一般情況下直接固定填 `1`，用 `width`/`height` 決定實際尺寸即可，不需要用縮放。 |
| `transform.rotation` | number | 旋轉角度，**單位是弧度**，不是角度（例如轉 90 度要填 `Math.PI/2 ≈ 1.5708`）。沒有旋轉需求就填 `0`。 |
| `width` / `height` | number | 節點的寬高，**必須 > 0**。 |
| `zIndex` | number | 疊放順序，數字越大越上層。同一個 Scene 裡的節點建議給遞增的整數（0, 1, 2, ...），數字本身沒有絕對意義，只用來比大小。 |
| `locked` | boolean | 是否鎖定禁止編輯，agent 產生內容時填 `false` 即可。 |
| `style` | NodeStyle | 見下方。 |
| `text` | string | 這個節點顯示的文字（`text`／`shape` 節點會實際渲染文字內容；其他型別節點這個欄位可以填一個辨識用的名稱字串，不會顯示出來，但仍須是字串，不能省略）。 |
| `initiallyHidden` | boolean（可省略） | 若為 `true`，這個節點在該 Scene 一開始不顯示，要靠某個 Step 的 `reveal.enter` 把它揭示出來才會出現（做「逐項揭示」效果時使用，見下方 Step 一節）。 |

### NodeStyle（`style` 欄位）

```jsonc
{
  "fill": "#6a9bcc",
  "stroke": "#a9c5e3",
  "textColor": "#171918",
  "fontSize": 17,
  "radius": 16,
  "fontFamily": "Avenir Next",
  "fontWeight": 400,
  "fontStyle": "normal",
  "textAlign": "left",
  "lineHeight": 1.13,
  "letterSpacing": 0,
  "borderStyle": "solid",
  "borderWidth": 2
}
```

| 欄位 | 型別 / 範圍 | 說明 |
|---|---|---|
| `fill` | CSS 顏色字串（含 `transparent`） | 背景／填色。`text` 節點通常用 `"transparent"`。 |
| `stroke` | CSS 顏色字串 | 邊框顏色。 |
| `textColor` | CSS 顏色字串 | 文字顏色。**務必實際核對跟 `fill` 的對比度**（見下方「配色與可讀性」）。 |
| `fontSize` | number | px。 |
| `radius` | number ≥ 0 | 圓角半徑（px）。`frame` 節點常用較大值（如 20）。 |
| `fontFamily` | string（可省略） | 預設 `"Avenir Next"`，沒有特殊需求不用改。 |
| `fontWeight` | number，會被夾在 300～800 之間 | 400 = 正常，700 = 粗體。`**text**` markdown 語法也能達到粗體效果（見下方）。 |
| `fontStyle` | `"normal" \| "italic"` | |
| `textAlign` | `"left" \| "center" \| "right"` | `shape` 節點預設置中，`text` 節點預設靠左。 |
| `lineHeight` | number，夾在 0.8～3 | |
| `letterSpacing` | number，夾在 -2～12 | px。 |
| `borderStyle` | `"solid" \| "dashed" \| "dotted" \| "double"`（可省略） | |
| `borderWidth` | number ≥ 0（可省略） | px。 |

**⚠️ Connector 的 `textColor` 是唯一的例外**：Connector 標籤永遠畫在一張接近純白（`rgba(255,255,255,0.94)`）的卡片上，跟畫布深色背景無關，所以 Connector 節點的 `style.textColor` **必須用深色**（例如 `#1c1712`），跟其他節點「深色背景配淺色文字」的慣例正好相反。這是最容易被忽略、也最容易做出「看不見的文字」的地方。

### 各種節點型別要另外填的內容欄位

**`type: "text"` / `type: "shape"`**
- 純文字或幾何圖形卡片。`text` 欄位放要顯示的內容（支援 Markdown，見下一節）。
- `shape` 節點另外需要 `shapeKind`：`"rectangle" | "ellipse" | "triangle" | "diamond" | "pentagon" | "star" | "arrow"`。
- **非矩形形狀（`ellipse`／`triangle`／`diamond`／`pentagon`／`star`／`arrow`）裡不要放文字**——文字是置中的矩形範圍，塞進尖角形狀會被截斷。用這些形狀當語意化圖示（例如 `star` 代表能量、`ellipse` 代表液體、`diamond` 代表分子、`arrow` 代表流動），文字另外用一個獨立的 `text` 節點放在旁邊。

**`type: "image"`**
```jsonc
"image": { "src": "https://example.com/photo.jpg", "alt": "描述文字", "fit": "contain" }
```
- `src` **必須是一般的 `http://` 或 `https://` 網址**（agent 沒辦法上傳二進位檔案到伺服器，不要使用 `asset:` 開頭的內部參照，也不要塞 base64 data URI——雖然技術上不會被擋，但檔案會變得非常大）。缺少有效圖片網址時，寧可用 `shape` 或 `text` 節點代替，不要留一個會顯示破圖的 `image` 節點（驗證器會擋掉沒有合法 `src` 的 `image` 節點）。
- `fit`：`"contain" | "cover" | "fill"`，預設 `"contain"`。

**`type: "video"`**
```jsonc
"video": { "src": "https://example.com/clip.mp4", "alt": "描述文字", "fit": "contain", "controls": true, "muted": false, "loop": false }
```
- `src` 規則同 `image`。

**`type: "embed"`**（嵌入 YouTube / Vimeo / 其他網頁）
```jsonc
"embed": { "provider": "youtube", "url": "https://www.youtube.com/watch?v=XXXXXXXXXXX", "title": "影片標題", "allowFullscreen": true }
```
- `provider`：`"youtube" | "vimeo" | "custom"`。**只要給一般的 YouTube 分享連結或 Vimeo 連結，`provider` 填對應值即可**（`youtube.com/watch?v=`、`youtu.be/`、`vimeo.com/數字ID` 都可以）。其他任意網頁用 `provider: "custom"`，`url` 直接填該網頁的 `https://` 網址。
- 只接受 `https://` 開頭的網址。

**`type: "frame"`**（畫框，指向子 Scene）
```jsonc
"frame": {
  "childSceneId": "scene-input",
  "previewMode": "live",
  "padding": 18,
  "clip": true
}
```
- `childSceneId`：**必須**對應到 `scenes` 裡實際存在、且 `parentFrameId` 指回這個 Frame 節點 id 的一個 Scene（見上方「Scene」一節的雙向對應規則）。
- `previewMode`：`"empty" | "snapshot" | "live"`。一般建議用 `"live"`（畫框裡即時顯示子場景內容的縮圖預覽）。
- `padding`：子場景內容跟畫框邊緣的留白（px），預設 18。
- `clip`：是否裁切超出畫框的內容，一般填 `true`。
- 選填的標題文字樣式：`titleFontSize`（10～120，預設 32）、`titleColor`、`titleFontFamily`、`titleFontWeight`（300～800）、`titleFontStyle`（`"normal"|"italic"`）——這些控制畫框上方標題列（顯示 `text` 欄位內容）的外觀。
- **課程簡報不要使用上述標題樣式欄位,也不要給 Frame 加有色填色**:標題列的背景色不可控,自訂顏色造成過低對比(實際發生過)。標準寫法見 `SKILL.md` §4D。
- **Frame 節點的 `text` 欄位就是顯示在畫框標題列上的文字**，通常填這個知識單元的標題（例如 `"INPUT"`、`"光合作用過程"`）。

**`type: "group"`**（群組，把多個節點視覺上綁在一起）
```jsonc
"children": ["node-id-1", "node-id-2"]
```
- `children` 是被群組的節點 id 陣列。agent 產生內容時**不建議主動使用 group**（群組主要是給人在編輯器裡手動操作用的），直接把節點各自放在 Scene 裡即可，除非有明確理由需要把某幾個節點綁成一個可整體移動的單位。

**`type: "connector"`**（連接線，表示兩個節點之間的關聯）
```jsonc
"connector": {
  "sourceNodeId": "frame-input",
  "sourceHook": 4,
  "targetNodeId": "frame-process",
  "targetHook": 12,
  "curve": true,
  "direction": "forward",
  "arrowSize": "medium",
  "label": { "text": "提供原料", "t": 0.5, "offset": "above" }
}
```
- `sourceNodeId` / `targetNodeId`：**必須是同一個 Scene 裡的其他節點 id**（不能是 Connector 自己，也不能跨 Scene，也不能連到另一條 Connector）。
- `sourceHook` / `targetHook`：整數 `0`～`15`，代表節點四周 16 個等角度掛點（`0` = 正上方，順時針排列，`4` ≈ 正右方，`8` ≈ 正下方，`12` ≈ 正左方，其餘依此類推）。**Connector 節點本身也要放進該 Scene 的 `nodeIds`**，並給它自己的 `transform`/`width`/`height`（隨意填、不影響連線視覺，例如 `x:0, y:0, width:10, height:10`）。
- `curve`：是否用曲線而非直線連接，可省略。
- `direction`：`"none" | "forward" | "backward" | "both"`，決定箭頭方向，可省略。
- `arrowSize`：`"small" | "medium" | "large"`，可省略。
- `waypoints`（可省略）：`{x,y}[]`，手動指定連接線經過的中繼點。
- `label`（可省略）：`{ text, t, offset }`——`t` 是 0～1，代表標籤沿連線的相對位置（0.5 = 中點）；`offset` 是 `"on" | "above" | "below"`。**`label.text` 的 `style.textColor` 一律要用深色**（見上方 NodeStyle 一節的說明）。
- **線與箭頭的顏色使用 `style.stroke`**,不是 `textColor` 或 `fill`;必須與畫布有足夠對比,不可用 `transparent` 或零透明度。深色畫布可用 `stroke: "#6a9fd6"`、`borderWidth: 3`。`textColor` 只控制標籤文字,仍用深色。節點存在或格式檢查通過不代表連線可見,必須在實際播放器確認線與箭頭。

---

## 文字內容格式（`text` 欄位支援的語法）

`text` / `shape` 節點的 `text` 欄位、Connector 的 `label.text`，都支援標準 **Markdown** 語法（用 `markdown-to-jsx` 渲染，關閉了原始 HTML）：

- `**粗體**`、`*斜體*`、`***粗斜體***`
- 換行：字串裡直接放 `\n`
- 標題（`# ` `## ` ...）、清單（`- ` `1. `）、引言（`> `）等區塊語法也會被解析成對應的排版——但**在小尺寸的卡片節點裡，建議只用粗體/斜體/換行做簡單強調，不要用完整的標題/清單巢狀結構**，避免排版跑掉。
- 支援 **LaTeX 數學公式**：行內用 `$公式$`，區塊用單獨一行的 `$$` 包住公式（例如 `$$\nE = mc^2\n$$`），會用 KaTeX 渲染。

字面上要顯示 `*`、`#`、`` ` `` 等 Markdown 特殊字元時，前面加反斜線跳脫，例如 `\*` 顯示成 `*`。

---

## Step（鏡頭步驟）— CameraStepV3

`steps` 是一個**全域扁平陣列**，決定簡報播放（Present／Preview 模式）時攝影機依序怎麼移動。

```jsonc
{
  "id": "step-open-input",
  "order": 0,
  "label": "輸入單元",
  "target": { "kind": "scene-point", "sceneId": "scene-root", "point": { "x": 300, "y": 360 }, "zoom": 2.667, "referenceViewport": { "width": 1280, "height": 720 } },
  "durationMs": 900,
  "holdMs": 420,
  "easing": "smooth",
  "reveal": { "timing": "after-camera", "enter": [ { "nodeId": "input-title", "effect": "fade", "delayMs": 0, "durationMs": 400 } ], "exitNodeIds": [] },
  "speakerNotes": "給講者看的備註，觀眾看不到"
}
```

| 欄位 | 型別 / 範圍 | 說明 |
|---|---|---|
| `id` | string，非空 | 全域唯一。 |
| `order` | number | **決定播放順序**，建議直接用陣列索引 `0, 1, 2, ...`（陣列本身的排列順序不重要，真正生效的是這個數字，重複或跳號雖然不會擋掉匯入，但會讓順序難以預期，務必保持與陣列順序一致的遞增整數）。 |
| `label` | string，≤ 200 字 | 顯示在時間軸卡片上的名稱。 |
| `target` | CameraTarget | 見下方四種類型。 |
| `durationMs` | number，180～10000 | 攝影機移動到這一步的動畫時間（毫秒）。一般內容用 800～1200。 |
| `holdMs` | number，0～30000 | 到達後停留多久才能進到下一步（手動點「下一步」時這個值只是可以提前跳過的下限）。一般用 400～800。 |
| `easing` | `"linear" \| "easeInOut" \| "smooth"` | 動畫緩動函數，一般用 `"smooth"`。 |
| `fallbackCamera`（可省略） | Camera | `target` 解析失敗時的備援鏡頭，agent 產生內容時通常不需要填。 |
| `reveal`（可省略） | StepReveal | 逐項揭示效果，見下方。 |
| `speakerNotes`（可省略） | string，≤ 20000 字 | 純講者備註，不會顯示給觀眾。 |

### `target`（CameraTarget）四種類型

1. **`scene-overview`** — 讓攝影機縮放到「剛好framing 這整個 Scene 目前所有內容」的範圍。
   ```jsonc
   { "kind": "scene-overview", "sceneId": "scene-root" }
   ```
   會在 Scene mode 畫出一個涵蓋整個 Scene 的 reticle。**含 Frame 的 Scene 不要用它**（不論是開場總覽或「返回總覽」）：含 Frame 的 Scene 必須「每個 Frame 一個 step」，讓時間軸 step 與畫布 reticle 一對一；多出的 `scene-overview` 只會多一個停點，並疊出重複的整場景 reticle。沒有 Frame 的單一 Scene（例如最小範例）可以用。

2. **`focus-node`** — 攝影機縮放到剛好框住某一個節點。
   ```jsonc
   { "kind": "focus-node", "sceneId": "scene-input", "nodeId": "input-title" }
   ```
   `nodeId` 必須是同一個 `sceneId` 裡實際存在的節點。

3. **`enter-frame`** — 把攝影機從目前的 Scene **換到**某個 Frame 節點指向的子 Scene。**課程投影片（view-from-text 技能）不使用它**：`enter-frame` 在 Scene mode 沒有 reticle，時間軸卡片就無法與畫布 reticle 一對一。要「進入」一個 Frame，改在父 Scene 寫一個「以該 Frame 為中心的 `scene-point`」；播放時走到這個 step 會自動深度優先進入該 Frame 的子 Scene，播完再退回並顯示 Finished。
   ```jsonc
   { "kind": "enter-frame", "sceneId": "scene-root", "frameId": "frame-input" }
   ```
   `frameId` 必須是 `sceneId` 這個 Scene 裡、`type === "frame"` 的節點 id。

4. **`scene-point`** — 攝影機移到 Scene 座標系裡指定的一個點、指定的縮放倍率。**這是 agent 手動精算構圖時最常用、最直接的類型**，因為前三種都是「自動算出來」的框景，只有這種能精確控制畫面裡看到什麼。
   ```jsonc
   { "kind": "scene-point", "sceneId": "scene-input", "point": { "x": 640, "y": 310 }, "zoom": 0.878, "referenceViewport": { "width": 1280, "height": 720 } }
   ```
   - `point`：這個 Scene 座標系裡，畫面**中心點**的座標。
   - `referenceViewport`：`{ "width", "height" }`，**一律要寫**，16:9 為 `{1280, 720}`，4:3 為 `{960, 720}`（等於頁面參考尺寸）。它決定 `zoom` 以哪個畫面大小為基準。
   - `zoom`：**相對 `referenceViewport` 的倍率**，必須 > 0。`zoom: 1` 表示剛好用 `referenceViewport` 這麼大的範圍填滿整個畫面，播放視窗再大或再小都會等比縮放，所以構圖在任何視窗下一致。數字越大代表放得越大（越靠近）。
   - **不可以省略 `referenceViewport`。** 省略時 `zoom` 會變成「一個場景單位 = 一個螢幕像素」，與視窗大小無關：在 1920×1080 的播放器裡，一頁只佔約六成寬並露出相鄰頁，而編輯器 Scene mode 的 reticle 仍是按 1280×720 畫的，兩邊看到的範圍不一致。（這是舊版文件曾建議「省略即可」所造成的問題。）
   - **進入 Frame 後，畫面最上方會蓋一條 Frame 標題列**（約 56 px，不隨視窗縮放）。鏡頭要多涵蓋頁面上方 100 單位的空白，讓標題列蓋在空白上，不要蓋到頁面內容：`zoom = H / (H + 100)`、`point.x = 頁面左上 x + W/2`、`point.y = 頁面左上 y + H/2 − 50`（`W×H` 為頁面參考尺寸）。完整公式、頁面間隔與程式碼見設計準則「頁面排列與鏡頭公式」。

### `reveal`（逐項揭示，可省略）

讓一個 Step 到達目的地後，**依序淡入/縮放顯示**目的地 Scene 裡原本隱藏的節點，或讓某些節點退場。

```jsonc
{
  "timing": "after-camera",
  "enter": [
    { "nodeId": "point-1", "effect": "fade", "delayMs": 0, "durationMs": 400 },
    { "nodeId": "point-2", "effect": "fade", "delayMs": 300, "durationMs": 400 }
  ],
  "exitNodeIds": []
}
```

| 欄位 | 說明 |
|---|---|
| `timing` | `"after-camera"`（鏡頭到位後才開始揭示，較常用）或 `"with-camera"`（鏡頭移動的同時就開始揭示）。 |
| `enter[].nodeId` | 要揭示的節點 id。**這個節點必須跟這個 Step 的 `target.sceneId` 屬於同一個 Scene**——不能在 `enter-frame`（換場景）的 Step 上直接列出子 Scene 裡的節點，要另外用一個 `target.sceneId` 是該子 Scene 的 Step（例如緊接著的 `scene-overview`）來搭配 `reveal`。 |
| `enter[].effect` | `"none" \| "fade" \| "scale"`。 |
| `enter[].delayMs` | 0～10000，這一項相對這個 Step 揭示階段開始的延遲，可以用不同的 `delayMs` 做出「一個一個跳出來」的效果。 |
| `enter[].durationMs` | 0～5000。 |
| `exitNodeIds` | 要退場（隱藏）的節點 id 陣列，同樣必須跟這個 Step 的 `target.sceneId` 同一個 Scene。 |

**要讓節點一開始是隱藏、靠 `reveal.enter` 才出現的**，記得在該節點上設定 `"initiallyHidden": true`。

---

## 配色與可讀性（務必實際核對，不要憑感覺）

- 深色背景（JianBauDau 畫布預設深色）配淺色文字是一般節點的慣例；**唯獨 Connector 標籤背景接近純白，`textColor` 必須用深色**（見上方兩處提醒）。
- 有能力計算的話，用 WCAG 相對亮度公式驗證每一組 `fill`（或該節點實際可見的背景色）與 `textColor` 的對比度 ≥ 4.5:1，不要用肉眼猜。
- 避免整份文件所有卡片都用同一種 `fill`/`shapeKind`/排版——不同知識單元之間刻意做出視覺差異（見 `PRESENTATION_DESIGN_GUIDE.md`）。

---

## 驗證規則與常見錯誤（產生檔案後務必逐條自我檢查）

App 匯入檔案時會執行結構驗證，以下任何一條不成立，整份檔案會被**整批拒絕匯入**（不是忽略單一節點）：

1. `schemaVersion` 必須是 `3`；`rootSceneId` 對應的 Scene 必須存在。
2. 每個 Scene 的 `camera.zoom` 必須是有限數字且 `> 0`；`camera.x`/`y`/`rotation` 必須是有限數字。
3. 每個 Scene 的 `nodeIds` 列出的每一個 id，必須在 `nodes` 裡實際存在，且該節點的 `sceneId` 等於這個 Scene 的 `id`（**雙向一致**，這是最容易犯的錯）。
4. 一個節點 **只能屬於一個 Scene**（不能同一個節點 id 出現在兩個 Scene 的 `nodeIds` 裡），也 **不能是孤兒**（存在於 `nodes` 裡，但沒有被任何 Scene 的 `nodeIds` 引用到）。
5. 每個節點的 `transform.x/y/scaleX/scaleY/rotation`、`width`、`height` 都必須是有限數字；`width`/`height` 必須 `> 0`；`scaleX`/`scaleY` 不能是 `0`。
6. `type: "frame"` 的節點必須有合法的 `frame` 內容，且 `frame.childSceneId` 指向的 Scene 必須存在、該 Scene 的 `parentFrameId` 必須等於這個 Frame 節點的 `id`。
7. `type: "image"` 必須有非空的 `image.src`；`type: "video"` 必須有非空的 `video.src`；`type: "embed"` 必須有合法（已正規化）的 `embed.url`。
8. `type: "connector"` 必須有合法的 `connector` 內容：`sourceNodeId`/`targetNodeId` 都存在、都跟這條 Connector 同一個 Scene、都不是 Connector 自己、彼此不相同；`sourceHook`/`targetHook` 都是 0～15 的整數。
9. Scene 之間透過 `parentFrameId` 往上追溯，**不能形成循環**（不會出現「A 的父層最終繞回 A 自己」）。
10. 每個 Step：`id` 非空字串、`label` ≤ 200 字、`durationMs` 落在 180～10000、`holdMs` 落在 0～30000、`easing` 是三選一合法值、`speakerNotes`（若有）≤ 20000 字。
11. 每個 Step 的 `target.sceneId` 必須對應到實際存在的 Scene；`target.kind` 必須是四選一合法值。
12. `scene-point` 的 `point.x`/`point.y`/`zoom` 必須是有限數字且 `zoom > 0`。
13. `focus-node` 的 `nodeId` 必須存在、且該節點的 `sceneId` 等於這個 Step 的 `target.sceneId`。
14. `enter-frame` 的 `frameId` 必須存在、`type` 是 `"frame"`、且該節點的 `sceneId` 等於這個 Step 的 `target.sceneId`。
15. `reveal.enter`/`reveal.exitNodeIds` 裡列出的每一個節點，都必須跟這個 Step 的 `target.sceneId` 屬於同一個 Scene（見上方 Step 一節的說明）。

除了上面這些「會被拒絕」的硬規則之外，還有幾個**不會報錯、但會讓畫面明顯出錯**的地方，agent 產生內容時要主動避免：

- Connector 的 `style.textColor` 用了淺色 → 文字在近白底卡片上幾乎看不見（見上方提醒）。
- 非矩形 `shapeKind`（`star`/`diamond`/... ）裡塞了長文字 → 文字被形狀邊緣截斷。
- `scene-point` 的 `zoom` 抓太大或太小、`point` 沒對準內容中心 → Present 模式畫面留白過多或裁到內容一部分（構圖時盡量讓這一步要呈現的內容貼齊編輯器裡的紅色瞄準框）。
- `scene-point` **沒有 `referenceViewport`** → `zoom` 不隨播放視窗縮放：視窗比 1280×720 大時，頁面只佔一部分並露出相鄰頁；在編輯器 Scene mode 與播放時看到的範圍不一致。
- 頁面內容貼著頁頂、鏡頭沒有多留標題列的空白 → 進入 Frame 後，頁面標題被 Frame 標題列遮住或與它疊在一起。
- 含 Frame 的 Scene 用了 `enter-frame`、開場 `scene-overview`、「返回總覽」，或讓某個 Frame 沒有對應的 step／有多個 step → 時間軸 step 數與畫布 reticle 數對不上（`enter-frame` 沒有 reticle；`scene-overview` 的 reticle 蓋住整個場景）。含 Frame 的 Scene 必須「每個 Frame 恰好一個以它為中心的 `scene-point` step」，播放時會自動深度優先、播完退回該 Frame 並顯示 Finished。
- Step 的 `label` 加序號（「1 …」「2 …」）→ 與時間軸卡片自動顯示的編號重複，且容易各單元不一致。
- `metadata.aspectRatio` 忘了填 → 會被視為缺省值處理成 `"16:9"`，如果你真的要 `4:3` 一定要顯式填。

---

## 給 agent 的產生流程建議（Checklist）

拿到使用者的文本後，建議照這個順序進行：

1. **拆解內容**：把文本拆成幾個獨立的「知識單元」（章節/主題/概念），評估要不要有子單元（巢狀不建議超過 3 層）。跨單元的因果/比較/流程關係另外記下來，稍後用 Connector 表達，不要塞進單一單元裡。
2. **規劃 Scene 樹**：一個根 Scene（`scene-root`），每個一級知識單元對應根 Scene 上的一個 Frame 節點 + 一個子 Scene；子單元依此類推往下巢狀。先把所有 `sceneId`/`nodeId` 命名定下來（建議語意化命名，如 `frame-<單元>`、`scene-<單元>`、`<單元>-title`）。
3. **在每個 Scene 裡放 Node**：標題文字、說明文字、圖示形狀 + 標籤、Frame（指向子單元）、Connector（單元內或同層單元間的關聯）。決定座標時讓同一個 Scene 內的物件彼此不重疊、留白合理；不同單元之間的排版盡量做出差異（橫向並列/主副配置/左右對照，見設計準則文件）。
4. **檢查配色對比**：尤其 Connector 標籤的 `textColor` 記得用深色。
5. **寫 Step 序列**：含 Frame 的 Scene（根 Scene 等）**每個 Frame 一個 step**——以該 Frame 為中心的 `scene-point`（`zoom = 1280/480`、`referenceViewport` 1280×720，剛好框住 400×200 的 Frame）；每個單元的子 Scene **每頁一個 `scene-point` step**（需要的話搭配 `reveal` 逐項揭示 + 對應節點的 `initiallyHidden: true`）。**不用 `enter-frame`、不寫開場 `scene-overview`、不寫退回上一層的 Step**（播放時自動深度優先，播完退回該 Frame 並顯示 Finished）。每個 `scene-point` 都要寫 `referenceViewport`；內容頁依公式留出標題列空白；`label` 只寫結論短句、不加序號。把所有 Step 依深度優先「Frame 1 → 單元 1 的頁面 → Frame 2 → 單元 2 的頁面 → …」串成一個扁平陣列，`order` 依序遞增。
6. **組裝成完整 JSON**：`schemaVersion: 3`、`rootSceneId`、`scenes`、`nodes`、`steps`、`metadata`。
7. **自我檢查**：逐條核對上方「驗證規則與常見錯誤」，特別是 Scene↔Node 的雙向 `nodeIds`/`sceneId` 一致性、Frame↔子 Scene 的雙向 `childSceneId`/`parentFrameId` 一致性、Connector 的節點參照與 hook 範圍、Reveal 節點與 Step 目的地同 Scene——這些是最常出錯、也最容易在自我檢查時用簡單的程式邏輯核對出來的地方。
8. 輸出最終 JSON 檔案內容（純 JSON，不要包在 Markdown code fence 之外的說明文字裡，方便使用者直接存成 `.json` 檔用「Open」匯入）。

---

## 最小可行範例（單一 Scene、單一 Step，先求「能匯入、能播放」）

```json
{
  "schemaVersion": 3,
  "rootSceneId": "scene-root",
  "scenes": {
    "scene-root": {
      "id": "scene-root",
      "name": "根畫布",
      "parentFrameId": null,
      "nodeIds": ["title-1", "body-1"],
      "camera": { "x": 400, "y": 200, "zoom": 0.6, "rotation": 0 }
    }
  },
  "nodes": {
    "title-1": {
      "id": "title-1",
      "type": "text",
      "name": "標題",
      "sceneId": "scene-root",
      "transform": { "x": 100, "y": 60, "scaleX": 1, "scaleY": 1, "rotation": 0 },
      "width": 600,
      "height": 90,
      "zIndex": 1,
      "locked": false,
      "style": { "fill": "transparent", "stroke": "transparent", "textColor": "#f5f1e9", "fontSize": 48, "radius": 0, "fontWeight": 700 },
      "text": "**主題標題**"
    },
    "body-1": {
      "id": "body-1",
      "type": "text",
      "name": "說明",
      "sceneId": "scene-root",
      "transform": { "x": 100, "y": 170, "scaleX": 1, "scaleY": 1, "rotation": 0 },
      "width": 600,
      "height": 120,
      "zIndex": 1,
      "locked": false,
      "style": { "fill": "transparent", "stroke": "transparent", "textColor": "#b7b0a5", "fontSize": 20, "radius": 0 },
      "text": "這是說明文字，可以用 *斜體* 或 **粗體** 強調重點。"
    }
  },
  "steps": [
    {
      "id": "step-1",
      "order": 0,
      "label": "開場",
      "target": { "kind": "scene-overview", "sceneId": "scene-root" },
      "durationMs": 900,
      "holdMs": 500,
      "easing": "smooth"
    }
  ],
  "metadata": {
    "title": "範例簡報",
    "createdAt": "2026-09-26T00:00:00.000Z",
    "updatedAt": "2026-09-26T00:00:00.000Z",
    "aspectRatio": "16:9"
  }
}
```

要做出多 Scene、Frame 巢狀、Connector 關聯的完整範例，直接參考 [`examples/photosynthesis-knowledge-units.json`](examples/photosynthesis-knowledge-units.json)。
