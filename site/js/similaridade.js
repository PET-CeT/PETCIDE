/**
 * Similaridade de textos por TF-IDF + cosseno, no navegador.
 *
 * Reproduz o TfidfVectorizer do scikit-learn com os parâmetros padrão
 * (smooth_idf, norma L2) e o tokenizador abaixo. A equivalência é verificada
 * em tests/ contra a implementação de referência em Python.
 *
 * O vocabulário e o IDF vêm apenas da base de deliberações: palavras que só
 * aparecem nos textos digitados são ignoradas.
 */

/** Separa o texto em palavras (letras/dígitos), minúsculas, com 2+ caracteres e sem stopwords. */
export function tokenizar(texto, stopwords) {
    const palavras = String(texto).normalize('NFC').toLowerCase().match(/[\p{L}\p{N}]+/gu) || [];
    return palavras.filter(p => [...p].length >= 2 && !stopwords.has(p));
}

/** Primeiro ano (19xx/20xx) que aparece no texto, ou null. */
export function extrairAno(texto) {
    const m = String(texto).match(/(?:19|20)\d{2}/);
    return m ? Number(m[0]) : null;
}

/** Monta o índice TF-IDF da base. `deliberacoes`: [{id, evento, ano, descricao}]. */
export function criarIndice(deliberacoes, listaStopwords) {
    const stopwords = new Set(listaStopwords);
    const tokensPorDoc = deliberacoes.map(d => tokenizar(d.descricao, stopwords));

    const df = new Map();
    for (const tokens of tokensPorDoc) {
        for (const termo of new Set(tokens)) df.set(termo, (df.get(termo) || 0) + 1);
    }

    const n = deliberacoes.length;
    const idf = new Map();
    for (const [termo, freq] of df) idf.set(termo, Math.log((1 + n) / (1 + freq)) + 1);

    const indice = { stopwords, idf, deliberacoes, vetores: [] };
    indice.vetores = tokensPorDoc.map(tokens => vetorizarTokens(tokens, idf));
    return indice;
}

function vetorizarTokens(tokens, idf) {
    const vetor = new Map();
    for (const termo of tokens) {
        if (idf.has(termo)) vetor.set(termo, (vetor.get(termo) || 0) + 1);
    }
    let norma = 0;
    for (const [termo, tf] of vetor) {
        const peso = tf * idf.get(termo);
        vetor.set(termo, peso);
        norma += peso * peso;
    }
    norma = Math.sqrt(norma);
    if (norma > 0) for (const [termo, peso] of vetor) vetor.set(termo, peso / norma);
    return vetor;
}

export function vetorizar(texto, indice) {
    return vetorizarTokens(tokenizar(texto, indice.stopwords), indice.idf);
}

/** Cosseno entre dois vetores já normalizados. */
export function cosseno(a, b) {
    if (a.size > b.size) [a, b] = [b, a];
    let soma = 0;
    for (const [termo, peso] of a) {
        const outro = b.get(termo);
        if (outro !== undefined) soma += peso * outro;
    }
    return soma;
}

/**
 * Para cada consulta {evento, descricao}, retorna os `limite` textos mais
 * parecidos entre a base e as demais consultas. Textos do mesmo ano da
 * consulta (ano tirado do nome do evento) são ignorados, e textos com
 * similaridade 0 não entram no resultado.
 *
 * Cada resultado: {origem: 'base' | 'consulta', indice, similaridade}, em que
 * `indice` aponta para `indice.deliberacoes` ou para `consultas`.
 */
export function buscar(consultas, indice, { limite = 5 } = {}) {
    const vetoresConsulta = consultas.map(c => vetorizar(c.descricao, indice));
    const anosConsulta = consultas.map(c => extrairAno(c.evento));

    return consultas.map((consulta, i) => {
        const ano = anosConsulta[i];
        const candidatos = [];

        indice.deliberacoes.forEach((d, j) => {
            if (ano !== null && d.ano === ano) return;
            candidatos.push({ origem: 'base', indice: j, similaridade: cosseno(vetoresConsulta[i], indice.vetores[j]) });
        });
        consultas.forEach((_, j) => {
            if (j === i || (ano !== null && anosConsulta[j] === ano)) return;
            candidatos.push({ origem: 'consulta', indice: j, similaridade: cosseno(vetoresConsulta[i], vetoresConsulta[j]) });
        });

        return candidatos
            .filter(c => c.similaridade > 1e-12)
            .sort((a, b) => b.similaridade - a.similaridade)
            .slice(0, limite);
    });
}
