# 来源清单

四份材料。前两份在仓库里（Week 3&4 已下载），后两份是这一周新增的。

## 1. 英国沉船调查委员会报告（一手）

*Loss of the Steamship "Titanic"* — Report of a Formal Investigation into the
circumstances attending the foundering on April 15, 1912, of the British
steamship *Titanic*, of Liverpool. Washington, 1912（62d Congress, 2d Session,
Senate Document No. 933）。

- 电子文本：Project Gutenberg eBook #39415，<https://www.gutenberg.org/ebooks/39415>
- 本地副本：`../week3&4/sources/raw/british-inquiry-1912-loss-of-steamship-titanic.txt`
- 本书里用 `L####` 指该文件的行号。
- 用到的部分：卷首开庭记录（L148–162，含会期与地点）、**§V「The circumstances in
  connection with the steamship Californian」**（L3260–3560）。§V 是这一周几乎全部
  史实的来源：船位、冰区、来船、八枚火箭、1.10 的传声筒问答、2.00 派学徒的话、
  2.05 船长的问话、2.40 的第二次报告、三份证词的矛盾、法庭的判词。

## 2. Beesley 回忆录（一手，幸存者）

Lawrence Beesley, *The Loss of the S.S. Titanic: Its Story and Its Lessons* (1912)。

- 电子文本：Project Gutenberg eBook #6675，<https://www.gutenberg.org/ebooks/6675>
- 本地副本：`../week3&4/sources/raw/beesley-1912-loss-of-ss-titanic.txt`
- 本书里用 `L####` 指该文件的行号。
- 用到两处：沉船上有人喊「Rockets!」（L1304）；他记下的 1912 年那个反对说法——
  火箭也可以是渔船招呼小艇的信号（L2660）。后者是这个模拟里「看不懂」的物质基础：
  1912 年的火箭并非只用于求救。

## 3. 英国调查庭第 7 天证词（一手，庭审速记）

Titanic Inquiry Project 对英国沉船调查庭（Wreck Commissioner's Inquiry）速记记录的转录：

- James Gibson（学徒）第 7 天证词：<https://www.titanicinquiry.org/BOTInq/BOTInq07Gibson01.php>
  （Q7412–7610）
- Herbert Stone（二副）第 7 天证词：<https://www.titanicinquiry.org/BOTInq/BOTInq07Stone01.php>
  （Q7803–7960）
- 开庭日：1912 年 5 月 14 日（第 7 天，与 Lord 同一天）。报告 §V 引用了其中大部分问答，
  但有些只有速记里才有：Gibson 二十岁、家住 Southport（Q7412–7414）；
  Stone 持大副证书、海上八年（Q7803、Q7835）；Gibson 以为她是条 tramp steamer（Q7545）；
  Stone「I just took them as white rockets, and informed the Master and left him to judge」
  （Q7853）；「I had never seen company's signals like them before」（Q7901）。

**注意**：这两页没能整页存进仓库——见 [`../sources/raw/README.md`](../sources/raw/README.md)。
逐字摘录在 [`../sources/processed/tip-day7-extracts.txt`](../sources/processed/tip-day7-extracts.txt)，
`data/verify_kb.py` 会核对知识库里每条引文是否真的在这份摘录里；摘录里每行带 Q 号，
读者可以拿 Q 号回原页逐条对照。

## 4. 英国调查庭证人索引（用来否证一个设计）

<https://www.titanicinquiry.org/BOTInq/BOTIndx01.php>（以及续页 `BOTIndx02.php`）

- 抓取日期：2026-10-07。
- 用途：核对某个人有没有在该庭作证。**Beesley 不在索引里**——他从未在英国调查庭作证。
  这一条否掉了我最初的设计（见 [`difficulties.md`](difficulties.md) 第 1 条）。
- 同页确认：Stone、Gibson 均在第 7 天作证；Lord 也在第 7 天；Stewart 在第 8 天。

## 5. 价格（算费用用的不是史料，但也要写清出处）

DeepSeek《Models & Pricing》：<https://api-docs.deepseek.com/quick_start/pricing>
（读取日期 2026-10-07）。`deepseek-flash`：输入缓存命中 $0.003/$0.006（谷/峰）、
未命中 $0.15/$0.30、输出 $0.60/$1.20（每 1M tokens）。峰时为 UTC 周一至周五
01:00–04:00 与 06:00–10:00。`sim/model.py` 按这张表算钱。

## 没有用到的

- 没有图片、没有 3D、没有音效。这一周的作业不要求，也没有素材能加强「信息不足」这件事。
- 没有用美国参议院调查（US Senate Inquiry）：它的证词里有多位三等舱乘客，是另一个题目
  （「谁被听见」），这一周不做。
