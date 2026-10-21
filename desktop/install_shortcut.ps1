<#
  Builds the launcher (if needed) and puts a "Scout Finance" shortcut with its icon on the Windows desktop.
  Usage (from the project folder):  powershell -ExecutionPolicy Bypass -File desktop\install_shortcut.ps1
  Add -Rebuild to compile again, and -Remove to delete the shortcut. It never touches the app, its data or any key.
  (-Directory puts the shortcut somewhere else than the desktop and -NoRemember skips root.txt: both are for the automatic test.)

  The shortcut is written through the Unicode shell-link interface, not WScript.Shell: that one only understands ANSI paths and fails when the
  project folder name has an emoji or a character outside the system code page.
#>
param([switch]$Rebuild, [switch]$Remove, [string]$Directory = "", [switch]$NoRemember)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $here
$exe = Join-Path $here "Scout Finance.exe"
if (-not $Directory) { $Directory = [Environment]::GetFolderPath("Desktop") }
$link = Join-Path $Directory "Scout Finance.lnk"

if ($Remove) {
    if (Test-Path -LiteralPath $link) { Remove-Item -LiteralPath $link; Write-Host "Acceso directo eliminado: $link" } else { Write-Host "No había acceso directo." }
    return
}

if ($Rebuild -or -not (Test-Path -LiteralPath $exe)) { & (Join-Path $here "build_launcher.ps1") }

if (-not $NoRemember) {
    # the launcher normally finds the project next to itself; this is the fallback if the .exe is ever moved
    $data = Join-Path $env:LOCALAPPDATA "ScoutFinance"
    New-Item -ItemType Directory -Force $data | Out-Null
    [IO.File]::WriteAllText((Join-Path $data "root.txt"), $root, (New-Object Text.UTF8Encoding($false)))
}

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
using System.Text;

public static class ScoutShellLink
{
    [ComImport, Guid("00021401-0000-0000-C000-000000000046")]
    private class CShellLink { }

    [ComImport, InterfaceType(ComInterfaceType.InterfaceIsIUnknown), Guid("000214F9-0000-0000-C000-000000000046")]
    private interface IShellLinkW
    {
        void GetPath([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder file, int max, IntPtr data, uint flags);
        void GetIDList(out IntPtr list);
        void SetIDList(IntPtr list);
        void GetDescription([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder name, int max);
        void SetDescription([MarshalAs(UnmanagedType.LPWStr)] string name);
        void GetWorkingDirectory([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder dir, int max);
        void SetWorkingDirectory([MarshalAs(UnmanagedType.LPWStr)] string dir);
        void GetArguments([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder args, int max);
        void SetArguments([MarshalAs(UnmanagedType.LPWStr)] string args);
        void GetHotkey(out short hotkey);
        void SetHotkey(short hotkey);
        void GetShowCmd(out int show);
        void SetShowCmd(int show);
        void GetIconLocation([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder path, int max, out int index);
        void SetIconLocation([MarshalAs(UnmanagedType.LPWStr)] string path, int index);
        void SetRelativePath([MarshalAs(UnmanagedType.LPWStr)] string path, uint reserved);
        void Resolve(IntPtr window, uint flags);
        void SetPath([MarshalAs(UnmanagedType.LPWStr)] string file);
    }

    [ComImport, InterfaceType(ComInterfaceType.InterfaceIsIUnknown), Guid("0000010B-0000-0000-C000-000000000046")]
    private interface IPersistFile
    {
        void GetClassID(out Guid id);
        [PreserveSig] int IsDirty();
        void Load([MarshalAs(UnmanagedType.LPWStr)] string file, uint mode);
        void Save([MarshalAs(UnmanagedType.LPWStr)] string file, [MarshalAs(UnmanagedType.Bool)] bool remember);
        void SaveCompleted([MarshalAs(UnmanagedType.LPWStr)] string file);
        void GetCurFile([MarshalAs(UnmanagedType.LPWStr)] out string file);
    }

    public static void Create(string link, string target, string workingDirectory, string icon, string description)
    {
        IShellLinkW shell = (IShellLinkW)new CShellLink();
        shell.SetPath(target);
        shell.SetWorkingDirectory(workingDirectory);
        shell.SetIconLocation(icon, 0);
        shell.SetDescription(description);
        ((IPersistFile)shell).Save(link, true);
    }
}
"@

New-Item -ItemType Directory -Force $Directory | Out-Null
[ScoutShellLink]::Create($link, $exe, $root, (Join-Path $here "scout_finance.ico"), "Scout Finance: investigación local de mercados")
Write-Host "Acceso directo creado: $link"
