# Prometheus e Coleta de Métricas em .NET

## O que é o Prometheus?

**Prometheus** é um sistema open-source de monitoramento e alerta focado em **métricas numéricas
baseadas em séries temporais**. Ele coleta métricas por **pull** (scraping) — ou seja, ele acessa
periodicamente um endpoint `/metrics` da sua aplicação e armazena os dados.

```
Sua Aplicação .NET          Prometheus              Grafana
  ┌──────────┐    scrape    ┌──────────┐   query   ┌──────────┐
  │ /metrics │ ◄──────────  │  Server  │ ─────────► │Dashboard │
  └──────────┘  a cada 15s  └──────────┘  PromQL   └──────────┘
                                  │
                            ┌─────▼──────┐
                            │ Alertmanager│
                            └────────────┘
```

## Expondo Métricas no .NET

### Via OpenTelemetry (recomendado)

```bash
dotnet add package OpenTelemetry.Exporter.Prometheus.AspNetCore
dotnet add package OpenTelemetry.Instrumentation.Runtime
```

```csharp
builder.Services.AddOpenTelemetry()
    .WithMetrics(metrics => metrics
        .AddAspNetCoreInstrumentation()   // métricas HTTP automáticas
        .AddHttpClientInstrumentation()   // métricas de HttpClient
        .AddRuntimeInstrumentation()      // GC, threads, memória CLR
        .AddMeter("MinhaApp.*")
        .AddPrometheusExporter()
    );

var app = builder.Build();
app.MapPrometheusScrapingEndpoint("/metrics");  // expõe /metrics
```

### Via prometheus-net (alternativa direta)

```bash
dotnet add package prometheus-net.AspNetCore
```

```csharp
using Prometheus;

var app = builder.Build();
app.UseMetricServer("/metrics");   // endpoint do Prometheus
app.UseHttpMetrics();              // métricas HTTP automáticas
```

## Tipos de Métricas no Prometheus

### Counter (Contador)

Valor monotonicamente crescente. Útil para totais.

```csharp
// Via OpenTelemetry
var ordersCreated = meter.CreateCounter<long>("orders_created_total",
    description: "Total de pedidos criados");

ordersCreated.Add(1, new KeyValuePair<string, object?>("status", "success"));

// Via prometheus-net
private static readonly Counter OrdersCreated = Metrics.CreateCounter(
    "orders_created_total",
    "Total de pedidos criados",
    labelNames: new[] { "status" });

OrdersCreated.WithLabels("success").Inc();
```

**No Prometheus/Grafana**: use `rate(orders_created_total[5m])` para ver a taxa por segundo.

### Gauge (Medidor)

Valor que pode subir ou descer. Útil para estado atual.

```csharp
// prometheus-net
private static readonly Gauge ActiveConnections = Metrics.CreateGauge(
    "db_connections_active",
    "Conexões ativas com o banco de dados");

ActiveConnections.Inc();   // ao abrir conexão
ActiveConnections.Dec();   // ao fechar conexão
ActiveConnections.Set(42); // valor absoluto
```

### Histogram (Histograma)

Distribui observações em buckets. Ideal para latência e tamanho de payload.

```csharp
// prometheus-net
private static readonly Histogram RequestDuration = Metrics.CreateHistogram(
    "http_request_duration_seconds",
    "Duração das requisições HTTP",
    new HistogramConfiguration
    {
        LabelNames = new[] { "method", "route", "status_code" },
        Buckets = new[] { 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5 }
    });

using (RequestDuration.WithLabels("GET", "/api/orders", "200").NewTimer())
{
    await ProcessRequestAsync();
}
```

**No Prometheus/Grafana**: use `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))` para p95.

## Métricas Automáticas do OpenTelemetry

Com `AddAspNetCoreInstrumentation()` e `AddRuntimeInstrumentation()`, você ganha automaticamente:

| Métrica | Tipo | Descrição |
|---------|------|-----------|
| `http.server.request.duration` | Histogram | Latência das requisições HTTP |
| `http.server.active_requests` | UpDownCounter | Requisições em andamento |
| `dotnet.gc.collections` | Counter | Total de coletas do GC por geração |
| `dotnet.gc.heap.total_allocated` | Counter | Bytes alocados no heap |
| `dotnet.process.cpu.time` | Counter | Tempo de CPU usado |
| `dotnet.thread_pool.queue.length` | Gauge | Tamanho da fila do ThreadPool |
| `dotnet.dns.lookups.duration` | Histogram | Duração de resoluções DNS |

## Configuração do Prometheus Server

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'order-service'
    static_configs:
      - targets: ['order-service:8080']
    metrics_path: /metrics

  - job_name: 'payment-service'
    static_configs:
      - targets: ['payment-service:8080']
    metrics_path: /metrics
```

### Service Discovery com Docker / Kubernetes

```yaml
# Kubernetes — scrape automático de pods anotados
scrape_configs:
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: "true"
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
```

## PromQL — Consultando Métricas

PromQL (Prometheus Query Language) é a linguagem de consulta do Prometheus:

```promql
# Taxa de requisições por segundo nos últimos 5 minutos
rate(http_server_request_duration_ms_count[5m])

# Percentil 95 de latência
histogram_quantile(0.95,
  sum by (le, route) (
    rate(http_server_request_duration_ms_bucket[5m])
  )
)

# Taxa de erro (status 5xx)
sum(rate(http_server_request_duration_ms_count{status_code=~"5.."}[5m]))
/
sum(rate(http_server_request_duration_ms_count[5m]))

# Uso de memória heap do .NET
dotnet_gc_heap_size_bytes{generation="loh"}

# Pedidos criados por minuto
sum(rate(orders_created_total[1m])) by (status)
```

## Alerting com Alertmanager

```yaml
# alerting-rules.yml
groups:
  - name: minhaapp
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate(http_server_request_duration_ms_count{status_code=~"5.."}[5m]))
          /
          sum(rate(http_server_request_duration_ms_count[5m])) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Taxa de erros acima de 5%"
          description: "A taxa de erros HTTP 5xx está em {{ $value | humanizePercentage }}"

      - alert: HighLatencyP95
        expr: |
          histogram_quantile(0.95,
            rate(http_server_request_duration_ms_bucket[5m])
          ) > 1000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "P95 de latência acima de 1 segundo"
```

## Próximo passo

[07-grafana.md](07-grafana.md) — Grafana para visualização de métricas e logs.

## Referências

- [Prometheus — Documentação oficial](https://prometheus.io/docs/)
- [prometheus-net no GitHub](https://github.com/prometheus-net/prometheus-net)
- [OpenTelemetry Prometheus Exporter](https://github.com/open-telemetry/opentelemetry-dotnet/blob/main/src/OpenTelemetry.Exporter.Prometheus.AspNetCore/README.md)
- [PromQL — Documentação](https://prometheus.io/docs/prometheus/latest/querying/basics/)
