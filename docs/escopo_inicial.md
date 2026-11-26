# Escopo inicial

Esta etapa entrega autenticação por e-mail, dashboard de estoque, cadastro e edição de ingredientes e pizzas, ficha técnica, administração, o modelo XLSX da HU05, a prévia da HU06, a confirmação de importações da HU07, o registro de períodos da HU08, as pizzas vendidas da HU09, a baixa automática da HU10, a consulta de movimentações da HU11, o custo atualizado das pizzas da HU12, o ranking de margens da HU13 e as sugestões de compras da HU14. Todas as views próprias são funções. O estoque negativo é permitido e sinalizado; o cadastro manual exige valor não negativo. A quantidade da ficha usa a unidade base do ingrediente.

O dashboard mostra somente dados existentes. Pizza sem itens de ficha aparece como pendente. Não há exclusão pelo painel operacional; os relacionamentos da ficha são protegidos contra exclusão. A tela de planilha permite baixar o modelo e pré-visualizar XLSX ou CSV. Linhas inválidas são identificadas, KG/L são convertidos para G/ML, e ingredientes novos são sinalizados. A prévia não altera o estoque; a confirmação aplica compra ou contagem e registra a importação com valores anteriores e posteriores. O mesmo envio não é reaplicado e conteúdo idêntico exige confirmação expressa de repetição. O arquivo enviado não é armazenado.

O módulo de vendas registra tipo (dia, semana ou mês), intervalo de datas inclusivo e total de pedidos não negativo. Períodos com datas sobrepostas são rejeitados, mesmo quando os tipos são diferentes. Cada período pode ter várias pizzas vendidas, com quantidades inteiras não negativas. Pizzas sem ficha técnica ou inativas não podem ser adicionadas; a mesma pizza não pode ser repetida no período.

Salvar as pizzas calcula o consumo pela ficha técnica, soma o uso por ingrediente e baixa o estoque atomicamente. Preço e custo unitário da pizza são preservados no item da venda. As movimentações registram baixas e estornos com seus saldos e custos. Reenvios idênticos não duplicam a baixa; uma correção estorna a versão anterior antes de aplicar a nova. Saldos negativos são aceitos e sinalizados.

A consulta de movimentações reúne compras, contagens, baixas e estornos em ordem cronológica. Cada lançamento informa data, usuário, origem, ingrediente, diferença e saldos anterior e posterior, além de identificar a importação ou venda responsável. Filtros por origem, ingrediente e período e paginação estão disponíveis. Novas operações acrescentam registros sem remover o histórico existente.

O custo atual de cada pizza é calculado pela soma das quantidades da ficha técnica multiplicadas pelos custos vigentes dos ingredientes. A lista apresenta o total e uma página detalha sua composição. Alterações de custo feitas por importações aparecem na consulta seguinte, enquanto cada item de venda preserva o custo capturado no momento de sua baixa.

O ranking considera pizzas ativas com ficha configurada e ordena por margem percentual, usando o lucro unitário como desempate. O lucro é o preço de venda menos o custo atual, e a margem é o lucro dividido pelo preço e multiplicado por 100. Preço zero retorna margem de 0% sem erro. Valores em reais e percentuais são identificados separadamente; fichas pendentes ficam fora do ranking e são sinalizadas.

As sugestões de compras usam o consumo líquido das baixas e estornos dividido pelos dias abrangidos pelos períodos registrados. A projeção multiplica esse consumo médio diário pelos dias de cobertura, soma o estoque mínimo e desconta o saldo atual. A cobertura começa em sete dias, pode ser ajustada entre 1 e 365 e somente resultados positivos são exibidos. Ingredientes com saldo menor ou igual ao mínimo são classificados como críticos no dashboard, na lista e na consulta de compras.

## Próximas etapas

Os models `Importacao` e `ItemImportacao` registram as atualizações confirmadas; `RegistroVenda`, `ItemVenda` e `Movimentacao` representam vendas, snapshots e alterações do estoque da HU08 à HU10. A HU11 consulta esses registros sem duplicá-los, e as HU12 à HU14 calculam custos, margens e sugestões sem armazenar valores derivados. `Configuracao` fica reservada para sprint futura. Relatórios avançados, API, notificações, integrações e implantação em produção continuam fora desta entrega.

O TAP citado no pedido não estava presente no diretório. Esta implementação segue o escopo descrito na solicitação.
