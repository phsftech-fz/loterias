@echo off
echo ========================================
echo Sistema para sustentar o Girinho com a Loto Facil
echo ========================================
echo.
echo Iniciando servidor web...
echo.
echo Acesse: http://localhost:5000
echo.
echo Pressione Ctrl+C para parar o servidor
echo.

python app.py

if %errorlevel% neq 0 (
    echo.
    echo Erro ao executar o sistema.
    echo Verifique se o Python esta instalado e as dependencias foram instaladas.
    echo.
    pause
)

