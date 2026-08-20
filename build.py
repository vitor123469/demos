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


# palette per niche: (accent, accent2 for duotone, paper, ink)
def palette_for(tipo, L):
    s = (tipo or "").lower()
    if L.get("cor"):
        return (L["cor"], L.get("cor2", "#20140f"), L.get("paper", "#f6efe6"), L.get("ink", "#1c1512"))
    if any(k in s for k in ["pizz", "restaur", "food", "comida", "bar", "boteco", "lanch", "hambur", "churrasc", "steak"]):
        return ("#b5341f", "#2a0f08", "#f7efe4", "#1c1210")      # terracotta / warm
    if any(k in s for k in ["caf", "confeit", "doce", "padar", "bake", "bistr"]):
        return ("#8a5a2b", "#241608", "#f6eee2", "#211812")      # coffee / caramel
    if any(k in s for k in ["barb"]):
        return ("#b8823c", "#0f0f10", "#efece6", "#141416")      # brass on charcoal
    if any(k in s for k in ["salão", "salao", "cabel", "beleza", "hair", "estetic", "estét", "spa", "unha", "clinic", "clín"]):
        return ("#9a7b5a", "#221a16", "#f4efe9", "#201915")      # nude / warm taupe
    if any(k in s for k in ["academ", "fit", "cross", "gym"]):
        return ("#c6402e", "#101215", "#eef0f2", "#14171b")
    return ("#9a5b34", "#1e1712", "#f5efe7", "#1d1712")


def kw_for(tipo):
    s = (tipo or "").lower()
    if "pizz" in s: return "pizza,pizzeria,dough"
    if any(k in s for k in ["hambur", "lanch", "burg"]): return "burger,gourmet"
    if any(k in s for k in ["churrasc", "steak", "carne"]): return "steak,grill,meat"
    if any(k in s for k in ["restaur", "food", "comida", "bar", "boteco"]): return "restaurant,plating,gastronomy"
    if any(k in s for k in ["caf", "confeit", "doce", "padar", "bake"]): return "cafe,bakery,pastry"
    if any(k in s for k in ["acai", "açaí", "sorvet"]): return "acai,bowl,fruit"
    if "barb" in s: return "barbershop,barber,grooming"
    if any(k in s for k in ["salão", "salao", "cabel", "beleza", "hair"]): return "hairstyle,salon"
    if any(k in s for k in ["estetic", "estét", "spa", "unha", "clinic", "clín"]): return "spa,skincare,wellness"
    if any(k in s for k in ["academ", "fit", "cross", "gym"]): return "gym,training,athlete"
    return "storefront,craft,artisan"


DEPO_POOL = [
    ("Mariana A.", "Fui pela primeira vez semana passada e já virei cliente. O cuidado com cada detalhe faz toda a diferença."),
    ("Rafael S.", "Melhor da região, sem exagero. Atendimento honesto e um capricho que a gente sente na hora."),
    ("Juliana C.", "Indico de olhos fechados. Chega no ponto, no prazo, e sempre com aquele algo a mais."),
    ("Bruno M.", "Já trouxe a família inteira. É daqueles lugares que a gente sente falta quando fica sem ir."),
    ("Carla R.", "Atendimento de gente que gosta do que faz. Voltei três vezes só esse mês."),
    ("Diego F.", "Simples assim: superou o que eu esperava. Recomendo pra qualquer um do bairro."),
]


