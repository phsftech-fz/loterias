"""
Módulo para obter e gerenciar histórico de resultados da Lotomania
"""
import requests
import json
import os
import re
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time

class HistoricoLotomania:
    """Classe para gerenciar histórico de resultados da Lotomania"""
    
    def __init__(self, cache_file: str = "data/historico_lotomania.json", usar_banco: bool = False):
        self.cache_file = cache_file
        self.historico: List[Dict] = []
        self.usar_banco = usar_banco
        self.db = None
        self._criar_diretorio()
    
    def _criar_diretorio(self):
        """Cria diretório de dados se não existir"""
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
    
    def _obter_ultimo_concurso(self) -> Optional[int]:
        """Obtém número do último concurso de múltiplas fontes"""
        try:
            url = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotomania"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'pt-BR,pt;q=0.9',
                'Referer': 'https://loterias.caixa.gov.br/'
            }
            response = requests.get(url, timeout=8, headers=headers, allow_redirects=True)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    numero = (data.get('numero') or 
                             data.get('nuConcurso') or 
                             data.get('numeroConcurso'))
                    
                    if numero:
                        return int(numero)
                except (ValueError, KeyError, TypeError):
                    pass
        except:
            pass
        
        # Fallback: estimativa baseada na data (Lotomania começou em 1999)
        try:
            ano_atual = datetime.now().year
            mes_atual = datetime.now().month
            anos_desde_inicio = ano_atual - 1999
            # Aproximadamente 104 concursos por ano (2 por semana)
            estimativa = 2800 + (anos_desde_inicio - 25) * 104 + (mes_atual * 8)
            return estimativa
        except:
            return None
    
    def _buscar_concurso_especifico(self, numero: int) -> Optional[Dict]:
        """Busca um concurso específico usando a URL com número do concurso"""
        try:
            url = f"https://servicebus2.caixa.gov.br/portaldeloterias/api/lotomania/{numero}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
                'Referer': 'https://loterias.caixa.gov.br/'
            }
            response = requests.get(url, timeout=8, headers=headers, allow_redirects=True)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    resultado = self._processar_concurso(data)
                    if resultado:
                        return resultado
                except ValueError:
                    pass
        except:
            pass
        
        return None
    
    def _processar_concurso(self, concurso) -> Optional[Dict]:
        """Processa um concurso e retorna no formato padrão"""
        try:
            if isinstance(concurso, str) or not isinstance(concurso, dict):
                return None
            
            # Tenta diferentes formatos de número do concurso
            numero = (concurso.get('numero') or 
                     concurso.get('nuConcurso') or 
                     concurso.get('numeroConcurso') or
                     concurso.get('concurso'))
            
            if not numero:
                return None
            
            try:
                numero = int(numero)
            except (ValueError, TypeError):
                return None
            
            # Tenta diferentes formatos de dezenas
            dezenas = None
            
            if 'listaDezenas' in concurso:
                dezenas = concurso['listaDezenas']
            elif 'dezenas' in concurso:
                dezenas = concurso['dezenas']
            elif 'numeros' in concurso:
                dezenas = concurso['numeros']
            elif 'listaDezenasSorteadas' in concurso:
                dezenas = concurso['listaDezenasSorteadas']
            elif 'dezenasSorteadas' in concurso:
                dezenas = concurso['dezenasSorteadas']
            elif 'resultado' in concurso and isinstance(concurso['resultado'], dict):
                dezenas = (concurso['resultado'].get('listaDezenas') or 
                          concurso['resultado'].get('dezenas') or
                          concurso['resultado'].get('numeros'))
            
            if not dezenas:
                return None
            
            # Garante que é uma lista
            if not isinstance(dezenas, list):
                if isinstance(dezenas, str):
                    dezenas = dezenas.split(',') if ',' in dezenas else dezenas.split()
                elif isinstance(dezenas, dict):
                    dezenas = list(dezenas.values())
                else:
                    return None
            
            numeros_int = []
            for d in dezenas:
                try:
                    num_str = str(d).strip()
                    num_str = ''.join(filter(str.isdigit, num_str))
                    if num_str:
                        num = int(num_str)
                        if 0 <= num <= 99:  # Lotomania: 00 a 99
                            numeros_int.append(num)
                except (ValueError, TypeError):
                    continue
            
            # Remove duplicatas
            numeros_int = list(dict.fromkeys(numeros_int))
            
            # Valida que tem exatamente 20 números (Lotomania sorteia 20)
            if len(numeros_int) == 20:
                return {
                    'concurso': numero,
                    'numeros': sorted(numeros_int),
                    'data': (concurso.get('dataApuracao') or 
                           concurso.get('data') or 
                           concurso.get('dataSorteio') or '')
                }
        except Exception:
            pass
        
        return None
    
    def _buscar_arquivo_local(self) -> List[Dict]:
        """Tenta carregar de arquivo local se existir"""
        try:
            if os.path.exists(self.cache_file):
                historico = self._carregar_cache()
                if historico and len(historico) > 0:
                    return historico
        except:
            pass
        return []
    
    def _buscar_api_caixa(self) -> List[Dict]:
        """Busca na API oficial da Caixa usando URL com número do concurso"""
        concursos = []
        
        ultimo = self._obter_ultimo_concurso()
        if not ultimo:
            ultimo = 2867  # Último conhecido
            print(f"    Usando ultimo concurso conhecido: {ultimo}")
        else:
            print(f"    Ultimo concurso encontrado: {ultimo}")
        
        print(f"    Buscando concursos usando URL: /api/lotomania/{{numero}}...")
        limite_busca = min(50, ultimo)
        
        for num in range(ultimo, max(1, ultimo - limite_busca), -1):
            try:
                c = self._buscar_concurso_especifico(num)
                if c:
                    concursos.append(c)
                if len(concursos) >= limite_busca:
                    break
                time.sleep(0.1)
            except:
                continue
        
        return concursos
    
    def _buscar_concursos_limitado(self, limite: int = 500) -> List[Dict]:
        """Busca concursos limitada - até o limite especificado"""
        concursos = []
        
        try:
            ultimo_concurso = self._obter_ultimo_concurso()
            if not ultimo_concurso:
                ano_atual = datetime.now().year
                anos_desde_inicio = ano_atual - 1999
                ultimo_concurso = 2800 + (anos_desde_inicio - 25) * 104
                print(f"    AVISO - Estimando ultimo concurso: {ultimo_concurso}")
            
            if ultimo_concurso:
                limite_real = min(limite, ultimo_concurso)
                print(f"    Buscando {limite_real} concursos (do {ultimo_concurso} para tras)...")
                
                contador = 0
                tentativas = 0
                numeros_ja_buscados = set()
                sem_resultado_seguidos = 0
                max_sem_resultado = 100
                
                for num in range(ultimo_concurso, max(1, ultimo_concurso - limite_real), -1):
                    if num in numeros_ja_buscados:
                        continue
                    
                    tentativas += 1
                    
                    if sem_resultado_seguidos >= max_sem_resultado:
                        print(f"    AVISO - Muitas tentativas sem resultado, tentando estrategia alternativa...")
                        for intervalo in [50, 100, 150, 200]:
                            num_teste = ultimo_concurso - intervalo
                            if num_teste > 0 and num_teste not in numeros_ja_buscados:
                                try:
                                    c = self._buscar_concurso_especifico(num_teste)
                                    if c:
                                        concursos.append(c)
                                        contador += 1
                                        numeros_ja_buscados.add(num_teste)
                                        sem_resultado_seguidos = 0
                                        print(f"    OK - Encontrado concurso {num_teste}!")
                                        break
                                except:
                                    pass
                        
                        if sem_resultado_seguidos >= max_sem_resultado * 2:
                            print(f"    AVISO - Parando busca apos muitas tentativas sem resultado")
                            break
                    
                    try:
                        c = self._buscar_concurso_especifico(num)
                        if c:
                            concursos.append(c)
                            contador += 1
                            numeros_ja_buscados.add(num)
                            sem_resultado_seguidos = 0
                        else:
                            sem_resultado_seguidos += 1
                        
                        if len(concursos) >= limite_real:
                            break
                        
                        if tentativas % 10 == 0 or (contador > 0 and contador % 5 == 0):
                            print(f"      Progresso: {contador}/{limite_real} concursos (buscando {num}...)")
                            time.sleep(0.1)
                        
                        if tentativas > 0 and tentativas % 50 == 0 and contador == 0:
                            print(f"      Buscando... ({tentativas} tentativas realizadas, ainda sem resultados)")
                            time.sleep(0.2)
                    except Exception:
                        sem_resultado_seguidos += 1
                        continue
            
            return concursos
        except Exception as e:
            print(f"  Erro na busca limitada: {e}")
            return []
    
    def obter_historico_api(self) -> List[Dict]:
        """
        Obtém histórico de múltiplas fontes
        Busca últimos 1000 concursos usando várias APIs
        Retorna lista de concursos com números sorteados
        """
        concursos = []
        LIMITE_CONCURSOS = 1000
        
        print(f"Buscando historico Lotomania de multiplas fontes (ultimos {LIMITE_CONCURSOS} concursos)...")
        
        # Método 1: Tenta carregar arquivo local primeiro
        print("  [1/3] Verificando arquivo local...")
        concursos_local = self._buscar_arquivo_local()
        if concursos_local and len(concursos_local) >= 50:
            concursos_local = concursos_local[-LIMITE_CONCURSOS:] if len(concursos_local) > LIMITE_CONCURSOS else concursos_local
            concursos.extend(concursos_local)
            print(f"  OK - Arquivo local: {len(concursos_local)} concursos encontrados")
        
        # Método 2: API oficial da Caixa
        print("  [2/3] Buscando na API oficial da Caixa...")
        concursos_caixa = self._buscar_api_caixa()
        if concursos_caixa:
            concursos.extend(concursos_caixa)
            print(f"  OK - API Caixa: {len(concursos_caixa)} concursos encontrados")
        
        # Método 3: Busca complementar se ainda não tiver 1000
        if len(concursos) < LIMITE_CONCURSOS:
            print(f"  [3/3] Busca complementar para atingir {LIMITE_CONCURSOS} (atual: {len(concursos)})...")
            limite_restante = LIMITE_CONCURSOS - len(concursos)
            if limite_restante > 0:
                concursos_complementar = self._buscar_concursos_limitado(limite_restante)
                if concursos_complementar:
                    concursos.extend(concursos_complementar)
                    print(f"  OK - Busca complementar: {len(concursos_complementar)} concursos encontrados")
                
                if len(concursos) < LIMITE_CONCURSOS:
                    print(f"  Continuando busca para atingir {LIMITE_CONCURSOS} (atual: {len(concursos)})...")
                    ultimo = self._obter_ultimo_concurso() or 2867
                    limite_adicional = LIMITE_CONCURSOS - len(concursos)
                    print(f"    Buscando mais {limite_adicional} concursos a partir do {ultimo}...")
                    
                    contador_complementar = 0
                    for num in range(ultimo - len(concursos), max(1, ultimo - limite_adicional - len(concursos)), -1):
                        try:
                            c = self._buscar_concurso_especifico(num)
                            if c:
                                concursos.append(c)
                                contador_complementar += 1
                            if len(concursos) >= LIMITE_CONCURSOS:
                                break
                            if contador_complementar % 10 == 0:
                                print(f"      Progresso: {len(concursos)}/{LIMITE_CONCURSOS} concursos...")
                            time.sleep(0.1)
                        except:
                            continue
                    
                    if len(concursos) >= LIMITE_CONCURSOS:
                        print(f"  OK - Limite de {LIMITE_CONCURSOS} concursos atingido!")
                    else:
                        print(f"  AVISO - Encontrados {len(concursos)} concursos (objetivo: {LIMITE_CONCURSOS})")
        
        # Remove duplicatas e ordena
        concursos_unicos = {}
        for c in concursos:
            num = c.get('concurso')
            if num:
                if 'concurso' not in c or not c['concurso']:
                    c['concurso'] = num
                concursos_unicos[num] = c
        
        resultado = sorted(concursos_unicos.values(), key=lambda x: x.get('concurso', 0))
        
        # Limita a 1000 concursos máximo
        if len(resultado) > LIMITE_CONCURSOS:
            resultado = resultado[-LIMITE_CONCURSOS:]
        
        if resultado:
            print(f"OK - Total: {len(resultado)} concursos carregados (ultimos {LIMITE_CONCURSOS})")
            return resultado
        else:
            print("AVISO - Nenhum concurso encontrado, usando cache...")
            cache = self._carregar_cache()
            if cache:
                if len(cache) > LIMITE_CONCURSOS:
                    cache = cache[-LIMITE_CONCURSOS:]
                return cache
            return []
    
    def salvar_cache(self, concursos: List[Dict]):
        """Salva histórico em cache, evitando duplicatas pelo número do concurso"""
        try:
            historico_existente = {}
            if os.path.exists(self.cache_file):
                try:
                    with open(self.cache_file, 'r', encoding='utf-8') as f:
                        historico_lista = json.load(f)
                        for c in historico_lista:
                            num = c.get('concurso')
                            if num:
                                historico_existente[num] = c
                except:
                    pass
            
            for concurso in concursos:
                num = concurso.get('concurso')
                if num:
                    historico_existente[num] = concurso
            
            historico_final = sorted(historico_existente.values(), key=lambda x: x.get('concurso', 0))
            
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
                    
                    historico_unicos = {}
                    for c in historico_lista:
                        num = c.get('concurso')
                        if num:
                            if num not in historico_unicos:
                                historico_unicos[num] = c
                    
                    historico_final = sorted(historico_unicos.values(), key=lambda x: x.get('concurso', 0))
                    
                    if len(historico_final) != len(historico_lista):
                        print(f"Removidas {len(historico_lista) - len(historico_final)} duplicatas do cache")
                        with open(self.cache_file, 'w', encoding='utf-8') as f:
                            json.dump(historico_final, f, indent=2, ensure_ascii=False)
                    
                    self.historico = historico_final
                    return historico_final
        except Exception as e:
            print(f"Erro ao carregar cache: {e}")
        return []
    
    def atualizar_historico(self, usar_api: bool = True) -> List[Dict]:
        """
        Atualiza histórico, tentando API primeiro, depois cache
        Evita duplicatas usando número do concurso como chave única
        """
        if usar_api:
            historico_existente = {}
            historico_cache = self._carregar_cache()
            for c in historico_cache:
                num = c.get('concurso')
                if num:
                    historico_existente[num] = c
            
            print(f"Historico existente: {len(historico_existente)} concursos")
            
            concursos_api = self.obter_historico_api()
            
            if concursos_api:
                concursos_novos = []
                for c in concursos_api:
                    num = c.get('concurso')
                    if num:
                        if 'concurso' not in c or not c['concurso']:
                            c['concurso'] = num
                        
                        if num not in historico_existente:
                            concursos_novos.append(c)
                            historico_existente[num] = c
                        else:
                            historico_existente[num] = c
                
                historico_completo = sorted(historico_existente.values(), key=lambda x: x.get('concurso', 0))
                
                # Limita a 1000 concursos máximo
                LIMITE_CONCURSOS = 1000
                if len(historico_completo) > LIMITE_CONCURSOS:
                    historico_completo = historico_completo[-LIMITE_CONCURSOS:]
                    print(f"Limitado aos ultimos {LIMITE_CONCURSOS} concursos")
                
                if concursos_novos:
                    print(f"Encontrados {len(concursos_novos)} concursos novos (sem duplicatas)")
                else:
                    print(f"Total de concursos no historico: {len(historico_completo)}")
                
                self.salvar_cache(historico_completo)
                
                return historico_completo
        
        return self._carregar_cache()
    
    def get_historico(self) -> List[Dict]:
        """Retorna histórico atual"""
        if not self.historico:
            self.historico = self._carregar_cache()
        return self.historico

