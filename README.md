# CarreiraHub

> Plataforma brasileira de vagas de emprego, currículos e ferramentas de carreira.

## Execução local (homepage)

Requisitos: Python 3.12+ e Node.js LTS (apenas para (re)compilar o CSS).

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
copy .env.example .env   # Windows
# cp .env.example .env   # Linux/macOS

npm install
npm run css:build

uvicorn app.main:app --reload
```

Abra `http://localhost:8000`. Sem PostgreSQL, o SQLite local (`carreirahub.db`) é suficiente para a homepage.

Em desenvolvimento, vagas de **demonstração** aparecem identificadas. Artigos só são listados se existirem no banco com `is_published=true`. Anúncios permanecem desligados até `ADSENSE_ENABLED=true` e um client ID válidos.

```bash
pytest
```

## Deploy no Render

O arquivo `render.yaml` sobe o FastAPI (Docker) e um PostgreSQL na mesma região (Ohio). Não use Vercel nem Supabase para este stack.

1. Envie o código para o GitHub (o Render lê o repositório).
2. Em [render.com](https://render.com), crie a conta e conecte o GitHub.
3. **New → Blueprint** e selecione o repositório CarreiraHub.
4. Confirme o serviço `carreirahub` e o banco `carreirahub-db`.
5. Preencha as variáveis com `sync: false` que o painel pedir (`CONTACT_EMAIL`, redes sociais, `APP_BASE_URL` se for usar domínio próprio).
6. Aguarde o primeiro deploy. A URL pública será algo como `https://carreirahub.onrender.com`.
7. Com domínio próprio: aponte o DNS no painel do Render e defina `APP_BASE_URL=https://seudominio.com` (canonical e Open Graph).

O start do container roda `alembic upgrade head` e depois o Uvicorn. `SECRET_KEY` e `DATABASE_URL` são gerados/ligados pelo Blueprint.

O plano `0.5c-512mb` permanece ligado (melhor para SEO). O plano `free` do Render dorme sem tráfego e não é adequado para um site público indexável.

---

# Portal de Carreiras

> **Nome provisório do projeto.** Plataforma de vagas de emprego, currículos e ferramentas de carreira, construída para oferecer uma experiência rápida, acessível e otimizada para mecanismos de busca.

## Visão geral

O **Portal de Carreiras** será uma plataforma que conecta candidatos e empresas, reúne vagas atualizadas, disponibiliza ferramentas gratuitas e publica conteúdo educativo sobre o mercado de trabalho.

O modelo de negócio combina **tráfego orgânico**, **Google AdSense** (sujeito à aprovação e às políticas da plataforma) e, futuramente, serviços premium, como destaque de vagas e análise de currículos com IA.

**Status:** planejamento / desenvolvimento inicial. As funcionalidades descritas são planejadas e não devem ser interpretadas como já implementadas.

## Objetivos

- Publicar e pesquisar vagas com filtros por cargo, cidade, modalidade e categoria.
- Disponibilizar páginas individuais de vagas, acessíveis e indexáveis.
- Oferecer cadastro e gestão de vagas para empresas.
- Permitir criação, armazenamento e exportação de currículos em PDF.
- Publicar guias de carreira e ferramentas gratuitas.
- Aplicar boas práticas de SEO técnico e desempenho web.
- Preparar espaços publicitários sem prejudicar a experiência do usuário.
- Evoluir para alertas de vagas e análise de currículo com IA.

## Stack tecnológica

| Camada | Tecnologia | Responsabilidade |
| --- | --- | --- |
| Backend | Python + FastAPI | Rotas, regras de negócio e APIs |
| Templates | Jinja2 | Renderização HTML no servidor (SSR) |
| Interface | HTML5 + Tailwind CSS | Layout responsivo |
| Interatividade | HTMX + Alpine.js + JavaScript | Filtros, formulários e componentes |
| Validação | Pydantic | Validação e serialização de dados |
| Persistência | SQLAlchemy 2 | ORM e consultas |
| Migrações | Alembic | Evolução do esquema |
| Banco principal | PostgreSQL | Dados transacionais |
| Cache e filas | Redis (fase posterior) | Cache e broker |
| Processamento assíncrono | Celery (fase posterior) | Importações, alertas e PDFs |
| Servidor web | Nginx + Uvicorn | Proxy reverso e execução ASGI |
| Infraestrutura | Docker Compose | Desenvolvimento e deploy inicial |
| Monitoramento | Prometheus + Grafana (fase posterior) | Métricas e observabilidade |

**Decisão arquitetural:** monólito modular. O FastAPI renderiza páginas públicas com Jinja2; não há dependência de React/Vite para o MVP. Um editor de currículo mais avançado poderá utilizar componentes React isolados futuramente.

## Arquitetura

```mermaid
flowchart TD
    A[Visitantes e mecanismos de busca] --> B[Nginx / HTTPS]
    B --> C[FastAPI]
    C --> D[Jinja2 / HTML SSR]
    D --> A
    C --> E[(PostgreSQL)]
    C -. cache e tarefas .-> F[(Redis)]
    F -. fila .-> G[Celery Workers]
    G --> E
    C --> H[Arquivos estáticos / storage privado]
    I[APIs e feeds autorizados de vagas] -. importação .-> G
```

Redis e Celery são componentes planejados para quando houver necessidade de processamento em segundo plano.

## Módulos previstos

| Módulo | Escopo |
| --- | --- |
| `accounts` | Cadastro, login, perfis e permissões |
| `companies` | Empresas e gestão de suas vagas |
| `jobs` | Cadastro, pesquisa, filtros, publicação e expiração |
| `applications` | Candidaturas, quando suportadas pela plataforma |
| `resumes` | Currículos, templates e exportação PDF |
| `content` | Blog, artigos, categorias e páginas de profissões |
| `tools` | Calculadoras e ferramentas gratuitas |
| `notifications` | Alertas e notificações por e-mail |
| `integrations` | Integração com fontes de vagas autorizadas |
| `advertising` | Configuração de posicionamentos de anúncios |
| `admin` | Moderação, auditoria e administração |

## Estrutura proposta do repositório

```text
portal-carreiras/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   └── cache.py
│   ├── modules/
│   │   ├── accounts/
│   │   ├── companies/
│   │   ├── jobs/
│   │   ├── applications/
│   │   ├── resumes/
│   │   ├── content/
│   │   ├── tools/
│   │   ├── notifications/
│   │   ├── integrations/
│   │   ├── advertising/
│   │   └── admin/
│   ├── templates/
│   │   ├── base.html
│   │   ├── home.html
│   │   ├── jobs/
│   │   ├── resumes/
│   │   ├── blog/
│   │   └── components/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── workers/
├── migrations/
├── tests/
├── infrastructure/
│   ├── nginx/
│   ├── docker/
│   └── monitoring/
├── alembic.ini
├── pyproject.toml
├── package.json
├── Dockerfile
├── compose.yaml
├── .env.example
└── README.md
```

> Esta é a organização-alvo, não uma afirmação de que os arquivos já existem no repositório.

## Modelo de dados inicial

Entidades previstas:

- **users:** conta, e-mail, senha com hash seguro, papel e data de criação.
- **companies:** empresa, proprietário, slug e estado de verificação.
- **jobs:** empresa, cargo, descrição, localização, modalidade, fonte, datas e status.
- **job_sources:** fontes autorizadas e informações de sincronização.
- **applications:** candidato, vaga, currículo e status da candidatura.
- **resumes:** proprietário e metadados do documento; arquivos em armazenamento privado.
- **articles:** conteúdo editorial, slug, autor, publicação e metadados SEO.
- **job_alerts:** preferências e consentimento para envio de alertas.
- **audit_logs:** eventos administrativos e de segurança.

Diretrizes: chaves estrangeiras, índices nas consultas frequentes, restrições de unicidade para vagas importadas e migrações versionadas. A busca poderá começar com PostgreSQL Full Text Search.

## SEO e descoberta orgânica

- HTML completo renderizado no servidor para páginas públicas.
- URLs legíveis e estáveis, como `/vagas/desenvolvedor-python-remoto-123`.
- `title`, meta description, canonical e headings apropriados.
- `sitemap.xml` atualizado e `robots.txt` configurado.
- Dados estruturados `JobPosting` **somente em páginas individuais de vagas elegíveis**.
- Tratamento de vagas expiradas, remoção de marcação desatualizada e atualização do sitemap.
- Paginação rastreável e controle de páginas de filtros para evitar duplicações.
- Otimização de Core Web Vitals, imagens, CSS, JavaScript e cache.
- Conteúdo original e útil, evitando páginas criadas em massa sem valor adicional.

## Monetização

**Modelo inicial:** Google AdSense após aprovação da propriedade e atendimento às políticas aplicáveis.

Locais candidatos a anúncios:

- Listagens de vagas.
- Artigos e guias de carreira.
- Páginas de ferramentas gratuitas.
- Páginas individuais de vagas, com posicionamento moderado.

Não posicionar anúncios de modo a induzir cliques acidentais, confundir anúncios com candidaturas ou prejudicar a navegação. Reservar espaço visual para reduzir deslocamento de layout.

**Possíveis receitas futuras:** vagas patrocinadas, assinaturas empresariais e ferramentas premium de currículo.

## Ambiente de desenvolvimento

### Pré-requisitos planejados

- Python 3.12 ou superior compatível com as dependências escolhidas.
- PostgreSQL.
- Node.js LTS para compilação do Tailwind CSS.
- Docker com Compose (opcional para desenvolvimento, recomendado para padronização).

### Configuração planejada

Após a implementação dos arquivos de configuração:

```bash
# Clonar o repositório
 git clone <URL_DO_REPOSITORIO>
 cd portal-carreiras

# Criar arquivo local de variáveis de ambiente
 cp .env.example .env

# Subir os serviços
 docker compose up -d --build

# Aplicar migrações
 docker compose exec web alembic upgrade head
```

**Atenção:** os comandos acima são o fluxo esperado, mas só funcionarão após a criação do `compose.yaml`, `Dockerfile`, `.env.example` e configuração do Alembic. Os nomes dos serviços poderão ser ajustados na implementação.

### Variáveis de ambiente propostas

```dotenv
APP_ENV=development
APP_DEBUG=false
APP_BASE_URL=http://localhost:8000
DATABASE_URL=postgresql+psycopg://portal:change-me@postgres:5432/portal
REDIS_URL=redis://redis:6379/0
SECRET_KEY=replace-with-a-long-random-secret
ADSENSE_CLIENT_ID=
```

Nunca publicar credenciais reais ou arquivos `.env` no Git. Configurar `.gitignore` e usar gerenciador de segredos em produção.

## Segurança e privacidade

- HTTPS obrigatório em produção.
- Hash de senhas com algoritmo apropriado e atualizado.
- Sessões/cookies com `HttpOnly`, `Secure` e política `SameSite` adequada.
- Proteção CSRF para ações autenticadas e validação de entradas.
- Controle de acesso por perfil: candidato, empresa e administrador.
- Rate limiting, prevenção de abuso e logs de auditoria.
- Uploads com validação de tipo/tamanho e armazenamento privado.
- Backups automáticos do PostgreSQL e testes de restauração.
- Política de privacidade, gestão de consentimento e processos LGPD.
- Respeito aos termos de uso e direitos das fontes de vagas; não copiar conteúdo sem autorização.

## Infraestrutura inicial

Proposta para MVP em uma VM Linux:

| Serviço | Implantação |
| --- | --- |
| Nginx | Container exposto nas portas 80/443 |
| FastAPI/Uvicorn | Container na rede interna |
| PostgreSQL | Container com volume persistente e backup |
| Redis | Container interno, quando necessário |
| Celery Worker / Beat | Containers internos, quando necessários |

Dimensionamento inicial de referência: **4 vCPU, 8 GB RAM e 80 GB SSD**, a validar com testes de carga e observabilidade. Evitar exposição direta de PostgreSQL e Redis à internet.

## Qualidade e testes

- Testes unitários e de integração com `pytest`.
- Testes de rotas HTML e APIs, incluindo autenticação e autorização.
- Testes de migração do banco.
- Verificação de HTML, metadados e dados estruturados.
- Testes de acessibilidade e responsividade.
- Testes de carga antes de campanhas ou aumento expressivo de tráfego.
- Lint/format com Ruff e análise de segurança de dependências.

## Roadmap

### Fase 1 — Fundação

- [ ] Configurar repositório, Docker Compose e ambientes.
- [ ] Inicializar FastAPI, Jinja2, SQLAlchemy e Alembic.
- [ ] Criar design system, layout base e navegação responsiva.
- [ ] Implementar usuários, permissões e autenticação.

### Fase 2 — Vagas

- [ ] Modelar empresas e vagas.
- [ ] Implementar publicação e moderação de vagas.
- [ ] Criar listagem, busca, filtros e paginação.
- [ ] Criar página individual de vaga.
- [ ] Implementar expiração e deduplicação.

### Fase 3 — SEO e conteúdo

- [ ] Criar sitemap, robots, canonical e metadados dinâmicos.
- [ ] Implementar dados estruturados `JobPosting`.
- [ ] Criar módulo editorial de blog e páginas de profissões.
- [ ] Integrar Google Search Console e Analytics.

### Fase 4 — Ferramentas e monetização

- [ ] Criar gerador de currículo em PDF.
- [ ] Disponibilizar calculadoras e ferramentas gratuitas.
- [ ] Criar páginas institucionais e documentos de privacidade.
- [ ] Preparar posições de anúncios e solicitar avaliação no AdSense.

### Fase 5 — Evolução

- [ ] Integrar fontes autorizadas de vagas.
- [ ] Criar alertas de vagas por e-mail.
- [ ] Implementar análise de currículo com IA.
- [ ] Criar vagas patrocinadas e serviços premium.
- [ ] Adicionar monitoramento e otimização avançada de desempenho.

## Convenções de desenvolvimento

- Organizar regras de negócio por módulo, separando rotas, serviços, modelos e templates.
- Utilizar tipagem Python e validação Pydantic.
- Criar migração Alembic para toda alteração de esquema.
- Escrever testes para regras críticas e correções de bugs.
- Utilizar variáveis de ambiente para configurações sensíveis.
- Priorizar HTML semântico, acessibilidade e progressive enhancement.
- Documentar decisões arquiteturais relevantes no repositório.

## Licença

A definir antes da distribuição pública do código. Até a escolha de uma licença, não presumir autorização para redistribuição ou reutilização por terceiros.

---

**Portal de Carreiras** — Vagas, ferramentas e oportunidades para o próximo passo profissional.
