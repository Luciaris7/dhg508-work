# Week 8 · Californian 号，中班 00:15–02:20

> 一个历史模拟：1912 年 4 月 15 日凌晨，你站在「加州人号」的桥楼上，是二副手下的中班学徒。
> 远处一条船在冰区里停着，先闪灯，后放火箭。你能看、能问、能记——你不能改变这条船的方向，
> 也不能让船长起床。

## 情境（三句话）

1. 你在 1912 年 4 月 15 日凌晨的「加州人号」桥楼上当中班学徒，能看、能问、能往值班簿上写字；
   海图室的门在两点以前关着。
2. 五六英里外那条船先闪灯、后放八枚白色火箭；二副把这件事报给船长，船长只让他「继续用莫尔斯灯叫」。
3. 走的时候该带走的不是「他应该过去」，而是：一个错误的判断，可以由许多各自都合理的小延迟堆起来；
   而记录，只是被抄下来的那一部分。

**为什么不是电影？** 因为电影会让你同时看见两边：Titanic 在沉，Californian 在等。
这个模拟只给你桥楼上那个人当时能看见的东西：一盏桅灯、八枚白火箭、一句「继续用莫尔斯灯叫」，
和一个睡在海图室里的船长。**把「他本该过去」这句话变得廉价，是电影的强项；把这个小时里
每一个都不像错的判断摊开给你看，是模拟的强项。** 详见 [`research/why-not-a-film.md`](research/why-not-a-film.md)。

```
[00:20] Stone: Flickering, is it. Put the glasses on her yourself before you make up your mind what it is.
[01:05] 你:     That is five rockets now, sir. Shall I call the captain?
[01:05] Stone: Five, you say. I make it five myself. No — hold off. I'll have the glasses on her again first...
[02:00] Stone: Go down to the master. Wake him. Tell him altogether we have seen eight of these white
               lights like white rockets...
[02:08] 船长:  Were they all white? Any colour in them at all? / What is the time?
[02:20] 世界:  两点二十分。你什么也不知道。
```

上面这几段是真实调用跑出来的，不是写好的台词。原样记录在
[`research/demo-transcript.md`](research/demo-transcript.md)，每一次调用的 prompt、回复、
token 与费用在 [`research/calls.jsonl`](research/calls.jsonl)。

## 先跑起来

```powershell
cd week8
python sim\server.py          # 需要 Python 3，只用标准库
# 打开 http://127.0.0.1:8765
```

- 有 `DEEPSEEK_API_KEY`：每个角色回答都是**真调用**，页眉显示 `真调用 · deepseek-flash`。
- 没有密钥：`WEEK8_MODE=fixture python sim\server.py` 会重放上次录下的回答，页眉写
  `录制重放（不是真调用）`，绝不冒充。没录过的句子会直接拒绝（409），不拿别的话顶上。
- 密钥只从环境变量读，代码里没有、日志里也没有。设置方法见 Week 5 的 `code/set_key.py`
  （同一个变量，不用再设一次）。

自检（不联网、不花钱）：

```powershell
python code\check_sim.py       # 21 项：世界规则、模型 JSON、无密钥不冒充、史料可查、费用算对、HTTP 冒烟
python data\verify_kb.py       # 38 条事实，逐一核对引文在原文里的位置
```

本模拟会读 Week 3&4 的两份原文：`../week3&4/sources/raw/british-inquiry-….txt` 与
`beesley-….txt`。仓库结构不变就不用管；挪了地方就设 `WEEK8_SOURCES` 指向那个目录。

## 这一局里有什么

| 是什么 | 在这份作业里的位置 |
|---|---|
| 情境 | 1912 年 4 月 15 日 00:15–02:20，Californian 桥楼／海图室／前甲板 |
| 角色（agentic） | 二副 Herbert Stone：自己的目标、记忆、感知与动作；由模型决定说什么、做什么 |
| 剧本化的人 | 船长 Stanley Lord：他的四句话来自报告原文，所以不许模型即兴 |
| 你 | 中班学徒 James Gibson，二十岁；你的名字与年龄来自他的证词 |
| 知识库 | [`data/californian_kb.json`](data/californian_kb.json)：38 条事实，每条带 locator |
| skill | [`skills/californian-watch-officer/SKILL.md`](skills/californian-watch-officer/SKILL.md)：Stone 是谁、能知道什么 |
| 工具调用 | 模型只能提一个动作（observe / call_up / speak / send_down / nothing），由世界执行或拒绝 |
| 真实 API | `sim/model.py`，DeepSeek `deepseek-flash`，每次调用写进 `research/calls.jsonl` |
| 一条真正的规则 | 世界不是模型：时间、冰、火箭、门锁、船长的回答、值班簿行数，全在 `sim/world.py` 里 |

## 目录

