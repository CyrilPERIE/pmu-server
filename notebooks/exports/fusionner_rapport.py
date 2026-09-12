"""Fusionne les exports HTML Jupyter en un rapport unique, sans code."""

from __future__ import annotations

import copy
import re
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = Path("/home/cyril/dev/epmu/pmu-server/notebooks/exports")
SOURCES = [
    {
        "file": "001_exploration.html",
        "prefix": "p1-",
        "kicker": "Partie 1",
        "label": "Panorama",
        "id": "partie-1",
    },
    {
        "file": "002_faisabilite_modelisation.html",
        "prefix": "p2-",
        "kicker": "Partie 2",
        "label": "Modélisation",
        "id": "partie-2",
    },
    {
        "file": "003_marche_en_direct.html",
        "prefix": "p3-",
        "kicker": "Partie 3",
        "label": "Marché en direct",
        "id": "partie-3",
    },
]

PONTS = {
    "partie-1": """
<aside class="pont">
  <p class="pont-kicker">Fil conducteur</p>
  <p>Le panorama le dit clairement : le calendrier est complet, les fiches sont cohérentes,
  les contrôles croisés tiennent. La question n’est plus <em>qu’y a-t-il dans la base ?</em>
  mais <em>peut-on s’en servir pour prévoir ?</em></p>
  <p><a href="#partie-2">Enchaîner sur la faisabilité de la modélisation →</a></p>
</aside>
""",
    "partie-2": """
<aside class="pont">
  <p class="pont-kicker">Fil conducteur</p>
  <p>La cote avale presque tout le signal du palmarès. Il reste un angle mort : la cote
  n’est qu’une <strong>photo</strong>. Le marché, lui, est un <strong>film</strong> — et ce
  film n’existe que pour les courses suivies en direct.</p>
  <p><a href="#partie-3">Voir comment l’argent bouge jusqu’au départ →</a>
  · <a href="#p2-verdict">Relire le verdict du modèle</a></p>
</aside>
""",
    "partie-3": """
<aside class="pont">
  <p class="pont-kicker">Fil conducteur</p>
  <p>On n’identifie pas un clan de parieurs lucides. On voit une foule qui <em>confirme</em>
  plus qu’elle ne révèle. Si le suivi en direct continue, deux ingrédients méritent d’entrer
  dans le modèle de la partie 2 : la <strong>dérive de cote</strong> et le
  <strong>régime de marché</strong> (boulevard, chahut, leurre).</p>
  <p><a href="#p2-verdict">Retour au verdict de modélisation</a>
  · <a href="#synthese">Lire la synthèse des trois parties →</a></p>
</aside>
""",
}

SYNTHESE = """
<section class="partie" id="synthese">
  <p class="kicker">Pour finir</p>
  <h1>Ce que les trois parties disent ensemble</h1>
  <p>Lues séparément, ces analyses répondent à trois questions. Lues à la suite, elles
  dessinent une stratégie.</p>
  <div class="cartes">
    <article class="carte">
      <h2><a href="#partie-1">1. La matière est là</a></h2>
      <p>Vingt mois sans trou, des dizaines de milliers de courses, des cotes alignées sur
      les arrivées. On peut travailler. Les limites utiles à retenir : devises étrangères,
      champs propres à une discipline, et une cote qui n’est qu’un instant.</p>
    </article>
    <article class="carte">
      <h2><a href="#partie-2">2. Un modèle peut classer, pas encore miser</a></h2>
      <p>Sans la cote, le profil du cheval bat le hasard. Avec la cote, on retombe sur le
      favori. Battre le marché demanderait un signal que le prix n’a pas déjà avalé —
      ou une cible différente de « trouver le gagnant ».</p>
    </article>
    <article class="carte">
      <h2><a href="#partie-3">3. Le film existe, trop court pour une loi</a></h2>
      <p>Deux semaines de direct suffisent à voir le geste : le favori de dernière minute
      gagne plus souvent que celui du matin. Trop peu pour généraliser. Assez pour savoir
      <em>quoi</em> collecter ensuite.</p>
    </article>
  </div>
  <p>La suite naturelle n’est pas un algorithme plus compliqué sur la même photo. C’est un
  jeu plus propre — un modèle par discipline, des performances calculées dans le temps —
  enrichi, dès que le suivi tourne, de la dérive de cote et du visage du marché.</p>
</section>
"""

