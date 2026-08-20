import os, re, json, time, datetime, pathlib, subprocess, urllib.request

APIFY = os.environ.get("APIFY", "").strip()
TG = os.environ.get("TG", "").strip()
ACTOR = "compass~crawler-google-places"
BASE = "https://api.apify.com/v2"
QUEUE = "data/queue.json"

NICHOS = ["pizzaria", "barbearia", "restaurante", "estetica", "hamburgueria",
          "salao de beleza", "lanchonete", "clinica de estetica", "pet shop",
          "acai", "confeitaria", "oficina mecanica"]
CIDADES = ["Campinas SP", "Ribeirao Preto SP", "Sorocaba SP", "Sao Jose do Rio Preto SP",
           "Bauru SP", "Franca SP", "Piracicaba SP", "Jundiai SP", "Marilia SP",
           "Presidente Prudente SP", "Juiz de Fora MG", "Uberlandia MG", "Uberaba MG",
           "Montes Claros MG", "Divinopolis MG", "Governador Valadares MG",
           "Londrina PR", "Maringa PR", "Ponta Grossa PR", "Cascavel PR", "Foz do Iguacu PR",
           "Caxias do Sul RS", "Pelotas RS", "Santa Maria RS", "Joinville SC",
           "Blumenau SC", "Chapeco SC", "Niteroi RJ", "Campos dos Goytacazes RJ",
           "Vitoria ES", "Vila Velha ES", "Feira de Santana BA", "Vitoria da Conquista BA",
           "Caruaru PE", "Juazeiro do Norte CE", "Aparecida de Goiania GO", "Anapolis GO",
           "Dourados MS", "Cuiaba MT", "Sao Luis MA"]


def apify_get(path):
    url = "%s%s%stoken=%s" % (BASE, path, ("&" if "?" in path else "?"), APIFY)
    with urllib.request.urlopen(url, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))


def apify_post(path, body):
    url = "%s%s?token=%s" % (BASE, path, APIFY)
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))


def digits(s):
    return re.sub(r"\D", "", s or "")


def is_mobile_br(ph):
    d = digits(ph)
    if d.startswith("55"):
        d = d[2:]
    return len(d) == 11 and d[2] == "9"


def intl(ph):
    d = digits(ph)
    if not d.startswith("55") and len(d) in (10, 11):
        d = "55" + d
    return d


def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
    return s or "lead"


def score(p):
    if p.get("permanentlyClosed") or p.get("temporarilyClosed"):
        return -1
    if (p.get("website") or "").strip():
        return -1
    ph = p.get("phoneUnformatted") or p.get("phone") or ""
    if not digits(ph):
        return -1
    s = 45 if is_mobile_br(ph) else 5
    try:
        r = float(p.get("totalScore") or 0)
    except Exception:
        r = 0
    if r >= 4.5:
        s += 25
    elif r >= 4.0:
        s += 18
    elif r >= 3.5:
        s += 8
    try:
        rc = int(p.get("reviewsCount") or 0)
    except Exception:
        rc = 0
    if rc >= 100:
        s += 25
    elif rc >= 50:
        s += 18
    elif rc >= 20:
        s += 12
    elif rc >= 5:
        s += 5
    if p.get("imagesCount") or p.get("imageUrl"):
        s += 3
    return s


def to_lead(p, hint):
    nome = p.get("title") or "Negocio"
    cidade = p.get("city") or ""
    nota = p.get("totalScore")
    return {
        "slug": slugify("%s-%s" % (nome, cidade)),
        "nome": nome, "tipo": p.get("categoryName") or hint, "cidade": cidade,
        "bairro": p.get("neighborhood") or "",
        "telefone": intl(p.get("phoneUnformatted") or p.get("phone") or ""),
        "telefone_exibicao": p.get("phone") or "",
        "nota": (("%.1f" % float(nota)).replace(".", ",")) if nota else "",
        "avaliacoes": str(p.get("reviewsCount") or ""),
        "endereco": p.get("address") or cidade, "_score": score(p),
    }


def load_queue():
    if os.path.exists(QUEUE):
        try:
            return json.load(open(QUEUE, encoding="utf-8"))
        except Exception:
            return []
    return []


