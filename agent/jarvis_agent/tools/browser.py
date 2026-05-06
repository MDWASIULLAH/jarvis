from __future__ import annotations

import re
from typing import Any

import httpx
from bs4 import BeautifulSoup


class CloudBrowserTool:
    """Cloud browser/search/extraction tool with graceful fallbacks."""

    async def search(self, query: str, limit: int = 5) -> list[dict[str, str]]:
        try:
            from duckduckgo_search import DDGS

            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=limit))
            return [
                {
                    "title": item.get("title", "Untitled"),
                    "url": item.get("href", ""),
                    "snippet": item.get("body", ""),
                }
                for item in results
            ]
        except Exception:
            return await self._search_duckduckgo_html(query, limit)

    async def read_url(self, url: str) -> dict[str, Any]:
        try:
            return await self._read_with_playwright(url)
        except Exception:
            return await self._read_with_http(url)

    async def _read_with_playwright(self, url: str) -> dict[str, Any]:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30000)
            title = await page.title()
            text = await page.locator("body").inner_text(timeout=10000)
            await browser.close()
        return {"title": title, "url": url, "text": self._clean_text(text)}

    async def _read_with_http(self, url: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": "JarvisCloudAgent/1.0"})
            response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for node in soup(["script", "style", "noscript", "svg"]):
            node.decompose()
        title = soup.title.string.strip() if soup.title and soup.title.string else url
        return {"title": title, "url": url, "text": self._clean_text(soup.get_text(" "))}

    async def _search_duckduckgo_html(self, query: str, limit: int) -> list[dict[str, str]]:
        url = "https://duckduckgo.com/html/"
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            response = await client.post(url, data={"q": query}, headers={"User-Agent": "JarvisCloudAgent/1.0"})
            response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        rows: list[dict[str, str]] = []
        for result in soup.select(".result")[:limit]:
            link = result.select_one(".result__a")
            snippet = result.select_one(".result__snippet")
            if not link:
                continue
            rows.append(
                {
                    "title": link.get_text(" ", strip=True),
                    "url": link.get("href", ""),
                    "snippet": snippet.get_text(" ", strip=True) if snippet else "",
                }
            )
        return rows

    @staticmethod
    def _clean_text(text: str, max_chars: int = 6000) -> str:
        return re.sub(r"\s+", " ", text).strip()[:max_chars]
