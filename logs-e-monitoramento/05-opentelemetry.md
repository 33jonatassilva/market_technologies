# OpenTelemetry — Padrão Aberto para Observabilidade em .NET

## O que é OpenTelemetry?

**OpenTelemetry (OTel)** é um projeto open-source da CNCF (Cloud Native Computing Foundation) que
padroniza a coleta de telemetria — logs, métricas e traces — independente de vendor. Ele resolve
o problema de lock-in: você instrumenta sua aplicação uma vez e decide depois para onde enviar os dados.

Antes do OTel, cada plataforma (Datadog, New Relic, Jaeger) exigia seu próprio SDK de instrumentação.
Com OTel, você usa um único SDK e exporta para qualquer destino via **exporters**.

```
Sua Aplicação .NET
     │
     │ OpenTelemetry SDK
     ▼
┌─────────────────────────────────┐
│     OTel Collector (opcional)   │
└──────────┬──────────────────────┘
           │
    ┌──────┼──────┐
    ▼      ▼      ▼
 Jaeger  Grafana Datadog
(traces)(metrics)(tudo)
```

## Instalação dos Pacotes

```bash
# Core
dotnet add package OpenTelemetry
dotnet add package OpenTelemetry.Extensions.Hosting

# Instrumentação automática ASP.NET Core
dotnet add package OpenTelemetry.Instrumentation.AspNetCore
dotnet add package OpenTelemetry.Instrumentation.Http
dotnet add package OpenTelemetry.Instrumentation.EntityFrameworkCore

# Exporters
dotnet add package OpenTelemetry.Exporter.Console          # desenvolvimento
dotnet add package OpenTelemetry.Exporter.Prometheus.AspNetCore  # Prometheus
dotnet add package OpenTelemetry.Exporter.OpenTelemetryProtocol  # OTLP (Jaeger, Grafana, etc.)
```

## Configuração no Program.cs

```csharp
using OpenTelemetry.Logs;
using OpenTelemetry.Metrics;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;

var builder = WebApplication.CreateBuilder(args);

// Recurso compartilhado — identifica a aplicação
var resourceBuilder = ResourceBuilder.CreateDefault()
    .AddService(serviceName: "OrderService", serviceVersion: "1.0.0")
    .AddAttributes(new Dictionary<string, object>
    {
        ["deployment.environment"] = builder.Environment.EnvironmentName
    });

// Traces
builder.Services.AddOpenTelemetry()
    .WithTracing(tracing => tracing
        .SetResourceBuilder(resourceBuilder)
        .AddAspNetCoreInstrumentation(opts =>
        {
            opts.RecordException = true;
            opts.Filter = ctx => !ctx.Request.Path.StartsWithSegments("/health");
        })
        .AddHttpClientInstrumentation()
        .AddEntityFrameworkCoreInstrumentation()
        .AddSource("MinhaApp.*")  // registra ActivitySources customizados
        .AddOtlpExporter(opts => opts.Endpoint = new Uri("http://jaeger:4317"))
    )

// Métricas
    .WithMetrics(metrics => metrics
        .SetResourceBuilder(resourceBuilder)
        .AddAspNetCoreInstrumentation()
        .AddHttpClientInstrumentation()
        .AddRuntimeInstrumentation()    // métricas da CLR (GC, threads, etc.)
        .AddMeter("MinhaApp.*")          // meters customizados
        .AddPrometheusExporter()         // expõe /metrics para o Prometheus
    );

// Logs via OTel (integra com ILogger)
builder.Logging.AddOpenTelemetry(logging =>
{
    logging.SetResourceBuilder(resourceBuilder);
    logging.AddOtlpExporter(opts => opts.Endpoint = new Uri("http://loki:4317"));
    logging.IncludeFormattedMessage = true;
    logging.IncludeScopes = true;
});
```

## Instrumentação Manual — Traces

Além da instrumentação automática (HTTP, EF Core), você pode criar spans manuais para operações de negócio:

