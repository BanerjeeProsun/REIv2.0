Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd /d C:\Users\Prosun\Desktop\Work\REIv2.0 && uv run python src\rei\main.py", 0, False
