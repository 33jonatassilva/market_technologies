# Consumer groups e Share Consumer

O Kafka oferece duas formas principais de consumo cooperativo: **consumer groups** (clássico) e **share groups** (Share Consumer API).

## Consumer groups

Em um **consumer group**, cada partição do tópico é consumida por **no máximo um** consumer do grupo. Vários consumers dividem as partições entre si: assim você escala o consumo adicionando mais instâncias ao grupo.

- O **coordinator** (broker) atribui partições aos membros do grupo.
- Se um consumer sai ou entra, ocorre um **rebalance**: as partições são redistribuídas.
- O progresso é o **offset** por partição; o consumer (ou o grupo) faz commit do offset. Não há “ack” por mensagem; o commit é tipicamente por lote.

**Static membership**: a partir do 2.3, os membros podem usar um ID estável (`group.instance.id`). Assim, em deploys ou restarts, o grupo não precisa rebalancear só porque um processo reiniciou, o que ajuda em aplicações com estado pesado (ex.: Kafka Streams).

## Share groups (Share Consumer API)

**Share groups** são uma alternativa ao modelo de consumer group. Os consumidores no share group são chamados **share consumers**.

Diferenças principais em relação ao consumer group:

- **Contagem de tentativas**: o sistema conta quantas vezes um record foi entregue, permitindo tratar records “não processáveis” (dead letter, retry limitado).
- **Ack por record**: cada record pode ser confirmado (ack) ou liberado individualmente, embora o sistema incentive processamento em lote.
- **Mais consumers que partições**: o número de share consumers pode ser maior que o número de partições; os records são distribuídos entre eles com um mecanismo de “empréstimo”.
- **Cooperação**: várias partições podem ser compartilhadas por vários consumers; cada record fica “emprestado” a um consumer por um tempo (lock).

Quando um share consumer busca records, ele recebe records disponíveis das partições inscritas. O record fica **adquirido** (lock) por um tempo configurável (ex.: 30 segundos). O consumer pode:

- **Não fazer nada** → o lock expira.
- **Renovar** o lock (ainda processando).
- **Rejeitar** o record (marca como não processável, não será reentregue).
- **Liberar** o record (fica disponível para outra tentativa).
- **Confirmar (ack)** o processamento com sucesso.

O broker limita quantos records por partição podem estar “emprestados” ao mesmo tempo em um share group (`group.share.partition.max.record.locks`), evitando que um consumer segure tudo sem processar.

## Quando usar cada um

| Cenário | Sugestão |
|--------|----------|
| Processamento paralelo por partição, ordem por partição, estado simples | Consumer group |
| Replay fácil, reprocessamento, pipelines clássicos | Consumer group |
| Múltiplas tentativas, ack por mensagem, mais consumers que partições | Share group |
| Evitar rebalance em deploys (Kafka Streams, etc.) | Consumer group + static membership |

## Referências

- [Consumer groups — Apache Kafka](https://kafka.apache.org/documentation/#consumerconfigs)
- [The Share Consumer — Design](https://kafka.apache.org/documentation/#design_share_consumer)
- [Static Membership (KIP-345)](https://cwiki.apache.org/confluence/x/kRg0BQ)
