# Health Checks no ASP.NET Core

## O que são Health Checks?

**Health Checks** são endpoints que expõem o estado de saúde de uma aplicação e suas dependências.
Eles são consumidos por:

- **Load balancers** — para remover instâncias doentes do pool de tráfego
- **Orquestradores** (Kubernetes, Docker Swarm) — para reiniciar containers com falha
- **Sistemas de monitoramento** (Prometheus, Grafana) — para alertas de disponibilidade
- **Dashboards** — para visibilidade operacional

### Tipos de Health Check

| Tipo | Propósito | Quem consome |
|------|-----------|-------------|
| **Liveness** | A aplicação está viva? Deve ser reiniciada? | Kubernetes (kubelet) |
| **Readiness** | A aplicação está pronta para receber tráfego? | Load balancer, Kubernetes |
| **Startup** | A inicialização foi concluída? | Kubernetes (startup probe) |

## Configuração Básica

```bash
dotnet add package Microsoft.AspNetCore.Diagnostics.HealthChecks
dotnet add package AspNetCore.HealthChecks.UI                    # UI visual (opcional)
dotnet add package AspNetCore.HealthChecks.SqlServer             # SQL Server
dotnet add package AspNetCore.HealthChecks.NpgSql                # PostgreSQL
dotnet add package AspNetCore.HealthChecks.Redis                 # Redis
dotnet add package AspNetCore.HealthChecks.RabbitMQ              # RabbitMQ
dotnet add package AspNetCore.HealthChecks.Kafka                 # Kafka
dotnet add package AspNetCore.HealthChecks.Uris                  # URLs externas
```

## Configurando Health Checks

```csharp
// Program.cs
builder.Services.AddHealthChecks()
    // Banco de dados
    .AddNpgSql(
        connectionString: builder.Configuration.GetConnectionString("DefaultConnection"),
        name: "database",
        tags: new[] { "db", "sql", "postgres" })

    // Redis
    .AddRedis(
        redisConnectionString: builder.Configuration["Redis:ConnectionString"],
        name: "redis",
        tags: new[] { "cache", "redis" })

    // RabbitMQ
    .AddRabbitMQ(
        rabbitConnectionString: builder.Configuration["RabbitMQ:ConnectionString"],
        name: "rabbitmq",
        tags: new[] { "messaging", "rabbitmq" })

    // Serviço externo (HTTP)
    .AddUrlGroup(
        uri: new Uri("https://api.pagamento.com/health"),
        name: "payment-api",
        tags: new[] { "external" })

    // Espaço em disco
    .AddDiskStorageHealthCheck(setup =>
        setup.AddDrive("/", minimumFreeMegabytes: 500),
        name: "disk-storage")

    // Memória
    .AddProcessAllocatedMemoryHealthCheck(
        maximumMegabytesAllocated: 512,
        name: "memory");

var app = builder.Build();

// Endpoint principal — retorna Healthy/Degraded/Unhealthy
app.MapHealthChecks("/health");

// Liveness — apenas verifica se o processo está vivo
app.MapHealthChecks("/health/live", new HealthCheckOptions
{
    Predicate = _ => false  // não executa nenhum check, apenas retorna Healthy
});

// Readiness — verifica dependências críticas
app.MapHealthChecks("/health/ready", new HealthCheckOptions
{
    Predicate = check => check.Tags.Contains("db") || check.Tags.Contains("cache")
});
```

## Health Check Customizado

Implemente `IHealthCheck` para verificações específicas de negócio:

```csharp
public class OrderQueueHealthCheck : IHealthCheck
{
    private readonly IOrderQueue _queue;
    private readonly ILogger<OrderQueueHealthCheck> _logger;

    public OrderQueueHealthCheck(IOrderQueue queue, ILogger<OrderQueueHealthCheck> logger)
    {
        _queue = queue;
        _logger = logger;
    }

    public async Task<HealthCheckResult> CheckHealthAsync(
        HealthCheckContext context,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var queueDepth = await _queue.GetDepthAsync(cancellationToken);

            var data = new Dictionary<string, object>
            {
                { "queue_depth", queueDepth },
                { "threshold", 1000 }
            };

            return queueDepth switch
            {
                < 500 => HealthCheckResult.Healthy("Fila saudável", data),
                < 1000 => HealthCheckResult.Degraded($"Fila com {queueDepth} mensagens pendentes", data: data),
                _ => HealthCheckResult.Unhealthy($"Fila crítica com {queueDepth} mensagens", data: data)
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Erro ao verificar saúde da fila");
            return HealthCheckResult.Unhealthy("Erro ao verificar fila", ex);
        }
    }
}

// Registrando o health check customizado
builder.Services.AddHealthChecks()
    .AddCheck<OrderQueueHealthCheck>("order-queue",
        failureStatus: HealthStatus.Degraded,
        tags: new[] { "queue", "business" });
```

