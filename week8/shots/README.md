# shots 是空的：为什么

这一周想给页面截三张图（开场 / 中段 Stone 说话 / 02:20 的结束页），但截图没有做成：

```
PS> msedge --headless=new --screenshot=shots\test.png http://127.0.0.1:8765/
[ERROR:crashpad_client_win.cc:457] OpenProcess: 拒绝访问。 (0x5)
[FATAL:mojo\public\cpp\platform\platform_channel.cc:187] Check failed: . : 拒绝访问。 (0x5)
```

这台机器的运行沙箱不允许浏览器起自己的进程间通道，所以 headless Edge 起不来。
这不是页面的问题：`code/check_sim.py` 的 G1 用 HTTP 走了页面会走的同一条路径
（`GET /api/state` → `POST /api/act` → 409 → `GET /api/ending`），数据都对，但**渲染没看到**。

## 怎么补

在能开浏览器的机器上：

```powershell
cd week8
python sim\server.py                     # 有密钥时是真调用；没有则 WEEK8_MODE=fixture
# 打开 http://127.0.0.1:8765
# 1. 开场截一张；2. 说两句话、等到 01:10 后截一张；3. 等到 02:20 截结束页
```

把三张图放进这个目录，文件名随意（建议 `01-opening.png` / `02-midwatch.png` /
`03-ending.png`），README 的「诚实的边界」一节就可以删掉第一条。
