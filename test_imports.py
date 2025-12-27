# -*- coding: utf-8 -*-
"""Teste rápido de imports"""
import sys
import io

# Configura encoding para UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    from flask import Flask
    print("OK - Flask importado com sucesso")
except ImportError as e:
    print(f"ERRO - Erro ao importar Flask: {e}")

try:
    from src.historico import HistoricoLotofacil
    print("OK - HistoricoLotofacil importado com sucesso")
except ImportError as e:
    print(f"ERRO - Erro ao importar HistoricoLotofacil: {e}")

try:
    from src.analise import AnalisadorLotofacil
    print("OK - AnalisadorLotofacil importado com sucesso")
except ImportError as e:
    print(f"ERRO - Erro ao importar AnalisadorLotofacil: {e}")

try:
    from src.fechamento import GeradorFechamento
    print("OK - GeradorFechamento importado com sucesso")
except ImportError as e:
    print(f"ERRO - Erro ao importar GeradorFechamento: {e}")

print("\nTeste de imports concluido!")

