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
    
    def analisar_times_coracao(self) -> Dict:
        """
        Analisa a frequência dos times do coração no histórico
        Retorna estatísticas sobre quais times mais aparecem
        """
        if not self.historico:
            return {
                'times_frequencia': {},
                'times_mais_sorteados': [],
                'times_recentes': [],
                'total_concursos_com_time': 0
            }
        
        frequencia_times = Counter()
        times_recentes = []
        total_com_time = 0
        
        # Analisa últimos 30 concursos para times recentes
        ultimos_concursos = self.historico[-30:] if len(self.historico) >= 30 else self.historico
        
        for concurso in self.historico:
            time = concurso.get('time_coracao', '')
            # Normaliza o nome do time (remove espaços extras, converte para minúsculas para comparação)
            time_normalizado = time.strip() if time else ''
            if time_normalizado:
                frequencia_times[time_normalizado] += 1
                total_com_time += 1
        
        # Times recentes (últimos 30 concursos)
        for concurso in ultimos_concursos:
            time = concurso.get('time_coracao', '').strip()
            if time:
                times_recentes.append(time)
        
        # Remove duplicatas mantendo ordem
        times_recentes_unicos = []
        for time in times_recentes:
            if time and time not in times_recentes_unicos:
                times_recentes_unicos.append(time)
        
        # Ordena por frequência (mais frequente primeiro)
        times_mais_sorteados = sorted(
            frequencia_times.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            'times_frequencia': dict(frequencia_times),
            'times_mais_sorteados': times_mais_sorteados[:10],  # Top 10
            'times_recentes': times_recentes_unicos[:10],  # Últimos 10 times únicos
            'total_concursos_com_time': total_com_time,
            'total_concursos': len(self.historico)
        }
    
    def sugerir_time_coracao(self) -> Dict:
        """
        Sugere um time do coração baseado em análise estatística:
        - 50% peso: Times mais frequentes no histórico completo
        - 30% peso: Times que apareceram recentemente (últimos 30 concursos)
        - 20% peso: Times que apareceram muito mas estão "devendo" (não aparecem recentemente)
        """
        analise = self.analisar_times_coracao()
        
        if not analise['times_frequencia']:
            return {
                'time_sugerido': '',
                'razao': 'Nenhum time encontrado no histórico',
                'confianca': 0
            }
        
        times_mais_sorteados = analise['times_mais_sorteados']
        times_recentes = analise['times_recentes']
        
        if not times_mais_sorteados:
            return {
                'time_sugerido': '',
                'razao': 'Nenhum time disponível',
                'confianca': 0
            }
        
        # Calcula pontuação para cada time
        pontuacoes = {}
        max_frequencia = times_mais_sorteados[0][1] if times_mais_sorteados else 1
        
        # Peso 1: Frequência geral (50%)
        for time, freq in times_mais_sorteados:
            pontuacoes[time] = (freq / max_frequencia) * 0.5
        
        # Peso 2: Aparições recentes (30%)
        # Times que apareceram recentemente ganham bônus
        if times_recentes:
            for i, time in enumerate(times_recentes[:10], 1):
                if time in pontuacoes:
                    # Quanto mais recente, maior o bônus (inverso da posição)
                    bonus_recente = (11 - i) / 10 * 0.3
                    pontuacoes[time] += bonus_recente
                else:
                    # Novo time nos recentes também recebe pontuação
                    pontuacoes[time] = (11 - i) / 10 * 0.3
        
        # Peso 3: Times que estão "devendo" (20%)
        # Times frequentes que não apareceram recentemente
        if times_recentes:
            times_recentes_set = set(times_recentes)
            for time, freq in times_mais_sorteados[:10]:
                if time not in times_recentes_set and freq >= 3:
                    # Time frequente que não apareceu recentemente
                    pontuacoes[time] = pontuacoes.get(time, 0) + 0.2
        
        # Seleciona o time com maior pontuação
        if not pontuacoes:
            # Fallback: usa o time mais frequente
            time_sugerido = times_mais_sorteados[0][0]
            razao = f"Time mais frequente no histórico ({times_mais_sorteados[0][1]} vezes)"
            confianca = 70
        else:
            time_sugerido = max(pontuacoes.items(), key=lambda x: x[1])[0]
            pontuacao_max = max(pontuacoes.values())
            
            # Calcula confiança baseada na pontuação e diferença para o segundo colocado
            confianca = min(95, int(pontuacao_max * 100))
            
            # Determina a razão
            freq_total = analise['times_frequencia'].get(time_sugerido, 0)
            if time_sugerido in times_recentes[:3]:
                razao = f"Time frequente ({freq_total}x) e apareceu recentemente nos sorteios"
            elif time_sugerido in times_recentes:
                razao = f"Time frequente ({freq_total}x) no histórico e apareceu recentemente"
            else:
                razao = f"Time muito frequente ({freq_total}x) no histórico e está 'devendo' aparecer"
        
        return {
            'time_sugerido': time_sugerido,
            'razao': razao,
            'confianca': confianca,
            'frequencia_historico': analise['times_frequencia'].get(time_sugerido, 0),
            'apareceu_recentemente': time_sugerido in times_recentes
        }

