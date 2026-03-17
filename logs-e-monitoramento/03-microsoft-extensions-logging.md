# Microsoft.Extensions.Logging — Logging Nativo do .NET

## O que é Microsoft.Extensions.Logging?

**Microsoft.Extensions.Logging** é a abstração de logging nativa do .NET. Ela fornece a interface
`ILogger<T>` e permite trocar a implementação concreta (Console, Serilog, NLog) sem alterar o código
da aplicação.

É parte do pacote `Microsoft.Extensions.Logging` e já vem configurada por padrão no ASP.NET Core.

## Configuração padrão no ASP.NET Core

No `Program.cs`, o logging já é adicionado automaticamente ao usar `WebApplication.CreateBuilder`:

```csharp
var builder = WebApplication.CreateBuilder(args);

// O logging já está configurado. Para customizar:
builder.Logging.ClearProviders();                         // remove providers padrão
builder.Logging.AddConsole();                             // adiciona Console
builder.Logging.AddDebug();                               // adiciona Debug
builder.Logging.SetMinimumLevel(LogLevel.Information);    // nível mínimo global
```

## Configuração via appsettings.json

O nível mínimo de log pode ser configurado por namespace, sem recompilar:

```json
{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning",
      "Microsoft.EntityFrameworkCore.Database.Command": "Information",
      "MinhaApp.Services": "Debug"
    },
    "Console": {
      "LogLevel": {
        "Default": "Warning"
      }
    }
  }
}
```

Os namespaces são avaliados do mais específico para o mais genérico, então
`MinhaApp.Services.OrderService` usará a regra de `MinhaApp.Services`.

## Usando ILogger<T>

A interface `ILogger<T>` é injetada via DI. O parâmetro `T` é usado como **category name**
(aparece nos logs para identificar a origem).

```csharp
public class OrderService
{
    private readonly ILogger<OrderService> _logger;

    public OrderService(ILogger<OrderService> logger)
    {
        _logger = logger;
    }

    public async Task<Order> CreateOrderAsync(CreateOrderRequest request)
    {
        _logger.LogInformation("Iniciando criação de pedido para cliente {CustomerId}", request.CustomerId);

        try
        {
            var order = await _repository.SaveAsync(request);
            _logger.LogInformation("Pedido {OrderId} criado com sucesso", order.Id);
            return order;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Erro ao criar pedido para cliente {CustomerId}", request.CustomerId);
            throw;
        }
    }
}
```

## Log Scopes

Scopes permitem adicionar **contexto compartilhado** a todos os logs dentro de um bloco,
sem repetir as propriedades em cada chamada:

```csharp
public async Task ProcessOrderAsync(int orderId)
{
    using (_logger.BeginScope(new Dictionary<string, object>
    {
        ["OrderId"] = orderId,
        ["UserId"] = _currentUser.Id
    }))
    {
        _logger.LogInformation("Iniciando processamento");     // terá OrderId e UserId
        await ValidateAsync();
        _logger.LogInformation("Validação concluída");         // também terá OrderId e UserId
        await SaveAsync();
        _logger.LogInformation("Pedido salvo");                // também terá OrderId e UserId
    }
}
```

## Log Source Generation (Alta Performance)

A partir do .NET 6, é possível usar **source generators** para criar métodos de log com
performance otimizada — sem alocações desnecessárias:

```csharp
public partial class OrderService
{
    [LoggerMessage(EventId = 1001, Level = LogLevel.Information, Message = "Pedido {OrderId} criado para cliente {CustomerId}")]
    private static partial void LogOrderCreated(ILogger logger, int orderId, int customerId);

    [LoggerMessage(EventId = 1002, Level = LogLevel.Error, Message = "Erro ao processar pedido {OrderId}")]
    private static partial void LogOrderError(ILogger logger, Exception ex, int orderId);
}
```

Vantagens: verificação em tempo de compilação, sem boxing de value types, sem alocação de arrays.

## Providers Embutidos

O .NET inclui os seguintes providers de log por padrão:

| Provider | Pacote | Onde envia |
|----------|--------|-----------|
| Console | Microsoft.Extensions.Logging.Console | Terminal / stdout |
| Debug | Microsoft.Extensions.Logging.Debug | Debug output (IDE) |
| EventSource | Microsoft.Extensions.Logging | ETW / dotnet-trace |
| EventLog | Microsoft.Extensions.Logging.EventLog | Windows Event Log |

Para produção, o recomendado é substituir por **Serilog** ou **NLog** (próximo documento).

## EventIds — Identificando Logs por Código

`EventId` permite identificar tipos de evento por número, facilitando filtros e alertas:

```csharp
public static class LogEvents
{
    public static readonly EventId OrderCreated    = new(1001, "OrderCreated");
    public static readonly EventId OrderFailed     = new(1002, "OrderFailed");
    public static readonly EventId PaymentReceived = new(2001, "PaymentReceived");
}

_logger.LogInformation(LogEvents.OrderCreated, "Pedido {OrderId} criado", orderId);
```

## Próximo passo

[04-serilog.md](04-serilog.md) — Serilog, a biblioteca de logging estruturado mais popular do .NET.

## Referências

- [Microsoft Docs — Logging in .NET](https://learn.microsoft.com/en-us/dotnet/core/extensions/logging)
- [Microsoft Docs — High-performance logging](https://learn.microsoft.com/en-us/dotnet/core/extensions/logger-message-generator)
- [Microsoft Docs — Log scopes](https://learn.microsoft.com/en-us/dotnet/core/extensions/logging#log-scopes)
