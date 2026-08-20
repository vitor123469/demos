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


def kw_for(tipo):
    s = (tipo or "").lower()
    if any(k in s for k in ["pizz"]): return "pizza,italian,restaurant"
    if any(k in s for k in ["hambur", "lanch", "burg"]): return "burger,food"
    if any(k in s for k in ["restaur", "food", "comida", "bar", "boteco"]): return "restaurant,food,dish"
    if any(k in s for k in ["caf", "confeit", "doce", "padar", "bake"]): return "cafe,bakery,coffee"
    if any(k in s for k in ["acai", "açaí", "sorvet", "gelat"]): return "acai,dessert"
    if any(k in s for k in ["barb"]): return "barbershop,haircut,beard"
    if any(k in s for k in ["salão", "salao", "cabel", "beleza", "hair"]): return "hairsalon,beauty"
    if any(k in s for k in ["estetic", "estét", "spa", "unha", "clinic", "clín"]): return "spa,beauty,wellness"
    if any(k in s for k in ["academ", "fit", "cross", "gym"]): return "gym,fitness"
    if any(k in s for k in ["pet", "veterin"]): return "pet,dog,animal"
    if any(k in s for k in ["auto", "mecan", "mecân", "car"]): return "car,garage,auto"
    return "business,shop,store"


DEPO_POOL = [
    ("Mariana Alves", "Melhor experiência que já tive na região. Atendimento nota 10 e qualidade impecável!"),
    ("Rafael Souza", "Virei cliente fiel. Recomendo de olhos fechados pra todo mundo do bairro."),
    ("Juliana Costa", "Simplesmente perfeito. Rápido, caprichado e com um preço que vale muito a pena."),
    ("Bruno Martins", "Sensacional! Já indiquei pra família toda. Padrão de qualidade que não cai nunca."),
    ("Carla Ribeiro", "Apaixonada! Cada detalhe é pensado com carinho. Voltarei muitas vezes."),
    ("Diego Fernandes", "Superou minhas expectativas. Profissionais atenciosos e resultado incrível."),
]


