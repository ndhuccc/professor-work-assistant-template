# 簡報設計準則

這份文件說明如何用 JianBauDau 的巢狀 Scene / Frame 資料模型，設計一份清楚、好導覽的簡報。搭配範例檔案 [`examples/photosynthesis-knowledge-units.json`](examples/photosynthesis-knowledge-units.json) 一起看，用「Open」把它匯入 App 就能直接操作、進入 Present 模式體驗完整效果。

## 核心原則：一個 Frame = 一個知識單元

把每一個 Frame 當作一個獨立的「知識單元」（一個主題、一個概念、一個章節）。Frame 本身在根畫布上只需要呈現這個單元的**標題**與**輪廓**；單元內部的細節，放進這個 Frame 的 child scene 裡，用 step 帶著觀眾「進入」這個 Frame 之後才逐步展開。

這樣做的好處：

- 觀眾在最外層（根畫布）看到的是整份簡報的「地圖」——幾個知識單元並列，一眼看出結構。
- 每個知識單元的細節被隔離在自己的座標空間裡，彼此不會互相干擾版面，編輯時也不用擔心誤觸其他單元的物件。
- 呼應 App 自己的導覽邏輯：播放時依 Scene/Frame 樹深度優先，先播完 Frame 內部的頁面，再退回該 Frame 的 reticle（顯示 Finished），接著播下一個，跟這個準則完全對應。

## 知識單元的結構

一個標準的知識單元，資料模型長這樣：

- 根畫布（或上一層 scene）裡有一個 `type: "frame"` 的節點，它的 `frame.childSceneId` 指向一個獨立的 scene。
- 那個獨立的 scene（`parentFrameId` 指回這個 Frame）裡放這個單元的實際內容：標題文字、說明、圖片、子項目卡片等等。
- Step 路徑上，在含 Frame 的 Scene 裡，每個 Frame 對應**恰好一個** step（以該 Frame 為中心的 `scene-point`），在 child scene 裡則每頁一個 `scene-point` step。不要寫退回上一層的 step：child scene 播完後，Present 會自動退回該 Frame 的 reticle 並顯示 Finished，再接下一個單元（見下方「Step 路徑設計建議」）。

## 遞迴巢狀：單元可以再切子單元

這個規則不必只套一層。一個知識單元內部如果本身還能再拆解，就在它的 child scene 裡再放一個（或多個）Frame，形成子單元——資料模型本身沒有深度限制，App 也沒有限制巢狀層數。範例檔案裡的「光合作用過程」單元就是這樣：它自己是一個 Frame，內部又切成「光反應」「暗反應」兩個子單元 Frame。

實務上建議：**巢狀不要超過 3 層**（單元 → 子單元 → 細節），太深的話觀眾容易迷失在導覽路徑裡，找不到自己在整體架構的哪個位置。

## 跨單元的關聯：留在外層，用 Connector 表示

單元與單元之間的比較、因果、流程關係，**不要硬塞進某一個 Frame 裡**——那樣會讓一個單元變成不只描述自己，還要負責描述跟別人的關係，模型會變得混亂。正確做法是把這類關聯留在「兩個單元共同的上一層 scene」，用 Connector 把兩個 Frame 連起來，並在 Connector 上加文字標籤說明關係（例如「提供原料」「導致」「對比」）。

範例檔案的根畫布上，「輸入 → 光合作用過程 → 輸出」的流程就是用兩條根層的 Connector 表示，而不是把「輸出是由輸入經過過程產生的」這句話寫進任何一個 Frame 裡。

## Step 路徑設計建議：時間軸 step 與畫布 reticle 一對一

**核心規則：每個 Scene 的時間軸 step 數量，必須等於該 Scene 畫布上的 reticle 數量。** 時間軸卡片與畫布上的 reticle 是同一件事的兩種顯示：卡片是第幾步，reticle 是這一步鏡頭框住的範圍。只有 `scene-point`、`focus-node`、`scene-overview` 在 Scene mode 會畫出 reticle；`enter-frame` 沒有 reticle（它的鏡頭落在子 Scene），所以**本技能不使用 `enter-frame`**。

結構如下：

1. **根 Scene（或任何含 Frame 的 Scene）：每個 Frame 恰好一個 step。** 用「以該 Frame 為中心的 `scene-point`」聚焦 Frame（`point` 取 Frame 中心，必須落在 Frame 範圍內），reticle 就框住這個 Frame。畫布上有幾個 Frame，這個 Scene 的時間軸就有幾個 step、畫布上就有幾個 reticle。**不要**在這個 Scene 加開場的 `scene-overview`（它的 reticle 會蓋住整個場景，不對應任何單元），也不要加「返回總覽」。
2. **單元的子 Scene（沒有 Frame 的內容頁）：每頁一個 `scene-point` step**，reticle 框住那一頁。需要的話搭配 `reveal` 逐項揭示（見下方）。
3. **播放順序是深度優先，由播放器自動完成**：播到某個 Frame 的 reticle → 進入它的子 Scene，依序播完所有頁 → 自動退回該 Frame 的 reticle viewport，並在畫面上顯示 **Finished**（代表這個 Frame 內的所有頁都播完了）→ 接著播下一個 Frame 的 reticle。因此不必、也不可以另外寫「退回」的 step；多寫會多出停點，也破壞一對一。
4. **`steps` 陣列是扁平的**，建議照深度優先排：Frame 1 的 step → 單元 1 的頁面 step → Frame 2 的 step → 單元 2 的頁面 step → …，`order` 依陣列索引遞增。時間軸是依 Scene 分開顯示的：根層只看到各單元入口，進入單元後才看到該單元的頁面，這就是階層。
5. **巢狀單元同理**：子單元再含 Frame 時，在那個子 Scene 裡同樣「每個 Frame 一個 step」，播放時遞迴深度優先。
6. **`label` 只寫結論短句，不加序號**：Frame 的 step 寫單元標題，內容頁的 step 寫結論短句。時間軸卡片本身就會顯示編號，label 再寫「1 …」「2 …」會重複。