CSS = """
:root {
  --background: #faf9f5;
  --foreground: #3d3929;
  --card: #f5f4ef;
  --card-foreground: #141413;
  --primary: #c96442;
  --primary-foreground: #ffffff;
  --secondary: #e9e6dc;
  --muted: #ede9de;
  --muted-foreground: #6e6d68;
  --border: #dad9d4;
  --chart-1: #b05730;
  --chart-2: #9c87f5;
  --radius: 1rem;
  --shadow: 0 1px 3px hsl(0 0% 0% / 0.10), 0 1px 2px -1px hsl(0 0% 0% / 0.10);
  --text: 14px;
  --text-head: 12px;
  --heading-3: 1.25rem;
  --heading-2: 1.5rem;
  --heading-1: 1.75rem;
  --display: 2rem;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background: var(--background);
  color: var(--foreground);
  font-family: Outfit, "Noto Sans", sans-serif;
  font-size: var(--text);
  line-height: 1.65;
}
a { color: var(--primary); text-decoration-thickness: 1px; text-underline-offset: 3px; }
a:hover { color: var(--chart-1); }
.layout {
  display: grid;
  grid-template-columns: minmax(0, 16rem) minmax(0, 1fr);
  min-height: 100vh;
}
.toc {
  position: sticky;
  top: 0;
  align-self: start;
  height: 100vh;
  overflow: auto;
  padding: 1.75rem 1.25rem 2rem 1.5rem;
  background: var(--card);
  border-right: 1px solid var(--border);
}
.toc a { color: var(--foreground); text-decoration: none; }
.toc a:hover { color: var(--primary); }
.toc-brand {
  font-size: 0.78rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted-foreground);
  margin: 0 0 1.25rem;
  font-weight: 600;
}
.toc ol { list-style: none; margin: 0; padding: 0; }
.toc > ol > li { margin: 0 0 1rem; }
.toc .part-link {
  display: block;
  font-weight: 600;
  margin-bottom: 0.35rem;
}
.toc .chapters {
  padding-left: 0.2rem;
  border-left: 2px solid var(--border);
  margin: 0.2rem 0 0 0.15rem;
}
.toc .chapters a {
  display: block;
  font-size: 0.92rem;
  color: var(--muted-foreground);
  padding: 0.15rem 0 0.15rem 0.75rem;
}
.page {
  max-width: 52rem;
  min-width: 0;
  margin: 0 auto;
  padding: 2.5rem 1.75rem 4.5rem;
}
.hero {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: calc(var(--radius) + 4px);
  padding: 1.75rem 1.75rem 1.5rem;
  box-shadow: var(--shadow);
  margin-bottom: 2.5rem;
}
.hero h1 { margin: 0 0 0.6rem; font-size: var(--display); letter-spacing: -0.02em; }
.hero p { margin: 0.4rem 0; color: var(--muted-foreground); }
.kicker {
  font-size: 0.78rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--primary);
  font-weight: 600;
  margin: 0 0 0.5rem;
}
h1, h2, h3, h4 {
  font-family: Outfit, "Noto Sans", sans-serif;
  color: var(--card-foreground);
  line-height: 1.25;
  letter-spacing: -0.02em;
}
h1 { font-size: var(--heading-1); font-weight: 700; margin: 0.4rem 0 1rem; }
h2 {
  font-size: var(--heading-2);
  font-weight: 600;
  color: var(--primary);
  margin: 2.4rem 0 0.8rem;
  padding-top: 0.4rem;
}
h3 { font-size: var(--heading-3); font-weight: 600; margin: 1.6rem 0 0.5rem; }
.partie { margin-bottom: 2rem; }
.partie > h1 { font-size: var(--display); }
.anchor-link { display: none; }
.pont, .note {
  background: var(--card);
  border: 1px solid var(--border);
  border-left: 4px solid var(--primary);
  border-radius: var(--radius);
  padding: 1rem 1.2rem;
  margin: 2rem 0;
  box-shadow: var(--shadow);
}
.pont-kicker, .note-kicker {
  margin: 0 0 0.35rem;
  font-size: 0.78rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--primary);
  font-weight: 600;
}
.pont p, .note p { margin: 0.35rem 0; }
figure.chart {
  margin: 1.4rem 0 1.8rem;
  padding: 0.75rem;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}
figure.chart img { display: block; width: 100%; height: auto; border-radius: 0.5rem; }
.tableau {
  margin: 1.25rem 0 1.75rem;
  max-width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  -webkit-overflow-scrolling: touch;
}
.tableau > table:not([id]) {
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--card);
}
.tableau table {
  display: table !important;
  width: max-content !important;
  min-width: 100%;
  max-width: none !important;
  table-layout: auto !important;
  border-collapse: collapse;
  overflow: visible !important;
  margin: 0 !important;
  font-size: var(--text) !important;
}
.tableau caption {
  caption-side: top;
  text-align: left;
  font-size: var(--text) !important;
  font-weight: 600;
  padding: 0.15rem 0.2rem 0.7rem;
  color: var(--foreground);
}
.tableau th,
.tableau td {
  white-space: nowrap !important;
  width: auto !important;
  min-width: 6.5rem;
  padding: 0.45rem 0.75rem !important;
  font-size: var(--text) !important;
  line-height: 1.45;
  vertical-align: top;
}
.tableau thead th {
  background: var(--secondary);
  color: var(--muted-foreground);
  font-size: var(--text-head) !important;
  font-weight: 600;
  text-align: left;
  border-bottom: 1px solid var(--border);
}
.tableau tbody th,
.tableau tbody td {
  border-bottom: 1px solid var(--border);
}
.tableau tbody tr:last-child th,
.tableau tbody tr:last-child td {
  border-bottom: none;
}
.jp-RenderedHTMLCommon p { margin: 0.7rem 0; }
.retenir {
  font-size: var(--text);
  line-height: 1.65;
  background: var(--card);
  border: 1px solid var(--border);
  border-left: 4px solid var(--primary);
  border-radius: var(--radius);
  padding: 0.85rem 1.05rem;
  margin: 1.25rem 0 1.5rem;
}
.cartes {
  display: grid;
  gap: 1rem;
  margin: 1.25rem 0 1.5rem;
}
@media (min-width: 720px) {
  .cartes { grid-template-columns: 1fr 1fr 1fr; }
}
.carte {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem 1.1rem 1.15rem;
  box-shadow: var(--shadow);
}
.carte h2 { margin: 0 0 0.5rem; font-size: var(--heading-3); }
.carte p { margin: 0; font-size: var(--text); color: var(--muted-foreground); }
footer.fin {
  margin-top: 3rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
  color: var(--muted-foreground);
  font-size: 0.92rem;
}
@media (max-width: 900px) {
  .layout { grid-template-columns: 1fr; }
  .toc { position: relative; height: auto; border-right: none; border-bottom: 1px solid var(--border); }
}
"""

