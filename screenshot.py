import os, ImageGrab, subprocess

_nirCmd = (
	os.path.abspath(os.path.dirname(__file__)) + os.sep + 'nircmd' + os.sep + 'nircmd.exe',
	'savescreenshot',
	'*clipboard*'
)
_cmdFlags = subprocess.STARTUPINFO()
_cmdFlags.dwFlags |= subprocess.STARTF_USESHOWWINDOW
def screenshot():
	subprocess.Popen(_nirCmd, startupinfo=_cmdFlags).communicate()
	return ImageGrab.grabclipboard()
