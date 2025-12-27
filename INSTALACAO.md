# Guia de Instalação - Sistema Lotofácil

## 📋 Pré-requisitos

Este sistema requer **Python 3.8 ou superior**.

## 🔧 Instalação do Python

### Opção 1: Instalação via Microsoft Store (Recomendado para Windows)

1. Abra a **Microsoft Store** no Windows
2. Procure por **"Python 3.11"** ou **"Python 3.12"**
3. Clique em **Instalar**
4. Após a instalação, reinicie o terminal/PowerShell

### Opção 2: Download Direto

1. Acesse: https://www.python.org/downloads/
2. Baixe a versão mais recente do Python (3.11 ou 3.12)
3. **IMPORTANTE**: Durante a instalação, marque a opção **"Add Python to PATH"**
4. Complete a instalação
5. Reinicie o terminal/PowerShell

### Opção 3: Via Chocolatey (se você tem Chocolatey instalado)

```powershell
choco install python
```

## ✅ Verificar Instalação

Após instalar o Python, verifique se está funcionando:

```powershell
python --version
```

ou

```powershell
py --version
```

Você deve ver algo como: `Python 3.11.x` ou `Python 3.12.x`

## 📦 Instalar Dependências

Após o Python estar instalado, execute:

```powershell
python -m pip install -r requirements.txt
```

ou, se `python` não funcionar:

```powershell
py -m pip install -r requirements.txt
```

## 🚀 Executar o Sistema

Após instalar as dependências:

```powershell
python app.py
```

ou

```powershell
py app.py
```

## ❓ Problemas Comuns

### "pip não é reconhecido"

Use:
```powershell
python -m pip install -r requirements.txt
```

### "python não é reconhecido"

1. Verifique se o Python está instalado
2. Verifique se marcou "Add Python to PATH" durante a instalação
3. Reinicie o terminal/PowerShell
4. Tente usar `py` ao invés de `python`

### Erro de permissão

Execute o PowerShell como Administrador:
- Clique com botão direito no PowerShell
- Selecione "Executar como administrador"

## 📞 Precisa de Ajuda?

Se continuar com problemas:
1. Verifique se o Python está no PATH do sistema
2. Tente reinstalar o Python marcando "Add Python to PATH"
3. Reinicie completamente o computador após a instalação

