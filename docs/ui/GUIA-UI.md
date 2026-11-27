# Guia de UI do SIGE Murilo's

> Resumo fiel do guia publicado em <https://claude.ai/artifact/WVJ8odqMXh6mnU9r1mSdgj>
> (v1 · 27/11/2026). Os blocos de código foram copiados do guia sem alteração.
> Protótipo aprovado pelo cliente: <https://claude.ai/artifact/7bhqKhPUeVBjbRjwX746qy>
> (SIGE Murilos — Temas e Dashboard).

Como levar a interface aprovada pelo cliente (temas **Cantina** e **Forno a lenha**)
para o projeto Django, tela por tela, sem mexer nas regras de negócio que já estão testadas.

- **Base analisada pelo guia:** branch `main`, commit `447b1ad` (UI do commit `1deb706`).
- **Stack:** Python 3.14 · Django 6.0.10 · templates + Bootstrap 5.3.3 · SQLite.

Sumário: [0 Instruções](#0-instruções-para-o-claude-code) ·
[1 Diagnóstico](#1-diagnóstico-hoje--protótipo-aprovado) ·
[2 Fundamentos](#2-fundamentos-do-tema) · [3 Componentes](#3-componentes) ·
[4 Layout](#4-layout-base) · [5 Mapa](#5-mapa-de-telas-protótipo--projeto) ·
[6 Telas](#6-especificação-de-cada-tela) · [7 Estados](#7-estados-e-padrões-de-interação) ·
[8 Plano](#8-plano-de-implementação) · [9 Checklist](#9-checklist-de-revisão-de-cada-tela) ·
[Adaptações ao repositório](#adaptações-ao-repositório)

---

## 0. Instruções para o Claude Code

Este documento é a fonte de verdade da UI. Ordem de prioridade: **(1)** o pedido do Luiz
na conversa, **(2)** este guia, **(3)** o protótipo aprovado, **(4)** o que já existe em
`templates/` e `static/`.

**Pode**

- Reescrever `templates/**`, `static/css/**`, `static/js/app.js`.
- Criar `static/css/tokens.css`, `bootstrap-sige.css`, `sige.css`, `templates/includes/ui.html` (partials).
- Baixar e servir localmente Bootstrap 5.3.3, Phosphor Icons 2.1.1 e o logo em `static/vendor/` e `static/img/`.
- Adicionar `attrs={"class": ...}` em widgets de `forms.py` e criar *templatetags* só de apresentação (ex.: formatar R$/kg).
- Adicionar dados ao contexto de uma view **apenas para exibição** (ex.: contagem de críticos), sem mudar cálculos.

**Não pode**

- Alterar models, migrations, cálculos (custo, margem, baixa, sugestões), validações de forms, URLs ou nomes de rotas.
- Alterar ou apagar testes. Todos os testes devem continuar passando (110 na época do guia).
- Mudar cores, fontes ou formas do tema (aprovado pelo cliente).
- Renomear entidades no código (Ingrediente, Pizza, RegistroVenda). Só os *rótulos* da tela seguem este guia.
- Usar estilo inline novo, CDN no lugar de arquivo local (fora as fontes do Google), ou JavaScript de framework.

**Rotina de cada fase**

1. Criar a branch a partir da `dev`: `git switch dev && git pull && git switch -c style/ui-N-nome`.
2. Implementar só o escopo da fase (seção [8](#8-plano-de-implementação)).
3. Rodar `python manage.py check && python manage.py test && ruff check .` — tudo verde.
4. Abrir cada tela alterada nos dois temas e em 390 px de largura (celular).
5. Commit no padrão do repo, em português: `style(ui): aplica tema Cantina ao layout base`.
6. Pull request para a `dev` com prints das telas nos dois temas.

## 1. Diagnóstico: hoje × protótipo aprovado

| Aspecto | Como está hoje (repo) | Como deve ficar |
|---|---|---|
| Cor de marca | `--brand: #8f1d2c`, fundo cinza `#f5f5f7` | Vinho `#7A1B16` no menu, tomate `#CF3F22` nas ações, fundo creme `#F6EEE4` |
| Temas | Só claro | Cantina (claro, padrão) e Forno a lenha (escuro), troca no topo |
| Fontes | Fonte do sistema (SF/Segoe) | Bricolage Grotesque (títulos e números) + Figtree (texto) |
| Forma | Cantos de 12–22px, sombra difusa, topo translúcido | Pílulas (999px) em botões, campos e chips; cards 24px com sombra sólida `0 4px 0` |
| Menu | Lateral claro, botão "Nova venda", grupos Visão geral / Operação / Análises | Lateral vinho com faixa xadrez e logo, grupos Hoje / Estoque / Cozinha / Gestão, item ativo em pílula creme |
| Ícones | SVG desenhados à mão no menu | Phosphor 2.1.1 (regular e fill), servidos localmente |
| Bootstrap | 5.3.3 via CDN; grid e componentes nos templates | Mantido na fase 1 (local, sem CDN) e tematizado por variáveis; trocado aos poucos pelos componentes deste guia |
| Situação de estoque | Badges Bootstrap "Normal / Baixo / Negativo" | Selos "OK / Abaixo do mínimo / Saldo negativo" com bolinha |
| Mensagens | `.alert` no topo do conteúdo | Avisos flutuantes no canto inferior direito (verde, vermelho, dourado) |
| Custo do ingrediente | `R$ {{ custo_unitario\|floatformat:2 }}` mostra R$ 0,04 para R$ 0,042/g | Mostrar por unidade de compra: **R$ 42,00/kg**, **R$ 9,80/L**, **R$ 1,85/un** (filtro de template) |

> **Manter:** link "Ir para o conteúdo", menu em gaveta no celular (`app.js`), abas acessíveis
> do painel, estados vazios, textos claros e o uso de `aria-*`.

## 2. Fundamentos do tema

### Paleta

| Token | Cor | Uso |
|---|---|---|
| `chrome` | `#7A1B16` | menu, login |
| `tomato` | `#CF3F22` | ação principal, alerta |
| `gold` | `#CC9532` | dinheiro, destaque, Classe A |
| `basil` | `#3F7E4A` | OK, sucesso |
| `bg` | `#F6EEE4` | fundo Cantina |
| `surface` | `#FFFAF2` | cards |
| `ink` | `#2B1912` | texto |
| `bg` Forno | `#1E1814` | fundo escuro |

Significado fixo das cores, nos dois temas: **tomate** = ação principal ou problema;
**manjericão** = OK; **dourado** = dinheiro e atenção moderada; **vinho** = moldura do sistema.
Cor nunca vem sozinha: sempre com texto ("Abaixo do mínimo"), ícone ou ambos.

### Tipografia e medidas

| Uso | Fonte | Tamanho / peso |
|---|---|---|
| Título da página | Bricolage Grotesque | 38px / 700, letter-spacing −0,03em |
| Título de card | Bricolage Grotesque | 22–26px / 700 |
| Número de KPI | Bricolage Grotesque | 30–32px / 700, tabular |
| Texto | Figtree | 14px / 400–700 |
| Rótulo de seção e cabeçalho de tabela | Figtree | 11,5–12px / 700, caixa alta, +0,08em |
| Raios | — | Cards 24px · campos, botões e chips 999px · blocos internos 16–18px · diálogos 28px |
| Sombras | — | Card `0 4px 0 var(--edge), 0 12px 24px var(--shadow)` · botão primário `0 3px 0 var(--edge)` |
| Larguras | — | Menu 244px · topo 68px · conteúdo até 1400px · painel lateral 300–360px · gutter 32px (16px no celular) |

### tokens.css

```css
/* static/css/tokens.css — tema aprovado pelo cliente (NÃO alterar cores sem aprovação)
   Uso: <html data-tema="cantina" data-bs-theme="light"> ou data-tema="forno" data-bs-theme="dark" */
:root,
[data-tema="cantina"] {
  --bg: #F6EEE4;  --surface: #FFFAF2;  --surface2: #F8EDE0;
  --ink: #2B1912; --ink2: #6E5144;
  --line: #EAD6C3; --edge: #E0C4A8;   --shadow: rgba(110, 40, 20, .07);
  --tomato: #CF3F22; --onTomato: #FFF8F0; --tomatoInk: #B33519; --tomatoSoft: #FBE1D7;
  --basil: #3F7E4A;  --basilSoft: #E2EEDB;
  --gold: #CC9532;   --goldInk: #7E560E; --goldSoft: #F7E8CB;
  --barB: #C2A08C;   --barC: #E9D5C4;
  --chrome: #7A1B16; --chromeInk: #FCEBD8; --chromeInk2: #E6BBA5;
  --chromeActive: #FCEBD8; --chromeActiveInk: #7A1B16;
  --chromeLine: #8E2A22; --chromeBadge: #92302A;
  --pattern: repeating-conic-gradient(#7A1B16 0 25%, #F3E2CC 0 50%) 0 0 / 20px 20px;
  color-scheme: light;
}
[data-tema="forno"] {
  --bg: #1E1814;  --surface: #2B231E;  --surface2: #362C25;
  --ink: #F5ECDF; --ink2: #C2B19E;
  --line: #45382E; --edge: #110C09;   --shadow: rgba(0, 0, 0, .35);
  --tomato: #CC3F28; --onTomato: #FFF6EE; --tomatoInk: #F2836B; --tomatoSoft: rgba(229, 83, 58, .15);
  --basil: #80C48E;  --basilSoft: rgba(128, 196, 142, .14);
  --gold: #E2AE4A;   --goldInk: #EDC274; --goldSoft: rgba(226, 174, 74, .14);
  --barB: #9A8673;   --barC: #54463B;
  --chrome: #15100D; --chromeInk: #F5ECDF; --chromeInk2: #AE9A84;
  --chromeActive: #2E251F; --chromeActiveInk: #F5ECDF;
  --chromeLine: #2A211B; --chromeBadge: #2E251F;
  --pattern: none;
  color-scheme: dark;
}
:root {
  --fonte-titulo: "Bricolage Grotesque", system-ui, sans-serif;
  --fonte-texto: "Figtree", system-ui, sans-serif;
  --raio-card: 24px;   --raio-campo: 999px;  --raio-interno: 16px;
  --sombra-card: 0 4px 0 var(--edge), 0 12px 24px var(--shadow);
  --sombra-botao: 0 3px 0 var(--edge);
  --menu-largura: 244px;  --topo-altura: 68px;  --conteudo-max: 1400px;
}
```

### Tema e troca de tema

O tema vale para o navegador do usuário (localStorage). O atributo `data-bs-theme`
acompanha para que os componentes do Bootstrap também escureçam no Forno.

```html
<!-- No <head> do base.html, ANTES dos CSS: aplica o tema salvo sem "piscar" -->
<script>
  (function () {
    try { var t = localStorage.getItem("sige-tema"); } catch (e) {}
    t = (t === "forno" || t === "cantina") ? t : "cantina";
    document.documentElement.dataset.tema = t;
    document.documentElement.dataset.bsTheme = t === "forno" ? "dark" : "light";
  })();
</script>

// static/js/app.js — botão de troca de tema (adicionar ao IIFE existente)
document.addEventListener("click", (e) => {
  const bt = e.target.closest("[data-tema-escolher]");
  if (!bt) return;
  const tema = bt.dataset.temaEscolher;                    // "forno" | "cantina"
  document.documentElement.dataset.tema = tema;
  document.documentElement.dataset.bsTheme = tema === "forno" ? "dark" : "light";
  try { localStorage.setItem("sige-tema", tema); } catch (err) {}
  document.querySelectorAll("[data-tema-escolher]").forEach((b) => b.setAttribute("aria-pressed", String(b === bt)));
});
```

### Bootstrap tematizado (fase de transição)

Os templates atuais usam `row/col`, `.btn`, `.card`, `.table`, `.form-control`, `.badge`,
`.alert` e `.pagination`. Esta folha faz todos seguirem o tema sem reescrever os templates
de uma vez:

```css
/* static/css/bootstrap-sige.css — carrega DEPOIS do bootstrap.min.css.
   Faz os componentes do Bootstrap que já estão nos templates (row/col, .btn,
   .card, .table, .form-control, .badge, .alert, .pagination) seguirem o tema,
   sem reescrever todos os templates de uma vez. */
:root, [data-tema] {
  --bs-body-font-family: var(--fonte-texto);
  --bs-body-font-size: .875rem;
  --bs-body-bg: var(--bg);
  --bs-body-color: var(--ink);
  --bs-secondary-color: var(--ink2);
  --bs-emphasis-color: var(--ink);
  --bs-border-color: var(--line);
  --bs-link-color: var(--tomatoInk);
  --bs-link-hover-color: var(--ink);
  --bs-link-color-rgb: 179, 53, 25;
  --bs-heading-color: var(--ink);
  --bs-border-radius: var(--raio-interno);
  --bs-focus-ring-color: color-mix(in srgb, var(--gold) 45%, transparent);
}
h1, h2, h3, h4, .h1, .h2, .h3, .h4 { font-family: var(--fonte-titulo); font-weight: 700; letter-spacing: -.025em; }
.card {
  --bs-card-bg: var(--surface); --bs-card-color: var(--ink);
  --bs-card-border-width: 0; --bs-card-border-radius: var(--raio-card);
  box-shadow: var(--sombra-card);
}
.table {
  --bs-table-bg: transparent; --bs-table-color: var(--ink);
  --bs-table-striped-bg: var(--surface2); --bs-table-striped-color: var(--ink);
  --bs-table-hover-bg: var(--surface2); --bs-table-border-color: var(--line);
}
.table > thead th { font-size: .72rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--ink2); border-bottom-width: 1px; }
.btn { --bs-btn-border-radius: var(--raio-campo); --bs-btn-font-weight: 700; --bs-btn-padding-x: 1.25rem; --bs-btn-padding-y: .6rem; }
.btn-brand, .btn-primary {
  --bs-btn-bg: var(--tomato); --bs-btn-color: var(--onTomato); --bs-btn-border-color: transparent;
  --bs-btn-hover-bg: var(--tomatoInk); --bs-btn-hover-color: var(--onTomato);
  --bs-btn-active-bg: var(--tomatoInk); --bs-btn-active-color: var(--onTomato);
  box-shadow: var(--sombra-botao);
}
.btn-outline-secondary {
  --bs-btn-color: var(--ink); --bs-btn-border-color: var(--line); --bs-btn-bg: var(--surface);
  --bs-btn-hover-bg: var(--surface2); --bs-btn-hover-color: var(--ink); --bs-btn-hover-border-color: var(--line);
}
.form-control, .form-select {
  min-height: 44px; border-radius: var(--raio-campo); border: 1.5px solid var(--line);
  background-color: transparent; color: var(--ink); padding-inline: 1.1rem;
}
.form-control:focus, .form-select:focus { border-color: var(--ink); box-shadow: none; }
.badge { border-radius: 999px; font-weight: 700; padding: .35em .8em; }
.text-bg-success { background: var(--basilSoft) !important; color: var(--basil) !important; }
.text-bg-warning { background: var(--goldSoft) !important;  color: var(--goldInk) !important; }
.text-bg-danger  { background: var(--tomato) !important;    color: var(--onTomato) !important; }
.text-bg-info    { background: var(--surface2) !important;  color: var(--ink2) !important; }
.text-danger { color: var(--tomatoInk) !important; }
.text-muted  { color: var(--ink2) !important; }
.alert { border-radius: 18px; border-width: 2px; }
.alert-danger  { background: var(--tomatoSoft); border-color: var(--tomato); color: var(--ink); }
.alert-warning { background: var(--goldSoft);   border-color: var(--gold);   color: var(--ink); }
.alert-success { background: var(--basilSoft);  border-color: var(--basil);  color: var(--ink); }
.alert-info    { background: var(--surface2);   border-color: var(--line);   color: var(--ink); }
.pagination { --bs-pagination-border-radius: 999px; --bs-pagination-color: var(--ink);
  --bs-pagination-bg: var(--surface); --bs-pagination-border-color: var(--line);
  --bs-pagination-active-bg: var(--ink); --bs-pagination-active-border-color: var(--ink); --bs-pagination-active-color: var(--bg); gap: 4px; }
.page-link { border-radius: 999px !important; }
```

## 3. Componentes

O guia traz uma prévia ao vivo dos componentes nos dois temas, lado a lado: cabeçalho de
página, chips, faixa de alerta, KPIs (com `cartao--ouro`), tabela com selos, controle
segmentado, selo de margem, passo-a-passo, campo em pílula, interruptor, botões escuro e de
perigo, barra de proporção e aviso flutuante.

### sige.css

```css
/* static/css/sige.css — componentes do protótipo (classes em português, BEM leve) */
body { margin: 0; background: var(--bg); color: var(--ink); font: 14px/1.45 var(--fonte-texto); }
a { color: var(--tomatoInk); }
:focus-visible { outline: 3px solid var(--gold); outline-offset: 2px; }
.titulo { font: 700 38px/1.02 var(--fonte-titulo); letter-spacing: -.03em; margin: 0; text-wrap: balance; }
.subtitulo { font-size: 14px; color: var(--ink2); margin: 0 0 6px; }
.rotulo { font-size: 12px; font-weight: 700; letter-spacing: .09em; text-transform: uppercase; color: var(--ink2); }
.num { font-family: var(--fonte-titulo); font-weight: 700; font-variant-numeric: tabular-nums; }

/* Cabeçalho de página: subtítulo + título à esquerda, ações à direita */
.cabecalho { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px 20px; flex-wrap: wrap; }
.cabecalho__acoes { display: flex; gap: 8px; flex-wrap: wrap; }

/* Botões — sempre <button> ou <a href> reais */
.botao { display: inline-flex; align-items: center; justify-content: center; gap: 8px; min-height: 44px; padding: 0 20px;
  border-radius: 999px; border: 1.5px solid var(--line); background: var(--surface); color: var(--ink);
  font: 700 14px/1 var(--fonte-texto); text-decoration: none; cursor: pointer; white-space: nowrap; }
.botao:hover { background: var(--surface2); color: var(--ink); }
.botao--primario { background: var(--tomato); color: var(--onTomato); border-color: transparent; box-shadow: var(--sombra-botao); font-size: 15px; }
.botao--primario:hover { background: var(--tomatoInk); color: var(--onTomato); }
.botao--escuro { background: var(--ink); color: var(--bg); border-color: transparent; }
.botao--escuro:hover { background: var(--ink); color: var(--bg); opacity: .9; }
.botao--perigo { background: transparent; border-color: var(--tomato); color: var(--tomatoInk); }
.botao--pequeno { min-height: 36px; padding: 0 14px; font-size: 13px; }
.botao--icone { width: 40px; min-height: 40px; padding: 0; }
.botao[disabled], .botao[aria-disabled="true"] { opacity: .45; cursor: not-allowed; }

/* Chips de filtro e controle segmentado */
.chips { display: flex; gap: 6px; flex-wrap: wrap; }
.chip { display: inline-flex; align-items: center; gap: 7px; padding: 8px 16px; border-radius: 999px; border: 1px solid var(--line);
  background: var(--surface); color: var(--ink); font-weight: 700; text-decoration: none; cursor: pointer; }
.chip[aria-pressed="true"], .chip[aria-current="true"], .chip--ativo { background: var(--ink); color: var(--bg); border-color: var(--ink); }
.chip__qtd { font-family: var(--fonte-titulo); opacity: .7; }
.segmentado { display: inline-flex; gap: 3px; padding: 3px; border-radius: 999px; background: var(--surface2); }
.segmentado > * { border: 0; background: transparent; padding: 7px 16px; border-radius: 999px; font-weight: 700; font-size: 13px; color: var(--ink2); cursor: pointer; text-decoration: none; }
.segmentado > [aria-selected="true"], .segmentado > [aria-pressed="true"] { background: var(--ink); color: var(--bg); }

/* Cards */
.cartao { background: var(--surface); border-radius: var(--raio-card); padding: 20px 22px; box-shadow: var(--sombra-card); }
.cartao--ouro { border: 2px solid var(--gold); }
.cartao--alerta { background: var(--tomatoSoft); border: 2px solid var(--tomato); box-shadow: none; }
.cartao--tabela { padding: 10px 12px; overflow-x: auto; }

/* Números-chave (KPIs) */
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }
.kpi__rotulo { color: var(--ink2); font-weight: 600; display: flex; gap: 7px; align-items: center; }
.kpi__valor { display: block; font: 700 32px/1.05 var(--fonte-titulo); letter-spacing: -.03em; font-variant-numeric: tabular-nums; margin-top: 4px; }
.kpi__nota { font-size: 12.5px; color: var(--ink2); }
.kpi__valor--negativo { color: var(--tomatoInk); }

/* Faixa de aviso no topo da página */
.faixa { display: flex; align-items: center; gap: 12px; padding: 14px 18px; border-radius: 22px; }
.faixa--alerta { background: var(--tomatoSoft); border: 2px solid var(--tomato); }
.faixa--ouro { background: var(--surface); border: 2px solid var(--gold); box-shadow: var(--sombra-botao); }
.faixa--info { background: var(--surface2); }

/* Tabela */
.tabela { width: 100%; border-collapse: separate; border-spacing: 0 2px; min-width: 620px; }
.tabela th { text-align: left; padding: 10px 12px; font-size: 11.5px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--ink2); }
.tabela td { padding: 0 12px; height: 52px; }
.tabela tbody tr:hover td { background: var(--surface2); }
.tabela td:first-child { border-radius: 16px 0 0 16px; }
.tabela td:last-child { border-radius: 0 16px 16px 0; }
.tabela .direita { text-align: right; }
.tabela__sub { display: block; font-size: 12px; color: var(--ink2); }
.tabela tr.linha--alerta td { background: var(--tomatoSoft); }

/* Selos de situação (sempre com texto, nunca só cor) */
.selo { display: inline-flex; align-items: center; gap: 6px; padding: 4px 11px; border-radius: 999px; font-size: 12.5px; font-weight: 700; white-space: nowrap; background: var(--surface2); color: var(--ink2); }
.selo::before { content: ""; width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
.selo--ok { background: var(--basilSoft); color: var(--basil); }
.selo--ouro { background: var(--goldSoft); color: var(--goldInk); }
.selo--alerta { background: var(--tomatoSoft); color: var(--tomatoInk); }
.selo--negativo { background: var(--tomato); color: var(--onTomato); }
.classe { display: inline-grid; place-items: center; width: 24px; height: 24px; border-radius: 50%; font: 700 12px/1 var(--fonte-titulo); background: var(--gold); color: #2A1D15; }

/* Campos em pílula — estiliza também inputs gerados pelo Django sem classe */
.campo { display: flex; flex-direction: column; gap: 5px; font-size: 12.5px; font-weight: 700; color: var(--ink2); }
.campo input:not([type="checkbox"]):not([type="radio"]):not([type="file"]), .campo select,
.formulario input:not([type="checkbox"]):not([type="radio"]):not([type="file"]), .formulario select {
  min-height: 44px; width: 100%; border-radius: 999px; border: 1.5px solid var(--line); background: transparent;
  color: var(--ink); padding: 0 18px; font: 400 14px var(--fonte-texto); }
.campo input:focus, .campo select:focus, .formulario input:focus, .formulario select:focus { outline: none; border-color: var(--ink); }
.campo textarea, .formulario textarea { border-radius: 20px; border: 1.5px solid var(--line); background: var(--bg); padding: 12px 16px; color: var(--ink); }
.campo .errorlist, .formulario .errorlist { list-style: none; margin: 0; padding: 0 6px; color: var(--tomatoInk); font-weight: 600; }
.campo--prefixo { position: relative; }
.campo__prefixo { position: absolute; left: 18px; bottom: 13px; color: var(--ink2); font-weight: 600; }
.campo--prefixo input { padding-left: 46px !important; }

/* Interruptor (checkbox estilizado; continua sendo <input type="checkbox">) */
.interruptor { display: flex; align-items: center; gap: 12px; padding: 12px 14px; border-radius: 18px; background: var(--surface2); cursor: pointer; }
.interruptor input { appearance: none; width: 42px; height: 24px; border-radius: 999px; background: var(--line); position: relative; flex: none; margin: 0; cursor: pointer; }
.interruptor input::after { content: ""; position: absolute; top: 3px; left: 3px; width: 18px; height: 18px; border-radius: 50%; background: #fff; transition: left .15s; }
.interruptor input:checked { background: var(--basil); }
.interruptor input:checked::after { left: 21px; }
.interruptor__texto { flex: 1; font-size: 13px; }
.interruptor__texto small { display: block; color: var(--ink2); font-size: 12.5px; }

/* Duas colunas: conteúdo + painel lateral (empilha abaixo de 1000px) */
.duas-colunas { display: grid; grid-template-columns: minmax(0, 1fr) minmax(300px, 360px); gap: 16px; align-items: start; }
.painel-lateral { position: sticky; top: calc(var(--topo-altura) + 24px); display: flex; flex-direction: column; gap: 14px; }
@media (max-width: 1000px) { .duas-colunas { grid-template-columns: 1fr; } .painel-lateral { position: static; } }

/* Quantidade com − e + (Comprar para N dias, quantidades vendidas) */
.passo-a-passo { display: inline-flex; align-items: center; gap: 8px; padding: 6px 6px 6px 18px; border-radius: 999px; background: var(--surface); border: 1px solid var(--line); }
.passo-a-passo button { width: 34px; height: 34px; border-radius: 50%; border: 0; background: var(--surface2); color: var(--ink); font-size: 18px; cursor: pointer; }
.passo-a-passo output, .passo-a-passo input { font: 700 20px/1 var(--fonte-titulo); min-width: 64px; text-align: center; border: 0; background: transparent; color: var(--ink); }

/* Barra de proporção (margem, consumo) */
.barra { height: 10px; border-radius: 999px; background: var(--surface2); overflow: hidden; }
.barra > span { display: block; height: 100%; border-radius: 999px; background: var(--ink); }
.barra--ok > span { background: var(--basil); } .barra--ouro > span { background: var(--gold); } .barra--alerta > span { background: var(--tomato); }

/* Avisos flutuantes (mensagens do Django) */
.avisos { position: fixed; right: 28px; bottom: 28px; z-index: 60; display: flex; flex-direction: column; gap: 10px; align-items: flex-end; }
.aviso { display: flex; align-items: center; gap: 12px; max-width: 420px; padding: 14px 16px 14px 18px; border-radius: 22px;
  background: var(--surface); border: 2px solid var(--basil); box-shadow: 0 4px 0 var(--edge), 0 18px 40px var(--shadow); }
.aviso--alerta { border-color: var(--tomato); } .aviso--dinheiro { border-color: var(--gold); } .aviso--info { border-color: var(--line); }
.aviso__fechar { width: 30px; height: 30px; border-radius: 50%; border: 0; background: var(--surface2); color: var(--ink); cursor: pointer; flex: none; }
@media (prefers-reduced-motion: no-preference) { .aviso { animation: aviso-entra .25s ease-out; } }
@keyframes aviso-entra { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }

/* Estado vazio */
.vazio { padding: 28px; border-radius: 18px; border: 1.5px dashed var(--line); text-align: center; color: var(--ink2); }

/* Área de envio de arquivo (planilha) */
.envio { display: flex; align-items: center; gap: 18px; padding: 22px 24px; border-radius: 24px; border: 2px dashed var(--line); background: var(--surface); flex-wrap: wrap; }

/* Cards de pizza (cardápio) */
.grade-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 16px; }
.pizza-card { background: var(--surface); border-radius: 24px; padding: 12px; box-shadow: var(--sombra-card); display: flex; flex-direction: column; gap: 12px; border: 2px solid transparent; }
.pizza-card--pendente { border-color: var(--tomato); }
.pizza-card__foto { height: 132px; border-radius: 18px; background: repeating-linear-gradient(135deg, var(--surface2) 0 10px, var(--bg) 10px 20px); display: grid; place-items: center; color: var(--ink2); font-size: 12px; }
.pizza-card__rodape { display: flex; align-items: center; gap: 8px; padding: 10px 12px; border-radius: 16px; background: var(--surface2); }

/* Diálogo de confirmação (<dialog> nativo) */
.dialogo { border: 0; padding: 26px; width: min(440px, calc(100% - 32px)); border-radius: 28px; background: var(--surface); color: var(--ink); box-shadow: 0 4px 0 var(--edge), 0 30px 60px rgba(0,0,0,.35); }
.dialogo::backdrop { background: rgba(20, 10, 6, .55); }
```

### Componentes como template partials (Django 6.0)

O Django 6.0 tem *template partials* nativos: um arquivo com vários blocos nomeados,
incluídos por `arquivo.html#nome`. Use para KPI, selos e cabeçalho, em vez de repetir HTML.

```django
{# templates/includes/ui.html — componentes reutilizáveis com template partials (Django 6.0) #}
{% partialdef cabecalho %}
<div class="cabecalho">
  <div>
    {% if subtitulo %}<p class="subtitulo">{{ subtitulo }}</p>{% endif %}
    <h1 class="titulo">{{ titulo }}</h1>
  </div>
  {% if acoes %}<div class="cabecalho__acoes">{{ acoes }}</div>{% endif %}
</div>
{% endpartialdef %}

{% partialdef kpi %}
<div class="cartao{% if destaque %} cartao--ouro{% endif %}">
  <div class="kpi__rotulo">{% if icone %}<i class="ph-fill {{ icone }}" style="color:var(--gold)" aria-hidden="true"></i>{% endif %}{{ rotulo }}</div>
  <span class="kpi__valor{% if negativo %} kpi__valor--negativo{% endif %}">{{ valor }}</span>
  {% if nota %}<span class="kpi__nota">{{ nota }}</span>{% endif %}
</div>
{% endpartialdef %}

{% partialdef selo_estoque %}
{% if item.estoque_negativo %}<span class="selo selo--negativo">Saldo negativo</span>
{% elif item.estoque_baixo %}<span class="selo selo--alerta">Abaixo do mínimo</span>
{% else %}<span class="selo selo--ok">OK</span>{% endif %}
{% endpartialdef %}

{% partialdef selo_margem %}
<span class="selo {% if margem >= 60 %}selo--ok{% elif margem >= 45 %}selo--ouro{% else %}selo--alerta{% endif %}">{{ margem|floatformat:0 }}% de margem</span>
{% endpartialdef %}

{# Uso em qualquer template: #}
{% include "includes/ui.html#kpi" with rotulo="Faturamento" valor=fat icone="ph-coins" destaque=True %}
{% include "includes/ui.html#selo_estoque" with item=ingrediente %}
```

### Regras de uso

- **Um único botão primário (tomate) por área.** Os demais são secundários (contorno) ou escuros.
- **Ação destrutiva** (desativar, remover) usa `.botao--perigo` e confirmação em `<dialog>` com o texto do impacto ("O histórico continua guardado").
- **Filtro por categoria/origem** = `.chips`; **alternar visão** (Vendas/Estoque, Compra/Contagem, 3/6 meses) = `.segmentado`.
- **Dinheiro em destaque** = `.cartao--ouro` com ícone `ph-coins`; **problema** = `.faixa--alerta` no topo da página.
- **Números** sempre com `.num` (tabular) e alinhados à direita em tabelas.
- **Ícones** decorativos com `aria-hidden="true"`; botão só com ícone leva `aria-label`.
- **Contraste** mínimo 4,5:1 nos dois temas; foco visível em tudo que é clicável.

## 4. Layout base

```
┌────────────────┬──────────────────────────────────────────────┐
│ ▚▚▚ faixa ▚▚▚  │ Hoje › Painel        [+ Nova venda] [Forno|Cantina]
│ (logo) Murilo's├──────────────────────────────────────────────┤
│ HOJE           │ Visão geral                                  │
│ ● Painel       │ Painel                                       │
│   Vendas       │ [KPI] [KPI ouro] [KPI] [KPI]                 │
│ ESTOQUE        │ [ tabela ................................ ]  │
│   Ingredientes │                                              │
│   Entradas     │                                              │
│   O que comprar 3                                             │
│   Movimentações│                                              │
│ COZINHA        │                                              │
│   Pizzas e fichas                                             │
│   Margens      │                                              │
│   Consumo      │                                              │
└────────────────┴──────────────────────────────────────────────┘
```

- **Menu lateral** (vinho): faixa xadrez de 10px no topo, logo redondo 58px + "Murilo's / Pizzaria & Pastelaria", grupos em caixa alta, item ativo em pílula creme, contador vermelho em "O que comprar" quando há ingredientes críticos, usuário no rodapé com botão Sair.
- **Topo** (dentro do `base.html`): botão de menu no celular, trilha "Grupo › **Tela**" preenchida pelo bloco `trilha` de cada tela, e à direita "Nova venda" e o seletor de tema Forno | Cantina.
- **Página**: cabeçalho (subtítulo pequeno + título 38px + ações), depois faixas de aviso, filtros, conteúdo. Espaço vertical de 20px entre blocos.
- **Celular** (< 992px): o menu vira gaveta (o `app.js` atual já faz isso com `body.nav-open`); tabelas rolam na horizontal dentro do card; o painel lateral desce para baixo do conteúdo.
- **Login** não usa o layout com menu: tela dividida, painel vinho à esquerda e formulário à direita.

### base.html

```django
{% load static %}
<!doctype html>
<html lang="pt-br" data-tema="cantina" data-bs-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#7A1B16">
  <title>{% block title %}SIGE · Murilo's{% endblock %}</title>
  {# script do tema aqui (ver "Tema e troca de tema") #}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400..800&family=Figtree:wght@400..700&display=swap">
  <link rel="stylesheet" href="{% static 'vendor/bootstrap-5.3.3/bootstrap.min.css' %}">
  <link rel="stylesheet" href="{% static 'vendor/phosphor-2.1.1/regular/style.css' %}">
  <link rel="stylesheet" href="{% static 'vendor/phosphor-2.1.1/fill/style.css' %}">
  <link rel="stylesheet" href="{% static 'css/tokens.css' %}">
  <link rel="stylesheet" href="{% static 'css/bootstrap-sige.css' %}">
  <link rel="stylesheet" href="{% static 'css/sige.css' %}">
  <script src="{% static 'js/app.js' %}" defer></script>
</head>
<body>
  <a class="skip-link" href="#conteudo-principal">Ir para o conteúdo</a>
  <div class="{% if user.is_authenticated %}shell{% else %}publico{% endif %}">
    {% if user.is_authenticated %}{% include "includes/sidebar.html" %}{% endif %}
    <div class="conteudo">
      {% if user.is_authenticated %}
      {# Topo fica AQUI (e não num include) para que cada tela preencha o bloco "trilha" #}
      <header class="topo">
        <button class="menu-toggle" type="button" data-menu-toggle aria-label="Abrir menu" aria-controls="menu-principal" aria-expanded="false">
          <span class="menu-toggle-lines" aria-hidden="true"></span>
        </button>
        <div class="topo__trilha">{% block trilha %}{% endblock %}</div>
        <div class="topo__acoes">
          <a class="botao botao--pequeno" href="{% url 'vendas:novo' %}"><i class="ph ph-plus-circle" aria-hidden="true"></i>Nova venda</a>
          <div class="segmentado" role="group" aria-label="Tema">
            <button type="button" data-tema-escolher="forno" aria-pressed="false"><i class="ph ph-moon" aria-hidden="true"></i> Forno</button>
            <button type="button" data-tema-escolher="cantina" aria-pressed="true"><i class="ph ph-sun" aria-hidden="true"></i> Cantina</button>
          </div>
        </div>
      </header>
      {% endif %}
      <main class="{% if user.is_authenticated %}pagina{% endif %}" id="conteudo-principal" tabindex="-1">
        {% block content %}{% endblock %}
      </main>
    </div>
  </div>
  {% include "includes/messages.html" %}
  {% block scripts %}{% endblock %}
</body>
</html>
{# Em cada tela:  {% block trilha %}Estoque › <b>Ingredientes</b>{% endblock %} #}
{# includes/navbar.html deixa de ser usado (o topo está acima). #}
```

### Layout (CSS)

```css
/* Layout: menu lateral vinho + topo + conteúdo (substitui .app-shell/.sidebar/.topbar atuais) */
.shell { display: flex; min-height: 100vh; }
.menu { width: var(--menu-largura); flex: none; background: var(--chrome); color: var(--chromeInk);
  display: flex; flex-direction: column; position: sticky; top: 0; height: 100vh; }
.menu__faixa { height: 10px; flex: none; background: var(--pattern); }
.menu__marca { display: flex; align-items: center; gap: 12px; padding: 18px 14px 16px; color: inherit; text-decoration: none; }
.menu__marca img { width: 58px; height: 58px; border-radius: 50%; box-shadow: 0 4px 14px rgba(0,0,0,.25); }
.menu__nome { font: 700 22px/1 var(--fonte-titulo); letter-spacing: -.025em; }
.menu__nome small { display: block; font: 400 12px var(--fonte-texto); color: var(--chromeInk2); margin-top: 4px; }
.menu nav { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; padding: 4px 14px 10px; scrollbar-width: none; }
.menu__grupo { padding: 0 14px 5px; font-size: 11px; font-weight: 700; letter-spacing: .09em; text-transform: uppercase; color: var(--chromeInk2); }
.menu__item { display: flex; align-items: center; gap: 11px; height: 36px; padding: 0 14px; border-radius: 999px;
  color: var(--chromeInk2); font-weight: 500; text-decoration: none; }
.menu__item:hover { color: var(--chromeInk); }
.menu__item[aria-current="page"] { background: var(--chromeActive); color: var(--chromeActiveInk); font-weight: 700; }
.menu__item i, .menu__item svg { font-size: 18px; width: 18px; height: 18px; }
.menu__contador { margin-left: auto; min-width: 24px; height: 22px; padding: 0 7px; border-radius: 999px; background: var(--chromeBadge);
  font: 700 12px/22px var(--fonte-titulo); text-align: center; }
.menu__contador--alerta { background: var(--tomato); color: var(--onTomato); }
.menu__usuario { margin: 10px 14px 14px; padding: 9px 10px; border-radius: 999px; background: var(--chromeBadge); display: flex; align-items: center; gap: 10px; }
.avatar { width: 34px; height: 34px; border-radius: 50%; background: #E5A93C; color: #3A1A0C; display: grid; place-items: center; font: 700 13px/1 var(--fonte-titulo); flex: none; }
.conteudo { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.topo { position: sticky; top: 0; z-index: 20; display: flex; align-items: center; gap: 12px; min-height: var(--topo-altura);
  padding: 0 32px; border-bottom: 1px solid var(--line); background: var(--bg); flex-wrap: wrap; }
.topo__trilha { font-size: 13.5px; color: var(--ink2); }
.topo__trilha b { color: var(--ink); }
.topo__acoes { margin-left: auto; display: flex; align-items: center; gap: 10px; }
.pagina { padding: 28px 32px 56px; width: 100%; max-width: var(--conteudo-max); display: flex; flex-direction: column; gap: 20px; }
.publico .conteudo { min-height: 100vh; }
.skip-link { position: fixed; z-index: 1100; top: 12px; left: 12px; padding: 10px 16px; border-radius: 999px;
  background: var(--ink); color: var(--bg); transform: translateY(-150%); }
.skip-link:focus { transform: none; }
.menu-toggle { display: none; width: 40px; height: 40px; border-radius: 50%; border: 1px solid var(--line); background: var(--surface); }
.menu-toggle-lines, .menu-toggle-lines::before, .menu-toggle-lines::after { display: block; width: 16px; height: 2px; margin: auto; background: var(--ink); border-radius: 2px; position: relative; }
.menu-toggle-lines::before, .menu-toggle-lines::after { content: ""; position: absolute; left: 0; }
.menu-toggle-lines::before { top: -5px; } .menu-toggle-lines::after { top: 5px; }
.sidebar-backdrop { display: none; }
/* Celular / tablet: o menu vira gaveta (reaproveita o JS atual: body.nav-open) */
@media (max-width: 991.98px) {
  .menu-toggle { display: inline-grid; place-items: center; }
  .menu { position: fixed; z-index: 1040; left: 0; transform: translateX(-100%); transition: transform .2s; }
  body.nav-open .menu { transform: none; }
  body.nav-open .sidebar-backdrop { display: block; position: fixed; inset: 0; z-index: 1035; background: rgba(20, 10, 6, .45); }
  .topo, .pagina { padding-inline: 16px; }
}
@media (prefers-reduced-motion: reduce) { .menu { transition: none; } }
```

### includes/sidebar.html

```django
{# templates/includes/sidebar.html — grupos e nomes adaptados ao que o projeto tem hoje #}
<aside class="menu" id="menu-principal" aria-label="Navegação principal">
  <div class="menu__faixa" aria-hidden="true"></div>
  <a class="menu__marca" href="{% url 'core:dashboard' %}">
    <img src="{% static 'img/logo-murilos.png' %}" alt="" width="58" height="58">
    <span class="menu__nome">Murilo's<small>Pizzaria &amp; Pastelaria</small></span>
  </a>
  <nav>
    <div>
      <div class="menu__grupo">Hoje</div>
      <a class="menu__item" href="{% url 'core:dashboard' %}"><i class="ph ph-squares-four" aria-hidden="true"></i>Painel</a>
      <a class="menu__item" href="{% url 'vendas:listar' %}"><i class="ph ph-receipt" aria-hidden="true"></i>Vendas</a>
    </div>
    <div>
      <div class="menu__grupo">Estoque</div>
      <a class="menu__item" href="{% url 'ingredientes:listar' %}"><i class="ph ph-package" aria-hidden="true"></i>Ingredientes</a>
      <a class="menu__item" href="{% url 'ingredientes:importar' %}"><i class="ph ph-tray-arrow-down" aria-hidden="true"></i>Entradas (planilha)</a>
      <a class="menu__item" href="{% url 'ingredientes:sugestoes' %}"><i class="ph ph-shopping-cart" aria-hidden="true"></i>O que comprar
        {% if criticos_total %}<span class="menu__contador menu__contador--alerta">{{ criticos_total }}</span>{% endif %}</a>
      <a class="menu__item" href="{% url 'core:movimentacoes' %}"><i class="ph ph-arrows-left-right" aria-hidden="true"></i>Movimentações</a>
    </div>
    <div>
      <div class="menu__grupo">Cozinha</div>
      <a class="menu__item" href="{% url 'pizzas:listar' %}"><i class="ph ph-cooking-pot" aria-hidden="true"></i>Pizzas e fichas</a>
      <a class="menu__item" href="{% url 'pizzas:ranking' %}"><i class="ph ph-scales" aria-hidden="true"></i>Margens</a>
      <a class="menu__item" href="{% url 'vendas:consumo' %}"><i class="ph ph-chart-donut" aria-hidden="true"></i>Consumo</a>
    </div>
    {% if user.is_superuser %}
    <div>
      <div class="menu__grupo">Gestão</div>
      <a class="menu__item" href="{% url 'admin:index' %}"><i class="ph ph-gear" aria-hidden="true"></i>Administração</a>
    </div>
    {% endif %}
  </nav>
  <div class="menu__usuario">
    <span class="avatar" aria-hidden="true">{{ user.email|slice:":2"|upper }}</span>
    <span style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;font-size:12.5px">{{ user.email }}</span>
    <form action="{% url 'accounts:sair' %}" method="post">{% csrf_token %}
      <button class="botao botao--icone" style="background:transparent;border:0;color:var(--chromeInk2)" aria-label="Sair"><i class="ph ph-sign-out" aria-hidden="true"></i></button>
    </form>
  </div>
</aside>
<div class="sidebar-backdrop" data-menu-backdrop aria-hidden="true"></div>
{# O app.js atual já marca o link ativo: troque .classList.add('active') por aria-current="page" (já faz) e use .menu a[href] no seletor. #}
```

### includes/messages.html

```django
{# templates/includes/messages.html — mensagens do Django viram avisos flutuantes #}
{% if messages %}
<div class="avisos" aria-live="polite">
  {% for message in messages %}
  <div class="aviso {% if message.level_tag == 'error' or message.level_tag == 'warning' %}aviso--alerta{% elif message.level_tag == 'info' %}aviso--info{% endif %}"
       role="{% if message.level_tag == 'error' %}alert{% else %}status{% endif %}" data-aviso>
    <i class="ph-fill {% if message.level_tag == 'success' %}ph-check-circle{% elif message.level_tag == 'info' %}ph-info{% else %}ph-warning-circle{% endif %}" aria-hidden="true" style="font-size:22px"></i>
    <span style="flex:1">{{ message }}</span>
    <button class="aviso__fechar" type="button" aria-label="Fechar aviso" data-aviso-fechar>×</button>
  </div>
  {% endfor %}
</div>
{% endif %}
{# app.js: fechar no × e sumir sozinho após 6 s; mensagens de erro (role=alert) NÃO somem sozinhas. #}
```

> **Logo:** o arquivo oficial está no projeto de design em `project/assets/logo-murilos.png`.
> Copie para `static/img/logo-murilos.png`. **Contador de críticos:** um *context processor*
> de apresentação em `apps/core/` pode expor `criticos_total` reutilizando a mesma consulta
> que o painel já faz (sem novo cálculo).

## 5. Mapa de telas: protótipo × projeto

O protótipo tem 21 telas, 8 telas de app de bolso e 16 estados por ação. O projeto tem 18
templates. Os nomes no código continuam os mesmos; os rótulos na tela seguem a coluna "Rótulo".

| Template no repo | URL | Tela do protótipo | Rótulo na tela | Fase |
|---|---|---|---|---|
| `accounts/login.html` | /conta/entrar/ | 01 Login | — | UI-1 |
| `core/dashboard.html` | / | 02 Painel | Painel | UI-3 |
| `core/movimentacoes.html` | /movimentacoes/ | 06 Produto · Movimentações | Movimentações | UI-3 |
| `ingredientes/lista.html` | /ingredientes/ | 05 Produtos | Ingredientes | UI-4 |
| `ingredientes/formulario.html` | /ingredientes/novo/, /&lt;id&gt;/editar/ | 05 · estado A5 Novo produto | Novo / Editar ingrediente | UI-4 |
| `ingredientes/importar.html` | /ingredientes/importar/ | 08 Entradas · aba Planilha (A8) | Entradas por planilha | UI-4 |
| `ingredientes/importacao.html` | /ingredientes/importar/&lt;id&gt;/ | 08 Entradas · resultado | Entrada registrada | UI-4 |
| `ingredientes/sugestoes.html` | /ingredientes/sugestoes-compras/ | 09 Compras | O que comprar | UI-4 |
| `pizzas/lista.html` | /pizzas/ | 10 Cardápio e fichas | Pizzas e fichas | UI-5 |
| `pizzas/formulario.html` | /pizzas/nova/, /&lt;id&gt;/editar/ | 10 · novo item | Nova / Editar pizza | UI-5 |
| `pizzas/ficha_tecnica.html` | /pizzas/&lt;id&gt;/ficha-tecnica/ | 11 Ficha técnica | Ficha técnica | UI-5 |
| `pizzas/custo.html` | /pizzas/&lt;id&gt;/custo/ | 11 · card de custo e margem | Custo da pizza | UI-5 |
| `pizzas/ranking.html` | /pizzas/ranking/ | 12 Custos e margens | Margens | UI-5 |
| `vendas/lista.html` | /vendas/ | 03 Pedidos (visual) | Vendas | UI-6 |
| `vendas/formulario.html` | /vendas/novo/, /&lt;id&gt;/editar/ | 04 Novo pedido (passo 1) | Nova venda | UI-6 |
| `vendas/pizzas.html` | /vendas/&lt;id&gt;/pizzas/ | 04 Novo pedido (comanda) | Pizzas vendidas | UI-6 |
| `vendas/consumo.html` | /vendas/consumo-ingredientes/ | 13 Consumo | Consumo | UI-6 |
| `base.html`, `includes/*` | todas | Layout do protótipo | — | UI-0 / UI-1 |

> **Diferença de conceito:** no projeto, "Vendas" registra *períodos* (dia, semana ou mês) com
> total de pedidos e pizzas vendidas. A tela "Pedidos" do protótipo é por pedido individual.
> Use o *visual* de Pedidos/Novo pedido, mas mantenha a lógica de períodos.

### Telas do protótipo que ainda não existem no projeto

Ficam para quando as funcionalidades forem construídas. Não criar telas vazias agora.

- **Pedidos e Novo pedido por pedido:** canal (balcão, delivery, iFood), linha do tempo, cancelamento com senha do admin.
- **Produto · detalhe:** histórico de 6 meses do preço de compra (só o dono vê), cobertura em dias.
- **Inventário:** contagem por categoria, diferença em R$.
- **Fornecedores:** cadastro, força para negociar, quem cobra menos, cadastro na hora da compra.
- **Entregas:** rota pizzaria → entregador → cliente, temperatura da pizza.
- **Clientes e Mensagens:** segmentos, opt-in, WhatsApp automático e pesquisa 20 min.
- **Notas fiscais, Relatórios, Integrações, Usuários:** NFC-e, sazonalidade, iFood, permissões.
- **App de bolso (PWA):** entregador (rota, código, minha noite) · dono (hoje, auditoria, lista do mercado).

## 6. Especificação de cada tela

Formato: **estrutura** de cima para baixo, **componentes**, **estados** e **aceite**. Dados e
variáveis de contexto são os que a view já entrega.

### Login · `accounts/login.html` (UI-1)

- **Estrutura:** tela dividida em duas colunas iguais. Esquerda: fundo `--chrome`, faixa xadrez de 10px no rodapé, logo redondo 128px com sombra, "Bom serviço hoje!" em Bricolage 26px. Direita: formulário centralizado, até 380px.
- **Componentes:** campos em pílula (E-mail, Senha) com `<label>` visível; botão primário largura total "Entrar →"; erro de credencial em `.faixa--alerta` acima dos campos ("E-mail ou senha não conferem.").
- **Celular:** empilha: painel vinho com 220px de altura em cima, formulário embaixo.
- **Aceite:** foco inicial no e-mail; Enter envia; funciona sem JavaScript; nos dois temas.

### Painel · `core/dashboard.html` (UI-3)

- **Estrutura:** cabeçalho (subtítulo "Visão geral", título "Painel"). Abas Vendas | Estoque como `.segmentado` (mantém os `data-dashboard-*` e o JS atual).
  - **Aba Vendas:** card de filtro com datas em pílula + botão escuro "Atualizar"; título do resultado ("Vendas de 01/11 a 07/11") com nota de cálculo em `.faixa--info` quando houver estimativa/proporção; 4 KPIs: Pedidos, Custo dos ingredientes, **Faturamento (`cartao--ouro`, `ph-coins`)**, Lucro estimado (vermelho se negativo); tabela "Pizzas mais vendidas e margens" com posição em círculo, quantidade, faturamento, lucro e margem como `selo_margem`.
  - **Aba Estoque:** `.faixa--alerta` se houver saldo negativo; lista de críticos com selo e botão "Ver o que comprar".
- **Estados:** sem vendas no período: `.vazio` "Nenhuma venda registrada de dd/mm a dd/mm." com link "Registrar venda". Sem críticos: selo verde "Estoque em dia".
- **Aceite:** mesmos números de hoje (nenhum cálculo muda); abas por teclado (setas) continuam funcionando.

### Movimentações · `core/movimentacoes.html` (UI-3)

- **Estrutura:** cabeçalho "Estoque / Movimentações". Filtros: origem como `.chips` (Todas, Compra, Contagem, Baixa, Estorno) + ingrediente (select) e período (datas) em pílula. Tabela em `.cartao--tabela`: Data, Tipo, Origem, Ingrediente, Variação, Saldo (antes → depois), Usuário. Paginação em pílulas.
- **Tipos:** Compra: ícone `ph-file-text` verde, variação "+" verde · Contagem: `ph-clipboard-text` dourado · Baixa: `ph-receipt` neutro · Estorno: `ph-arrow-counter-clockwise` verde. A coluna Origem mantém o link para a importação ou o período de venda.
- **Aceite:** filtros continuam via GET e são preservados na paginação.

### Ingredientes · `ingredientes/lista.html` (UI-4)

- **Estrutura:** cabeçalho: subtítulo "Tudo o que a pizzaria compra e consome", título "Ingredientes", ações "Entradas por planilha" (secundário, `ph-microsoft-excel-logo`) e "Novo ingrediente" (primário). Chips: Todos · Abaixo do mínimo · Saldo negativo, com quantidade (filtro no navegador por `data-situacao` na linha, sem mudar a view). `.faixa--alerta` se houver negativos: "Azeitona está com saldo negativo: falta lançar uma entrada?". Tabela: Ingrediente (nome + unidade como sub-linha), Estoque (vermelho se crítico), Mínimo, Custo (R$/kg, R$/L ou R$/un), Situação (`selo_estoque`), botão "Editar" com ícone lápis e `aria-label="Editar Mussarela"`.
- **Estados:** vazio: "Nenhum ingrediente ativo. Cadastre o primeiro ou importe a planilha."

### Novo / Editar ingrediente · `ingredientes/formulario.html` (UI-4)

- **Estrutura:** card de formulário com no máximo 560px, título "Novo ingrediente" ou "Editar Mussarela". Campos em `.formulario`: Nome; Unidade e Estoque mínimo lado a lado; Quantidade em estoque e Custo unitário (com prefixo R$) lado a lado; "Ativo" como `.interruptor` com texto "Aparece nas listas e na baixa automática". Rodapé: "Cancelar" (secundário) e "Salvar" (primário).
- **Erros:** abaixo de cada campo, em `--tomatoInk`; erros gerais em `.faixa--alerta` no topo do card.

### Entradas por planilha · `ingredientes/importar.html` e `importacao.html` (UI-4)

- **Estrutura:** cabeçalho "Entradas no estoque" com ação "Baixar modelo .xlsx" (secundário). Área de envio `.envio`: ícone de planilha, "Arraste ou escolha a planilha (.xlsx ou .csv, até 2 MB)", texto das colunas obrigatórias, botão escuro "Escolher arquivo" (o `<input type="file">` real fica dentro do `<label>`). Após a prévia: layout `.duas-colunas` — à esquerda a tabela da prévia (linha, ingrediente, unidade, quantidade, custo, situação: Válida / Ingrediente novo / Erro; linhas com erro em `.linha--alerta`); à direita o painel com `.segmentado` Compra × Contagem e a explicação ("Soma ao saldo e recalcula o custo médio" / "Substitui saldo e custo"), resumo (válidas, novas, com erro), a caixa "Registrar outra operação idêntica" quando aparecer e o botão primário "Confirmar compra" ou "Confirmar contagem".
- **Resultado:** `importacao.html`: KPIs (itens, tipo, arquivo, data e usuário) e tabela antes → depois de saldo e custo.
- **Aceite:** linhas com erro bloqueiam a confirmação, como hoje; a mensagem de repetição bloqueada aparece em `.faixa--ouro`.

### O que comprar · `ingredientes/sugestoes.html` (UI-4)

- **Estrutura:** cabeçalho: subtítulo "Baseado no consumo dos períodos de venda registrados", título "O que comprar", à direita o `.passo-a-passo` "Comprar para [−] 7 dias [+]" (o campo atual de cobertura, 1–365; os botões só alteram o número e enviam o formulário GET). `.faixa--alerta` com os críticos. `.duas-colunas`: tabela (ingrediente + "Acaba em 2 dias" em vermelho quando aplicável, Tem, Gasta/dia, **Comprar**, Custo estimado) e painel com `.cartao--ouro` "Custo estimado" e botão "Imprimir lista".
- **Estados:** nada a comprar: selo verde e "Com a cobertura de 7 dias, nenhum ingrediente precisa de reposição."

### Pizzas e fichas · `pizzas/lista.html` (UI-5)

- **Estrutura:** cabeçalho: subtítulo "O que a casa vende e do que cada pizza é feita", ações "Margens" (secundário) e "Nova pizza" (primário). `.faixa--alerta` se houver pizzas sem ficha. Grade `.grade-cards` de `.pizza-card`: área de foto listrada ("foto · Calabresa G"), nome e preço, rodapé com "Custo R$ 18,40" e `selo_margem`. Sem ficha: borda tomate e rodapé "Sem ficha técnica · não baixa estoque". Links do card: "Ficha técnica", "Custo", "Editar".

### Ficha técnica · `pizzas/ficha_tecnica.html` (UI-5)

- **Estrutura:** voltar "← Pizzas e fichas", título com o nome da pizza, nota "Quantidades na unidade base do ingrediente (g, ml ou un)". `.duas-colunas`: à esquerda o card "Do que é feita" com cada item do formset numa linha (ingrediente em select pílula, quantidade em pílula com a unidade ao lado, remover como botão de ícone que marca o DELETE); abaixo, "Adicionar ingrediente" (o JS atual de `__prefix__` continua). À direita: preço de venda, custo atual, sobra por pizza e margem com `.barra` (meta 60%: verde ≥ 60, dourado ≥ 45, vermelho < 45) — valores vindos de `pizza` no contexto (se não houver, linkar para "Custo da pizza"). Botão primário "Salvar ficha".
- **Estados:** pendente: `.faixa--ouro` "Esta pizza ainda não tem ingredientes e não baixa estoque."

### Custo da pizza · `pizzas/custo.html` (UI-5)

- **Estrutura:** KPIs: Custo atual (`cartao--ouro`), Preço de venda, Lucro unitário, Margem. Tabela de composição: ingrediente, quantidade na ficha, custo vigente, custo na pizza (direita, tabular), total em destaque. Nota: "Calculado agora com o custo atual dos ingredientes. Vendas já registradas mantêm o custo da época."

### Margens · `pizzas/ranking.html` (UI-5)

- **Estrutura:** cabeçalho "Custos e margens". Lista ranqueada: posição em círculo dourado para o 1º, nome, preço, custo, lucro unitário e margem com `.barra` colorida + valor. Seção separada "Pendentes" com `.faixa--ouro` listando pizzas sem ficha e link para cada ficha.

### Vendas · `vendas/lista.html` (UI-6)

- **Estrutura:** cabeçalho "Registros de venda" com "Nova venda" (primário). Chips por tipo: Todos · Dia · Semana · Mês (filtro no navegador). Tabela: Período (datas), Tipo (selo neutro), Pedidos (tabular), ações "Pizzas vendidas" (escuro pequeno) e "Editar" (ícone). Registro com estoque negativo após a baixa ganha selo "Gerou saldo negativo".

### Nova venda · `vendas/formulario.html` (UI-6)

- **Estrutura:** card estreito: "1 · Período" com Tipo como `.segmentado` de rádios (Dia, Semana, Mês), datas lado a lado, total de pedidos em pílula. Erro de sobreposição em `.faixa--alerta`. Botões Cancelar / Salvar e continuar.

### Pizzas vendidas · `vendas/pizzas.html` (UI-6)

- **Estrutura:** estilo "comanda" do Novo pedido: cada linha do formset num bloco `--surface2` arredondado com a pizza (select), a quantidade com `.passo-a-passo` (− e + mudam o input número) e remover. À direita, card com o período, total de pedidos e a nota verde "Ao salvar, o estoque baixa pela ficha técnica de cada pizza." Botão primário "Salvar e baixar estoque".
- **Estados:** depois de salvar com saldo negativo: aviso vermelho "Mussarela ficou com saldo negativo (−0,4 kg). Lance a entrada que falta." (a mensagem já existe; só muda o visual).

### Consumo · `vendas/consumo.html` (UI-6)

- **Estrutura:** cabeçalho "Para onde vão os ingredientes". Filtro de período em pílulas. KPIs: pedidos considerados, ingredientes. Tabela: ingrediente, consumo total, média por pedido e uma `.barra` proporcional ao maior consumo (use `{% widthratio total maior 100 %}`; se a view não entregar o maior, calcular num filtro de template).

## 7. Estados e padrões de interação

| Estado | Onde | Como fazer |
|---|---|---|
| Aviso de sucesso / alerta / dinheiro | todas | Mensagens do Django → `.avisos` (seção 4) |
| Confirmar ação destrutiva | desativar ingrediente ou pizza, remover item da ficha | `<dialog class="dialogo">` com título, impacto e botões "Voltar" / "Desativar" |
| Carregando | envio de planilha, filtros | Botão de envio com `aria-busy="true"` e texto "Gerando prévia…"; sem telas de animação |
| Vazio | listas e tabelas | `.vazio` com frase útil + link da próxima ação |
| Erro de formulário | formulários | Erro abaixo do campo + resumo em `.faixa--alerta` no topo |
| Estoque crítico | painel, ingredientes, sugestões, menu | Selo + número em vermelho + contador no menu |
| Somente leitura / sem permissão | admin | Item de menu só aparece para superusuário |

## 8. Plano de implementação

Uma fase por branch e por pull request. Cada fase termina com todos os testes passando.

| Fase | Branch (guia) | Escopo |
|---|---|---|
| **UI-0 · Fundação** | `style/ui-0-fundacao` | Baixar para `static/vendor/`: Bootstrap 5.3.3 (css e js), Phosphor 2.1.1 (regular e fill, só woff2). Criar `tokens.css`, `bootstrap-sige.css`, `sige.css`; script do tema no `<head>`. Retirar o CDN do Bootstrap do `base.html`; manter `style.css` antigo carregado por último *só* até a UI-1. **Aceite:** todas as telas abrem com a paleta nova, sem quebrar layout. |
| **UI-1 · Layout e login** | `style/ui-1-layout` | `base.html` (com o topo embutido), `sidebar.html` e `messages.html` conforme a seção 4; `navbar.html` deixa de ser usado; troca de tema funcionando; bloco `trilha` em cada tela. Login no layout dividido; logo em `static/img/`. Remover do `style.css` o que foi substituído (`.app-shell`, `.topbar`, `.sidebar`…). **Aceite:** menu em gaveta no celular, item ativo marcado, avisos fecham. |
| **UI-2 · Componentes** | `style/ui-2-componentes` | `templates/includes/ui.html` com partials: cabeçalho, kpi, selo_estoque, selo_margem, vazio, faixa. Filtro de template `preco_unidade` (R$/kg, R$/L, R$/un) em `apps/core/templatetags/sige_ui.py`. **Aceite:** partials usados em pelo menos uma tela; teste simples do filtro. |
| **UI-3 · Painel e Movimentações** | `style/ui-3-painel` | Seção 6: Painel, Movimentações. |
| **UI-4 · Estoque** | `style/ui-4-estoque` | Ingredientes, formulário, Entradas por planilha, resultado, O que comprar. |
| **UI-5 · Cozinha** | `style/ui-5-cozinha` | Pizzas e fichas, formulário, Ficha técnica, Custo, Margens. |
| **UI-6 · Vendas** | `style/ui-6-vendas` | Registros, Nova venda, Pizzas vendidas, Consumo. |
| **UI-7 · Acabamento** | `style/ui-7-acabamento` | Revisão nos dois temas e em 390px; contraste; foco por teclado; remover classes Bootstrap que sobraram onde houver componente próprio. Apagar o `style.css` antigo. |

**Pedidos prontos para colar no Claude Code**

- **Fase UI-0:** "Leia o Guia de UI do SIGE Murilo's (link). Crie a branch style/ui-0-fundacao a partir da dev e implemente a fase UI-0 exatamente como descrita: arquivos locais do Bootstrap 5.3.3 e Phosphor 2.1.1, tokens.css, bootstrap-sige.css, sige.css e o script de tema. Não altere models, views, forms ou testes. No final rode check, test e ruff e me mostre o resultado e a lista de arquivos alterados."
- **Fases seguintes:** "Agora a fase UI-N do guia, na branch style/ui-N-…, seguindo a seção 6 para cada tela listada. Mostre o antes e depois de cada template e rode check, test e ruff."

## 9. Checklist de revisão de cada tela

- [ ] Usa só tokens (nenhuma cor fixa no template ou em CSS novo).
- [ ] Cabeçalho no padrão: subtítulo, título 38px, ações à direita, um único botão primário.
- [ ] Números com `.num`, alinhados à direita; dinheiro como "R$ 1.234,56".
- [ ] Situações com selo e texto, nunca só cor.
- [ ] Funciona no tema Forno (fundo escuro) sem texto ilegível.
- [ ] Em 390px: nada corta, tabelas rolam dentro do card, botões não quebram texto.
- [ ] Teclado: Tab percorre tudo em ordem; foco visível; diálogos fecham com Esc.
- [ ] Ícones decorativos com `aria-hidden`; botões só-ícone com `aria-label`.
- [ ] Mensagens de erro dizem o que aconteceu e o que fazer.
- [ ] `python manage.py test` e `ruff check .` passando.

---

## Adaptações ao repositório

Decisões e correções tomadas ao aplicar o guia neste repositório. Elas não mudam o tema
aprovado, só ajustam o guia ao estado atual do código.

### Stack de front adotada

O SIGE é renderizado no servidor (Django templates + views em função) e os testes verificam
o HTML das telas. Por isso **não** se adota Vue/Vuex, React ou outro framework JavaScript:
isso exigiria transformar o sistema em API + SPA e reescrever as telas e os testes. Também
não se adota Tailwind: exigiria uma etapa de build (Node ou binário) e duplicaria o que o
guia já define em classes próprias.

| Camada | Escolha | Papel |
|---|---|---|
| Renderização e componentes | Django 6 templates + **template partials** (`{% partialdef %}`) em `templates/includes/ui.html` | Componentes reutilizáveis (cabeçalho, KPI, selos, vazio, faixa) sem dependência nova |
| Design system | `tokens.css` (variáveis dos temas Cantina e Forno) + `sige.css` (componentes em português, BEM leve) | Fonte única de cores, formas e componentes |
| Grid e componentes de transição | **Bootstrap 5.3.3** local em `static/vendor/`, tematizado por `bootstrap-sige.css` | Mantém as telas atuais funcionando enquanto são migradas tela a tela |
| Ícones | **Phosphor 2.1.1** (regular e fill) local | Substitui os SVG desenhados à mão |
| Fontes | Bricolage Grotesque + Figtree (Google Fonts) | Únicos arquivos externos permitidos |
| Interação | JavaScript puro em `static/js/app.js` | Tema, menu em gaveta, avisos, chips, passo-a-passo |
| Formatação | templatetags de apresentação em `apps/core/templatetags/sige_ui.py` | R$/kg, R$/L, R$/un, números tabulares |

### Branches e commits

- Branches seguem o padrão do repositório, com underscore: `style/ui_0_fundacao`,
  `style/ui_1_layout` etc. (o guia usa hífen).
- Dentro de cada fase, **um commit por tela ou por peça** (ex.: um commit para os arquivos de
  vendor, outro para os tokens), para facilitar a revisão.

### Correções no próprio guia

1. O `sidebar.html` do guia usa `{% static %}` sem `{% load static %}`. Includes não herdam o
   `load` do `base.html`: o arquivo precisa começar com `{% load static %}`.
2. Os snippets de `sidebar.html`, `messages.html` e do partial `kpi` usam `style="..."`, o que
   contraria a regra "sem estilo inline novo". Na implementação, esses estilos viram classes
   em `sige.css`/`shell.css`.
3. O logo (`logo-murilos.png`) está no projeto de design, fora do repositório; precisa ser
   copiado para `static/img/`.
4. O número de testes cresceu: a regra vale para **todos** os testes existentes
   (112 em 27/11/2026), não só os 110 citados.

### Textos que os testes exigem

Vários testes verificam textos das telas. Quando o rótulo do guia conflitar com um teste, o
**texto exigido pelo teste é mantido** e o visual do guia é aplicado em volta dele. Exemplos:
"Lucro unitário (R$)", "Margem (%)" e "Fichas pendentes" (ranking); "Confirmar atualização"
(importação); "Pendente" (lista de pizzas); "Custo total dos ingredientes" e "Custo atual"
(custo); "100 G" / "5 ML" (consumo); "Estimativa diária" e "Cálculo proporcional" (painel);
"Compra", "Baixa por venda", "Importação #N", "Venda #N" (movimentações). O layout base nunca
pode conter as palavras "Inativo", "Inativa" ou "Sem ficha", que alguns testes verificam que
**não** aparecem.