```csharp
public class OrderService
{
    private static readonly ActivitySource ActivitySource = new("MinhaApp.OrderService");

    public async Task<Order> CreateOrderAsync(CreateOrderRequest request)
    {
        // Cria um span filho do span atual (propagação automática de contexto)
        using var activity = ActivitySource.StartActivity("CreateOrder");

        // Tags — metadados do span (baixa cardinalidade)
        activity?.SetTag("order.customer_id", request.CustomerId);
        activity?.SetTag("order.item_count", request.Items.Count);

        try
        {
            var order = await _repository.SaveAsync(request);

            // Adiciona evento dentro do span
            activity?.AddEvent(new ActivityEvent("OrderSaved",
                tags: new ActivityTagsCollection { ["order.id"] = order.Id }));

            activity?.SetStatus(ActivityStatusCode.Ok);
            return order;
        }
        catch (Exception ex)
        {
            activity?.SetStatus(ActivityStatusCode.Error, ex.Message);
            activity?.RecordException(ex);
            throw;
        }
    }
}
```

## Instrumentação Manual — Métricas

```csharp
public class OrderMetrics
{
    private readonly Counter<long> _ordersCreated;
    private readonly Counter<long> _ordersFailed;
    private readonly Histogram<double> _orderProcessingDuration;
    private readonly UpDownCounter<int> _activeOrders;

    public OrderMetrics(IMeterFactory meterFactory)
    {
        var meter = meterFactory.Create("MinhaApp.OrderService");

        _ordersCreated = meter.CreateCounter<long>(
            "orders.created.total",
            unit: "orders",
            description: "Total de pedidos criados");

        _ordersFailed = meter.CreateCounter<long>(
            "orders.failed.total",
            unit: "orders",
            description: "Total de pedidos com falha");

        _orderProcessingDuration = meter.CreateHistogram<double>(
            "orders.processing.duration",
            unit: "ms",
            description: "Duração do processamento de pedidos");

        _activeOrders = meter.CreateUpDownCounter<int>(
            "orders.active",
            unit: "orders",
            description: "Pedidos em processamento no momento");
    }

    public void RecordOrderCreated(string paymentMethod) =>
        _ordersCreated.Add(1, new KeyValuePair<string, object?>("payment.method", paymentMethod));

    public void RecordOrderFailed(string reason) =>
        _ordersFailed.Add(1, new KeyValuePair<string, object?>("failure.reason", reason));

    public void RecordProcessingDuration(double milliseconds) =>
        _orderProcessingDuration.Record(milliseconds);
}
```

## Context Propagation — Rastreamento entre Serviços

O OTel propaga automaticamente o contexto de trace entre serviços via headers HTTP:

```
GET /api/orders HTTP/1.1
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
tracestate: rojo=00f067aa0ba902b7
```

O `HttpClient` com instrumentação OTel injeta e lê esses headers automaticamente.

### Propagação manual (se necessário)

```csharp
// Ao publicar mensagem em fila, propagar o contexto
var propagator = Propagators.DefaultTextMapPropagator;
var propagationContext = new PropagationContext(Activity.Current?.Context ?? default, Baggage.Current);

var headers = new Dictionary<string, string>();
propagator.Inject(propagationContext, headers, (carrier, key, value) => carrier[key] = value);

// Ao consumir mensagem da fila, restaurar o contexto
var parentContext = propagator.Extract(default, headers, (carrier, key) =>
    carrier.TryGetValue(key, out var value) ? new[] { value } : Array.Empty<string>());

using var activity = ActivitySource.StartActivity("ConsumeMessage",
    ActivityKind.Consumer,
    parentContext.ActivityContext);
```

## OTel Collector

O **OTel Collector** é um proxy/agente que recebe telemetria via OTLP, processa e exporta:

```yaml
# otel-collector.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
  memory_limiter:
    limit_mib: 256

exporters:
  prometheus:
    endpoint: "0.0.0.0:8889"
  otlp/jaeger:
    endpoint: jaeger:4317
  loki:
    endpoint: http://loki:3100/loki/api/v1/push

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp/jaeger]
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [prometheus]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [loki]
```

## Próximo passo

[06-prometheus-e-metricas.md](06-prometheus-e-metricas.md) — Prometheus e coleta de métricas em .NET.

## Referências

- [OpenTelemetry .NET — Documentação oficial](https://opentelemetry.io/docs/languages/dotnet/)
- [OpenTelemetry .NET no GitHub](https://github.com/open-telemetry/opentelemetry-dotnet)
- [OTel Collector](https://opentelemetry.io/docs/collector/)
- [W3C TraceContext specification](https://www.w3.org/TR/trace-context/)
