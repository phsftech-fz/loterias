// Sistema para sustentar o Girinho com a Loto Fácil - JavaScript

let estatisticas = null;
let jogosGerados = [];

// Carrega combinação mais repetida
async function carregarCombinacaoMaisRepetida() {
    try {
        const response = await fetch('/api/combinacao-mais-repetida');
        const data = await response.json();
        
        const footerDiv = document.getElementById('combinacao-mais-repetida');
        
        if (data.success && data.combinacao && data.combinacao.length > 0) {
            let html = '';
            
            // Mostra os números da combinação
            data.combinacao.forEach(numero => {
                html += `<span class="numero-badge">${numero.toString().padStart(2, '0')}</span>`;
            });
            
            // Mostra a quantidade de vezes que se repetiu
            html += `<span class="quantidade-badge">Repetiu ${data.quantidade} vez${data.quantidade !== 1 ? 'es' : ''}</span>`;
            
            footerDiv.innerHTML = html;
        } else {
            footerDiv.innerHTML = '<span class="loading-text">Nenhuma combinação repetida encontrada</span>';
        }
    } catch (error) {
        console.error('Erro ao carregar combinação mais repetida:', error);
        document.getElementById('combinacao-mais-repetida').innerHTML = 
            '<span class="loading-text">Erro ao carregar</span>';
    }
}

// Carrega estatísticas ao carregar a página
document.addEventListener('DOMContentLoaded', () => {
    carregarEstatisticas();
    carregarCombinacaoMaisRepetida();
    
    document.getElementById('btn-gerar').addEventListener('click', gerarJogos);
    document.getElementById('btn-atualizar').addEventListener('click', atualizarHistorico);
    document.getElementById('btn-exportar').addEventListener('click', exportarJogos);
    document.getElementById('btn-conferir').addEventListener('click', conferirJogos);
});

