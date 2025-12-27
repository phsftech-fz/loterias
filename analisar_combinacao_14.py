"""
Script para encontrar a combinação de 14 números que mais apareceu no histórico da Lotofácil
"""
import json
from collections import Counter
from itertools import combinations
from src.historico import HistoricoLotofacil

def analisar_combinacoes_14():
    """Analisa todas as combinações de 14 números e encontra a mais frequente"""
    
    # Carrega o histórico
    print("Carregando histórico...")
    historico_manager = HistoricoLotofacil(usar_banco=True)
    historico = historico_manager.get_historico()
    
    if not historico:
        print("Nenhum histórico encontrado. Tentando atualizar...")
        historico = historico_manager.atualizar_historico(usar_api=False)
    
    if not historico:
        print("ERRO: Não foi possível carregar o histórico")
        return
    
    print(f"Histórico carregado: {len(historico)} concursos")
    
    # Contador para todas as combinações de 14 números
    combinacoes_14 = Counter()
    
    # Para cada concurso (que tem 15 números), gera todas as combinações de 14
    print("Analisando combinações de 14 números...")
    total_concursos = len(historico)
    
    for idx, concurso in enumerate(historico):
        numeros = concurso.get('numeros', [])
        
        if len(numeros) != 15:
            continue
        
        # Gera todas as combinações de 14 números a partir dos 15
        # (são 15 combinações possíveis: remover cada um dos 15 números)
        for combo_14 in combinations(sorted(numeros), 14):
            # Usa tupla ordenada como chave
            combinacoes_14[combo_14] += 1
        
        # Mostra progresso a cada 100 concursos
        if (idx + 1) % 100 == 0:
            print(f"  Processados {idx + 1}/{total_concursos} concursos...")
    
    print(f"\nTotal de combinações de 14 números encontradas: {len(combinacoes_14)}")
    
    # Encontra a combinação mais frequente
    if combinacoes_14:
        combinacao_mais_frequente, quantidade = combinacoes_14.most_common(1)[0]
        
        print("\n" + "="*60)
        print("RESULTADO:")
        print("="*60)
        print(f"Combinação de 14 números mais frequente:")
        print(f"  Números: {sorted(combinacao_mais_frequente)}")
        print(f"  Frequência: {quantidade} vezes")
        print(f"  Percentual: {(quantidade / total_concursos) * 100:.2f}% dos concursos")
        print("="*60)
        
        # Mostra as top 10 combinações
        print("\nTop 10 combinações de 14 números mais frequentes:")
        print("-" * 60)
        for i, (combo, freq) in enumerate(combinacoes_14.most_common(10), 1):
            print(f"{i}. {sorted(combo)} - {freq} vezes")
        
        return {
            'combinacao': sorted(combinacao_mais_frequente),
            'frequencia': quantidade,
            'total_concursos': total_concursos
        }
    else:
        print("Nenhuma combinação encontrada")
        return None

if __name__ == "__main__":
    resultado = analisar_combinacoes_14()

