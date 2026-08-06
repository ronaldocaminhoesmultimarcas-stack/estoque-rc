import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.rccaminhoesmultimarcas.com.br/"
HOME_URL = "https://www.rccaminhoesmultimarcas.com.br/19/"
OUTPUT = Path("docs/estoque.xml")
G_NS = "http://base.google.com/ns/1.0"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; RCCaminhoesCatalogBot/1.0; "
        "+https://www.rccaminhoesmultimarcas.com.br/)"
    )
}

def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()

def fetch(url):
    response = requests.get(url, headers=HEADERS, timeout=40)
    response.raise_for_status()
    return response.text

def vehicle_links():
    soup = BeautifulSoup(fetch(HOME_URL), "html.parser")
    links = set()

    for anchor in soup.find_all("a", href=True):
        href = urljoin(HOME_URL, anchor["href"])
        if "DetalhesVeiculo.aspx" in href and "veiculo=" in href:
            links.add(href)

    if not links:
        raise RuntimeError("Nenhum veículo foi encontrado na página de estoque.")

    return sorted(links)

def get_label_value(soup, label):
    label_regex = re.compile(rf"^{re.escape(label)}$", re.I)
    node = soup.find(string=label_regex)
    if not node:
        return ""

    parent = node.parent
    for candidate in (
        parent.find_next_sibling(),
        parent.parent.find_next_sibling() if parent.parent else None,
        parent.find_next(),
    ):
        if candidate:
            value = clean(candidate.get_text(" ", strip=True))
            if value and value.lower() != label.lower():
                return value
    return ""

def parse_price(text):
    match = re.search(r"R\$\s*([\d.]+,\d{2})", text)
    if not match:
        return ""
    value = match.group(1).replace(".", "").replace(",", ".")
    return f"{value} BRL"

def vehicle_data(url):
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")
    page_text = clean(soup.get_text(" ", strip=True))

    title_node = soup.find("h1")
    title = clean(title_node.get_text(" ", strip=True)) if title_node else ""
    if not title or "veículo não encontrado" in page_text.lower():
        return None

    vehicle_id = parse_qs(urlparse(url).query).get("veiculo", [""])[0]

    image = ""
    og_image = soup.find("meta", property="og:image")
    if og_image and og_image.get("content"):
        image = urljoin(url, og_image["content"])
    if not image:
        for img in soup.find_all("img", src=True):
            src = urljoin(url, img["src"])
            if "veiculos" in src.lower() and ("big" in src.lower() or "cloudfront" in src.lower()):
                image = src
                break

    description = ""
    desc_heading = soup.find(string=re.compile(r"^Descrição$", re.I))
    if desc_heading:
        container = desc_heading.parent
        for candidate in [container.find_next_sibling(), container.parent.find_next_sibling() if container.parent else None]:
            if candidate:
                description = clean(candidate.get_text(" ", strip=True))
                if len(description) > 20:
                    break

    if not description:
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            description = clean(meta_desc.get("content"))

    year = get_label_value(soup, "Ano")
    model_year = get_label_value(soup, "Ano do Modelo")
    mileage = get_label_value(soup, "Quilometragem")
    body = get_label_value(soup, "Carroceria")
    traction = get_label_value(soup, "Tração")
    color = get_label_value(soup, "Cor")

    brand = title.split()[0] if title else "RC Caminhões"
    if title.startswith("MERCEDES-BENZ"):
        brand = "MERCEDES-BENZ"
    elif title.startswith("KIA MOTORS"):
        brand = "KIA MOTORS"

    extra = ", ".join(
        part for part in [
            f"Ano {year}/{model_year}" if year or model_year else "",
            f"{mileage} km" if mileage else "",
            traction,
            body,
            f"cor {color}" if color else "",
        ] if part
    )

    return {
        "id": vehicle_id,
        "title": title,
        "description": description or extra or title,
        "availability": "in stock",
        "condition": "used",
        "price": parse_price(page_text),
        "link": url,
        "image_link": image,
        "brand": brand,
    }

def build_xml(items):
    ET.register_namespace("g", G_NS)
    rss = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "Estoque RC Caminhões Multimarcas"
    ET.SubElement(channel, "link").text = BASE_URL
    ET.SubElement(channel, "description").text = (
        "Feed automático de veículos disponíveis da RC Caminhões Multimarcas"
    )

    for data in items:
        item = ET.SubElement(channel, "item")
        for field in (
            "id", "title", "description", "availability", "condition",
            "price", "link", "image_link", "brand"
        ):
            value = data.get(field, "")
            if value:
                ET.SubElement(item, f"{{{G_NS}}}{field}").text = value

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ")
    tree.write(OUTPUT, encoding="utf-8", xml_declaration=True)

def main():
    links = vehicle_links()
    items = []

    for index, link in enumerate(links, start=1):
        try:
            data = vehicle_data(link)
            if data:
                items.append(data)
                print(f"[{index}/{len(links)}] OK: {data['title']}")
            else:
                print(f"[{index}/{len(links)}] Ignorado: veículo indisponível")
        except Exception as exc:
            print(f"[{index}/{len(links)}] Erro em {link}: {exc}", file=sys.stderr)
        time.sleep(0.5)

    if not items:
        raise RuntimeError("O XML não foi gerado porque nenhum veículo válido foi encontrado.")

    build_xml(items)
    print(f"XML atualizado com {len(items)} veículos em {OUTPUT}")

if __name__ == "__main__":
    main()