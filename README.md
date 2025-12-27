# Sistema para sustentar o Girinho com a Loto Fácil

Sistema inteligente para gerar fechamentos de jogos da Lotofácil com alta probabilidade de acerto, utilizando análise de histórico e técnicas avançadas de otimização.

## 🎯 Funcionalidades

- 📊 **Análise de histórico**: Obtém e analisa resultados dos concursos anteriores
- 🔍 **Identificação de padrões**: Detecta frequências, atrasos e sequências
- 🎯 **Geração de fechamentos**: Múltiplas estratégias de otimização
- 📈 **Estatísticas detalhadas**: Números quentes, frios, atrasados
- 🎲 **Técnicas avançadas**: Matrizes de fechamento e balanceamento
- 💻 **Interface web**: Interface moderna e intuitiva
- 📥 **Exportação**: Exporta jogos gerados para arquivo de texto

## 🚀 Instalação

### Pré-requisito: Python 3.8+

**Se você não tem Python instalado:**
- Windows: Baixe em https://www.python.org/downloads/
- **IMPORTANTE**: Marque "Add Python to PATH" durante a instalação
- Veja [INSTALACAO.md](INSTALACAO.md) para instruções detalhadas

### Instalação das Dependências

**Opção 1: Script automático (Windows)**
```bash
instalar.bat
```

**Opção 2: Manual**
```bash
python -m pip install -r requirements.txt
```

ou, se `python` não funcionar:
```bash
py -m pip install -r requirements.txt
```

## 💻 Uso

### Interface Web (Recomendado)

**Opção 1: Script automático (Windows)**
```bash
executar.bat
```

**Opção 2: Manual**
```bash
python app.py
```

ou

```bash
py app.py
```

Acesse `http://localhost:5000` no navegador.

### Teste do Sistema

Para testar o sistema via linha de comando:

```bash
python test_system.py
```

## 📖 Estratégias Disponíveis

1. **Misto** (Recomendado): Combina múltiplas técnicas
2. **Por Frequência**: Foca em números mais sorteados
3. **Balanceado**: Mantém distribuição estatística
4. **Por Atraso**: Prioriza números atrasados

Veja [TECNICAS.md](TECNICAS.md) para detalhes completos.

## ⚠️ Aviso Importante

Este sistema é uma ferramenta de análise estatística baseada em padrões históricos. **Não garante acertos**, apenas aumenta a probabilidade baseada em dados passados. Jogue com responsabilidade.

## 📁 Estrutura do Projeto

```
lotofacil/
├── src/
│   ├── historico.py      # Gerenciamento de histórico
│   ├── analise.py        # Análise de padrões
│   └── fechamento.py     # Geração de fechamentos
├── templates/
│   └── index.html        # Interface web
├── static/
│   ├── css/
│   │   └── style.css     # Estilos
│   └── js/
│       └── app.js        # JavaScript
├── app.py                # Aplicação Flask
├── test_system.py        # Script de teste
└── requirements.txt      # Dependências
```

## 🔧 Configuração

O sistema tenta obter dados automaticamente da API da Caixa. Se não conseguir, usa cache local em `data/historico.json`.

## 📝 Licença

Este projeto é fornecido "como está", sem garantias. Use por sua conta e risco.

