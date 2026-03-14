# Operações e monitoramento

Este documento resume tópicos operacionais do Kafka conforme a documentação oficial. Para ambientes de produção, consulte sempre a documentação completa e as melhores práticas da sua versão.

## Operações básicas

- **Tópicos**: criação, alteração de configuração, listagem e exclusão via ferramentas de linha de comando (`kafka-topics.sh`) ou Admin API. Atenção a número de partições, fator de replicação e políticas de retenção/compaction.
- **Brokers**: adicionar/remover brokers, rolling restarts. O controller (no KRaft, os nós de controller) gerencia a distribuição de partições e a eleição de líderes.
- **Consumers**: acompanhar lag por consumer group (`kafka-consumer-groups.sh`), revisar configurações de session e heartbeat para evitar rebalances desnecessários.

## KRaft vs ZooKeeper

O Kafka pode usar **ZooKeeper** (modo legado) ou **KRaft** (Kafka Raft) para metadados do cluster (tópicos, brokers, controller).

- **KRaft**: não depende do ZooKeeper; os nós do cluster assumem papéis de controller ou broker. É o modo recomendado para novos ambientes e versões recentes.
- **ZooKeeper**: ainda suportado em versões atuais, mas a migração para KRaft é o caminho indicado pela documentação.

Consulte a documentação de [KRaft](https://kafka.apache.org/documentation/#kraft) e [upgrading](https://kafka.apache.org/documentation/#upgrade) para planejar migração ou novo deploy.

## Monitoramento

- **Métricas dos brokers**: JMX ou sistemas que coletam métricas do Kafka (taxa de produce/fetch, latência, tamanho dos logs, ISR, under-replicated partitions, etc.).
- **Consumer lag**: atraso entre o último offset produzido e o offset commitado do consumer group. Lag alto pode indicar consumers lentos ou partições desbalanceadas.
- **Quotas**: acompanhar throttling (request rate e bandwidth) por client-id/user para ajustar limites.
- **Log compaction**: métricas como tempo de compactação, partições não compactáveis, atraso de compactação (quando aplicável).

A documentação oficial tem uma seção dedicada a [Monitoring](https://kafka.apache.org/documentation/#monitoring).

## Multi-tenancy

Em clusters compartilhados, use **quotas** (por user e/ou client-id) para limitar uso de CPU e banda. Tópicos e ACLs permitem isolar recursos por equipe ou aplicação. Namespaces lógicos podem ser feitos por prefixos de nomes de tópicos e políticas de acesso.

## Tiered Storage (resumo)

Algumas implementações ou extensões permitem armazenar dados antigos em armazenamento mais barato (object storage) em vez de apenas disco nos brokers. Isso reduz custo e permite reter mais dados. Consulte a documentação da sua versão e do provedor para disponibilidade e configuração.

## Referências

- [Operations — Apache Kafka](https://kafka.apache.org/documentation/#operations)
- [Basic Kafka Operations](https://kafka.apache.org/documentation/#basic_ops)
- [Monitoring](https://kafka.apache.org/documentation/#monitoring)
- [KRaft](https://kafka.apache.org/documentation/#kraft)
- [Multi-Tenancy](https://kafka.apache.org/documentation/#multitenancy)
