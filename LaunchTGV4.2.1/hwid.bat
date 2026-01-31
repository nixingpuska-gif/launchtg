@echo off
powershell -Command "Get-CimInstance -Class Win32_ComputerSystemProduct | Select-Object -Property UUID"
pause