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
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ==================== VALIDAÇÕES DE SEGURANÇA ====================

# Limites de segurança
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_LINES = 10000  # Máximo de linhas no arquivo
MAX_JOGOS_IMPORT = 1000  # Máximo de jogos por importação
MAX_QUANTIDADE_JOGOS = 100  # Máximo de jogos gerados por vez
ALLOWED_EXTENSIONS = {'txt'}

def allowed_file(filename: str) -> bool:
    """Valida se o arquivo tem extensão permitida"""
    if not filename:
        return False
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_filename(filename: str) -> tuple[bool, str, str]:
    """Valida e sanitiza nome de arquivo - proteção contra path traversal"""
    if not filename:
        return False, "Nome de arquivo vazio", ""
    
    # Sanitiza nome do arquivo
    safe_filename = secure_filename(filename)
    
    # Verifica path traversal (../, ..\, etc)
    if '..' in filename or '/' in filename or '\\' in filename:
        return False, "Nome de arquivo inválido - contém caracteres não permitidos", ""
    
    # Verifica extensão
    if not allowed_file(safe_filename):
        return False, "Apenas arquivos .txt são permitidos", ""
    
    # Limita tamanho do nome
    if len(safe_filename) > 255:
        return False, "Nome de arquivo muito longo", ""
    
    return True, "", safe_filename

def validate_file_size(file) -> tuple[bool, str]:
    """Valida tamanho do arquivo"""
    try:
        # Verifica tamanho do arquivo
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Volta ao início
        
        if file_size > MAX_FILE_SIZE:
            return False, f"Arquivo muito grande. Tamanho máximo: {MAX_FILE_SIZE / (1024*1024):.1f}MB"
        
        if file_size == 0:
            return False, "Arquivo vazio"
        
        return True, ""
    except Exception as e:
        return False, f"Erro ao validar tamanho do arquivo: {str(e)}"

def validate_file_content(content: str) -> tuple[bool, str]:
    """Valida conteúdo do arquivo"""
    if not content:
        return False, "Conteúdo do arquivo vazio"
    
    # Limita tamanho do conteúdo (em caracteres)
    if len(content) > MAX_FILE_SIZE:
        return False, f"Conteúdo do arquivo muito grande. Máximo: {MAX_FILE_SIZE / (1024*1024):.1f}MB"
    
    # Limita número de linhas
    lines = content.split('\n')
    if len(lines) > MAX_LINES:
        return False, f"Arquivo contém muitas linhas. Máximo: {MAX_LINES} linhas"
    
    # Verifica caracteres não permitidos (proteção contra scripts)
    # Permite apenas caracteres alfanuméricos, espaços, pontuação básica e quebras de linha
    dangerous_patterns = ['<script', 'javascript:', 'onerror=', 'onload=', 'eval(', 'exec(']
    content_lower = content.lower()
    for pattern in dangerous_patterns:
        if pattern in content_lower:
            return False, f"Conteúdo do arquivo contém código potencialmente perigoso"
    
    return True, ""

def validate_numeros_list(numeros: list, min_num: int, max_num: int, max_quantidade: int = None) -> tuple[bool, str, list]:
    """Valida lista de números"""
    if not isinstance(numeros, list):
        return False, "Números devem ser uma lista", []
    
    if max_quantidade and len(numeros) > max_quantidade:
        return False, f"Máximo de {max_quantidade} números permitidos", []
    
    try:
        numeros_validos = []
        for num in numeros:
            # Converte para int
            if not isinstance(num, (int, str)):
                continue
            
            num_int = int(num)
            
            # Valida range
            if num_int < min_num or num_int > max_num:
                continue
            
            # Adiciona apenas se não for duplicata
            if num_int not in numeros_validos:
                numeros_validos.append(num_int)
        
        return True, "", numeros_validos
    except (ValueError, TypeError):
        return False, "Números inválidos", []

def validate_quantidade(quantidade: any, min_val: int, max_val: int) -> tuple[bool, str, int]:
    """Valida quantidade numérica"""
    try:
        qtd = int(quantidade)
        if qtd < min_val or qtd > max_val:
            return False, f"Quantidade deve estar entre {min_val} e {max_val}", 0
        return True, "", qtd
    except (ValueError, TypeError):
        return False, "Quantidade inválida", 0

