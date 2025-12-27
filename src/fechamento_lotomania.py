"""
Módulo para gerar fechamentos otimizados de jogos da Lotomania
"""
import random
from typing import List, Dict
from collections import Counter


class GeradorFechamentoLotomania:
    """Classe para gerar fechamentos otimizados para Lotomania"""
    
    def __init__(self, analisador, historico: List[Dict]):
        self.analisador = analisador
        self.historico = historico
        self.numeros_range = range(0, 100)  # Lotomania: 00 a 99
        self.quantidade_numeros = 50  # Lotomania: 50 números por jogo
    
    def fechamento_por_frequencia(self, quantidade_jogos: int = 10) -> List[List[int]]:
        """Gera jogos baseados em números de maior frequência"""
        mais_sorteados = [num for num, _ in self.analisador.numeros_mais_sorteados(70)]
        jogos = []
        
        for _ in range(quantidade_jogos):
            jogo = sorted(random.sample(mais_sorteados, min(50, len(mais_sorteados))))
            if jogo not in jogos:
                jogos.append(jogo)
        
        return jogos
    
    def fechamento_balanceado(self, quantidade_jogos: int = 10) -> List[List[int]]:
        """Gera jogos balanceados considerando distribuição por dezenas e pares/ímpares"""
        stats = self.analisador.get_estatisticas_completas()
        media_dezenas = stats['media_dezenas']
        media_pi = stats['pares_impares']
        
        # Define dezenas (00-09, 10-19, 20-29, etc.)
        dezenas = {}
        for i in range(10):
            dezenas[f'D{i}'] = list(range(i * 10, (i + 1) * 10))
        
        jogos = []
        
        for _ in range(quantidade_jogos):
            jogo = []
            
            # Distribuição por dezenas (baseada na média histórica)
            proporcoes = {}
            total_proporcao = sum(media_dezenas.values())
            for d, media in media_dezenas.items():
                proporcoes[d] = (media / total_proporcao) * 50 if total_proporcao > 0 else 5
            
            # Distribui números entre dezenas
            distribuicao = {}
            total_distribuido = 0
            for d in dezenas.keys():
                qtd = max(3, int(round(proporcoes[d])))
                distribuicao[d] = qtd
                total_distribuido += qtd
            
            # Ajusta para ter exatamente 50
            while total_distribuido < 50:
                for d in dezenas.keys():
                    if total_distribuido >= 50:
                        break
                    distribuicao[d] += 1
                    total_distribuido += 1
            
            while total_distribuido > 50:
                for d in reversed(list(dezenas.keys())):
                    if total_distribuido <= 50:
                        break
                    if distribuicao[d] > 3:
                        distribuicao[d] -= 1
                        total_distribuido -= 1
            
            # Seleciona números de cada dezena
            for d, qtd in distribuicao.items():
                jogo.extend(random.sample(dezenas[d], min(qtd, len(dezenas[d]))))
            
            # Balanceia pares/ímpares
            pares = [n for n in jogo if n % 2 == 0]
            impares = [n for n in jogo if n % 2 == 1]
            
            proporcao_pares = media_pi['pares'] / (media_pi['pares'] + media_pi['impares']) if (media_pi['pares'] + media_pi['impares']) > 0 else 0.5
            target_pares = max(20, int(round(proporcao_pares * 50)))
            target_impares = 50 - target_pares
            
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
            
            jogo = sorted(jogo[:50])
            if jogo not in jogos:
                jogos.append(jogo)
        
        return jogos
    
    def fechamento_por_atraso(self, quantidade_jogos: int = 10) -> List[List[int]]:
        """Gera jogos baseados em números mais atrasados"""
        atrasos = self.analisador.calcular_atraso()
        numeros_ordenados_por_atraso = sorted(atrasos.items(), key=lambda x: x[1], reverse=True)
        
        numeros_atrasados = [num for num, _ in numeros_ordenados_por_atraso[:70]]
        
        jogos = []
        for _ in range(quantidade_jogos):
            jogo = sorted(random.sample(numeros_atrasados, min(50, len(numeros_atrasados))))
            if jogo not in jogos:
                jogos.append(jogo)
        
        return jogos
    
    def fechamento_misto(self, quantidade_jogos: int = 10) -> List[List[int]]:
        """
        ESTRATÉGIA OTIMIZADA PARA LOTOMANIA:
        - 30% números quentes (tendência recente)
        - 25% números atrasados (lei dos grandes números)
        - 20% números de alta frequência histórica
        - 20% distribuição equilibrada por dezenas (00-09, 10-19, etc)
        - 5% números aleatórios (diversificação)
        
        Garante cobertura de todas as 10 dezenas para maximizar chances.
        """
        stats = self.analisador.get_estatisticas_completas()
        quentes = stats.get('numeros_quentes', [])
        atrasados = stats.get('numeros_atrasados', [])
        mais_sorteados = [num for num, _ in self.analisador.numeros_mais_sorteados(50)]
        media_dezenas = stats.get('media_dezenas', {})
        
        # Define dezenas (00-09, 10-19, 20-29, etc)
        dezenas = {}
        for i in range(10):
            dezenas[f'D{i}'] = list(range(i * 10, (i + 1) * 10))
        
        jogos = []
        
        for _ in range(quantidade_jogos):
            jogo = []
            numeros_usados = set()
            
            # 30% números quentes (15 números)
            if quentes:
                quentes_disponiveis = [n for n in quentes if n not in numeros_usados]
                if quentes_disponiveis:
                    selecionados = random.sample(quentes_disponiveis, min(15, len(quentes_disponiveis)))
                    jogo.extend(selecionados)
                    numeros_usados.update(selecionados)
            
            # 25% números atrasados (12-13 números)
            if atrasados:
                atrasados_disponiveis = [n for n in atrasados if n not in numeros_usados]
                if atrasados_disponiveis:
                    selecionados = random.sample(atrasados_disponiveis, min(12, len(atrasados_disponiveis)))
                    jogo.extend(selecionados)
                    numeros_usados.update(selecionados)
            
            # 20% números de alta frequência (10 números)
            frequencia_disponiveis = [n for n in mais_sorteados if n not in numeros_usados]
            if frequencia_disponiveis:
                selecionados = random.sample(frequencia_disponiveis, min(10, len(frequencia_disponiveis)))
                jogo.extend(selecionados)
                numeros_usados.update(selecionados)
            
            # 20% distribuição equilibrada por dezenas (10 números - 1 por dezena prioritariamente)
            # Garante cobertura de todas as 10 dezenas
            qtd_por_dezena = 10 // 10  # 1 número por dezena mínimo
            for i in range(10):
                if len(jogo) >= 50:
                    break
                d_key = f'D{i}'
                dezena_disponiveis = [n for n in dezenas[d_key] if n not in numeros_usados]
                if dezena_disponiveis:
                    # Prioriza números da dezena que ainda não estão no jogo
                    selecionados = random.sample(dezena_disponiveis, min(qtd_por_dezena + 1, len(dezena_disponiveis)))
                    jogo.extend(selecionados)
                    numeros_usados.update(selecionados)
            
            # 5% números aleatórios para completar (2-3 números)
            todos_disponiveis = [n for n in self.numeros_range if n not in numeros_usados]
            faltam = 50 - len(jogo)
            if faltam > 0 and todos_disponiveis:
                selecionados = random.sample(todos_disponiveis, min(faltam, len(todos_disponiveis)))
                jogo.extend(selecionados)
            
            # Garante exatamente 50 números
            jogo = sorted(list(set(jogo))[:50])
            while len(jogo) < 50:
                disponiveis = [n for n in self.numeros_range if n not in jogo]
                if disponiveis:
                    jogo.append(random.choice(disponiveis))
                    jogo = sorted(jogo)
                else:
                    break
            
            if len(jogo) == 50 and jogo not in jogos:
                jogos.append(jogo)
        
        return jogos
    
    def fechamento_matriz(self, numeros_fixos: List[int], quantidade_jogos: int = 10) -> List[List[int]]:
        """Gera fechamento usando matriz de cobertura"""
        if len(numeros_fixos) >= 50:
            jogos = []
            for _ in range(quantidade_jogos):
                jogo = sorted(random.sample(numeros_fixos, 50))
                if jogo not in jogos:
                    jogos.append(jogo)
            return jogos
        
        jogos = []
        numeros_restantes = [n for n in self.numeros_range if n not in numeros_fixos]
        
        for _ in range(quantidade_jogos):
            jogo = numeros_fixos.copy()
            
            qtd_restante = 50 - len(jogo)
            if qtd_restante > 0 and numeros_restantes:
                jogo.extend(random.sample(numeros_restantes, min(qtd_restante, len(numeros_restantes))))
            
            jogo = sorted(jogo[:50])
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
        """Valida se um jogo está correto (50 números entre 0 e 99)"""
        if len(jogo) != 50:
            return False
        if not all(0 <= n <= 99 for n in jogo):
            return False
        if len(set(jogo)) != 50:
            return False
        return True

