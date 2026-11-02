#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TrayMon · Windows 托盘 CPU / GPU 实时监控

常驻右下角托盘，每秒刷新 CPU 和 GPU 占用率：
  - 托盘图标上直接印 `C:xx% / G:xx%`
  - 悬停显示一位小数
  - 右键菜单：开机自启开关 / 关于面板 / 退出

依赖：psutil（CPU）、GPUtil（NVIDIA GPU）、pystray（托盘）、Pillow（图标绘制）
打包：python -m PyInstaller --onefile --windowed --name TrayMon system_monitor.py
"""

import os
import sys
import platform
import subprocess
import webbrowser

from PIL import Image, ImageDraw, ImageFont

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None

try:
    import pystray
    from pystray import Icon, Menu, MenuItem
except ImportError:  # pragma: no cover
    pystray = None
    Icon = Menu = MenuItem = None

try:
    import GPUtil
except ImportError:
    GPUtil = None

APP_NAME = "TrayMon"
APP_VERSION = "1.0"
AUTHOR = "zhangpu"
HOME_URL = "https://zhangpu.dev"
REPO_URL = "https://github.com/zhang-pu/traymon"

INTERVAL = 1.0          # 刷新间隔（秒）
ICON_SIZE = 64          # 绘制图标分辨率

# Windows 开机自启：注册表 Run 键
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


# --------------------------------------------------------------------------- #
# 采集
# --------------------------------------------------------------------------- #
def cpu_percent():
    """CPU 占用率；首次调用返回 0（psutil 首调用是基线）。"""
    if psutil is None:
        return 0.0
    try:
        return float(psutil.cpu_percent(interval=None))
    except Exception:
        return 0.0


def gpu_percent():
    """GPU 占用率（NVIDIA，走 nvidia-smi）；非 N 卡 / 无独显时返回 0。"""
    if GPUtil is None:
        return 0.0
    try:
        gpus = GPUtil.getGPUs()
        if not gpus:
            return 0.0
        return float(max(g.load for g in gpus))
    except Exception:
        return 0.0


# --------------------------------------------------------------------------- #
# 自启
# --------------------------------------------------------------------------- #
def _is_windows():
    return platform.system().lower().startswith("win")


def autostart_enabled():
    if not _is_windows():
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ) as k:
            value, _ = winreg.QueryValueEx(k, APP_NAME)
            return bool(value)
    except Exception:
        return False


def set_autostart(enable):
    """开关开机自启（写当前用户 Run 键，免管理员权限）。"""
    if not _is_windows():
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
            if enable:
                exe = os.path.abspath(sys.argv[0] if getattr(sys, "frozen", False) else sys.executable)
                # 源码运行时用 pythonw 静默启动打包后的 exe
                cmd = f'"{exe}"' if getattr(sys, "frozen", False) else f'"{exe}" "{os.path.abspath(__file__)}"'
                winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(k, APP_NAME)
                except FileNotFoundError:
                    pass
        return True
    except Exception:
        return False


# --------------------------------------------------------------------------- #
# 图标绘制
# --------------------------------------------------------------------------- #
def _load_font(size):
    """尽量取一个能显示 ASCII 的字体；取不到就用默认位图字体。"""
    candidates = [
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "segoeui.ttf"),
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "arial.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default()
    except Exception:
        return None


def make_icon(cpu, gpu):
    """画出托盘图标：C:xx% / G:xx% 两行文字。"""
    img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # 背景：深色圆角块，保证在亮/暗任务栏上都可读
    d.rounded_rectangle((2, 2, ICON_SIZE - 3, ICON_SIZE - 3), radius=12,
                        fill=(28, 32, 38, 235))

    font = _load_font(15)
    small = _load_font(13)

    # CPU 行
    d.text((8, 6), "C:%d%%" % int(round(cpu)), font=font, fill=(120, 220, 140, 255))
    # GPU 行
    d.text((8, 30), "G:%d%%" % int(round(gpu)), font=small, fill=(120, 180, 240, 255))

    # 细边框
    d.rounded_rectangle((2, 2, ICON_SIZE - 3, ICON_SIZE - 3), radius=12,
                        outline=(90, 100, 110, 255), width=1)
    return img


# --------------------------------------------------------------------------- #
# 主程序
# --------------------------------------------------------------------------- #
class TrayMon:
    def __init__(self):
        self.cpu = 0.0
        self.gpu = 0.0
        self.icon = None
        self._first = True

    # ---- 状态 ----
    def update_usage(self):
        self.cpu = cpu_percent()
        self.gpu = gpu_percent()
        self._first = False

    def title(self):
        return "%s · CPU %.1f%% · GPU %.1f%%" % (APP_NAME, self.cpu, self.gpu)

    def refresh(self):
        self.update_usage()
        if self.icon is not None:
            self.icon.icon = make_icon(self.cpu, self.gpu)
            self.icon.title = self.title()

    # ---- 菜单动作 ----
    def toggle_autostart(self, icon, item):
        enable = not autostart_enabled()
        ok = set_autostart(enable)
        state = "已开启" if enable else "已关闭"
        if not ok:
            state = "操作失败"
        if self.icon is not None:
            self.icon.title = "%s · 开机自启 %s" % (self.title(), state)
            self.icon.menu = self.build_menu()

    def about(self, icon, item):
        lines = [
            "%s v%s" % (APP_NAME, APP_VERSION),
            "作者：%s" % AUTHOR,
            "主页：%s" % HOME_URL,
            "",
            "托盘显示 CPU / GPU 实时占用率。",
        ]
        try:
            _message_box("关于 %s" % APP_NAME, "\n".join(lines))
        except Exception:
            pass

    def open_home(self, icon, item):
        webbrowser.open(HOME_URL)

    def quit(self, icon, item):
        if icon is not None:
            icon.stop()

    # ---- 菜单 ----
    def build_menu(self):
        if Menu is None:
            return None
        autostart_on = autostart_enabled()
        return Menu(
            MenuItem("CPU %.1f%%   GPU %.1f%%" % (self.cpu, self.gpu), None, enabled=False),
            Menu.SEPARATOR,
            MenuItem(
                "开机自启（已开启）" if autostart_on else "开机自启（已关闭）",
                self.toggle_autostart,
                checked=lambda item: autostart_enabled(),
            ),
            MenuItem("关于", self.about),
            MenuItem("打开主页", self.open_home),
            Menu.SEPARATOR,
            MenuItem("退出", self.quit),
        )


def _message_box(title, text):
    """尽量用系统原生对话框；没有就退化到控制台输出。"""
    try:
        if _is_windows():
            ctypes_windll = __import__("ctypes").windll
            ctypes_windll.user32.MessageBoxW(None, text, title, 0x40)
            return
    except Exception:
        pass
    try:
        import tkinter
        from tkinter import messagebox
        root = tkinter.Tk()
        root.withdraw()
        messagebox.showinfo(title, text)
        root.destroy()
        return
    except Exception:
        pass
    print("%s\n%s" % (title, text))


def main():
    if pystray is None:
        print("缺少依赖 pystray，请先 pip install pystray psutil GPUtil Pillow")
        return 1

    app = TrayMon()

    # 预热一次 psutil 基线，避免首帧 0%
    cpu_percent()
    app.update_usage()

    icon = Icon(
        "traymon",
        make_icon(app.cpu, app.gpu),
        app.title(),
        menu=app.build_menu(),
    )
    app.icon = icon

    def _tick(icon_arg=None):
        # pystray 会把 icon 作为参数传给 setup 回调
        if icon_arg is not None:
            icon_arg.visible = True
        app.refresh()
        return True

    icon.run(_tick)
    return 0


if __name__ == "__main__":
    sys.exit(main())
