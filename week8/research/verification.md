# 自检记录

运行环境：Windows，Python 3.14，无第三方库。全部不联网（除了 `run_demo.py` 那一次真调用）。

## 1. 知识库：38 条事实，逐条查引文

```
python data/verify_kb.py
```

```
  ok   cal.ship           report L3303     3303
  ok   cal.stopped        report L3333     3333
  ok   cal.heading        report L3343     3343
  ok   cal.scraplog       report L3339     3339
  ok   steamer.approach   report L3348     3348
  ...
  ok   court.rockets      report L3538     3538
  ok   court.ice          report L3557     3557
  ok   court.saved        report L3559     3559
  ok   court.distance     report L3553     3553
  ok   court.night        report L3556     3556
  ok   court.number       report L3539     3539
  ok   court.discrepancy  report L3489     3489

38 facts, 0 failed
```

**第一次跑是 20 failed**，原因是我用估算的行号写 `locator`。后来给脚本加了 `--fix`，
由它把真实行号写回 JSON——所以现在这些数字是搜出来的，不是我数的。

## 2. 世界与角色：21 项

```
python code/check_sim.py
```

```
  PASS  A1 the watch opens at 00:15 on the bridge
  PASS  A2 the chart room is shut until you are sent
  PASS  A3 looking at something that is not there is refused, with the list
  PASS  A4 the scrap log holds eight lines; you must cross one out
  PASS  A5 rockets fire on the world's clock, not the player's
  PASS  A6 the report to the master happens once, and only when sent
  PASS  A7 the watch ends at 02:20 and says so
  PASS  A8 you cannot talk to a man who is on another deck
  PASS  A9 a number the player asserts is checked against the world's count
  PASS  B1 a code-fenced reply is read as JSON
  PASS  B2 an unknown action becomes 'speak'; a long reply is cut
  PASS  B3 hindsight is flagged, and ice is not hindsight
  PASS  B4 Stone cannot send you down before there is anything to report
  PASS  B5 after three rockets his 'send down' happens, and is marked as a divergence
  PASS  C1 with no key and no recording, the character refuses to answer
  PASS  C2 WEEK8_MODE=deepseek without a key is an error, not a fallback
  PASS  D1 every fact's quotation is on disk, and the locator agrees
  PASS  E1 the court's finding is not in the character's prompt
  PASS  E2 only facts marked for him are sent, each with a locator
  PASS  F1 the receipt is arithmetic, not a guess
  PASS  G1 one HTTP round trip: state, action, refusal, ending

21 passed, 0 failed
```

其中 E1 与 B3 是「被 bug 逼出来的检查」：E1 第一次失败，是因为我把「你从没听说过泰坦尼克号」
写进了提示词（见 `difficulties.md` 第 2 条）；B3 是为了保证 `ice` 不被误判成未来词。

## 3. 真调用跑一局

```
python code/run_demo.py
```

15 步里 11 个是动作（其余是三次「等到第 5 枚」「等到第 8 枚」「等到被叫下去」，
以及最后那次世界已经结束、没走成的等待），共 4 次模型调用，02:20 结束。关键片段（全文见
[`demo-transcript.md`](demo-transcript.md)）：

```
[01:05] 你:     That is five rockets now, sir. Shall I call the captain?
[01:05] Stone: Five, you say. I make it five myself. No — hold off. ...
[01:10] 世界:  传声筒的盖子掀开……「Are they company's signals?」……「Go on Morsing.」
[02:00] Stone: Go down to the master. Wake him. Tell him altogether we have seen eight ...
[02:08] 船长:  Were they all white? Any colour in them at all? / What is the time?
[02:20] 世界:  两点二十分。你什么也不知道。
```

- hindsight 标记：0 次
- JSON 修复重试：0 次
- 回答超长被截断：0 次
- 世界里被拒绝：0 次

## 4. 费用

见 [`cost.md`](cost.md)：4 次调用，输入 6,396 tok / 输出 426 tok / **$0.000669**。
费用不是估的：`usage` 里的 `prompt_cache_hit_tokens` 与 `prompt_cache_miss_tokens` 分别
按官方价目表计价（`sim/model.py` 的 `PRICES`），F1 用手算结果验过这条公式。

## 5. 页面