**根層聚焦 Frame 的鏡頭**：16:9 預設 reticle 為 480×270，設 `zoom = 1280 / 480 ≈ 2.667`、`referenceViewport = {"width": 1280, "height": 720}`，剛好框住 400×200 的 Frame 並留一點邊。Frame 與 Frame 的間隔要夠，讓一個 reticle 不框進隔壁 Frame（例如 Frame 400 寬時，間隔至少 40）。

**`reveal` 的重要限制：** `reveal.enter`／`reveal.exit` 裡列出的節點，必須跟該 step 目的地 scene 的節點屬於同一個 scene——不能在 `enter-frame` 這種「换 scene」的 step 上直接揭示子 scene 裡的節點，要另外用一個目的地是該 child scene 的 step（例如 `scene-overview`）來搭配 `reveal`。要讓節點一開始就是隱藏狀態，記得在節點上設定 `initiallyHidden: true`。

## 構圖建議：對齊瞄準框

編輯畫面右上角的紅色虛線框（瞄準框／aiming frame）就是 Present 模式實際會顯示的範圍，比例鎖定在您選的 Presentation Ratio（預設 16:9）。捕捉每個 step 的鏡頭時，盡量讓這一步要呈現的內容**貼齊瞄準框、不要留下大片空白**，也不要讓不相關的物件跑進瞄準框裡——因為 Present 模式會把瞄準框裡的內容線性縮放填滿整個螢幕，瞄準框裡有什麼、觀眾在台上看到的就是什麼。

### 頁面排列與鏡頭公式（手算 `scene-point` 時必須照做）

**為什麼：** 手寫的 `scene-point` 如果沒有 `referenceViewport`，`zoom` 的意思就變成「一個場景單位 = 一個螢幕像素」，不會隨播放視窗縮放。在 1920×1080 的 Player 裡，一頁只佔畫面約六成寬，右邊還會露出下一頁；編輯器 Scene mode 的 reticle 又是用 1280×720 畫的，兩邊看到的範圍不一致。另外，進入 Frame 後畫面最上方會蓋一條 Frame 標題列（約 56 px，不隨視窗縮放），頁面自己的標題如果貼著頁頂，就會被標題列遮住或疊在一起。

**規則（16:9 為 1280×720，4:3 為 960×720；下面以 `W×H` 表示頁面參考尺寸）：**

1. **每個 `scene-point` 都必須寫 `referenceViewport`**，值固定為頁面參考尺寸：`{"width": W, "height": H}`。有了它，`zoom` 才是「相對頁面參考尺寸的倍率」，在任何視窗大小下構圖都一致。
2. **鏡頭要多留標題列的空間**：令 `HEADROOM = 100`（單行 Frame 標題；標題不要超過一行），一頁的左上角是 `(x0, y0)`，則
   - `zoom = H / (H + HEADROOM)`（16:9 與 4:3 都是 `0.878`）
   - `point.x = x0 + W / 2`
   - `point.y = y0 + H / 2 − HEADROOM / 2`
   也就是畫面涵蓋頁面上方多出的 100 單位空白；標題列蓋在這段空白上，頁面內容（含頁面標題）完整露在標題列下方。
3. **同一個 Scene 內的頁面橫向排列，間隔至少 160**：`pitch = W + 160`（16:9 為 1440，4:3 為 1120）。鏡頭左右各會多看到 `(W / zoom − W) / 2` 單位（16:9 約 89，4:3 約 67），間隔夠大才不會露出相鄰頁。
4. 頁面內容放在 `0 ≤ y ≤ H` 之內；頁面上方那段 100 單位的空白不要放任何節點。

```python
W, H = 1280, 720          # 4:3 → 960, 720
HEADROOM, GAP = 100, 160
ZOOM = H / (H + HEADROOM)  # 0.878
PITCH = W + GAP

def page_origin(index):             # 單元 Scene 內第 index 頁（0 起算）的左上角
    return index * PITCH, 0

def page_camera_target(scene_id, index):
    x0, y0 = page_origin(index)
    return {
        "kind": "scene-point",
        "sceneId": scene_id,
        "point": {"x": x0 + W / 2, "y": y0 + H / 2 - HEADROOM / 2},
        "zoom": ZOOM,
        "referenceViewport": {"width": W, "height": H},
    }
```