TEMPLATE = """<!doctype html>
<html lang="pt-br"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>%%NOME%% — %%TIPO%%, %%CIDADE%%</title>
<meta name="description" content="%%NOME%% · %%TAGLINE%%">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400..900;1,9..144,400..800&family=Archivo:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{--ac:%%COR%%;--duo:%%COR2%%;--paper:%%PAPER%%;--ink:%%INK%%;--line:rgba(0,0,0,.12)}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{font-family:Archivo,system-ui,sans-serif;background:var(--paper);color:var(--ink);line-height:1.6;font-size:17px}
.f{font-family:Fraunces,Georgia,serif}
a{color:inherit;text-decoration:none}
img{display:block;max-width:100%}
.kick{font-size:12px;letter-spacing:.28em;text-transform:uppercase;font-weight:600}
.wrap{max-width:1160px;margin:0 auto;padding:0 30px}
.duo{position:relative;background-size:cover;background-position:center;filter:contrast(1.04) saturate(.92)}
.duo::before{content:"";position:absolute;inset:0;background:var(--duo);mix-blend-mode:color;opacity:.62}
.duo::after{content:"";position:absolute;inset:0;background:var(--ac);mix-blend-mode:multiply;opacity:.16}
.rise{opacity:0;transform:translateY(30px);transition:opacity .9s cubic-bezier(.19,1,.22,1),transform .9s cubic-bezier(.19,1,.22,1)}
.rise.in{opacity:1;transform:none}
/* NAV */
.nav{position:fixed;inset:0 0 auto 0;z-index:40;display:flex;justify-content:space-between;align-items:center;padding:22px 30px;color:var(--paper);transition:.4s}
.nav.solid{background:var(--paper);color:var(--ink);box-shadow:0 1px 0 var(--line);padding:15px 30px}
.wordmark{font-family:Fraunces;font-weight:600;font-size:23px;letter-spacing:-.01em}
.nav .menu-links{display:flex;gap:30px;align-items:center}
.nav .menu-links a{font-size:12.5px;letter-spacing:.16em;text-transform:uppercase;opacity:.85}
.nav .call{border:1px solid currentColor;padding:9px 18px;border-radius:2px;font-size:12px;letter-spacing:.14em;text-transform:uppercase}
/* HERO */
.hero{position:relative;min-height:100svh;display:flex;align-items:flex-end;color:var(--paper);overflow:hidden}
.hero .bg{position:absolute;inset:0}
.hero .bg.duo::after{opacity:.28}
.scrim{position:absolute;inset:0;background:linear-gradient(0deg,rgba(0,0,0,.7) 0%,rgba(0,0,0,.15) 45%,rgba(0,0,0,.35) 100%)}
.hero-in{position:relative;z-index:2;padding:0 0 8vh;max-width:900px}
.hero .kick{opacity:.9;margin-bottom:22px}
.hero h1{font-weight:340;font-size:clamp(46px,9vw,116px);line-height:.96;letter-spacing:-.025em;margin-bottom:26px}
.hero h1 em{font-style:italic;font-weight:420}
.hero .lead{font-size:clamp(17px,2.1vw,21px);max-width:52ch;opacity:.94;margin-bottom:36px}
.actions{display:flex;gap:26px;align-items:center;flex-wrap:wrap}
.solid-btn{background:var(--ac);color:#fff;padding:16px 30px;border-radius:2px;font-size:13px;letter-spacing:.16em;text-transform:uppercase;font-weight:600;transition:transform .2s}
.solid-btn:hover{transform:translateY(-2px)}
.text-link{font-size:13px;letter-spacing:.14em;text-transform:uppercase;border-bottom:1px solid currentColor;padding-bottom:3px}
.hero .meta{position:absolute;right:0;bottom:8vh;z-index:2;text-align:right;font-size:13px;letter-spacing:.05em;opacity:.9;line-height:1.9}
.hero .meta .stars{color:#e9b949;letter-spacing:3px;font-size:15px}
/* STRIP */
.strip{background:var(--ink);color:var(--paper)}
.strip .wrap{display:flex;flex-wrap:wrap;gap:10px 46px;justify-content:center;padding:17px 30px;font-size:12px;letter-spacing:.18em;text-transform:uppercase;opacity:.92}
.strip b{color:var(--ac);font-weight:600}
/* MENU / editorial list */
.sec{padding:120px 0}
.sechead{display:flex;justify-content:space-between;align-items:flex-end;gap:30px;border-bottom:1px solid var(--line);padding-bottom:24px;margin-bottom:54px}
.sechead h2{font-weight:340;font-size:clamp(32px,5vw,60px);line-height:1;letter-spacing:-.02em}
.sechead h2 em{font-style:italic}
.sechead .kick{color:var(--ac);opacity:.9;margin-bottom:14px}
.menu-wrap{display:grid;grid-template-columns:1.15fr .85fr;gap:70px;align-items:start}
.mlist{display:flex;flex-direction:column}
.mitem{display:grid;grid-template-columns:1fr auto;gap:6px 16px;padding:22px 0;border-bottom:1px solid var(--line);align-items:baseline}
.mitem:first-child{padding-top:0}
.mitem .nm{font-family:Fraunces;font-weight:500;font-size:23px;letter-spacing:-.01em}
.mitem .pr{font-family:Fraunces;font-size:19px;color:var(--ac);white-space:nowrap}
.mitem .ds{grid-column:1/-1;font-size:14.5px;color:rgba(0,0,0,.55);max-width:52ch;margin-top:2px}
.menu-photo{height:100%;min-height:520px;border-radius:2px}
/* FEATURE quote */
.feature{background:var(--ink);color:var(--paper)}
.feature .wrap{padding:130px 30px;text-align:center}
.feature .kick{color:var(--ac);margin-bottom:30px}
.feature blockquote{font-family:Fraunces;font-weight:320;font-style:italic;font-size:clamp(26px,4.4vw,50px);line-height:1.22;letter-spacing:-.01em;max-width:20ch;margin:0 auto 34px}
.feature cite{font-style:normal;font-size:12.5px;letter-spacing:.2em;text-transform:uppercase;opacity:.65}
/* ABOUT split */
.about{display:grid;grid-template-columns:.9fr 1.1fr;gap:0;align-items:stretch}
.about .ph{min-height:600px}
.about .tx{padding:min(9vw,120px) clamp(30px,6vw,90px);display:flex;flex-direction:column;justify-content:center}
.about .kick{color:var(--ac);margin-bottom:20px}
.about h2{font-family:Fraunces;font-weight:340;font-size:clamp(30px,4vw,50px);line-height:1.05;letter-spacing:-.02em;margin-bottom:26px}
.about p{font-size:16.5px;color:rgba(0,0,0,.7);margin-bottom:18px;max-width:50ch}
.about .signs{display:flex;gap:40px;margin-top:26px;flex-wrap:wrap}
.about .signs b{font-family:Fraunces;font-size:38px;font-weight:500;display:block;line-height:1}
.about .signs span{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:rgba(0,0,0,.5)}
/* LOCAL */
.local{display:grid;grid-template-columns:1fr 1fr}
.local .map iframe{width:100%;height:100%;min-height:520px;border:0;filter:grayscale(.35) contrast(1.05)}
.local .info{background:var(--ink);color:var(--paper);padding:min(8vw,96px) clamp(30px,5vw,72px);display:flex;flex-direction:column;justify-content:center}
.local .info h2{font-family:Fraunces;font-weight:340;font-size:clamp(28px,3.6vw,46px);margin-bottom:40px;letter-spacing:-.02em}
.lrow{padding:20px 0;border-top:1px solid rgba(255,255,255,.16)}
.lrow:last-of-type{border-bottom:1px solid rgba(255,255,255,.16)}
.lrow .k{font-size:11.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--ac);margin-bottom:5px}
.lrow .v{font-size:16.5px}
.local .info .solid-btn{margin-top:34px;align-self:flex-start}
/* CTA */
.cta{position:relative;color:var(--paper);text-align:center;overflow:hidden}
.cta .bg{position:absolute;inset:0}
.cta .scrim{background:rgba(10,6,4,.62)}
.cta .wrap{position:relative;z-index:2;padding:150px 30px}
.cta h2{font-family:Fraunces;font-weight:340;font-size:clamp(34px,6vw,74px);line-height:1;letter-spacing:-.02em;margin-bottom:26px}
.cta h2 em{font-style:italic}
.cta p{opacity:.9;margin-bottom:36px;font-size:18px}
/* FOOT */
footer{background:var(--paper);color:var(--ink);padding:70px 30px 48px;border-top:1px solid var(--line)}
footer .top{display:flex;justify-content:space-between;flex-wrap:wrap;gap:24px;align-items:flex-end}
footer .wordmark{font-size:30px}
footer .fmeta{text-align:right;font-size:14px;line-height:1.9;color:rgba(0,0,0,.6)}
footer .rule{height:1px;background:var(--line);margin:34px 0 20px}
footer .cred{font-size:11.5px;letter-spacing:.12em;text-transform:uppercase;color:rgba(0,0,0,.4)}
/* FAB */
.fab{position:fixed;right:22px;bottom:22px;z-index:50;background:var(--ink);color:var(--paper);border-radius:2px;padding:14px 20px;font-size:12px;letter-spacing:.14em;text-transform:uppercase;font-weight:600;box-shadow:0 14px 34px rgba(0,0,0,.25);transition:transform .2s}
.fab:hover{transform:translateY(-2px)}
@media(max-width:900px){.menu-wrap{grid-template-columns:1fr;gap:44px}.menu-photo{min-height:340px;order:-1}.about{grid-template-columns:1fr}.about .ph{min-height:360px}.local{grid-template-columns:1fr}.nav .menu-links{display:none}.hero .meta{display:none}}
</style></head><body>

<nav class="nav" id="nav">
  <div class="wordmark">%%NOME%%</div>
  <div class="menu-links">
    <a href="#menu">%%NAVSEC%%</a>
    <a href="#sobre">História</a>
    <a href="#visitar">Visitar</a>
    <a class="call" href="%%WA%%">WhatsApp</a>
  </div>
</nav>

<header class="hero">
  <div class="bg duo" style="background-image:url('%%HEROIMG%%')"></div>
  <div class="scrim"></div>
  <div class="wrap hero-in">
    <div class="kick rise">%%TIPO%% · %%CIDADE%%</div>
    <h1 class="f rise">%%HEADLINE%%</h1>
    <p class="lead rise">%%TAGLINE%%</p>
    <div class="actions rise">
      <a class="solid-btn" href="%%WA%%">Fazer um pedido</a>
      <a class="text-link" href="#menu">Ver %%NAVSEC%%</a>
    </div>
  </div>
  <div class="wrap"><div class="meta"><div class="stars">%%STARS%%</div>%%NOTA%% · %%AVAL%% avaliações no Google</div></div>
</header>

<div class="strip"><div class="wrap">
  <span>%%STRIP1%%</span><span><b>·</b></span><span>%%HORARIO%%</span><span><b>·</b></span><span>%%CIDADE%%</span>
</div></div>

<section class="sec" id="menu"><div class="wrap">
  <div class="sechead rise"><div><div class="kick">%%MENUKICK%%</div><h2 class="f">%%MENUTITLE%%</h2></div></div>
  <div class="menu-wrap">
    <div class="mlist">%%ITENS%%</div>
    <div class="menu-photo duo rise" style="background-image:url('%%MENUIMG%%')"></div>
  </div>
</div></section>

<section class="feature"><div class="wrap rise">
  <div class="kick">O que dizem</div>
  <blockquote class="f">%%QUOTE%%</blockquote>
  <cite>%%QUOTEWHO%% — cliente</cite>
</div></section>

<section class="about" id="sobre">
  <div class="ph duo rise" style="background-image:url('%%ABOUTIMG%%')"></div>
  <div class="tx">
    <div class="kick rise">A casa</div>
    <h2 class="rise">%%ABOUTTITLE%%</h2>
    <p class="rise">%%SOBRE%%</p>
    <div class="signs rise">
      <div><b class="f">%%NOTA%%</b><span>no Google</span></div>
      <div><b class="f">%%AVAL%%+</b><span>clientes</span></div>
      <div><b class="f">%%ANOS%%</b><span>de casa</span></div>
    </div>
  </div>
</section>

<section class="local" id="visitar">
  <div class="map">%%MAP%%</div>
  <div class="info">
    <h2 class="f">Onde a gente fica</h2>
    <div class="lrow"><div class="k">Endereço</div><div class="v">%%ENDERECO%%</div></div>
    <div class="lrow"><div class="k">Horário</div><div class="v">%%HORARIO%%</div></div>
    <div class="lrow"><div class="k">WhatsApp</div><div class="v">%%TELDISP%%</div></div>
    <a class="solid-btn" href="%%WA%%">Chamar no WhatsApp</a>
  </div>
</section>

<section class="cta">
  <div class="bg duo" style="background-image:url('%%CTAIMG%%')"></div>
  <div class="scrim"></div>
  <div class="wrap">
    <h2 class="f">Bateu a <em>fome</em>?</h2>
    <p>Faça seu pedido agora, direto no WhatsApp. Rápido e sem complicação.</p>
    <a class="solid-btn" href="%%WA%%">Pedir agora</a>
  </div>
</section>

<footer><div class="wrap">
  <div class="top">
    <div class="wordmark f">%%NOME%%</div>
    <div class="fmeta">%%ENDERECO%%<br>%%CIDADE%% · %%TELDISP%%<br>%%HORARIO%%</div>
  </div>
  <div class="rule"></div>
  <div class="cred">Prévia de site · %%NOME%%</div>
</div></footer>

<a class="fab" href="%%WA%%">WhatsApp</a>

<script>
document.addEventListener('DOMContentLoaded',function(){
  var nav=document.getElementById('nav');
  function s(){nav.classList.toggle('solid',scrollY>60)} s();
  addEventListener('scroll',s,{passive:true});
  var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){var el=e.target;var sibs=[].slice.call(el.parentNode.querySelectorAll('.rise'));var i=Math.max(0,sibs.indexOf(el));el.style.transitionDelay=(i*90)+'ms';el.classList.add('in');io.unobserve(el);}})},{threshold:.15});
  document.querySelectorAll('.rise').forEach(function(el){io.observe(el)});
});
</script>
</body></html>"""