## Resposta Detalhada em JSON

Por padrão, o endpoint retorna apenas o texto `Healthy`. Para obter detalhes em JSON:

```csharp
app.MapHealthChecks("/health", new HealthCheckOptions
{
    ResponseWriter = async (context, report) =>
    {
        context.Response.ContentType = "application/json";

        var result = new
        {
            status = report.Status.ToString(),
            duration = report.TotalDuration.TotalMilliseconds,
            entries = report.Entries.Select(e => new
            {
                name = e.Key,
                status = e.Value.Status.ToString(),
                description = e.Value.Description,
                duration = e.Value.Duration.TotalMilliseconds,
                data = e.Value.Data,
                exception = e.Value.Exception?.Message
            })
        };

        await context.Response.WriteAsJsonAsync(result);
    }
});
```

Resposta exemplo:

```json
{
  "status": "Degraded",
  "duration": 123.45,
  "entries": [
    {
      "name": "database",
      "status": "Healthy",
      "duration": 12.3,
      "data": {}
    },
    {
      "name": "order-queue",
      "status": "Degraded",
      "description": "Fila com 750 mensagens pendentes",
      "duration": 111.15,
      "data": {
        "queue_depth": 750,
        "threshold": 1000
      }
    }
  ]
}
```

## Integrando com Prometheus

```csharp
dotnet add package AspNetCore.HealthChecks.Publisher.Prometheus
```

```csharp
builder.Services.AddHealthChecks()
    .AddNpgSql(connectionString, name: "database")
    .AddRedis(redisConnectionString, name: "redis");

// Publica métricas de health check no endpoint do Prometheus
builder.Services.Configure<HealthCheckPublisherOptions>(opts =>
{
    opts.Delay = TimeSpan.FromSeconds(5);
    opts.Period = TimeSpan.FromSeconds(30);
});

builder.Services.AddSingleton<IHealthCheckPublisher, PrometheusHealthCheckPublisher>();
```

Métricas geradas:

```promql
# Status por health check (1 = Healthy, 0 = Unhealthy)
health_check_status{check="database"}

# Duração de cada check
health_check_duration_seconds{check="database"}

# Alerta quando qualquer dependência está Unhealthy
health_check_status < 1
```

## Configuração no Kubernetes

```yaml
# deployment.yaml
spec:
  containers:
    - name: order-service
      image: order-service:latest
      ports:
        - containerPort: 8080

      # Startup probe — aguarda a aplicação iniciar
      startupProbe:
        httpGet:
          path: /health/live
          port: 8080
        initialDelaySeconds: 10
        periodSeconds: 5
        failureThreshold: 30  # aguarda até 150s para iniciar

      # Liveness probe — reinicia se a aplicação travar
      livenessProbe:
        httpGet:
          path: /health/live
          port: 8080
        periodSeconds: 10
        failureThreshold: 3

      # Readiness probe — remove do load balancer se não estiver pronto
      readinessProbe:
        httpGet:
          path: /health/ready
          port: 8080
        periodSeconds: 5
        failureThreshold: 3
```

## Health Checks UI

O pacote `AspNetCore.HealthChecks.UI` oferece uma interface visual:

```csharp
builder.Services.AddHealthChecksUI(setup =>
{
    setup.SetEvaluationTimeInSeconds(15);
    setup.MaximumHistoryEntriesPerEndpoint(60);
    setup.AddHealthCheckEndpoint("Order Service", "/health");
}).AddInMemoryStorage();

app.MapHealthChecksUI(opts => opts.UIPath = "/health-ui");
```

Acesse `http://app/health-ui` para ver o painel visual com histórico.

## Próximo passo

[10-exemplos-praticos.md](10-exemplos-praticos.md) — Exemplos práticos combinando logs, métricas, traces e health checks.

## Referências

- [Microsoft Docs — Health checks in ASP.NET Core](https://learn.microsoft.com/en-us/aspnet/core/host-and-deploy/health-checks)
- [AspNetCore.HealthChecks no GitHub](https://github.com/Xabaril/AspNetCore.Diagnostics.HealthChecks)
- [Kubernetes — Configure Liveness, Readiness and Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
