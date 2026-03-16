# Testes unitários

Este documento detalha **escopo**, **quando usar** e **exemplos** de testes unitários no .NET.

---

## Escopo

- Testar **uma unidade** de cada vez: uma classe, um método público ou uma regra de negócio.
- **Todas as dependências externas** (repositórios, HTTP, filas, arquivos) são substituídas por **mocks** ou **stubs**.
- Não há acesso a banco real, rede ou sistema de arquivos; o teste roda apenas em memória.

## Quando usar

- **Lógica de negócio**: cálculos, validações, regras (ex.: desconto por faixa, validação de CPF).
- **Orquestração**: serviços que coordenam outros (ex.: “buscar pedido, calcular total, publicar evento”) — dependências mockadas.
- **Mapeamentos**: conversão entidade ↔ DTO, desde que seja lógica pura ou com dependências injetadas e mockáveis.
- **Qualquer código** que possa ser isolado e que você queira refatorar com segurança.

## Padrão AAA e nomenclatura

Use **Arrange-Act-Assert** e nomes que descrevam o cenário e o resultado esperado:

- `MetodoTestado_DeveRetornarX_QuandoY` (convenção comum em .NET)
- Ou: `Deve_retornar_desconto_10_por_cento_quando_cliente_vip` (mais legível em português)

## Exemplo 1: Serviço com dependência mockada

**Código sob teste** (exemplo simplificado):

```csharp
// Serviço que aplica desconto e persiste via repositório
public interface IPedidoRepository
{
    Task<Pedido?> ObterPorIdAsync(Guid id, CancellationToken ct = default);
    Task SalvarAsync(Pedido pedido, CancellationToken ct = default);
}

public class PedidoService
{
    private readonly IPedidoRepository _repository;

    public PedidoService(IPedidoRepository repository) => _repository = repository;

    public async Task<ResultadoDesconto> AplicarDescontoVipAsync(Guid pedidoId, CancellationToken ct = default)
    {
        var pedido = await _repository.ObterPorIdAsync(pedidoId, ct);
        if (pedido is null)
            return ResultadoDesconto.NaoEncontrado;

        if (!pedido.ClienteVip)
            return ResultadoDesconto.NaoElegivel;

        pedido.AplicarDesconto(0.10m); // 10%
        await _repository.SalvarAsync(pedido, ct);
        return ResultadoDesconto.Aplicado(pedido.Total);
    }
}
```

**Teste unitário** (xUnit + Moq + FluentAssertions):

```csharp
using FluentAssertions;
using Moq;
using Xunit;

public class PedidoServiceTests
{
    private readonly Mock<IPedidoRepository> _repositoryMock;
    private readonly PedidoService _sut;

    public PedidoServiceTests()
    {
        _repositoryMock = new Mock<IPedidoRepository>();
        _sut = new PedidoService(_repositoryMock.Object);
    }

    [Fact]
    public async Task AplicarDescontoVipAsync_DeveRetornarNaoEncontrado_QuandoPedidoNaoExiste()
    {
        // Arrange
        var pedidoId = Guid.NewGuid();
        _repositoryMock
            .Setup(r => r.ObterPorIdAsync(pedidoId, It.IsAny<CancellationToken>()))
            .ReturnsAsync((Pedido?)null);

        // Act
        var resultado = await _sut.AplicarDescontoVipAsync(pedidoId);

        // Assert
        resultado.Should().Be(ResultadoDesconto.NaoEncontrado);
        _repositoryMock.Verify(r => r.SalvarAsync(It.IsAny<Pedido>(), It.IsAny<CancellationToken>()), Times.Never);
    }

    [Fact]
    public async Task AplicarDescontoVipAsync_DeveRetornarNaoElegivel_QuandoClienteNaoEVip()
    {
        // Arrange
        var pedidoId = Guid.NewGuid();
        var pedido = new Pedido(pedidoId, total: 100m, clienteVip: false);
        _repositoryMock
            .Setup(r => r.ObterPorIdAsync(pedidoId, It.IsAny<CancellationToken>()))
            .ReturnsAsync(pedido);

        // Act
        var resultado = await _sut.AplicarDescontoVipAsync(pedidoId);

        // Assert
        resultado.Should().Be(ResultadoDesconto.NaoElegivel);
        _repositoryMock.Verify(r => r.SalvarAsync(It.IsAny<Pedido>(), It.IsAny<CancellationToken>()), Times.Never);
    }

    [Fact]
    public async Task AplicarDescontoVipAsync_DeveAplicar10PorCentoESalvar_QuandoClienteVip()
    {
        // Arrange
        var pedidoId = Guid.NewGuid();
        var pedido = new Pedido(pedidoId, total: 100m, clienteVip: true);
        _repositoryMock
            .Setup(r => r.ObterPorIdAsync(pedidoId, It.IsAny<CancellationToken>()))
            .ReturnsAsync(pedido);

        // Act
        var resultado = await _sut.AplicarDescontoVipAsync(pedidoId);

        // Assert
        resultado.Should().Be(ResultadoDesconto.Aplicado(90m));
        _repositoryMock.Verify(
            r => r.SalvarAsync(It.Is<Pedido>(p => p.Total == 90m), It.IsAny<CancellationToken>()),
            Times.Once);
    }
}
```

Aqui o **escopo** é só o `PedidoService`: o repositório é mockado; não há banco real.

---

## Exemplo 2: Lógica pura (sem dependências)

```csharp
// Classe com apenas lógica
public static class CalculadoraDesconto
{
    public static decimal Aplicar(decimal valor, int quantidadeItens)
    {
        if (valor <= 0 || quantidadeItens <= 0) return valor;
        if (quantidadeItens >= 10) return valor * 0.85m;  // 15%
        if (quantidadeItens >= 5)  return valor * 0.90m;  // 10%
        return valor;
    }
}

// Teste
public class CalculadoraDescontoTests
{
    [Theory]
    [InlineData(100, 1, 100)]
    [InlineData(100, 5, 90)]
    [InlineData(100, 10, 85)]
    [InlineData(100, 20, 85)]
    public void Aplicar_DeveRetornarValorComDescontoCorreto_PorQuantidade(decimal valor, int qtd, decimal esperado)
    {
        var resultado = CalculadoraDesconto.Aplicar(valor, qtd);
        resultado.Should().Be(esperado);
    }

    [Fact]
    public void Aplicar_DeveRetornarValorOriginal_QuandoValorOuQuantidadeZero()
    {
        CalculadoraDesconto.Aplicar(0, 5).Should().Be(0);
        CalculadoraDesconto.Aplicar(100, 0).Should().Be(100);
    }
}
```

`[Theory]` + `[InlineData]` evitam repetir o mesmo teste com vários dados.

---

## Resumo

| Prática | Recomendação |
|--------|---------------|
| Isolamento | Sempre mockar dependências externas. |
| AAA | Arrange, Act, Assert em blocos claros. |
| Um conceito por teste | Cada teste um cenário (ex.: “não encontrado”, “não elegível”, “aplicado”). |
| Nome descritivo | Método_ResultadoEsperado_Condicao. |
| Theory para dados | Use `[Theory]` e `[InlineData]` para vários inputs. |

## Próximo passo

Em [04-testes-de-integracao.md](04-testes-de-integracao.md) você verá como testar **API + banco** e outros componentes juntos.

## Referências

- [Unit testing best practices — .NET](https://learn.microsoft.com/pt-br/dotnet/core/testing/unit-testing-best-practices)
- [Moq quickstart](https://github.com/moq/moq4/wiki/Quickstart)
- [FluentAssertions](https://fluentassertions.com/introduction)
