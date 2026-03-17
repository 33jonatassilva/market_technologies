# Elastic Stack (ELK) — Busca e Análise de Logs

## O que é o Elastic Stack?

**Elastic Stack** (anteriormente chamado de ELK Stack) é um conjunto de ferramentas open-source
para ingestão, armazenamento, busca e visualização de dados — especialmente logs. É composto por:

| Componente | Função |
|-----------|--------|
| **Elasticsearch** | Motor de busca e armazenamento distribuído (coração do stack) |
| **Logstash** | Pipeline de ingestão e transformação de dados |
| **Kibana** | Interface de visualização e análise |
| **Beats / Elastic Agent** | Agentes leves de coleta de dados |

```
Aplicação .NET
  │
  ├── Serilog.Sinks.Elasticsearch
  │     └─► Elasticsearch ──► Kibana
  │
  └── OpenTelemetry (OTLP)
        └─► OTel Collector ──► Elasticsearch ──► Kibana
```

## Quando usar ELK vs Grafana/Loki?

| Critério | ELK | Grafana Loki |
|----------|-----|-------------|
| Busca full-text em logs | Excelente (índice invertido) | Básica (regex/filtros) |
| Custo de armazenamento | Alto (indexa tudo) | Baixo (indexa só labels) |
| Velocidade de ingestão | Alta com Logstash | Muito alta (sem indexação) |
| Análise exploratória | Muito boa (KQL, Lens) | Boa (LogQL) |
| Complexidade operacional | Alta | Baixa |
| Casos de uso ideais | Auditoria, busca em conteúdo | Logs de aplicação, correlação |

## Instalação dos Pacotes .NET

```bash
dotnet add package Serilog.Sinks.Elasticsearch
dotnet add package Elastic.Apm.NetCoreAll    # APM (Application Performance Monitoring)
```

## Configurando Serilog → Elasticsearch

### Via código

```csharp
using Serilog;
using Serilog.Sinks.Elasticsearch;

Log.Logger = new LoggerConfiguration()
    .Enrich.FromLogContext()
    .Enrich.WithMachineName()
    .Enrich.WithEnvironmentName()
    .WriteTo.Elasticsearch(new ElasticsearchSinkOptions(new Uri("http://elasticsearch:9200"))
    {
        AutoRegisterTemplate = true,
        AutoRegisterTemplateVersion = AutoRegisterTemplateVersion.ESv8,
        IndexFormat = "minhaapp-logs-{0:yyyy.MM.dd}",
        NumberOfReplicas = 1,
        NumberOfShards = 2,
        ModifyConnectionSettings = conn =>
            conn.BasicAuthentication("elastic", "senha"),
        // Formata os logs como Elastic Common Schema (ECS)
        CustomFormatter = new EcsTextFormatter()
    })
    .CreateLogger();
```

### Via appsettings.json

```json
{
  "Serilog": {
    "MinimumLevel": "Information",
    "WriteTo": [
      {
        "Name": "Elasticsearch",
        "Args": {
          "nodeUris": "http://elasticsearch:9200",
          "indexFormat": "minhaapp-logs-{0:yyyy.MM.dd}",
          "autoRegisterTemplate": true,
          "autoRegisterTemplateVersion": "ESv8"
        }
      }
    ],
    "Enrich": ["FromLogContext", "WithMachineName"]
  }
}
```

## Elastic Common Schema (ECS)

O **ECS** é o esquema padrão de campos do Elastic Stack. Usar ECS garante compatibilidade com
dashboards prontos e integração com outras ferramentas Elastic.

Campos principais do ECS relevantes para .NET:

| Campo ECS | Descrição | Exemplo |
|-----------|-----------|---------|
| `@timestamp` | Timestamp do evento | `2024-01-15T10:30:45.123Z` |
| `log.level` | Nível do log | `ERROR` |
| `message` | Mensagem do log | `Falha ao processar pedido` |
| `service.name` | Nome do serviço | `order-service` |
| `service.version` | Versão | `1.2.3` |
| `error.message` | Mensagem da exceção | `Connection timeout` |
| `error.stack_trace` | Stack trace | `at OrderService.cs:42...` |
| `trace.id` | ID do trace (OTel) | `4bf92f3577b34da6` |
| `span.id` | ID do span | `00f067aa0ba902b7` |
| `host.name` | Hostname | `pod-order-service-abc` |

