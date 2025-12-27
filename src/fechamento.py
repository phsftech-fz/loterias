"""
Módulo para gerar fechamentos otimizados de jogos
"""
import random
import itertools
from typing import List, Set, Dict, Tuple
from collections import Counter


class GeradorFechamento:
    """Classe para gerar fechamentos otimizados"""
    
    def __init__(self, analisador, historico: List[Dict]):
        self.analisador = analisador
        self.historico = historico
        self.numeros_range = range(1, 26)
    
    def fechamento_por_frequencia(self, quantidade_jogos: int = 10, quantidade_numeros: int = 15) -> List[List[int]]:
        """
        Gera jogos baseados em números de maior frequência
        """
        mais_sorteados = [num for num, _ in self.analisador.numeros_mais_sorteados(25)]
        jogos = []
        
        for _ in range(quantidade_jogos):
            # Seleciona quantidade_numeros dos mais sorteados
            jogo = sorted(random.sample(mais_sorteados, min(quantidade_numeros, len(mais_sorteados))))
            if jogo not in jogos:
                jogos.append(jogo)
        
        return jogos
    
    def fechamento_balanceado(self, quantidade_jogos: int = 10, quantidade_numeros: int = 15) -> List[List[int]]:
        """
        Gera jogos balanceados considerando:
        - Distribuição por quadrantes
        - Balanceamento pares/ímpares
        - Números quentes e frios
        """
        stats = self.analisador.get_estatisticas_completas()
        media_quad = stats['media_quadrantes']
        media_pi = stats['media_pares_impares']
        
        # Define quadrantes
        quadrantes = {
            'Q1': list(range(1, 7)),
            'Q2': list(range(7, 13)),
            'Q3': list(range(13, 19)),
            'Q4': list(range(19, 26))
        }
        
        jogos = []
        
        for _ in range(quantidade_jogos):
            jogo = []
            
            # Distribuição por quadrantes (baseada na média histórica)
            # Proporcionalmente ajustado para quantidade_numeros
            proporcao_q1 = media_quad['Q1'] / 15 if media_quad['Q1'] > 0 else 0.25
            proporcao_q2 = media_quad['Q2'] / 15 if media_quad['Q2'] > 0 else 0.25
            proporcao_q3 = media_quad['Q3'] / 15 if media_quad['Q3'] > 0 else 0.25
            
            q1_count = max(3, int(round(proporcao_q1 * quantidade_numeros)))
            q2_count = max(3, int(round(proporcao_q2 * quantidade_numeros)))
            q3_count = max(3, int(round(proporcao_q3 * quantidade_numeros)))
            q4_count = quantidade_numeros - q1_count - q2_count - q3_count
            
            # Ajusta se necessário
            total = q1_count + q2_count + q3_count + q4_count
            if total != quantidade_numeros:
                q4_count += (quantidade_numeros - total)
            
            # Seleciona números de cada quadrante
            jogo.extend(random.sample(quadrantes['Q1'], min(q1_count, len(quadrantes['Q1']))))
            jogo.extend(random.sample(quadrantes['Q2'], min(q2_count, len(quadrantes['Q2']))))
            jogo.extend(random.sample(quadrantes['Q3'], min(q3_count, len(quadrantes['Q3']))))
            jogo.extend(random.sample(quadrantes['Q4'], min(q4_count, len(quadrantes['Q4']))))
            
            # Balanceia pares/ímpares
            pares = [n for n in jogo if n % 2 == 0]
            impares = [n for n in jogo if n % 2 == 1]
            
            # Ajusta para manter proporção histórica (geralmente ~7 pares e ~8 ímpares)
            # Proporcionalmente ajustado para quantidade_numeros
            proporcao_pares = media_pi['pares'] / 15 if media_pi['pares'] > 0 else 0.47
            target_pares = max(quantidade_numeros // 2 - 1, int(round(proporcao_pares * quantidade_numeros)))
            target_impares = quantidade_numeros - target_pares
            
            while len(pares) != target_pares or len(impares) != target_impares:
                if len(pares) > target_pares:
                    # Remove par, adiciona ímpar
                    par_remover = random.choice(pares)
                    jogo.remove(par_remover)
                    pares.remove(par_remover)
                    impares_disponiveis = [n for n in self.numeros_range if n % 2 == 1 and n not in jogo]
                    if impares_disponiveis:
                        novo_impar = random.choice(impares_disponiveis)
                        jogo.append(novo_impar)
                        impares.append(novo_impar)
                elif len(impares) > target_impares:
                    # Remove ímpar, adiciona par
                    impar_remover = random.choice(impares)
                    jogo.remove(impar_remover)
                    impares.remove(impar_remover)
                    pares_disponiveis = [n for n in self.numeros_range if n % 2 == 0 and n not in jogo]
                    if pares_disponiveis:
                        novo_par = random.choice(pares_disponiveis)
                        jogo.append(novo_par)
                        pares.append(novo_par)
                else:
                    break
            
            jogo = sorted(jogo[:quantidade_numeros])  # Garante exatamente quantidade_numeros números
            if jogo not in jogos:
                jogos.append(jogo)
        
        return jogos
    
    def fechamento_por_atraso(self, quantidade_jogos: int = 10, quantidade_numeros: int = 15) -> List[List[int]]:
        """
        Gera jogos priorizando números atrasados
        """
        atrasos = self.analisador.calcular_atraso()
        numeros_ordenados_por_atraso = sorted(
            atrasos.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # Pega números suficientes para gerar jogos
        numeros_atrasados = [num for num, _ in numeros_ordenados_por_atraso[:min(25, quantidade_numeros + 10)]]
        
        jogos = []
        for _ in range(quantidade_jogos):
            jogo = sorted(random.sample(numeros_atrasados, min(quantidade_numeros, len(numeros_atrasados))))
            if jogo not in jogos:
                jogos.append(jogo)
        
        return jogos
    
    def fechamento_misto(self, quantidade_jogos: int = 10, quantidade_numeros: int = 15) -> List[List[int]]:
        """
        Combina múltiplas estratégias:
        - 40% números quentes
        - 30% números atrasados
        - 20% números de alta frequência
        - 10% números aleatórios
        """
        stats = self.analisador.get_estatisticas_completas()
        quentes = stats['numeros_quentes']
        atrasados = stats['numeros_atrasados']
        mais_sorteados = [num for num, _ in self.analisador.numeros_mais_sorteados(15)]
        
        jogos = []
        
        for _ in range(quantidade_jogos):
            jogo = []
            
            # 40% números quentes
            qtd_quentes = int(quantidade_numeros * 0.4)
            if quentes:
                jogo.extend(random.sample(quentes, min(qtd_quentes, len(quentes))))
            
            # 30% números atrasados
            qtd_atrasados = int(quantidade_numeros * 0.3)
            if atrasados:
                jogo.extend(random.sample(atrasados, min(qtd_atrasados, len(atrasados))))
            
            # 20% números de alta frequência
            qtd_frequencia = int(quantidade_numeros * 0.2)
            disponiveis = [n for n in mais_sorteados if n not in jogo]
            if disponiveis:
                jogo.extend(random.sample(disponiveis, min(qtd_frequencia, len(disponiveis))))
            
            # 10% números aleatórios para completar
            todos_disponiveis = [n for n in self.numeros_range if n not in jogo]
            if todos_disponiveis:
                faltam = quantidade_numeros - len(jogo)
                if faltam > 0:
                    jogo.extend(random.sample(todos_disponiveis, min(faltam, len(todos_disponiveis))))
            
            jogo = sorted(jogo[:quantidade_numeros])
            if jogo not in jogos:
                jogos.append(jogo)
        
        return jogos
    
    def fechamento_matriz(self, numeros_fixos: List[int], quantidade_jogos: int = 10, quantidade_numeros: int = 15) -> List[List[int]]:
        """
        Gera fechamento usando matriz de cobertura
        Garante que todos os números fixos apareçam em pelo menos X jogos
        """
        if len(numeros_fixos) >= quantidade_numeros:
            # Se já tem quantidade_numeros ou mais, gera variações
            jogos = []
            for _ in range(quantidade_jogos):
                jogo = sorted(random.sample(numeros_fixos, quantidade_numeros))
                if jogo not in jogos:
                    jogos.append(jogo)
            return jogos
        
        jogos = []
        numeros_restantes = [n for n in self.numeros_range if n not in numeros_fixos]
        
        for _ in range(quantidade_jogos):
            # Sempre inclui os fixos
            jogo = numeros_fixos.copy()
            
            # Completa com números restantes
            qtd_restante = quantidade_numeros - len(jogo)
            if qtd_restante > 0 and numeros_restantes:
                jogo.extend(random.sample(numeros_restantes, min(qtd_restante, len(numeros_restantes))))
            
            jogo = sorted(jogo[:quantidade_numeros])
            if jogo not in jogos:
                jogos.append(jogo)
        
        return jogos
    
    def gerar_fechamento_completo(
        self, 
        estrategia: str = 'misto',
        quantidade_jogos: int = 10,
        numeros_fixos: List[int] = None,
        quantidade_numeros: int = 15
    ) -> List[List[int]]:
        """
        Gera fechamento completo baseado na estratégia escolhida
        """
        if numeros_fixos:
            return self.fechamento_matriz(numeros_fixos, quantidade_jogos, quantidade_numeros)
        
        estrategias = {
            'frequencia': self.fechamento_por_frequencia,
            'balanceado': self.fechamento_balanceado,
            'atraso': self.fechamento_por_atraso,
            'misto': self.fechamento_misto
        }
        
        estrategia_func = estrategias.get(estrategia, self.fechamento_misto)
        return estrategia_func(quantidade_jogos, quantidade_numeros)
    
    def validar_jogo(self, jogo: List[int], quantidade_numeros: int = None) -> bool:
        """
        Valida se um jogo está correto
        Se quantidade_numeros não for especificada, aceita 15-20 números
        """
        if quantidade_numeros:
            if len(jogo) != quantidade_numeros:
                return False
        else:
            # Aceita 15-20 números
            if not (15 <= len(jogo) <= 20):
                return False
        
        if not all(1 <= n <= 25 for n in jogo):
            return False
        if len(set(jogo)) != len(jogo):
            return False
        return True

