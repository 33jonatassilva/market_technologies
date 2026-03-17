# Exemplos Práticos — Observabilidade Completa em .NET

Este documento demonstra como combinar todas as ferramentas apresentadas para montar uma stack
de observabilidade completa em uma aplicação ASP.NET Core.

## Cenário: API de Pedidos com Stack Completa

Vamos configurar um `OrderService` com:

- **Serilog** → logs estruturados enviados ao **Loki**
- **OpenTelemetry** → traces enviados ao **Tempo**, métricas ao **Prometheus**
- **Grafana** → dashboards unificando os três pilares
- **Health Checks** → disponibilidade monitorada pelo Prometheus

## 1. Pacotes NuGet

```xml
<!-- MinhaApp.OrderService.csproj -->
<ItemGroup>
  <!-- Logging -->
  <PackageReference Include="Serilog.AspNetCore" Version="8.*" />
  <PackageReference Include="Serilog.Sinks.Grafana.Loki" Version="8.*" />
  <PackageReference Include="Serilog.Enrichers.Environment" Version="2.*" />
  <PackageReference Include="Serilog.Enrichers.Thread" Version="3.*" />

  <!-- OpenTelemetry -->
  <PackageReference Include="OpenTelemetry.Extensions.Hosting" Version="1.*" />
  <PackageReference Include="OpenTelemetry.Instrumentation.AspNetCore" Version="1.*" />
  <PackageReference Include="OpenTelemetry.Instrumentation.Http" Version="1.*" />
  <PackageReference Include="OpenTelemetry.Instrumentation.EntityFrameworkCore" Version="1.*" />
  <PackageReference Include="OpenTelemetry.Instrumentation.Runtime" Version="1.*" />
  <PackageReference Include="OpenTelemetry.Exporter.Prometheus.AspNetCore" Version="1.*-rc.*" />
  <PackageReference Include="OpenTelemetry.Exporter.OpenTelemetryProtocol" Version="1.*" />

  <!-- Health Checks -->
  <PackageReference Include="AspNetCore.HealthChecks.NpgSql" Version="8.*" />
  <PackageReference Include="AspNetCore.HealthChecks.Redis" Version="8.*" />
  <PackageReference Include="AspNetCore.HealthChecks.Publisher.Prometheus" Version="8.*" />
</ItemGroup>
```

## 2. Program.cs — Configuração Completa

