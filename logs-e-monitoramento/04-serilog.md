# Serilog — Biblioteca de Logging Estruturado para .NET

## O que é o Serilog?

**Serilog** é a biblioteca de logging estruturado mais popular do ecossistema .NET. Ele implementa
a interface `ILogger` do `Microsoft.Extensions.Logging`, portanto substitui o logging padrão sem
exigir mudanças no código da aplicação.

Seus diferenciais são:

- **Logging estruturado de primeira classe** — propriedades são cidadãos de primeira classe
- **Sinks** — destinos de log configuráveis (Console, Arquivo, Elasticsearch, Seq, etc.)
- **Enrichers** — adicionam propriedades automáticas a todos os logs (Machine, Thread, User)
- **Filtros** — controle fino sobre quais eventos são registrados
- **Configuração via código ou appsettings.json**

## Instalação

```bash
dotnet add package Serilog.AspNetCore
dotnet add package Serilog.Sinks.Console
dotnet add package Serilog.Sinks.File
dotnet add package Serilog.Sinks.Elasticsearch    # opcional
dotnet add package Serilog.Sinks.Seq              # opcional
dotnet add package Serilog.Enrichers.Environment
dotnet add package Serilog.Enrichers.Thread
dotnet add package Serilog.Enrichers.Context
```

## Configuração no Program.cs

### Via código (fluent API)

```csharp
using Serilog;

Log.Logger = new LoggerConfiguration()
    .MinimumLevel.Information()
    .MinimumLevel.Override("Microsoft", LogEventLevel.Warning)
    .MinimumLevel.Override("Microsoft.EntityFrameworkCore", LogEventLevel.Information)
    .Enrich.FromLogContext()
    .Enrich.WithMachineName()
    .Enrich.WithThreadId()
    .WriteTo.Console(outputTemplate:
        "[{Timestamp:HH:mm:ss} {Level:u3}] {Message:lj} {Properties:j}{NewLine}{Exception}")
    .WriteTo.File("logs/app-.log",
        rollingInterval: RollingInterval.Day,
        retainedFileCountLimit: 7)
    .CreateLogger();

var builder = WebApplication.CreateBuilder(args);
builder.Host.UseSerilog();  // substitui o logging padrão pelo Serilog
```

### Via appsettings.json

```json
{
  "Serilog": {
    "MinimumLevel": {
      "Default": "Information",
      "Override": {
        "Microsoft": "Warning",
        "Microsoft.EntityFrameworkCore": "Information"
      }
    },
    "WriteTo": [
      {
        "Name": "Console",
        "Args": {
          "outputTemplate": "[{Timestamp:HH:mm:ss} {Level:u3}] {Message:lj}{NewLine}{Exception}"
        }
      },
      {
        "Name": "File",
        "Args": {
          "path": "logs/app-.log",
          "rollingInterval": "Day",
          "retainedFileCountLimit": 7
        }
      }
    ],
    "Enrich": ["FromLogContext", "WithMachineName", "WithThreadId"]
  }
}
```

```csharp
// Program.cs lendo do appsettings
builder.Host.UseSerilog((context, services, configuration) =>
    configuration
        .ReadFrom.Configuration(context.Configuration)
        .ReadFrom.Services(services)
        .Enrich.FromLogContext());
```

## Sinks — Destinos de Log

Sinks são destinos onde os logs são enviados. O Serilog possui mais de 60 sinks disponíveis:

| Sink | Pacote | Uso |
|------|--------|-----|
| Console | Serilog.Sinks.Console | Terminal, desenvolvimento |
| File | Serilog.Sinks.File | Arquivo local com rolling |
| Seq | Serilog.Sinks.Seq | Plataforma Seq (logs estruturados) |
| Elasticsearch | Serilog.Sinks.Elasticsearch | Elastic Stack (ELK) |
| Grafana Loki | Serilog.Sinks.Grafana.Loki | Grafana Loki |
| ApplicationInsights | Serilog.Sinks.ApplicationInsights | Azure Monitor |
| MSSqlServer | Serilog.Sinks.MSSqlServer | SQL Server |
| MongoDB | Serilog.Sinks.MongoDB | MongoDB |

