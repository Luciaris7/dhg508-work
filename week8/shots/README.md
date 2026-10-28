# shots · 浏览器里的样子

三张，都是这台机器上 `msedge --headless=new` 截的（1600×1000，JPEG）。
来源：`http://127.0.0.1:8765/`，Blender 全景 + 网页 HUD。

| 文件 | 什么时候 |
|---|---|
| `01-opening.jpg` | 00:15，打开页面看到的第一眼：右舷翼、栏杆、冰区、远处那盏灯（网页实时画的），二副在左手边 |
| `02-talking.jpg` | 00:19，问了二副一句「她的桅灯在闪，先生在叫她吗？」，这是他那次真调用回答 |
| `03-chart-room.jpg` | 02:11，被叫下去、进了海图室：海图桌、油灯、墙上的钟、舷窗、坐在桌后的船长 |

## 怎么重截

```powershell
python sim\server.py                     # 另开一个窗口也行
& "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" `
  --headless=new --disable-gpu --no-sandbox --disable-breakpad --disable-crash-reporter `
  --user-data-dir="$env:TEMP\es" --hide-scrollbars --window-size=1600,1000 `
  --virtual-time-budget=9000 --screenshot="shots\01-opening.jpg" "http://127.0.0.1:8765/"
```

要点：`--virtual-time-budget` 要给足（页面要先取 `/api/state` 和 `/api/scene` 才画）；
`--user-data-dir` 指一个临时目录，不然 Edge 会因为复用你的主配置而拒绝启动。
