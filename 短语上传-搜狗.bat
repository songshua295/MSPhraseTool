@echo off
chcp 65001 >nul
main.py convert -i "C:\Users\t295\Downloads\PhraseEdit.txt" -f sg -o out
main.py upload
pause
