import { carregarDeliberacoes, el, semAcento, truncar, mostrarErro } from './comum.js';

const POR_PAGINA = 10;
const MAX_BOTOES_PAGINA = 5;

let todas = [];
let filtradas = [];
let paginaAtual = 1;

document.addEventListener('DOMContentLoaded', async () => {
    try {
        todas = await carregarDeliberacoes();
    } catch (erro) {
        console.error(erro);
        mostrarErro(document.querySelector('#tabelaDeliberacoes').parentElement,
            'Não foi possível carregar as deliberações. Tente recarregar a página.');
        return;
    }

    const selectAno = document.getElementById('ano');
    for (const ano of [...new Set(todas.map(d => d.ano))].sort()) {
        selectAno.append(el('option', { value: ano }, String(ano)));
    }

    document.getElementById('filtroForm').addEventListener('submit', e => {
        e.preventDefault();
        aplicarFiltros();
    });
    selectAno.addEventListener('change', aplicarFiltros);

    aplicarFiltros();
});

function aplicarFiltros() {
    const ano = document.getElementById('ano').value;
    const evento = semAcento(document.getElementById('evento').value.trim());
    const busca = semAcento(document.getElementById('busca').value.trim());

    filtradas = todas.filter(d =>
        (!ano || d.ano === Number(ano))
        && (!evento || semAcento(d.evento).includes(evento))
        && (!busca || semAcento(d.descricao).includes(busca)));

    paginaAtual = 1;
    renderizar();
}

function renderizar() {
    const totalPaginas = Math.max(1, Math.ceil(filtradas.length / POR_PAGINA));
    const inicio = (paginaAtual - 1) * POR_PAGINA;
    const pagina = filtradas.slice(inicio, inicio + POR_PAGINA);

    document.getElementById('contagem').textContent = filtradas.length === todas.length
        ? `${todas.length} deliberações`
        : `${filtradas.length} de ${todas.length} deliberações`;

    const tbody = document.querySelector('#tabelaDeliberacoes tbody');
    if (pagina.length === 0) {
        tbody.replaceChildren(el('tr', {}, el('td', { colspan: 5, class: 'text-center' }, 'Nenhuma deliberação encontrada')));
    } else {
        tbody.replaceChildren(...pagina.map(d => el('tr', {},
            el('td', { class: 'd-none d-md-table-cell' }, String(d.id)),
            el('td', {}, d.evento),
            el('td', {}, String(d.ano)),
            el('td', {}, truncar(d.descricao, 100)),
            el('td', {}, el('button', { class: 'btn btn-sm btn-dark', type: 'button', onclick: () => abrirDetalhes(d) }, 'Ver')),
        )));
    }

    renderizarPaginacao(totalPaginas);
}

function renderizarPaginacao(totalPaginas) {
    const itemPagina = (rotulo, destino, { ativo = false, desabilitado = false } = {}) => el('li',
        { class: `page-item${ativo ? ' active' : ''}${desabilitado ? ' disabled' : ''}` },
        el('button', {
            class: 'page-link', type: 'button', 'aria-current': ativo ? 'page' : null,
            onclick: () => { paginaAtual = destino; renderizar(); },
        }, rotulo));
    const reticencias = () => el('li', { class: 'page-item disabled' }, el('span', { class: 'page-link' }, '…'));

    let inicio = Math.max(1, paginaAtual - Math.floor(MAX_BOTOES_PAGINA / 2));
    const fim = Math.min(totalPaginas, inicio + MAX_BOTOES_PAGINA - 1);
    inicio = Math.max(1, fim - MAX_BOTOES_PAGINA + 1);

    const itens = [itemPagina('Anterior', paginaAtual - 1, { desabilitado: paginaAtual === 1 })];
    if (inicio > 1) {
        itens.push(itemPagina('1', 1));
        if (inicio > 2) itens.push(reticencias());
    }
    for (let i = inicio; i <= fim; i++) itens.push(itemPagina(String(i), i, { ativo: i === paginaAtual }));
    if (fim < totalPaginas) {
        if (fim < totalPaginas - 1) itens.push(reticencias());
        itens.push(itemPagina(String(totalPaginas), totalPaginas));
    }
    itens.push(itemPagina('Próximo', paginaAtual + 1, { desabilitado: paginaAtual === totalPaginas }));

    document.getElementById('paginacao').replaceChildren(...itens);
}

function abrirDetalhes(d) {
    document.getElementById('eventoModalLabel').textContent = d.evento;
    document.getElementById('eventoModalInfo').textContent = `Deliberação #${d.id} · ${d.ano}`;
    document.getElementById('eventoModalDescricao').textContent = d.descricao;
    document.getElementById('eventoModalComparar').href = `similaridade.html?id=${d.id}`;
    bootstrap.Modal.getOrCreateInstance(document.getElementById('eventoModal')).show();
}
