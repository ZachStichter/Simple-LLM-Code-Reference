@echo off
start /min "Ollama TTS Server" %1\ollama.exe serve
exit