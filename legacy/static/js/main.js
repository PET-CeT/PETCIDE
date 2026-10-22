/**
 * Funções comuns para o SIGDEB
 */

// Formatação de data
function formatarData(dataString) {
    if (!dataString) return '';
    const data = new Date(dataString);
    return data.toLocaleDateString('pt-BR');
}

// Truncar texto
function truncarTexto(texto, tamanho = 100) {
    if (!texto) return '';
    if (texto.length <= tamanho) return texto;
    return texto.substring(0, tamanho) + '...';
}

// Animar scroll para elemento
function scrollPara(elementoId) {
    const elemento = document.getElementById(elementoId);
    if (elemento) {
        elemento.scrollIntoView({ behavior: 'smooth' });
    }
}

// Mostrar notificação
function mostrarNotificacao(mensagem, tipo = 'info') {
    alert(mensagem);
}