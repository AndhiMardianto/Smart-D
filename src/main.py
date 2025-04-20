import wx
import subprocess
import os
import threading
import re
import sys 

class YTDownloader(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Smart Downloader", size=(400, 350))

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.url_label = wx.StaticText(panel, label="Masukkan Link")
        vbox.Add(self.url_label, flag=wx.LEFT | wx.TOP, border=10)
        self.url_input = wx.TextCtrl(panel)
        vbox.Add(self.url_input, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        self.format_label = wx.StaticText(panel, label="Pilih Format:")
        vbox.Add(self.format_label, flag=wx.LEFT | wx.TOP, border=10)
        self.format_choice = wx.ComboBox(panel, choices=["Video", "Audio"], style=wx.CB_READONLY)
        self.format_choice.SetSelection(0)
        vbox.Add(self.format_choice, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        self.download_button = wx.Button(panel, label="Download")
        vbox.Add(self.download_button, flag=wx.ALL | wx.EXPAND, border=10)
        self.download_button.Bind(wx.EVT_BUTTON, self.on_download)

        self.progress_label = wx.StaticText(panel, label="Sedang Mendownload... Sabar ya guys!")
        vbox.Add(self.progress_label, flag=wx.LEFT | wx.TOP, border=10)
        self.progress_bar = wx.Gauge(panel, range=100, size=(-1, 20))
        vbox.Add(self.progress_bar, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)

        panel.SetSizer(vbox)
        self.Centre()

        # Lokasi folder aplikasi tergantung running dari source atau exe
        if getattr(sys, 'frozen', False):
            self.script_dir = os.path.dirname(sys.executable)
        else:
            self.script_dir = os.path.dirname(os.path.abspath(__file__))

        self.ytdlp_path = os.path.join(self.script_dir, "yt-dlp.exe")
        self.ffmpeg_path = os.path.join(self.script_dir, "ffmpeg.exe")

    def on_download(self, event):
        url = self.url_input.GetValue().strip()
        if not url:
            wx.MessageBox("Harap masukkan Link!", "Peringatan", wx.ICON_WARNING)
            return

        format_choice = self.format_choice.GetValue()
        download_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        command = self.get_command(url, format_choice, download_folder)

        self.progress_bar.SetValue(0)
        self.download_button.Disable()
        self.progress_bar.SetFocus()

        threading.Thread(target=self.run_download, args=(command,), daemon=True).start()

    def get_command(self, url, format_choice, download_folder):
        output_template = os.path.join(download_folder, "%(title).50s.%(ext)s")
        if format_choice == "Video":
            args = [self.ytdlp_path, "--ffmpeg-location", self.ffmpeg_path, "--restrict-filenames",
                    "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4", url, "-o", output_template]
        else:
            args = [self.ytdlp_path, "--ffmpeg-location", self.ffmpeg_path, "-f", "bestaudio",
                    "--extract-audio", "--audio-format", "mp3", "--restrict-filenames", url, "-o", output_template]
        return args

    def run_download(self, command):
        env = os.environ.copy()
        env["PATH"] = self.script_dir + os.pathsep + env.get("PATH", "")

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
            startupinfo=startupinfo
        )

        for line in process.stdout:
            wx.CallAfter(self.update_progress, line)

        process.wait()
        wx.CallAfter(self.download_finished, process.returncode)

    def update_progress(self, output):
        match = re.search(r"(\d+)%", output)
        if match:
            percent = int(match.group(1))
            self.progress_bar.SetValue(percent)
            self.progress_bar.SetToolTip(f"{percent}%")

    def download_finished(self, returncode):
        self.progress_bar.SetValue(100)
        if returncode == 0:
            wx.MessageBox("Download Selesai! Lihat di folder Download kamu.", "Sukses", wx.ICON_INFORMATION)
        else:
            wx.MessageBox("Download Gagal! LINK atau format tidak didukung.", "Gagal", wx.ICON_ERROR)
        self.download_button.Enable()

if __name__ == "__main__":
    app = wx.App(False)
    frame = YTDownloader()
    frame.Show()
    app.MainLoop()