def validate_estrategia(estrategia: str, estrategias_validas: list) -> tuple[bool, str]:
    """Valida estratégia escolhida"""
    if not isinstance(estrategia, str):
        return False, "Estratégia inválida"
    
    if estrategia not in estrategias_validas:
        return False, f"Estratégia deve ser uma das seguintes: {', '.join(estrategias_validas)}"
    
    return True, ""

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
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados inválidos'
            }), 400
        
        # Valida estratégia
        estrategia = data.get('estrategia', 'misto')
        estrategias_validas = ['misto', 'frequencia', 'balanceado', 'atraso']
        is_valid_estrategia, error_msg = validate_estrategia(estrategia, estrategias_validas)
        if not is_valid_estrategia:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # Valida quantidade de jogos
        quantidade = data.get('quantidade', 10)
        is_valid_qtd, error_msg, quantidade = validate_quantidade(quantidade, 1, MAX_QUANTIDADE_JOGOS)
        if not is_valid_qtd:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # Valida quantidade de números por jogo
        quantidade_numeros = data.get('quantidade_numeros', 15)
        is_valid_qtd_nums, error_msg, quantidade_numeros = validate_quantidade(quantidade_numeros, 15, 20)
        if not is_valid_qtd_nums:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # Valida números fixos
        numeros_fixos = data.get('numeros_fixos', [])
        if numeros_fixos:
            is_valid_nums, error_msg, numeros_fixos = validate_numeros_list(
                numeros_fixos, 
                min_num=1, 
                max_num=25, 
                max_quantidade=quantidade_numeros
            )
            if not is_valid_nums:
                return jsonify({
                    'success': False,
                    'error': error_msg
                }), 400
            
            # Valida que números fixos não excedem quantidade_numeros
            if len(numeros_fixos) > quantidade_numeros:
                return jsonify({
                    'success': False,
                    'error': f'Números fixos ({len(numeros_fixos)}) não podem exceder quantidade de números por jogo ({quantidade_numeros})'
                }), 400
        else:
            numeros_fixos = None
        
        jogos = gerador.gerar_fechamento_completo(
            estrategia=estrategia,
            quantidade_jogos=quantidade,
            numeros_fixos=numeros_fixos,
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
            'error': f'Erro ao gerar jogos: {str(e)}'
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
        # Validação: verifica se arquivo foi enviado
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Nenhum arquivo enviado'
            }), 400
        
        arquivo = request.files['file']
        
        # Validação: verifica se arquivo foi selecionado
        if arquivo.filename == '':
            return jsonify({
                'success': False,
                'error': 'Nenhum arquivo selecionado'
            }), 400
        
        # Validação: nome do arquivo
        is_valid_filename, error_msg, safe_filename = validate_filename(arquivo.filename)
        if not is_valid_filename:
            return jsonify({
                'success': False,
                'error': error_msg or 'Nome de arquivo inválido'
            }), 400
        
        # Validação: tamanho do arquivo
        is_valid_size, error_msg = validate_file_size(arquivo)
        if not is_valid_size:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # Lê conteúdo do arquivo com tratamento de encoding
        try:
            conteudo = arquivo.read().decode('utf-8')
        except UnicodeDecodeError:
            # Tenta outros encodings comuns
            arquivo.seek(0)
            try:
                conteudo = arquivo.read().decode('latin-1')
            except:
                return jsonify({
                    'success': False,
                    'error': 'Erro ao decodificar arquivo. Use UTF-8 ou Latin-1'
                }), 400
        
        # Validação: conteúdo do arquivo
        is_valid_content, error_msg = validate_file_content(conteudo)
        if not is_valid_content:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # Parseia jogos
        jogos = parsear_arquivo_txt(conteudo)
        
        # Validação: verifica se encontrou jogos
        if not jogos:
            return jsonify({
                'success': False,
                'error': 'Nenhum jogo válido encontrado no arquivo'
            }), 400
        
        # Validação: limite de jogos por importação
        if len(jogos) > MAX_JOGOS_IMPORT:
            return jsonify({
                'success': False,
                'error': f'Máximo de {MAX_JOGOS_IMPORT} jogos por importação. Arquivo contém {len(jogos)} jogos'
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
            'error': f'Erro ao processar arquivo: {str(e)}'
        }), 500


