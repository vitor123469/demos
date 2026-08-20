import json, os, re, time, subprocess, urllib.request, urllib.parse, pathlib

TG = os.environ.get("TG", "").strip()
REPO = os.environ.get("GITHUB_REPOSITORY", "vitor123469/demos")
OWNER = REPO.split("/")[0]
REPONAME = REPO.split("/")[1] if "/" in REPO else "demos"
PAGES = "https://%s.github.io/%s" % (OWNER, REPONAME)


def tg(method, payload):
    if not TG:
        print("no TG token"); return None
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.telegram.org/bot%s/%s" % (TG, method),
        data=data, headers={"Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8"))
    except Exception as e:
        print("tg error", method, e); return None


def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
    return s or "demo"


def resolve_chats():
    ids = []
    cfg = {}
    if os.path.exists("data/config.json"):
        try: cfg = json.load(open("data/config.json"))
        except Exception: cfg = {}
    if cfg.get("chat_id"):
        ids = [cfg["chat_id"]]
    else:
        upd = tg("getUpdates", {})
        seen = set()
        if upd and upd.get("ok"):
            for u in upd["result"]:
                msg = u.get("message") or u.get("channel_post") or u.get("edited_message") or {}
                ch = (msg.get("chat") or {}).get("id")
                if ch and ch not in seen:
                    seen.add(ch); ids.append(ch)
        if ids:
            cfg["chat_id"] = ids[0]
            pathlib.Path("data").mkdir(exist_ok=True)
            json.dump(cfg, open("data/config.json", "w"), ensure_ascii=False, indent=2)
    return ids


TEMPLATE = """<!doctype html>
<html lang="pt-br"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>%%NOME%% — %%CIDADE%%</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Poppins,system-ui,sans-serif;color:#1a1a1a;background:#fff;line-height:1.6}
a{text-decoration:none}
.wrap{max-width:920px;margin:0 auto;padding:0 20px}
.hero{background:linear-gradient(135deg,%%COR%% 0%,%%COR2%% 100%);color:#fff;padding:70px 0 80px;text-align:center}
.badge{display:inline-block;background:rgba(255,255,255,.18);padding:6px 16px;border-radius:999px;font-size:14px;font-weight:600;margin-bottom:18px}
.hero h1{font-size:44px;font-weight:800;line-height:1.1;margin-bottom:12px}
.hero p{font-size:19px;opacity:.95;max-width:600px;margin:0 auto 28px}
.cta{display:inline-block;background:#25D366;color:#fff;font-weight:700;font-size:17px;padding:16px 34px;border-radius:14px;box-shadow:0 10px 30px rgba(0,0,0,.2);transition:transform .15s}
.cta:hover{transform:translateY(-2px)}
.stars{margin-top:22px;font-size:15px;opacity:.95}
section{padding:60px 0}
.h2{font-size:30px;font-weight:800;text-align:center;margin-bottom:8px}
.sub{text-align:center;color:#666;margin-bottom:38px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:20px}
.card{border:1px solid #eee;border-radius:16px;padding:26px;background:#fafafa;transition:box-shadow .2s}
.card:hover{box-shadow:0 12px 28px rgba(0,0,0,.08)}
.card h3{font-size:19px;font-weight:600;margin-bottom:6px}
.card .dot{width:42px;height:42px;border-radius:12px;background:%%COR%%;opacity:.15;margin-bottom:14px}
.info{background:#f6f6f8}
.info .grid{grid-template-columns:repeat(auto-fit,minmax(240px,1fr))}
.info .card{background:#fff;text-align:left}
.info b{display:block;color:%%COR%%;font-size:13px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px}
.foot{background:#111;color:#aaa;text-align:center;padding:40px 20px;font-size:14px}
.foot .cta{margin-top:16px}
.pill{position:fixed;bottom:16px;right:16px;background:#111;color:#fff;padding:10px 16px;border-radius:999px;font-size:13px;opacity:.85;z-index:9}
@media(max-width:600px){.hero h1{font-size:32px}.hero{padding:52px 0 60px}}
</style></head><body>
<div class="hero"><div class="wrap">
<div class="badge">%%TIPO%% • %%BAIRRO%%%%CIDADE%%</div>
<h1>%%NOME%%</h1>
<p>%%TAGLINE%%</p>
<a class="cta" href="%%WA%%">📲 Fazer pedido no WhatsApp</a>
<div class="stars">⭐ %%NOTA%% no Google · %%AVAL%% avaliações</div>
</div></div>
<section><div class="wrap">
<div class="h2">%%DESTTITULO%%</div>
<div class="sub">%%DESTSUB%%</div>
<div class="grid">%%ITENS%%</div>
</div></section>
<section class="info"><div class="wrap">
<div class="h2">Onde nos encontrar</div>
<div class="sub">Tudo o que seu cliente precisa em um só lugar</div>
<div class="grid">
<div class="card"><b>Horário</b>%%HORARIO%%</div>
<div class="card"><b>Endereço</b>%%ENDERECO%%</div>
<div class="card"><b>Contato</b>%%TELDISP%%</div>
</div>
<div style="text-align:center;margin-top:34px"><a class="cta" href="%%WA%%">Falar agora no WhatsApp</a></div>
</div></section>
<div class="foot"><div class="wrap">
<b style="color:#fff;font-size:16px">%%NOME%%</b><br>%%ENDERECO%% · %%CIDADE%%
<br><span style="font-size:12px;opacity:.6">Prévia de site — feito sob medida para o seu negócio</span>
</div></div>
<a class="pill" href="%%WA%%">💬 Gostou? Deixo no ar hoje</a>
</body></html>"""


