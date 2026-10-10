from html.parser import HTMLParser


class HeadingParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.h1 = 0
        self.in_h1 = False
        self.h1_text = ""

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "h1":
            self.h1 += 1
            self.in_h1 = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "h1":
            self.in_h1 = False

    def handle_data(self, data: str) -> None:
        if self.in_h1:
            self.h1_text += data


def test_homepage_renders(client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    assert "Sua próxima oportunidade começa aqui." in html
    assert 'name="description"' in html
    assert 'rel="canonical"' in html
    assert "og:title" in html
    assert "twitter:card" in html
    assert "Organization" in html
    assert "WebSite" in html
    assert "JobPosting" not in html
    parser = HeadingParser()
    parser.feed(html)
    assert parser.h1 == 1
    assert "Sua próxima oportunidade começa aqui." in parser.h1_text


def test_search_form_points_to_jobs(client):
    html = client.get("/").text
    assert 'action="/vagas"' in html
    assert 'method="get"' in html
    assert 'name="q"' in html
    assert 'name="cidade"' in html
    assert 'name="remoto"' in html


def test_jobs_accept_get_filters(client):
    response = client.get("/vagas", params={"q": "Python", "cidade": "", "remoto": "1"})
    assert response.status_code == 200
    assert "Vagas de emprego" in response.text


def test_robots_and_sitemap(client):
    robots = client.get("/robots.txt")
    sitemap = client.get("/sitemap.xml")
    assert robots.status_code == 200
    assert "Sitemap:" in robots.text
    assert sitemap.status_code == 200
    assert "http://testserver/" in sitemap.text


def test_ads_are_disabled_by_default(client):
    html = client.get("/").text
    assert "adsbygoogle" not in html
    assert "Publicidade" not in html


def test_demo_jobs_are_labeled(client):
    html = client.get("/").text
    assert "Demonstração" in html
    assert "Empresa demonstração" in html


def test_articles_empty_state_without_fiction(client):
    html = client.get("/").text
    assert "Os primeiros artigos ainda não foram publicados." in html
    assert "Como criar um currículo profissional" not in html


def test_newsletter_requires_consent(client):
    home = client.get("/")
    token = home.cookies.get("session")
    assert token is not None
    csrf = "missing"
    marker = 'name="csrf_token" value="'
    start = home.text.find(marker)
    if start != -1:
        start += len(marker)
        csrf = home.text[start : home.text.find('"', start)]
    response = client.post(
        "/alertas",
        data={"email": "pessoa@example.com", "interest_area": "tecnologia", "csrf_token": csrf},
        headers={"hx-request": "true"},
    )
    assert response.status_code == 200
    assert "consentir" in response.text.lower() or "necessário" in response.text.lower()


def test_newsletter_with_consent(client):
    home = client.get("/")
    marker = 'name="csrf_token" value="'
    start = home.text.find(marker) + len(marker)
    csrf = home.text[start : home.text.find('"', start)]
    response = client.post(
        "/alertas",
        data={
            "email": "pessoa@example.com",
            "interest_area": "tecnologia",
            "consent": "1",
            "csrf_token": csrf,
        },
        headers={"hx-request": "true"},
    )
    assert response.status_code == 200
    assert "Inscrição recebida" in response.text


def test_healthcheck(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_placeholder_nav_pages(client):
    for path in ("/curriculo", "/ferramentas", "/blog", "/empresas", "/entrar", "/cadastrar", "/privacidade"):
        assert client.get(path).status_code == 200
