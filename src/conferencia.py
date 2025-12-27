"""
Módulo para conferir jogos com resultados
"""
from typing import List, Dict, Tuple
from collections import Counter


class ConferidorJogos:
    """Classe para conferir jogos com resultados históricos"""
    
    def __init__(self, historico: List[Dict]):
        self.historico = historico
    
    def conferir_ultimo_concurso(self, jogos: List[List[int]]) -> List[Dict]:
        """
        Confere jogos com o último concurso
        Funciona com qualquer quantidade de números (15-20)
        Retorna lista com resultados da conferência
        """
        if not self.historico:
            return []
        
        ultimo_concurso = self.historico[-1]
        numeros_sorteados = set(ultimo_concurso['numeros'])
        numero_concurso = ultimo_concurso['concurso']
        data_concurso = ultimo_concurso.get('data', '')
        
        resultados = []
        
        for idx, jogo in enumerate(jogos, 1):
            numeros_jogo = set(jogo)
            acertos = numeros_jogo.intersection(numeros_sorteados)
            quantidade_acertos = len(acertos)
            quantidade_numeros_jogo = len(jogo)
            
            # Calcula percentual de acertos
            percentual_acertos = (quantidade_acertos / quantidade_numeros_jogo * 100) if quantidade_numeros_jogo > 0 else 0
            
            resultados.append({
                'jogo_numero': idx,
                'jogo': sorted(jogo),
                'quantidade_numeros': quantidade_numeros_jogo,
                'acertos': sorted(list(acertos)),
                'quantidade_acertos': quantidade_acertos,
                'percentual_acertos': round(percentual_acertos, 2),
                'concurso': numero_concurso,
                'data': data_concurso,
                'numeros_sorteados': sorted(list(numeros_sorteados))
            })
        
        return resultados
    
    def conferir_historico_completo(self, jogos: List[List[int]]) -> List[Dict]:
        """
        Confere jogos com todo o histórico
        Retorna estatísticas de cada jogo
        """
        if not self.historico:
            return []
        
        resultados = []
        
        for idx, jogo in enumerate(jogos, 1):
            numeros_jogo = set(jogo)
            
            # Estatísticas por concurso
            estatisticas_concursos = []
            total_acertos = 0
            max_acertos = 0
            quantidade_numeros_jogo = len(jogo)
            min_acertos = quantidade_numeros_jogo if self.historico else 0
            concursos_com_acertos = 0
            
            for concurso in self.historico:
                numeros_sorteados = set(concurso['numeros'])
                acertos = numeros_jogo.intersection(numeros_sorteados)
                quantidade = len(acertos)
                
                total_acertos += quantidade
                max_acertos = max(max_acertos, quantidade)
                if quantidade > 0:
                    concursos_com_acertos += 1
                    min_acertos = min(min_acertos, quantidade) if min_acertos > 0 else quantidade
                    
                    estatisticas_concursos.append({
                        'concurso': concurso['concurso'],
                        'data': concurso.get('data', ''),
                        'acertos': quantidade,
                        'numeros_acertados': sorted(list(acertos))
                    })
            
            # Estatísticas por número individual
            frequencia_numeros = {}
            for numero in jogo:
                contador = 0
                for concurso in self.historico:
                    if numero in concurso['numeros']:
                        contador += 1
                frequencia_numeros[numero] = contador
            
            # Média de acertos
            media_acertos = total_acertos / len(self.historico) if self.historico else 0
            
            resultados.append({
                'jogo_numero': idx,
                'jogo': sorted(jogo),
                'quantidade_numeros': quantidade_numeros_jogo,
                'total_concursos': len(self.historico),
                'concursos_com_acertos': concursos_com_acertos,
                'percentual_com_acertos': (concursos_com_acertos / len(self.historico) * 100) if self.historico else 0,
                'total_acertos': total_acertos,
                'media_acertos': round(media_acertos, 2),
                'max_acertos': max_acertos,
                'min_acertos': min_acertos,
                'frequencia_numeros': frequencia_numeros,
                'estatisticas_concursos': sorted(estatisticas_concursos, key=lambda x: x['acertos'], reverse=True)[:10]  # Top 10
            })
        
        return resultados
    
    def conferir_completo(self, jogos: List[List[int]]) -> Dict:
        """
        Confere jogos com último concurso e histórico completo
        Retorna resultado completo ordenado pela melhor média de acertos
        """
        resultado_ultimo = self.conferir_ultimo_concurso(jogos)
        resultado_historico = self.conferir_historico_completo(jogos)
        
        # Ordena histórico completo pela média de acertos (melhor primeiro)
        resultado_historico_ordenado = sorted(
            resultado_historico, 
            key=lambda x: x.get('media_acertos', 0), 
            reverse=True
        )
        
        # Reordena também o último concurso para manter consistência
        # Cria um dicionário para mapear jogo_numero -> média
        media_por_jogo = {estat['jogo_numero']: estat.get('media_acertos', 0) 
                          for estat in resultado_historico_ordenado}
        
        # Ordena último concurso pela mesma ordem (melhor média primeiro)
        resultado_ultimo_ordenado = sorted(
            resultado_ultimo,
            key=lambda x: media_por_jogo.get(x.get('jogo_numero', 0), 0),
            reverse=True
        )
        
        return {
            'ultimo_concurso': resultado_ultimo_ordenado,
            'historico_completo': resultado_historico_ordenado,
            'total_jogos': len(jogos),
            'total_concursos_historico': len(self.historico)
        }

