# 真实的困难

按「疼过」排序。每一条都有例子。

## 1. 我的第一版设计是错的：Beesley 没有在英国调查庭作证

第一版的想法：1912 年 5 月，伦敦 Buckingham Gate 的苏格兰厅（Scottish Hall），
玩家是调查庭的临时书记官，在走廊里等着被传唤的二等舱乘客 Lawrence Beesley。
我连台词都想好了：他会说「Anybody knows what rockets at sea mean」。

后来我去查调查庭的证人索引（<https://www.titanicinquiry.org/BOTInq/BOTIndx01.php>），
在 B 段里找不到 Beesley：Barr、Barrett、Bartlett、Beauchamp、Boxhall、Boyle、Braes、
Bride、Brown、Buley，没有他。索引里乘客只有 Ismay 与 Duff Gordon 夫妇这一小撮。
**Beesley 从未在英国调查庭作证。**

这意味着：那个「走廊」场景里，等着被传唤的那个人不存在。一个历史模拟如果连「这个人今天
会不会来这栋楼」都错了，后面所有细节都不必谈。

改法：换到同一夜的另一条船上，Californian 的桥楼。Stone 与 Gibson 都在 1912 年 5 月 14 日
（第 7 天）作过证，报告 §V 几乎逐句引了他们的话。教训是：**选题不是灵感的产物，
是索引翻出来的。** 一个「查一下」花了我十分钟，省掉了一次课堂上被一句话问倒。

## 2. 模型知道未来，而角色不能知道

我第一次跑自检时 E1 失败：

```
FAIL  E1 the court's finding is not in the character's prompt
      AssertionError: prompt leaks 'titanic'
```

原因可笑：我在提示词里写了「你从没听说过泰坦尼克号」。**这句话本身就把「泰坦尼克号」
送进了它的上下文。** 否定式提示是泄漏。

改法：把这句话改成「今晚没有任何海难的消息传到这座桥楼」，并且把 E1 改成**逐条**检查：
所有标 `later` 的 10 条事实，其原文不得出现在 prompt 里。现在 E1 通过。

这件事的教训比 bug 大：**「不许知道」这件事，不能靠一句请求，只能靠一次检查。**
`data/californian_kb.json` 里 `who` 字段是给脚本看的，不是给模型看的。

## 3. 模型会把玩家说错的数字当真

第二次真跑时，玩家在 00:45 喊「That is five rockets now」，而海面上其实只有一枚。
Stone 的回答是：

> Five, is it. Very well. Call her up on the lamp again first — if she gives no answer to
> that, then you may go down and wake him.

他数都没数，就接受了玩家报的数字。这正好是历史里发生的事——三个人对八枚、五枚、一枚的
说法不一致——但它在这局里是 bug，不是设计：世界明明知道只有一枚。

改法：世界在 `say` 里抽数字（`world.rocket_claim`），把「玩家说的」与「世界数的」都记下来，
感知里明说「他喊的是七枚，你只数到五枚」。现在 Stone 会回「Five, you say. I make it five
myself」，而说错的那一次会进结局的对照表。

## 4. 语言：1912 年的二副听不懂中文

玩家是中文用户，角色是 1912 年的英国二副。让 Stone 说现代中文，比不真实更糟——那是把
「语言不通」这件历史上的真事（三等舱乘客听不懂英语询问）悄悄抹掉。

做法：角色只说英语；页面说「假设你把这句话说出了口（页面假设它已译成英语）」；每句回答
同时给一份中文译文，但那是我（模拟）的翻译，不是角色的语言。这是 invented 装置，
写进 `parts-table.md`，不假装它是史料。

## 5. 抄写规则没有史料，只能标成推断

报告只有一句：「The log book … was written up from the scrap log book by the chief officer.
The scrap log is destroyed.」（L3308）它没说抄了什么、漏了什么。

我不想凭空发明一个「史实」，于是把这条规则明确标成 **inferred**，并在结束页上写着
「下面的『抄进日志的』与『没有抄进去的』，是本模拟按『只抄方位、航向与天气』的推断规则分的，
不是史料」。设计上也留了余地：哪怕这条规则是假的，那一句「值班簿已销毁」是真的，
而玩家亲手写过它——这一层体验不依赖推断是否正确。

## 6. 这台机器不让我下载、也不让我截图

- **下载**：`Invoke-WebRequest` 与 `curl.exe` 都失败（schannel「没有可用的凭证」、TLS 连接被关），
  于是两页证词存不进 `sources/raw/`。改法：用能出网的工具读一遍，**逐字摘录**用到的那几十行，
  存成 `sources/processed/tip-day7-extracts.txt`，每行带 Q 号，`verify_kb.py` 核对引文是否
  真在这份摘录里，读者可以拿 Q 号回原页对照。这是一个退让，不是等价物。
- **截图**：`msedge --headless` 起不来（crashpad `OpenProcess` 拒绝访问、mojo 命名管道 `Check failed`）。
  所以 `shots/` 是空的。页面本身在同学浏览器里能跑；`code/check_sim.py` 的 G1 用 HTTP 走了
  同一条路径，但**我看不到它长什么样**——这一点必须说清楚，不能拿「应该没问题」当验证。

## 7. 时间被压缩了，这是一个取舍

真实：125 分钟，几十个动作。若按真实节奏，玩家要敲上百次，模型要调上百次，一局几毛钱
变成几块钱，而「时间紧」的感觉反而被操作疲劳替代。

做法：事件按史料的钟点发生（这一点没有压缩），玩家的动作成本被放大（看 5 分钟、走 6 分钟、
等 10 分钟）。于是 16 个动作能走完一夜。这是 invented，写进
`parts-table.md` 的「时间」段，理由也写在那一行里。