@app.route('/api/conferir-jogos', methods=['POST'])
def conferir_jogos():
    """Confere lista de jogos enviada via JSON"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados inválidos'
            }), 400
        
        jogos = data.get('jogos', [])
        
        if not isinstance(jogos, list):
            return jsonify({
                'success': False,
                'error': 'Jogos devem ser uma lista'
            }), 400
        
        if not jogos:
            return jsonify({
                'success': False,
                'error': 'Nenhum jogo fornecido'
            }), 400
        
        # Validação: limite de jogos por conferência
        if len(jogos) > MAX_JOGOS_IMPORT:
            return jsonify({
                'success': False,
                'error': f'Máximo de {MAX_JOGOS_IMPORT} jogos por conferência'
            }), 400
        
        # Valida jogos (aceita 15-20 números)
        jogos_validos = []
        for idx, jogo in enumerate(jogos):
            if not isinstance(jogo, list):
                continue
            
            if not (15 <= len(jogo) <= 20):
                continue
            
            # Valida números do jogo
            is_valid, error_msg, jogo_validado = validate_numeros_list(
                jogo,
                min_num=1,
                max_num=25,
                max_quantidade=20
            )
            
            if is_valid and 15 <= len(jogo_validado) <= 20:
                jogos_validos.append(sorted(jogo_validado))
        
        if not jogos_validos:
            return jsonify({
                'success': False,
                'error': 'Nenhum jogo válido encontrado. Jogos devem ter entre 15 e 20 números de 1 a 25'
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
            'error': f'Erro ao conferir jogos: {str(e)}'
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
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados inválidos'
            }), 400
        
        # Valida estratégia
        estrategia = data.get('estrategia', 'misto')
        estrategias_validas = ['misto', 'frequencia', 'balanceado', 'atraso']
        is_valid_estrategia, error_msg = validate_estrategia(estrategia, estrategias_validas)
        if not is_valid_estrategia:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # Valida quantidade de jogos
        quantidade = data.get('quantidade', 10)
        is_valid_qtd, error_msg, quantidade = validate_quantidade(quantidade, 1, MAX_QUANTIDADE_JOGOS)
        if not is_valid_qtd:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # Valida números fixos (Timemania: 1-80, máximo 10)
        numeros_fixos = data.get('numeros_fixos', [])
        if numeros_fixos:
            is_valid_nums, error_msg, numeros_fixos = validate_numeros_list(
                numeros_fixos,
                min_num=1,
                max_num=80,
                max_quantidade=10
            )
            if not is_valid_nums:
                return jsonify({
                    'success': False,
                    'error': error_msg
                }), 400
            
            if len(numeros_fixos) > 10:
                return jsonify({
                    'success': False,
                    'error': f'Números fixos ({len(numeros_fixos)}) não podem exceder 10 números por jogo'
                }), 400
        else:
            numeros_fixos = None
        
        resultado = gerador_timemania.gerar_fechamento_completo(
            estrategia=estrategia,
            quantidade_jogos=quantidade,
            numeros_fixos=numeros_fixos
        )
        
        jogos = resultado.get('jogos', [])
        time_sugerido = resultado.get('time_sugerido', {})
        
        return jsonify({
            'success': True,
            'jogos': jogos,
            'quantidade': len(jogos),
            'quantidade_numeros': 10,
            'time_sugerido': time_sugerido
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao gerar jogos: {str(e)}'
        }), 500


@app.route('/api/timemania/historico')
def get_historico_timemania():
    """Retorna histórico de concursos da Timemania com times sorteados"""
    try:
        limite = int(request.args.get('limite', 50))
        limite = min(limite, 450)  # Limite máximo de segurança
        
        ultimos = historico_timemania[-limite:] if len(historico_timemania) > limite else historico_timemania
        
        # Garante que cada concurso tem time_coracao (mesmo que vazio)
        for concurso in ultimos:
            if 'time_coracao' not in concurso:
                concurso['time_coracao'] = ''
        
        return jsonify({
            'success': True,
            'concursos': ultimos,
            'total': len(historico_timemania)
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
        # Validação: verifica se arquivo foi enviado
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Nenhum arquivo enviado'
            }), 400
        
        arquivo = request.files['file']
        
        # Validação: verifica se arquivo foi selecionado
        if arquivo.filename == '':
            return jsonify({
                'success': False,
                'error': 'Nenhum arquivo selecionado'
            }), 400
        
        # Validação: nome do arquivo
        is_valid_filename, error_msg, safe_filename = validate_filename(arquivo.filename)
        if not is_valid_filename:
            return jsonify({
                'success': False,
                'error': error_msg or 'Nome de arquivo inválido'
            }), 400
        
        # Validação: tamanho do arquivo
        is_valid_size, error_msg = validate_file_size(arquivo)
        if not is_valid_size:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # Lê conteúdo do arquivo com tratamento de encoding
        try:
            conteudo = arquivo.read().decode('utf-8')
        except UnicodeDecodeError:
            arquivo.seek(0)
            try:
                conteudo = arquivo.read().decode('latin-1')
            except:
                return jsonify({
                    'success': False,
                    'error': 'Erro ao decodificar arquivo. Use UTF-8 ou Latin-1'
                }), 400
        
        # Validação: conteúdo do arquivo
        is_valid_content, error_msg = validate_file_content(conteudo)
        if not is_valid_content:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        jogos = parsear_arquivo_txt_timemania(conteudo)
        
        # Validação: verifica se encontrou jogos
        if not jogos:
            return jsonify({
                'success': False,
                'error': 'Nenhum jogo válido encontrado no arquivo'
            }), 400
        
        # Validação: limite de jogos por importação
        if len(jogos) > MAX_JOGOS_IMPORT:
            return jsonify({
                'success': False,
                'error': f'Máximo de {MAX_JOGOS_IMPORT} jogos por importação. Arquivo contém {len(jogos)} jogos'
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
            'error': f'Erro ao processar arquivo: {str(e)}'
        }), 500


@app.route('/api/timemania/conferir-jogos', methods=['POST'])
def conferir_jogos_timemania():
    """Confere jogos enviados via JSON - Timemania"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados inválidos'
            }), 400
        
        jogos = data.get('jogos', [])
        
        if not isinstance(jogos, list):
            return jsonify({
                'success': False,
                'error': 'Jogos devem ser uma lista'
            }), 400
        
        if not jogos:
            return jsonify({
                'success': False,
                'error': 'Nenhum jogo fornecido'
            }), 400
        
        # Validação: limite de jogos por conferência
        if len(jogos) > MAX_JOGOS_IMPORT:
            return jsonify({
                'success': False,
                'error': f'Máximo de {MAX_JOGOS_IMPORT} jogos por conferência'
            }), 400
        
        jogos_validos = []
        for jogo in jogos:
            if not isinstance(jogo, list):
                continue
            
            if len(jogo) != 10:
                continue
            
            # Valida números do jogo (Timemania: 1-80)
            is_valid, error_msg, jogo_validado = validate_numeros_list(
                jogo,
                min_num=1,
                max_num=80,
                max_quantidade=10
            )
            
            if is_valid and len(jogo_validado) == 10:
                jogos_validos.append(sorted(jogo_validado))
        
        if not jogos_validos:
            return jsonify({
                'success': False,
                'error': 'Nenhum jogo válido encontrado. Jogos devem ter exatamente 10 números de 1 a 80'
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
            'error': f'Erro ao conferir jogos: {str(e)}'
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
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados inválidos'
            }), 400
        
        # Valida estratégia
        estrategia = data.get('estrategia', 'misto')
        estrategias_validas = ['misto', 'frequencia', 'balanceado', 'atraso']
        is_valid_estrategia, error_msg = validate_estrategia(estrategia, estrategias_validas)
        if not is_valid_estrategia:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # Valida quantidade de jogos
        quantidade = data.get('quantidade', 10)
        is_valid_qtd, error_msg, quantidade = validate_quantidade(quantidade, 1, MAX_QUANTIDADE_JOGOS)
        if not is_valid_qtd:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # Valida números fixos (Lotomania: 0-99, máximo 50)
        numeros_fixos = data.get('numeros_fixos', [])
        if numeros_fixos:
            is_valid_nums, error_msg, numeros_fixos = validate_numeros_list(
                numeros_fixos,
                min_num=0,
                max_num=99,
                max_quantidade=50
            )
            if not is_valid_nums:
                return jsonify({
                    'success': False,
                    'error': error_msg
                }), 400
            
            if len(numeros_fixos) > 50:
                return jsonify({
                    'success': False,
                    'error': f'Números fixos ({len(numeros_fixos)}) não podem exceder 50 números por jogo'
                }), 400
        else:
            numeros_fixos = None
        
        jogos = gerador_lotomania.gerar_fechamento_completo(
            estrategia=estrategia,
            quantidade_jogos=quantidade,
            numeros_fixos=numeros_fixos
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
            'error': f'Erro ao gerar jogos: {str(e)}'
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
        # Validação: verifica se arquivo foi enviado
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Nenhum arquivo enviado'
            }), 400
        
        arquivo = request.files['file']
        
        # Validação: verifica se arquivo foi selecionado
        if arquivo.filename == '':
            return jsonify({
                'success': False,
                'error': 'Nenhum arquivo selecionado'
            }), 400
        
        # Validação: nome do arquivo
        is_valid_filename, error_msg, safe_filename = validate_filename(arquivo.filename)
        if not is_valid_filename:
            return jsonify({
                'success': False,
                'error': error_msg or 'Nome de arquivo inválido'
            }), 400
        
        # Validação: tamanho do arquivo
        is_valid_size, error_msg = validate_file_size(arquivo)
        if not is_valid_size:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # Lê conteúdo do arquivo com tratamento de encoding
        try:
            conteudo = arquivo.read().decode('utf-8')
        except UnicodeDecodeError:
            arquivo.seek(0)
            try:
                conteudo = arquivo.read().decode('latin-1')
            except:
                return jsonify({
                    'success': False,
                    'error': 'Erro ao decodificar arquivo. Use UTF-8 ou Latin-1'
                }), 400
        
        # Validação: conteúdo do arquivo
        is_valid_content, error_msg = validate_file_content(conteudo)
        if not is_valid_content:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        jogos = parsear_arquivo_txt_lotomania(conteudo)
        
        # Validação: verifica se encontrou jogos
        if not jogos:
            return jsonify({
                'success': False,
                'error': 'Nenhum jogo válido encontrado no arquivo'
            }), 400
        
        # Validação: limite de jogos por importação
        if len(jogos) > MAX_JOGOS_IMPORT:
            return jsonify({
                'success': False,
                'error': f'Máximo de {MAX_JOGOS_IMPORT} jogos por importação. Arquivo contém {len(jogos)} jogos'
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
            'error': f'Erro ao processar arquivo: {str(e)}'
        }), 500


