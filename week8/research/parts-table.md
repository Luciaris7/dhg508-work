# 每一样东西：evidenced / inferred / invented

三档，照老师给的分类。**evidenced**：有出处，写清哪一处；**inferred**：从材料推出来的，
写清怎么推；**invented**：没有出处，为了让东西能跑而造，写清为什么需要。

> 「出处」栏里的 `L####` 指报告或 Beesley 的行号（见 [sources.md](sources.md)），
> `Q####` 指调查庭速记的问答号。所有 `evidenced` 行都能被 `data/verify_kb.py` 逐条核对。

## 一、地方

| 部件 | 等级 | 依据 / 做法 | 出处 |
|---|---|---|---|
| 船名、船东、吨位、航线、无乘客、航速 12.5–13 节 | evidenced | 报告 §V 开头 | L3263–3272 |
| 22:20 停船、倒车，因为驶入田冰 | evidenced | 报告 §V | L3333 |
| 船头被「twisted her head」到 E.N.E.，随后基本静止，慢慢向右转 | evidenced | 报告 §V | L3343–3350 |
| 冰区、晴夜、海面平静、极冷 | evidenced | 报告 §V 结尾「The night was clear and the sea was smooth.」 | L3556 |
| 桥楼、海图室、前甲板三个可去之处 | inferred | 报告与证词都提到桥楼、传声筒、海图室的门、甲板；三处的取景（能看见什么）是我按海员常识补的 | L3426、L3471、Q7554 |
| 桥楼上的具体物件：罗经柜、望远镜、莫尔斯灯键盘、传声筒、挂钟 | evidenced（存在）+ inferred（位置） | 证词提到键盘「on top of the bridge」、双眼望远镜、传声筒、驾驶室的钟；摆放位置是推的 | Q7448、Q7462、Q7828、Q7565 |
| 海图室陈设（海图、铜钟、船长坐的椅子） | inferred | 报告只说「went down to the chart room and told the master」；船长「was awake」坐在那里的样子是推的 | L3471–3473、Q7557–Q7570 |
| 前甲板的专利计程仪零件 | evidenced（事件）+ inferred（细节） | Stone 说派 Gibson 下去准备 patent log 的零件 | Q7932 |

## 二、时间

| 部件 | 等级 | 依据 / 做法 | 出处 |
|---|---|---|---|
| 这一局从 00:15 开始，02:20 结束 | inferred | 中班 00:00–04:00；泰坦尼克在 02:20 沉没；报告用它作为整段叙述的终点 | Q7806、L3512 |
| 来船的灯第一次被注意到：约 00:20 | evidenced | 「at about 12.20 a. m.」 | L3431 |
| 火箭从约 00:45 到 01:40，共八枚 | inferred | 报告只说「12.45–1.45 之间共约八枚」，法庭说八枚；具体每一枚的三四分钟间隔来自 Stone 的证词 | L3538–3539、Q7842 |
| 01:10 报告船长 | evidenced | 「about 1.10 a. m.」 | L3439 |
| 02:00 派学徒下去 | evidenced | Stone：「At two o'clock」 | Q7934 |
| 02:05 船长问话 | evidenced | 「It was five minutes past two」 | L3474 |
| 02:40 第二次报告 | evidenced | 报告原文 | L3480 |
| **动作的时间成本**（看 5 分钟、说话 4 分钟…） | **invented** | 真实一小时二十五分，若按真实秒数走，玩家要操作上百次。压缩成二十来次，是为了让「时间紧」变成能感觉到的东西。为什么可以这样造：所有**事件**仍按史料的钟点发生，只有玩家的操作速度被加速 | `sim/world.py` 的 `COST` |

## 三、人与规则