### Configurando múltiplos sinks

```csharp
.WriteTo.Console()
.WriteTo.File("logs/app-.log", rollingInterval: RollingInterval.Day)
.WriteTo.Seq("http://seq:5341")
.WriteTo.Elasticsearch(new ElasticsearchSinkOptions(new Uri("http://elasticsearch:9200"))
{
    AutoRegisterTemplate = true,
    IndexFormat = "minhaapp-logs-{0:yyyy.MM.dd}"
})
```

### Sinks condicionais por nível

```csharp
.WriteTo.Console(restrictedToMinimumLevel: LogEventLevel.Information)
.WriteTo.File("logs/errors-.log",
    restrictedToMinimumLevel: LogEventLevel.Error,
    rollingInterval: RollingInterval.Day)
```

## Enrichers — Enriquecendo Logs com Contexto

Enrichers adicionam **propriedades automáticas** a todos os eventos de log:

```csharp
.Enrich.FromLogContext()          // usa LogContext.PushProperty(...)
.Enrich.WithMachineName()         // adiciona MachineName
.Enrich.WithThreadId()            // adiciona ThreadId
.Enrich.WithEnvironmentName()     // adiciona EnvironmentName (Production, Staging...)
.Enrich.WithProperty("Application", "MinhaApp")  // propriedade fixa
.Enrich.WithProperty("Version", Assembly.GetExecutingAssembly().GetName().Version)
```

### LogContext — Contexto dinâmico

```csharp
// Adiciona propriedade ao contexto para todos os logs dentro do using
using (LogContext.PushProperty("OrderId", orderId))
using (LogContext.PushProperty("UserId", userId))
{
    _logger.LogInformation("Processando pedido");
    _logger.LogInformation("Validando estoque");
    // ambos os logs terão OrderId e UserId
}
```

## Logging com Destruturing

O Serilog permite controlar como objetos complexos são serializados nos logs usando `@` e `$`:

```csharp
var order = new Order { Id = 1, Amount = 299.90m, CustomerId = 42 };

// @ desestrutura o objeto (serializa todas as propriedades)
_logger.LogInformation("Pedido criado: {@Order}", order);
// Output: Pedido criado: {"Id": 1, "Amount": 299.90, "CustomerId": 42}

// $ converte para string (chama .ToString())
_logger.LogInformation("Pedido: {$Order}", order);
// Output: Pedido: Order { Id=1, Amount=299.90 }
```

## Request Logging com UseSerilogRequestLogging

O Serilog tem middleware para substituir o verbose logging do ASP.NET Core por um único log por request:

```csharp
var app = builder.Build();

app.UseSerilogRequestLogging(options =>
{
    options.MessageTemplate = "HTTP {RequestMethod} {RequestPath} respondeu {StatusCode} em {Elapsed:0.0000} ms";
    options.EnrichDiagnosticContext = (diagnosticContext, httpContext) =>
    {
        diagnosticContext.Set("RequestHost", httpContext.Request.Host.Value);
        diagnosticContext.Set("UserAgent", httpContext.Request.Headers["User-Agent"]);
        diagnosticContext.Set("UserId", httpContext.User.FindFirst("sub")?.Value);
    };
});
```

## Próximo passo

[05-opentelemetry.md](05-opentelemetry.md) — OpenTelemetry, o padrão aberto para observabilidade em .NET.

## Referências

- [Serilog — Site oficial](https://serilog.net/)
- [Serilog.AspNetCore no GitHub](https://github.com/serilog/serilog-aspnetcore)
- [Lista completa de sinks](https://github.com/serilog/serilog/wiki/Provided-Sinks)
- [Serilog — Structured data](https://github.com/serilog/serilog/wiki/Structured-Data)
