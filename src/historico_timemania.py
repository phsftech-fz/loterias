"""
Módulo para obter e gerenciar histórico de resultados da Timemania
"""
import requests
import json
import os
import re
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time

class HistoricoTimemania:
    """Classe para gerenciar histórico de resultados da Timemania"""
    
    def __init__(self, cache_file: str = "data/historico_timemania.json", usar_banco: bool = False):
        self.cache_file = cache_file
        self.historico: List[Dict] = []
        self.usar_banco = usar_banco  # Por enquanto não usa banco (banco é específico para Lotofácil)
        self.db = None
        self._criar_diretorio()
    
    def _criar_diretorio(self):
        """Cria diretório de dados se não existir"""
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
    
    def _obter_ultimo_concurso(self) -> Optional[int]:
        """Obtém número do último concurso de múltiplas fontes"""
        # Tenta buscar o último concurso diretamente da API
        try:
            url = "https://servicebus2.caixa.gov.br/portaldeloterias/api/timemania"
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
                    # A API retorna o último concurso diretamente
                    numero = (data.get('numero') or 
                             data.get('nuConcurso') or 
                             data.get('numeroConcurso'))
                    
                    if numero:
                        return int(numero)
                except (ValueError, KeyError, TypeError):
                    pass
        except:
            pass
        
        # Se não conseguiu, tenta buscar um concurso conhecido recente (2335 foi mencionado pelo usuário)
        # Tenta buscar alguns concursos recentes para encontrar o último válido
        try:
            for num_teste in range(2335, 2300, -1):
                try:
                    url = f"https://servicebus2.caixa.gov.br/portaldeloterias/api/timemania/{num_teste}"
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'application/json'
                    }
                    response = requests.get(url, timeout=5, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('numero') or data.get('listaDezenas'):
                            return int(data.get('numero', num_teste))
                except:
                    continue
        except:
            pass
        
        # Fallback: estimativa baseada na data
        try:
            ano_atual = datetime.now().year
            mes_atual = datetime.now().month
            anos_desde_inicio = ano_atual - 2008
            # Aproximadamente 156 concursos por ano (3 por semana)
            estimativa = 2000 + (anos_desde_inicio - 15) * 156 + (mes_atual * 13)
            return estimativa
        except:
            return None
    
    def _buscar_concurso_especifico(self, numero: int) -> Optional[Dict]:
        """Busca um concurso específico de múltiplas fontes"""
        # Lista de fontes para tentar
        fontes = [
            {
                'url': f"https://servicebus2.caixa.gov.br/portaldeloterias/api/timemania/{numero}",
                'nome': 'API Caixa Oficial'
            },
            {
                'url': f"https://apiloterias.com.br/app/resultado?loteria=timemania&token=YOUR_TOKEN&concurso={numero}",
                'nome': 'API Loterias (sem token)',
                'skip': True  # Pula se precisar de token
            },
            {
                'url': f"https://www.lotodicas.com.br/api/timemania/{numero}",
                'nome': 'LotoDicas'
            },
            {
                'url': f"https://lottolookup.com.br/api/timemania/{numero}",
                'nome': 'LottoLookup'
            }
        ]
        
        for fonte in fontes:
            if fonte.get('skip'):
                continue
                
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
                    'Referer': 'https://loterias.caixa.gov.br/'
                }
                response = requests.get(fonte['url'], timeout=8, headers=headers, allow_redirects=True)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        resultado = self._processar_concurso(data)
                        if resultado:
                            return resultado
                    except ValueError:
                        # Se não for JSON, tenta parsear HTML ou texto
                        texto = response.text
                        resultado = self._processar_texto_html(texto, numero)
                        if resultado:
                            return resultado
                elif response.status_code == 404:
                    # Concurso não existe, continua para próxima fonte
                    continue
            except requests.exceptions.Timeout:
                continue
            except requests.exceptions.RequestException:
                continue
            except Exception:
                continue
        
        return None
    
    def _processar_texto_html(self, texto: str, numero: int) -> Optional[Dict]:
        """Tenta extrair dados de HTML ou texto"""
        try:
            # Procura por padrões de números (1-80)
            numeros_encontrados = re.findall(r'\b([1-9]|[1-7][0-9]|80)\b', texto)
            numeros_int = []
            for num_str in numeros_encontrados:
                try:
                    num = int(num_str)
                    if 1 <= num <= 80 and num not in numeros_int:
                        numeros_int.append(num)
                except:
                    continue
            
            # Se encontrou pelo menos 7 números (a API pode retornar 7 ou 10), pode ser válido
            if len(numeros_int) >= 7:
                return {
                    'concurso': numero,
                    'numeros': sorted(numeros_int),
                    'time_coracao': '',
                    'data': ''
                }
        except:
            pass
        return None
    
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
    
    def _buscar_api_caixa(self) -> List[Dict]:
        """Busca na API oficial da Caixa usando URL com número do concurso"""
        concursos = []
        
        # Primeiro tenta obter o último concurso
        ultimo = self._obter_ultimo_concurso()
        if not ultimo:
            # Usa 2335 como fallback (último conhecido)
            ultimo = 2335
            print(f"    Usando ultimo concurso conhecido: {ultimo}")
        else:
            print(f"    Ultimo concurso encontrado: {ultimo}")
        
        # Busca concursos usando a URL com número: /api/timemania/{numero}
        print(f"    Buscando concursos usando URL: /api/timemania/{{numero}}...")
        limite_busca = min(50, ultimo)  # Busca até 50 concursos recentes
        
        for num in range(ultimo, max(1, ultimo - limite_busca), -1):
            try:
                c = self._buscar_concurso_especifico(num)
                if c:
                    concursos.append(c)
                if len(concursos) >= limite_busca:
                    break
                time.sleep(0.1)  # Pequeno delay para não sobrecarregar
            except Exception as e:
                # Continua mesmo se uma requisição falhar
                continue
        
        return concursos
    
    def _processar_resposta_api(self, data) -> List[Dict]:
        """Processa resposta da API"""
        concursos = []
        try:
            if isinstance(data, list):
                for item in data:
                    c = self._processar_concurso(item)
                    if c:
                        concursos.append(c)
            elif isinstance(data, dict):
                # Tenta diferentes estruturas
                resultados = (data.get('resultados', []) or 
                            data.get('data', []) or 
                            data.get('listaDezenas', []) or
                            data.get('concursos', []))
                
                # Se não encontrou lista, tenta processar o próprio dict
                if not resultados:
                    c = self._processar_concurso(data)
                    if c:
                        concursos.append(c)
                else:
                    for item in resultados:
                        c = self._processar_concurso(item)
                        if c:
                            concursos.append(c)
        except:
            pass
        return concursos
    
    def _buscar_apis_alternativas(self) -> List[Dict]:
        """Busca em múltiplas APIs alternativas"""
        concursos = []
        apis = [
            {
                'nome': 'LotoDicas API',
                'url': 'https://www.lotodicas.com.br/api/timemania',
                'processar': self._processar_api_lotodicas
            },
            {
                'nome': 'LotoDicas (alternativa)',
                'url': 'https://lotodicas.com.br/api/timemania',
                'processar': self._processar_api_lotodicas
            },
            {
                'nome': 'Loterias Caixa API',
                'url': 'https://loteriasonline.caixa.gov.br/api/timemania',
                'processar': self._processar_api_loterias_caixa
            }
        ]
        
        for api in apis:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'pt-BR,pt;q=0.9',
                    'Referer': 'https://loterias.caixa.gov.br/'
                }
                response = requests.get(api['url'], timeout=8, headers=headers, allow_redirects=True)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        resultado = api['processar'](data)
                        if resultado:
                            concursos.extend(resultado)
                            print(f"    OK - {api['nome']}: {len(resultado)} concursos")
                            if len(concursos) >= 50:  # Se já tem bastante, continua
                                break
                    except ValueError:
                        # Não é JSON válido
                        continue
            except Exception as e:
                # Mostra erro apenas em debug (comentado)
                # print(f"    Erro em {api['nome']}: {e}")
                continue  # Continua para próxima API
        
        # Se não conseguiu nada das APIs, tenta buscar últimos concursos diretamente
        if not concursos:
            print("    Tentando buscar concursos recentes diretamente...")
            ultimo = self._obter_ultimo_concurso()
            if ultimo:
                # Busca últimos 30 concursos
                for num in range(ultimo, max(1, ultimo - 30), -1):
                    try:
                        c = self._buscar_concurso_especifico(num)
                        if c:
                            concursos.append(c)
                        if len(concursos) >= 30:
                            break
                        time.sleep(0.1)
                    except:
                        continue
        
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
    
    def _buscar_concursos_limitado(self, limite: int = 500) -> List[Dict]:
        """Busca concursos limitada - até o limite especificado"""
        concursos = []
        
        try:
            # Tenta obter o último concurso
            ultimo_concurso = self._obter_ultimo_concurso()
            if not ultimo_concurso:
                # Estima baseado na data (Timemania começou em 2008)
                ano_atual = datetime.now().year
                anos_desde_inicio = ano_atual - 2008
                # Aproximadamente 156 concursos por ano (3 por semana)
                ultimo_concurso = 2000 + (anos_desde_inicio - 15) * 156
                print(f"    AVISO - Estimando ultimo concurso: {ultimo_concurso}")
            
            if ultimo_concurso:
                # Usa o limite solicitado
                limite_real = min(limite, ultimo_concurso)
                print(f"    Buscando {limite_real} concursos (do {ultimo_concurso} para tras)...")
                
                # Busca com timeout e delays
                contador = 0
                tentativas = 0
                numeros_ja_buscados = set()  # Evita buscar o mesmo número duas vezes
                sem_resultado_seguidos = 0
                max_sem_resultado = 100  # Para após 100 tentativas sem resultado
                
                # Estratégia: começa do último e vai para trás
                for num in range(ultimo_concurso, max(1, ultimo_concurso - limite_real), -1):
                    if num in numeros_ja_buscados:
                        continue
                    
                    tentativas += 1
                    
                    # Se muitas tentativas sem resultado, tenta estratégia diferente
                    if sem_resultado_seguidos >= max_sem_resultado:
                        print(f"    AVISO - Muitas tentativas sem resultado, tentando estrategia alternativa...")
                        # Tenta buscar em intervalos maiores (últimos 50, 100, 150, etc)
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
                        
                        # Se ainda não encontrou nada, para
                        if sem_resultado_seguidos >= max_sem_resultado * 2:
                            print(f"    AVISO - Parando busca apos muitas tentativas sem resultado")
                            break
                    
                    try:
                        c = self._buscar_concurso_especifico(num)
                        if c:
                            concursos.append(c)
                            contador += 1
                            numeros_ja_buscados.add(num)
                            sem_resultado_seguidos = 0  # Reset contador
                        else:
                            sem_resultado_seguidos += 1
                        
                        # Limite de segurança
                        if len(concursos) >= limite_real:
                            break
                        
                        # Mostra progresso a cada 10 tentativas ou a cada 5 concursos encontrados
                        if tentativas % 10 == 0 or (contador > 0 and contador % 5 == 0):
                            print(f"      Progresso: {contador}/{limite_real} concursos (buscando {num}...)")
                            time.sleep(0.1)  # Delay um pouco maior
                        
                        # Mostra progresso mesmo se não encontrou nada ainda
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
    
    def _processar_concurso(self, concurso) -> Optional[Dict]:
        """Processa um concurso e retorna no formato padrão"""
        try:
            if isinstance(concurso, str):
                return None
            
            if not isinstance(concurso, dict):
                return None
            
            # Tenta diferentes formatos de número do concurso
            numero = (concurso.get('numero') or 
                     concurso.get('nuConcurso') or 
                     concurso.get('numeroConcurso') or
                     concurso.get('concurso') or
                     concurso.get('numeroConcursoProximo') or
                     concurso.get('numeroConcursoAnterior') or
                     concurso.get('numero_concurso') or
                     concurso.get('concurso_numero'))
            
            if not numero:
                return None
            
            try:
                numero = int(numero)
            except (ValueError, TypeError):
                return None
            
            # Tenta diferentes formatos de dezenas
            dezenas = None
            
            # Formato 1: listaDezenas (array direto)
            if 'listaDezenas' in concurso:
                dezenas = concurso['listaDezenas']
            # Formato 2: dezenas (array)
            elif 'dezenas' in concurso:
                dezenas = concurso['dezenas']
            # Formato 3: numeros (array)
            elif 'numeros' in concurso:
                dezenas = concurso['numeros']
            # Formato 4: listaDezenasSorteadas
            elif 'listaDezenasSorteadas' in concurso:
                dezenas = concurso['listaDezenasSorteadas']
            # Formato 5: dezenasSorteadas
            elif 'dezenasSorteadas' in concurso:
                dezenas = concurso['dezenasSorteadas']
            # Formato 6: resultado (pode conter listaDezenas)
            elif 'resultado' in concurso and isinstance(concurso['resultado'], dict):
                dezenas = (concurso['resultado'].get('listaDezenas') or 
                          concurso['resultado'].get('dezenas') or
                          concurso['resultado'].get('numeros'))
            # Formato 7: listaDezenas pode estar dentro de outro objeto
            elif isinstance(concurso.get('listaDezenas'), dict):
                dezenas = concurso['listaDezenas'].get('listaDezenas')
            # Formato 8: data pode conter listaDezenas
            elif isinstance(concurso.get('data'), dict):
                dezenas = (concurso['data'].get('listaDezenas') or 
                          concurso['data'].get('dezenas'))
            
            if not dezenas:
                return None
            
            # Garante que é uma lista
            if not isinstance(dezenas, list):
                if isinstance(dezenas, str):
                    # Tenta parsear string
                    dezenas = dezenas.split(',') if ',' in dezenas else dezenas.split()
                elif isinstance(dezenas, dict):
                    # Pode ser um objeto com números
                    dezenas = list(dezenas.values())
                else:
                    return None
            
            numeros_int = []
            for d in dezenas:
                try:
                    # Remove espaços e converte
                    num_str = str(d).strip()
                    # Remove caracteres não numéricos
                    num_str = ''.join(filter(str.isdigit, num_str))
                    if num_str:
                        num = int(num_str)
                        if 1 <= num <= 80:
                            numeros_int.append(num)
                except (ValueError, TypeError):
                    continue
            
            # Remove duplicatas
            numeros_int = list(dict.fromkeys(numeros_int))
            
            # Valida que tem pelo menos 7 números (a API pode retornar 7 ou 10)
            # Timemania pode ter mudado as regras ou a API retorna formato diferente
            if len(numeros_int) >= 7:
                # Se tiver menos de 10, pode ser que a API retorne apenas os principais
                # Mas vamos aceitar se tiver pelo menos 7 números válidos
                return {
                    'concurso': numero,
                    'numeros': sorted(numeros_int),
                    'time_coracao': (concurso.get('nomeTimeCoracaoMesSorte') or
                                   concurso.get('timeCoracao') or 
                                   concurso.get('time_coracao') or 
                                   concurso.get('timeDoCoracao') or 
                                   concurso.get('time_do_coracao') or ''),
                    'data': (concurso.get('dataApuracao') or 
                           concurso.get('data') or 
                           concurso.get('dataSorteio') or 
                           concurso.get('data_sorteio') or '')
                }
        except Exception as e:
            # Log do erro para debug (opcional)
            # print(f"Erro ao processar concurso: {e}")
            pass
        
        return None
    
    def obter_historico_api(self) -> List[Dict]:
        """
        Obtém histórico de múltiplas fontes
        Busca últimos 500 concursos usando várias APIs
        Retorna lista de concursos com números sorteados
        """
        concursos = []
        
        print("Buscando historico Timemania de multiplas fontes (ultimos 500 concursos)...")
        
        # Método 1: Tenta carregar arquivo local primeiro (mais rápido)
        print("  [1/5] Verificando arquivo local...")
        concursos_local = self._buscar_arquivo_local()
        if concursos_local and len(concursos_local) >= 50:
            # Limita aos últimos 500 do arquivo local
            concursos_local = concursos_local[-500:] if len(concursos_local) > 500 else concursos_local
            concursos.extend(concursos_local)
            print(f"  OK - Arquivo local: {len(concursos_local)} concursos encontrados")
        
        # Método 2: API oficial da Caixa
        print("  [2/5] Buscando na API oficial da Caixa...")
        concursos_caixa = self._buscar_api_caixa()
        if concursos_caixa:
            concursos.extend(concursos_caixa)
            print(f"  OK - API Caixa: {len(concursos_caixa)} concursos encontrados")
        
        # Método 3: APIs alternativas (múltiplas fontes)
        if len(concursos) < 500:
            print("  [3/5] Buscando em APIs alternativas...")
            concursos_alternativas = self._buscar_apis_alternativas()
            if concursos_alternativas:
                concursos.extend(concursos_alternativas)
                print(f"  OK - APIs alternativas: {len(concursos_alternativas)} concursos encontrados")
        
        # Método 4: Busca complementar se ainda não tiver 500
        if len(concursos) < 500:
            print(f"  [4/5] Busca complementar para atingir 500 (atual: {len(concursos)})...")
            limite_restante = 500 - len(concursos)
            if limite_restante > 0:
                concursos_complementar = self._buscar_concursos_limitado(limite_restante)
                if concursos_complementar:
                    concursos.extend(concursos_complementar)
                    print(f"  OK - Busca complementar: {len(concursos_complementar)} concursos encontrados")
                
                # Se ainda não tiver 500, continua buscando usando a URL correta
                if len(concursos) < 500:
                    print(f"  Continuando busca para atingir 500 (atual: {len(concursos)})...")
                    ultimo = self._obter_ultimo_concurso() or 2335
                    limite_adicional = 500 - len(concursos)
                    print(f"    Buscando mais {limite_adicional} concursos a partir do {ultimo}...")
                    
                    contador_complementar = 0
                    for num in range(ultimo - len(concursos), max(1, ultimo - limite_adicional - len(concursos)), -1):
                        try:
                            c = self._buscar_concurso_especifico(num)
                            if c:
                                concursos.append(c)
                                contador_complementar += 1
                            if len(concursos) >= 500:
                                break
                            if contador_complementar % 10 == 0:
                                print(f"      Progresso: {len(concursos)}/500 concursos...")
                            time.sleep(0.1)
                        except:
                            continue
                    
                    if len(concursos) >= 500:
                        print(f"  OK - Limite de 500 concursos atingido!")
                    else:
                        print(f"  AVISO - Encontrados {len(concursos)} concursos (objetivo: 500)")
        
        # Método 5: Se ainda não tiver, tenta carregar do cache
        if len(concursos) < 50:
            print("  [5/5] Carregando do cache...")
            cache = self._carregar_cache()
            if cache:
                # Limita aos últimos 500 do cache
                cache = cache[-500:] if len(cache) > 500 else cache
                concursos.extend(cache)
                print(f"  OK - Cache: {len(cache)} concursos encontrados")
        
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
        
        # Limita a 500 concursos máximo (últimos 500)
        if len(resultado) > 500:
            resultado = resultado[-500:]
        
        if resultado:
            print(f"OK - Total: {len(resultado)} concursos carregados (ultimos 500)")
            return resultado
        else:
            print("AVISO - Nenhum concurso encontrado, usando cache...")
            cache = self._carregar_cache()
            if cache:
                # Limita cache também a 500
                if len(cache) > 500:
                    cache = cache[-500:]
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
                
                # Limita a 500 concursos máximo
                if len(historico_completo) > 500:
                    historico_completo = historico_completo[-500:]
                    print(f"Limitado aos ultimos 500 concursos")
                
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