```csharp
using Serilog;
using Serilog.Events;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;
using OpenTelemetry.Metrics;
using OpenTelemetry.Logs;

// ───── Serilog (bootstrap antes do WebApplication) ─────
Log.Logger = new LoggerConfiguration()
    .MinimumLevel.Override("Microsoft", LogEventLevel.Warning)
    .MinimumLevel.Override("Microsoft.EntityFrameworkCore.Database.Command", LogEventLevel.Information)
    .Enrich.FromLogContext()
    .Enrich.WithMachineName()
    .Enrich.WithThreadId()
    .Enrich.WithEnvironmentName()
    .WriteTo.Console(outputTemplate:
        "[{Timestamp:HH:mm:ss} {Level:u3}] {Message:lj} {Properties:j}{NewLine}{Exception}")
    .CreateBootstrapLogger();

try
{
    var builder = WebApplication.CreateBuilder(args);

    // ───── Serilog (integrado ao host) ─────
    builder.Host.UseSerilog((context, services, config) =>
        config
            .ReadFrom.Configuration(context.Configuration)
            .ReadFrom.Services(services)
            .Enrich.FromLogContext()
            .WriteTo.Console()
            .WriteTo.GrafanaLoki(
                context.Configuration["Observability:LokiUrl"]!,
                labels: new List<LokiLabel>
                {
                    new() { Key = "app", Value = "order-service" },
                    new() { Key = "env", Value = context.HostingEnvironment.EnvironmentName }
                }));

    // ───── Resource OTel compartilhado ─────
    var resourceBuilder = ResourceBuilder.CreateDefault()
        .AddService(
            serviceName: "OrderService",
            serviceVersion: builder.Configuration["App:Version"] ?? "1.0.0")
        .AddAttributes(new Dictionary<string, object>
        {
            ["deployment.environment"] = builder.Environment.EnvironmentName,
            ["host.name"] = Environment.MachineName
        });

    // ───── OpenTelemetry ─────
    builder.Services.AddOpenTelemetry()
        .WithTracing(tracing => tracing
            .SetResourceBuilder(resourceBuilder)
            .AddAspNetCoreInstrumentation(opts =>
            {
                opts.RecordException = true;
                opts.Filter = ctx => !ctx.Request.Path.StartsWithSegments("/health")
                                  && !ctx.Request.Path.StartsWithSegments("/metrics");
            })
            .AddHttpClientInstrumentation(opts => opts.RecordException = true)
            .AddEntityFrameworkCoreInstrumentation(opts => opts.SetDbStatementForText = true)
            .AddSource("MinhaApp.OrderService")
            .AddOtlpExporter(opts =>
                opts.Endpoint = new Uri(builder.Configuration["Observability:TempoUrl"]!)))

        .WithMetrics(metrics => metrics
            .SetResourceBuilder(resourceBuilder)
            .AddAspNetCoreInstrumentation()
            .AddHttpClientInstrumentation()
            .AddRuntimeInstrumentation()
            .AddMeter("MinhaApp.OrderService")
            .AddPrometheusExporter());

    // ───── Health Checks ─────
    builder.Services.AddHealthChecks()
        .AddNpgSql(
            builder.Configuration.GetConnectionString("DefaultConnection")!,
            name: "postgres",
            tags: new[] { "db", "ready" })
        .AddRedis(
            builder.Configuration["Redis:ConnectionString"]!,
            name: "redis",
            tags: new[] { "cache", "ready" })
        .AddCheck<OrderQueueHealthCheck>(
            "order-queue",
            tags: new[] { "queue", "ready" });

    builder.Services.Configure<HealthCheckPublisherOptions>(opts =>
        opts.Period = TimeSpan.FromSeconds(30));
    builder.Services.AddSingleton<IHealthCheckPublisher, PrometheusHealthCheckPublisher>();

    // ───── Serviços da aplicação ─────
    builder.Services.AddScoped<OrderService>();
    builder.Services.AddSingleton<OrderMetrics>();
    builder.Services.AddControllers();

    var app = builder.Build();

    app.UseSerilogRequestLogging(opts =>
    {
        opts.MessageTemplate = "HTTP {RequestMethod} {RequestPath} {StatusCode} em {Elapsed:0.000}ms";
        opts.EnrichDiagnosticContext = (diag, http) =>
        {
            diag.Set("RequestHost", http.Request.Host.Value);
            diag.Set("UserId", http.User.FindFirst("sub")?.Value ?? "anonymous");
        };
        opts.GetLevel = (ctx, elapsed, ex) =>
            ex != null || ctx.Response.StatusCode >= 500
                ? LogEventLevel.Error
                : elapsed > 1000
                    ? LogEventLevel.Warning
                    : LogEventLevel.Information;
    });

    app.MapControllers();
    app.MapPrometheusScrapingEndpoint("/metrics");
    app.MapHealthChecks("/health/live", new HealthCheckOptions { Predicate = _ => false });
    app.MapHealthChecks("/health/ready", new HealthCheckOptions
    {
        Predicate = c => c.Tags.Contains("ready"),
        ResponseWriter = WriteDetailedHealthResponse
    });

    Log.Information("OrderService iniciado. Ambiente: {Environment}", app.Environment.EnvironmentName);
    await app.RunAsync();
}
catch (Exception ex)
{
    Log.Fatal(ex, "Aplicação encerrada inesperadamente");
}
finally
{
    await Log.CloseAndFlushAsync();
}
```

## 3. OrderService — Instrumentação de Negócio

```csharp
public class OrderService
{
    private static readonly ActivitySource ActivitySource = new("MinhaApp.OrderService");

    private readonly IOrderRepository _repository;
    private readonly ILogger<OrderService> _logger;
    private readonly OrderMetrics _metrics;

    public OrderService(IOrderRepository repository, ILogger<OrderService> logger, OrderMetrics metrics)
    {
        _repository = repository;
        _logger = logger;
        _metrics = metrics;
    }

    public async Task<Order> CreateOrderAsync(CreateOrderRequest request, CancellationToken ct = default)
    {
        using var activity = ActivitySource.StartActivity("CreateOrder");
        activity?.SetTag("order.customer_id", request.CustomerId);
        activity?.SetTag("order.item_count", request.Items.Count);

        using var scope = _logger.BeginScope(new Dictionary<string, object>
        {
            ["CustomerId"] = request.CustomerId,
            ["CorrelationId"] = Activity.Current?.TraceId.ToString() ?? Guid.NewGuid().ToString()
        });

        _logger.LogInformation("Iniciando criação de pedido com {ItemCount} itens", request.Items.Count);

        var stopwatch = Stopwatch.StartNew();

        try
        {
            var order = await _repository.SaveAsync(request, ct);

            stopwatch.Stop();
            _metrics.RecordOrderCreated(request.PaymentMethod, stopwatch.Elapsed.TotalMilliseconds);

            activity?.SetTag("order.id", order.Id);
            activity?.SetStatus(ActivityStatusCode.Ok);

            _logger.LogInformation("Pedido {OrderId} criado com sucesso em {ElapsedMs}ms",
                order.Id, stopwatch.ElapsedMilliseconds);

            return order;
        }
        catch (Exception ex)
        {
            stopwatch.Stop();
            _metrics.RecordOrderFailed(ex.GetType().Name);

            activity?.SetStatus(ActivityStatusCode.Error, ex.Message);
            activity?.RecordException(ex);

            _logger.LogError(ex, "Falha ao criar pedido para cliente {CustomerId} após {ElapsedMs}ms",
                request.CustomerId, stopwatch.ElapsedMilliseconds);

            throw;
        }
    }
}
```