```
week8/
├── README.md                     你在这里
├── questions.md                  这一轮没解决的问题
├── sim/
│   ├── world.py                  世界：地点、物件、时钟、事件、规则、值班簿、结局
│   ├── stone.py                  角色 Stone：记忆、感知、动作清单、JSON 校验、 hindsight 检查
│   ├── model.py                  真调用 + 计费（含峰谷价与缓存命中价）
│   ├── paths.py                  到哪里找 Week 3&4 的原文
│   ├── server.py                 标准库 HTTP，只绑 127.0.0.1
│   ├── static/index.html         一个网页（原生 HTML + JS）
│   └── fixtures/stone_recorded.json   录制的回答，离线重放用
├── data/
│   ├── californian_kb.json       知识库：38 条事实 + 出处 + 等级
│   └── verify_kb.py              逐条核对引文（--fix 可重写 locator）
├── code/
│   ├── check_sim.py              21 项自检
│   └── run_demo.py               跑一局，留下 calls.jsonl / 剧本记录 / 离线替身
├── skills/californian-watch-officer/SKILL.md
├── sources/
│   ├── raw/README.md             为什么这里是空的（见「困难」）
│   └── processed/tip-day7-extracts.txt   逐字摘录的 Day 7 证词
├── research/
│   ├── why-not-a-film.md         这堂课要的回答
│   ├── sources.md                来源清单
│   ├── parts-table.md            每一样东西：evidenced / inferred / invented
│   ├── tools-and-ai.md           每个工具做了什么，AI 做了什么，我查了什么
│   ├── difficulties.md           真实的困难（含例子）
│   ├── verification.md           自检记录
│   ├── cost.md                   花费
│   ├── calls.jsonl               每一次调用：prompt、输出、usage、费用
│   └── demo-transcript.md        一局的完整记录
└── shots/                        截图——见「诚实的边界」
```

## 四个部件怎么拼起来

老师给的四个部件，这次是这么接上的：

1. **agent + skill**（Week 3–5）：`skills/californian-watch-officer/SKILL.md` 写 Stone 的身份、
   已知、未知与判断方式；`data/californian_kb.json` 里标 `"who": ["stone"]` 的 28 条事实，
   就是他能想起来的东西，每条带出处。别的 10 条标 `later`，**永远不进他的 prompt**——
   `code/check_sim.py` 的 E1 会因此失败。
2. **tool calls**（Week 4）：模型只能返回一个动作，`send_down` 在火箭不足三枚时会被世界拒绝；
   `report_master` 根本不在动作表里——报告船长是记录里的事，不是模型能改的事。
3. **知识库**（Week 3–4）：38 条事实，`source` + `locator` + `quote`，`verify_kb.py` 逐条查证。
   引文在原文里找不到，事实就不许加载。
4. **API**（Week 5）：真调用，JSON 模式，`response_format` + prompt 里出现 "JSON"，
   每次调用写一行日志，费用按官方价目表算（含峰谷与缓存命中）。

## 史实与分级

完整表在 [`research/parts-table.md`](research/parts-table.md)。摘要：

- **evidenced**：船停在冰区（10.20）、来船与灯、八枚火箭、1.10 的传声筒问答原文、
  2.00 派学徒的话、2.05 船长的三个问题、2.40 的第二次报告、法庭的判词——全部有 locator。
- **inferred**：桥楼与海图室的具体陈设、值班簿抄进航海日志的规则、火箭的具体间隔
  （报告只给「12.45–1.45 之间共约八枚」）。
- **invented**：动作的时间成本（让 125 分钟压缩成二十来次操作）、页面把玩家的中文当作
  已译成英语说出、hindsight 检查的词表、`send_down` 的提前分支（记录里没有）。

## 工具与 AI 的分工

摘要见 [`research/tools-and-ai.md`](research/tools-and-ai.md)。一句话：
**AI 写代码、写台词、写文档；史料的定位、数字、边界由脚本与人工核。**
模型只被允许扮演一个人，禁止当叙述者；它说的每句话进日志，说漏了 1912 年不该知道的事会被标出来。

## 花费

一局（11 个动作、4 次调用）：**输入 6,396 tok / 输出 426 tok / $0.000669**。
分项在 [`research/cost.md`](research/cost.md)。系统提示约 1.5k tokens，DeepSeek 的前缀缓存
命中了一部分（每次 hit 768–1408 tok），所以比按全价估算便宜。

## 真实的困难

详见 [`research/difficulties.md`](research/difficulties.md)。最要紧的一条：
**我的第一版设计是错的。** 我原本想让玩家在 1912 年伦敦调查庭的走廊里等 Beesley 被传唤——
后来查英国调查庭的证人索引，Beesley 根本不在里面，他从未在该庭作证。设计整个作废，
改成现在这个：Californian 的桥楼，二副 Stone 和学徒 Gibson，两人都在 1912 年 5 月 14 日
（第 7 天）作过证。

## 诚实的边界

- **没有截图**：这台机器的 shell 里起不来浏览器（Edge headless 在命名管道上被挡），
  所以页面只有文字记录与自检，没有图片。页面本身在同学的浏览器里跑得起来——
  这是环境限制，不是页面限制；`code/check_sim.py` 的 G1 用 HTTP 走过同一条路径。
- **没做 3D**：这一周的题不要求；用的是一个网页。
- **船长是剧本**：他的四句话来自报告原文。让他即兴，就是把史料降级成小说。
- **一行代码都没有改 Week 3&4**：本文件夹只读那两份原文。
