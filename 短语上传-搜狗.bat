@echo off
chcp 65001 >nul
python main.py convert -i "C:\Users\t295\Downloads\PhraseEdit.txt" -f sg -o out
python main.py upload
pause