**驗證：** 在 Player 以 1280×720 與 1920×1080 各播一次，每頁都應該填滿畫面、看不到相鄰頁、頁面標題完整位於 Frame 標題列下方；兩種視窗的構圖應該相同。

## 視覺呈現：避免機械化、確保對比清楚

光是遵守以上的結構規則，內容還是可能長得很「制式」——每個知識單元都用同一種卡片樣式、同樣的排版，觀眾看久了會膩。以下是讓畫面更有設計感、同時避免文字看不清楚的具體做法：

**顏色對比要實際檢查，不要憑感覺挑色。** 文字顏色與背景顏色的對比不夠，是最常見也最容易被忽略的錯誤——尤其是 **Connector 的文字標籤**：它永遠畫在一個固定的、接近全白（`rgba(255, 255, 255, 0.94)`）的底色卡片上，跟畫布本身的深色背景無關。如果比照畫布上其他文字習慣，把 Connector 的 `style.textColor` 設成淺色（例如給一般文字用的米白色），文字就會「淺色字在淺色底上」，幾乎完全看不見。**Connector 的 `textColor` 一律要用深色**（例如 `#1c1712`），跟畫布上其他文字（深色背景、淺色文字）的慣例正好相反，這點很容易忽略。有能力寫程式產生文件時，建議直接算 WCAG 對比度（相對亮度公式）驗證每一組文字／背景配色 ≥ 4.5:1，不要用肉眼猜。

**用不同的形狀、佈局來表達不同的內容，不要每個場景都套同一個樣板。** 同樣是「列出幾個項目」，不必永遠用同一種「直向堆疊的圓角長條」。可以依內容選擇：

- 用不同的 `shapeKind`（`star`／`ellipse`／`diamond`／`triangle`／`pentagon`／`arrow`）當作語意化的圖示——例如用 `star` 代表能量／光，`ellipse` 代表液體，`diamond` 代表分子／結晶，`arrow` 代表流動／轉換。**圖示裡不要放文字**（文字是置中的矩形範圍，塞進星形、菱形這類非矩形形狀會被形狀的尖角截斷、跑版）；正確做法是圖示配一個獨立的文字節點放在旁邊或下方，形成「圖示＋標籤」的組合。
- 同一份簡報裡，不同知識單元可以用不同的排版邏輯：橫向三欄（並列的同類項目）、不對稱的主副配置（用大小表示重要性——主要產物放大、副產物縮小，而不是兩個一樣大的方塊）、左右對照（比較兩個子單元）。
- Connector 不一定要連兩個 Frame 本身；如果 Frame 標題列佔的高度會跟 Connector 的標籤重疊，可以改成連接兩個圖示節點（例如子單元標題上方的小圖示），畫面更乾淨，也能更精準地表達「這個環節的輸出接到下一個環節的輸入」。

## 快速檢查清單

- [ ] 每個知識單元都是一個獨立的 Frame，有自己的 child scene
- [ ] Frame 在外層只顯示標題／輪廓，細節都在 child scene 裡
- [ ] 需要再拆解的單元，用巢狀 Frame 表示子單元（建議不超過 3 層）
- [ ] 單元之間的關聯用根層（或共同上層）的 Connector 表示，附文字標籤
- [ ] 每個 Scene 的時間軸 step 數 = 畫布上的 reticle 數；含 Frame 的 Scene 每個 Frame 恰好一個 step（以 Frame 為中心的 `scene-point`），沒有 `enter-frame`、沒有開場 `scene-overview`、沒有「返回總覽」
- [ ] Step 的 `label` 只有結論短句，沒有序號前綴
- [ ] 每個 `scene-point` 都有 `referenceViewport`，並照「頁面排列與鏡頭公式」算 `zoom` 與 `point`（含 100 單位的標題列空白）
- [ ] 每個 step 捕捉鏡頭時，內容有貼齊瞄準框
- [ ] 用 `reveal` 逐項揭示的節點，跟該 step 的目的地 scene 一致，並設定 `initiallyHidden: true`
- [ ] Connector 的 `textColor` 用深色（它畫在固定的近全白底色上，不是畫布背景）
- [ ] 不同知識單元用不同的圖示形狀與排版邏輯，避免整份簡報只有一種樣板

## 範例檔案

[`examples/photosynthesis-knowledge-units.json`](examples/photosynthesis-knowledge-units.json) 用「光合作用」示範以上所有規則：三個根層知識單元（輸入／過程／輸出）用 Connector 串連；「過程」單元遞迴切出「光反應」「暗反應」兩個子單元，並用 `arrow`／`diamond` 圖示＋Connector 表達兩者的能量轉換關係；「輸入」單元用 `star`／`ellipse`／`diamond` 三種圖示搭配 `reveal` 逐項揭示，橫向三欄排列；「輸出」單元用大小不同的 `pentagon`／`ellipse` 表達主產物與副產物的重要性差異。用 App 的 **Open** 按鈕匯入後即可在編輯畫面瀏覽結構，或按 **Present** 走一遍完整的 13 個 step。