INTERPRETATIONS = [
    (
        "partie-1",
        "7. Ce qui est complet",
        """
<aside class="note">
  <p class="note-kicker">Comment le lire</p>
  <p>Cette section est le mode d’emploi de tout le reste. Une information à 100&nbsp;%
  (discipline, distance, jockey) peut entrer dans un modèle sans précaution. Une information
  à 60&nbsp;% (corde, terrain) ne décrit qu’une discipline. Une absence (mouvement des cotes)
  n’est pas un oubli de ligne : c’est un autre dispositif, traité en
  <a href="#partie-3">partie 3</a>.</p>
</aside>
""",
    ),
    (
        "partie-2",
        "5. La cote absorbe",
        """
<aside class="note">
  <p class="note-kicker">Lien avec le marché en direct</p>
  <p>Si la cote finale avale le palmarès, la question utile devient : la cote a-t-elle
  <em>bougé</em> ? Un cheval qui raccourcit n’est pas le même objet qu’un cheval déjà seul
  le matin. C’est exactement ce que mesure la <a href="#p3-temps">partie 3</a> — sur un
  calendrier beaucoup plus court.</p>
</aside>
""",
    ),
    (
        "partie-3",
        "5. Le public a-t-il",
        """
<aside class="note">
  <p class="note-kicker">Lien avec le modèle</p>
  <p>Le favori de dernière minute gagne plus souvent que celui du matin. Ce n’est pas un
  clan de cracks : c’est la foule qui se corrige. Dans un modèle, cela se traduit par une
  feature simple — <em>la cote a-t-elle raccourci ?</em> — à tester en complément du
  <a href="#p2-modele">modèle linéaire de la partie 2</a>, dès que l’historique direct
  sera assez long.</p>
</aside>
""",
    ),
]