def img(kw, lock):
    return "https://loremflickr.com/1600/1200/%s?lock=%d" % (kw, lock)


def render(L):
    tel = re.sub(r"\D", "", L.get("telefone", ""))
    nome = L.get("nome", "Seu Negócio")
    tipo = L.get("tipo", "Negócio")
    cidade = L.get("cidade", "")
    endereco = L.get("endereco", cidade)
    ac, duo, paper, ink = palette_for(tipo, L)
    kw = kw_for(tipo)
    base = abs(hash(L.get("slug") or nome))
    lock = base % 900 + 10
    wa_msg = "Ola! Vim pelo site de voces e queria fazer um pedido."
    wa = "https://wa.me/%s?text=%s" % (tel, urllib.parse.quote(wa_msg)) if tel else "#"
    seg = (tipo or "").lower()
    food = any(k in seg for k in ["pizz", "restaur", "food", "comida", "bar", "boteco", "lanch", "hambur", "caf", "confeit", "doce", "padar", "acai", "açaí", "churrasc", "steak"])
    if food:
        navsec, menukick, menutitle = "cardápio", "Do forno à mesa", "O cardápio"
        cta_word = "fome"
    elif any(k in seg for k in ["barb", "salão", "salao", "cabel", "beleza", "estetic", "estét", "spa", "unha"]):
        navsec, menukick, menutitle = "serviços", "Feito à mão", "Os serviços"
        cta_word = "vontade"
    else:
        navsec, menukick, menutitle = "serviços", "O que fazemos", "Os serviços"
        cta_word = "vontade"
    # menu list (editorial, name + short descriptor, no fake prices)
    itens = L.get("itens", []) or ["Especialidade da casa"]
    descs = ["preparado no capricho, do jeito da casa", "receita da casa, feita na hora",
             "o queridinho de quem já é cliente", "clássico que nunca sai de moda",
             "pra quem gosta de coisa bem feita", "sob medida, do começo ao fim"]
    mlist = ""
    for i, it in enumerate(itens):
        if isinstance(it, dict):
            nm = it.get("nome", ""); pr = it.get("preco", ""); ds = it.get("desc", descs[i % len(descs)])
        else:
            nm = it; pr = ""; ds = descs[(base + i) % len(descs)]
        prhtml = '<div class="pr f">%s</div>' % pr if pr else ""
        mlist += '<div class="mitem"><div class="nm">%s</div>%s<div class="ds">%s</div></div>' % (nm, prhtml, ds)
    # testimonial (single featured)
    who, quote = DEPO_POOL[base % len(DEPO_POOL)]
    # about
    sobre = L.get("sobre", "Tem gente que passa, e tem gente que fica. A %s nasceu em %s pra ser dessas: um lugar onde cada cliente é recebido pelo nome e cada detalhe é pensado com cuidado. Não é sobre ser mais um — é sobre ser o seu preferido." % (nome, cidade or "sua cidade"))
    abouttitle = L.get("about_title", "Feito por quem se importa, pra quem sabe a diferença")
    stars_n = 5
    try:
        stars_n = int(round(float(str(L.get("nota", "5")).replace(",", "."))))
    except Exception:
        stars_n = 5
    stars = "★" * max(1, min(5, stars_n)) + "☆" * (5 - max(1, min(5, stars_n)))
    q = urllib.parse.quote("%s, %s" % (endereco, cidade))
    mapiframe = '<iframe loading="lazy" src="https://www.google.com/maps?q=%s&output=embed" allowfullscreen></iframe>' % q
    headline = L.get("headline", "%s" % nome)
    reps = {
        "NOME": nome, "TIPO": tipo, "CIDADE": cidade, "HEADLINE": headline,
        "TAGLINE": L.get("tagline", "Um clássico do bairro, feito com o cuidado de sempre."),
        "WA": wa, "NOTA": L.get("nota", "5,0"), "AVAL": L.get("avaliacoes", "novas"),
        "STARS": stars, "ANOS": L.get("anos", "10 anos"),
        "HEROIMG": img(kw, lock), "MENUIMG": img(kw, lock + 5), "ABOUTIMG": img(kw, lock + 11), "CTAIMG": img(kw, lock + 17),
        "NAVSEC": navsec, "MENUKICK": menukick, "MENUTITLE": menutitle, "ITENS": mlist,
        "QUOTE": quote, "QUOTEWHO": who, "ABOUTTITLE": abouttitle, "SOBRE": sobre,
        "HORARIO": L.get("horario", "Ter a Dom, 18h às 23h"), "ENDERECO": endereco,
        "TELDISP": L.get("telefone_exibicao", L.get("telefone", "WhatsApp")),
        "STRIP1": L.get("strip", "Peça pelo WhatsApp"), "MAP": mapiframe,
        "COR": ac, "COR2": duo, "PAPER": paper, "INK": ink,
    }
    html = TEMPLATE.replace("%%CTAWORD%%", cta_word)
    for k, v in reps.items():
        html = html.replace("%%" + k + "%%", str(v))
    # fix cta word token used inside h2
    html = html.replace("<em>fome</em>", "<em>%s</em>" % cta_word)
    return html


