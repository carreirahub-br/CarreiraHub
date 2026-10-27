#!/usr/bin/env python3
"""
Script CLI para coletar vagas públicas do LinkedIn e integrá-las
ao banco de dados do CarreiraHub no padrão oficial do módulo 'Encontrar Vagas'.
"""

import argparse
import sys
from pathlib import Path

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.modules.jobs.scraper import fetch_linkedin_jobs, save_scraped_jobs

CATEGORY_DEFAULT_KEYWORDS = {
    "tecnologia": "desenvolvedor",
    "marketing": "marketing digital",
    "financeiro": "analista financeiro",
    "administracao": "assistente administrativo",
    "engenharia": "engenheiro civil",
    "saude": "enfermagem",
    "logistica": "analista de logistica",
    "atendimento": "suporte atendimento",
}


def main():
    parser = argparse.ArgumentParser(
        description="Scraper de vagas abertas no LinkedIn nos últimos 30 dias para o CarreiraHub."
    )
    parser.add_argument(
        "--keywords",
        type=str,
        default="desenvolvedor",
        help="Termos de busca de cargo ou habilidades (ex: python, desenvolvedor, analista).",
    )
    parser.add_argument(
        "--location",
        type=str,
        default="Brasil",
        help="Localização (ex: Brasil, São Paulo, Curitiba).",
    )
    parser.add_argument(
        "--geo-id",
        type=str,
        default="106057199",
        help="geoId do LinkedIn (106057199 é o padrão oficial para o Brasil).",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Janela máxima em dias para vagas em aberto (padrão: 30 dias).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=30,
        help="Quantidade de vagas a coletar (padrão: 30). Use 0 para puxar todas as encontradas.",
    )
    parser.add_argument(
        "--all-categories",
        action="store_true",
        help="Se ativado, busca vagas abertas em todas as 8 categorias do CarreiraHub nos últimos 30 dias.",
    )
    parser.add_argument(
        "--with-description",
        action="store_true",
        help="Se ativado, consulta a descrição detalhada de cada vaga no endpoint de detalhes.",
    )

    args = parser.parse_args()
    limit = None if args.limit <= 0 else args.limit

    print("=" * 65)
    print("🚀 CarreiraHub - Coleta de Vagas Abertas no LinkedIn (Últimos 30 Dias)")
    print(f"📍 Localização: {args.location}")
    print(f"⏳ Janela de tempo: até {args.days} dias")
    print(f"🎯 Limite por busca: {limit or 'Todas as disponíveis'}")
    print(f"📝 Descrições completas: {'Sim' if args.with_description else 'Não'}")
    print("=" * 65)

    db = SessionLocal()
    total_saved = 0

    try:
        queries = []
        if args.all_categories:
            print("🌐 Modo Todas as Categorias ativado (8 categorias do portal)...\n")
            for cat, kw in CATEGORY_DEFAULT_KEYWORDS.items():
                queries.append((cat, kw))
        else:
            queries.append(("busca_direta", args.keywords))

        for cat_name, kw in queries:
            print(f"🔍 Consultando vagas para: '{kw}' ({cat_name})...")
            jobs_data = fetch_linkedin_jobs(
                keywords=kw,
                location=args.location,
                geo_id=args.geo_id,
                limit=limit,
                max_days=args.days,
            )

            if not jobs_data:
                print(f"   ⚠️ Nenhuma vaga recente encontrada para '{kw}'.")
                continue

            print(f"   📦 {len(jobs_data)} vagas válidas nos últimos {args.days} dias. Salvando...")
            saved = save_scraped_jobs(
                db=db,
                jobs_data=jobs_data,
                fetch_descriptions=args.with_description,
            )
            total_saved += len(saved)

            for i, j in enumerate(saved, 1):
                loc = f"{j.city} / {j.state}" if j.city and j.state else (j.city or "Remoto")
                print(f"      [{i}] {j.title} | {j.company_name} ({loc}) - [{j.work_mode.upper()} · {j.contract_type} · {j.salary_text}]")

            print()

        print("=" * 65)
        print(f"🎉 Coleta concluída com sucesso! Total de {total_saved} vagas atualizadas no banco.")
        print("Todas já estão visíveis no formato padrão em: http://localhost:8000/vagas")
        print("=" * 65)

    finally:
        db.close()


if __name__ == "__main__":
    main()
