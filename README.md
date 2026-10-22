# PETCIDE

**PET + Collaborative Intelligent DEliberation**: consulta e análise de similaridade das
deliberações dos encontros PET (ENAPET, ENEPET, InterPET).

Site: https://pet-cet.github.io/PETCIDE/

O site é estático (GitHub Pages): a base de deliberações é um arquivo do repositório e a
análise de similaridade roda inteira no navegador. Nenhum texto digitado sai da máquina.

## Estrutura

| Caminho | O que é |
|---|---|
| `data/deliberacoes.csv` | Base de deliberações (`id,evento,ano,descricao`). **É aqui que os dados são editados.** |
| `scripts/gerar_dados.py` | Valida o CSV e gera `site/data/deliberacoes.json` |
| `scripts/adicionar_deliberacao.py` | Converte uma issue "Sugerir deliberação" em linhas do CSV |
| `site/` | O site publicado (HTML, CSS, JS) |
| `site/js/similaridade.js` | TF-IDF + cosseno com stopwords em português |
| `tests/` | Testes que comparam o JS com o scikit-learn |
| `.github/workflows/pages.yml` | Valida e testa em PRs; publica no Pages a cada push na `main` |
| `.github/workflows/deliberacao-aprovada.yml` | Transforma issues aprovadas em PRs |
| `legacy/` | Versão antiga em Django (API + login), mantida só como referência |

## Como atualizar a base

Nenhuma deliberação entra na base sem a aprovação de um curador (quem tem permissão de escrita
no repositório e está no [`CODEOWNERS`](.github/CODEOWNERS)).

### Sugerir pelo formulário (sem precisar de git)

1. No site, em **Deliberações → Sugerir deliberação** (ou em *Issues → New issue → Sugerir
   deliberação*), preencha encontro, ano, grupo e os textos. Várias deliberações do mesmo grupo
   vão separadas por uma linha só com `---`.
2. Um curador revisa a issue e coloca a label **`aprovada`**.
3. O Action [`deliberacao-aprovada.yml`](.github/workflows/deliberacao-aprovada.yml) valida os
   textos e abre um PR que acrescenta as linhas ao CSV. Se houver problema (ano inválido, texto
   que já existe na base…), ele comenta na issue e retira a label.
4. O curador faz o merge do PR; o site é publicado e a issue fecha sozinha.

Se a issue for editada depois de aprovada, remova e recoloque a label para atualizar o PR.

### Editar o CSV direto (curadores, importações grandes)

1. Edite `data/deliberacoes.csv` (cabeçalho `id,evento,ano,descricao`; textos com vírgula ou
   quebra de linha entre aspas).
2. Rode `python scripts/gerar_dados.py` para conferir. Ele aponta ids repetidos, anos inválidos,
   ano que não bate com o nome do evento, descrições vazias ou duplicadas.
3. Abra um PR. O Action roda a mesma validação e os testes; depois do merge o site é publicado.

### Configuração do repositório (uma vez, por um admin)

- **Settings → Pages → Source:** GitHub Actions.
- **Settings → Actions → General → Workflow permissions:** marcar *Allow GitHub Actions to
  create and approve pull requests* (se a organização bloquear, liberar também nas configurações
  da organização).
- **Issues → Labels:** criar `nova-deliberacao` e `aprovada`.
- **Settings → Branches → regra para `main`:** exigir PR, *Require review from Code Owners* e o
  status check `verificar`; bloquear push direto.

## Rodar localmente

Precisa de Python 3 e, para os testes, Node 20+ e scikit-learn.

```bash
python scripts/gerar_dados.py
python -m http.server -d site 8000      # abra http://localhost:8000
```

Abrir os HTML direto pelo arquivo (`file://`) não funciona: o navegador bloqueia o carregamento
dos módulos JS e do JSON.

Testes:

```bash
pip install scikit-learn
python tests/gerar_referencia.py
node --test tests/similaridade.test.mjs
python -m unittest discover tests
```

## Como funciona a similaridade

1. Cada texto é tokenizado: minúsculas, palavras com letras/dígitos de 2+ caracteres, sem as
   stopwords em português do NLTK (`site/data/stopwords-pt.json`).
2. Os textos viram vetores TF-IDF com os mesmos padrões do `TfidfVectorizer` do scikit-learn
   (`smooth_idf`, norma L2). Vocabulário e IDF vêm só da base.
3. Cada texto digitado é comparado por cosseno com a base e com os demais textos digitados,
   ignorando os do mesmo ano (o ano é tirado do nome do evento informado). São mostrados os
   5 mais parecidos com similaridade acima de zero.

Diferenças em relação à versão Django (`legacy/`): stopwords em português; o filtro de ano usa
a coluna `ano` da base (antes procurava o ano só no nome do evento); textos sem nenhuma
similaridade não aparecem mais como resultado; os textos digitados não alteram o IDF.

## Origem e limitações dos dados

A base veio de `dados.csv` do repositório
[nlp_research](https://github.com/Gabrielgermanoo/nlp_research), coletada de
http://pet.ufal.br/deliberacoes/. Na importação foram removidas as colunas `tematicas` e
`responsaveis` (vazias), 2 descrições duplicadas (ids 235 e 333), padronizados `GDT3` → `GDT 3`
e "Evassão" → "Evasão", e criada a coluna `ano` a partir do nome do evento.

Limitações conhecidas:

- Cobre só 2018, 2019, 2020 e 2022.
- Alguns nomes de evento estão truncados em 50 caracteres na fonte.

## Licença

Ver [LICENSE](LICENSE).
