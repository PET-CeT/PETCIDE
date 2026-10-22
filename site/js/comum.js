/** Funções compartilhadas pelas páginas do PETCIDE. */

let deliberacoes = null;

/** Base de deliberações [{id, evento, ano, descricao}], carregada uma vez por página. */
export async function carregarDeliberacoes() {
    deliberacoes ??= fetch('data/deliberacoes.json').then(resposta => {
        if (!resposta.ok) throw new Error(`HTTP ${resposta.status} ao carregar deliberações`);
        return resposta.json();
    });
    return deliberacoes;
}

export async function carregarStopwords() {
    const resposta = await fetch('data/stopwords-pt.json');
    if (!resposta.ok) throw new Error(`HTTP ${resposta.status} ao carregar stopwords`);
    return resposta.json();
}

/**
 * Cria um elemento. Filhos em texto viram nós de texto, então conteúdo vindo
 * dos dados nunca é interpretado como HTML.
 */
export function el(tag, atributos = {}, ...filhos) {
    const elemento = document.createElement(tag);
    for (const [nome, valor] of Object.entries(atributos)) {
        if (nome.startsWith('on')) elemento.addEventListener(nome.slice(2), valor);
        else if (valor !== false && valor != null) elemento.setAttribute(nome, valor === true ? '' : valor);
    }
    for (const filho of filhos.flat()) {
        if (filho != null && filho !== false) elemento.append(filho);
    }
    return elemento;
}

/** Minúsculas e sem acentos, para buscas que ignoram acentuação. */
export function semAcento(texto) {
    return String(texto).normalize('NFD').replace(/\p{M}/gu, '').toLowerCase();
}

export function truncar(texto, tamanho) {
    return texto.length <= tamanho ? texto : texto.slice(0, tamanho).trimEnd() + '…';
}

export function mostrarErro(container, mensagem) {
    container.replaceChildren(el('div', { class: 'alert alert-danger' }, mensagem));
}