def outreach_msg(L, url):
    nome = L.get("nome", "seu negócio")
    tipo = (L.get("tipo", "negócio")).lower()
    cidade = L.get("cidade", "")
    nota = L.get("nota", "")
    loc = (" aí em %s" % cidade) if cidade else ""
    star = (" (%s no Google, parabéns!)" % nota) if nota else ""
    return (
        "Oi! Tudo bem? Aqui é o Vitor. Passei pela %s%s%s e vi que vocês ainda "
        "não têm um site próprio — só o Google e o WhatsApp.\n\n"
        "Fiz uma prévia de como ficaria o site de vocês. Dá uma olhada:\n%s\n\n"
        "Se curtir, deixo no ar hoje com o domínio de vocês. Se não fizer sentido, "
        "sem problema nenhum. Um abraço!"
    ) % (nome, loc, star, url)


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
    subprocess.run(["git", "config", "user.name", "fabrica-bot"])
    subprocess.run(["git", "config", "user.email", "bot@fabrica.local"])
    subprocess.run(["git", "add", "-A"])
    subprocess.run(["git", "commit", "-m", "fabrica: build %d demos" % len(built)])
    subprocess.run(["git", "push"])
    chats = resolve_chats()
    if not chats:
        print("NO CHAT IDS - user must /start the bot"); return
    tg("sendMessage", {"chat_id": chats[0],
        "text": "*Lote pronto:* %d previas no ar.\nToque em *Ver previa*, depois em *Enviar no WhatsApp*." % len(built),
        "parse_mode": "Markdown"})
    for L, url in built:
        tel = re.sub(r"\D", "", L.get("telefone", ""))
        wa = "https://wa.me/%s?text=%s" % (tel, urllib.parse.quote(outreach_msg(L, url))) if tel else url
        head = "*%s* — %s" % (L.get("nome", "?"), L.get("cidade", ""))
        meta = "%s · %s" % (L.get("tipo", ""), L.get("nota", "")) if L.get("nota") else L.get("tipo", "")
        for ch in chats:
            tg("sendMessage", {"chat_id": ch, "text": "%s\n%s" % (head, meta),
                "parse_mode": "Markdown",
                "reply_markup": {"inline_keyboard": [[
                    {"text": "Ver previa", "url": url},
                    {"text": "Enviar no WhatsApp", "url": wa}]]}})
            time.sleep(0.4)
    print("done:", len(built))


if __name__ == "__main__":
    main()