TEMPLATE = """<!doctype html>
<html lang="pt-br"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>%%NOME%% — %%TIPO%% em %%CIDADE%%</title>
<meta name="description" content="%%NOME%% — %%TAGLINE%%">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{--c:%%COR%%;--c2:%%COR2%%;--ink:#141419;--muted:#6b7280;--bg:#ffffff;--soft:#f6f7f9;--radius:22px}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{font-family:Inter,system-ui,sans-serif;color:var(--ink);background:var(--bg);line-height:1.65;-webkit-font-smoothing:antialiased}
h1,h2,h3,.display{font-family:Sora,sans-serif;letter-spacing:-.02em;line-height:1.08}
a{text-decoration:none;color:inherit}
img{display:block;max-width:100%}
.wrap{max-width:1120px;margin:0 auto;padding:0 22px}
.reveal{opacity:0;transform:translateY(26px);transition:opacity .7s cubic-bezier(.2,.7,.2,1),transform .7s cubic-bezier(.2,.7,.2,1)}
.reveal.in{opacity:1;transform:none}
/* NAV */
.nav{position:fixed;top:0;left:0;right:0;z-index:50;display:flex;align-items:center;justify-content:space-between;padding:16px 22px;transition:.35s}
.nav.solid{background:rgba(255,255,255,.82);backdrop-filter:blur(14px);box-shadow:0 6px 24px rgba(0,0,0,.06)}
.brand{font-family:Sora;font-weight:800;font-size:20px;color:#fff;transition:.35s;display:flex;align-items:center;gap:9px}
.brand .b-dot{width:11px;height:11px;border-radius:50%;background:var(--c)}
.nav.solid .brand{color:var(--ink)}
.nav-cta{background:var(--c);color:#fff;font-weight:600;font-size:14px;padding:11px 20px;border-radius:999px;box-shadow:0 8px 22px rgba(0,0,0,.18);transition:transform .15s}
.nav-cta:hover{transform:translateY(-2px)}
/* HERO */
.hero{position:relative;min-height:100vh;display:flex;align-items:center;color:#fff;overflow:hidden}
.hero-bg{position:absolute;inset:0;background-image:linear-gradient(120deg,rgba(10,10,15,.82),rgba(10,10,15,.35)),url("%%HEROIMG%%");background-size:cover;background-position:center;transform:scale(1.06);animation:zoom 18s ease-in-out infinite alternate}
@keyframes zoom{to{transform:scale(1)}}
.hero-inner{position:relative;z-index:2;padding:120px 0 80px}
.eyebrow{display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.22);padding:8px 16px;border-radius:999px;font-size:13px;font-weight:600;margin-bottom:22px;backdrop-filter:blur(6px)}
.hero h1{font-size:clamp(38px,7vw,74px);font-weight:800;max-width:15ch;margin-bottom:20px}
.hero p.lead{font-size:clamp(17px,2.4vw,22px);max-width:56ch;opacity:.92;margin-bottom:34px;font-weight:400}
.btn-row{display:flex;gap:14px;flex-wrap:wrap;align-items:center}
.btn{display:inline-flex;align-items:center;gap:10px;font-weight:600;font-size:16px;padding:16px 30px;border-radius:14px;transition:transform .15s,box-shadow .15s}
.btn-wa{background:#25D366;color:#fff;box-shadow:0 12px 34px rgba(37,211,102,.4)}
.btn-wa:hover{transform:translateY(-3px)}
.btn-ghost{background:rgba(255,255,255,.12);color:#fff;border:1px solid rgba(255,255,255,.3)}
.hero .rate{margin-top:30px;display:flex;align-items:center;gap:12px;font-size:15px;opacity:.95}
.hero .rate .st{color:#ffce31;letter-spacing:2px}
.scrolld{position:absolute;bottom:26px;left:50%;transform:translateX(-50%);z-index:2;color:#fff;opacity:.7;font-size:12px;letter-spacing:.2em;text-transform:uppercase}
/* STATS */
.stats{background:var(--ink);color:#fff;padding:34px 0}
.stats .grid{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;text-align:center}
.stat b{font-family:Sora;font-size:34px;font-weight:800;display:block;background:linear-gradient(120deg,#fff,#c9c9d6);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.stat span{font-size:13px;opacity:.6;text-transform:uppercase;letter-spacing:.08em}
/* SECTIONS */
section.pad{padding:96px 0}
.khead{text-align:center;max-width:640px;margin:0 auto 54px}
.ktag{color:var(--c);font-weight:700;font-size:13px;letter-spacing:.14em;text-transform:uppercase;margin-bottom:12px}
.khead h2{font-size:clamp(28px,4vw,44px);font-weight:800;margin-bottom:14px}
.khead p{color:var(--muted);font-size:17px}
.menu{display:grid;grid-template-columns:repeat(3,1fr);gap:26px}
.mcard{background:var(--bg);border:1px solid #ededf2;border-radius:var(--radius);overflow:hidden;transition:transform .3s,box-shadow .3s}
.mcard:hover{transform:translateY(-8px);box-shadow:0 26px 60px rgba(0,0,0,.13)}
.mcard .ph{height:190px;background-size:cover;background-position:center}
.mcard .bd{padding:22px 22px 26px}
.mcard h3{font-size:20px;font-weight:700;margin-bottom:6px}
.mcard p{color:var(--muted);font-size:14px}
.mcard .tagp{display:inline-block;margin-top:14px;color:var(--c);font-weight:700;font-size:14px}
/* ABOUT */
.about{display:grid;grid-template-columns:1.05fr .95fr;gap:56px;align-items:center}
.about .ph{border-radius:var(--radius);height:420px;background-size:cover;background-position:center;box-shadow:0 30px 70px rgba(0,0,0,.18)}
.about h2{font-size:clamp(26px,3.6vw,40px);font-weight:800;margin-bottom:18px}
.about p{color:#4b4b55;font-size:16.5px;margin-bottom:16px}
.checks{list-style:none;margin-top:22px;display:grid;gap:12px}
.checks li{display:flex;gap:12px;align-items:flex-start;font-weight:500}
.checks .ck{flex:none;width:24px;height:24px;border-radius:50%;background:var(--c);color:#fff;display:grid;place-items:center;font-size:13px}
/* DEPO */
.depo{background:var(--soft)}
.dgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}
.dcard{background:#fff;border-radius:var(--radius);padding:30px;box-shadow:0 10px 34px rgba(0,0,0,.05)}
.dcard .st{color:#ffb400;letter-spacing:2px;margin-bottom:14px}
.dcard p{font-size:15.5px;color:#3a3a44;margin-bottom:20px}
.who{display:flex;align-items:center;gap:12px}
.who img{width:46px;height:46px;border-radius:50%}
.who b{font-size:15px}.who span{font-size:13px;color:var(--muted)}
/* LOCAL */
.local{display:grid;grid-template-columns:1fr 1fr;gap:0;border-radius:var(--radius);overflow:hidden;box-shadow:0 24px 60px rgba(0,0,0,.12)}
.local .map{min-height:440px}
.local .map iframe{width:100%;height:100%;border:0;min-height:440px}
.local .info{background:var(--ink);color:#fff;padding:48px}
.local .info h2{font-size:30px;font-weight:800;margin-bottom:26px}
.irow{display:flex;gap:14px;margin-bottom:22px}
.irow .ic{flex:none;width:42px;height:42px;border-radius:12px;background:rgba(255,255,255,.1);display:grid;place-items:center;font-size:19px}
.irow b{display:block;font-size:12px;text-transform:uppercase;letter-spacing:.1em;opacity:.55;margin-bottom:2px}
.irow span{font-size:15.5px}
/* CTA */
.cta{background:linear-gradient(120deg,var(--c),var(--c2));color:#fff;text-align:center;padding:84px 0}
.cta h2{font-size:clamp(28px,4vw,46px);font-weight:800;margin-bottom:16px}
.cta p{font-size:18px;opacity:.92;margin-bottom:30px}
.cta .btn-wa{background:#fff;color:var(--c)}
/* FOOT */
footer{background:#0d0d12;color:#8b8b98;padding:52px 0 40px;text-align:center}
footer .fb{font-family:Sora;font-weight:800;color:#fff;font-size:22px;margin-bottom:8px}
footer .cred{margin-top:20px;font-size:12.5px;opacity:.5}
/* FLOAT */
.fab{position:fixed;bottom:22px;right:22px;z-index:60;width:62px;height:62px;border-radius:50%;background:#25D366;display:grid;place-items:center;box-shadow:0 12px 30px rgba(37,211,102,.5);animation:pulse 2.4s infinite}
.fab svg{width:32px;height:32px;fill:#fff}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(37,211,102,.5)}70%{box-shadow:0 0 0 18px rgba(37,211,102,0)}100%{box-shadow:0 0 0 0 rgba(37,211,102,0)}}
@media(max-width:860px){.menu,.dgrid{grid-template-columns:1fr 1fr}.stats .grid{grid-template-columns:1fr 1fr;gap:26px}.about,.local{grid-template-columns:1fr}.about .ph{height:280px}.local .map iframe{min-height:300px}}
@media(max-width:560px){.menu,.dgrid{grid-template-columns:1fr}.hero-inner{padding-top:104px}}
</style></head><body>

<nav class="nav" id="nav">
<div class="brand"><span class="b-dot"></span>%%NOME%%</div>
<a class="nav-cta" href="%%WA%%">Falar no WhatsApp</a>
</nav>

<header class="hero">
<div class="hero-bg"></div>
<div class="wrap hero-inner">
<span class="eyebrow">★ %%TIPO%% %%BADGELOC%%</span>
<h1>%%NOME%%</h1>
<p class="lead">%%TAGLINE%%</p>
<div class="btn-row">
<a class="btn btn-wa" href="%%WA%%">📲 Fazer pedido agora</a>
<a class="btn btn-ghost" href="#cardapio">Ver %%DESTLABEL%%</a>
</div>
<div class="rate"><span class="st">★★★★★</span> <span>%%NOTA%% no Google · %%AVAL%% avaliações</span></div>
</div>
<div class="scrolld">role para descobrir ↓</div>
</header>

<div class="stats"><div class="wrap"><div class="grid">
<div class="stat reveal"><b>%%NOTA%%</b><span>Nota no Google</span></div>
<div class="stat reveal"><b>%%AVAL%%+</b><span>Clientes felizes</span></div>
<div class="stat reveal"><b>%%ANOS%%</b><span>De história</span></div>
<div class="stat reveal"><b>100%</b><span>Feito com amor</span></div>
</div></div></div>

<section class="pad" id="cardapio"><div class="wrap">
<div class="khead reveal"><div class="ktag">%%DESTTAG%%</div><h2>%%DESTTITULO%%</h2><p>%%DESTSUB%%</p></div>
<div class="menu">%%ITENS%%</div>
</div></section>

<section class="pad" style="background:var(--soft)"><div class="wrap">
<div class="about">
<div class="ph reveal" style="background-image:url('%%ABOUTIMG%%')"></div>
<div class="reveal">
<div class="ktag">Sobre nós</div>
<h2>Uma experiência que o seu bairro confia</h2>
<p>%%SOBRE%%</p>
<ul class="checks">
<li><span class="ck">✓</span> Atendimento rápido e caprichado, do pedido à entrega</li>
<li><span class="ck">✓</span> Qualidade reconhecida com %%NOTA%%★ e %%AVAL%% avaliações</li>
<li><span class="ck">✓</span> Peça em segundos direto pelo WhatsApp</li>
</ul>
</div>
</div>
</div></section>

<section class="pad depo"><div class="wrap">
<div class="khead reveal"><div class="ktag">Depoimentos</div><h2>Quem conhece, recomenda</h2><p>Avaliações reais de quem já é cliente</p></div>
<div class="dgrid">%%DEPO%%</div>
</div></section>

<section class="pad"><div class="wrap">
<div class="local">
<div class="map">%%MAP%%</div>
<div class="info">
<h2>Venha nos visitar</h2>
<div class="irow"><div class="ic">📍</div><div><b>Endereço</b><span>%%ENDERECO%%</span></div></div>
<div class="irow"><div class="ic">🕒</div><div><b>Horário</b><span>%%HORARIO%%</span></div></div>
<div class="irow"><div class="ic">📱</div><div><b>Contato</b><span>%%TELDISP%%</span></div></div>
<a class="btn btn-wa" style="margin-top:8px" href="%%WA%%">Chamar no WhatsApp</a>
</div>
</div>
</div></section>

<section class="cta"><div class="wrap reveal">
<h2>Bateu a vontade?</h2>
<p>Faça seu pedido agora — é rápido, fácil e direto no WhatsApp.</p>
<a class="btn btn-wa" href="%%WA%%">📲 Pedir pelo WhatsApp</a>
</div></section>

<footer><div class="wrap">
<div class="fb">%%NOME%%</div>
<div>%%ENDERECO%% · %%CIDADE%%</div>
<div style="margin-top:6px">%%TELDISP%%</div>
<div class="cred">Site desenvolvido sob medida · prévia exclusiva para %%NOME%%</div>
</div></footer>

<a class="fab" href="%%WA%%" aria-label="WhatsApp"><svg viewBox="0 0 24 24"><path d="M.057 24l1.687-6.163a11.867 11.867 0 01-1.587-5.945C.16 5.335 5.495 0 12.05 0a11.82 11.82 0 018.413 3.488 11.82 11.82 0 013.48 8.414c-.003 6.557-5.338 11.892-11.893 11.892a11.9 11.9 0 01-5.688-1.448L.057 24zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884a9.86 9.86 0 001.517 5.26l-.999 3.648 3.971-1.007zm11.387-5.464c-.074-.124-.272-.198-.57-.347-.297-.149-1.758-.868-2.031-.967-.272-.099-.47-.149-.669.149-.198.297-.767.967-.94 1.165-.173.198-.347.223-.644.074-.297-.149-1.255-.462-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.297-.347.446-.521.151-.172.2-.296.3-.495.099-.198.05-.372-.025-.521-.075-.148-.669-1.611-.916-2.206-.242-.579-.487-.501-.669-.51l-.57-.01c-.198 0-.52.074-.792.372s-1.04 1.016-1.04 2.479 1.065 2.876 1.213 3.074c.149.198 2.095 3.2 5.076 4.487.71.306 1.263.489 1.694.626.712.226 1.36.194 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.695.248-1.29.173-1.414z"/></svg></a>

<script>
document.addEventListener('DOMContentLoaded',function(){
var nav=document.getElementById('nav');
function s(){nav.classList.toggle('solid',window.scrollY>60)}
s();window.addEventListener('scroll',s,{passive:true});
var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}})},{threshold:.14});
document.querySelectorAll('.reveal').forEach(function(el){io.observe(el)});
});
</script>
</body></html>"""


