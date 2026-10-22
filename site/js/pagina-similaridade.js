import { carregarDeliberacoes, carregarStopwords, el, truncar, mostrarErro } from './comum.js';
import { criarIndice, buscar, extrairAno } from './similaridade.js';

const RESULTADOS_POR_TEXTO = 5;

let indice = null;

document.addEventListener('DOMContentLoaded', async () => {
    const container = document.getElementById('textosContainer');
    container.append(criarItemTexto({ removivel: false }));

    document.getElementById('btnAddTexto').addEventListener('click', () => {
        container.append(criarItemTexto({ removivel: true }));
    });
    document.getElementById('similaridadeForm').addEventListener('submit', e => {
        e.preventDefault();
        analisar();
    });

    try {
        const [deliberacoes, stopwords] = await Promise.all([carregarDeliberacoes(), carregarStopwords()]);
        indice = criarIndice(deliberacoes, stopwords);
    } catch (erro) {
        console.error(erro);
        mostrarErro(document.getElementById('avisoForm'),
            'Não foi possível carregar a base de deliberações. Tente recarregar a página.');
        return;
    }
    document.getElementById('btnAnalisar').disabled = false;

    // Vindo de "Buscar parecidas" na página de deliberações.
    const id = Number(new URLSearchParams(location.search).get('id'));
    const origem = indice.deliberacoes.find(d => d.id === id);
    if (origem) {
        container.querySelector('.evento-input').value = origem.evento;
        container.querySelector('.descricao-input').value = origem.descricao;
        analisar();
    }
});

function criarItemTexto({ removivel }) {
    const item = el('div', { class: 'texto-item border rounded p-3 mb-3' });
    if (removivel) {
        item.append(el('div', { class: 'd-flex justify-content-end mb-2' },
            el('button', { type: 'button', class: 'btn btn-danger btn-sm', onclick: () => item.remove() },
                el('i', { class: 'bi bi-trash' }), ' Remover')));
    }
    item.append(
        el('div', { class: 'mb-3' },
            el('label', { class: 'form-label w-100' }, 'Evento (opcional)',
                el('input', { type: 'text', class: 'form-control evento-input', placeholder: 'Ex.: Assembleia ENAPET 2024' }))),
        el('div', { class: 'mb-3' },
            el('label', { class: 'form-label w-100' }, 'Descrição',
                el('textarea', { class: 'form-control descricao-input', rows: 3, placeholder: 'Digite o texto para análise' }))),
    );
    return item;
}

function analisar() {
    const consultas = [...document.querySelectorAll('.texto-item')]
        .map(item => ({
            evento: item.querySelector('.evento-input').value.trim(),
            descricao: item.querySelector('.descricao-input').value.trim(),
        }))
        .filter(c => c.descricao);

    const aviso = document.getElementById('avisoForm');
    if (consultas.length === 0) {
        aviso.replaceChildren(el('div', { class: 'alert alert-warning' }, 'Digite pelo menos um texto para análise.'));
        return;
    }
    aviso.replaceChildren();

    const resultados = buscar(consultas, indice, { limite: RESULTADOS_POR_TEXTO });
    document.getElementById('resultados').replaceChildren(
        ...consultas.map((consulta, i) => cartaoConsulta(consulta, resultados[i], consultas)));

    const container = document.getElementById('resultadosContainer');
    container.hidden = false;
    container.scrollIntoView({ behavior: 'smooth' });
}

function cartaoConsulta(consulta, resultados, consultas) {
    const ano = extrairAno(consulta.evento);
    const corpo = el('div', { class: 'card-body' },
        el('h6', {}, 'Texto base:'),
        el('p', { class: 'texto-longo' }, truncar(consulta.descricao, 600)),
        el('p', { class: 'text-muted small' }, ano
            ? `Deliberações de ${ano} foram ignoradas.`
            : 'Nenhum ano encontrado no nome do evento: todos os anos foram considerados.'),
        el('hr'));

    if (resultados.length === 0) {
        corpo.append(el('p', { class: 'mb-0' }, 'Nenhum texto parecido encontrado.'));
    } else {
        corpo.append(el('h6', {}, `Textos mais similares (${resultados.length}):`),
            el('ol', { class: 'list-group list-group-numbered' }, resultados.map(r => itemResultado(r, consultas))));
    }

    return el('div', { class: 'card mb-4' },
        el('div', { class: 'card-header' }, el('h5', { class: 'mb-0' }, consulta.evento || 'Texto sem evento')),
        corpo);
}

function itemResultado(resultado, consultas) {
    const percentual = resultado.similaridade * 100;
    const texto = resultado.origem === 'base' ? indice.deliberacoes[resultado.indice] : consultas[resultado.indice];
    const titulo = resultado.origem === 'base'
        ? `${texto.evento} · #${texto.id}`
        : `${texto.evento || 'Texto sem evento'} (texto desta análise)`;

    return el('li', { class: 'list-group-item d-flex' },
        el('div', { class: 'ms-2 flex-grow-1' },
            el('div', { class: 'd-flex justify-content-between gap-2' },
                el('strong', {}, titulo),
                el('span', { class: 'badge text-bg-dark align-self-start' }, `${percentual.toFixed(1)}%`)),
            el('div', {
                class: 'progress progress-similaridade my-2', role: 'progressbar',
                'aria-label': 'Similaridade', 'aria-valuenow': Math.round(percentual), 'aria-valuemin': 0, 'aria-valuemax': 100,
            }, el('div', { class: 'progress-bar bg-dark', style: `width: ${percentual}%` })),
            el('details', {},
                el('summary', {}, truncar(texto.descricao, 200)),
                el('p', { class: 'texto-longo mt-2 mb-0' }, texto.descricao))));
}