- `GET /api/state`、`POST /api/act`、`POST /api/reset`、`GET /api/ending` 都跑过（fixture 模式）。
- 用 HTTP 按页面会走的顺序走了一遍：看灯 → 说 → 莫尔斯 → 等 → 说 → 写 → 等 → 说 → 写 → 等
  → 进海图室 → 报告 → 回桥楼 → 说 → 等；`/api/ending` 返回的 `scrap`、`fair`、`lost`、
  `facts` 都对。
- **没有做**：浏览器里的渲染检查（这台机器的沙箱起不来浏览器）。所以「页面好不好看、有没有
  JS 报错」这一条**没有验证**，不装作验证过。这一条写进了 `README.md` 的「诚实的边界」。

## 6. 没验证的事（明确列出）

1. 页面在浏览器里的实际渲染与交互（只验证了 HTTP 层）。
2. 课堂投影下的可读性。
3. Stone 的回答是否**稳定**地像 1912 年的人——只跑了 4 次。
4. `fair log` 那条推断规则是否符合当时的商船惯例（我只按报告里「大副抄写」一句推的）。

## 7. 场景（Blender）

```
blender --background --factory-startup --python scene/build_bridge.py -- --glb
```

- 引擎：Cycles，OptiX GPU（`NVIDIA GeForce RTX 5070 Laptop GPU`）。
- 分辨率：全景 3072×1536（JPEG，150–300 KB），剧照 1760×990（PNG）。
- 采样：160，自适应 + 降噪（OIDN）。
- 用时：整套约 5 分半（三张全景 + 两张剧照 + `.blend` + `.glb`）。
- 输出：`scene/renders/` 下 9 个文件，`hotspots.json` 在每个渲染前写好。

逐张看过：桥楼（冰区、栏杆、莫尔斯灯、轮船舱、值班簿、二副）、前甲板（桅、支索、绞车、冰）、
海图室（海图桌、油灯、舷窗、门、船长）。**第一轮二副不在画面里**（站在实心船舱内），
**海图室第一轮是一间空房**（船长的位置与桌子重叠、房间是实心方块），改过之后重渲。见 `difficulties.md`。

## 8. 网页场景层

```
GET /                 → scene.html（3D 场景）
GET /text             → index.html（文字版）
GET /api/scene        → hotspots.json
GET /scene/pano_bridge.jpg → 3072×1536 JPEG
```

- `node -e "new Function(script)"`：语法通过，391 行。
- HTML 里的 id 与 JS 里 `$("…")` 引用逐个比对：无缺失。
- HTTP 逐条取过：`/api/state`、`/api/scene`、`/scene/pano_*.jpg`、`/api/act`（含 409 拒绝）、`/text`。
- **没做到**：真浏览器里看它。见 `difficulties.md` 第 9 条。

## 9. 没验证的事（更新）

1. 场景页在浏览器里的实际渲染、拖动、热点位置（只验证了数据与语法）。
2. 全景在 60° 视野下的清晰度（3072 宽 → 每度约 8.5 px）。
3. Stone 的回答是否稳定地像 1912 年的人——只跑了 4 次。
4. `fair log` 那条推断规则是否符合当时的商船惯例。
5. `.glb` 能不能在 Unity/Godot 里正常导入（没装 Unity）。

## 10. 浏览器里的验证（补上了）

沙箱的策略改过之后，headless Edge 可以用了（需要 `--user-data-dir` 指一个临时目录）。
于是网页这一层终于真的被看过：

```
msedge --headless=new --disable-gpu --no-sandbox --user-data-dir=%TEMP%\es \
  --window-size=1600,1000 --virtual-time-budget=9000 \
  --screenshot=shots\01-opening.png http://127.0.0.1:8765/
```

- 三张截图：`shots/01-opening.jpg`（00:15 开场）、`02-talking.jpg`（跟二副说话，真调用）、
  `03-chart-room.jpg`（02:11，被叫下去之后）。
- 截图当场暴露的四个 bug（开场正对冰区、冰排过大、二副在实心船舱里、空值班簿编号）都已修好，
  见 `difficulties.md` 第 11 条。
- 还验证了：热点标签落在物体上（「那盏灯」「冰」「船长」「海图」「钟」），
  远处那盏灯的光点由网页实时画在正确方位，`现场` 卡片会把世界的事件按时间排出来，
  「向船长报告」按钮只在海图室里、且被叫下去之后才出现。

**仍然没验的**：拖动手感、转动时热点跟随是否跟手、窗口尺寸变化后的重排、触屏。
