# reference · 给改这个 skill 的人

这一页不重复 `SKILL.md`。它只说：改动时哪些地方必须一起改，哪些地方不能动。

## 1. 事实的唯一来源是 `data/californian_kb.json`

- 每条事实有 `id` / `who` / `kind` / `text` / `source` / `locator` / `quote` / `note`。
- `who` 里含 `stone` 的，才进 Stone 的提示词；含 `later` 的，永远不进
  （`code/check_sim.py` 的 E1 会失败）。
- 加一条事实的流程：写 `quote`（原文逐字）→ `python data/verify_kb.py --fix` 让它把 locator
  写成真实行号 → 再跑 `python data/verify_kb.py` 确认 0 failed。
- 引文在原文里找不到，脚本会拒绝；不要手写行号。

## 2. 提示词在 `sim/stone.py`

- `SYSTEM` 是模板：身份、已知、感知、行为规则、动作表、JSON 要求。
- 行为规则里有一条不能删：**「不许知道未来」**。但注意：不要用「你从没听说过 X」这种
  否定句写它——那句话本身就把 X 送进了上下文（`research/difficulties.md` 第 2 条）。
- 加规则时先想：这条规则能不能被一次自检抓到？抓不到的规则，写在文档里也要标明是「靠人守」。

## 3. 动作表在 `sim/stone.py` 的 `ACTS`，执行在 `sim/stone.py` 的 `_apply`

- 加动作 → 在 `ACTS` 加一行说明 + 在 `_apply` 加一个分支（世界怎么执行或拒绝）。
- `_apply` 里每个拒绝都要写清原因，并且用中文，因为那句话会显示给玩家。
- **不要让模型直接改世界状态**。模型只能提议，`_apply` 与 `world.py` 决定。

## 4. 世界在 `sim/world.py`

- 时间线在 `BEATS`；玩家的动作成本在 `COST`；能看见什么在 `PLACES`。
- 加一个「物件」要同时加：`PLACES[...]["objects"]` 的说明、`index.html` 的
  `OBJECT_LABELS` 中文标签（不加也能点，只是按钮显示英文键名）。
- 结局在 `Game.ending()`；`fair` / `lost` 的规则在那里，改它要同步改
  `research/parts-table.md` 与结束页的说明文字。

## 5. 不能动的东西

- 船长的四句话（`_beat` 里的 `report`、`_report_to_master` 里的两句、`stone.240`）：
  它们是报告原文。要改，先改 `parts-table.md`，把它从 evidenced 降级成 invented。
- 八个火箭的时间与数量：报告说「12.45–1.45，约八枚」，法庭说「八枚」。
- 「海图室两点以前进不去」：这是 `why-not-a-film.md` 论证的一部分（军衔的物理形态）。

## 6. 改完跑什么

```powershell
python data\verify_kb.py      # 史料还站得住吗
python code\check_sim.py      # 世界规则、JSON、无密钥、prompt 洁癖、费用、HTTP
python code\run_demo.py       # 真跑一局（花钱，几分钱），顺便重录离线替身
```
