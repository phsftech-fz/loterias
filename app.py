"""
Aplicação Flask para interface web do sistema para sustentar o Girinho com a Loto Fácil e Timemania
"""
from flask import Flask, render_template, request, jsonify
from src.historico import HistoricoLotofacil
from src.analise import AnalisadorLotofacil
from src.fechamento import GeradorFechamento
from src.conferencia import ConferidorJogos
from src.historico_timemania import HistoricoTimemania
from src.analise_timemania import AnalisadorTimemania
from src.fechamento_timemania import GeradorFechamentoTimemania
from src.conferencia_timemania import ConferidorJogosTimemania
from src.historico_lotomania import HistoricoLotomania
from src.analise_lotomania import AnalisadorLotomania
from src.fechamento_lotomania import GeradorFechamentoLotomania
from src.conferencia_lotomania import ConferidorJogosLotomania
import json
import re

app = Flask(__name__)

# Inicializa componentes Lotofácil
historico_manager = HistoricoLotofacil(usar_banco=True)
historico = historico_manager.get_historico()
if not historico or len(historico) < 10:
    print("Banco vazio ou com poucos dados, buscando da API...")
    historico = historico_manager.atualizar_historico(usar_api=True)
analisador = AnalisadorLotofacil(historico)
gerador = GeradorFechamento(analisador, historico)
conferidor = ConferidorJogos(historico)

# Inicializa componentes Timemania
historico_manager_timemania = HistoricoTimemania(usar_banco=False)
historico_timemania = historico_manager_timemania.get_historico()
if not historico_timemania or len(historico_timemania) < 10:
    print("Cache Timemania vazio ou com poucos dados, buscando da API...")
    historico_timemania = historico_manager_timemania.atualizar_historico(usar_api=True)
analisador_timemania = AnalisadorTimemania(historico_timemania)
gerador_timemania = GeradorFechamentoTimemania(analisador_timemania, historico_timemania)
conferidor_timemania = ConferidorJogosTimemania(historico_timemania)

# Inicializa componentes Lotomania
historico_manager_lotomania = HistoricoLotomania(usar_banco=False)
historico_lotomania = historico_manager_lotomania.get_historico()
if not historico_lotomania or len(historico_lotomania) < 10:
    print("Cache Lotomania vazio ou com poucos dados, buscando da API...")
    historico_lotomania = historico_manager_lotomania.atualizar_historico(usar_api=True)
analisador_lotomania = AnalisadorLotomania(historico_lotomania)
gerador_lotomania = GeradorFechamentoLotomania(analisador_lotomania, historico_lotomania)
conferidor_lotomania = ConferidorJogosLotomania(historico_lotomania)


@app.route('/')
def index():
    """Página principal - Lotofácil"""
    return render_template('index.html')


@app.route('/timemania')
def timemania():
    """Página principal - Timemania"""
    return render_template('timemania.html')


@app.route('/lotomania')
def lotomania():
    """Página principal - Lotomania"""
    return render_template('lotomania.html')


