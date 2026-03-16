(function () {
  const API = "/api";

  function get(path) {
    return fetch(API + path).then(async (r) => {
      const body = await r.json().catch(() => ({}));
      if (!r.ok) {
        const msg = body.error || body.message || r.status + " " + r.statusText;
        throw new Error(msg);
      }
      return body;
    });
  }

  function post(path, body) {
    return fetch(API + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    }).then(async (r) => {
      const data = await r.json().catch(() => ({}));
      if (!r.ok) {
        const msg = data.error || data.message || r.status + " " + r.statusText;
        throw new Error(msg);
      }
      return data;
    });
  }

  // --- Tabs ---
  document.querySelectorAll(".tab").forEach((btn) => {
    btn.addEventListener("click", function () {
      const tab = this.dataset.tab;
      document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
      this.classList.add("active");
      const panel = document.getElementById(tab);
      if (panel) panel.classList.add("active");
      if (tab === "visao") refreshVisao();
      if (tab === "pedidos") refreshPedidos();
      if (tab === "controle") refreshControl();
    });
  });

  // --- Visão geral ---
  function refreshVisao() {
    const cards = document.getElementById("health-cards");
    cards.innerHTML = "<p class=\"loading\">Carregando…</p>";
    const services = ["pedidos", "estoque", "pagamentos", "notificacoes"];
    Promise.all(services.map((s) => get("/health/" + s).then((d) => ({ name: s, ...d })).catch((e) => ({ name: s, error: true }))))
      .then((results) => {
        cards.innerHTML = results
          .map((r) => {
            const status = r.error ? "down" : (r.status === "ok" ? "ok" : "unhealthy");
            const text = r.error ? "Desligado" : (r.status === "ok" ? "OK" : r.status || "—");
            return `<div class="card ${status}"><span class="name">${r.name}</span><br><span class="status">${text}</span></div>`;
          })
          .join("");
      })
      .catch(() => {
        cards.innerHTML = "<p class=\"error\">Erro ao carregar status.</p>";
      });

    get("/estoque")
      .then((d) => {
        const el = document.getElementById("estoque-resumo");
        el.textContent = "Inventário: " + JSON.stringify(d.inventory || {}, null, 2) + "\n\nReservas: " + JSON.stringify(d.reservations || {}, null, 2);
      })
      .catch(() => {
        document.getElementById("estoque-resumo").textContent = "Indisponível.";
      });

    get("/notificacoes")
      .then((d) => {
        const el = document.getElementById("notificacoes-resumo");
        const list = (d.notifications || []).slice(-10).reverse();
        if (list.length === 0) {
          el.innerHTML = "Nenhuma notificação recente.";
        } else {
          el.innerHTML = list.map((n) => `<div class="notif-item">Pedido ${n.orderId} — ${n.customerId} — R$ ${n.total} — ${n.timestamp || ""}</div>`).join("");
        }
      })
      .catch(() => {
        document.getElementById("notificacoes-resumo").innerHTML = "Indisponível.";
      });
  }

  // --- Pedidos ---
  function refreshPedidos() {
    const wrap = document.getElementById("pedidos-list");
    wrap.innerHTML = "<p class=\"loading\">Carregando…</p>";
    get("/pedidos")
      .then((list) => {
        if (!Array.isArray(list) || list.length === 0) {
          wrap.innerHTML = "<p>Nenhum pedido.</p>";
          return;
        }
        wrap.innerHTML =
          "<table><thead><tr><th>orderId</th><th>customerId</th><th>Total</th><th>Status</th></tr></thead><tbody>" +
          list
            .map(
              (o) =>
                `<tr class="clickable" data-id="${o.orderId}"><td>${o.orderId}</td><td>${o.customerId}</td><td>${o.total}</td><td><span class="badge ${o.status}">${o.status}${o.motivo ? " (" + o.motivo + ")" : ""}</span></td></tr>`
            )
            .join("") +
          "</tbody></table>";
        wrap.querySelectorAll("tr.clickable").forEach((row) => {
          row.addEventListener("click", function () {
            const id = this.dataset.id;
            get("/pedidos/" + id)
              .then((ord) => {
                const det = document.getElementById("pedido-detalhe");
                det.classList.remove("hidden");
                det.innerHTML = "<strong>Detalhe</strong><pre>" + JSON.stringify(ord, null, 2) + "</pre>";
              })
              .catch((e) => {
                document.getElementById("pedido-detalhe").innerHTML = "<p class=\"error\">" + e.message + "</p>";
                document.getElementById("pedido-detalhe").classList.remove("hidden");
              });
          });
        });
      })
      .catch((e) => {
        wrap.innerHTML = "<p class=\"error\">Erro: " + e.message + "</p>";
      });
  }

  document.getElementById("btn-refresh-pedidos").addEventListener("click", refreshPedidos);

  // --- Novo pedido ---
  let itemCount = 1;
  document.getElementById("btn-add-item").addEventListener("click", function () {
    const container = document.getElementById("itens-container");
    const div = document.createElement("div");
    div.className = "item-row";
    div.innerHTML = '<input type="text" name="productId" placeholder="P1" value="P2"> <input type="number" name="quantity" placeholder="1" value="1" min="1">';
    container.appendChild(div);
  });

  document.getElementById("form-pedido").addEventListener("submit", function (e) {
    e.preventDefault();
    const form = e.target;
    const productIds = form.querySelectorAll('input[name="productId"]');
    const quantities = form.querySelectorAll('input[name="quantity"]');
    const items = [];
    for (let i = 0; i < productIds.length; i++) {
      items.push({ productId: productIds[i].value || "P1", quantity: parseInt(quantities[i].value, 10) || 1 });
    }
    const body = {
      customerId: form.querySelector('input[name="customerId"]').value || "cliente-anonimo",
      items,
      total: parseFloat(form.querySelector('input[name="total"]').value, 10) || 0,
    };
    const resultEl = document.getElementById("novo-pedido-result");
    resultEl.classList.add("hidden");
    resultEl.className = "result";
    post("/pedidos", body)
      .then((d) => {
        resultEl.classList.remove("hidden");
        resultEl.classList.add("success");
        resultEl.innerHTML = "Pedido criado: <strong>" + d.orderId + "</strong> (status: " + d.status + "). <a href=\"#\" data-tab=\"pedidos\">Ver lista de pedidos</a>.";
        resultEl.querySelector("a").addEventListener("click", function (ev) {
          ev.preventDefault();
          document.querySelector('.tab[data-tab="pedidos"]').click();
        });
      })
      .catch((err) => {
        resultEl.classList.remove("hidden");
        resultEl.classList.add("error");
        resultEl.textContent = "Erro: " + err.message;
      });
  });

  // --- Controle ---
  function refreshControl() {
    const wrap = document.getElementById("control-cards");
    wrap.innerHTML = "<p class=\"loading\">Carregando…</p>";
    get("/control/status")
      .then((d) => {
        const containers = d.containers || {};
        const useDocker = d.docker === true;
        wrap.innerHTML = ["pedidos", "estoque", "pagamentos", "notificacoes"]
          .map((name) => {
            const status = containers[name] || "unknown";
            const running = status === "running";
            return (
              '<div class="card ' +
              (running ? "ok" : "down") +
              '"><span class="name">' +
              name +
              '</span><br><span class="status">' +
              status +
              "</span><br>" +
              (useDocker
                ? '<button type="button" class="ctrl-btn" data-service="' +
                  name +
                  '" data-action="' +
                  (running ? "stop" : "start") +
                  '">' +
                  (running ? "Desligar" : "Ligar") +
                  "</button>"
                : "<span class=\"muted\">Docker não disponível</span>") +
              "</div>"
            );
          })
          .join("");
        wrap.querySelectorAll(".ctrl-btn").forEach((btn) => {
          btn.addEventListener("click", function () {
            const service = this.dataset.service;
            const action = this.dataset.action;
            post("/control/" + action + "/" + service)
              .then(() => refreshControl())
              .catch((err) => alert("Erro: " + err.message));
          });
        });
      })
      .catch(() => {
        wrap.innerHTML = "<p class=\"error\">Erro ao carregar status dos containers.</p>";
      });
  }

  document.getElementById("btn-refresh-control").addEventListener("click", refreshControl);

  // --- Config pagamentos (simular rejeição) ---
  function refreshConfigPagamentos() {
    get("/config/pagamentos")
      .then((d) => {
        const toggle = document.getElementById("toggle-rejeicao");
        if (toggle) toggle.checked = d.simularRejeicao === true;
        const st = document.getElementById("config-status");
        if (st) st.textContent = d.simularRejeicao ? "Ativada" : "Desativada";
      })
      .catch(() => {});
  }

  const toggleRejeicao = document.getElementById("toggle-rejeicao");
  if (toggleRejeicao) {
    toggleRejeicao.addEventListener("change", function () {
      post("/config/pagamentos", { simularRejeicao: this.checked })
        .then(() => refreshConfigPagamentos())
        .catch((err) => alert("Erro: " + err.message));
    });
  }

  refreshConfigPagamentos();
  refreshVisao();
})();
