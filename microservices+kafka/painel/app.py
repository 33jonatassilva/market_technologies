"""
Painel do sistema de vendas: API proxy para os microserviços e controle de containers (start/stop).
Serve o frontend estático e expõe /api/* para o painel web.
"""
import os
import logging
from flask import Flask, request, jsonify, send_from_directory

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("painel")

app = Flask(__name__, static_folder="static", static_url_path="")

# URLs dos serviços: no Docker use hostnames (pedidos:5000); no host use localhost e portas expostas
def _base_url(env_var: str, default_host: str, default_port: int, host_port: int = None) -> str:
    url = os.environ.get(env_var)
    if url:
        return url.rstrip("/")
    # Se rodando no host (sem Docker), hostnames como "pedidos" não resolvem; usar localhost e porta mapeada
    in_docker = os.environ.get("PANEL_IN_DOCKER", "").lower() in ("1", "true", "yes")
    if host_port is not None and not in_docker:
        return f"http://127.0.0.1:{host_port}"
    return f"http://{default_host}:{default_port}"

PEDIDOS_URL = _base_url("PEDIDOS_URL", "pedidos", 5000, 5001)
ESTOQUE_URL = _base_url("ESTOQUE_URL", "estoque", 5000, 5002)
PAGAMENTOS_URL = _base_url("PAGAMENTOS_URL", "pagamentos", 5000, 5003)
NOTIFICACOES_URL = _base_url("NOTIFICACOES_URL", "notificacoes", 5000, 5004)

SERVICES = {
    "pedidos": PEDIDOS_URL,
    "estoque": ESTOQUE_URL,
    "pagamentos": PAGAMENTOS_URL,
    "notificacoes": NOTIFICACOES_URL,
}

TIMEOUT = 10


def _proxy_get(service: str, path: str = ""):
    base = SERVICES.get(service)
    if not base:
        return jsonify({"error": "Serviço desconhecido"}), 400
    path_part = path.strip("/") if path else ""
    url = f"{base}/{path_part}" if path_part else base
    try:
        r = requests.get(url, timeout=TIMEOUT)
        try:
            data = r.json()
        except Exception:
            data = {"error": r.text or f"Resposta não-JSON (status {r.status_code})"}
        return jsonify(data), r.status_code
    except requests.RequestException as e:
        logger.warning("Proxy GET %s: %s", url, e)
        return jsonify({"error": str(e), "status": "unavailable"}), 503


def _proxy_post(service: str, path: str, json_body: dict = None):
    base = SERVICES.get(service)
    if not base:
        return jsonify({"error": "Serviço desconhecido"}), 400
    path_part = path.strip("/") if path else ""
    url = f"{base}/{path_part}" if path_part else base
    try:
        r = requests.post(url, json=json_body or request.get_json(), timeout=TIMEOUT)
        try:
            data = r.json()
        except Exception:
            data = {"error": r.text or f"Resposta não-JSON (status {r.status_code})"}
        return jsonify(data), r.status_code
    except requests.RequestException as e:
        logger.warning("Proxy POST %s: %s", url, e)
        return jsonify({"error": str(e), "status": "unavailable"}), 503


# --- Health ---
@app.route("/api/health/<service>", methods=["GET"])
def api_health(service):
    if service not in SERVICES:
        return jsonify({"error": "Serviço desconhecido"}), 400
    return _proxy_get(service, "health")


# --- Pedidos ---
@app.route("/api/pedidos", methods=["GET"])
def api_pedidos_list():
    return _proxy_get("pedidos", "pedidos")


@app.route("/api/pedidos", methods=["POST"])
def api_pedidos_create():
    return _proxy_post("pedidos", "pedidos")


@app.route("/api/pedidos/<order_id>", methods=["GET"])
def api_pedidos_get(order_id):
    return _proxy_get("pedidos", f"pedidos/{order_id}")


# --- Estoque ---
@app.route("/api/estoque", methods=["GET"])
def api_estoque():
    return _proxy_get("estoque", "estoque")


# --- Notificações ---
@app.route("/api/notificacoes", methods=["GET"])
def api_notificacoes():
    return _proxy_get("notificacoes", "notificacoes")


# --- Config Pagamentos (simular rejeição) ---
@app.route("/api/config/pagamentos", methods=["GET"])
def api_config_pagamentos_get():
    return _proxy_get("pagamentos", "config")


@app.route("/api/config/pagamentos", methods=["POST"])
def api_config_pagamentos_post():
    body = request.get_json() or {}
    return _proxy_post("pagamentos", "config", body)


# --- Controle de containers (Docker) ---
def _docker_control():
    try:
        import docker
        client = docker.from_env()
        return client
    except Exception as e:
        logger.warning("Docker não disponível: %s", e)
        return None


CONTAINER_NAMES = ["pedidos", "estoque", "pagamentos", "notificacoes"]


@app.route("/api/control/status", methods=["GET"])
def api_control_status():
    client = _docker_control()
    if not client:
        # Fallback: inferir pelo health de cada serviço
        status = {}
        for name in CONTAINER_NAMES:
            try:
                r = requests.get(f"{SERVICES[name]}/health", timeout=2)
                status[name] = "running" if r.status_code == 200 else "unhealthy"
            except requests.RequestException:
                status[name] = "down"
        return jsonify({"containers": status, "docker": False}), 200
    result = {}
    try:
        for c in client.containers.list(all=True):
            name = c.name
            if name in CONTAINER_NAMES:
                result[name] = "running" if c.status == "running" else "exited"
        for name in CONTAINER_NAMES:
            if name not in result:
                result[name] = "exited"
    except Exception as e:
        logger.warning("Docker list: %s", e)
        return jsonify({"error": str(e), "containers": {}}), 503
    return jsonify({"containers": result, "docker": True}), 200


@app.route("/api/control/stop/<service>", methods=["POST"])
def api_control_stop(service):
    if service not in CONTAINER_NAMES:
        return jsonify({"error": "Serviço desconhecido"}), 400
    client = _docker_control()
    if not client:
        return jsonify({"error": "Docker não disponível"}), 503
    try:
        container = client.containers.get(service)
        container.stop()
        return jsonify({"ok": True, "service": service, "action": "stopped"}), 200
    except Exception as e:
        logger.warning("Docker stop %s: %s", service, e)
        return jsonify({"error": str(e)}), 503


@app.route("/api/control/start/<service>", methods=["POST"])
def api_control_start(service):
    if service not in CONTAINER_NAMES:
        return jsonify({"error": "Serviço desconhecido"}), 400
    client = _docker_control()
    if not client:
        return jsonify({"error": "Docker não disponível"}), 503
    try:
        container = client.containers.get(service)
        container.start()
        return jsonify({"ok": True, "service": service, "action": "started"}), 200
    except Exception as e:
        logger.warning("Docker start %s: %s", service, e)
        return jsonify({"error": str(e)}), 503


# --- Frontend estático ---
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def static_file(path):
    return send_from_directory(app.static_folder, path)


if __name__ == "__main__":
    port = int(os.environ.get("FLASK_PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
