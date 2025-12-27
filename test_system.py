"""
Script para testar o sistema para sustentar o Girinho com a Loto Fácil
"""
from src.historico import HistoricoLotofacil
from src.analise import AnalisadorLotofacil
from src.fechamento import GeradorFechamento

def main():
    print("=" * 60)
    print("SISTEMA PARA SUSTENTAR O GIRINHO COM A LOTO FACIL - TESTE")
    print("=" * 60)
    
    # Carrega histórico
    print("\n[1/4] Carregando histórico...")
    historico_manager = HistoricoLotofacil()
    historico = historico_manager.atualizar_historico(usar_api=True)
    
    if not historico:
        print("⚠️  Não foi possível carregar histórico. Usando dados de exemplo...")
        # Dados de exemplo para teste
        historico = [
            {'concurso': 1, 'numeros': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], 'data': '2024-01-01'},
            {'concurso': 2, 'numeros': [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16], 'data': '2024-01-02'},
        ]
    
    print(f"✓ Histórico carregado: {len(historico)} concursos")
    
    # Analisa padrões
    print("\n[2/4] Analisando padrões...")
    analisador = AnalisadorLotofacil(historico)
    stats = analisador.get_estatisticas_completas()
    
    print(f"✓ Total de concursos analisados: {stats['total_concursos']}")
    print(f"✓ Números quentes: {stats['numeros_quentes']}")
    print(f"✓ Números atrasados: {len(stats['numeros_atrasados'])}")
    
    # Gera fechamento
    print("\n[3/4] Gerando fechamento...")
    gerador = GeradorFechamento(analisador, historico)
    
    estrategias = ['misto', 'frequencia', 'balanceado', 'atraso']
    
    for estrategia in estrategias:
        print(f"\n  Estratégia: {estrategia.upper()}")
        jogos = gerador.gerar_fechamento_completo(estrategia=estrategia, quantidade_jogos=3)
        
        for i, jogo in enumerate(jogos, 1):
            numeros_str = ' '.join([f"{n:02d}" for n in jogo])
            print(f"    Jogo {i}: {numeros_str}")
    
    # Testa validação
    print("\n[4/4] Testando validação...")
    jogo_valido = list(range(1, 16))
    jogo_invalido = list(range(1, 14))  # Apenas 13 números
    
    print(f"  Jogo válido (15 números): {gerador.validar_jogo(jogo_valido)}")
    print(f"  Jogo inválido (13 números): {gerador.validar_jogo(jogo_invalido)}")
    
    print("\n" + "=" * 60)
    print("TESTE CONCLUÍDO COM SUCESSO!")
    print("=" * 60)
    print("\nPara usar a interface web, execute: python app.py")

if __name__ == '__main__':
    main()

