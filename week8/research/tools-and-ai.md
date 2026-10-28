# 每个工具做了什么，AI 做了什么，我自己查了什么

## 1. 工具

| 工具 | 做了什么 | 我给它打几分 |
|---|---|---|
| `read` / `grep` / `glob`（读文件） | 把 Week 3&4 的报告与 Beesley 全文、Week 5 的应用、`.gitignore` 读进来；定位 §V 与证人证词 | 好：行号与原文一起给，能直接当 locator |
| Python 3 标准库 | 世界、角色、服务器、自检、计费，全部无第三方依赖 | 好：`sqlite3` 与 `urllib` 就够 |
| PowerShell | 起服务器、跑脚本、读注册表里的密钥（不打印）、列目录 | 能用，但**它出不了网**（见困难 6） |
| DeepSeek API（`deepseek-flash`，JSON 模式） | 扮演 Stone：每句话、每个动作 | 见下面第 3 节 |
| Edge headless | 想给页面截图 | **失败**：沙箱里起不来（命名管道被挡） |
| git | 提交到 `dhg508-work` 仓库的 `week8/` | 待做，见 README |

## 2. AI 做了什么（以及没做什么）

**AI（这个 agent）做的：**

- 把报告 §V 的叙述拆成时间线、地点、物件；
- 读证人索引，**否掉**了自己最初的 Beesley 方案（困难 1）；
- 写 `world.py` 的规则、`stone.py` 的提示词、`index.html`、自检与文档；
- 起草 Stone 的 system prompt，并把「不许知道未来」写进约束；
- 起草这一页与 `why-not-a-film.md`。

**AI 没有做、也不能做的：**

- **编造史料**。每一条 `evidenced` 事实都必须在原文里找得到引文，`verify_kb.py` 找不到就报错；
  locator 不是我估的行号，是脚本搜出来再写回去的（`--fix`）。
- **决定历史**。船停不停、火箭几枚、船长说不说话、门锁不锁，全是 `world.py` 的代码。
- **代替我看证据**。Beesley 有没有作证、火舰间隔多长、八枚还是十枚——这些我都回原文核过，
  核不出来的就标成 inferred 或 invented。

## 3. 模型在模拟里做了什么

一个回合，里外是这样的：

```
玩家:  "That is five rockets now, sir. Shall I call the captain?"
  ↓ world.act("say")
    1. 世界记下这句，抽出数字 5 → game.claims = [{said:5, true:5}]
    2. world 拼出「感知」：现在 01:05、桥楼、来船右舷正横 5 英里、你数到 5 枚、船长没被报告过…
    3. stone.py 组装 messages：身份 + 已知 28 条（带 locator）+ 感知 + 动作表 + JSON 要求
    4. model.chat() 真调用 → 返回 JSON（下面这一段就是真的）
    5. parse() 校验：字段、动作白名单、词数、hindsight 词表
    6. world 执行 act=call_up：叙述「Stone 走到莫尔斯灯前……没有回答」
    7. 日志写一行：prompt、response、usage、tokens、峰谷价、费用
```

真的返回（`research/calls.jsonl` 第 2 条）：

```json
{"say": "Five, you say. I make it five myself. No — hold off. I'll have the glasses on her
 again first, and I'll call her up. If she gives me nothing, then you may go down to the captain.",
 "say_zh": "你说五发。我数的也是五发。不——先等等。我再用望远镜看一遍，用莫尔斯灯呼她。
 要是她仍不答，你再下去见船长。",
 "act": "call_up",
 "why": "先弄清她到底答不答话，再惊动船长不迟。"}
```

**模型说错话会怎样**：`act` 不在白名单里 → 降级成 `speak`；超过 60 词 → 截断；
说到 `Titanic` / `distress` / `sinking` → 标 `hindsight`，页面写一句「这条回答不当作史实」。
统计：这一局 4 次调用，0 次 hindsight，0 次截断，0 次 JSON 修复。

## 4. 我自己查了什么

| 检查 | 怎么查 | 结果 |
|---|---|---|
| 38 条事实的引文在原文里 | `python data/verify_kb.py` | 0 failed（locator 由脚本写回） |
| 世界规则（门锁、值班簿、八枚、2:20） | `python code/check_sim.py` A 段 9 项 | 全 PASS |
| 模型 JSON 的抗坏能力 | B 段 5 项（代码围栏、未知动作、超长、hindsight、提前 send_down） | 全 PASS |
| 没有密钥时不冒充 | C 段 2 项 | 全 PASS |
| 未来知识不进 prompt | E1：把标注 `later` 的 10 条逐条查是否出现 | 全 PASS（第一次**失败**过，见困难 2） |
| 费用算术 | F1：手算 1000 in / 100 out 的谷峰两价 | PASS（$0.00021 / $0.00042） |
| HTTP 三接口 | G1：起真服务器，GET state → POST act → 409 → ending | PASS |
| 页面能不能跑 | 用 HTTP 走了一遍页面会走的同一串动作（fixture 模式），并看 `/api/ending` | 数据都对；**渲染没看到**（见困难 6） |

## 5. 哪些话我不该说

- 我没有在课堂上演示过，所以不能说「它讲得动」。
- 我没有截图，所以不能说「页面长这样」。
- 模型只跑了 4 次，所以不能说「Stone 稳定地像 1912 年的二副」——只能说这 4 次里像。
