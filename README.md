# SIGE Murilo's

Fundação funcional do sistema de gestão de estoque da Pizzaria Murilo's, implementada com Python 3.14, Django 6.0.10, templates, Bootstrap 5, SQLite e views baseadas em funções.

## Estrutura

- `config/`: configurações e roteamento principal.
- `apps/accounts/`: usuário por e-mail e autenticação.
- `apps/core/`: painel de indicadores e consulta de movimentações do estoque.
- `apps/ingredientes/`: cadastro, planilhas, atualização do estoque e sugestões de compras.
- `apps/pizzas/`: pizzas, fichas técnicas, custos atuais e ranking de margens.
- `apps/vendas/`: períodos, pizzas vendidas e baixa automática do estoque (HU08 a HU10).
- `templates/` e `static/`: interface.
- `docs/escopo_inicial.md`: limites desta etapa.

## Instalação

Requer Python 3.14 e Git. No Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Configure `DJANGO_SECRET_KEY` no ambiente. Em desenvolvimento, uma chave local descartável é usada se a variável estiver ausente. Para desativar o modo de depuração, defina `DJANGO_DEBUG=0` e uma chave própria. `.env.example` documenta as variáveis; o projeto lê variáveis do ambiente e não carrega `.env` automaticamente.

SQLite é o padrão local. A opção `DB_ENGINE=postgresql` prepara a configuração de conexão futura; nesse caso, será preciso instalar `psycopg` e definir as variáveis `DB_*`.

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Validação

```powershell
python manage.py check
python manage.py test
ruff check .
```

## URLs

| Caminho | Função |
| --- | --- |
| `/` | Dashboard |
| `/movimentacoes/` | Histórico unificado de movimentações do estoque |
| `/conta/entrar/` | Login |
| `/conta/sair/` | Logout via POST |
| `/ingredientes/` | Lista de ingredientes ativos |
| `/ingredientes/novo/` | Cadastro de ingrediente |
| `/ingredientes/importar/` | Download do modelo e prévia de XLSX ou CSV |
| `/ingredientes/importar/modelo/` | Download do modelo XLSX |
| `/ingredientes/importar/confirmar/` | Confirmação de compra ou contagem via POST |
| `/ingredientes/importar/<id>/` | Resultado e registro da importação |
| `/ingredientes/sugestoes-compras/` | Ingredientes críticos e sugestões de reposição |
| `/ingredientes/<id>/editar/` | Edição de ingrediente |
| `/pizzas/` | Lista de pizzas ativas |
| `/pizzas/nova/` | Cadastro de pizza |
| `/pizzas/ranking/` | Ranking de margem e lucro unitário |
| `/pizzas/<id>/editar/` | Edição de pizza |
| `/pizzas/<id>/ficha-tecnica/` | Ficha técnica |
| `/pizzas/<id>/custo/` | Custo atual e composição da pizza |
| `/vendas/` | Lista de períodos de vendas |
| `/vendas/novo/` | Registro de período |
| `/vendas/<id>/editar/` | Edição de período |
| `/vendas/<id>/pizzas/` | Pizzas vendidas no período |
| `/admin/` | Django Admin |

O primeiro usuário é criado com `createsuperuser`. Não há cadastro público. As páginas internas exigem login.

## Modelo de planilha do estoque

Na tela `/ingredientes/importar/`, usuários autenticados podem baixar o modelo XLSX com as colunas `ingrediente`, `unidade`, `quantidade` e `custo_unitario`. O envio aceita XLSX e CSV de até 2 MB, com as colunas obrigatórias em qualquer ordem. CSV pode usar vírgula ou ponto e vírgula como separador, com codificação UTF-8 ou Windows-1252.

A prévia identifica linhas com quantidade ou custo inválidos, ingredientes novos e unidades incompatíveis com o cadastro. Aceita G, ML, UN, KG e L: KG é convertido em G e L em ML. A quantidade é multiplicada por 1.000 e o custo unitário por KG ou L é dividido por 1.000, com arredondamento para quatro casas decimais. A planilha pode ter até 5.000 linhas preenchidas. Gerar a prévia não altera o estoque.

Quando todas as linhas são válidas, escolha **compra** ou **contagem** e confirme. Compra soma a quantidade ao saldo e calcula o custo médio ponderado pelos saldos e custos anteriores e pela entrada. Se o saldo anterior for zero ou negativo, o custo da entrada é usado; uma compra de quantidade zero mantém o custo existente. Contagem substitui saldo e custo pelos valores informados. A confirmação é atômica e registra usuário, arquivo, tipo e valores antes/depois por ingrediente. Repetir o POST não aplica novamente a operação; reenviar os mesmos dados e tipo também é bloqueado, salvo quando o usuário marca expressamente que deseja registrar outra operação idêntica. O arquivo enviado não é armazenado. Para usar a nova tabela de importações, execute `python manage.py migrate`.

## Períodos de vendas

