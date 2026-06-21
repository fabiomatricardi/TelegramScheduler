import trafilatura


def fetch_url_content(url: str) -> dict:
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return {"url": url, "title": "", "content": "", "error": "Failed to download"}

        title_match = ""
        if "<title>" in downloaded.lower():
            import re
            title_match = re.search(r"<title[^>]*>(.*?)</title>", downloaded, re.IGNORECASE | re.DOTALL)
            title_match = title_match.group(1).strip() if title_match else ""

        text = trafilatura.extract(downloaded, include_links=False, include_tables=False)
        if not text:
            return {"url": url, "title": title_match, "content": "", "error": "No text extracted"}

        return {"url": url, "title": title_match, "content": text[:5000], "error": None}
    except Exception as e:
        return {"url": url, "title": "", "content": "", "error": str(e)}


def process_urls(urls: list[str]) -> list[dict]:
    results = []
    for url in urls:
        result = fetch_url_content(url)
        if not result["error"]:
            results.append(result)
    return results
