# Testes de integração

Este documento cobre **escopo**, **quando usar** e **exemplos** de testes de integração no .NET, em especial para APIs ASP.NET Core.

---

## Escopo

- Testar **vários componentes juntos**: por exemplo, HTTP → Controller → Serviço → Repositório → Banco (ou banco em memória).
- **Dependências reais** ou substitutos realistas: banco SQLite em memória, EF Core InMemory, TestContainers com SQL Server/Postgres, ou APIs reais em ambiente de teste.
- Objetivo: garantir que a **integração** entre camadas funciona (serialização, rotas, middlewares, persistência).

## Quando usar

- Validar que **endpoints** retornam status e corpo corretos (200, 201, 404, 400).
- Validar que **dados persistem** no banco e são recuperados como esperado.
- Validar **autenticação/autorização**, middlewares e filtros.
- Validar **serialização** (JSON, content-type) e binding de modelos.

## WebApplicationFactory (ASP.NET Core)

O **WebApplicationFactory&lt;TEntryPoint&gt;** sobe a aplicação em memória para testes. Você faz requisições HTTP com `HttpClient` e asserta respostas e estado (ex.: banco).

### Exemplo 1: API que retorna e persiste dados

**Projeto de testes** referencia o projeto da API (onde está `Program.cs` ou o `Startup`).

```csharp
// CustomWebApplicationFactory.cs — substitui serviços reais se necessário
public class CustomWebApplicationFactory : WebApplicationFactory<Program>
{
    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.ConfigureServices(services =>
        {
            // Trocar banco real por um em memória para os testes
            var descriptor = services.SingleOrDefault(
                d => d.ServiceType == typeof(DbContextOptions<AppDbContext>));
            if (descriptor != null)
                services.Remove(descriptor);

            services.AddDbContext<AppDbContext>(options =>
            {
                options.UseInMemoryDatabase("TestDb");
            });

            services.EnsureCreated(); // opcional: criar schema no startup do host
        });
    }
}
```

**Teste de integração** — POST cria recurso e GET retorna:

```csharp
using System.Net;
using System.Net.Http.Json;
using FluentAssertions;
using Xunit;

public class ClientesControllerIntegrationTests : IClassFixture<CustomWebApplicationFactory>
{
    private readonly HttpClient _client;

    public ClientesControllerIntegrationTests(CustomWebApplicationFactory factory)
    {
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task POST_Clientes_DeveRetornar201_E_CriarClienteNoBanco()
    {
        // Arrange
        var payload = new { Nome = "Maria", Email = "maria@example.com" };

        // Act
        var response = await _client.PostAsJsonAsync("/api/clientes", payload);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.Created);
        response.Headers.Location.Should().NotBeNull();

        var cliente = await response.Content.ReadFromJsonAsync<ClienteResponse>();
        cliente.Should().NotBeNull();
        cliente!.Nome.Should().Be("Maria");
        cliente.Email.Should().Be("maria@example.com");

        // Verificar persistência: GET no Location
        var getResponse = await _client.GetAsync(response.Headers.Location);
        getResponse.StatusCode.Should().Be(HttpStatusCode.OK);
        var obtido = await getResponse.Content.ReadFromJsonAsync<ClienteResponse>();
        obtido!.Id.Should().Be(cliente.Id);
    }

    [Fact]
    public async Task GET_Clientes_Id_DeveRetornar404_QuandoNaoExiste()
    {
        var response = await _client.GetAsync($"/api/clientes/{Guid.NewGuid()}");
        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
    }
}
```

Aqui o **escopo** é a integração: HTTP + controller + serviço + banco (em memória). Não mockamos o controller nem o DbContext.

---

## Exemplo 2: Resposta e validação de modelo

```csharp
[Fact]
public async Task POST_Clientes_DeveRetornar400_QuandoEmailInvalido()
{
    var payload = new { Nome = "João", Email = "email-invalido" };

    var response = await _client.PostAsJsonAsync("/api/clientes", payload);

    response.StatusCode.Should().Be(HttpStatusCode.BadRequest);
    var problemDetails = await response.Content.ReadFromJsonAsync<ValidationProblemDetails>();
    problemDetails.Should().NotBeNull();
    problemDetails!.Errors.Should().ContainKey("Email");
}
```

---

## Boas práticas

| Prática | Descrição |
|--------|-----------|
| Banco isolado | Use um banco por teste (ex.: nome único do InMemory por teste) ou limpe dados entre testes para evitar interferência. |
| Não depender de ordem | Testes de integração não devem depender da ordem de execução. |
| Substituir apenas o necessário | Troque só o que é pesado ou instável (banco, APIs externas); use o resto real. |
| TestContainers | Para comportamento mais próximo do real, use containers (SQL Server, Postgres) em vez de InMemory. |

## Resumo

- **Escopo**: fluxo que cruza camadas (HTTP → app → persistência).
- **Quando**: validar endpoints, persistência, autenticação e serialização.
- **Ferramenta**: `WebApplicationFactory<T>` + `HttpClient` + banco em memória ou TestContainers.

## Próximo passo

Em [05-testes-e2e-e-outros.md](05-testes-e2e-e-outros.md) você verá E2E, testes de contrato e outros tipos.

## Referências

- [Integration tests — ASP.NET Core](https://learn.microsoft.com/pt-br/aspnet/core/test/integration-tests)
- [WebApplicationFactory](https://learn.microsoft.com/pt-br/aspnet/core/test/integration-tests#customize-webapplicationfactory)
