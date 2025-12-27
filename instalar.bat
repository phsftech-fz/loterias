@echo off
echo ========================================
echo Instalador - Sistema Lotofacil
echo ========================================
echo.

REM Verifica se Python esta instalado
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo Python encontrado!
    echo.
    echo Instalando dependencias...
    python -m pip install -r requirements.txt
    if %errorlevel% == 0 (
        echo.
        echo ========================================
        echo Instalacao concluida com sucesso!
        echo ========================================
        echo.
        echo Para executar o sistema, use:
        echo   python app.py
        echo.
    ) else (
        echo.
        echo Erro ao instalar dependencias.
        echo Tente executar como Administrador.
    )
) else (
    echo Python nao encontrado!
    echo.
    echo Por favor, instale o Python primeiro:
    echo 1. Acesse: https://www.python.org/downloads/
    echo 2. Baixe e instale o Python 3.11 ou superior
    echo 3. IMPORTANTE: Marque "Add Python to PATH" durante a instalacao
    echo 4. Reinicie o terminal e execute este script novamente
    echo.
    pause
)

