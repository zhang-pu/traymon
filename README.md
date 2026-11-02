# TrayMon

> 挂在 Windows 托盘的 CPU / GPU 实时监控小工具。

常驻右下角托盘，每秒刷新 CPU 和 GPU 占用率，不占任务栏、不弹窗口、零打扰。

![version](https://img.shields.io/badge/version-v1.0-blue)
![platform](https://img.shields.io/badge/platform-Windows%2010%2F11%2064--bit-lightgrey)
![license](https://img.shields.io/badge/license-MIT-green)

## 截图

_(TODO: 托盘图标 + 右键菜单 + 关于窗口)_

## 特性

- **托盘直显**：图标上直接印 `C:xx% / G:xx%`，悬停显示一位小数。
- **右键自启开关**：一键切换开机自启，状态自动记住，无需手动改注册表或 Startup 文件夹。
- **NVIDIA GPU 占用**：通过 `nvidia-smi` 读取显卡使用率（非 N 卡或无独显时显示 0%）。
- **单文件免安装**：PyInstaller 打包成一个 exe，无控制台黑窗，双击即跑。
- **关于面板**：内置作者信息与主页链接。

## 下载

到 [Releases](https://github.com/zhang-pu/traymon/releases) 下载最新版 `TrayMon.exe`（约 30 MB），双击即可运行。

> 仅支持 Windows 10 / 11 64-bit。

## 从源码运行

需要 Python 3.10+：

```powershell
git clone https://github.com/zhang-pu/traymon.git
cd traymon
python -m pip install -r requirements.txt
python system_monitor.py
```

## 从源码打包成单文件 exe

```powershell
./build/build.ps1
```

产物会输出到 `release/TrayMon.exe`。

或者手动：

```powershell
python -m pip install pyinstaller
python -m PyInstaller --onefile --windowed --name TrayMon `
  --clean --noconfirm system_monitor.py
```

## 目录结构

```
traymon/
├── system_monitor.py     # 主程序（单文件）
├── requirements.txt      # Python 依赖
├── build/
│   └── build.ps1         # 一键打包脚本
├── release/              # 打包产物（git 忽略）
├── screenshots/          # 截图资源
├── README.md
└── LICENSE
```

## 技术栈

- Python 3
- [psutil](https://github.com/giampaolo/psutil) — CPU 占用
- [GPUtil](https://github.com/anderskm/gputil) — GPU 占用
- [pystray](https://github.com/moses-palmer/pystray) — 系统托盘
- [Pillow](https://python-pillow.org/) — 图标绘制
- [PyInstaller](https://www.pyinstaller.org/) — 打包 exe

## 作者

**zhangpu** — <https://zhangpu.dev>

## License

[MIT](./LICENSE)