@app.route('/api/lotomania/conferir-jogos', methods=['POST'])
def conferir_jogos_lotomania():
    """Confere jogos enviados via JSON - Lotomania"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados inválidos'
            }), 400
        
        jogos = data.get('jogos', [])
        
        if not isinstance(jogos, list):
            return jsonify({
                'success': False,
                'error': 'Jogos devem ser uma lista'
            }), 400
        
        if not jogos:
            return jsonify({
                'success': False,
                'error': 'Nenhum jogo fornecido'
            }), 400
        
        # Validação: limite de jogos por conferência
        if len(jogos) > MAX_JOGOS_IMPORT:
            return jsonify({
                'success': False,
                'error': f'Máximo de {MAX_JOGOS_IMPORT} jogos por conferência'
            }), 400
        
        jogos_validos = []
        for jogo in jogos:
            if not isinstance(jogo, list):
                continue
            
            if len(jogo) != 50:  # Lotomania: 50 números
                continue
            
            # Valida números do jogo (Lotomania: 0-99)
            is_valid, error_msg, jogo_validado = validate_numeros_list(
                jogo,
                min_num=0,
                max_num=99,
                max_quantidade=50
            )
            
            if is_valid and len(jogo_validado) == 50:
                jogos_validos.append(sorted(jogo_validado))
        
        if not jogos_validos:
            return jsonify({
                'success': False,
                'error': 'Nenhum jogo válido encontrado. Jogos devem ter exatamente 50 números de 0 a 99'
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
            'error': f'Erro ao conferir jogos: {str(e)}'
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