## 4. Métricas de Negócio

```csharp
public class OrderMetrics
{
    private readonly Counter<long> _ordersCreated;
    private readonly Counter<long> _ordersFailed;
    private readonly Histogram<double> _processingDuration;

    public OrderMetrics(IMeterFactory meterFactory)
    {
        var meter = meterFactory.Create("MinhaApp.OrderService");

        _ordersCreated = meter.CreateCounter<long>(
            "orders_created_total", "orders", "Total de pedidos criados por método de pagamento");

        _ordersFailed = meter.CreateCounter<long>(
            "orders_failed_total", "orders", "Total de pedidos com falha por tipo de erro");

        _processingDuration = meter.CreateHistogram<double>(
            "orders_processing_duration_ms", "ms", "Duração do processamento de pedidos");
    }

    public void RecordOrderCreated(string paymentMethod, double durationMs)
    {
        _ordersCreated.Add(1, new KeyValuePair<string, object?>("payment_method", paymentMethod));
        _processingDuration.Record(durationMs, new KeyValuePair<string, object?>("status", "success"));
    }

    public void RecordOrderFailed(string errorType)
    {
        _ordersFailed.Add(1, new KeyValuePair<string, object?>("error_type", errorType));
    }
}
```

## 5. Docker Compose — Stack Completa

```yaml
# docker-compose.yml
services:

  order-service:
    build: .
    ports: ["8080:8080"]
    environment:
      - ASPNETCORE_ENVIRONMENT=Production
      - ConnectionStrings__DefaultConnection=Host=postgres;Database=orders;Username=app;Password=secret
      - Redis__ConnectionString=redis:6379
      - Observability__LokiUrl=http://loki:3100
      - Observability__TempoUrl=http://tempo:4317
    depends_on: [postgres, redis, loki, tempo]

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: orders
      POSTGRES_USER: app
      POSTGRES_PASSWORD: secret

  redis:
    image: redis:7-alpine

  prometheus:
    image: prom/prometheus:latest
    ports: ["9090:9090"]
    volumes:
      - ./infra/prometheus.yml:/etc/prometheus/prometheus.yml
    command: >
      --config.file=/etc/prometheus/prometheus.yml
      --web.enable-lifecycle

  loki:
    image: grafana/loki:latest
    ports: ["3100:3100"]
    command: -config.file=/etc/loki/local-config.yaml

  tempo:
    image: grafana/tempo:latest
    ports: ["3200:3200", "4317:4317"]
    command: -config.file=/etc/tempo/tempo.yaml
    volumes:
      - ./infra/tempo.yaml:/etc/tempo/tempo.yaml

  grafana:
    image: grafana/grafana:latest
    ports: ["3000:3000"]
    environment:
      - GF_AUTH_ANONYMOUS_ENABLED=true
      - GF_AUTH_ANONYMOUS_ORG_ROLE=Admin
    volumes:
      - ./infra/grafana/provisioning:/etc/grafana/provisioning
    depends_on: [prometheus, loki, tempo]
```

## 6. prometheus.yml

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: order-service
    static_configs:
      - targets: ['order-service:8080']
    metrics_path: /metrics
```

## 7. Provisioning Grafana — Data Sources

```yaml
# infra/grafana/provisioning/datasources/datasources.yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    url: http://prometheus:9090
    isDefault: true

  - name: Loki
    type: loki
    url: http://loki:3100
    jsonData:
      derivedFields:
        - matcherRegex: '"TraceId":"(\w+)"'
          name: TraceID
          url: '$${__value.raw}'
          datasourceUid: tempo

  - name: Tempo
    type: tempo
    url: http://tempo:3200
    jsonData:
      tracesToLogsV2:
        datasourceUid: loki
        filterByTraceID: true
      serviceMap:
        datasourceUid: prometheus
```

## 8. Queries Grafana Úteis

```promql
# Taxa de criação de pedidos por segundo
rate(orders_created_total[1m])

# P95 de tempo de processamento de pedidos
histogram_quantile(0.95, rate(orders_processing_duration_ms_bucket[5m]))

# Taxa de falha de pedidos
sum(rate(orders_failed_total[5m])) by (error_type)

# Disponibilidade da aplicação (health checks)
health_check_status{check="postgres"}
```

```logql
# Logs de erro do order-service (Loki)
{app="order-service"} | json | level="Error"

# Logs de pedidos falhos com detalhes
{app="order-service"} | json | level="Error" | line_format "{{.message}} — Customer: {{.CustomerId}}"
```

## Referências

- [OpenTelemetry .NET — Getting started](https://opentelemetry.io/docs/languages/dotnet/getting-started/)
- [Grafana — Correlate logs and traces](https://grafana.com/docs/grafana/latest/datasources/tempo/configure-tempo-data-source/)
- [Serilog — Best practices](https://github.com/serilog/serilog/wiki/Writing-Log-Events)
- [Microsoft Docs — Observability in .NET microservices](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/implement-resilient-applications/monitor-app-health)
