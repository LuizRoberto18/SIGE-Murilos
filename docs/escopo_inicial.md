# Escopo inicial

Esta etapa entrega autenticação por e-mail, dashboard de estoque, cadastro e edição de ingredientes e pizzas, ficha técnica, administração, o modelo XLSX da HU05, a prévia da HU06, a confirmação de importações da HU07, o registro de períodos da HU08, as pizzas vendidas da HU09 e a baixa automática da HU10. Todas as views próprias são funções. O estoque negativo é permitido e sinalizado; o cadastro manual exige valor não negativo. A quantidade da ficha usa a unidade base do ingrediente.

O dashboard mostra somente dados existentes. Pizza sem itens de ficha aparece como pendente. Não há exclusão pelo painel operacional; os relacionamentos da ficha são protegidos contra exclusão. A tela de planilha permite baixar o modelo e pré-visualizar XLSX ou CSV. Linhas inválidas são identificadas, KG/L são convertidos para G/ML, e ingredientes novos são sinalizados. A prévia não altera o estoque; a confirmação aplica compra ou contagem e registra a importação com valores anteriores e posteriores. O mesmo envio não é reaplicado e conteúdo idêntico exige confirmação expressa de repetição. O arquivo enviado não é armazenado.

O módulo de vendas registra tipo (dia, semana ou mês), intervalo de datas inclusivo e total de pedidos não negativo. Períodos com datas sobrepostas são rejeitados, mesmo quando os tipos são diferentes. Cada período pode ter várias pizzas vendidas, com quantidades inteiras não negativas. Pizzas sem ficha técnica ou inativas não podem ser adicionadas; a mesma pizza não pode ser repetida no período.

Salvar as pizzas calcula o consumo pela ficha técnica, soma o uso por ingrediente e baixa o estoque atomicamente. Preço e custo unitário da pizza são preservados no item da venda. As movimentações registram baixas e estornos com seus saldos e custos. Reenvios idênticos não duplicam a baixa; uma correção estorna a versão anterior antes de aplicar a nova. Saldos negativos são aceitos e sinalizados.

## Próximas etapas

Os models `Importacao` e `ItemImportacao` registram as atualizações confirmadas; `RegistroVenda`, `ItemVenda` e `Movimentacao` representam vendas, snapshots e alterações do estoque da HU08 à HU10. `Configuracao` fica reservada para sprint futura. A consulta operacional unificada do histórico da HU11, sugestões de compra, métricas de margem, relatórios avançados, API, notificações, integrações e implantação em produção continuam fora desta entrega.

O TAP citado no pedido não estava presente no diretório. Esta implementação segue o escopo descrito na solicitação.
