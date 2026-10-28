# sources/raw 是空的：为什么

这一周的原始材料有 3 份，其中 2 份已经在仓库里：

| 材料 | 在哪儿 |
|---|---|
| 英国调查庭报告（Gutenberg #39415） | `../week3&4/sources/raw/british-inquiry-1912-loss-of-steamship-titanic.txt` |
| Beesley 回忆录（Gutenberg #6675） | `../week3&4/sources/raw/beesley-1912-loss-of-ss-titanic.txt` |
| 调查庭第 7 天证词（Titanic Inquiry Project） | **没能整页存下来**，见下 |

## 为什么第 3 份没存下来

这台机器上的 shell 出不了网：

```
PS> Invoke-WebRequest https://www.titanicinquiry.org/BOTInq/BOTInq07Gibson01.php
Invoke-WebRequest : 基础连接已经关闭: 接收时发生错误。

PS> curl.exe -sS -L ... https://www.titanicinquiry.org/BOTInq/BOTInq07Gibson01.php
curl: (35) schannel: AcquireCredentialsHandle failed: SEC_E_NO_CREDENTIALS
```

能出网的那条路（我用来读页面的）不落盘，所以只能**逐字摘录**用到的那些行，
放进 `../processed/tip-day7-extracts.txt`，每行带 Q 号。

## 怎么自己补全

任一方式都行：

```powershell
# 1) 浏览器里打开三页，另存为 HTML 到这里
#    BOTInq07Gibson01.php / BOTInq07Stone01.php / BOTInq07Lord01.php

# 2) 或者用能出网的机器
curl -o tip-bot-day7-gibson-01.html https://www.titanicinquiry.org/BOTInq/BOTInq07Gibson01.php

# 3) 补完之后，把 californian_kb.json 里 source=tip 的条目改成直接核对整页
#    （verify_kb.py 现在核对的是 processed/ 里的摘录）
```

三页的正文都在公共领域（1912 年英国政府速记记录），Titanic Inquiry Project 是把它们转录上网。

## 一个提醒

`data/verify_kb.py` 现在对 `source: "tip"` 的条目只核对「引文在那份摘录里」，
不核对「摘录与网页一致」——后者只能靠人。`research/verification.md` 第 6 节把这条列为未验证。