def render(L):
    tel = re.sub(r"\D", "", L.get("telefone", ""))
    nome = L.get("nome", "Seu Negócio")
    tipo = L.get("tipo", "Negócio")
    cidade = L.get("cidade", "")
    bairro = L.get("bairro", "")
    endereco = L.get("endereco", cidade)
    cat = kw_for(tipo)
    lock = abs(hash(L.get("slug") or nome)) % 900 + 10
    heroimg = "https://loremflickr.com/1600/900/%s?lock=%d" % (cat, lock)
    aboutimg = "https://loremflickr.com/900/700/%s?lock=%d" % (cat, lock + 3)
    wa_msg = "Ola! Vim pelo site de voces e quero fazer um pedido :)"
    wa = "https://wa.me/%s?text=%s" % (tel, urllib.parse.quote(wa_msg)) if tel else "#"
    # menu / services cards with images
    itens = L.get("itens", []) or ["Qualidade garantida"]
    cards = ""
    for i, it in enumerate(itens):
        ikw = urllib.parse.quote(it.split()[0]) + "," + cat.split(",")[0]
        img = "https://loremflickr.com/600/400/%s?lock=%d" % (ikw, lock + 20 + i)
        cards += ('<div class="mcard reveal"><div class="ph" style="background-image:url(\'%s\')"></div>'
                  '<div class="bd"><h3>%s</h3><p>Preparado com ingredientes selecionados e todo o capricho da casa.</p>'
                  '<span class="tagp">Peça no WhatsApp →</span></div></div>') % (img, it)
    # segment labels
    seg = (tipo or "").lower()
    if any(k in seg for k in ["pizz", "restaur", "lanch", "hambur", "food", "bar", "caf", "doce", "confeit", "acai", "açaí", "padar"]):
        dtag, dtitulo, dsub, dlabel = "Nosso cardápio", "Sabores que você vai amar", "Feito na hora, do jeito que você gosta", "cardápio"
    elif any(k in seg for k in ["barb", "salão", "salao", "estetic", "estét", "beleza", "cabel", "unha", "spa"]):
        dtag, dtitulo, dsub, dlabel = "Nossos serviços", "Cuidado em cada detalhe", "Profissionais dedicados ao seu melhor visual", "serviços"
    else:
        dtag, dtitulo, dsub, dlabel = "O que oferecemos", "Qualidade que faz a diferença", "Soluções sob medida para você", "serviços"
    # testimonials
    depo = ""
    base = abs(hash(nome))
    for j in range(3):
        who, quote = DEPO_POOL[(base + j) % len(DEPO_POOL)]
        av = "https://ui-avatars.com/api/?name=%s&background=random&size=96" % urllib.parse.quote(who)
        depo += ('<div class="dcard reveal"><div class="st">★★★★★</div><p>“%s”</p>'
                 '<div class="who"><img src="%s" alt=""><div><b>%s</b><span>Cliente verificado</span></div></div></div>') % (quote, av, who)
    # map
    q = urllib.parse.quote("%s, %s" % (endereco, cidade))
    mapsrc = "https://www.google.com/maps?q=%s&output=embed" % q
    mapiframe = '<iframe loading="lazy" src="%s" allowfullscreen></iframe>' % mapsrc
    sobre = L.get("sobre", "Somos referência em %s na região de %s. Cada cliente é tratado como único, com atenção aos detalhes e o compromisso de entregar sempre o melhor. Venha viver essa experiência." % (tipo.lower(), cidade or "sua cidade"))
    badgeloc = ("· " + bairro + ", " + cidade) if (bairro and cidade) else ("· " + cidade if cidade else "")
    reps = {
        "NOME": nome, "TIPO": tipo, "CIDADE": cidade, "BADGELOC": badgeloc,
        "TAGLINE": L.get("tagline", "Atendimento de qualidade que o seu bairro confia."),
        "WA": wa, "NOTA": L.get("nota", "5,0"), "AVAL": L.get("avaliacoes", "novas"),
        "ANOS": L.get("anos", "10 anos"), "HEROIMG": heroimg, "ABOUTIMG": aboutimg,
        "ITENS": cards, "DEPO": depo, "MAP": mapiframe, "SOBRE": sobre,
        "DESTTAG": dtag, "DESTTITULO": dtitulo, "DESTSUB": dsub, "DESTLABEL": dlabel,
        "HORARIO": L.get("horario", "Seg a Sáb, 9h às 19h"), "ENDERECO": endereco,
        "TELDISP": L.get("telefone_exibicao", L.get("telefone", "WhatsApp")),
        "COR": L.get("cor", "#e11d48"), "COR2": L.get("cor2", "#9f1239"),
    }
    html = TEMPLATE
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
    subprocess.run(["git", "config", "user.name", "fabrica-bot"])
    subprocess.run(["git", "config", "user.email", "bot@fabrica.local"])
    subprocess.run(["git", "add", "-A"])
    subprocess.run(["git", "commit", "-m", "fabrica: build %d demos" % len(built)])
    subprocess.run(["git", "push"])
    chats = resolve_chats()
    if not chats:
        print("NO CHAT IDS - user must /start the bot"); return
    tg("sendMessage", {"chat_id": chats[0],
        "text": "🏭 *Lote pronto:* %d prévias no ar.\nToque em *Ver prévia*, depois em *Enviar no WhatsApp*." % len(built),
        "parse_mode": "Markdown"})
    for L, url in built:
        tel = re.sub(r"\D", "", L.get("telefone", ""))
        wa = "https://wa.me/%s?text=%s" % (tel, urllib.parse.quote(outreach_msg(L, url))) if tel else url
        head = "🏪 *%s* — %s" % (L.get("nome", "?"), L.get("cidade", ""))
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
