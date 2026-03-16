# Replicação e alta disponibilidade

Este documento resume como o RabbitMQ oferece **alta disponibilidade** e **replicação** de dados, com base na documentação oficial.

## Clustering

- Vários nós RabbitMQ podem formar um **cluster**: compartilham usuários, virtual hosts, definições de exchanges e bindings. As **queues** são criadas em um nó específico; metadados são replicados no cluster.
- Clientes podem se conectar a **qualquer** nó; se a queue estiver em outro nó, a mensagem é encaminhada internamente (transparente para o publisher/consumer).
- Para **alta disponibilidade** das filas em si, é necessário usar filas **replicadas**: hoje o modelo recomendado são as **quorum queues**.

## Quorum queues

- **Quorum queues** são o tipo de fila replicada recomendado no RabbitMQ (a partir de 3.8; em 4.x as classic mirrored queues foram removidas). Elas usam o algoritmo **Raft** para consenso.
- Várias **réplicas** da mesma queue existem em nós diferentes do cluster. Uma réplica é o **leader**; as outras são **followers**.
- Uma mensagem só é considerada **confirmada** quando uma **maioria (quorum)** de réplicas a recebeu: `(N/2)+1` réplicas, onde N é o número de réplicas. Assim, falhas de minoria de nós não causam perda de mensagens.
- Se o **leader** cair, um novo leader é **eleito** automaticamente entre os followers. O cluster continua servindo desde que uma maioria permaneça ativa.
- Quorum queues são **durable** por definição e priorizam **segurança dos dados**; suportam TTL, dead letter, single active consumer e (em versões recentes) prioridade.

**Recomendação**: para produção com HA, use **quorum queues** com pelo menos 3 nós no cluster (ou 3 réplicas da queue).

## Federação e Shovel

- **Federation**: permite que exchanges ou queues em um broker “replicem” ou encaminhem mensagens para outro broker (outro datacenter, outra rede). Útil para distribuição geográfica ou integração entre clusters.
- **Shovel**: move mensagens de uma queue (ou exchange) em um broker para outro broker. Pode ser usado para migração, backup ou integração ponta a ponta.

Esses recursos são configurados via **plugins** e políticas; a documentação oficial descreve cenários e limitações.

## Resumo

| Conceito | Descrição |
|----------|-----------|
| Cluster | Vários nós compartilham metadados; queues em nós específicos |
| Quorum queues | Filas replicadas via Raft; maioria confirma; líder eleito; HA recomendado |
| Federation | Encaminhamento entre brokers (ex.: multi-datacenter) |
| Shovel | Movimento de mensagens entre brokers (queue/exchange → outro broker) |

## Referências

- [Quorum Queues — RabbitMQ](https://www.rabbitmq.com/docs/quorum-queues)
- [Clustering — RabbitMQ](https://www.rabbitmq.com/docs/clustering)
- [Distributed RabbitMQ](https://www.rabbitmq.com/docs/distributed)
- [Federation](https://www.rabbitmq.com/docs/federation)
- [Shovel](https://www.rabbitmq.com/docs/shovel)
