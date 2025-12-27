# Banco de Dados - Sistema Lotofácil

## 📊 Visão Geral

O sistema agora utiliza **SQLite** para armazenar o histórico de concursos, evitando buscar na web toda vez que o sistema é iniciado.

## 🎯 Vantagens

1. **Performance**: Carregamento muito mais rápido do histórico
2. **Offline**: Funciona mesmo sem internet (após primeira sincronização)
3. **Eficiência**: Busca apenas concursos novos, não todos
4. **Persistência**: Dados permanecem entre execuções
5. **Confiabilidade**: Não depende da disponibilidade da API

## 📁 Localização

O banco de dados é criado automaticamente em:
```
data/lotofacil.db
```

## 🔧 Funcionamento

### Primeira Execução

1. Sistema detecta que o banco está vazio
2. Busca concursos da API (até 2000)
3. Salva todos no banco de dados
4. Próximas execuções serão muito mais rápidas

### Execuções Seguintes

1. Sistema carrega dados do banco (instantâneo)
2. Ao clicar em "Atualizar Histórico":
   - Verifica qual é o último concurso no banco
   - Verifica qual é o último concurso na API
   - Busca **apenas os concursos novos**
   - Salva no banco

### Sincronização Inteligente

O sistema possui sincronização inteligente que:
- ✅ Identifica concursos faltantes
- ✅ Busca apenas o que falta
- ✅ Não duplica dados
- ✅ Atualiza automaticamente

## 📊 Estrutura do Banco

### Tabela: `concursos`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| numero | INTEGER | Número do concurso (chave primária) |
| data_apuracao | TEXT | Data do sorteio |
| numeros | TEXT | Números sorteados (JSON) |
| data_insercao | TIMESTAMP | Quando foi inserido no banco |
| data_atualizacao | TIMESTAMP | Última atualização |

## 🛠️ Funcionalidades

### Carregamento Automático

Ao iniciar o sistema:
- Tenta carregar do banco primeiro
- Se banco vazio, busca da API
- Salva automaticamente no banco

### Atualização Manual

Clique em "Atualizar Histórico":
- Sincroniza apenas concursos novos
- Muito mais rápido que buscar tudo
- Mantém banco sempre atualizado

### Estatísticas do Banco

Acesse `/api/estatisticas-banco` para ver:
- Total de concursos no banco
- Último concurso armazenado
- Data do último concurso

## 🔍 Consultas Úteis

O banco permite:
- Buscar concurso específico
- Listar últimos N concursos
- Filtrar por período
- Verificar concursos faltantes
- Contar total de registros

## ⚙️ Configuração

O banco de dados está **habilitado por padrão**.

Para desabilitar (usar apenas cache JSON):
```python
historico_manager = HistoricoLotofacil(usar_banco=False)
```

## 📈 Performance

### Com Banco de Dados
- Carregamento inicial: **Instantâneo** (se banco populado)
- Atualização: **Apenas novos concursos** (segundos)
- Uso de memória: **Mínimo** (dados no disco)

### Sem Banco de Dados
- Carregamento inicial: **Minutos** (busca 2000 concursos)
- Atualização: **Minutos** (busca tudo novamente)
- Uso de memória: **Alto** (tudo em memória)

## 🔒 Backup

O arquivo `data/lotofacil.db` contém todo o histórico.

**Recomendação**: Faça backup periódico deste arquivo.

## 🗑️ Limpeza

Para limpar o banco (cuidado!):
```python
from src.database import DatabaseLotofacil
db = DatabaseLotofacil()
db.limpar_banco()
```

## 📝 Notas

- O banco é criado automaticamente na primeira execução
- Dados são salvos automaticamente após busca da API
- Cache JSON ainda é mantido para compatibilidade
- Banco tem prioridade sobre cache JSON

## 🚀 Benefícios Práticos

1. **Inicialização Rápida**: Sistema inicia em segundos
2. **Atualizações Rápidas**: Sincroniza apenas o novo
3. **Economia de Banda**: Não baixa dados repetidos
4. **Confiabilidade**: Funciona offline após primeira sincronização
5. **Escalabilidade**: Suporta milhares de concursos sem problemas

---

**Conclusão**: O banco de dados torna o sistema muito mais eficiente e rápido, especialmente após a primeira sincronização.

