# Grafana — Visualização de Métricas e Logs

## O que é o Grafana?

**Grafana** é a principal plataforma open-source de **visualização e análise de dados de observabilidade**.
Ela conecta múltiplas fontes de dados — Prometheus, Loki, Tempo, Elasticsearch, SQL — e permite
criar dashboards interativos, configurar alertas e correlacionar logs, métricas e traces em uma
única interface.

## Fontes de Dados (Data Sources) para .NET

| Data Source | O que armazena | Protocolo |
|-------------|---------------|-----------|
| **Prometheus** | Métricas numéricas (counters, gauges, histograms) | HTTP pull (scraping) |
| **Loki** | Logs estruturados | HTTP push/pull |
| **Tempo** | Traces distribuídos | OTLP/gRPC |
| **Elasticsearch** | Logs, métricas e documentos | HTTP |
| **Azure Monitor** | Métricas e logs Azure | API Azure |
| **SQL** | Dados de banco relacional | JDBC |

### Stack recomendada para .NET (Grafana OSS)

```
Aplicação .NET
  │
  ├── Logs ─────────────► Loki ──────────────────► Grafana
  ├── Métricas ─────────► Prometheus (scraping) ──► Grafana
  └── Traces ──────────► Tempo ─────────────────► Grafana
```

## Grafana Loki — Logs

**Loki** é o agregador de logs do ecossistema Grafana. Diferente do Elasticsearch, ele não indexa
o conteúdo dos logs (apenas os **labels**), tornando-o muito mais econômico em armazenamento.

### Enviando logs do .NET para o Loki

```bash
dotnet add package Serilog.Sinks.Grafana.Loki
```

```csharp
Log.Logger = new LoggerConfiguration()
    .Enrich.FromLogContext()
    .Enrich.WithProperty("Application", "OrderService")
    .WriteTo.GrafanaLoki("http://loki:3100",
        labels: new List<LokiLabel>
        {
            new() { Key = "app", Value = "order-service" },
            new() { Key = "env", Value = Environment.GetEnvironmentVariable("ASPNETCORE_ENVIRONMENT") ?? "Production" }
        },
        propertiesAsLabels: new[] { "Level" })
    .CreateLogger();
```

### Via OpenTelemetry + OTel Collector

```csharp
// No Program.cs — envia logs via OTLP para o OTel Collector, que repassa ao Loki
builder.Logging.AddOpenTelemetry(logging =>
{
    logging.AddOtlpExporter(opts => opts.Endpoint = new Uri("http://otel-collector:4317"));
});
```

### LogQL — Consultando logs no Loki

```logql
# Todos os logs do serviço order-service
{app="order-service"}

# Filtrar por nível de log
{app="order-service"} | json | level="Error"

# Filtrar por texto
{app="order-service"} |= "Falha ao processar"

# Extrair campos e filtrar
{app="order-service"} | json | orderId="1234"

# Taxa de logs de erro por minuto
sum(rate({app="order-service"} | json | level="Error" [1m]))

# Logs de múltiplos serviços
{app=~"order-service|payment-service"} | json | level="Error"
```

## Grafana Tempo — Traces

**Tempo** é o backend de traces distribuídos do ecossistema Grafana. Ele recebe traces via OTLP
e os armazena de forma eficiente para consulta por TraceId.

### Configurando o Tempo

```yaml
# tempo.yaml
server:
  http_listen_port: 3200

distributor:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: 0.0.0.0:4317

storage:
  trace:
    backend: local
    local:
      path: /tmp/tempo/blocks

query_frontend:
  search:
    default_result_limit: 20
```

### TraceQL — Consultando traces no Tempo

```traceql
# Traces com duração > 1 segundo
{ duration > 1s }

# Traces com erro
{ status = error }

# Spans do serviço OrderService com erro
{ resource.service.name = "OrderService" && status = error }

# Traces que passaram pelo span CreateOrder com duração > 500ms
{ name = "CreateOrder" && duration > 500ms }
```

## Criando Dashboards no Grafana

### Estrutura de um Dashboard

