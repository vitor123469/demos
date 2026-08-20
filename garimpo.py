import os, re, json, time, datetime, pathlib, urllib.request, urllib.parse

APIFY = os.environ.get("APIFY", "").strip()
TG = os.environ.get("TG", "").strip()
ACTOR = "compass~crawler-google-places"
BASE = "https://api.apify.com/v2"

# rotacao para runs agendados (sem input)
NICHOS = ["pizzaria", "barbearia", "restaurante", "estetica", "hamburgueria",
          "salao de beleza", "lanchonete", "clinica de estetica", "pet shop", "acai"]
CIDADES = ["Campinas SP", "Ribeirao Preto SP", "Sorocaba SP", "Sao Jose do Rio Preto SP",
           "Juiz de Fora MG", "Uberlandia MG", "Londrina PR", "Maringa PR",
           "Caxias do Sul RS", "Joinville SC", "Niteroi RJ", "Vitoria ES",
           "Feira de Santana BA", "Uberaba MG", "Bauru SP", "Franca SP"]


def apify_get(path):
    url = "%s%s%stoken=%s" % (BASE, path, ("&" if "?" in path else "?"), APIFY)
    with urllib.request.urlopen(url, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))


def apify_post(path, body):
    url = "%s%s?token=%s" % (BASE, path, APIFY)
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
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
    # sinais de dono engajado
    if p.get("imagesCount") or p.get("imageUrl"):
        s += 3
    return s


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
        raw = urllib.request.urlopen(
            "https://api.telegram.org/bot%s/getUpdates" % TG, timeout=30).read()
        upd = json.loads(raw.decode("utf-8"))
        for u in upd.get("result", []):
            m = u.get("message") or u.get("edited_message") or u.get("channel_post") or {}
            ch = (m.get("chat") or {}).get("id")
            if ch:
                pathlib.Path("data").mkdir(exist_ok=True)
                json.dump({"chat_id": ch}, open(cfgp, "w"), ensure_ascii=False, indent=2)
                print("chat_id salvo:", ch)
                return
    except Exception as e:
        print("chat err", e)


def main():
    nicho = os.environ.get("NICHO", "").strip()
    local = os.environ.get("LOCAL", "").strip()
    try:
        qtd = int(os.environ.get("QTD", "15") or "15")
    except Exception:
        qtd = 15
    if not nicho or not local:
        idx = datetime.date.today().toordinal()
        nicho = NICHOS[idx % len(NICHOS)]
        local = CIDADES[idx % len(CIDADES)]
    print("Garimpando:", nicho, "em", local, "| alvo:", qtd)

    ensure_chat()

    run_input = {
        "searchStringsArray": [nicho],
        "locationQuery": local,
        "maxCrawledPlacesPerSearch": min(120, max(50, qtd * 5)),
        "language": "pt-BR",
        "countryCode": "br",
        "skipClosedPlaces": True,
        "website": "withoutWebsite",
        "scrapePlaceDetailPage": True,
        "maxReviews": 0, "maxImages": 0, "maxQuestions": 0,
    }
    run = apify_post("/acts/%s/runs" % ACTOR, run_input)
    rid = run["data"]["id"]
    ds = run["data"]["defaultDatasetId"]
    print("run:", rid, "dataset:", ds)

    status = "READY"
    for _ in range(120):
        time.sleep(10)
        st = apify_get("/actor-runs/%s" % rid)
        status = st["data"]["status"]
        if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            break
    print("status:", status)

    items = apify_get("/datasets/%s/items?clean=true" % ds)
    if not isinstance(items, list):
        items = []
    print("brutos:", len(items))

    scored = []
    for p in items:
        sc = score(p)
        if sc >= 70:
            scored.append((sc, p))
    scored.sort(key=lambda x: x[0], reverse=True)
    print("qualificados (score>=70):", len(scored))

    leads = []
    seen = set()
    for sc, p in scored[:qtd]:
        tel = intl(p.get("phoneUnformatted") or p.get("phone") or "")
        if tel in seen:
            continue
        seen.add(tel)
        nome = p.get("title") or "Negocio"
        cidade = p.get("city") or local
        nota = p.get("totalScore")
        leads.append({
            "slug": slugify("%s-%s" % (nome, cidade)),
            "nome": nome,
            "tipo": p.get("categoryName") or nicho.capitalize(),
            "cidade": cidade,
            "bairro": p.get("neighborhood") or "",
            "telefone": tel,
            "telefone_exibicao": p.get("phone") or "",
            "nota": (("%.1f" % float(nota)).replace(".", ",")) if nota else "",
            "avaliacoes": str(p.get("reviewsCount") or ""),
            "endereco": p.get("address") or p.get("street") or cidade,
            "_score": sc,
        })

    pathlib.Path("data").mkdir(exist_ok=True)
    json.dump(leads, open("data/leads.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("leads gravados:", len(leads))
    for L in leads:
        print("  [%d] %s - %s (%s aval, nota %s) %s" % (
            L["_score"], L["nome"], L["cidade"], L["avaliacoes"], L["nota"], L["telefone"]))


if __name__ == "__main__":
    main()