Em `/vendas/`, usuários autenticados podem listar, cadastrar e corrigir períodos. Cada registro informa o tipo (dia, semana ou mês), as datas inicial e final, e o número inteiro de pedidos, que pode ser zero. As datas delimitam o intervalo informado; o tipo identifica sua granularidade. O sistema rejeita datas invertidas e qualquer sobreposição com outro registro, inclusive quando os tipos diferem ou os intervalos compartilham uma data de borda. A edição mantém essa validação e permite corrigir o próprio registro. A migration da HU08 é aplicada com `python manage.py migrate`.

Em cada período, a tela **Pizzas vendidas** permite adicionar mais de um tipo de pizza, corrigir quantidades e remover itens. A quantidade de cada pizza deve ser um inteiro não negativo. Somente pizzas ativas com ao menos um ingrediente na ficha técnica podem ser selecionadas; duplicatas no mesmo período são rejeitadas.

Ao salvar, o consumo de cada ingrediente é calculado pela quantidade vendida de cada pizza multiplicada pela quantidade de sua ficha técnica. Os consumos iguais são somados antes da baixa. Cada item preserva o preço de venda e o custo da pizza no momento da operação; cada movimentação preserva quantidade, custo do ingrediente, usuário e saldos anterior e posterior.

Um reenvio sem alterações não gera nova baixa. Quando a venda é corrigida, o sistema estorna o consumo vigente e aplica a nova composição na mesma transação. O estoque pode ficar negativo e, nesse caso, a interface exibe um alerta; o dashboard também passa a identificar o ingrediente. A migration da HU10 é aplicada com `python manage.py migrate`.

## Movimentações do estoque

Em `/movimentacoes/`, usuários autenticados podem consultar em uma única linha do tempo as compras, contagens, baixas e estornos. Cada lançamento mostra data, usuário, ingrediente, origem, variação e saldos anterior e posterior. A identificação da operação possui link para a importação ou para o período de venda correspondente.

A consulta pode ser filtrada por origem, ingrediente e intervalo de datas, e os filtros são preservados durante a paginação. O histórico utiliza os registros permanentes das importações e das movimentações de venda, mantendo lançamentos anteriores quando novas operações são realizadas. A HU11 não adiciona migration.

## Custos atuais das pizzas

A lista de pizzas apresenta o custo atual dos ingredientes de cada produto. Em `/pizzas/<id>/custo/`, o total é detalhado por ingrediente, com a quantidade da ficha técnica, o custo unitário vigente e o custo correspondente na pizza. O cálculo soma a quantidade de cada item da ficha multiplicada pelo custo atual do ingrediente e arredonda o total para quatro casas decimais.

Como o valor é calculado no momento da consulta, uma compra ou contagem que altere os custos dos ingredientes atualiza automaticamente o custo da pizza. Vendas já registradas mantêm em `ItemVenda.custo_unitario` o custo capturado quando o estoque foi baixado. A HU12 não adiciona migration.

## Margens e ranking

Em `/pizzas/ranking/`, as pizzas ativas com ficha técnica são ordenadas pela margem calculada e, em caso de empate, pelo lucro unitário. O lucro unitário corresponde ao preço de venda menos o custo atual. A margem percentual corresponde ao lucro dividido pelo preço de venda e multiplicado por 100; o cálculo retorna 0% quando o preço é zero, sem divisão inválida.

A tabela identifica os valores monetários em reais e a margem em percentual. Pizzas sem ingredientes na ficha aparecem separadamente como pendentes e não recebem uma margem artificial. O ranking usa os custos atuais dos ingredientes e não altera os snapshots históricos das vendas. A HU13 não adiciona migration.

## Sugestões de compras

Em `/ingredientes/sugestoes-compras/`, o sistema alerta quando o saldo de um ingrediente ativo é menor ou igual ao estoque mínimo. A quantidade sugerida aplica `consumo médio diário × dias de cobertura + estoque mínimo − saldo atual`; somente resultados positivos são exibidos.

O consumo médio diário considera as baixas menos os estornos e divide o consumo líquido pela quantidade total de dias dos períodos de vendas registrados. Dessa forma, correções de venda não duplicam o consumo. A cobertura começa em sete dias e pode ser alterada na própria consulta, entre 1 e 365 dias. Ingredientes acima do mínimo também podem receber sugestão quando a projeção indicar cobertura insuficiente. A HU14 não adiciona migration.

## Painel de indicadores

O dashboard em `/` permite selecionar uma data de referência e consultar o dia, a semana de segunda a domingo ou o mês correspondente. O painel apresenta pedidos, custo dos ingredientes, faturamento, lucro estimado e as cinco pizzas mais vendidas, incluindo lucro e margem de cada produto.

Faturamento e custo usam os preços e custos históricos preservados em `ItemVenda`; o lucro estimado é a diferença entre esses valores. Registros que cobrem apenas parte do intervalo são proporcionados pela quantidade de dias sobrepostos. Quando um dia é derivado de um registro semanal ou mensal, a interface identifica os resultados como médias diárias estimadas. A HU15 não adiciona migration.
