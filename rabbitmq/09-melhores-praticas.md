# Melhores práticas

Este documento resume **melhores práticas** para usar o RabbitMQ em produção, com base na documentação oficial e em guias de implantação.

## Conexões e canais

- **Reutilize conexões**: abra uma conexão por aplicação (ou por processo) e mantenha-a aberta; não abra uma conexão por mensagem.
- **Use um canal por thread**: canais não são thread-safe; use um canal por thread ou por fluxo de trabalho. Múltiplos canais na mesma conexão são baratos.
- **Feche canais e conexões de forma graciosa** ao encerrar; evite derrubar apenas o TCP.

## Durabilidade e persistência

- **Produção**: use **queues durable** e **exchanges durable** para sobreviver a reinício do broker.
- **Mensagens**: publique com **delivery mode persistent** quando não puder perder mensagens; apenas queue durable não persiste o corpo da mensagem.
- Para **alta disponibilidade** das filas, use **quorum queues** (replicadas por Raft) em cluster com pelo menos 3 nós.

## Acknowledgements e confirmações

- **Consumer**: use **manual ack** (não auto ack). Envie o ack **apenas após** processar com sucesso (e persistir se necessário), para garantir at-least-once.
- **Publisher**: use **publisher confirms** quando a perda de mensagem no caminho até o broker for inaceitável. Trate nack e timeouts com retry ou dead letter.
- **Prefetch**: defina um **prefetch count** razoável (ex.: 10–50) para balancear carga entre consumers e evitar acúmulo em um único consumer.

## Filas e roteamento

- **Mantenha filas curtas**: filas que crescem sem parar indicam consumers insuficientes ou lentos; ajuste prefetch, escale consumers ou otimize o processamento.
- **Dead letter queue (DLQ)**: use para mensagens que falham após N tentativas; evita requeue infinito e permite inspeção e retry manual.
- **TTL (time-to-live)**: considere TTL por mensagem ou por queue para evitar acúmulo de mensagens obsoletas.

## Topologia

- **Declare queues e exchanges de forma idempotente**: use sempre os mesmos parâmetros ao declarar; conflitos (parâmetros diferentes em queue existente) geram erro. Preferir que a aplicação declare o que precisa ao iniciar.
- **Default exchange**: use para “publicar direto na fila” em cenários simples; para roteamento mais rico, declare exchanges específicos (direct, topic, fanout) e bindings.

## Monitoramento e operações

- **Management plugin**: habilite o plugin de management (HTTP API + UI) para inspecionar queues, conexões, throughput e mensagens.
- **Alertas**: monitore profundidade das filas (ready + unacked), taxa de publish/consume e conexões. Filas crescendo ou consumers desconectando podem indicar problemas.
- **Quorum queues**: em clusters, monitore nós do cluster e réplicas das quorum queues; perda de quorum implica indisponibilidade da queue.

## Resumo

| Área | Prática |
|------|---------|
| Conexões | Uma conexão por processo; vários canais; um canal por thread |
| Durabilidade | Queues e exchanges durable; mensagens persistent; quorum queues para HA |
| Acks | Manual ack no consumer; publisher confirms no publisher |
| Prefetch | Valor moderado (10–50) para balanceamento |
| Filas | DLQ para falhas; TTL quando fizer sentido; manter filas curtas |
| Topologia | Declaração idempotente; exchanges específicos para roteamento complexo |
| Ops | Management plugin; alertas em profundidade e throughput |

## Referências

- [Production Checklist — RabbitMQ](https://www.rabbitmq.com/docs/production-checklist)
- [Queues — Durability](https://www.rabbitmq.com/docs/queues#durability)
- [Consumer Acknowledgements and Publisher Confirms](https://www.rabbitmq.com/docs/confirms)
- [Monitoring](https://www.rabbitmq.com/docs/monitoring)