@app.route('/api/estatisticas')
def get_estatisticas():
    """Retorna estatísticas completas"""
    try:
        stats = analisador.get_estatisticas_completas()
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/gerar-jogos', methods=['POST'])
def gerar_jogos():
    """Gera jogos baseado nos parâmetros"""
    try:
        data = request.get_json()
        estrategia = data.get('estrategia', 'misto')
        quantidade = int(data.get('quantidade', 10))
        quantidade_numeros = int(data.get('quantidade_numeros', 15))
        numeros_fixos = data.get('numeros_fixos', [])
        
        # Valida quantidade de números
        if quantidade_numeros < 15 or quantidade_numeros > 20:
            return jsonify({
                'success': False,
                'error': 'Quantidade de números deve ser entre 15 e 20'
            }), 400
        
        if numeros_fixos:
            numeros_fixos = [int(n) for n in numeros_fixos]
            # Valida que números fixos não excedem quantidade_numeros
            if len(numeros_fixos) > quantidade_numeros:
                return jsonify({
                    'success': False,
                    'error': f'Números fixos ({len(numeros_fixos)}) não podem exceder quantidade de números por jogo ({quantidade_numeros})'
                }), 400
        
        jogos = gerador.gerar_fechamento_completo(
            estrategia=estrategia,
            quantidade_jogos=quantidade,
            numeros_fixos=numeros_fixos if numeros_fixos else None,
            quantidade_numeros=quantidade_numeros
        )
        
        return jsonify({
            'success': True,
            'jogos': jogos,
            'quantidade': len(jogos),
            'quantidade_numeros': quantidade_numeros
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/atualizar-historico', methods=['POST'])
def atualizar_historico():
    """Atualiza histórico de concursos"""
    try:
        global historico, analisador, gerador, conferidor
        
        # Sincroniza banco de dados (busca apenas novos)
        if historico_manager.usar_banco:
            resultado_sync = historico_manager.sincronizar_banco()
            if resultado_sync.get('sucesso'):
                historico = historico_manager.get_historico()
            else:
                # Se sincronização falhou, tenta busca completa
                historico = historico_manager.atualizar_historico(usar_api=True)
        else:
            historico = historico_manager.atualizar_historico(usar_api=True)
        
        analisador = AnalisadorLotofacil(historico)
        gerador = GeradorFechamento(analisador, historico)
        conferidor = ConferidorJogos(historico)
        
        return jsonify({
            'success': True,
            'total_concursos': len(historico),
            'banco_atualizado': historico_manager.usar_banco
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/estatisticas-banco', methods=['GET'])
def estatisticas_banco():
    """Retorna estatísticas do banco de dados"""
    try:
        if historico_manager.usar_banco and historico_manager.db:
            total = historico_manager.db.contar_concursos()
            ultimo = historico_manager.db.obter_ultimo_concurso()
            
            return jsonify({
                'success': True,
                'total_concursos': total,
                'ultimo_concurso': ultimo['concurso'] if ultimo else None,
                'data_ultimo': ultimo.get('data', '') if ultimo else ''
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Banco de dados não está habilitado'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/historico')
def get_historico():
    """Retorna histórico de concursos"""
    try:
        limite = int(request.args.get('limite', 50))
        ultimos = historico[-limite:] if len(historico) > limite else historico
        return jsonify({
            'success': True,
            'concursos': ultimos,
            'total': len(historico)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/combinacao-mais-repetida')
def get_combinacao_mais_repetida():
    """Retorna a combinação de 15 números que mais se repetiu no histórico"""
    try:
        global analisador
        analisador = AnalisadorLotofacil(historico)
        resultado = analisador.combinacao_mais_repetida()
        
        return jsonify({
            'success': True,
            'combinacao': resultado['combinacao'],
            'quantidade': resultado['quantidade']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def parsear_arquivo_txt(conteudo: str) -> list:
    """
    Parseia arquivo TXT exportado pelo sistema
    Formato esperado:
    Jogo 01: 01 - 02 - 03 - 04 - 05 - 06 - 07 - 08 - 09 - 10 - 11 - 12 - 13 - 14 - 15
    """
    jogos = []
    linhas = conteudo.split('\n')
    
    for linha in linhas:
        linha = linha.strip()
        if not linha or linha.startswith('=') or 'JOGOS GERADOS' in linha.upper() or 'TOTAL' in linha.upper() or 'GERADO' in linha.upper() or 'QUANTIDADE' in linha.upper():
            continue
        
        # Procura padrão: Jogo XX: números ou Jogo XX (Y números): números
        # Aceita ambos os formatos: "Jogo 01:" e "Jogo 01 (17 números):"
        match = re.search(r'Jogo\s+\d+(?:\s*\([^)]+\))?:\s*(.+)', linha, re.IGNORECASE)
        if match:
            numeros_str = match.group(1)
            # Extrai números (formato: 01 - 02 - 03 ou 1, 2, 3)
            # Usa regex mais específica para números de 1 a 25
            numeros = re.findall(r'\b(0?[1-9]|1[0-9]|2[0-5])\b', numeros_str)
            if numeros:
                try:
                    jogo = [int(n) for n in numeros if 1 <= int(n) <= 25]
                    # Remove duplicatas mantendo ordem
                    jogo = list(dict.fromkeys(jogo))
                    # Aceita jogos com 15-20 números
                    if 15 <= len(jogo) <= 20:
                        jogos.append(sorted(jogo))
                except ValueError:
                    continue
        else:
            # Tenta extrair números diretamente da linha (fallback)
            numeros = re.findall(r'\b(0?[1-9]|1[0-9]|2[0-5])\b', linha)
            # Aceita jogos com 15-20 números
            if 15 <= len(numeros) <= 20:
                try:
                    jogo = [int(n) for n in numeros]
                    # Remove duplicatas
                    jogo = list(dict.fromkeys(jogo))
                    if 15 <= len(jogo) <= 20:
                        jogos.append(sorted(jogo))
                except ValueError:
                    continue
    
    return jogos


@app.route('/api/importar-jogos', methods=['POST'])
def importar_jogos():
    """Importa jogos de arquivo TXT e confere"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Nenhum arquivo enviado'
            }), 400
        
        arquivo = request.files['file']
        if arquivo.filename == '':
            return jsonify({
                'success': False,
                'error': 'Nenhum arquivo selecionado'
            }), 400
        
        # Lê conteúdo do arquivo
        conteudo = arquivo.read().decode('utf-8')
        
        # Parseia jogos
        jogos = parsear_arquivo_txt(conteudo)
        
        if not jogos:
            return jsonify({
                'success': False,
                'error': 'Nenhum jogo válido encontrado no arquivo'
            }), 400
        
        # Atualiza conferidor com histórico atual
        global conferidor
        conferidor = ConferidorJogos(historico)
        
        # Confere jogos
        resultado = conferidor.conferir_completo(jogos)
        
        return jsonify({
            'success': True,
            'jogos_importados': len(jogos),
            'resultado': resultado
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/conferir-jogos', methods=['POST'])
def conferir_jogos():
    """Confere lista de jogos enviada via JSON"""
    try:
        data = request.get_json()
        jogos = data.get('jogos', [])
        
        if not jogos:
            return jsonify({
                'success': False,
                'error': 'Nenhum jogo fornecido'
            }), 400
        
        # Valida jogos (aceita 15-20 números)
        jogos_validos = []
        for jogo in jogos:
            if isinstance(jogo, list) and 15 <= len(jogo) <= 20:
                try:
                    jogo_int = [int(n) for n in jogo if 1 <= int(n) <= 25]
                    # Remove duplicatas
                    jogo_int = list(dict.fromkeys(jogo_int))
                    if 15 <= len(jogo_int) <= 20:
                        jogos_validos.append(sorted(jogo_int))
                except (ValueError, TypeError):
                    continue
        
        if not jogos_validos:
            return jsonify({
                'success': False,
                'error': 'Nenhum jogo válido encontrado'
            }), 400
        
        # Atualiza conferidor
        global conferidor
        conferidor = ConferidorJogos(historico)
        
        # Confere jogos
        resultado = conferidor.conferir_completo(jogos_validos)
        
        return jsonify({
            'success': True,
            'jogos_conferidos': len(jogos_validos),
            'resultado': resultado
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== ROTAS TIMEMANIA ====================

@app.route('/api/timemania/estatisticas')
def get_estatisticas_timemania():
    """Retorna estatísticas completas da Timemania"""
    try:
        global analisador_timemania
        analisador_timemania = AnalisadorTimemania(historico_timemania)
        stats = analisador_timemania.get_estatisticas_completas()
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/timemania/gerar-jogos', methods=['POST'])
def gerar_jogos_timemania():
    """Gera jogos da Timemania baseado nos parâmetros"""
    try:
        data = request.get_json()
        estrategia = data.get('estrategia', 'misto')
        quantidade = int(data.get('quantidade', 10))
        numeros_fixos = data.get('numeros_fixos', [])
        
        if numeros_fixos:
            numeros_fixos = [int(n) for n in numeros_fixos]
            if len(numeros_fixos) > 10:
                return jsonify({
                    'success': False,
                    'error': f'Números fixos ({len(numeros_fixos)}) não podem exceder 10 números por jogo'
                }), 400
        
        jogos = gerador_timemania.gerar_fechamento_completo(
            estrategia=estrategia,
            quantidade_jogos=quantidade,
            numeros_fixos=numeros_fixos if numeros_fixos else None
        )
        
        return jsonify({
            'success': True,
            'jogos': jogos,
            'quantidade': len(jogos),
            'quantidade_numeros': 10
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/timemania/atualizar-historico', methods=['POST'])
def atualizar_historico_timemania():
    """Atualiza histórico de concursos da Timemania"""
    try:
        global historico_timemania, analisador_timemania, gerador_timemania, conferidor_timemania
        
        historico_timemania = historico_manager_timemania.atualizar_historico(usar_api=True)
        analisador_timemania = AnalisadorTimemania(historico_timemania)
        gerador_timemania = GeradorFechamentoTimemania(analisador_timemania, historico_timemania)
        conferidor_timemania = ConferidorJogosTimemania(historico_timemania)
        
        return jsonify({
            'success': True,
            'total_concursos': len(historico_timemania)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/timemania/combinacao-mais-repetida')
def get_combinacao_mais_repetida_timemania():
    """Retorna a combinação de 10 números que mais se repetiu no histórico da Timemania"""
    try:
        global analisador_timemania
        analisador_timemania = AnalisadorTimemania(historico_timemania)
        resultado = analisador_timemania.combinacao_mais_repetida()
        
        return jsonify({
            'success': True,
            'combinacao': resultado['combinacao'],
            'quantidade': resultado['quantidade']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def parsear_arquivo_txt_timemania(conteudo: str) -> list:
    """Parseia arquivo TXT exportado pelo sistema para Timemania"""
    jogos = []
    linhas = conteudo.split('\n')
    
    for linha in linhas:
        linha = linha.strip()
        if not linha or linha.startswith('=') or 'JOGOS GERADOS' in linha.upper() or 'TOTAL' in linha.upper() or 'GERADO' in linha.upper() or 'QUANTIDADE' in linha.upper():
            continue
        
        match = re.search(r'Jogo\s+\d+(?:\s*\([^)]+\))?:\s*(.+)', linha, re.IGNORECASE)
        if match:
            numeros_str = match.group(1)
            numeros = re.findall(r'\b(0?[1-9]|[1-7][0-9]|80)\b', numeros_str)
            if numeros:
                try:
                    jogo = [int(n) for n in numeros if 1 <= int(n) <= 80]
                    jogo = list(dict.fromkeys(jogo))
                    if len(jogo) == 10:
                        jogos.append(sorted(jogo))
                except ValueError:
                    continue
    
    return jogos


@app.route('/api/timemania/importar-jogos', methods=['POST'])
def importar_jogos_timemania():
    """Importa jogos de arquivo TXT e confere - Timemania"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Nenhum arquivo enviado'
            }), 400
        
        arquivo = request.files['file']
        if arquivo.filename == '':
            return jsonify({
                'success': False,
                'error': 'Nenhum arquivo selecionado'
            }), 400
        
        conteudo = arquivo.read().decode('utf-8')
        jogos = parsear_arquivo_txt_timemania(conteudo)
        
        if not jogos:
            return jsonify({
                'success': False,
                'error': 'Nenhum jogo válido encontrado no arquivo'
            }), 400
        
        global conferidor_timemania
        conferidor_timemania = ConferidorJogosTimemania(historico_timemania)
        
        resultado = conferidor_timemania.conferir_completo(jogos)
        
        return jsonify({
            'success': True,
            'jogos_importados': len(jogos),
            'resultado': resultado
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/timemania/conferir-jogos', methods=['POST'])
def conferir_jogos_timemania():
    """Confere jogos enviados via JSON - Timemania"""
    try:
        data = request.get_json()
        jogos = data.get('jogos', [])
        
        jogos_validos = []
        for jogo in jogos:
            if isinstance(jogo, list) and len(jogo) == 10:
                try:
                    jogo_int = [int(n) for n in jogo if 1 <= int(n) <= 80]
                    jogo_int = list(dict.fromkeys(jogo_int))
                    if len(jogo_int) == 10:
                        jogos_validos.append(sorted(jogo_int))
                except (ValueError, TypeError):
                    continue
        
        if not jogos_validos:
            return jsonify({
                'success': False,
                'error': 'Nenhum jogo válido encontrado'
            }), 400
        
        global conferidor_timemania
        conferidor_timemania = ConferidorJogosTimemania(historico_timemania)
        
        resultado = conferidor_timemania.conferir_completo(jogos_validos)
        
        return jsonify({
            'success': True,
            'jogos_conferidos': len(jogos_validos),
            'resultado': resultado
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ========== ROTAS LOTOMANIA ==========

@app.route('/api/lotomania/estatisticas')
def get_estatisticas_lotomania():
    """Retorna estatísticas completas da Lotomania"""
    try:
        global analisador_lotomania
        analisador_lotomania = AnalisadorLotomania(historico_lotomania)
        stats = analisador_lotomania.get_estatisticas_completas()
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/lotomania/gerar-jogos', methods=['POST'])
def gerar_jogos_lotomania():
    """Gera jogos da Lotomania baseado nos parâmetros"""
    try:
        data = request.get_json()
        estrategia = data.get('estrategia', 'misto')
        quantidade = int(data.get('quantidade', 10))
        numeros_fixos = data.get('numeros_fixos', [])
        
        if numeros_fixos:
            numeros_fixos = [int(n) for n in numeros_fixos]
            if len(numeros_fixos) > 50:
                return jsonify({
                    'success': False,
                    'error': f'Números fixos ({len(numeros_fixos)}) não podem exceder 50 números por jogo'
                }), 400
        
        jogos = gerador_lotomania.gerar_fechamento_completo(
            estrategia=estrategia,
            quantidade_jogos=quantidade,
            numeros_fixos=numeros_fixos if numeros_fixos else None
        )
        
        return jsonify({
            'success': True,
            'jogos': jogos,
            'quantidade': len(jogos),
            'quantidade_numeros': 50
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/lotomania/atualizar-historico', methods=['POST'])
def atualizar_historico_lotomania():
    """Atualiza histórico de concursos da Lotomania"""
    try:
        global historico_lotomania, analisador_lotomania, gerador_lotomania, conferidor_lotomania
        
        historico_lotomania = historico_manager_lotomania.atualizar_historico(usar_api=True)
        analisador_lotomania = AnalisadorLotomania(historico_lotomania)
        gerador_lotomania = GeradorFechamentoLotomania(analisador_lotomania, historico_lotomania)
        conferidor_lotomania = ConferidorJogosLotomania(historico_lotomania)
        
        return jsonify({
            'success': True,
            'total_concursos': len(historico_lotomania)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/lotomania/combinacao-mais-repetida')
def get_combinacao_mais_repetida_lotomania():
    """Retorna a combinação de 20 números que mais se repetiu no histórico da Lotomania"""
    try:
        global analisador_lotomania
        analisador_lotomania = AnalisadorLotomania(historico_lotomania)
        resultado = analisador_lotomania.combinacao_mais_repetida()
        
        return jsonify({
            'success': True,
            'combinacao': resultado['combinacao'],
            'quantidade': resultado['quantidade']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def parsear_arquivo_txt_lotomania(conteudo: str) -> list:
    """Parseia arquivo TXT exportado pelo sistema para Lotomania"""
    jogos = []
    linhas = conteudo.split('\n')
    
    for linha in linhas:
        linha = linha.strip()
        if not linha or linha.startswith('=') or 'JOGOS GERADOS' in linha.upper() or 'TOTAL' in linha.upper() or 'GERADO' in linha.upper() or 'QUANTIDADE' in linha.upper():
            continue
        
        match = re.search(r'Jogo\s+\d+(?:\s*\([^)]+\))?:\s*(.+)', linha, re.IGNORECASE)
        if match:
            numeros_str = match.group(1)
            # Lotomania: números de 00 a 99
            numeros = re.findall(r'\b([0-9]|[1-9][0-9])\b', numeros_str)
            if numeros:
                try:
                    jogo = [int(n) for n in numeros if 0 <= int(n) <= 99]
                    jogo = list(dict.fromkeys(jogo))
                    if len(jogo) == 50:  # Lotomania: 50 números por jogo
                        jogos.append(sorted(jogo))
                except ValueError:
                    continue
    
    return jogos


@app.route('/api/lotomania/importar-jogos', methods=['POST'])
def importar_jogos_lotomania():
    """Importa jogos de arquivo TXT e confere - Lotomania"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Nenhum arquivo enviado'
            }), 400
        
        arquivo = request.files['file']
        if arquivo.filename == '':
            return jsonify({
                'success': False,
                'error': 'Nenhum arquivo selecionado'
            }), 400
        
        conteudo = arquivo.read().decode('utf-8')
        jogos = parsear_arquivo_txt_lotomania(conteudo)
        
        if not jogos:
            return jsonify({
                'success': False,
                'error': 'Nenhum jogo válido encontrado no arquivo'
            }), 400
        
        global conferidor_lotomania
        conferidor_lotomania = ConferidorJogosLotomania(historico_lotomania)
        
        resultado = conferidor_lotomania.conferir_completo(jogos)
        
        return jsonify({
            'success': True,
            'jogos_importados': len(jogos),
            'resultado': resultado
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/lotomania/conferir-jogos', methods=['POST'])
def conferir_jogos_lotomania():
    """Confere jogos enviados via JSON - Lotomania"""
    try:
        data = request.get_json()
        jogos = data.get('jogos', [])
        
        jogos_validos = []
        for jogo in jogos:
            if isinstance(jogo, list) and len(jogo) == 50:  # Lotomania: 50 números
                try:
                    jogo_int = [int(n) for n in jogo if 0 <= int(n) <= 99]
                    jogo_int = list(dict.fromkeys(jogo_int))
                    if len(jogo_int) == 50:
                        jogos_validos.append(sorted(jogo_int))
                except (ValueError, TypeError):
                    continue
        
        if not jogos_validos:
            return jsonify({
                'success': False,
                'error': 'Nenhum jogo válido encontrado'
            }), 400
        
        global conferidor_lotomania
        conferidor_lotomania = ConferidorJogosLotomania(historico_lotomania)
        
        resultado = conferidor_lotomania.conferir_completo(jogos_validos)
        
        return jsonify({
            'success': True,
            'jogos_conferidos': len(jogos_validos),
            'resultado': resultado
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

