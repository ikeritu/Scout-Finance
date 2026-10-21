// Scout Finance desktop launcher (v2.50M). A tiny native Windows program (no Python, no console window) that:
//   1. finds the project folder (next to this .exe or in a parent, or the path in %LOCALAPPDATA%\ScoutFinance\root.txt),
//   2. starts the app with the project's own .venv on a free local port, with no console window,
//   3. opens it in its own app window (Google Chrome or Microsoft Edge in --app mode, with a profile of its own),
//   4. stops the server when that window is closed.
// It never writes or prints the CoinGecko key: if the key is only in the user's registry environment it is passed to the app's process
// environment and nowhere else. Compiled with the .NET Framework compiler that ships with Windows (see build_launcher.ps1): C# 5 syntax only.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Management;
using System.Net;
using System.Net.Sockets;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Windows.Forms;
using Microsoft.Win32;

namespace ScoutFinance
{
    internal static class Launcher
    {
        const string AppFile = "app_v2_37.py";
        const string KeyVariable = "SCOUT_FINANCE_COINGECKO_API_KEY";
        const string MutexName = "Local\\ScoutFinanceDesktopLauncher";
        const int StartupSeconds = 120;

        [DllImport("user32.dll")]
        static extern bool SetProcessDPIAware();

        static Process server;
        static StreamWriter log;
        static readonly object logLock = new object();

