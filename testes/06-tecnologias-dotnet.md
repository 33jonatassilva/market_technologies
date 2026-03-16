# Tecnologias .NET para testes

Este documento resume as principais **tecnologias de mercado** na plataforma .NET para escrever e melhorar testes (unitários, integração, E2E).

---

## Frameworks de teste (test runners)

São os que **descobrem** e **executam** os testes e exibem resultados.

| Framework | Descrição | Quando usar |
|-----------|-----------|-------------|
| **xUnit** | Sem estado compartilhado entre testes por padrão; uma instância da classe de teste por método; `[Fact]` e `[Theory]`. | **Recomendado** para projetos novos; padrão em muitos templates e libs .NET. |
| **NUnit** | Maduro, `[Test]`, `[SetUp]`/`[TearDown]`, atributos ricos (`[TestCase]`, `[Range]`). | Projetos que já usam ou equipes que preferem NUnit. |
| **MSTest** | Integrado à Microsoft; `[TestMethod]`, `[TestInitialize]`. | Ambientes fortemente alinhados ao Visual Studio e MSTest. |

Para novos projetos em .NET, **xUnit** é a escolha mais comum.

---

## Mocking (simular dependências)

| Biblioteca | Descrição | Exemplo rápido |
|------------|-----------|----------------|
| **Moq** | Muito usada; API com `Mock<T>`, `Setup()`, `Verify()`, `ReturnsAsync()`. | `_repo.Setup(r => r.GetAsync(1)).ReturnsAsync(entity);` |
| **NSubstitute** | API fluente com `Substitute.For<T>()`, `Returns()`, `Received()`. | `_repo.GetAsync(1).Returns(entity);` |

Ambas permitem **stub** (retornar valores) e **mock** (verificar chamadas). Escolha por preferência de sintaxe e padrão do time.

---

## Assertions (asserções)

| Biblioteca | Descrição | Exemplo |
|------------|-----------|---------|
| **FluentAssertions** | Asserções encadeadas e mensagens de erro claras. | `resultado.Should().Be(10);` `lista.Should().HaveCount(2).And.Contain(x);` |
| **Assert do xUnit/NUnit** | Built-in: `Assert.Equal`, `Assert.NotNull`. | `Assert.Equal(10, resultado);` |

**FluentAssertions** melhora legibilidade e diagnóstico quando o teste falha; é amplamente adotado.

---

## Dados de teste (geração e builders)

| Ferramenta | Descrição | Uso |
|------------|-----------|-----|
| **Bogus** | Gera dados realistas (nome, e-mail, data, texto). | `new Faker<Cliente>().RuleFor(c => c.Nome, f => f.Person.FullName)` |
| **AutoFixture** | Gera objetos e preenche propriedades automaticamente; útil para “any” em testes. | Reduz boilerplate de Arrange. |
| **Builders manuais** | Classes que constroem entidades com valores padrão sobrescrevíveis. | Controle fino e legibilidade. |

Bogus é ótimo para testes que precisam de muitos cenários com dados variados sem repetir strings fixas.

---

## Testes de integração (APIs e banco)

| Ferramenta | Descrição | Uso |
|------------|-----------|-----|
| **WebApplicationFactory&lt;T&gt;** | Sobe a aplicação ASP.NET Core em memória para testes. | Criar `HttpClient` e chamar endpoints reais. |
| **Microsoft.AspNetCore.Mvc.Testing** | Pacote NuGet que fornece `WebApplicationFactory`. | Referenciar no projeto de testes de integração. |
| **EF Core InMemory** | Provedor em memória do Entity Framework. | Testes de integração sem banco real (não é um SQL real). |
| **TestContainers** | Sobe containers Docker (SQL Server, Postgres, Redis) para testes. | Integração com banco real em CI/local. |

Para máxima fidelidade ao banco, use **TestContainers**; para velocidade, **InMemory** (com cuidado com diferenças de comportamento do SQL).

---

## Testes E2E (UI e API como usuário)

| Ferramenta | Descrição | Uso |
|------------|-----------|-----|
| **Playwright** | Automação de browser (Chromium, Firefox, WebKit); API .NET. | E2E de aplicações web. |
| **Selenium** | Clássico para automação de browser. | E2E quando já há investimento em Selenium. |
| **HttpClient + WebApplicationFactory** | Chamadas HTTP à API. | E2E “só API” (fluxo completo sem UI). |

---

## Snapshot / output verification

| Ferramenta | Descrição | Uso |
|------------|-----------|-----|
| **Verify** | Compara saída (objeto, texto, XML) com um arquivo “aprovado”; atualiza arquivo quando aprovado. | Evitar asserções longas em objetos grandes ou JSON. |

Útil para serialização, relatórios e respostas grandes onde você quer “congelar” o resultado esperado.

---

## Performance e carga

| Ferramenta | Descrição | Uso |
|------------|-----------|-----|
| **BenchmarkDotNet** | Micro-benchmarks de métodos no .NET. | Medir performance de trechos de código. |
| **NBomber** | Testes de carga e stress em .NET. | Simular muitos usuários em APIs ou cenários. |

---

## Pacotes NuGet sugeridos por tipo de projeto

**Projeto de testes unitários (xUnit + Moq + FluentAssertions):**

```xml
<ItemGroup>
  <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.8.0" />
  <PackageReference Include="xunit" Version="2.6.2" />
  <PackageReference Include="xunit.runner.visualstudio" Version="2.5.4" />
  <PackageReference Include="Moq" Version="4.20.70" />
  <PackageReference Include="FluentAssertions" Version="6.12.0" />
  <!-- opcional -->
  <PackageReference Include="Bogus" Version="35.0.1" />
</ItemGroup>
```

**Projeto de testes de integração (ASP.NET Core):**

```xml
<ItemGroup>
  <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.8.0" />
  <PackageReference Include="xunit" Version="2.6.2" />
  <PackageReference Include="xunit.runner.visualstudio" Version="2.5.4" />
  <PackageReference Include="FluentAssertions" Version="6.12.0" />
  <PackageReference Include="Microsoft.AspNetCore.Mvc.Testing" Version="8.0.0" />
  <!-- para banco em memória -->
  <PackageReference Include="Microsoft.EntityFrameworkCore.InMemory" Version="8.0.0" />
</ItemGroup>
```

(Ajuste as versões conforme o .NET e os pacotes atuais.)

---

## Resumo

| Necessidade | Tecnologia típica |
|-------------|-------------------|
| Rodar testes | xUnit (ou NUnit / MSTest) |
| Mockar dependências | Moq ou NSubstitute |
| Asserções legíveis | FluentAssertions |
| Dados realistas | Bogus (ou AutoFixture) |
| Integração API | WebApplicationFactory + HttpClient |
| Banco em teste | EF InMemory ou TestContainers |
| E2E com browser | Playwright |
| Snapshot de saída | Verify |
| Performance | BenchmarkDotNet, NBomber |

## Próximo passo

Em [07-exemplos-praticos.md](07-exemplos-praticos.md) há **exemplos completos** por tipo de teste, prontos para inspirar seu código.

## Referências

- [Unit testing — .NET](https://learn.microsoft.com/pt-br/dotnet/core/testing/)
- [xUnit](https://xunit.net/)
- [Moq](https://github.com/moq/moq4)
- [FluentAssertions](https://fluentassertions.com/)
- [Bogus](https://github.com/bchavez/Bogus)
- [TestContainers](https://dotnet.testcontainers.org/)
