"""
Módulo para gerenciar banco de dados de concursos
"""
import sqlite3
import json
import os
from typing import List, Dict, Optional
from datetime import datetime


class DatabaseLotofacil:
    """Classe para gerenciar banco de dados de concursos da Lotofácil"""
    
    def __init__(self, db_path: str = "data/lotofacil.db"):
        self.db_path = db_path
        self._criar_diretorio()
        self._criar_tabelas()
    
    def _criar_diretorio(self):
        """Cria diretório de dados se não existir"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def _criar_tabelas(self):
        """Cria tabelas necessárias no banco de dados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de concursos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS concursos (
                numero INTEGER PRIMARY KEY,
                data_apuracao TEXT,
                numeros TEXT NOT NULL,
                data_insercao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Índice para busca rápida
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_numero ON concursos(numero)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_data ON concursos(data_apuracao)
        ''')
        
        conn.commit()
        conn.close()
    
    def inserir_concurso(self, concurso: Dict) -> bool:
        """
        Insere ou atualiza um concurso no banco
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            numero = concurso.get('concurso')
            data = concurso.get('data', '')
            numeros = json.dumps(concurso.get('numeros', []))
            
            cursor.execute('''
                INSERT OR REPLACE INTO concursos 
                (numero, data_apuracao, numeros, data_atualizacao)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (numero, data, numeros))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao inserir concurso {concurso.get('concurso')}: {e}")
            return False
    
    def inserir_concursos(self, concursos: List[Dict]) -> int:
        """
        Insere múltiplos concursos de uma vez (mais eficiente)
        Retorna quantidade de concursos inseridos
        """
        if not concursos:
            return 0
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            inseridos = 0
            for concurso in concursos:
                try:
                    numero = concurso.get('concurso')
                    data = concurso.get('data', '')
                    numeros = json.dumps(concurso.get('numeros', []))
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO concursos 
                        (numero, data_apuracao, numeros, data_atualizacao)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (numero, data, numeros))
                    inseridos += 1
                except Exception as e:
                    continue
            
            conn.commit()
            conn.close()
            return inseridos
        except Exception as e:
            print(f"Erro ao inserir concursos: {e}")
            return 0
    
    def obter_concurso(self, numero: int) -> Optional[Dict]:
        """Obtém um concurso específico pelo número"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT numero, data_apuracao, numeros 
                FROM concursos 
                WHERE numero = ?
            ''', (numero,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'concurso': row[0],
                    'data': row[1] or '',
                    'numeros': json.loads(row[2])
                }
            return None
        except Exception as e:
            print(f"Erro ao obter concurso {numero}: {e}")
            return None
    
    def obter_todos_concursos(self, limite: Optional[int] = None, ordenar_desc: bool = True) -> List[Dict]:
        """
        Obtém todos os concursos do banco
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            ordem = "DESC" if ordenar_desc else "ASC"
            query = f'SELECT numero, data_apuracao, numeros FROM concursos ORDER BY numero {ordem}'
            
            if limite:
                query += f' LIMIT {limite}'
            
            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()
            
            concursos = []
            for row in rows:
                concursos.append({
                    'concurso': row[0],
                    'data': row[1] or '',
                    'numeros': json.loads(row[2])
                })
            
            # Se ordenou DESC, inverte para ter ordem crescente
            if ordenar_desc:
                concursos.reverse()
            
            return concursos
        except Exception as e:
            print(f"Erro ao obter concursos: {e}")
            return []
    
    def obter_ultimos_concursos(self, quantidade: int = 100) -> List[Dict]:
        """Obtém os últimos N concursos"""
        return self.obter_todos_concursos(limite=quantidade, ordenar_desc=True)
    
    def obter_ultimo_concurso(self) -> Optional[Dict]:
        """Obtém o último concurso (maior número)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT numero, data_apuracao, numeros 
                FROM concursos 
                ORDER BY numero DESC 
                LIMIT 1
            ''')
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'concurso': row[0],
                    'data': row[1] or '',
                    'numeros': json.loads(row[2])
                }
            return None
        except Exception as e:
            print(f"Erro ao obter último concurso: {e}")
            return None
    
    def contar_concursos(self) -> int:
        """Retorna o total de concursos no banco"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM concursos')
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
        except Exception as e:
            print(f"Erro ao contar concursos: {e}")
            return 0
    
    def obter_concursos_por_periodo(self, data_inicio: str, data_fim: str) -> List[Dict]:
        """
        Obtém concursos em um período específico
        Formato de data: 'YYYY-MM-DD'
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT numero, data_apuracao, numeros 
                FROM concursos 
                WHERE data_apuracao >= ? AND data_apuracao <= ?
                ORDER BY numero ASC
            ''', (data_inicio, data_fim))
            
            rows = cursor.fetchall()
            conn.close()
            
            concursos = []
            for row in rows:
                concursos.append({
                    'concurso': row[0],
                    'data': row[1] or '',
                    'numeros': json.loads(row[2])
                })
            
            return concursos
        except Exception as e:
            print(f"Erro ao obter concursos por período: {e}")
            return []
    
    def verificar_concurso_existe(self, numero: int) -> bool:
        """Verifica se um concurso já existe no banco"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT 1 FROM concursos WHERE numero = ? LIMIT 1', (numero,))
            existe = cursor.fetchone() is not None
            conn.close()
            
            return existe
        except Exception as e:
            return False
    
    def obter_concursos_faltantes(self, ultimo_numero: int, limite: int = 1000) -> List[int]:
        """
        Retorna lista de números de concursos que faltam no banco
        Útil para identificar quais concursos precisam ser buscados
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Obtém todos os números que existem
            cursor.execute('SELECT numero FROM concursos')
            numeros_existentes = set(row[0] for row in cursor.fetchall())
            conn.close()
            
            # Gera lista de números esperados
            numeros_esperados = set(range(max(1, ultimo_numero - limite + 1), ultimo_numero + 1))
            
            # Retorna os que faltam
            faltantes = sorted(list(numeros_esperados - numeros_existentes))
            return faltantes
        except Exception as e:
            print(f"Erro ao verificar concursos faltantes: {e}")
            return []
    
    def limpar_banco(self):
        """Remove todos os concursos do banco (cuidado!)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM concursos')
            conn.commit()
            conn.close()
            print("Banco de dados limpo com sucesso")
        except Exception as e:
            print(f"Erro ao limpar banco: {e}")

