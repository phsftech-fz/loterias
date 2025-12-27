"""
Módulo para gerar fechamentos otimizados de jogos da Timemania
"""
import random
from typing import List, Dict
from collections import Counter


class GeradorFechamentoTimemania:
    """Classe para gerar fechamentos otimizados para Timemania"""
    
    def __init__(self, analisador, historico: List[Dict]):
        self.analisador = analisador
        self.historico = historico
        self.numeros_range = range(1, 81)  # Timemania: 1 a 80
        self.quantidade_numeros = 10  # Timemania: 10 números por jogo
    
    def fechamento_por_frequencia(self, quantidade_jogos: int = 10) -> List[List[int]]:
        """Gera jogos baseados em números de maior frequência"""
        mais_sorteados = [num for num, _ in self.analisador.numeros_mais_sorteados(40)]
        jogos = []
        
        for _ in range(quantidade_jogos):
            jogo = sorted(random.sample(mais_sorteados, min(10, len(mais_sorteados))))
            if jogo not in jogos:
                jogos.append(jogo)
        
        return jogos
    
    def fechamento_balanceado(self, quantidade_jogos: int = 10) -> List[List[int]]:
        """Gera jogos balanceados considerando distribuição por dezenas e pares/ímpares"""
        stats = self.analisador.get_estatisticas_completas()
        media_dezenas = stats['media_dezenas']
        media_pi = stats['pares_impares']
        
        # Define dezenas (1-10, 11-20, 21-30, etc.)
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
        
        jogos = []
        
        for _ in range(quantidade_jogos):
            jogo = []
            
            # Distribuição por dezenas (baseada na média histórica)
            proporcoes = {}
            total_proporcao = sum(media_dezenas.values())
            for d, media in media_dezenas.items():
                proporcoes[d] = (media / total_proporcao) * 10 if total_proporcao > 0 else 1.25
            
            # Distribui números entre dezenas
            distribuicao = {}
            total_distribuido = 0
            for d in dezenas.keys():
                qtd = max(1, int(round(proporcoes[d])))
                distribuicao[d] = qtd
                total_distribuido += qtd
            
            # Ajusta para ter exatamente 10
            while total_distribuido < 10:
                for d in dezenas.keys():
                    if total_distribuido >= 10:
                        break
                    distribuicao[d] += 1
                    total_distribuido += 1
            
            while total_distribuido > 10:
                for d in reversed(list(dezenas.keys())):
                    if total_distribuido <= 10:
                        break
                    if distribuicao[d] > 1:
                        distribuicao[d] -= 1
                        total_distribuido -= 1
            
            # Seleciona números de cada dezena
            for d, qtd in distribuicao.items():
                jogo.extend(random.sample(dezenas[d], min(qtd, len(dezenas[d]))))
            
            # Balanceia pares/ímpares
            pares = [n for n in jogo if n % 2 == 0]
            impares = [n for n in jogo if n % 2 == 1]
            
            proporcao_pares = media_pi['pares'] / (media_pi['pares'] + media_pi['impares']) if (media_pi['pares'] + media_pi['impares']) > 0 else 0.5
            target_pares = max(4, int(round(proporcao_pares * 10)))
            target_impares = 10 - target_pares
            
            while len(pares) != target_pares or len(impares) != target_impares:
                if len(pares) > target_pares:
                    par_remover = random.choice(pares)
                    jogo.remove(par_remover)
                    pares.remove(par_remover)
                    impares_disponiveis = [n for n in self.numeros_range if n % 2 == 1 and n not in jogo]
                    if impares_disponiveis:
                        novo_impar = random.choice(impares_disponiveis)
                        jogo.append(novo_impar)
                        impares.append(novo_impar)
                elif len(impares) > target_impares:
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
            
            jogo = sorted(jogo[:10])
            if jogo not in jogos:
                jogos.append(jogo)
        
        return jogos
    
    def fechamento_por_atraso(self, quantidade_jogos: int = 10) -> List[List[int]]:
        """Gera jogos baseados em números mais atrasados"""
        atrasos = self.analisador.calcular_atraso()
        numeros_ordenados_por_atraso = sorted(atrasos.items(), key=lambda x: x[1], reverse=True)
        
        numeros_atrasados = [num for num, _ in numeros_ordenados_por_atraso[:30]]
        
        jogos = []
        for _ in range(quantidade_jogos):
            jogo = sorted(random.sample(numeros_atrasados, min(10, len(numeros_atrasados))))
            if jogo not in jogos:
                jogos.append(jogo)
        
        return jogos
    
    def fechamento_misto(self, quantidade_jogos: int = 10) -> List[List[int]]:
        """
        ESTRATÉGIA OTIMIZADA PARA TIMEMANIA:
        - 35% números quentes (3-4 números - tendência recente)
        - 30% números atrasados (3 números - lei dos grandes números)
        - 20% números de alta frequência histórica (2 números)
        - 10% distribuição por oitavas (1 número de diferentes faixas)
        - 5% números aleatórios (diversificação final)
        
        Garante boa cobertura das 8 oitavas para maximizar chances.
        """
        stats = self.analisador.get_estatisticas_completas()
        quentes = stats.get('numeros_quentes', [])
        atrasados = stats.get('numeros_atrasados', [])
        mais_sorteados = [num for num, _ in self.analisador.numeros_mais_sorteados(30)]
        media_dezenas = stats.get('media_dezenas', {})
        
        # Define oitavas (1-10, 11-20, 21-30, etc)
        oitavas = {
            'O1': list(range(1, 11)),
            'O2': list(range(11, 21)),
            'O3': list(range(21, 31)),
            'O4': list(range(31, 41)),
            'O5': list(range(41, 51)),
            'O6': list(range(51, 61)),
            'O7': list(range(61, 71)),
            'O8': list(range(71, 81))
        }
        
        jogos = []
        
        for _ in range(quantidade_jogos):
            jogo = []
            numeros_usados = set()
            
            # 35% números quentes (3-4 números)
            if quentes:
                quentes_disponiveis = [n for n in quentes if n not in numeros_usados]
                if quentes_disponiveis:
                    selecionados = random.sample(quentes_disponiveis, min(4, len(quentes_disponiveis)))
                    jogo.extend(selecionados)
                    numeros_usados.update(selecionados)
            
            # 30% números atrasados (3 números)
            if atrasados:
                atrasados_disponiveis = [n for n in atrasados if n not in numeros_usados]
                if atrasados_disponiveis:
                    selecionados = random.sample(atrasados_disponiveis, min(3, len(atrasados_disponiveis)))
                    jogo.extend(selecionados)
                    numeros_usados.update(selecionados)
            
            # 20% números de alta frequência (2 números)
            frequencia_disponiveis = [n for n in mais_sorteados if n not in numeros_usados]
            if frequencia_disponiveis:
                selecionados = random.sample(frequencia_disponiveis, min(2, len(frequencia_disponiveis)))
                jogo.extend(selecionados)
                numeros_usados.update(selecionados)
            
            # 10% distribuição por oitavas (1 número de diferentes faixas)
            # Seleciona aleatoriamente algumas oitavas para garantir distribuição
            oitavas_keys = list(oitavas.keys())
            random.shuffle(oitavas_keys)
            for o_key in oitavas_keys[:2]:  # Seleciona de 2 oitavas diferentes
                if len(jogo) >= 10:
                    break
                oitava_disponiveis = [n for n in oitavas[o_key] if n not in numeros_usados]
                if oitava_disponiveis:
                    selecionado = random.choice(oitava_disponiveis)
                    jogo.append(selecionado)
                    numeros_usados.add(selecionado)
            
            # 5% números aleatórios para completar (1 número)
            todos_disponiveis = [n for n in self.numeros_range if n not in numeros_usados]
            faltam = 10 - len(jogo)
            if faltam > 0 and todos_disponiveis:
                selecionados = random.sample(todos_disponiveis, min(faltam, len(todos_disponiveis)))
                jogo.extend(selecionados)
            
            # Garante exatamente 10 números
            jogo = sorted(list(set(jogo))[:10])
            while len(jogo) < 10:
                disponiveis = [n for n in self.numeros_range if n not in jogo]
                if disponiveis:
                    jogo.append(random.choice(disponiveis))
                    jogo = sorted(jogo)
                else:
                    break
            
            if len(jogo) == 10 and jogo not in jogos:
                jogos.append(jogo)
        
        return jogos
    
    def fechamento_matriz(self, numeros_fixos: List[int], quantidade_jogos: int = 10) -> List[List[int]]:
        """Gera fechamento usando matriz de cobertura"""
        if len(numeros_fixos) >= 10:
            jogos = []
            for _ in range(quantidade_jogos):
                jogo = sorted(random.sample(numeros_fixos, 10))
                if jogo not in jogos:
                    jogos.append(jogo)
            return jogos
        
        jogos = []
        numeros_restantes = [n for n in self.numeros_range if n not in numeros_fixos]
        
        for _ in range(quantidade_jogos):
            jogo = numeros_fixos.copy()
            
            qtd_restante = 10 - len(jogo)
            if qtd_restante > 0 and numeros_restantes:
                jogo.extend(random.sample(numeros_restantes, min(qtd_restante, len(numeros_restantes))))
            
            jogo = sorted(jogo[:10])
            if jogo not in jogos:
                jogos.append(jogo)
        
        return jogos
    
    def gerar_fechamento_completo(
        self, 
        estrategia: str = 'misto',
        quantidade_jogos: int = 10,
        numeros_fixos: List[int] = None
    ) -> List[List[int]]:
        """Gera fechamento completo baseado na estratégia escolhida"""
        if numeros_fixos:
            return self.fechamento_matriz(numeros_fixos, quantidade_jogos)
        
        estrategias = {
            'frequencia': self.fechamento_por_frequencia,
            'balanceado': self.fechamento_balanceado,
            'atraso': self.fechamento_por_atraso,
            'misto': self.fechamento_misto
        }
        
        estrategia_func = estrategias.get(estrategia, self.fechamento_misto)
        jogos = estrategia_func(quantidade_jogos)
        
        # Garante que não há jogos duplicados
        jogos_unicos = []
        for jogo in jogos:
            if jogo not in jogos_unicos:
                jogos_unicos.append(jogo)
        
        return jogos_unicos
    
    def validar_jogo(self, jogo: List[int]) -> bool:
        """Valida se um jogo está correto (10 números entre 1 e 80)"""
        if len(jogo) != 10:
            return False
        if not all(1 <= n <= 80 for n in jogo):
            return False
        if len(set(jogo)) != 10:
            return False
        return True

