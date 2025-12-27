"""
Módulo de análise de padrões e estatísticas dos resultados
"""
from typing import List, Dict, Tuple
from collections import Counter, defaultdict


class AnalisadorLotofacil:
    """Classe para analisar padrões nos resultados da Lotofácil"""
    
    def __init__(self, historico: List[Dict]):
        self.historico = historico
        self.numeros_range = range(1, 26)  # Lotofácil: 1 a 25
    
    def frequencia_numeros(self) -> Dict[int, int]:
        """Calcula frequência de cada número nos concursos"""
        frequencias = Counter()
        for concurso in self.historico:
            for numero in concurso['numeros']:
                frequencias[numero] += 1
        return dict(frequencias)
    
    def numeros_mais_sorteados(self, top: int = 15) -> List[Tuple[int, int]]:
        """Retorna os N números mais sorteados"""
        freq = self.frequencia_numeros()
        return sorted(freq.items(), key=lambda x: x[1], reverse=True)[:top]
    
    def numeros_menos_sorteados(self, top: int = 10) -> List[Tuple[int, int]]:
        """Retorna os N números menos sorteados"""
        freq = self.frequencia_numeros()
        return sorted(freq.items(), key=lambda x: x[1])[:top]
    
    def combinacao_mais_repetida(self) -> Dict:
        """
        Encontra a combinação de 15 números que mais se repetiu no histórico
        Retorna a combinação e quantas vezes apareceu
        """
        if not self.historico:
            return {
                'combinacao': [],
                'quantidade': 0
            }
        
        # Conta cada combinação de 15 números
        combinacoes = Counter()
        
        for concurso in self.historico:
            numeros = concurso.get('numeros', [])
            if len(numeros) == 15:
                # Cria uma tupla ordenada para usar como chave
                combinacao = tuple(sorted(numeros))
                combinacoes[combinacao] += 1
        
        if not combinacoes:
            return {
                'combinacao': [],
                'quantidade': 0
            }
        
        # Encontra a combinação mais frequente
        combinacao_mais_frequente, quantidade = combinacoes.most_common(1)[0]
        
        return {
            'combinacao': list(combinacao_mais_frequente),
            'quantidade': quantidade
        }
    
    def calcular_atraso(self) -> Dict[int, int]:
        """
        Calcula quantos concursos cada número está atrasado
        (última vez que foi sorteado)
        """
        atrasos = {num: 0 for num in self.numeros_range}
        ultima_aparicao = {num: -1 for num in self.numeros_range}
        
        for idx, concurso in enumerate(self.historico):
            for numero in concurso['numeros']:
                ultima_aparicao[numero] = idx
        
        # Calcula atraso baseado no último concurso
        ultimo_concurso_idx = len(self.historico) - 1
        for numero in self.numeros_range:
            if ultima_aparicao[numero] >= 0:
                atrasos[numero] = ultimo_concurso_idx - ultima_aparicao[numero]
            else:
                atrasos[numero] = len(self.historico)  # Nunca foi sorteado
        
        return atrasos
    
    def numeros_atrasados(self, limite_atraso: int = 5) -> List[int]:
        """Retorna números que estão atrasados acima do limite"""
        atrasos = self.calcular_atraso()
        return [num for num, atraso in atrasos.items() if atraso >= limite_atraso]
    
    def analisar_sequencias(self) -> Dict[str, int]:
        """Analisa padrões de sequências consecutivas"""
        sequencias = defaultdict(int)
        
        for concurso in self.historico:
            numeros = sorted(concurso['numeros'])
            # Detecta sequências de 2 ou mais números consecutivos
            for i in range(len(numeros) - 1):
                if numeros[i+1] - numeros[i] == 1:
                    sequencias[f"{numeros[i]}-{numeros[i+1]}"] += 1
        
        return dict(sequencias)
    
    def distribuicao_quadrantes(self) -> Dict[str, List[int]]:
        """
        Analisa distribuição de números por quadrantes
        Quadrante 1: 1-6, Quadrante 2: 7-12, Quadrante 3: 13-18, Quadrante 4: 19-25
        """
        quadrantes = {
            'Q1': list(range(1, 7)),
            'Q2': list(range(7, 13)),
            'Q3': list(range(13, 19)),
            'Q4': list(range(19, 26))
        }
        
        distribuicao = defaultdict(list)
        
        for concurso in self.historico:
            for q_name, q_nums in quadrantes.items():
                count = sum(1 for n in concurso['numeros'] if n in q_nums)
                distribuicao[q_name].append(count)
        
        return dict(distribuicao)
    
    def media_por_quadrante(self) -> Dict[str, float]:
        """Calcula média de números por quadrante"""
        dist = self.distribuicao_quadrantes()
        return {q: sum(counts) / len(counts) if counts else 0.0 for q, counts in dist.items()}
    
    def analisar_pares_impares(self) -> Dict[str, List[int]]:
        """Analisa distribuição de pares e ímpares"""
        distribuicao = {'pares': [], 'impares': []}
        
        for concurso in self.historico:
            pares = sum(1 for n in concurso['numeros'] if n % 2 == 0)
            impares = 15 - pares
            distribuicao['pares'].append(pares)
            distribuicao['impares'].append(impares)
        
        return distribuicao
    
    def media_pares_impares(self) -> Dict[str, float]:
        """Calcula média de pares e ímpares"""
        dist = self.analisar_pares_impares()
        return {tipo: sum(counts) / len(counts) if counts else 0.0 for tipo, counts in dist.items()}
    
    def numeros_quentes(self, limite: int = 10) -> List[int]:
        """
        Identifica números quentes (frequentes nos últimos concursos)
        """
        if len(self.historico) < limite:
            limite = len(self.historico)
        
        ultimos = self.historico[-limite:]
        freq_recente = Counter()
        
        for concurso in ultimos:
            for numero in concurso['numeros']:
                freq_recente[numero] += 1
        
        # Números que apareceram em pelo menos 50% dos últimos concursos
        threshold = limite // 2
        return [num for num, count in freq_recente.items() if count >= threshold]
    
    def numeros_frios(self, limite: int = 10) -> List[int]:
        """
        Identifica números frios (raros nos últimos concursos)
        """
        if len(self.historico) < limite:
            limite = len(self.historico)
        
        ultimos = self.historico[-limite:]
        freq_recente = Counter()
        
        for concurso in ultimos:
            for numero in concurso['numeros']:
                freq_recente[numero] += 1
        
        # Números que apareceram em menos de 30% dos últimos concursos
        threshold = limite * 0.3
        todos_numeros = set(range(1, 26))
        numeros_que_sairam = set(freq_recente.keys())
        numeros_que_nao_sairam = todos_numeros - numeros_que_sairam
        
        frios = list(numeros_que_nao_sairam)
        frios.extend([num for num, count in freq_recente.items() if count < threshold])
        
        return list(set(frios))
    
    def get_estatisticas_completas(self) -> Dict:
        """Retorna todas as estatísticas em um dicionário"""
        return {
            'frequencia': self.frequencia_numeros(),
            'mais_sorteados': self.numeros_mais_sorteados(),
            'menos_sorteados': self.numeros_menos_sorteados(),
            'atrasos': self.calcular_atraso(),
            'numeros_atrasados': self.numeros_atrasados(),
            'media_quadrantes': self.media_por_quadrante(),
            'media_pares_impares': self.media_pares_impares(),
            'numeros_quentes': self.numeros_quentes(),
            'numeros_frios': self.numeros_frios(),
            'total_concursos': len(self.historico)
        }

