from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


BASE_URL = "https://vagas.solides.com.br"
SEARCH_URL = "https://vagas.solides.com.br/vagas/todos/desenvolvedor-full-stack?jobsType=remoto&page=1"

OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)


@dataclass
class JobItem:
    title: str
    company: Optional[str]
    location: Optional[str]
    url: str
    posted_at: Optional[str]
    tags: list[str]
    source: str = "solides"


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = re.sub(r"\s+", " ", value).strip()
    return value or None


def absolutize_url(url: str) -> str:
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return f"{BASE_URL}{url}"


def extract_jobs_from_listing(page) -> list[JobItem]:
    jobs: list[JobItem] = []

    # lista principal de vagas
    items = page.locator('ul[data-cy="list-vacancies"] > li')
    count = items.count()

    print(f"Encontrados {count} cards de vaga na listagem.")

    for i in range(count):
        item = items.nth(i)

        try:
            title = normalize_text(item.locator("h2 a").first.inner_text(timeout=2000))
        except Exception:
            title = None

        try:
            company = normalize_text(
                item.locator('p[data-cy="vacancy-company-name"]').first.inner_text(timeout=2000)
            )
        except Exception:
            company = None

        try:
            location = normalize_text(
                item.locator('p:has(span[data-icon="location_on"])').first.inner_text(timeout=2000)
            )
        except Exception:
            location = None

        try:
            posted_at = normalize_text(item.locator("time").first.inner_text(timeout=2000))
        except Exception:
            posted_at = None

        try:
            href = item.locator('a[href^="/vaga/"]').first.get_attribute("href", timeout=2000)
            url = absolutize_url(href) if href else None
        except Exception:
            url = None

        tags: list[str] = []
        try:
            tag_nodes = item.locator("div.flex.flex-wrap.gap-2 > div")
            tag_count = tag_nodes.count()
            for j in range(tag_count):
                tag_text = normalize_text(tag_nodes.nth(j).inner_text(timeout=1000))
                if tag_text:
                    tags.append(tag_text)
        except Exception:
            pass

        if title and url:
            jobs.append(
                JobItem(
                    title=title,
                    company=company,
                    location=location,
                    url=url,
                    posted_at=posted_at,
                    tags=tags,
                )
            )

    return jobs


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=150,
        )

        context = browser.new_context(
            locale="pt-BR",
            viewport={"width": 1440, "height": 2400},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
        )

        page = context.new_page()

        try:
            page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)

            # garante que a lista apareceu
            page.wait_for_selector('ul[data-cy="list-vacancies"] > li', timeout=15000)

            # debug
            page.screenshot(path=str(OUTPUT_DIR / "solides-search.png"), full_page=True)
            (OUTPUT_DIR / "solides-search.html").write_text(page.content(), encoding="utf-8")

            jobs = extract_jobs_from_listing(page)

            output_file = OUTPUT_DIR / "solides_jobs.json"
            output_file.write_text(
                json.dumps([asdict(job) for job in jobs], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            print(f"\nTotal extraído: {len(jobs)} vaga(s)")
            print(f"Arquivo salvo em: {output_file}")

            for job in jobs[:5]:
                print(f"- {job.title} | {job.company} | {job.location} | {job.tags}")

        except PlaywrightTimeoutError as exc:
            print(f"Timeout ao carregar a página: {exc}")

        finally:
            browser.close()


if __name__ == "__main__":
    main()