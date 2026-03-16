# Operações e monitoramento

Este documento resume tópicos **operacionais** e de **monitoramento** do RabbitMQ. Para produção, consulte sempre a [documentação oficial](https://www.rabbitmq.com/docs) e o [Production Checklist](https://www.rabbitmq.com/docs/production-checklist).

## Management plugin

- O **management plugin** expõe uma interface web (porta 15672) e uma **HTTP API** para gerenciar e inspecionar o broker.
- Permite: criar/listar/excluir queues, exchanges, bindings; publicar e consumir mensagens de teste; ver conexões, canais, usuários; métricas de publish/consume e profundidade de filas.
- Em produção: proteja com TLS e autenticação; restrinja acesso por rede; não use usuário `guest` em ambiente exposto.

## Métricas importantes

- **Queues**: mensagens **ready** (prontas para entrega), **unacked** (entregues mas não confirmadas), **total**; taxa de **publish** e **deliver** (ou **get**). Filas crescendo indicam consumers insuficientes ou lentos.
- **Connections e channels**: número de conexões e canais abertos; útil para detectar vazamento (conexões/canais não fechados).
- **Disk space**: o broker precisa de espaço em disco para metadados e mensagens persistentes; alertas de disco cheio evitam falhas.
- **Cluster**: em cluster, status dos nós (running/partition) e quorum das quorum queues (perda de maioria = queue indisponível).

## Operações básicas

- **Adicionar/remover nós** em um cluster: seguir a documentação de [Clustering](https://www.rabbitmq.com/docs/clustering); quorum queues toleram falha de minoria.
- **Políticas (policies)**: configuram TTL, alternate exchange, quorum, etc., por padrão de nome (queue/exchange). Preferir políticas quando possível em vez de hardcodar argumentos na aplicação.
- **Usuários e permissões**: criar usuários por aplicação ou ambiente; limitar permissões (configure, write, read) por vhost. Não usar guest em produção.
- **Virtual hosts**: usar vhosts para isolar ambientes (ex.: `/producao`, `/homolog`).

## Logs e troubleshooting

- **Logs do broker**: diretório de log e nível (info, warning, error) configuráveis. Úteis para erros de conexão, falhas de disco, problemas de cluster.
- **Firehose**: recurso do management que re-publica todas as mensagens em um exchange de trace (alto custo; usar só para debug pontual).
- **Unroutable messages**: mensagens que não conseguem ser roteadas (nenhuma binding compatível) podem ser descartadas ou devolvidas; use **alternate exchange** ou trate **return** no publisher para não perder mensagens.

## Resumo

| Área | O que fazer |
|------|-------------|
| Management | Habilitar plugin; proteger acesso; não usar guest em produção |
| Métricas | Profundidade de filas (ready/unacked), taxas publish/deliver, conexões, disco, cluster |
| Cluster | Acompanhar nós e quorum; adicionar/remover nós conforme doc |
| Segurança | Usuários, permissões, vhosts; TLS para conexões e management |
| Troubleshooting | Logs do broker; firehose só para debug; alternate exchange para unroutable |

## Referências

- [Monitoring — RabbitMQ](https://www.rabbitmq.com/docs/monitoring)
- [Management Plugin](https://www.rabbitmq.com/docs/management)
- [Production Checklist](https://www.rabbitmq.com/docs/production-checklist)
- [Clustering](https://www.rabbitmq.com/docs/clustering)
