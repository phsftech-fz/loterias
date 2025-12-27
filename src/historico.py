"""
Módulo para obter e gerenciar histórico de resultados da Lotofácil
"""
import requests
import json
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time

# Torna pandas opcional (só necessário para importar CSV)
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from src.database import DatabaseLotofacil


class HistoricoLotofacil:
    """Classe para gerenciar histórico de resultados da Lotofácil"""
    
    def __init__(self, cache_file: str = "data/historico.json", usar_banco: bool = True):
        self.cache_file = cache_file
        self.historico: List[Dict] = []
        self.usar_banco = usar_banco
        self.db = DatabaseLotofacil() if usar_banco else None
        self._criar_diretorio()
    
    def _criar_diretorio(self):
        """Cria diretório de dados se não existir"""
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
    
    def obter_historico_api(self) -> List[Dict]:
        """
        Obtém histórico de múltiplas fontes
        Busca últimos 1000 concursos usando várias APIs
        Retorna lista de concursos com números sorteados
        """
        concursos = []
        
        print("Buscando historico de multiplas fontes (ultimos 1000 concursos)...")
        
        # Método 1: Tenta carregar arquivo local primeiro (mais rápido)
        print("  [1/5] Verificando arquivo local...")
        concursos_local = self._buscar_arquivo_local()
        if concursos_local and len(concursos_local) >= 100:
            # Limita aos últimos 1000 do arquivo local
            concursos_local = concursos_local[-1000:] if len(concursos_local) > 1000 else concursos_local
            concursos.extend(concursos_local)
            print(f"  OK - Arquivo local: {len(concursos_local)} concursos encontrados")
        
        # Método 2: API oficial da Caixa
        print("  [2/5] Buscando na API oficial da Caixa...")
        concursos_caixa = self._buscar_api_caixa()
        if concursos_caixa:
            concursos.extend(concursos_caixa)
            print(f"  OK - API Caixa: {len(concursos_caixa)} concursos encontrados")
        
        # Método 3: APIs alternativas (múltiplas fontes)
        if len(concursos) < 1000:
            print("  [3/5] Buscando em APIs alternativas...")
            concursos_alternativas = self._buscar_apis_alternativas()
            if concursos_alternativas:
                concursos.extend(concursos_alternativas)
                print(f"  OK - APIs alternativas: {len(concursos_alternativas)} concursos encontrados")
        
        # Método 4: Busca complementar se ainda não tiver 1000
        if len(concursos) < 1000:
            print(f"  [4/5] Busca complementar para atingir 1000 (atual: {len(concursos)})...")
            limite_restante = 1000 - len(concursos)  # Busca o que falta para chegar a 1000
            if limite_restante > 0:
                concursos_complementar = self._buscar_concursos_limitado(limite_restante)
                if concursos_complementar:
                    concursos.extend(concursos_complementar)
                    print(f"  OK - Busca complementar: {len(concursos_complementar)} concursos encontrados")
                
                # Se ainda não tiver 1000, continua buscando
                if len(concursos) < 1000:
                    print(f"  Continuando busca para atingir 1000 (atual: {len(concursos)})...")
                    while len(concursos) < 1000:
                        limite_adicional = min(1000 - len(concursos), 100)
                        concursos_adicionais = self._buscar_concursos_limitado(limite_adicional)
                        if concursos_adicionais:
                            concursos.extend(concursos_adicionais)
                            print(f"    Progresso: {len(concursos)}/1000 concursos...")
                        else:
                            break  # Para se não conseguir mais
        
        # Método 5: Se ainda não tiver, tenta carregar do banco
        if len(concursos) < 100 and self.usar_banco and self.db:
            print("  [5/5] Carregando do banco de dados...")
            concursos_banco = self._carregar_banco()
            if concursos_banco:
                # Limita aos últimos 1000 do banco
                concursos_banco = concursos_banco[-1000:] if len(concursos_banco) > 1000 else concursos_banco
                concursos.extend(concursos_banco)
                print(f"  OK - Banco de dados: {len(concursos_banco)} concursos encontrados")
        
        # Remove duplicatas e ordena
        concursos_unicos = {}
        for c in concursos:
            num = c.get('concurso')
            if num:
                # Garante que o número do concurso está presente
                if 'concurso' not in c or not c['concurso']:
                    c['concurso'] = num
                # Mantém o mais recente se houver duplicata
                concursos_unicos[num] = c
        
        resultado = sorted(concursos_unicos.values(), key=lambda x: x.get('concurso', 0))
        
        # Limita a 1000 concursos máximo (últimos 1000)
        if len(resultado) > 1000:
            resultado = resultado[-1000:]
        
        if resultado:
            print(f"OK - Total: {len(resultado)} concursos carregados (ultimos 1000)")
            return resultado
        else:
            print("AVISO - Nenhum concurso encontrado, usando cache...")
            return self._carregar_cache()
    
    def _buscar_api_alternativa(self) -> List[Dict]:
        """Busca em API alternativa pública (mais confiável) - limitado a 1000 concursos"""
        concursos = []
        
        # API pública conhecida - busca últimos 1000 concursos
        try:
            url_base = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            }
            
            # Primeira requisição para pegar estrutura
            response = requests.get(url_base, timeout=10, headers=headers)
            if response.status_code == 200:
                data = response.json()
                
                # Processa resposta inicial
                resultado_inicial = self._processar_resposta_lotodicas(data)
                concursos.extend(resultado_inicial)
                
                # Se conseguiu resultados, busca até 1000 concursos
                if resultado_inicial:
                    # Encontra o número do último concurso
                    ultimo_num = max([c['concurso'] for c in resultado_inicial]) if resultado_inicial else None
                    
                    if ultimo_num:
                        # Limita a 1000 concursos
                        limite_busca = min(1000, ultimo_num)
                        print(f"  Buscando ultimos {limite_busca} concursos...")
                        
                        # Busca em lotes menores com timeout
                        contador = 0
                        for num in range(ultimo_num - 1, max(1, ultimo_num - limite_busca), -1):
                            try:
                                c = self._buscar_concurso_especifico(num)
                                if c:
                                    concursos.append(c)
                                    contador += 1
                                    
                                # Limite de segurança
                                if len(concursos) >= limite_busca:
                                    break
                                
                                # Delay a cada 50 requisições para não sobrecarregar
                                if contador % 50 == 0:
                                    time.sleep(0.1)
                                    print(f"    Progresso: {contador}/{limite_busca}...")
                                    
                            except Exception:
                                continue  # Continua mesmo se uma requisição falhar
        except Exception as e:
            print(f"  Erro na API alternativa: {e}")
        
        return concursos
    
    def _processar_resposta_lotodicas(self, data) -> List[Dict]:
        """Processa resposta da API lotodicas.com.br"""
        concursos = []
        try:
            if isinstance(data, list):
                for item in data:
                    c = self._processar_concurso(item)
                    if c:
                        concursos.append(c)
            elif isinstance(data, dict):
                resultados = data.get('resultados', []) or data.get('data', [])
                for item in resultados:
                    c = self._processar_concurso(item)
                    if c:
                        concursos.append(c)
        except:
            pass
        return concursos
    
    def _processar_resposta_caixa(self, data) -> List[Dict]:
        """Processa resposta da API oficial da Caixa"""
        return self._processar_resposta_lotodicas(data)
    
    def _buscar_api_caixa(self) -> List[Dict]:
        """Busca na API oficial da Caixa"""
        try:
            url = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            }
            response = requests.get(url, timeout=10, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            concursos = []
            
            # Tenta diferentes estruturas de resposta
            lista_concursos = []
            if isinstance(data, dict):
                lista_concursos = (data.get('listaDezenas', []) or 
                                 data.get('listaResultadoEquipeEsportiva', []) or
                                 data.get('resultado', []) or
                                 data.get('resultados', []))
            elif isinstance(data, list):
                lista_concursos = data
            
            # Processa os concursos
            for concurso in lista_concursos:
                c = self._processar_concurso(concurso)
                if c:
                    concursos.append(c)
            
            return concursos
        except Exception as e:
            print(f"  Erro na API Caixa: {e}")
            return []
    
    def _buscar_apis_alternativas(self) -> List[Dict]:
        """Busca em múltiplas APIs alternativas em paralelo"""
        concursos = []
        apis = [
            {
                'nome': 'Loterias Caixa API',
                'url': 'https://loteriasonline.caixa.gov.br/api/lotofacil',
                'processar': self._processar_api_loterias_caixa
            },
            {
                'nome': 'LotoDicas API',
                'url': 'https://lotodicas.com.br/api/lotofacil',
                'processar': self._processar_api_lotodicas
            }
        ]
        
        for api in apis:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json'
                }
                response = requests.get(api['url'], timeout=8, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    resultado = api['processar'](data)
                    if resultado:
                        concursos.extend(resultado)
                        print(f"    OK - {api['nome']}: {len(resultado)} concursos")
                        if len(concursos) >= 100:  # Se já tem bastante, continua
                            break
            except Exception:
                continue  # Continua para próxima API
        
        return concursos
    
    def _processar_api_loterias_caixa(self, data) -> List[Dict]:
        """Processa resposta da API Loterias Caixa"""
        concursos = []
        try:
            if isinstance(data, dict):
                resultados = data.get('resultados', []) or data.get('data', []) or data.get('lista', [])
            elif isinstance(data, list):
                resultados = data
            else:
                return []
            
            for item in resultados:
                c = self._processar_concurso(item)
                if c:
                    concursos.append(c)
        except:
            pass
        return concursos
    
    def _processar_api_lotodicas(self, data) -> List[Dict]:
        """Processa resposta da API LotoDicas"""
        concursos = []
        try:
            if isinstance(data, dict):
                resultados = data.get('resultados', []) or data.get('data', []) or data.get('concursos', [])
            elif isinstance(data, list):
                resultados = data
            else:
                return []
            
            for item in resultados:
                c = self._processar_concurso(item)
                if c:
                    concursos.append(c)
        except:
            pass
        return concursos
    
    def _buscar_arquivo_local(self) -> List[Dict]:
        """Tenta carregar de arquivo local se existir"""
        try:
            # Verifica se existe arquivo de histórico
            if os.path.exists(self.cache_file):
                historico = self._carregar_cache()
                if historico and len(historico) > 0:
                    return historico
        except:
            pass
        return []
    
    def _buscar_concursos_limitado(self, limite: int = 1000) -> List[Dict]:
        """Busca concursos limitada - até o limite especificado"""
        concursos = []
        
        try:
            # Tenta obter o último concurso
            ultimo_concurso = self._obter_ultimo_concurso()
            if not ultimo_concurso:
                # Estima baseado na data
                ano_atual = datetime.now().year
                anos_desde_inicio = ano_atual - 2003
                ultimo_concurso = 3000 + (anos_desde_inicio - 21) * 156
            
            if ultimo_concurso:
                # Usa o limite solicitado (pode ser maior que 1000 se necessário)
                limite_real = min(limite, ultimo_concurso)
                print(f"    Buscando {limite_real} concursos...")
                
                # Busca com timeout curto e delays
                contador = 0
                numeros_ja_buscados = set()  # Evita buscar o mesmo número duas vezes
                
                for num in range(ultimo_concurso - 1, max(1, ultimo_concurso - limite_real), -1):
                    if num in numeros_ja_buscados:
                        continue
                    
                    try:
                        c = self._buscar_concurso_especifico(num)
                        if c:
                            concursos.append(c)
                            contador += 1
                            numeros_ja_buscados.add(num)
                        
                        # Limite de segurança
                        if len(concursos) >= limite_real:
                            break
                        
                        # Delay a cada 50 requisições para não sobrecarregar
                        if contador % 50 == 0:
                            time.sleep(0.1)
                            print(f"      Progresso: {contador}/{limite_real} concursos...")
                    except Exception:
                        continue
            
            return concursos
        except Exception as e:
            print(f"  Erro na busca limitada: {e}")
            return []
    
    def _obter_ultimo_concurso(self) -> Optional[int]:
        """Obtém o número do último concurso"""
        try:
            url = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, timeout=10, headers=headers)
            data = response.json()
            
            # Tenta encontrar o número do último concurso
            if isinstance(data, dict):
                lista = data.get('listaDezenas', []) or data.get('resultado', [])
                if lista and len(lista) > 0:
                    primeiro = lista[0] if isinstance(lista, list) else lista
                    numero = (primeiro.get('numero') or 
                             primeiro.get('nuConcurso') or 
                             primeiro.get('numeroConcurso'))
                    if numero:
                        return int(numero)
            
            # Se não conseguir, tenta API alternativa
            return self._obter_ultimo_concurso_alternativo()
        except:
            return None
    
    def _obter_ultimo_concurso_alternativo(self) -> Optional[int]:
        """Tenta obter último concurso de fonte alternativa"""
        try:
            # API alternativa - busca o último resultado
            url = "https://lotodicas.com.br/api/lotofacil/ultimo"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('numero') or data.get('concurso')
        except:
            pass
        return None
    
    def _buscar_lote_concursos(self, inicio: int, quantidade: int) -> List[Dict]:
        """Busca um lote de concursos específicos"""
        concursos = []
        for num in range(inicio, max(1, inicio - quantidade), -1):
            c = self._buscar_concurso_especifico(num)
            if c:
                concursos.append(c)
        return concursos
    
    def _buscar_concurso_especifico(self, numero: int) -> Optional[Dict]:
        """Busca um concurso específico com timeout reduzido"""
        try:
            # Tenta API da Caixa com número específico (timeout curto)
            url = f"https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil/{numero}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            }
            
            # Timeout reduzido para não travar
            response = requests.get(url, timeout=3, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return self._processar_concurso(data)
        except:
            pass
        return None
    
    def _processar_concurso(self, concurso) -> Optional[Dict]:
        """Processa um concurso e retorna no formato padrão"""
        try:
            if isinstance(concurso, str):
                return None
            
            # Tenta diferentes formatos de número
            numero = None
            if isinstance(concurso, dict):
                numero = (concurso.get('numero') or 
                         concurso.get('nuConcurso') or 
                         concurso.get('numeroConcurso') or
                         concurso.get('concurso'))
            elif isinstance(concurso, (int, str)):
                numero = int(concurso) if str(concurso).isdigit() else None
            
            if not numero:
                return None
            
            # Tenta diferentes formatos de dezenas
            dezenas = None
            if isinstance(concurso, dict):
                dezenas = (concurso.get('dezenas') or 
                          concurso.get('listaDezenas') or 
                          concurso.get('dezenasSorteadasOrdemSorteio') or
                          concurso.get('resultadoOrdenado') or
                          concurso.get('numeros'))
            
            if not dezenas:
                return None
            
            # Converte dezenas para lista de inteiros
            if isinstance(dezenas, str):
                dezenas = [d.strip() for d in dezenas.replace('[', '').replace(']', '').split(',')]
            elif isinstance(dezenas, list):
                dezenas = [str(d) for d in dezenas]
            else:
                return None
            
            numeros_int = []
            for d in dezenas:
                try:
                    num = int(str(d).strip())
                    if 1 <= num <= 25:
                        numeros_int.append(num)
                except (ValueError, TypeError):
                    continue
            
            # Valida que tem exatamente 15 números
            if len(numeros_int) == 15:
                return {
                    'concurso': int(numero),
                    'numeros': sorted(numeros_int),
                    'data': (concurso.get('dataApuracao') if isinstance(concurso, dict) else None) or 
                           (concurso.get('data') if isinstance(concurso, dict) else None) or ''
                }
        except Exception:
            pass
        
        return None
    
    def obter_historico_arquivo(self, arquivo: str) -> List[Dict]:
        """
        Carrega histórico de arquivo CSV ou JSON
        Formato esperado: CSV com colunas 'concurso' e 'numeros' (separados por vírgula)
        """
        try:
            if arquivo.endswith('.csv'):
                if not PANDAS_AVAILABLE:
                    # Implementação alternativa sem pandas
                    concursos = []
                    with open(arquivo, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        if lines:
                            headers = lines[0].strip().split(',')
                            for line in lines[1:]:
                                values = line.strip().split(',')
                                if len(values) >= 2:
                                    try:
                                        concurso_num = int(values[0])
                                        numeros = [int(n.strip()) for n in values[1].split(',')]
                                        concursos.append({
                                            'concurso': concurso_num,
                                            'numeros': sorted(numeros),
                                            'data': values[2] if len(values) > 2 else ''
                                        })
                                    except (ValueError, IndexError):
                                        continue
                    return concursos
                else:
                    df = pd.read_csv(arquivo)
                    concursos = []
                    for _, row in df.iterrows():
                        numeros = [int(n.strip()) for n in str(row['numeros']).split(',')]
                        concursos.append({
                            'concurso': int(row['concurso']),
                            'numeros': sorted(numeros),
                            'data': row.get('data', '')
                        })
                    return concursos
            elif arquivo.endswith('.json'):
                with open(arquivo, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar arquivo: {e}")
            return []
    
    def salvar_cache(self, concursos: List[Dict]):
        """Salva histórico em cache, evitando duplicatas pelo número do concurso"""
        try:
            # Carrega histórico existente
            historico_existente = {}
            if os.path.exists(self.cache_file):
                try:
                    with open(self.cache_file, 'r', encoding='utf-8') as f:
                        historico_lista = json.load(f)
                        # Converte para dicionário usando número do concurso como chave
                        for c in historico_lista:
                            num = c.get('concurso')
                            if num:
                                historico_existente[num] = c
                except:
                    pass
            
            # Adiciona/atualiza concursos novos (evita duplicatas)
            for concurso in concursos:
                num = concurso.get('concurso')
                if num:
                    historico_existente[num] = concurso
            
            # Converte de volta para lista e ordena
            historico_final = sorted(historico_existente.values(), key=lambda x: x.get('concurso', 0))
            
            # Salva no arquivo
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(historico_final, f, indent=2, ensure_ascii=False)
            
            self.historico = historico_final
            print(f"Cache salvo: {len(historico_final)} concursos (sem duplicatas)")
        except Exception as e:
            print(f"Erro ao salvar cache: {e}")
    
    def _carregar_cache(self) -> List[Dict]:
        """Carrega histórico do cache, removendo duplicatas pelo número do concurso"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    historico_lista = json.load(f)
                    
                    # Remove duplicatas usando número do concurso como chave
                    historico_unicos = {}
                    for c in historico_lista:
                        num = c.get('concurso')
                        if num:
                            # Mantém o mais recente se houver duplicata
                            if num not in historico_unicos:
                                historico_unicos[num] = c
                    
                    # Converte de volta para lista e ordena
                    historico_final = sorted(historico_unicos.values(), key=lambda x: x.get('concurso', 0))
                    
                    if len(historico_final) != len(historico_lista):
                        print(f"Removidas {len(historico_lista) - len(historico_final)} duplicatas do cache")
                        # Salva versão sem duplicatas
                        with open(self.cache_file, 'w', encoding='utf-8') as f:
                            json.dump(historico_final, f, indent=2, ensure_ascii=False)
                    
                    self.historico = historico_final
                    return historico_final
        except Exception as e:
            print(f"Erro ao carregar cache: {e}")
        return []
    
    def atualizar_historico(self, usar_api: bool = True) -> List[Dict]:
        """
        Atualiza histórico, tentando API primeiro, depois banco/cache
        Evita duplicatas usando número do concurso como chave única
        """
        if usar_api:
            # Carrega histórico existente primeiro (do banco ou cache)
            historico_existente = {}
            
            if self.usar_banco and self.db:
                historico_banco = self._carregar_banco()
                for c in historico_banco:
                    num = c.get('concurso')
                    if num:
                        historico_existente[num] = c
            
            # Também carrega do cache JSON se não tiver no banco
            if not historico_existente:
                historico_cache = self._carregar_cache()
                for c in historico_cache:
                    num = c.get('concurso')
                    if num:
                        historico_existente[num] = c
            
            print(f"Historico existente: {len(historico_existente)} concursos")
            
            # Se já tem 1000 ou mais, retorna os últimos 1000
            if len(historico_existente) >= 1000:
                historico_completo = sorted(historico_existente.values(), key=lambda x: x.get('concurso', 0))[-1000:]
                print(f"Ja possui {len(historico_existente)} concursos, retornando ultimos 1000")
                return historico_completo
            
            # Busca novos concursos da API até atingir 1000
            print(f"Buscando concursos para atingir 1000 (atual: {len(historico_existente)})...")
            concursos_api = self.obter_historico_api()
            
            if concursos_api:
                # Identifica apenas concursos novos (não duplicados)
                concursos_novos = []
                for c in concursos_api:
                    num = c.get('concurso')
                    if num:
                        # Garante que o número do concurso está presente
                        if 'concurso' not in c or not c['concurso']:
                            c['concurso'] = num
                        
                        # Adiciona apenas se não existir
                        if num not in historico_existente:
                            concursos_novos.append(c)
                            historico_existente[num] = c
                        else:
                            # Atualiza se já existir (mantém dados mais recentes)
                            historico_existente[num] = c
                
                # Se ainda não tiver 1000, busca mais ativamente
                if len(historico_existente) < 1000:
                    print(f"Buscando mais concursos para atingir 1000 (atual: {len(historico_existente)})...")
                    faltam = 1000 - len(historico_existente)
                    
                    # Obtém primeiro e último concurso conhecido
                    concursos_ordenados = sorted([c.get('concurso', 0) for c in historico_existente.values()])
                    primeiro_conhecido = concursos_ordenados[0] if concursos_ordenados else 0
                    ultimo_conhecido = concursos_ordenados[-1] if concursos_ordenados else 0
                    
                    print(f"Primeiro concurso conhecido: {primeiro_conhecido}, Ultimo: {ultimo_conhecido}")
                    
                    # Busca concursos anteriores ao primeiro conhecido
                    if primeiro_conhecido > 1:
                        print(f"Buscando {faltam} concursos anteriores ao {primeiro_conhecido}...")
                        contador_busca = 0
                        for num in range(primeiro_conhecido - 1, max(1, primeiro_conhecido - faltam - 50), -1):
                            if num not in historico_existente:
                                c = self._buscar_concurso_especifico(num)
                                if c:
                                    concursos_novos.append(c)
                                    historico_existente[num] = c
                                    contador_busca += 1
                                    
                                    if len(historico_existente) >= 1000:
                                        break
                                    
                                    if contador_busca % 50 == 0:
                                        print(f"  Progresso: {len(historico_existente)}/1000 concursos (buscando anteriores)...")
                                        time.sleep(0.1)
                    
                    # Se ainda não tiver 1000, busca concursos posteriores ao último conhecido
                    if len(historico_existente) < 1000:
                        ultimo_api = self._obter_ultimo_concurso()
                        if ultimo_api and ultimo_conhecido < ultimo_api:
                            faltam_agora = 1000 - len(historico_existente)
                            print(f"Buscando {faltam_agora} concursos posteriores ao {ultimo_conhecido}...")
                            contador_busca = 0
                            for num in range(ultimo_conhecido + 1, min(ultimo_api + 1, ultimo_conhecido + faltam_agora + 50)):
                                if num not in historico_existente:
                                    c = self._buscar_concurso_especifico(num)
                                    if c:
                                        concursos_novos.append(c)
                                        historico_existente[num] = c
                                        contador_busca += 1
                                        
                                        if len(historico_existente) >= 1000:
                                            break
                                        
                                        if contador_busca % 50 == 0:
                                            print(f"  Progresso: {len(historico_existente)}/1000 concursos (buscando posteriores)...")
                                            time.sleep(0.1)
                
                # Combina histórico existente com novos
                historico_completo = sorted(historico_existente.values(), key=lambda x: x.get('concurso', 0))
                
                # Limita aos últimos 1000 concursos
                if len(historico_completo) > 1000:
                    historico_completo = historico_completo[-1000:]
                    print(f"Limitado aos ultimos 1000 concursos")
                
                if concursos_novos:
                    print(f"Encontrados {len(concursos_novos)} concursos novos (total: {len(historico_completo)})")
                    
                    # Salva apenas concursos novos no banco de dados
                    if self.usar_banco and self.db:
                        print(f"Salvando {len(concursos_novos)} concursos novos no banco de dados...")
                        inseridos = self.db.inserir_concursos(concursos_novos)
                        print(f"OK - {inseridos} concursos novos salvos no banco")
                else:
                    print(f"Total de concursos no historico: {len(historico_completo)}")
                
                # Salva histórico completo em cache JSON (evita duplicatas automaticamente)
                # Mantém apenas os últimos 1000
                self.salvar_cache(historico_completo)
                
                return historico_completo
        
        # Tenta carregar do banco primeiro
        if self.usar_banco and self.db:
            historico_banco = self._carregar_banco()
            if historico_banco:
                return historico_banco
        
        # Fallback para cache JSON
        return self._carregar_cache()
    
    def _carregar_banco(self) -> List[Dict]:
        """Carrega histórico do banco de dados (últimos 1000)"""
        try:
            if self.db:
                historico = self.db.obter_ultimos_concursos(quantidade=1000)
                if historico:
                    self.historico = historico
                    print(f"Carregados {len(historico)} concursos do banco de dados (ultimos 1000)")
                    return historico
        except Exception as e:
            print(f"Erro ao carregar do banco: {e}")
        return []
    
    def get_historico(self) -> List[Dict]:
        """Retorna histórico atual (do banco ou cache)"""
        if not self.historico:
            # Tenta carregar do banco primeiro
            if self.usar_banco and self.db:
                historico_banco = self._carregar_banco()
                if historico_banco:
                    return historico_banco
            
            # Fallback para cache
            self.historico = self._carregar_cache()
        
        return self.historico
    
    def get_ultimos_concursos(self, quantidade: int = 100) -> List[Dict]:
        """Retorna os últimos N concursos"""
        # Se usar banco, busca diretamente do banco
        if self.usar_banco and self.db:
            return self.db.obter_ultimos_concursos(quantidade)
        
        # Fallback para histórico em memória
        historico = self.get_historico()
        return historico[-quantidade:] if historico else []
    
    def sincronizar_banco(self, forcar_atualizacao: bool = False) -> Dict:
        """
        Sincroniza banco de dados com API
        Busca apenas concursos novos ou faltantes
        Retorna estatísticas da sincronização
        """
        if not self.usar_banco or not self.db:
            return {'sucesso': False, 'erro': 'Banco de dados não está habilitado'}
        
        try:
            # Obtém último concurso do banco
            ultimo_banco = self.db.obter_ultimo_concurso()
            ultimo_numero_banco = ultimo_banco['concurso'] if ultimo_banco else 0
            
            # Obtém último concurso da API
            ultimo_api = self._obter_ultimo_concurso()
            
            if not ultimo_api:
                return {'sucesso': False, 'erro': 'Não foi possível obter último concurso da API'}
            
            ultimo_numero_api = ultimo_api
            
            # Verifica quantos concursos faltam
            total_banco = self.db.contar_concursos()
            
            if ultimo_numero_api <= ultimo_numero_banco and not forcar_atualizacao:
                return {
                    'sucesso': True,
                    'atualizado': False,
                    'mensagem': 'Banco já está atualizado',
                    'total_banco': total_banco,
                    'ultimo_banco': ultimo_numero_banco,
                    'ultimo_api': ultimo_numero_api
                }
            
            # Busca concursos faltantes
            print(f"Buscando concursos de {ultimo_numero_banco + 1} até {ultimo_numero_api}...")
            concursos_novos = []
            
            # Busca em lotes para não sobrecarregar
            for num in range(ultimo_numero_banco + 1, ultimo_numero_api + 1):
                c = self._buscar_concurso_especifico(num)
                if c:
                    concursos_novos.append(c)
                
                if len(concursos_novos) % 50 == 0:
                    # Salva em lotes
                    self.db.inserir_concursos(concursos_novos)
                    print(f"  Progresso: {len(concursos_novos)} concursos novos salvos...")
                    concursos_novos = []
                    time.sleep(0.1)
            
            # Salva restante
            if concursos_novos:
                self.db.inserir_concursos(concursos_novos)
            
            total_final = self.db.contar_concursos()
            
            return {
                'sucesso': True,
                'atualizado': True,
                'concursos_adicionados': total_final - total_banco,
                'total_banco': total_final,
                'ultimo_banco': ultimo_numero_api
            }
        except Exception as e:
            return {'sucesso': False, 'erro': str(e)}