def render(L):
    tel = re.sub(r"\D", "", L.get("telefone", ""))
    nome = L.get("nome", "Seu Negócio")
    tipo = L.get("tipo", "Negócio")
    cidade = L.get("cidade", "")
    bairro = L.get("bairro", "")
    wa_msg = "Ola! Vim pelo site de voces :)"
    wa = "https://wa.me/%s?text=%s" % (tel, urllib.parse.quote(wa_msg)) if tel else "#"
    itens = L.get("itens", [])
    cards = ""
    for it in itens:
        cards += '<div class="card"><div class="dot"></div><h3>%s</h3></div>' % it
    seg = (tipo or "").lower()
    if any(k in seg for k in ["pizz", "restaur", "lanch", "hambur", "food", "bar", "caf", "doce", "confeit", "acai", "açaí"]):
        dtitulo, dsub = "Nosso cardápio", "Feito na hora, do jeito que você ama"
    elif any(k in seg for k in ["barb", "salão", "salao", "estetic", "estét", "beleza", "cabel", "unha", "spa"]):
        dtitulo, dsub = "Nossos serviços", "Cuidado e capricho em cada detalhe"
    else:
        dtitulo, dsub = "O que oferecemos", "Qualidade que faz a diferença"
    cor = L.get("cor", "#c0392b")
    html = TEMPLATE
    reps = {
        "NOME": nome, "TIPO": tipo, "CIDADE": (" • " + cidade) if (bairro and cidade) else cidade,
        "BAIRRO": bairro, "TAGLINE": L.get("tagline", "Atendimento de qualidade que o seu bairro confia."),
        "WA": wa, "NOTA": L.get("nota", "5,0"), "AVAL": L.get("avaliacoes", "novas"),
        "ITENS": cards or '<div class="card"><div class="dot"></div><h3>Qualidade garantida</h3></div>',
        "DESTTITULO": dtitulo, "DESTSUB": dsub,
        "HORARIO": L.get("horario", "Seg a Sáb"), "ENDERECO": L.get("endereco", cidade),
        "TELDISP": L.get("telefone_exibicao", L.get("telefone", "WhatsApp")),
        "COR": cor, "COR2": L.get("cor2", "#7b241c"),
    }
    for k, v in reps.items():
        html = html.replace("%%" + k + "%%", str(v))
    return html


def outreach_msg(L, url):
    nome = L.get("nome", "seu negócio")
    tipo = (L.get("tipo", "negócio")).lower()
    nota = L.get("nota", "")
    aval = L.get("avaliacoes", "")
    star = (" (%s⭐" % nota + (", %s avaliações" % aval if aval else "") + " — parabéns!)") if nota else ""
    return (
        "Oi! Tudo bem? 👋 Aqui é o Vitor. Vi a %s *%s* no Google%s e reparei "
        "que vocês ainda não têm um site próprio.\n\n"
        "Montei uma prévia sob medida pra vocês — dá uma olhada em como ficou:\n%s\n\n"
        "Se curtir, coloco no ar hoje mesmo, já pronto pra receber pedidos. Posso te contar como funciona? 🙂"
    ) % (tipo, nome, star, url)


def main():
    leads = json.load(open("data/leads.json", encoding="utf-8"))
    if isinstance(leads, dict):
        leads = leads.get("leads", [])
    built = []
    for L in leads:
        slug = L.get("slug") or slugify("%s-%s" % (L.get("nome", "demo"), L.get("cidade", "")))
        d = pathlib.Path(slug)
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(render(L), encoding="utf-8")
        built.append((L, "%s/%s/" % (PAGES, slug)))
    # commit generated sites
    subprocess.run(["git", "config", "user.name", "fabrica-bot"])
    subprocess.run(["git", "config", "user.email", "bot@fabrica.local"])
    subprocess.run(["git", "add", "-A"])
    subprocess.run(["git", "commit", "-m", "fabrica: build %d demos" % len(built)])
    subprocess.run(["git", "push"])
    # notify
    chats = resolve_chats()
    if not chats:
        print("NO CHAT IDS — user must /start the bot"); return
    tg("sendMessage", {"chat_id": chats[0],
        "text": "🏭 *Lote pronto:* %d prévias no ar.\nToque em *Ver prévia*, depois em *Enviar no WhatsApp*." % len(built),
        "parse_mode": "Markdown"})
    for L, url in built:
        tel = re.sub(r"\D", "", L.get("telefone", ""))
        wa = "https://wa.me/%s?text=%s" % (tel, urllib.parse.quote(outreach_msg(L, url))) if tel else url
        head = "🍕 *%s* — %s" % (L.get("nome", "?"), L.get("cidade", ""))
        meta = "%s · %s⭐" % (L.get("tipo", ""), L.get("nota", "")) if L.get("nota") else L.get("tipo", "")
        for ch in chats:
            tg("sendMessage", {"chat_id": ch, "text": "%s\n%s" % (head, meta),
                "parse_mode": "Markdown",
                "reply_markup": {"inline_keyboard": [[
                    {"text": "🌐 Ver prévia", "url": url},
                    {"text": "📲 Enviar no WhatsApp", "url": wa}]]}})
            time.sleep(0.4)
    print("done:", len(built))


if __name__ == "__main__":
    main()
