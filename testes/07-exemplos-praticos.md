# Exemplos práticos completos

Este documento reúne **exemplos completos** de cada tipo de teste discutido na documentação, em C# e .NET, para servir de referência.

---

## 1. Teste unitário: validador com Moq e FluentAssertions

**Código sob teste:**

```csharp
public interface IClienteRepository
{
    Task<bool> ExisteEmailAsync(string email, CancellationToken ct = default);
}

public class ClienteValidator
{
    private readonly IClienteRepository _repository;

    public ClienteValidator(IClienteRepository repository) => _repository = repository;

    public async Task<ValidationResult> ValidarAsync(ClienteInput input, CancellationToken ct = default)
    {
        if (string.IsNullOrWhiteSpace(input.Nome))
            return ValidationResult.Falha("Nome é obrigatório.");

        if (string.IsNullOrWhiteSpace(input.Email))
            return ValidationResult.Falha("Email é obrigatório.");

        if (!input.Email.Contains('@'))
            return ValidationResult.Falha("Email inválido.");

        var emailJaExiste = await _repository.ExisteEmailAsync(input.Email, ct);
        if (emailJaExiste)
            return ValidationResult.Falha("Email já cadastrado.");

        return ValidationResult.Ok();
    }
}

public record ClienteInput(string Nome, string Email);
public record ValidationResult(bool Sucesso, string? Mensagem)
{
    public static ValidationResult Ok() => new(true, null);
    public static ValidationResult Falha(string msg) => new(false, msg);
}
```

**Teste unitário:**

```csharp
using FluentAssertions;
using Moq;
using Xunit;

public class ClienteValidatorTests
{
    private readonly Mock<IClienteRepository> _repoMock;
    private readonly ClienteValidator _sut;

    public ClienteValidatorTests()
    {
        _repoMock = new Mock<IClienteRepository>();
        _sut = new ClienteValidator(_repoMock.Object);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("   ")]
    public async Task ValidarAsync_DeveFalhar_QuandoNomeVazio(string? nome)
    {
        var input = new ClienteInput(nome!, "a@b.com");
        var result = await _sut.ValidarAsync(input);
        result.Sucesso.Should().BeFalse();
        result.Mensagem.Should().Be("Nome é obrigatório.");
        _repoMock.Verify(r => r.ExisteEmailAsync(It.IsAny<string>(), It.IsAny<CancellationToken>()), Times.Never);
    }

    [Fact]
    public async Task ValidarAsync_DeveFalhar_QuandoEmailInvalido()
    {
        var input = new ClienteInput("João", "sem-arroba");
        var result = await _sut.ValidarAsync(input);
        result.Sucesso.Should().BeFalse();
        result.Mensagem.Should().Be("Email inválido.");
    }

    [Fact]
    public async Task ValidarAsync_DeveFalhar_QuandoEmailJaExiste()
    {
        _repoMock.Setup(r => r.ExisteEmailAsync("existente@mail.com", It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);
        var input = new ClienteInput("Maria", "existente@mail.com");

        var result = await _sut.ValidarAsync(input);

        result.Sucesso.Should().BeFalse();
        result.Mensagem.Should().Be("Email já cadastrado.");
    }

    [Fact]
    public async Task ValidarAsync_DeveRetornarOk_QuandoDadosValidos()
    {
        _repoMock.Setup(r => r.ExisteEmailAsync(It.IsAny<string>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(false);
        var input = new ClienteInput("Maria", "nova@mail.com");

        var result = await _sut.ValidarAsync(input);

        result.Sucesso.Should().BeTrue();
        result.Mensagem.Should().BeNull();
    }
}
```

---

## 2. Teste unitário: [Theory] com vários dados (lógica pura)

```csharp
public static class FaixaDesconto
{
    public static decimal DescontoPorFaixa(decimal valor, int quantidade)
    {
        if (valor <= 0 || quantidade <= 0) return 0;
        if (quantidade >= 100) return 0.20m;
        if (quantidade >= 50) return 0.15m;
        if (quantidade >= 10) return 0.10m;
        return 0;
    }
}

public class FaixaDescontoTests
{
    [Theory]
    [InlineData(100, 5, 0)]
    [InlineData(100, 10, 0.10)]
    [InlineData(100, 50, 0.15)]
    [InlineData(100, 100, 0.20)]
    [InlineData(100, 200, 0.20)]
    public void DescontoPorFaixa_RetornaPercentualCorreto(decimal valor, int qtd, decimal percentualEsperado)
    {
        var result = FaixaDesconto.DescontoPorFaixa(valor, qtd);
        result.Should().Be(percentualEsperado);
    }

    [Theory]
    [InlineData(0, 10)]
    [InlineData(10, 0)]
    [InlineData(-1, 5)]
    public void DescontoPorFaixa_RetornaZero_QuandoValorOuQuantidadeInvalido(decimal valor, int qtd)
    {
        FaixaDesconto.DescontoPorFaixa(valor, qtd).Should().Be(0);
    }
}
```