def prefix_fragment(value: str, prefix: str) -> str:
    if value.startswith(prefix):
        return value
    return prefix + value


def est_id_pandas(valeur: str) -> bool:
    """Les styles pandas ciblent `#T_xxxx` : ne pas préfixer, sinon le tableau perd sa mise en forme."""
    return valeur.startswith("T_")


def rewrite_tree(root: Tag, prefix: str) -> None:
    for tag in root.find_all(True):
        ident = tag.get("id")
        if ident and not est_id_pandas(ident):
            tag["id"] = prefix_fragment(ident, prefix)
        href = tag.get("href")
        if href and href.startswith("#") and not est_id_pandas(href[1:]):
            tag["href"] = "#" + prefix_fragment(href[1:], prefix)
        for attr in ("name", "for"):
            if tag.get(attr) and not str(tag.get(attr)).startswith("http") and not est_id_pandas(str(tag[attr])):
                tag[attr] = prefix_fragment(str(tag[attr]), prefix)
        if tag.name == "a" and "anchor-link" in (tag.get("class") or []):
            tag.decompose()


def envelopper_tableaux(chunk: Tag, soup: BeautifulSoup) -> None:
    for table in list(chunk.find_all("table")):
        if table.find_parent(class_="tableau"):
            continue
        wrapper = soup.new_tag("div")
        wrapper["class"] = "tableau"
        table.replace_with(wrapper)
        wrapper.append(table)


def marquer_retenir(chunk: Tag) -> None:
    for paragraph in chunk.find_all("p"):
        text = paragraph.get_text(" ", strip=True)
        if text.startswith("À retenir"):
            classes = list(paragraph.get("class") or [])
            if "retenir" not in classes:
                paragraph["class"] = classes + ["retenir"]


def extract_cells(soup: BeautifulSoup, prefix: str) -> list[Tag]:
    blocks: list[Tag] = []
    notebook = soup.select_one("main") or soup.select_one(".jp-Notebook") or soup.body
    for cell in notebook.select(".jp-Cell"):
        classes = cell.get("class") or []
        if "jp-MarkdownCell" in classes:
            rendered = cell.select_one(".jp-RenderedMarkdown")
            if not rendered:
                continue
            chunk = copy.copy(rendered)
            rewrite_tree(chunk, prefix)
            envelopper_tableaux(chunk, soup)
            marquer_retenir(chunk)
            blocks.append(chunk)
        elif "jp-CodeCell" in classes:
            if "jp-mod-noOutputs" in classes:
                continue
            for output in cell.select(".jp-OutputArea-output"):
                mime = output.get("data-mime-type") or ""
                classes_out = output.get("class") or []
                if "stderr" in mime or "stderr" in " ".join(classes_out):
                    continue
                if "application/vnd.jupyter.stderr" in mime:
                    continue
                chunk = copy.copy(output)
                rewrite_tree(chunk, prefix)
                if chunk.find("img"):
                    figure = soup.new_tag("figure")
                    figure["class"] = "chart"
                    for img in chunk.find_all("img"):
                        img.attrs.pop("class", None)
                        figure.append(copy.copy(img))
                    blocks.append(figure)
                else:
                    wrapper = soup.new_tag("div")
                    wrapper["class"] = "tableau"
                    wrapper.append(chunk)
                    blocks.append(wrapper)
    return blocks


