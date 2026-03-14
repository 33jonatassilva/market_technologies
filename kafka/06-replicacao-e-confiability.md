# Replicação e confiabilidade

A **replicação** é o que permite ao Kafka tolerar falhas de brokers e manter os dados disponíveis.

## Líder e followers

Cada **partição** tem um **líder** (leader) e zero ou mais **followers**. O fator de replicação define quantas réplicas existem no total (incluindo o líder).

- **Escritas**: vão apenas para o **líder** da partição.
- **Leituras**: podem ser atendidas pelo líder ou por followers (dependendo da configuração).
- Os logs dos followers são idênticos ao do líder (mesmos offsets e mesma ordem); o líder pode ter algumas mensagens no final ainda não replicadas.

Os followers consomem do líder como um consumer normal e aplicam as entradas ao próprio log (modelo pull).

## In-sync replicas (ISR)

Um broker é considerado “vivo” no sentido da replicação se:

1. Está replicando as escritas do líder e não fica “muito atrás”.
2. Mantém sessão ativa com o **controller** (heartbeats no KRaft, etc.).

Esses brokers formam o conjunto **ISR** (In-Sync Replicas). Apenas réplicas no ISR podem ser eleitas líder em caso de falha.

- Uma mensagem só é **committed** quando **todas** as réplicas no ISR a receberam.
- Se um follower morre ou fica muito atrasado, é removido do ISR. O atraso é controlado por configurações como `replica.lag.time.max.ms`.

## Quorum e ISR

Em sistemas baseados em quorum, normalmente se usa voto por maioria para commit e eleição. No Kafka, em vez de “maioria fixa”, o quorum é o conjunto **dinâmico** ISR: só quem está em sync pode ser líder. Com f+1 réplicas, o tópico tolera f falhas sem perda de mensagens committed.

## Unclean leader election

Se **todas** as réplicas de uma partição caírem, não há mais garantia de que os dados committed estejam em algum broker. Nesse caso há um trade-off:

- **Esperar** uma réplica do ISR voltar → máxima consistência, mas a partição pode ficar indisponível.
- **Permitir** que uma réplica fora do ISR vire líder → a partição volta a aceitar escritas, mas pode haver perda de mensagens já committed.

Por padrão (a partir de 0.11), o Kafka **não** permite unclean leader election: prefere indisponibilidade a perda de dados. Isso pode ser alterado com `unclean.leader.election.enable` para cenários em que disponibilidade é mais importante.

## Disponibilidade e durabilidade

- **Producer**: pode escolher quantas confirmações esperar (`acks=0`, `1` ou `all`). Com `acks=all`, a confirmação ocorre quando todas as réplicas no ISR receberem a mensagem (respeitando `min.insync.replicas` no tópico).
- **Durabilidade**: para preferir durabilidade à disponibilidade, use `min.insync.replicas` maior e desabilite unclean leader election. Assim a partição só aceita escritas com ISR suficiente e não elege uma réplica atrasada como líder.

O Kafka **não** garante disponibilidade em caso de partição de rede; a garantia é que uma mensagem committed não se perde enquanto houver pelo menos uma réplica in-sync viva.

## Referências

- [Replication — Apache Kafka Design](https://kafka.apache.org/documentation/#design_replication)
- [Availability and Durability Guarantees](https://kafka.apache.org/documentation/#design_availability)
