#!/usr/bin/env python3
"""QA for v2.50M: the Windows desktop launcher (desktop/ScoutFinanceLauncher.cs, built into "Scout Finance.exe").

Static checks on the source and the scripts (the app it starts, loopback only, the key never printed or logged, no flag that made Chrome close itself,
the process tree is stopped), the icon, and - only on Windows with the .NET Framework compiler - a real build whose non-GUI `--check` mode is run with a
FAKE key to prove that the report says whether a key exists but never its value. The window lifecycle (open, second launch, close, shutdown) needs a
desktop and was verified by hand; see DESKTOP_LAUNCHER_v2_50m.md. No network, no real key."""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESKTOP = ROOT / "desktop"
SOURCE = DESKTOP / "ScoutFinanceLauncher.cs"
FAKE_KEY = "CG-FAKE-LAUNCHER-KEY-NOT-REAL-0000"
CSC = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Microsoft.NET" / "Framework64" / "v4.0.30319" / "csc.exe"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_the_launcher_starts_the_current_app_on_loopback_only() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    app = re.search(r'const string AppFile = "([^"]+)"', source)
    require(app is not None and (ROOT / app.group(1)).exists() and app.group(1) == "app_v2_37.py", "it starts the current app, and that file exists")
    require("--server.address 127.0.0.1" in source and "--server.headless true" in source and "--browser.gatherUsageStats false" in source, "headless, loopback, no usage stats")
    require('"http://127.0.0.1:"' in source and "http://localhost" not in source.replace("// not \"localhost\"", ""), "127.0.0.1, never localhost (it resolves to IPv6 first and the app listens on IPv4)")
    require("CreateNoWindow = true" in source and "target:winexe" in (DESKTOP / "build_launcher.ps1").read_text(encoding="utf-8-sig"), "no console window")
    require("--app=" in source and "--user-data-dir" in source and "--scout-finance-window=" in source, "its own app window, with a profile of its own and a marker to recognise it")
    require("--disable-background-mode" not in source.replace("// ", ""), "that flag made Chrome close itself a few seconds after opening: it stays out")
    require(source.index("chrome.exe") < source.index("msedge.exe"), "Chrome is tried before Edge (an Edge app window closed itself on the test PC)")
    require("taskkill" in source and "/T /F" in source and "ProcessExit" in source, "the whole server process tree is stopped when the window closes or the launcher ends")
    require("Local\\\\ScoutFinanceDesktopLauncher" in source, "one instance at a time")


def test_the_key_is_never_printed_logged_or_written() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    uses = [m.start() for m in re.finditer(r"\bUserKey\(\)|\bKeyVariable\b", source)]
    require(uses, "the launcher does handle the key")
    for line in source.splitlines():
        if "UserKey()" in line or "KeyVariable" in line:
            require(not re.search(r"Write(Line)?\(|WriteAllText|MessageBox|Console\.", line) or "report.AppendLine" in line and "present" in line,
                    f"the key is not written anywhere: {line.strip()}")
    require("Console." not in source and "Debug." not in source, "no console or debug output")
    require("info.EnvironmentVariables[KeyVariable] = key" in source and "only into the app's own environment" in source, "the key goes only into the app's process environment")
    require(source.count("StreamWriter(") == 1 and "launcher.log" in source, "the only log is the server's own output")


def test_the_source_is_csharp_5_and_the_scripts_are_safe_for_windows_powershell() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    require("$\"" not in source and "?." not in re.sub(r'"[^"]*"|//.*', "", source) and "nameof(" not in source and "=>" not in source, "only C# 5 syntax: the compiler that ships with Windows is C# 5")
    for name in ("build_launcher.ps1", "install_shortcut.ps1"):
        data = (DESKTOP / name).read_bytes()
        require(data.startswith(b"\xef\xbb\xbf"), f"{name} has a BOM: Windows PowerShell 5 reads accents correctly")
    require("/codepage:65001" in (DESKTOP / "build_launcher.ps1").read_text(encoding="utf-8-sig"), "the source is compiled as UTF-8 (accents in the messages)")
    shortcut = (DESKTOP / "install_shortcut.ps1").read_text(encoding="utf-8-sig")
    require("-Remove" in shortcut and "root.txt" in shortcut and "CreateShortcut" in shortcut and "Remove-Item $link" in shortcut, "installs and removes only its own shortcut")
    require("SCOUT_FINANCE" not in shortcut.replace("SCOUT_FINANCE_ROOT", "") and "API_KEY" not in shortcut + (DESKTOP / "build_launcher.ps1").read_text(encoding="utf-8-sig"), "the scripts never touch a key")
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    require("desktop/*.exe" in ignore, "the built program is not committed")


def test_the_icon_has_every_size_windows_asks_for() -> None:
    from PIL import Image

    icon = Image.open(DESKTOP / "scout_finance.ico")
    sizes = set(icon.info.get("sizes", {icon.size}))
    require({(16, 16), (32, 32), (48, 48), (256, 256)} <= sizes, f"icon sizes: {sorted(sizes)}")


def test_a_real_build_reports_the_setup_and_never_the_key() -> None:
    if sys.platform != "win32" or not CSC.exists():
        print("SKIP: no Windows .NET Framework compiler here, the real build was not tested")
        return
    with tempfile.TemporaryDirectory() as tmp:
        exe = Path(tmp) / "Scout Finance.exe"
        built = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(DESKTOP / "build_launcher.ps1"), "-Output", str(exe)], capture_output=True, text=True)
        require(built.returncode == 0 and exe.exists() and exe.stat().st_size > 10_000, f"it compiles: {built.stdout[-200:]} {built.stderr[-200:]}")
        report = Path(tmp) / "report.txt"
        env = dict(os.environ) | {"SCOUT_FINANCE_ROOT": str(ROOT), "SCOUT_FINANCE_COINGECKO_API_KEY": FAKE_KEY}
        done = subprocess.run([str(exe), "--check", str(report)], env=env, timeout=60)
        text = report.read_text(encoding="utf-8")
        lines = dict(line.split("=", 1) for line in text.splitlines() if "=" in line)
        require(lines["root"] == str(ROOT) and lines["key"] == "present", f"it finds the project and says the key exists: {lines}")
        require(FAKE_KEY not in text and "CG-" not in text, "the report never contains the key")
        require(done.returncode in (0, 1) and (done.returncode == 0) == (lines["python"] == "ok" and not lines["browser"].startswith("NOT FOUND")), "the exit code follows the setup")
        env.pop("SCOUT_FINANCE_COINGECKO_API_KEY")
        env["SCOUT_FINANCE_ROOT"] = str(Path(tmp))  # no project there: falls back to the exe's own folder and then root.txt
        subprocess.run([str(exe), "--check", str(report)], env=env, timeout=60)
        text = report.read_text(encoding="utf-8")
        require("root=NOT FOUND" in text or "root=" in text, "a wrong root does not crash it")


CASES = [
    test_the_launcher_starts_the_current_app_on_loopback_only,
    test_the_key_is_never_printed_logged_or_written,
    test_the_source_is_csharp_5_and_the_scripts_are_safe_for_windows_powershell,
    test_the_icon_has_every_size_windows_asks_for,
    test_a_real_build_reports_the_setup_and_never_the_key,
]


def main() -> int:
    for case in CASES:
        case()
    print("v2.50M desktop launcher QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