async function carregarEstatisticas() {
    mostrarLoading();
    try {
        const response = await fetch('/api/estatisticas');
        const data = await response.json();
        
        if (data.success) {
            estatisticas = data.data;
            atualizarInterfaceEstatisticas();
        } else {
            alert('Erro ao carregar estatísticas: ' + data.error);
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao carregar estatísticas');
    } finally {
        esconderLoading();
    }
}

function atualizarInterfaceEstatisticas() {
    if (!estatisticas) return;
    
    // Total de concursos
    document.getElementById('total-concursos').textContent = estatisticas.total_concursos || 0;
    
    // Números quentes
    const quentes = estatisticas.numeros_quentes || [];
    document.getElementById('numeros-quentes').textContent = quentes.length;
    
    // Números atrasados
    const atrasados = estatisticas.numeros_atrasados || [];
    document.getElementById('numeros-atrasados').textContent = atrasados.length;
    
    // Mais sorteados
    const maisSorteados = estatisticas.mais_sorteados || [];
    const maisSorteadosDiv = document.getElementById('mais-sorteados');
    maisSorteadosDiv.innerHTML = '';
    maisSorteados.slice(0, 10).forEach(([numero, freq]) => {
        const badge = document.createElement('span');
        badge.className = 'number-badge';
        badge.textContent = `${numero} (${freq}x)`;
        maisSorteadosDiv.appendChild(badge);
    });
    
    // Menos sorteados
    const menosSorteados = estatisticas.menos_sorteados || [];
    const menosSorteadosDiv = document.getElementById('menos-sorteados');
    menosSorteadosDiv.innerHTML = '';
    menosSorteados.slice(0, 10).forEach(([numero, freq]) => {
        const badge = document.createElement('span');
        badge.className = 'number-badge';
        badge.style.background = '#dc3545';
        badge.textContent = `${numero} (${freq}x)`;
        menosSorteadosDiv.appendChild(badge);
    });
}

async function gerarJogos() {
    mostrarLoading();
    
    const estrategia = document.getElementById('estrategia').value;
    const quantidade = parseInt(document.getElementById('quantidade').value);
    const quantidadeNumeros = parseInt(document.getElementById('quantidade-numeros').value);
    const numerosFixosInput = document.getElementById('numeros-fixos').value;
    
    let numerosFixos = [];
    if (numerosFixosInput.trim()) {
        numerosFixos = numerosFixosInput.split(',').map(n => parseInt(n.trim())).filter(n => !isNaN(n) && n >= 1 && n <= 25);
    }
    
    try {
        const response = await fetch('/api/gerar-jogos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                estrategia: estrategia,
                quantidade: quantidade,
                quantidade_numeros: quantidadeNumeros,
                numeros_fixos: numerosFixos
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            jogosGerados = data.jogos;
            exibirJogos(jogosGerados);
        } else {
            alert('Erro ao gerar jogos: ' + data.error);
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao gerar jogos');
    } finally {
        esconderLoading();
    }
}

function exibirJogos(jogos) {
    const container = document.getElementById('jogos-container');
    const panel = document.getElementById('results-panel');
    
    container.innerHTML = '';
    
    jogos.forEach((jogo, index) => {
        const card = document.createElement('div');
        card.className = 'jogo-card';
        
        const titulo = document.createElement('h4');
        titulo.textContent = `Jogo ${index + 1}`;
        
        const numerosDiv = document.createElement('div');
        numerosDiv.className = 'jogo-numeros';
        
        jogo.forEach(numero => {
            const span = document.createElement('span');
            span.className = 'numero-jogo';
            span.textContent = numero.toString().padStart(2, '0');
            numerosDiv.appendChild(span);
        });
        
        card.appendChild(titulo);
        card.appendChild(numerosDiv);
        container.appendChild(card);
    });
    
    panel.style.display = 'block';
    panel.scrollIntoView({ behavior: 'smooth' });
}

async function atualizarHistorico() {
    mostrarLoading();
    try {
        const response = await fetch('/api/atualizar-historico', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(`Histórico atualizado! Total de concursos: ${data.total_concursos}`);
            carregarEstatisticas();
            carregarCombinacaoMaisRepetida(); // Atualiza combinação mais repetida
        } else {
            alert('Erro ao atualizar histórico: ' + data.error);
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao atualizar histórico');
    } finally {
        esconderLoading();
    }
}

function exportarJogos() {
    if (jogosGerados.length === 0) {
        alert('Nenhum jogo para exportar');
        return;
    }
    
    let texto = 'JOGOS GERADOS - LOTOFÁCIL\n';
    texto += '='.repeat(50) + '\n\n';
    
    jogosGerados.forEach((jogo, index) => {
        texto += `Jogo ${(index + 1).toString().padStart(2, '0')} (${jogo.length} números): `;
        texto += jogo.map(n => n.toString().padStart(2, '0')).join(' - ');
        texto += '\n';
    });
    
    texto += '\n' + '='.repeat(50) + '\n';
    texto += `Total de jogos: ${jogosGerados.length}\n`;
    if (jogosGerados.length > 0) {
        texto += `Quantidade de números por jogo: ${jogosGerados[0].length}\n`;
    }
    texto += `Gerado em: ${new Date().toLocaleString('pt-BR')}\n`;
    
    const blob = new Blob([texto], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `lotofacil_jogos_${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

function mostrarLoading() {
    document.getElementById('loading').style.display = 'flex';
}

function esconderLoading() {
    document.getElementById('loading').style.display = 'none';
}

async function conferirJogos() {
    const fileInput = document.getElementById('file-import');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Por favor, selecione um arquivo TXT com seus jogos');
        return;
    }
    
    mostrarLoading();
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/importar-jogos', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            exibirResultadoConferencia(data.resultado);
        } else {
            alert('Erro ao conferir jogos: ' + data.error);
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao conferir jogos');
    } finally {
        esconderLoading();
    }
}

function exibirResultadoConferencia(resultado) {
    const panel = document.getElementById('conference-results');
    const ultimoDiv = document.getElementById('ultimo-concurso-result');
    const historicoDiv = document.getElementById('historico-completo-result');
    
    // Limpa resultados anteriores
    ultimoDiv.innerHTML = '';
    historicoDiv.innerHTML = '';
    
    // Exibe resultado do último concurso
    if (resultado.ultimo_concurso && resultado.ultimo_concurso.length > 0) {
        let html = '<div style="background: #e3f2fd; padding: 10px; border-radius: 5px; margin-bottom: 15px;">';
        html += '<p style="margin: 0; color: #1976d2; font-weight: bold;"><i class="fas fa-sort-amount-down"></i> Resultados ordenados pela melhor média de acertos</p>';
        html += '</div>';
        
        resultado.ultimo_concurso.forEach(ultimo => {
            html += criarHTMLUltimoConcurso(ultimo);
        });
        ultimoDiv.innerHTML = html;
    }
    
    // Exibe análise do histórico completo
    if (resultado.historico_completo && resultado.historico_completo.length > 0) {
        let html = '<div style="background: #e3f2fd; padding: 10px; border-radius: 5px; margin-bottom: 15px;">';
        html += '<p style="margin: 0; color: #1976d2; font-weight: bold;"><i class="fas fa-sort-amount-down"></i> Resultados ordenados pela melhor média de acertos</p>';
        html += '</div>';
        html += `<p><strong>Total de concursos analisados:</strong> ${resultado.total_concursos_historico}</p>`;
        resultado.historico_completo.forEach(estat => {
            html += criarHTMLHistoricoCompleto(estat);
        });
        historicoDiv.innerHTML = html;
    }
    
    panel.style.display = 'block';
    panel.scrollIntoView({ behavior: 'smooth' });
}

function criarHTMLUltimoConcurso(dados) {
    const acertos = dados.quantidade_acertos;
    const quantidadeNumeros = dados.quantidade_numeros || dados.jogo.length;
    const percentual = dados.percentual_acertos || (acertos / quantidadeNumeros * 100).toFixed(2);
    
    // Ajusta classes de acertos baseado na quantidade de números
    let classeAcertos = 'acertos-0-11';
    if (quantidadeNumeros === 15) {
        classeAcertos = acertos >= 15 ? 'acertos-15' : 
                       acertos >= 14 ? 'acertos-14' : 
                       acertos >= 13 ? 'acertos-13' : 
                       acertos >= 12 ? 'acertos-12' : 'acertos-0-11';
    } else if (quantidadeNumeros === 16) {
        classeAcertos = acertos >= 16 ? 'acertos-15' : 
                       acertos >= 15 ? 'acertos-14' : 
                       acertos >= 14 ? 'acertos-13' : 
                       acertos >= 13 ? 'acertos-12' : 'acertos-0-11';
    } else if (quantidadeNumeros >= 17) {
        classeAcertos = acertos >= quantidadeNumeros ? 'acertos-15' : 
                       acertos >= quantidadeNumeros - 1 ? 'acertos-14' : 
                       acertos >= quantidadeNumeros - 2 ? 'acertos-13' : 
                       acertos >= quantidadeNumeros - 3 ? 'acertos-12' : 'acertos-0-11';
    }
    
    let html = `
        <div class="jogo-conferencia">
            <div class="jogo-conferencia-header">
                <h5>Concurso ${dados.concurso}${dados.data ? ' - ' + dados.data : ''}</h5>
                <span class="acertos-badge ${classeAcertos}">${acertos} acertos (${percentual}%)</span>
            </div>
            <div>
                <p><strong>Seu jogo (${quantidadeNumeros} números):</strong> ${dados.jogo.map(n => n.toString().padStart(2, '0')).join(' - ')}</p>
                <p><strong>Números sorteados:</strong> ${dados.numeros_sorteados.map(n => n.toString().padStart(2, '0')).join(' - ')}</p>
            </div>
    `;
    
    if (dados.acertos && dados.acertos.length > 0) {
        html += `
            <div class="numeros-acertados">
                <strong>Números acertados (${acertos}/${quantidadeNumeros}):</strong>
                ${dados.acertos.map(n => `<span class="numero-acertado">${n.toString().padStart(2, '0')}</span>`).join('')}
            </div>
        `;
    } else {
        html += `<p style="color: #dc3545;"><strong>Nenhum acerto neste concurso</strong></p>`;
    }
    
    html += '</div>';
    return html;
}

function criarHTMLHistoricoCompleto(estat) {
    const percentual = estat.percentual_com_acertos.toFixed(2);
    const media = estat.media_acertos.toFixed(2);
    const quantidadeNumeros = estat.quantidade_numeros || estat.jogo.length;
    
    let html = `
        <div class="jogo-conferencia">
            <div class="jogo-conferencia-header">
                <h5>Jogo ${estat.jogo_numero} (${quantidadeNumeros} números)</h5>
            </div>
            <div>
                <p><strong>Seu jogo:</strong> ${estat.jogo.map(n => n.toString().padStart(2, '0')).join(' - ')}</p>
            </div>
            <div class="estatisticas-jogo">
                <p><strong>Total de concursos analisados:</strong> ${estat.total_concursos}</p>
                <p><strong>Concursos com pelo menos 1 acerto:</strong> ${estat.concursos_com_acertos} (${percentual}%)</p>
                <p><strong>Média de acertos por concurso:</strong> ${media} de ${quantidadeNumeros} números</p>
                <p><strong>Máximo de acertos:</strong> ${estat.max_acertos} de ${quantidadeNumeros}</p>
                <p><strong>Mínimo de acertos:</strong> ${estat.min_acertos} de ${quantidadeNumeros}</p>
                <p><strong>Total de acertos acumulados:</strong> ${estat.total_acertos}</p>
            </div>
            <div>
                <strong>Frequência de cada número no histórico:</strong>
                <div class="frequencia-numeros">
    `;
    
    // Ordena números por frequência
    const numerosOrdenados = Object.entries(estat.frequencia_numeros)
        .sort((a, b) => b[1] - a[1]);
    
    numerosOrdenados.forEach(([numero, freq]) => {
        const percentualNum = ((freq / estat.total_concursos) * 100).toFixed(1);
        let classe = 'baixa';
        if (percentualNum >= 50) classe = 'alta';
        else if (percentualNum >= 30) classe = 'media';
        
        html += `<span class="freq-badge ${classe}">${numero.toString().padStart(2, '0')}: ${freq}x (${percentualNum}%)</span>`;
    });
    
    html += `
                </div>
            </div>
    `;
    
    // Top 10 concursos com mais acertos
    if (estat.estatisticas_concursos && estat.estatisticas_concursos.length > 0) {
        html += `
            <div style="margin-top: 15px;">
                <strong>Top 10 concursos com mais acertos:</strong>
                <ul style="margin-top: 10px; padding-left: 20px;">
        `;
        estat.estatisticas_concursos.forEach(conc => {
            html += `<li>Concurso ${conc.concurso}${conc.data ? ' (' + conc.data + ')' : ''}: <strong>${conc.acertos} acertos</strong> - Números: ${conc.numeros_acertados.map(n => n.toString().padStart(2, '0')).join(', ')}</li>`;
        });
        html += '</ul></div>';
    }
    
    html += '</div>';
    return html;
}

