# Log compaction e quotas

## Log compaction

Além da retenção por **tempo** ou **tamanho** (descarte do log antigo), o Kafka oferece **log compaction** para tópicos onde o que importa é manter a **última versão por chave**.

### Para que serve

- **Changelog / estado**: por exemplo, um tópico com alterações de email por usuário (chave = user id). Com compaction, o log mantém apenas o último valor por chave; um consumer pode reconstruir o estado atual relendo o tópico.
- **Event sourcing**, **caches**, **sincronização com banco**: o tópico compactado funciona como um “snapshot” mais recente por chave, sem precisar reter todo o histórico.

### Como funciona

- O **head** do log (segmentos ativos / mais recentes) permanece como um log normal: todos os records, offsets sequenciais.
- O **tail** (parte mais antiga) pode ser **compactado**: para cada chave, mantém apenas o record mais recente (pelo offset). O offset do record não muda; apenas records “antigos” para a mesma chave são removidos.
- **Deletes**: um record com **valor nulo** (tombstone) indica deleção daquela chave. Os records anteriores com essa chave são removidos na compaction; o tombstone pode ser removido após um tempo (`delete.retention.ms`) para liberar espaço.

A compactação é feita em background por threads do broker; não bloqueia leituras e pode ser limitada em I/O.

### Garantias

- Quem lê do início vê pelo menos o estado final de cada chave na ordem em que foram escritos; tombstones são visíveis dentro da janela de retenção de deletes.
- Offsets são estáveis; a ordem dos records não é alterada, apenas alguns são removidos.
- Records no head (recém-escritos) não são compactados antes do tempo definido por `min.compaction.lag.ms` (e opcionalmente `max.compaction.lag.ms`).

Para ativar em um tópico: `log.cleanup.policy=compact`.

## Quotas

O cluster pode aplicar **quotas** aos clientes para limitar uso de recursos e evitar que um cliente mal configurado prejudique os demais (multi-tenant).

### Tipos

1. **Request rate (CPU)**: percentual de utilização dos threads de I/O e de rede do broker por grupo de clientes (por janela de quota).
2. **Network bandwidth**: taxa em bytes/segundo por grupo de clientes (por broker).

### Grupos de clientes

A identidade é definida por **user** (principal de autenticação) e **client-id** (escolhido pela aplicação). Quotas podem ser configuradas por `(user, client-id)`, por `user` ou por `client-id`. Aplica-se a quota mais específica para a conexão.

### Aplicação

Quando um cliente excede a quota, o broker calcula um **delay** e devolve a resposta com esse delay; o canal fica “mudo” até o delay acabar. O cliente também deve deixar de enviar requisições durante o delay. Assim o broker impõe backpressure mesmo a clientes antigos que não entendem o campo de delay.

As métricas de quota são feitas em janelas pequenas (ex.: várias janelas de 1 segundo) para reagir rápido e evitar longos períodos de throttle após um pico.

## Referências

- [Log Compaction — Apache Kafka](https://kafka.apache.org/documentation/#design_compaction)
- [Quotas — Design](https://kafka.apache.org/documentation/#design_quotas)
- [Broker configs (cleanup, compaction)](https://kafka.apache.org/documentation/#brokerconfigs)
