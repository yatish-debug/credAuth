@echo off
title CredVerify - Windows 10/11 Setup and Launcher
echo Starting CredVerify Platform Setup...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup-windows.ps1" %*
pause
