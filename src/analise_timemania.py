"""
Módulo de análise de padrões e estatísticas dos resultados da Timemania
"""
from typing import List, Dict, Tuple
from collections import Counter, defaultdict


class AnalisadorTimemania:
    """Classe para analisar padrões nos resultados da Timemania"""
    
    def __init__(self, historico: List[Dict]):
        self.historico = historico
        self.numeros_range = range(1, 81)  # Timemania: 1 a 80
    
    def frequencia_numeros(self) -> Dict[int, int]:
        """Calcula frequência de cada número nos concursos"""
        frequencias = Counter()
        for concurso in self.historico:
            for numero in concurso['numeros']:
                frequencias[numero] += 1
        return dict(frequencias)
    
    def numeros_mais_sorteados(self, top: int = 20) -> List[Tuple[int, int]]:
        """Retorna os N números mais sorteados"""
        freq = self.frequencia_numeros()
        return sorted(freq.items(), key=lambda x: x[1], reverse=True)[:top]
    
    def numeros_menos_sorteados(self, top: int = 20) -> List[Tuple[int, int]]:
        """Retorna os N números menos sorteados"""
        freq = self.frequencia_numeros()
        return sorted(freq.items(), key=lambda x: x[1])[:top]
    
    def calcular_atraso(self) -> Dict[int, int]:
        """Calcula quantos concursos cada número está atrasado"""
        atrasos = {num: 0 for num in self.numeros_range}
        ultima_aparicao = {num: -1 for num in self.numeros_range}
        
        for idx, concurso in enumerate(self.historico):
            for numero in concurso['numeros']:
                ultima_aparicao[numero] = idx
        
        ultimo_concurso_idx = len(self.historico) - 1
        for numero in self.numeros_range:
            if ultima_aparicao[numero] >= 0:
                atrasos[numero] = ultimo_concurso_idx - ultima_aparicao[numero]
            else:
                atrasos[numero] = ultimo_concurso_idx + 1
        
        return atrasos
    
    def get_estatisticas_completas(self) -> Dict:
        """Retorna estatísticas completas"""
        freq = self.frequencia_numeros()
        atrasos = self.calcular_atraso()
        
        # Números quentes (mais sorteados recentemente)
        numeros_quentes = [num for num, _ in self.numeros_mais_sorteados(20)]
        
        # Números atrasados (não sorteados há mais tempo)
        numeros_atrasados = sorted(atrasos.items(), key=lambda x: x[1], reverse=True)[:20]
        numeros_atrasados = [num for num, _ in numeros_atrasados]
        
        # Distribuição por dezenas (1-10, 11-20, etc.)
        dezenas = {
            'D1': list(range(1, 11)),
            'D2': list(range(11, 21)),
            'D3': list(range(21, 31)),
            'D4': list(range(31, 41)),
            'D5': list(range(41, 51)),
            'D6': list(range(51, 61)),
            'D7': list(range(61, 71)),
            'D8': list(range(71, 81))
        }
        
        media_dezenas = {}
        for dezena, numeros in dezenas.items():
            total = sum(freq.get(n, 0) for n in numeros)
            media_dezenas[dezena] = total / len(self.historico) if self.historico else 0
        
        # Pares e ímpares
        total_pares = sum(freq.get(n, 0) for n in range(2, 81, 2))
        total_impares = sum(freq.get(n, 0) for n in range(1, 81, 2))
        
        return {
            'total_concursos': len(self.historico),
            'numeros_quentes': numeros_quentes,
            'numeros_atrasados': numeros_atrasados,
            'mais_sorteados': self.numeros_mais_sorteados(20),
            'menos_sorteados': self.numeros_menos_sorteados(20),
            'media_dezenas': media_dezenas,
            'pares_impares': {
                'pares': total_pares / len(self.historico) if self.historico else 0,
                'impares': total_impares / len(self.historico) if self.historico else 0
            },
            'atrasos': atrasos
        }
    
    def combinacao_mais_repetida(self) -> Dict:
        """
        Encontra a combinação de 10 números que mais se repetiu no histórico
        Retorna a combinação e quantas vezes apareceu
        """
        if not self.historico:
            return {
                'combinacao': [],
                'quantidade': 0
            }
        
        combinacoes = Counter()
        
        for concurso in self.historico:
            numeros = concurso.get('numeros', [])
            if len(numeros) == 10:
                combinacao = tuple(sorted(numeros))
                combinacoes[combinacao] += 1
        
        if not combinacoes:
            return {
                'combinacao': [],
                'quantidade': 0
            }
        
        combinacao_mais_frequente, quantidade = combinacoes.most_common(1)[0]
        
        return {
            'combinacao': list(combinacao_mais_frequente),
            'quantidade': quantidade
        }