def save_queue(q):
    pathlib.Path("data").mkdir(exist_ok=True)
    json.dump(q, open(QUEUE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def commit(msg):
    subprocess.run(["git", "config", "user.name", "fabrica-bot"])
    subprocess.run(["git", "config", "user.email", "bot@fabrica.local"])
    subprocess.run(["git", "add", "-A"])
    subprocess.run(["git", "commit", "-m", msg])
    subprocess.run(["git", "push"])


def ensure_chat():
    cfgp = "data/config.json"
    if os.path.exists(cfgp):
        try:
            if json.load(open(cfgp)).get("chat_id"):
                return
        except Exception:
            pass
    if not TG:
        return
    try:
        raw = urllib.request.urlopen("https://api.telegram.org/bot%s/getUpdates" % TG, timeout=30).read()
        for u in json.loads(raw.decode("utf-8")).get("result", []):
            m = u.get("message") or u.get("edited_message") or u.get("channel_post") or {}
            ch = (m.get("chat") or {}).get("id")
            if ch:
                pathlib.Path("data").mkdir(exist_ok=True)
                json.dump({"chat_id": ch}, open(cfgp, "w"), ensure_ascii=False, indent=2)
                print("chat_id salvo:", ch)
                return
    except Exception as e:
        print("chat err", e)


def scrape(searches, per):
    run_input = {
        "searchStringsArray": searches, "maxCrawledPlacesPerSearch": per,
        "language": "pt-BR", "countryCode": "br", "skipClosedPlaces": True,
        "website": "withoutWebsite", "scrapePlaceDetailPage": True,
        "maxReviews": 0, "maxImages": 0, "maxQuestions": 0,
    }
    run = apify_post("/acts/%s/runs" % ACTOR, run_input)
    rid = run["data"]["id"]
    ds = run["data"]["defaultDatasetId"]
    print("run:", rid, "| buscas:", len(searches))
    status = "READY"
    for _ in range(360):
        time.sleep(10)
        status = apify_get("/actor-runs/%s" % rid)["data"]["status"]
        if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            break
    print("status:", status)
    items = apify_get("/datasets/%s/items?clean=true" % ds)
    return items if isinstance(items, list) else []


def merge(items, hint):
    q = load_queue()
    seen = set(L.get("telefone") for L in q)
    added = 0
    for p in items:
        if score(p) >= 70:
            L = to_lead(p, hint)
            if L["telefone"] and L["telefone"] not in seen:
                seen.add(L["telefone"])
                q.append(L)
                added += 1
    q.sort(key=lambda L: L.get("_score", 0), reverse=True)
    save_queue(q)
    return added, len(q)


def harvest():
    nn = int(os.environ.get("NN", "5") or "5")
    nc = int(os.environ.get("NC", "6") or "6")
    per = int(os.environ.get("PER", "30") or "30")
    niches = NICHOS[:nn]
    off = (datetime.date.today().toordinal() * nc) % len(CIDADES)
    cities = (CIDADES + CIDADES)[off:off + nc]
    searches = ["%s em %s" % (n, c) for n in niches for c in cities]
    print("HARVEST:", len(searches), "buscas |", nn, "nichos x", nc, "cidades x", per, "lugares")
    items = scrape(searches, per)
    print("brutos:", len(items))
    added, total = merge(items, "Negocio")
    print("qualificados novos:", added, "| FILA TOTAL:", total)
    commit("harvest: +%d leads (fila %d)" % (added, total))


def dose():
    ensure_chat()
    try:
        n = int(os.environ.get("QTD", "40") or "40")
    except Exception:
        n = 40
    q = load_queue()
    if len(q) < n:
        print("Fila baixa (%d < %d), reabastecendo..." % (len(q), n))
        harvest()
        q = load_queue()
    take = q[:n]
    rest = q[n:]
    pathlib.Path("data").mkdir(exist_ok=True)
    json.dump(take, open("data/leads.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    save_queue(rest)
    print("DOSE:", len(take), "leads | restam na fila:", len(rest))


def main():
    mode = (os.environ.get("MODE", "dose") or "dose").strip().lower()
    nicho = os.environ.get("NICHO", "").strip()
    local = os.environ.get("LOCAL", "").strip()
    if nicho and local:
        print("Busca manual:", nicho, "em", local)
        items = scrape(["%s em %s" % (nicho, local)], int(os.environ.get("PER", "60") or "60"))
        added, total = merge(items, nicho.capitalize())
        print("qualificados novos:", added, "| fila:", total)
        dose()
    elif mode == "harvest":
        harvest()
    else:
        dose()


if __name__ == "__main__":
    main()
