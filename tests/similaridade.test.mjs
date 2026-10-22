// Compara site/js/similaridade.js com a referência do scikit-learn.
// Uso: python tests/gerar_referencia.py && node --test tests/similaridade.test.mjs

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { criarIndice, buscar, tokenizar, extrairAno } from '../site/js/similaridade.js';

const lerJson = caminho => JSON.parse(readFileSync(new URL(caminho, import.meta.url), 'utf-8'));
const deliberacoes = lerJson('../site/data/deliberacoes.json');
const stopwords = lerJson('../site/data/stopwords-pt.json');
const referencia = lerJson('./referencia.json');
const indice = criarIndice(deliberacoes, stopwords);

const TOLERANCIA = 1e-9;

test('tokenizar remove stopwords, pontuação e palavras de 1 caractere', () => {
    assert.deepEqual(
        tokenizar('Que o PET, e a CENAPET, façam 2 reuniões em 2024!', new Set(stopwords)),
        ['pet', 'cenapet', 'façam', 'reuniões', '2024'],
    );
});

test('extrairAno', () => {
    assert.equal(extrairAno('GDT 1 - ENAPET 2018'), 2018);
    assert.equal(extrairAno('InterPET 2019.1'), 2019);
    assert.equal(extrairAno('Sem ano'), null);
});

test('resultados iguais aos do scikit-learn', () => {
    for (const [n, caso] of referencia.entries()) {
        const obtido = buscar(caso.consultas, indice);
        assert.equal(obtido.length, caso.resultados.length, `caso ${n}`);

        caso.resultados.forEach((esperados, i) => {
            const achados = obtido[i];
            assert.equal(achados.length, esperados.length, `caso ${n}, consulta ${i}: quantidade`);

            esperados.forEach((esperado, k) => {
                const achado = achados[k];
                const msg = `caso ${n}, consulta ${i}, posição ${k}`;
                assert.ok(Math.abs(achado.similaridade - esperado.similaridade) < TOLERANCIA,
                    `${msg}: ${achado.similaridade} != ${esperado.similaridade}`);
                // Em empates a ordem pode variar por arredondamento; só exige o mesmo texto fora deles.
                const empatado = esperados.some((e, x) => x !== k
                    && Math.abs(e.similaridade - esperado.similaridade) < TOLERANCIA);
                if (!empatado) {
                    assert.deepEqual([achado.origem, achado.indice], [esperado.origem, esperado.indice], msg);
                }
            });
        });
    }
});

test('consulta só com stopwords não retorna nada (não repete o próprio texto)', () => {
    const [resultado] = buscar([{ evento: 'X 2020', descricao: 'que de a o e' }], indice);
    assert.deepEqual(resultado, []);
});

test('textos do mesmo ano da consulta são ignorados', () => {
    const [resultado] = buscar([{ evento: 'ENAPET 2020', descricao: deliberacoes[0].descricao }], indice);
    assert.ok(resultado.length > 0);
    for (const r of resultado) assert.notEqual(deliberacoes[r.indice].ano, 2020);
});