        [STAThread]
        static int Main(string[] args)
        {
            try { SetProcessDPIAware(); } catch (Exception) { }
            if (args.Length >= 1 && args[0] == "--check")
            {
                return Check(args.Length >= 2 ? args[1] : null);
            }
            bool createdNew;
            using (Mutex mutex = new Mutex(true, MutexName, out createdNew))
            {
                if (!createdNew)
                {
                    MessageBox.Show("Scout Finance ya está abierto.", "Scout Finance", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    return 0;
                }
                try
                {
                    return Run();
                }
                catch (Exception error)
                {
                    StopServer();
                    MessageBox.Show("Scout Finance no ha podido iniciarse (" + error.GetType().Name + "): " + error.Message, "Scout Finance", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    return 1;
                }
            }
        }

        // ------------------------------------------------------------------------------------------------------------------ discovery

        static string DataFolder()
        {
            string folder = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "ScoutFinance");
            Directory.CreateDirectory(folder);
            return folder;
        }

        static string FindRoot()
        {
            string fromEnv = Environment.GetEnvironmentVariable("SCOUT_FINANCE_ROOT");
            if (!string.IsNullOrEmpty(fromEnv) && File.Exists(Path.Combine(fromEnv, AppFile))) return fromEnv;
            string folder = AppDomain.CurrentDomain.BaseDirectory;
            for (int level = 0; level < 5 && !string.IsNullOrEmpty(folder); level++)
            {
                if (File.Exists(Path.Combine(folder, AppFile))) return folder.TrimEnd('\\');
                DirectoryInfo parent = Directory.GetParent(folder.TrimEnd('\\'));
                folder = parent == null ? null : parent.FullName;
            }
            string remembered = Path.Combine(DataFolder(), "root.txt");
            if (File.Exists(remembered))
            {
                string path = File.ReadAllText(remembered, Encoding.UTF8).Trim();
                if (File.Exists(Path.Combine(path, AppFile))) return path;
            }
            return null;
        }

        static string FindBrowser()
        {
            string local = Environment.GetEnvironmentVariable("LOCALAPPDATA") ?? "";
            // Chrome first: on the development PC an Edge app window in a fresh profile closed itself after ~7 s, Chrome's did not.
            string[] candidates = new string[]
            {
                @"C:\Program Files\Google\Chrome\Application\chrome.exe",
                @"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                Path.Combine(local, @"Google\Chrome\Application\chrome.exe"),
                @"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                @"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            };
            foreach (string candidate in candidates) if (File.Exists(candidate)) return candidate;
            return null;
        }

        // The key may exist only in the user's registry environment (a shortcut started before it was saved does not see it).
        static string UserKey()
        {
            string value = Environment.GetEnvironmentVariable(KeyVariable);
            if (!string.IsNullOrEmpty(value)) return value;
            using (RegistryKey environment = Registry.CurrentUser.OpenSubKey("Environment"))
            {
                object stored = environment == null ? null : environment.GetValue(KeyVariable);
                return stored as string;
            }
        }

        static int FreePort()
        {
            TcpListener listener = new TcpListener(IPAddress.Loopback, 0);
            listener.Start();
            int port = ((IPEndPoint)listener.LocalEndpoint).Port;
            listener.Stop();
            return port;
        }

        static int Check(string outputFile)
        {
            string root = FindRoot();
            string python = root == null ? null : Path.Combine(root, @".venv\Scripts\python.exe");
            string browser = FindBrowser();
            bool pythonOk = python != null && File.Exists(python);
            StringBuilder report = new StringBuilder();
            report.AppendLine("root=" + (root ?? "NOT FOUND"));
            report.AppendLine("python=" + (pythonOk ? "ok" : "MISSING"));
            report.AppendLine("browser=" + (browser ?? "NOT FOUND"));
            report.AppendLine("key=" + (string.IsNullOrEmpty(UserKey()) ? "absent" : "present"));  // only whether it exists, never its value
            if (!string.IsNullOrEmpty(outputFile)) File.WriteAllText(outputFile, report.ToString(), new UTF8Encoding(false));
            return root != null && pythonOk && browser != null ? 0 : 1;
        }

        // ------------------------------------------------------------------------------------------------------------------ the run

        static int Run()
        {
            string root = FindRoot();
            if (root == null)
            {
                MessageBox.Show("No encuentro la carpeta de Scout Finance. Deja este programa dentro de la carpeta del proyecto (o ejecuta desktop\\install_shortcut.ps1 otra vez).", "Scout Finance", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return 1;
            }
            string python = Path.Combine(root, @".venv\Scripts\python.exe");
            if (!File.Exists(python))
            {
                MessageBox.Show("Falta el entorno de la aplicación (.venv). Ejecuta una vez INICIAR_SCOUT_FINANCE.bat para prepararlo.", "Scout Finance", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return 1;
            }
            string browser = FindBrowser();
            if (browser == null)
            {
                MessageBox.Show("Necesito Google Chrome o Microsoft Edge para abrir la ventana de la aplicación.", "Scout Finance", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return 1;
            }

            int port = FreePort();
            string url = "http://127.0.0.1:" + port;  // not "localhost": that resolves to IPv6 first and the app listens on IPv4 only
            string marker = "--scout-finance-window=" + port;  // a harmless flag that lets us recognise our own browser processes
            string profile = Path.Combine(DataFolder(), "app-window-profile");
            log = new StreamWriter(Path.Combine(DataFolder(), "launcher.log"), false, new UTF8Encoding(false));
            log.AutoFlush = true;

            AppDomain.CurrentDomain.ProcessExit += delegate { StopServer(); };
            StartServer(python, root, port);

            Form splash = BuildSplash();
            splash.Show();
            Application.DoEvents();
            DateTime started = DateTime.UtcNow;
            while (!Healthy(url))
            {
                if (server.HasExited)
                {
                    splash.Close();
                    MessageBox.Show("La aplicación se ha detenido al arrancar. El registro está en:\n" + Path.Combine(DataFolder(), "launcher.log"), "Scout Finance", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    return 1;
                }
                if ((DateTime.UtcNow - started).TotalSeconds > StartupSeconds)
                {
                    splash.Close();
                    StopServer();
                    MessageBox.Show("La aplicación tarda demasiado en arrancar. El registro está en:\n" + Path.Combine(DataFolder(), "launcher.log"), "Scout Finance", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    return 1;
                }
                Application.DoEvents();
                Thread.Sleep(250);
            }

            ProcessStartInfo window = new ProcessStartInfo(browser);
            window.Arguments = "--app=" + url + " --user-data-dir=\"" + profile + "\" --no-first-run --no-default-browser-check --window-size=1360,900 " + marker;
            window.UseShellExecute = false;
            Process.Start(window);
            splash.Hide();

            // The app lives as long as its window: when no browser process with our marker is left, stop the server.
            bool seen = false;
            int goneChecks = 0;
            DateTime opened = DateTime.UtcNow;
            while (true)
            {
                Thread.Sleep(1000);
                Application.DoEvents();
                if (server.HasExited)
                {
                    KillBrowser(marker);
                    MessageBox.Show("La aplicación se ha detenido. El registro está en:\n" + Path.Combine(DataFolder(), "launcher.log"), "Scout Finance", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    return 1;
                }
                int alive = BrowserProcesses(marker).Count;
                if (alive > 0) { seen = true; goneChecks = 0; continue; }
                goneChecks++;
                if ((seen && goneChecks >= 2) || (!seen && (DateTime.UtcNow - opened).TotalSeconds > 30)) break;
            }
            StopServer();
            return 0;
        }

        static Form BuildSplash()
        {
            Form form = new Form();
            form.Text = "Scout Finance";
            form.FormBorderStyle = FormBorderStyle.FixedDialog;
            form.StartPosition = FormStartPosition.CenterScreen;
            form.MaximizeBox = false;
            form.MinimizeBox = false;
            form.ControlBox = false;
            form.ClientSize = new Size(380, 110);
            form.TopMost = true;
            try { form.Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath); } catch (Exception) { }
            Label label = new Label();
            label.Text = "Abriendo Scout Finance…\nLa primera vez puede tardar unos segundos.";
            label.Font = new Font("Segoe UI", 10f);
            label.AutoSize = false;
            label.Location = new Point(16, 14);
            label.Size = new Size(348, 44);
            form.Controls.Add(label);
            ProgressBar bar = new ProgressBar();
            bar.Style = ProgressBarStyle.Marquee;
            bar.MarqueeAnimationSpeed = 30;
            bar.Location = new Point(16, 68);
            bar.Size = new Size(348, 16);
            form.Controls.Add(bar);
            return form;
        }

        // ------------------------------------------------------------------------------------------------------------------ the server

        static void StartServer(string python, string root, int port)
        {
            ProcessStartInfo info = new ProcessStartInfo(python);
            info.Arguments = "-m streamlit run \"" + AppFile + "\" --server.headless true --server.address 127.0.0.1 --server.port " + port + " --browser.gatherUsageStats false";
            info.WorkingDirectory = root;
            info.UseShellExecute = false;
            info.CreateNoWindow = true;
            info.RedirectStandardOutput = true;
            info.RedirectStandardError = true;
            info.StandardOutputEncoding = Encoding.UTF8;
            info.StandardErrorEncoding = Encoding.UTF8;
            string key = UserKey();
            if (!string.IsNullOrEmpty(key)) info.EnvironmentVariables[KeyVariable] = key;  // only into the app's own environment
            server = new Process();
            server.StartInfo = info;
            server.OutputDataReceived += delegate (object sender, DataReceivedEventArgs e) { Write(e.Data); };
            server.ErrorDataReceived += delegate (object sender, DataReceivedEventArgs e) { Write(e.Data); };
            server.Start();
            server.BeginOutputReadLine();
            server.BeginErrorReadLine();
        }

        static void Write(string line)
        {
            if (line == null || log == null) return;
            lock (logLock) { try { log.WriteLine(line); } catch (Exception) { } }
        }

        static bool Healthy(string url)
        {
            try
            {
                HttpWebRequest request = (HttpWebRequest)WebRequest.Create(url + "/_stcore/health");
                request.Timeout = 1000;
                using (HttpWebResponse response = (HttpWebResponse)request.GetResponse())
                    return response.StatusCode == HttpStatusCode.OK;
            }
            catch (Exception) { return false; }
        }

        static void StopServer()
        {
            try
            {
                if (server != null && !server.HasExited)
                {
                    ProcessStartInfo kill = new ProcessStartInfo("taskkill", "/PID " + server.Id + " /T /F");
                    kill.CreateNoWindow = true;
                    kill.UseShellExecute = false;
                    Process.Start(kill).WaitForExit(5000);
                }
            }
            catch (Exception) { }
        }

        // ------------------------------------------------------------------------------------------------------------------ the window

        static List<int> BrowserProcesses(string marker)
        {
            List<int> ids = new List<int>();
            try
            {
                using (ManagementObjectSearcher searcher = new ManagementObjectSearcher("SELECT ProcessId FROM Win32_Process WHERE CommandLine LIKE '%" + marker + "%'"))
                    foreach (ManagementBaseObject item in searcher.Get()) ids.Add(Convert.ToInt32(item["ProcessId"]));
            }
            catch (Exception) { }
            return ids;
        }

        static void KillBrowser(string marker)
        {
            foreach (int id in BrowserProcesses(marker))
            {
                try { Process.GetProcessById(id).Kill(); } catch (Exception) { }
            }
        }
    }
}
