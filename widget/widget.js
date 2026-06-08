/* ====================================================================
   Widget de chat embebible.
   El cliente solo pega UNA línea en su web:
     <script src="https://TU-SERVIDOR/widget.js"
             data-api="https://TU-SERVIDOR/chat"></script>
   ==================================================================== */
(function () {
  // URL del backend: se lee del atributo data-api del <script>
  var script = document.currentScript;
  var API = (script && script.getAttribute("data-api")) || "http://localhost:5000/chat";
  var sesion = "web-" + Math.random().toString(36).slice(2);

  // ---- Estilos -------------------------------------------------------
  var css = `
    #cb-burbuja{position:fixed;bottom:20px;right:20px;width:60px;height:60px;
      border-radius:50%;background:#2563eb;color:#fff;font-size:28px;border:none;
      cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,.25);z-index:99999}
    #cb-panel{position:fixed;bottom:90px;right:20px;width:340px;max-width:92vw;
      height:460px;max-height:70vh;background:#fff;border-radius:14px;display:none;
      flex-direction:column;overflow:hidden;box-shadow:0 8px 30px rgba(0,0,0,.25);
      z-index:99999;font-family:system-ui,sans-serif}
    #cb-cab{background:#2563eb;color:#fff;padding:14px 16px;font-weight:600}
    #cb-msgs{flex:1;overflow-y:auto;padding:14px;background:#f7f8fa}
    .cb-m{margin:6px 0;padding:9px 12px;border-radius:12px;max-width:80%;
      font-size:14px;line-height:1.4;white-space:pre-wrap}
    .cb-user{background:#2563eb;color:#fff;margin-left:auto;border-bottom-right-radius:3px}
    .cb-bot{background:#fff;color:#1a1a1a;border:1px solid #e3e3e3;border-bottom-left-radius:3px}
    #cb-pie{display:flex;border-top:1px solid #eee;padding:8px}
    #cb-input{flex:1;border:1px solid #ddd;border-radius:8px;padding:9px;font-size:14px;outline:none}
    #cb-enviar{margin-left:6px;background:#2563eb;color:#fff;border:none;border-radius:8px;
      padding:0 14px;cursor:pointer}`;
  var st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);

  // ---- HTML ----------------------------------------------------------
  var burbuja = document.createElement("button");
  burbuja.id = "cb-burbuja"; burbuja.textContent = "💬";
  var panel = document.createElement("div");
  panel.id = "cb-panel";
  panel.innerHTML =
    '<div id="cb-cab">Asistente virtual</div>' +
    '<div id="cb-msgs"></div>' +
    '<div id="cb-pie"><input id="cb-input" placeholder="Escribe tu mensaje..."/>' +
    '<button id="cb-enviar">➤</button></div>';
  document.body.appendChild(burbuja);
  document.body.appendChild(panel);

  var msgs = panel.querySelector("#cb-msgs");
  var input = panel.querySelector("#cb-input");

  function pinta(texto, quien) {
    var d = document.createElement("div");
    d.className = "cb-m " + (quien === "user" ? "cb-user" : "cb-bot");
    d.textContent = texto; msgs.appendChild(d);
    msgs.scrollTop = msgs.scrollHeight;
    return d;
  }

  burbuja.onclick = function () {
    var abierto = panel.style.display === "flex";
    panel.style.display = abierto ? "none" : "flex";
    if (!abierto && !msgs.children.length)
      pinta("¡Hola! ¿En qué puedo ayudarte hoy?", "bot");
  };

  async function enviar() {
    var texto = input.value.trim();
    if (!texto) return;
    pinta(texto, "user"); input.value = "";
    var cargando = pinta("…", "bot");
    try {
      var r = await fetch(API, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mensaje: texto, sesion: sesion })
      });
      var data = await r.json();
      cargando.textContent = data.respuesta || "Lo siento, ha habido un error.";
    } catch (e) {
      cargando.textContent = "No he podido conectar. Inténtalo de nuevo.";
    }
  }

  panel.querySelector("#cb-enviar").onclick = enviar;
  input.addEventListener("keydown", function (e) { if (e.key === "Enter") enviar(); });
})();