---

## 3. Teste de integração: WebApplicationFactory + HttpClient

**Factory (ajuste o namespace e o tipo de entrada para o seu projeto):**

```csharp
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;

public class ApiFactory : WebApplicationFactory<Program> // Program = entry point da API
{
    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.ConfigureServices(services =>
        {
            services.RemoveAll(typeof(DbContextOptions<MeuDbContext>));
            services.AddDbContext<MeuDbContext>(opts =>
            {
                opts.UseInMemoryDatabase("TestDb_" + Guid.NewGuid());
            });

            var sp = services.BuildServiceProvider();
            using var scope = sp.CreateScope();
            var db = scope.ServiceProvider.GetRequiredService<MeuDbContext>();
            db.Database.EnsureCreated();
        });
    }
}
```

**Teste de integração:**

```csharp
using System.Net;
using System.Net.Http.Json;
using FluentAssertions;
using Xunit;

public class ProdutosApiTests : IClassFixture<ApiFactory>
{
    private readonly HttpClient _client;

    public ProdutosApiTests(ApiFactory factory) => _client = factory.CreateClient();

    [Fact]
    public async Task GET_Produtos_Id_Retorna404_QuandoNaoExiste()
    {
        var res = await _client.GetAsync("/api/produtos/99999");
        res.StatusCode.Should().Be(HttpStatusCode.NotFound);
    }

    [Fact]
    public async Task POST_Produtos_Retorna201_E_ProdutoNoCorpo()
    {
        var body = new { Nome = "Produto Teste", Preco = 29.90m };
        var res = await _client.PostAsJsonAsync("/api/produtos", body);
        res.StatusCode.Should().Be(HttpStatusCode.Created);
        var produto = await res.Content.ReadFromJsonAsync<ProdutoDto>();
        produto.Should().NotBeNull();
        produto!.Nome.Should().Be("Produto Teste");
        produto.Preco.Should().Be(29.90m);
    }
}
```

(Assumindo que a API expõe `POST /api/produtos` e `GET /api/produtos/{id}` e que `MeuDbContext` e `Program` existem no projeto da API.)

---

## 4. Teste de integração: health check (fumaça)

```csharp
[Fact]
public async Task Health_Retorna200()
{
    var res = await _client.GetAsync("/health");
    res.StatusCode.Should().Be(HttpStatusCode.OK);
}
```

---

## 5. Uso de Bogus para dados variados

```csharp
using Bogus;

var faker = new Faker<ClienteInput>("pt_BR")
    .RuleFor(c => c.Nome, f => f.Person.FullName)
    .RuleFor(c => c.Email, f => f.Internet.Email());

var cliente1 = faker.Generate();
var cliente2 = faker.Generate();
// Cada um com nome e e-mail realistas diferentes; útil para [Theory] ou vários testes.
```

---

## Resumo dos exemplos

| Seção | Tipo | O que ilustra |
|-------|------|----------------|
| 1 | Unitário | Validador com repositório mockado; Theory para múltiplos inputs. |
| 2 | Unitário | Lógica pura; [Theory] + [InlineData]. |
| 3 | Integração | WebApplicationFactory, HttpClient, banco InMemory. |
| 4 | Fumaça | Health check simples. |
| 5 | Dados | Bogus para geração de entradas realistas. |

Para rodar: crie um projeto de testes (xUnit), referencie o projeto da aplicação, adicione os pacotes (xUnit, Moq, FluentAssertions, Microsoft.AspNetCore.Mvc.Testing, etc.) e adapte namespaces e tipos ao seu código.

## Referências

- [03-testes-unitarios.md](03-testes-unitarios.md)
- [04-testes-de-integracao.md](04-testes-de-integracao.md)
- [06-tecnologias-dotnet.md](06-tecnologias-dotnet.md)
