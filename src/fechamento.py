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
        ESTRATÉGIA BALANCEADA OTIMIZADA:
        Gera jogos com distribuição estatística ideal baseada no histórico:
        - Distribuição proporcional por quadrantes (baseada na média histórica)
        - Balanceamento pares/ímpares (proporção histórica)
        - Preferência por números de maior frequência dentro de cada quadrante
        """
        stats = self.analisador.get_estatisticas_completas()
        media_quad = stats.get('media_quadrantes', {})
        media_pi = stats.get('media_pares_impares', {})
        freq = self.analisador.frequencia_numeros()
        
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
            
            # Calcula distribuição por quadrantes baseada na média histórica
            total_media = sum(media_quad.values()) if media_quad else 15
            if total_media > 0 and media_quad:
                q1_count = max(3, int(round((media_quad.get('Q1', 3.75) / total_media) * quantidade_numeros)))
                q2_count = max(3, int(round((media_quad.get('Q2', 3.75) / total_media) * quantidade_numeros)))
                q3_count = max(3, int(round((media_quad.get('Q3', 3.75) / total_media) * quantidade_numeros)))
                q4_count = quantidade_numeros - q1_count - q2_count - q3_count
                
                # Garante que cada quadrante tenha pelo menos 3 números (ou proporcional)
                min_por_quad = max(2, quantidade_numeros // 6)
                q1_count = max(min_por_quad, q1_count)
                q2_count = max(min_por_quad, q2_count)
                q3_count = max(min_por_quad, q3_count)
                q4_count = max(min_por_quad, q4_count)
                
                # Ajusta total para quantidade_numeros
                total_atual = q1_count + q2_count + q3_count + q4_count
                if total_atual != quantidade_numeros:
                    diff = quantidade_numeros - total_atual
                    if diff > 0:
                        q4_count += diff
                    else:
                        # Reduz proporcionalmente
                        reducao = abs(diff)
                        q4_count = max(min_por_quad, q4_count - reducao)
            else:
                # Distribuição uniforme se não houver histórico
                qtd_por_quad = quantidade_numeros // 4
                resto = quantidade_numeros % 4
                q1_count = qtd_por_quad + (1 if resto > 0 else 0)
                q2_count = qtd_por_quad + (1 if resto > 1 else 0)
                q3_count = qtd_por_quad + (1 if resto > 2 else 0)
                q4_count = qtd_por_quad
            
            # Seleciona números de cada quadrante priorizando frequência
            for q_name, q_count in [('Q1', q1_count), ('Q2', q2_count), ('Q3', q3_count), ('Q4', q4_count)]:
                nums_quad = quadrantes[q_name]
                # Ordena por frequência (maior primeiro)
                nums_ordenados = sorted(nums_quad, key=lambda x: freq.get(x, 0), reverse=True)
                selecionados = random.sample(nums_ordenados, min(q_count, len(nums_ordenados)))
                jogo.extend(selecionados)
            
            # Balanceia pares/ímpares
            pares = [n for n in jogo if n % 2 == 0]
            impares = [n for n in jogo if n % 2 == 1]
            
            # Proporção histórica de pares/ímpares
            total_pi = media_pi.get('pares', 7) + media_pi.get('impares', 8)
            if total_pi > 0:
                proporcao_pares = media_pi.get('pares', 7) / total_pi
            else:
                proporcao_pares = 0.47
            
            target_pares = int(round(proporcao_pares * quantidade_numeros))
            target_impares = quantidade_numeros - target_pares
            
            # Ajusta balanceamento com limite de tentativas
            tentativas = 0
            max_tentativas = 20
            while (len(pares) != target_pares or len(impares) != target_impares) and tentativas < max_tentativas:
                if len(pares) > target_pares:
                    par_remover = random.choice(pares)
                    jogo.remove(par_remover)
                    pares.remove(par_remover)
                    impares_disponiveis = [n for n in self.numeros_range if n % 2 == 1 and n not in jogo]
                    if impares_disponiveis:
                        # Prefere ímpares com maior frequência
                        impares_ordenados = sorted(impares_disponiveis, key=lambda x: freq.get(x, 0), reverse=True)
                        novo_impar = random.choice(impares_ordenados[:min(10, len(impares_ordenados))])
                        jogo.append(novo_impar)
                        impares.append(novo_impar)
                elif len(impares) > target_impares:
                    impar_remover = random.choice(impares)
                    jogo.remove(impar_remover)
                    impares.remove(impar_remover)
                    pares_disponiveis = [n for n in self.numeros_range if n % 2 == 0 and n not in jogo]
                    if pares_disponiveis:
                        # Prefere pares com maior frequência
                        pares_ordenados = sorted(pares_disponiveis, key=lambda x: freq.get(x, 0), reverse=True)
                        novo_par = random.choice(pares_ordenados[:min(10, len(pares_ordenados))])
                        jogo.append(novo_par)
                        pares.append(novo_par)
                else:
                    break
                tentativas += 1
            
            jogo = sorted(list(set(jogo))[:quantidade_numeros])
            
            # Completa se necessário
            while len(jogo) < quantidade_numeros:
                disponiveis = [n for n in self.numeros_range if n not in jogo]
                if disponiveis:
                    # Prefere números com maior frequência
                    disponiveis_ordenados = sorted(disponiveis, key=lambda x: freq.get(x, 0), reverse=True)
                    jogo.append(random.choice(disponiveis_ordenados[:min(10, len(disponiveis_ordenados))]))
                    jogo = sorted(jogo)
                else:
                    break
            
            if len(jogo) == quantidade_numeros and jogo not in jogos:
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
        ESTRATÉGIA OTIMIZADA - Combina múltiplas técnicas avançadas:
        - 35% números quentes (tendência de continuidade)
        - 25% números atrasados (lei dos grandes números)
        - 20% números de alta frequência histórica
        - 15% números balanceados por quadrantes
        - 5% números aleatórios (diversificação)
        
        Esta estratégia oferece a melhor cobertura estatística.
        """
        stats = self.analisador.get_estatisticas_completas()
        quentes = stats.get('numeros_quentes', [])
        atrasados = stats.get('numeros_atrasados', [])
        mais_sorteados = [num for num, _ in self.analisador.numeros_mais_sorteados(20)]
        media_quad = stats.get('media_quadrantes', {})
        
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
            numeros_usados = set()
            
            # 35% números quentes (tendência recente)
            qtd_quentes = max(5, int(quantidade_numeros * 0.35))
            if quentes:
                quentes_disponiveis = [n for n in quentes if n not in numeros_usados]
                if quentes_disponiveis:
                    selecionados = random.sample(quentes_disponiveis, min(qtd_quentes, len(quentes_disponiveis)))
                    jogo.extend(selecionados)
                    numeros_usados.update(selecionados)
            
            # 25% números atrasados (lei dos grandes números)
            qtd_atrasados = max(3, int(quantidade_numeros * 0.25))
            if atrasados:
                atrasados_disponiveis = [n for n in atrasados if n not in numeros_usados]
                if atrasados_disponiveis:
                    selecionados = random.sample(atrasados_disponiveis, min(qtd_atrasados, len(atrasados_disponiveis)))
                    jogo.extend(selecionados)
                    numeros_usados.update(selecionados)
            
            # 20% números de alta frequência histórica
            qtd_frequencia = max(3, int(quantidade_numeros * 0.20))
            frequencia_disponiveis = [n for n in mais_sorteados if n not in numeros_usados]
            if frequencia_disponiveis:
                selecionados = random.sample(frequencia_disponiveis, min(qtd_frequencia, len(frequencia_disponiveis)))
                jogo.extend(selecionados)
                numeros_usados.update(selecionados)
            
            # 15% números balanceados por quadrantes (melhor distribuição)
            qtd_quadrantes = max(2, int(quantidade_numeros * 0.15))
            for q_name in ['Q1', 'Q2', 'Q3', 'Q4']:
                if len(jogo) >= quantidade_numeros:
                    break
                qtd_por_quad = max(1, qtd_quadrantes // 4)
                quad_disponiveis = [n for n in quadrantes[q_name] if n not in numeros_usados]
                if quad_disponiveis:
                    selecionados = random.sample(quad_disponiveis, min(qtd_por_quad, len(quad_disponiveis)))
                    jogo.extend(selecionados)
                    numeros_usados.update(selecionados)
            
            # 5% números aleatórios para completar (diversificação final)
            todos_disponiveis = [n for n in self.numeros_range if n not in numeros_usados]
            faltam = quantidade_numeros - len(jogo)
            if faltam > 0 and todos_disponiveis:
                selecionados = random.sample(todos_disponiveis, min(faltam, len(todos_disponiveis)))
                jogo.extend(selecionados)
            
            # Garante quantidade exata e remove duplicatas
            jogo = sorted(list(set(jogo))[:quantidade_numeros])
            
            # Completa se necessário
            while len(jogo) < quantidade_numeros:
                disponiveis = [n for n in self.numeros_range if n not in jogo]
                if disponiveis:
                    jogo.append(random.choice(disponiveis))
                    jogo = sorted(jogo)
                else:
                    break
            
            if len(jogo) == quantidade_numeros and jogo not in jogos:
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
        jogos = estrategia_func(quantidade_jogos, quantidade_numeros)
        
        # Garante que não há jogos duplicados
        jogos_unicos = []
        for jogo in jogos:
            if jogo not in jogos_unicos:
                jogos_unicos.append(jogo)
        
        return jogos_unicos
    
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

