def test_resume_builder_renders(client):
    response = client.get("/curriculo")
    assert response.status_code == 200
    html = response.text
    assert html.count("<h1") == 1
    assert "Criar currículo" in html
    assert 'x-data="resumeBuilder"' in html
    assert "/static/js/resume.js" in html
    assert html.index("/static/js/resume.js") < html.index("/static/js/alpine.min.js")
    assert 'rel="canonical" href="http://testserver/curriculo"' in html
    assert "Baixar PDF" in html


def test_resume_builder_does_not_post_data(client):
    html = client.get("/curriculo").text
    assert 'method="post"' not in html
    assert "hx-post" not in html


def test_home_links_resume_tool(client):
    html = client.get("/").text
    assert 'href="/curriculo">Criar currículo</a>' in html


def test_resume_script_is_served(client):
    response = client.get("/static/js/resume.js")
    assert response.status_code == 200
    assert "resumeBuilder" in response.text
