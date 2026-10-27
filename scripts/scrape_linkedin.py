#!/usr/bin/env python3
"""
Script CLI para coletar vagas públicas do LinkedIn e integrá-las
automaticamente ao banco de dados e ao módulo 'Encontrar Vagas' do CarreiraHub.
"""

import argparse
import sys
from pathlib import Path

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.modules.jobs.scraper import fetch_linkedin_jobs, save_scraped_jobs


def main():
    parser = argparse.ArgumentParser(description="Scraper de vagas do LinkedIn para o CarreiraHub.")
    parser.add_argument(
        "--keywords",
        type=str,
        default="desenvolvedor",
        help="Termos de busca de cargo ou habilidades (ex: python, desenvolvedor, marketing, vendas).",
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
        help="geoId do LinkedIn (106057199 é o padrão para o Brasil).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Quantidade máxima de vagas a coletar (padrão: 10).",
    )
    parser.add_argument(
        "--with-description",
        action="store_true",
        help="Se informado, busca a descrição completa de cada vaga no endpoint de detalhes.",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🚀 Iniciando Scraping de Vagas do LinkedIn")
    print(f"📌 Palavras-chave: {args.keywords}")
    print(f"📍 Localização: {args.location}")
    print(f"🎯 Limite desejado: {args.limit}")
    print(f"📝 Buscar descrições detalhadas: {'Sim' if args.with_description else 'Não'}")
    print("=" * 60)

    jobs_data = fetch_linkedin_jobs(
        keywords=args.keywords,
        location=args.location,
        geo_id=args.geo_id,
        limit=args.limit,
    )

    if not jobs_data:
        print("⚠️ Nenhuma vaga encontrada ou houve bloqueio temporário do endpoint público do LinkedIn.")
        return

    print(f"\n📦 {len(jobs_data)} vagas coletadas com sucesso. Salvando no banco de dados...")

    db = SessionLocal()
    try:
        saved_jobs = save_scraped_jobs(
            db=db,
            jobs_data=jobs_data,
            fetch_descriptions=args.with_description,
        )
        print(f"✅ {len(saved_jobs)} vagas salvas/atualizadas no banco de dados com sucesso!\n")
        print("Vagas adicionadas:")
        for i, j in enumerate(saved_jobs, 1):
            loc = f"{j.city}/{j.state}" if j.city or j.state else "Remoto"
            print(f"  [{i}] {j.title} @ {j.company_name} ({loc}) - [{j.work_mode.upper()} / {j.contract_type}]")
            print(f"      URL local: /vagas/{j.slug}")
        print("\n🎉 Todas as vagas já estão visíveis no módulo 'Encontrar Vagas' (/vagas)!")
    finally:
        db.close()


if __name__ == "__main__":
    main()