```csharp
// Usando ECS formatter com Serilog
dotnet add package Elastic.CommonSchema.Serilog

.WriteTo.Console(new EcsTextFormatter())
.WriteTo.Elasticsearch(new ElasticsearchSinkOptions(...)
{
    CustomFormatter = new EcsTextFormatter()
})
```

## Elastic APM — Application Performance Monitoring

O **Elastic APM** oferece rastreamento distribuído, métricas e profiling integrados ao Kibana:

```bash
dotnet add package Elastic.Apm.NetCoreAll
```

```csharp
// Program.cs — instrumentação automática
var app = builder.Build();
app.UseAllElasticApm(builder.Configuration);  // captura HTTP, EF Core, Redis, etc.
```

```json
// appsettings.json
{
  "ElasticApm": {
    "ServerUrl": "http://apm-server:8200",
    "ServiceName": "OrderService",
    "ServiceVersion": "1.0.0",
    "Environment": "production",
    "LogLevel": "Error"
  }
}
```

### Spans customizados com Elastic APM

```csharp
using Elastic.Apm.Api;

public class OrderService
{
    public async Task<Order> CreateOrderAsync(CreateOrderRequest request)
    {
        return await Elastic.Apm.Agent.Tracer.CurrentTransaction
            .CaptureSpan("CreateOrder", "business", async span =>
            {
                span.SetLabel("customerId", request.CustomerId);

                var order = await _repository.SaveAsync(request);

                span.SetLabel("orderId", order.Id);
                return order;
            });
    }
}
```

## KQL — Kibana Query Language

O KQL é a linguagem de busca do Kibana, mais simples que o Lucene:

```kql
# Todos os logs de erro
log.level: "Error"

# Logs de erro do OrderService
log.level: "Error" AND service.name: "order-service"

# Logs contendo texto
message: "Falha ao processar"

# Filtro por campo específico
fields.OrderId: 1234

# Intervalo de valores
fields.Amount >= 100 AND fields.Amount <= 1000

# Busca com wildcard
service.name: "order*"

# Exceções de um tipo específico
error.type: "System.TimeoutException"
```

## Logstash — Pipeline de Ingestão

O Logstash permite transformar e enriquecer dados antes de enviar ao Elasticsearch:

```ruby
# logstash.conf
input {
  http {
    port => 5000
    codec => json
  }
}

filter {
  # Parsear timestamp customizado
  date {
    match => ["timestamp", "ISO8601"]
    target => "@timestamp"
  }

  # Adicionar campos
  mutate {
    add_field => { "environment" => "production" }
  }

  # Remover campos sensíveis
  mutate {
    remove_field => ["password", "credit_card_number"]
  }

  # Parsear stack trace em campos estruturados
  if [exception] {
    grok {
      match => { "exception" => "%{GREEDYDATA:error.message}" }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "minhaapp-logs-%{+yyyy.MM.dd}"
  }
}
```

## Index Templates e Retenção

```json
// Template para controlar mapeamento dos campos
PUT _index_template/minhaapp-logs
{
  "index_patterns": ["minhaapp-logs-*"],
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 1
    },
    "mappings": {
      "properties": {
        "@timestamp": { "type": "date" },
        "log.level": { "type": "keyword" },
        "service.name": { "type": "keyword" },
        "fields.OrderId": { "type": "long" },
        "fields.Amount": { "type": "double" },
        "message": { "type": "text" }
      }
    }
  }
}
```

### ILM (Index Lifecycle Management) — Retenção automática

```json
PUT _ilm/policy/minhaapp-logs-policy
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": { "max_age": "1d", "max_size": "10gb" }
        }
      },
      "warm": {
        "min_age": "7d",
        "actions": {
          "shrink": { "number_of_shards": 1 },
          "forcemerge": { "max_num_segments": 1 }
        }
      },
      "delete": {
        "min_age": "30d",
        "actions": { "delete": {} }
      }
    }
  }
}
```

## Próximo passo

[09-health-checks.md](09-health-checks.md) — Health Checks no ASP.NET Core.

## Referências

- [Elastic Stack — Documentação oficial](https://www.elastic.co/guide/index.html)
- [Serilog.Sinks.Elasticsearch](https://github.com/serilog-contrib/serilog-sinks-elasticsearch)
- [Elastic Common Schema](https://www.elastic.co/guide/en/ecs/current/index.html)
- [Elastic APM .NET Agent](https://www.elastic.co/guide/en/apm/agent/dotnet/current/index.html)
- [KQL — Referência](https://www.elastic.co/guide/en/kibana/current/kuery-query.html)
