# Introdução a Logs e Monitoramento

## O que são logs?

**Logs** são registros sequenciais de eventos que ocorrem durante a execução de uma aplicação.
Eles descrevem o que aconteceu, quando aconteceu e, idealmente, por quê aconteceu.

Exemplos de eventos que geram logs:

- Uma requisição HTTP chegou e foi processada
- Um erro ocorreu ao tentar conectar ao banco de dados
- Um usuário realizou login com sucesso
- Uma mensagem foi publicada em uma fila
- Uma regra de negócio impediu uma operação

## O que é Observabilidade?

**Observabilidade** é a capacidade de entender o estado interno de um sistema a partir de suas
saídas externas. No contexto de aplicações, ela é sustentada por três pilares:

| Pilar | O que responde | Exemplo |
|-------|---------------|---------|
| **Logs** | O que aconteceu? | "Erro ao processar pagamento: timeout" |
| **Métricas** | Quanto/com que frequência? | "Latência média: 230ms, 98% dos requests < 500ms" |
| **Rastreamento (Traces)** | Onde aconteceu e qual o caminho? | Request percorreu: API → OrderService → DB → PaymentService |

Esses três pilares juntos formam o que chamamos de **telemetria**.

## Por que monitorar aplicações?

Sem monitoramento, você opera no escuro. Com monitoramento bem configurado você consegue:

- **Detectar falhas rapidamente** antes que os usuários reportem
- **Diagnosticar a causa raiz** de problemas em produção
- **Entender o comportamento** da aplicação sob carga real
- **Medir SLAs e SLOs** (disponibilidade, tempo de resposta)
- **Auditar operações** críticas (acesso a dados, transações)
- **Planejar capacidade** com base em uso real

## Ecossistema .NET para Observabilidade

O .NET oferece um ecossistema robusto e bem integrado:

```
┌─────────────────────────────────────────────────────────┐
│                    Sua Aplicação .NET                    │
│                                                         │
│  Microsoft.Extensions.Logging  ←──── ILogger<T>         │
│  System.Diagnostics.Activity   ←──── Traces             │
│  System.Diagnostics.Metrics    ←──── Métricas           │
└────────────────────┬────────────────────────────────────┘
                     │
          ┌──────────▼──────────┐
          │    OpenTelemetry    │  ← padrão aberto
          └──────────┬──────────┘
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
   Prometheus    Jaeger/Tempo   Loki/Elastic
   (métricas)    (traces)       (logs)
       │             │             │
       └─────────────▼─────────────┘
                  Grafana
              (visualização)
```

## Próximo passo

[02-niveis-e-conceitos.md](02-niveis-e-conceitos.md) — Níveis de log, structured logging, traces e métricas.

## Referências

- [Microsoft Docs — Observability in .NET](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/observability-with-otel)
- [OpenTelemetry — Three pillars of observability](https://opentelemetry.io/docs/concepts/observability-primer/)
