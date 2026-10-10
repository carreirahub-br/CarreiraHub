from fastapi import APIRouter, Request

from app.core.templating import templates

router = APIRouter()

PAGES = {
    "ferramentas": {
        "path": "/ferramentas",
        "title": "Ferramentas de carreira",
        "intro": "Calculadoras e utilitários gratuitos serão publicados nesta área. Nenhuma ferramenta está ativa ainda.",
        "meta": "Ferramentas gratuitas de carreira do CarreiraHub, em breve.",
    },
    "blog": {
        "path": "/blog",
        "title": "Blog",
        "intro": "Artigos sobre carreira, mercado de trabalho e preparação para processos seletivos serão publicados aqui.",
        "meta": "Conteúdo de carreira do CarreiraHub.",
    },
    "empresas": {
        "path": "/empresas",
        "title": "Para empresas",
        "intro": "A publicação de vagas para empresas está em preparação. Em breve será possível divulgar oportunidades e alcançar candidatos.",
        "meta": "Divulgue vagas da sua empresa no CarreiraHub.",
    },
    "entrar": {
        "path": "/entrar",
        "title": "Entrar",
        "intro": "O acesso à conta ainda não está disponível. Cadastro e autenticação serão habilitados na próxima etapa da plataforma.",
        "meta": "Acesse sua conta CarreiraHub.",
    },
    "cadastrar": {
        "path": "/cadastrar",
        "title": "Cadastrar-se",
        "intro": "O cadastro de candidatos e empresas ainda não está aberto. Você já pode buscar vagas e acompanhar o lançamento das ferramentas.",
        "meta": "Crie sua conta no CarreiraHub.",
    },
    "sobre": {
        "path": "/sobre",
        "title": "Sobre nós",
        "intro": "O CarreiraHub conecta talentos a novas oportunidades, reunindo vagas, currículos e conteúdo de carreira em um só lugar.",
        "meta": "Conheça o CarreiraHub.",
    },
    "contato": {
        "path": "/contato",
        "title": "Contato",
        "intro": "Para dúvidas institucionais, utilize o e-mail informado no rodapé quando estiver disponível. O formulário de contato será publicado em breve.",
        "meta": "Fale com o CarreiraHub.",
    },
    "como-funciona": {
        "path": "/como-funciona",
        "title": "Como funciona",
        "intro": "Pesquise vagas, prepare seu currículo com as ferramentas da plataforma e candidate-se pelos canais informados por cada empresa.",
        "meta": "Como o CarreiraHub funciona para candidatos e empresas.",
    },
    "recrutadores": {
        "path": "/empresas/recrutadores",
        "title": "Para recrutadores",
        "intro": "Recursos para recrutadores, como gestão de vagas e destaque de anúncios, estão no roadmap e ainda não foram lançados.",
        "meta": "Recursos para recrutadores no CarreiraHub.",
    },
    "parcerias": {
        "path": "/parcerias",
        "title": "Parcerias",
        "intro": "Conversas de parceria institucional serão abertas após o lançamento da publicação de vagas.",
        "meta": "Parcerias com o CarreiraHub.",
    },
    "termos": {
        "path": "/termos",
        "title": "Termos de uso",
        "intro": "Os termos de uso definitivos serão publicados antes da abertura de cadastros e da coleta ampliada de dados pessoais.",
        "meta": "Termos de uso do CarreiraHub.",
    },
    "privacidade": {
        "path": "/privacidade",
        "title": "Política de privacidade",
        "intro": "Esta política será atualizada com bases legais, prazos de retenção e direitos do titular antes da operação plena, em conformidade com a LGPD.",
        "meta": "Política de privacidade do CarreiraHub.",
    },
    "cookies": {
        "path": "/cookies",
        "title": "Política de cookies",
        "intro": "Utilizamos cookies essenciais para segurança e sessão. Cookies de medição e publicidade só serão ativados após consentimento e configuração correspondentes.",
        "meta": "Política de cookies do CarreiraHub.",
    },
    "alertas-preferencias": {
        "path": "/alertas/preferencias",
        "title": "Preferências de alertas",
        "intro": "A gestão de preferências e o descadastramento serão habilitados junto ao envio de e-mails transacionais. Até lá, nenhuma mensagem promocional é disparada automaticamente.",
        "meta": "Gerencie alertas de vagas do CarreiraHub.",
    },
}


def _placeholder(request: Request, key: str):
    page = PAGES[key]
    return templates.TemplateResponse(
        request,
        "pages/placeholder.html",
        {
            "title": page["title"],
            "intro": page["intro"],
            "meta_title": f"{page['title']} | CarreiraHub",
            "meta_description": page["meta"],
            "canonical_path": page["path"],
        },
    )


@router.get("/ferramentas", include_in_schema=False)
def ferramentas(request: Request):
    return _placeholder(request, "ferramentas")


@router.get("/blog", include_in_schema=False)
def blog(request: Request):
    return _placeholder(request, "blog")


@router.get("/empresas", include_in_schema=False)
def empresas(request: Request):
    return _placeholder(request, "empresas")


@router.get("/entrar", include_in_schema=False)
def entrar(request: Request):
    return _placeholder(request, "entrar")


@router.get("/cadastrar", include_in_schema=False)
def cadastrar(request: Request):
    return _placeholder(request, "cadastrar")


@router.get("/sobre", include_in_schema=False)
def sobre(request: Request):
    return _placeholder(request, "sobre")


@router.get("/contato", include_in_schema=False)
def contato(request: Request):
    return _placeholder(request, "contato")


@router.get("/como-funciona", include_in_schema=False)
def como_funciona(request: Request):
    return _placeholder(request, "como-funciona")


@router.get("/empresas/recrutadores", include_in_schema=False)
def recrutadores(request: Request):
    return _placeholder(request, "recrutadores")


@router.get("/parcerias", include_in_schema=False)
def parcerias(request: Request):
    return _placeholder(request, "parcerias")


@router.get("/termos", include_in_schema=False)
def termos(request: Request):
    return _placeholder(request, "termos")


@router.get("/privacidade", include_in_schema=False)
def privacidade(request: Request):
    return _placeholder(request, "privacidade")


@router.get("/cookies", include_in_schema=False)
def cookies(request: Request):
    return _placeholder(request, "cookies")


@router.get("/alertas/preferencias", include_in_schema=False)
def alert_prefs(request: Request):
    return _placeholder(request, "alertas-preferencias")