def headings_for_nav(blocks: list[Tag]) -> list[tuple[str, str]]:
    seen: list[tuple[str, str]] = []
    skip = {"Sommaire", "La question", "À qui s'adresse ce document"}
    for block in blocks:
        if not isinstance(block, Tag):
            continue
        for heading in block.find_all("h2"):
            text = heading.get_text(" ", strip=True)
            if text in skip:
                continue
            ident = heading.get("id") or ""
            pair = (ident, text)
            if ident and pair not in seen:
                seen.append(pair)
    return seen


def insert_interpretations(blocks: list[Tag], soup: BeautifulSoup, partie_id: str) -> list[Tag]:
    extras = [item for item in INTERPRETATIONS if item[0] == partie_id]
    if not extras:
        return blocks
    result: list[Tag] = []
    for block in blocks:
        result.append(block)
        text = block.get_text(" ", strip=True) if isinstance(block, Tag) else ""
        for _, needle, html in extras:
            if needle in text and block.find("h2"):
                note = BeautifulSoup(html, "html.parser")
                result.append(note)
    return result


def main() -> None:
    parties = []
    for source in SOURCES:
        soup = BeautifulSoup((ROOT / source["file"]).read_text(encoding="utf-8"), "html.parser")
        blocks = extract_cells(soup, source["prefix"])
        blocks = insert_interpretations(blocks, soup, source["id"])
        chapters = headings_for_nav(blocks)
        parties.append({**source, "blocks": blocks, "chapters": chapters, "soup": soup})

    toc_items = []
    for party in parties:
        chapters = "".join(
            f'<a href="#{ident}">{title}</a>' for ident, title in party["chapters"] if ident
        )
        toc_items.append(
            f'<li><a class="part-link" href="#{party["id"]}">{party["kicker"]} · {party["label"]}</a>'
            f'<div class="chapters">{chapters}</div></li>'
        )
    toc_items.append('<li><a class="part-link" href="#synthese">Pour finir · Synthèse</a></li>')

    body_parts = []
    for party in parties:
        inner = "\n".join(str(block) for block in party["blocks"])
        title_guess = ""
        for block in party["blocks"]:
            h1 = block.find("h1") if isinstance(block, Tag) else None
            if h1:
                title_guess = h1.get_text(" ", strip=True)
                break
        body_parts.append(
            f'<section class="partie" id="{party["id"]}">'
            f'<p class="kicker">{party["kicker"]}</p>'
            f"{inner}"
            f'{PONTS[party["id"]]}'
            f"</section>"
        )

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Rapport d’exploration des données de courses</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>{CSS}</style>
</head>
<body>
  <div class="layout">
    <nav class="toc" aria-label="Sommaire">
      <p class="toc-brand">Données de courses</p>
      <ol>{''.join(toc_items)}</ol>
    </nav>
    <div class="page">
      <header class="hero">
        <p class="kicker">Rapport</p>
        <h1>Ce que contiennent les données, et ce qu’on peut en faire</h1>
        <p>Trois lectures d’une même base : d’abord le panorama (janvier 2025 – août 2026),
        puis la faisabilité d’un modèle, enfin le marché vu en direct — un film plus court,
        mais le seul qui montre l’argent bouger.</p>
        <p>Le code d’analyse a été retiré. Restent les tableaux, les graphiques, et le fil
        qui relie les trois parties.</p>
      </header>
      {''.join(body_parts)}
      {SYNTHESE}
      <footer class="fin">Document fusionné à partir des notebooks 001, 002 et 003.
      Couleurs et typographie : design system (Outfit, fond crème, terracotta).</footer>
    </div>
  </div>
</body>
</html>
"""
    # Drop leftover jupyter prompts if any
    html = re.sub(r"In&nbsp;\[[0-9]+\]:", "", html)
    html = html.replace("¶", "")
    target = ROOT / "rapport.html"
    target.write_text(html, encoding="utf-8")
    print(f"Écrit {target} ({target.stat().st_size / 1024:.0f} Ko)")


if __name__ == "__main__":
    main()
