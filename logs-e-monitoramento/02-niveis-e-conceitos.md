# Níveis de Log, Structured Logging, Traces e Métricas

## Níveis de Log

O .NET segue uma hierarquia de severidade de logs. Cada nível indica a importância do evento:

| Nível | Enum value | Quando usar |
|-------|-----------|-------------|
| **Trace** | 0 | Informações extremamente detalhadas para diagnóstico, desativado em produção |
| **Debug** | 1 | Informações de depuração, úteis durante desenvolvimento |
| **Information** | 2 | Fluxo normal da aplicação — requisições recebidas, operações concluídas |
| **Warning** | 3 | Situação inesperada mas recuperável — uso alto de memória, retry |
| **Error** | 4 | Falha em uma operação — exceção capturada, falha ao processar |
| **Critical** | 5 | Falha grave que pode derrubar a aplicação — banco inacessível, OOM |
| **None** | 6 | Desabilita o logging completamente |

### Regra prática de uso

```csharp
// Trace: detalhe máximo, apenas durante debugging local
_logger.LogTrace("Entrando no método ProcessOrder com orderId={OrderId}", orderId);

// Debug: útil para dev/staging, raramente em produção
_logger.LogDebug("Cache miss para chave {CacheKey}", cacheKey);

// Information: eventos de negócio normais
_logger.LogInformation("Pedido {OrderId} criado com sucesso para o cliente {CustomerId}", orderId, customerId);

// Warning: algo saiu do esperado, mas a operação continuou
_logger.LogWarning("Tentativa {Attempt} de 3 para conectar ao serviço de pagamento", attempt);

// Error: operação falhou, mas a aplicação continua
_logger.LogError(ex, "Falha ao processar pedido {OrderId}", orderId);

// Critical: sistema em risco
_logger.LogCritical("Conexão com banco de dados perdida — aplicação não pode continuar");
```

## Structured Logging (Log Estruturado)

Log estruturado é a prática de registrar eventos como **dados estruturados** (JSON, por exemplo),
em vez de texto plano. Isso permite filtrar, agregar e analisar logs de forma muito mais eficiente.

### Log tradicional (texto plano)

```
[2024-01-15 10:30:45] INFO Pedido 1234 criado para cliente 5678 no valor de 299.90
```

Difícil de filtrar: como encontrar todos os pedidos acima de R$ 200?

### Log estruturado (JSON)

```json
{
  "timestamp": "2024-01-15T10:30:45Z",
  "level": "Information",
  "message": "Pedido criado com sucesso",
  "orderId": 1234,
  "customerId": 5678,
  "amount": 299.90,
  "service": "OrderService"
}
```

Agora é possível filtrar por `amount > 200`, agrupar por `customerId`, etc.

### Message Templates no .NET

O .NET usa **message templates** para log estruturado. As chaves entre `{}` se tornam propriedades:

```csharp
// As chaves {OrderId} e {Amount} viram propriedades estruturadas
_logger.LogInformation("Pedido {OrderId} criado no valor de {Amount:C}", orderId, amount);
```

> **Atenção**: Nunca use interpolação de string (`$"..."`) em logs — você perde as propriedades estruturadas
> e impacta a performance.

```csharp
// ❌ Errado — perde estrutura e é mais lento
_logger.LogInformation($"Pedido {orderId} criado");

// ✅ Correto — mantém estrutura e usa deferred evaluation
_logger.LogInformation("Pedido {OrderId} criado", orderId);
```

## Traces (Rastreamento Distribuído)

Em sistemas distribuídos (microserviços), uma única operação de negócio pode percorrer vários
serviços. O rastreamento distribuído permite visualizar todo esse caminho.

### Conceitos fundamentais

| Conceito | Descrição |
|----------|-----------|
| **Trace** | Representação completa de uma operação ponta a ponta |
| **Span** | Unidade de trabalho dentro de um trace (ex: uma chamada HTTP, uma query SQL) |
| **TraceId** | Identificador único que acompanha toda a operação |
| **SpanId** | Identificador único de cada span |
| **Parent SpanId** | Liga spans filhos ao span pai, formando a árvore de execução |

### Exemplo visual de um trace

```
Trace: criar-pedido (TraceId: abc123)
│
├── [Span] API Gateway         0ms ──── 5ms
│   └── [Span] OrderService   2ms ───────── 80ms
│       ├── [Span] DB Insert  3ms ──── 20ms
│       └── [Span] PaymentSvc 25ms ─────────── 75ms
│           └── [Span] DB Read 26ms ── 40ms
```

### Traces no .NET com System.Diagnostics

```csharp
private static readonly ActivitySource ActivitySource = new("MinhaApp.OrderService");

public async Task<Order> CreateOrderAsync(CreateOrderRequest request)
{
    using var activity = ActivitySource.StartActivity("CreateOrder");
    activity?.SetTag("order.customerId", request.CustomerId);
    activity?.SetTag("order.amount", request.Amount);

    // lógica do método...

    activity?.SetStatus(ActivityStatusCode.Ok);
    return order;
}
```

## Métricas

Métricas são **medições numéricas** coletadas ao longo do tempo. Diferente de logs (descritivos),
métricas são ideais para alertas e dashboards.

### Tipos de métricas

| Tipo | Descrição | Exemplo |
|------|-----------|---------|
| **Counter** | Valor que só cresce | Total de requests, total de erros |
| **Gauge** | Valor que sobe e desce | Uso de memória, conexões ativas |
| **Histogram** | Distribuição de valores | Latência de requests (p50, p95, p99) |

### Métricas no .NET com System.Diagnostics.Metrics

```csharp
public class OrderMetrics
{
    private readonly Counter<int> _ordersCreated;
    private readonly Histogram<double> _orderAmount;

    public OrderMetrics(IMeterFactory meterFactory)
    {
        var meter = meterFactory.Create("MinhaApp.OrderService");
        _ordersCreated = meter.CreateCounter<int>("orders.created", "orders", "Total de pedidos criados");
        _orderAmount = meter.CreateHistogram<double>("orders.amount", "BRL", "Valor dos pedidos");
    }

    public void RecordOrderCreated(double amount)
    {
        _ordersCreated.Add(1);
        _orderAmount.Record(amount);
    }
}
```

## Próximo passo

[03-microsoft-extensions-logging.md](03-microsoft-extensions-logging.md) — Microsoft.Extensions.Logging, o sistema de logging nativo do .NET.

## Referências

- [Microsoft Docs — Log levels](https://learn.microsoft.com/en-us/dotnet/core/extensions/logging#log-level)
- [Microsoft Docs — Distributed tracing](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/distributed-tracing)
- [Microsoft Docs — Metrics in .NET](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/metrics)