| 部件 | 等级 | 依据 / 做法 | 出处 |
|---|---|---|---|
| Stone：二副、中班、持大副证书、海上八年 | evidenced | 他的证词第一页 | Q7803、Q7835 |
| Stone 的处境记忆（船停着、来船 5 英里、三副交班时说灯熄了） | evidenced | 报告 §V 转述他的证词 | L3320–3410 |
| 船长给他的命令：方位变了或她靠近了才报告 | evidenced | 「tell him if her bearings altered or if she got any closer」 | L3426 |
| 船长 1.10 的四句话 | evidenced | 「Are they company's signals?」/「I do not know…white rockets」/「go on Morsing」/「send the apprentice down」 | L3441–3445 |
| 船长 2.05 的三句话 | evidenced | 「Were they all white?」「Any colour?」「What is the time?」 | L3472–3474、Q7560–Q7566 |
| Stone 说过的两句：「she looks very queer out of water」「a ship is not going to fire rockets at sea for nothing」 | evidenced | 报告引了他的话，他自己承认可能说过 | L3455–3457 |
| Stone 的判断方式（拿不准、把判断交上去、认为可能是公司信号） | evidenced | 他的证词 | Q7853、Q7901、Q7856–7857 |
| Gibson：二十岁，Southport，38 Railway Terrace，学徒 | evidenced | 他的证词 | Q7412–Q7414 |
| Gibson 以为她是 tramp steamer | evidenced | 他的证词 | Q7545 |
| **Stone 的逐句台词** | **invented（但受约束）** | 模型每次生成；只给它身份、已知、可见、以及一句话——不许它知道未来。它说的话进日志，说漏了就标出来 | `sim/stone.py` |
| **船长的回答是剧本**（不交给模型） | evidenced（内容）+ invented（形式） | 他的原话在报告里；让模型即兴重写这四句，等于把史料降成小说。所以它们写死在 `world.py`，连中文译文一起 | `sim/world.py` 的 `_beat`、`_report_to_master` |
| 海图室的门：两点以前不许进 | inferred | 报告说 Gibson 是**被叫下去**的（「he sent Gibson down」「I told Gibson to go down」）；值班学徒自行离开桥楼没有依据。把「没有理由去」变成「去不了」，是模拟的语法 | L3461–3464、Q7949 |
| 在桥楼上只能靠莫尔斯灯，永远没有回答 | evidenced | 报告：反复呼叫，「received no information whatsoever」 | L3466–3469 |
| 火箭数目由世界数，不由玩家或模型说了算 | inferred | 报告里的矛盾正来自三个人数得不一样（八枚 / 五枚 / 一枚）；把「数错」做成机制，是这一课的一部分 | L3472–3489 |
| Stone 可以提前派你下去（`send_down`） | invented | 记录里没有这件事。允许它，是为了让玩家问出「我早点下去会怎样」，并在结局里明确标成「记录没有这样写」 | `sim/stone.py` 的 `_apply` |
| 值班簿八行、写满要划掉 | invented | 报告说「The scrap log is destroyed.」——这给了我一个机制：能留下来的东西有限。八行是我定的，为了让「记什么」变成取舍 | L3339 |
| 抄进航海日志的规则（只抄方位、航向、天气） | **inferred** | 报告说航海日志由大副根据值班簿抄写，但没说抄了什么。这个规则是我按当时商船日志的惯例推的，结束页会把它标成「推断」，不当作史实 | L3308、L3339 |
| hindsight 检查（模型说到 Titanic / distress / sinking 就打标） | invented | 选词很粗，只抓最明显的「未来词」。它不能证明模型真的不知道，只能抓「说漏」 | `sim/stone.py` 的 `HINDSIGHT` |
| 页面假设玩家说的中文已译成英语 | invented | 1912 年英国二副听不懂中文。把「语言不通」做成一个假的翻译层，比让角色说现代中文更不坏；文档里写明这是装置 | `sim/stone.py`、`README.md` |
| 玩家的身份（学徒本人） | inferred | Gibson 确有其人、确有其位；让玩家「成为他」是一种教学上的代用，不是史料主张 | Q7412–7414 |

## 四、明确没有做的事

- 没有把「泰坦尼克号」这个名字放进 Stone 的 prompt。E1 自检会因此失败。
- 没有让模型决定「船开不开」或「船长醒不醒」。那些是 `world.py` 的 if。
- 没有给「八枚火箭」之外的细节编数字：距离（5 英里）与「8–10 英里」的争议原样保留，
  法庭的话与船长的说法分开标注。

## 五、Blender 场景

场景不是「配图」，它是这一局的地方。所以它也要分档。

| 部件 | 等级 | 依据 / 做法 | 出处 |
|---|---|---|---|
| 桥楼是一座开放的平台：前有舷墙与挡风布，两侧是翼台，后面是船舱/轮船舱 | evidenced | 报告与证词反复提到「bridge」「bridge wing」「wheelhouse」「chart room」「the chart-room door」；当时的商船都是这个布置 | L3410、L3426、Q7565、Q7554 |
| 轮船舱（wheelhouse）在桥楼后部、带一排窗 | inferred | 证词只说「wheelhouse clock」，没说它长什么样；一排窗与木/铁壳按同时代船只的照片布置 | Q7565 |
| 海图室在轮船舱后面，门朝右舷，里面一张海图桌 | evidenced（存在）+ inferred（位置与陈设） | 「went down to the chart room and told the master」「the chart-room door」（门在关着） | L3471–3473、Q7554 |
| 莫尔斯灯在桥楼顶部、有灯罩与键盘 | evidenced | 「the keyboard…on top of the bridge」「Morse lamp」 | Q7448、L3468 |
| 罗经柜（binnacle）在桥楼中间 | inferred | 证词提到罗经方位（「S.S.E. by the standard compass」），但没说柜子在哪；按惯例放在桥楼中线 | Q7820 |
| 传声筒在舱门旁 | evidenced（存在）+ inferred（位置） | 「speaking tube」「by voice pipe」 | Q7828、L3420 |
| 双筒望远镜搁在舷墙的托架上 | evidenced（物件）+ inferred（位置） | 「with the glasses」「binoculars」 | Q7426、L7838 |
| 值班簿与铅笔在桥楼上一只木箱上 | invented | 报告只说「scrap log」；把它放在玩家手边，是为了让「记一行」这个动作有地方落 | L3308 |
| 船钟挂在舷墙上 | invented | 报告没提；加它是为了让观众一眼知道这是船 | — |
| 冰区：近处碎冰、远处连片冰原 | evidenced（有冰）+ invented（形状与数量） | 报告：船「surrounded by ice」，冰区宽 2–3 英里 | L3245、L3538 |
| 星空、月亮在左舷后上方 | invented | 报告只说「night was clear」；星与月是造出来给夜里的方向感 | L3556 |
| 三处全景的相机位置（桥楼右舷翼 1.66 m、前甲板、海图室门口 1.56 m） | invented | 相机在哪，决定观众看见什么。桥楼选右舷翼，是因为来船「right on the starboard beam」 | Q7438 |
| 每个热点的方位角/仰角 | 算出来的 | 不是手摆的：`hotspots.json` 由相机矩阵把世界坐标投到等距圆柱坐标，公式写在 `build_bridge.py` 的 `hotspot_angles()` | — |
| 网页上实时画的桅灯与火箭 | invented（画面）+ evidenced（事件） | 全景是静的；灯要闪、火箭要升，只能让网页画。它们由 `world.py` 的时钟触发 | `sim/static/scene.html` |
| 船舱里的船长 | evidenced（在场）+ invented（姿势） | 报告：「the master was awake」，问了两句话 | L3472–L3473、Q7570 |