```
Dashboard: Order Service Overview
├── Row: Disponibilidade
│   ├── Panel: Taxa de Sucesso (gauge)
│   └── Panel: Uptime (stat)
├── Row: Performance
│   ├── Panel: Latência P50/P95/P99 (time series)
│   ├── Panel: Requisições por segundo (time series)
│   └── Panel: Distribuição de latência (heatmap)
└── Row: Erros
    ├── Panel: Taxa de erros (time series)
    └── Panel: Últimos erros (logs panel — Loki)
```

### Exemplos de Panels com PromQL

```promql
# Panel: Requisições por segundo
sum(rate(http_server_request_duration_seconds_count[1m])) by (route)

# Panel: Latência P95
histogram_quantile(0.95,
  sum by (le, route) (
    rate(http_server_request_duration_seconds_bucket[5m])
  )
)

# Panel: Taxa de erros
(
  sum(rate(http_server_request_duration_seconds_count{status_code=~"5.."}[5m]))
  /
  sum(rate(http_server_request_duration_seconds_count[5m]))
) * 100

# Panel: Uso de memória .NET
process_working_set_bytes{job="order-service"} / 1024 / 1024
```

## Alertas no Grafana

O Grafana tem seu próprio sistema de alertas (Grafana Alerting) unificado para todas as data sources:

```yaml
# Exemplo de alerta via YAML (Grafana provisioning)
apiVersion: 1
groups:
  - orgId: 1
    name: order-service
    folder: MinhaApp
    interval: 1m
    rules:
      - uid: error-rate-alert
        title: Taxa de erros alta
        condition: C
        data:
          - refId: A
            queryType: ''
            relativeTimeRange:
              from: 300
              to: 0
            datasourceUid: prometheus
            model:
              expr: |
                sum(rate(http_server_request_duration_seconds_count{status_code=~"5.."}[5m]))
                /
                sum(rate(http_server_request_duration_seconds_count[5m]))
        noDataState: NoData
        execErrState: Error
        for: 2m
        annotations:
          summary: Taxa de erros HTTP acima de 5%
        labels:
          severity: critical
```

## Correlação entre Logs, Métricas e Traces

O grande diferencial do Grafana é a **correlação entre os três pilares**:

1. No dashboard de métricas, você vê um pico de erros às 14h30
2. Clica no ponto do gráfico → abre o Loki com os logs daquele período
3. Encontra o log de erro com o `traceId`
4. Clica no `traceId` → abre o Tempo com o trace completo
5. Vê que o span `PaymentService.Charge` demorou 8s (timeout)

Isso é possível configurando **derived fields** no Loki:

```json
{
  "derivedFields": [
    {
      "matcherRegex": "traceId=(\\w+)",
      "name": "TraceID",
      "url": "${__value.raw}",
      "datasourceUid": "tempo"
    }
  ]
}
```

## Docker Compose — Stack Completa

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    ports: ["9090:9090"]
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  loki:
    image: grafana/loki:latest
    ports: ["3100:3100"]

  tempo:
    image: grafana/tempo:latest
    ports: ["3200:3200", "4317:4317"]
    volumes:
      - ./tempo.yaml:/etc/tempo.yaml
    command: -config.file=/etc/tempo.yaml

  grafana:
    image: grafana/grafana:latest
    ports: ["3000:3000"]
    environment:
      - GF_AUTH_ANONYMOUS_ENABLED=true
      - GF_AUTH_ANONYMOUS_ORG_ROLE=Admin
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning
```

## Próximo passo

[08-elastic-stack.md](08-elastic-stack.md) — Elastic Stack (ELK) para busca e análise de logs.

## Referências

- [Grafana — Documentação oficial](https://grafana.com/docs/)
- [Grafana Loki](https://grafana.com/docs/loki/latest/)
- [Grafana Tempo](https://grafana.com/docs/tempo/latest/)
- [LogQL — Referência](https://grafana.com/docs/loki/latest/query/)
- [Serilog.Sinks.Grafana.Loki](https://github.com/mishamyte/serilog-sinks-grafana-loki)
