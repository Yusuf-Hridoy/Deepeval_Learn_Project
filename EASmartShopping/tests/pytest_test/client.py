"""HTTP client for the Zentra backend. Not collected by pytest (no test_ prefix)."""

import requests


class ZentraClient:
    def __init__(self, base_url, chat_timeout=180):
        self.base_url = base_url.rstrip("/")
        self.chat_timeout = chat_timeout
        self.http = requests.Session()

    def _url(self, path):
        return f"{self.base_url}{path}"

    def health(self):
        r = self.http.get(self._url("/api/health"), timeout=5)
        r.raise_for_status()
        return r.json()

    def chat(self, message, session_id):
        r = self.http.post(
            self._url("/api/chat"),
            json={"message": message, "session_id": session_id},
            timeout=self.chat_timeout,
        )
        r.raise_for_status()
        return r.json()

    def retrieval_context(self, query, k=5):
        """
        Product context for retrieval metrics, from the same vector store the chat uses.
        NOTE: the chat normalizes a query before retrieving, so this approximates its
        context rather than copying it exactly.
        """
        r = self.http.get(
            self._url("/api/products/search/semantic"), params={"q": query}, timeout=60
        )
        r.raise_for_status()
        return [
            f"{p.get('name', '')} | {p.get('category', '')} | ${p.get('price', '')} "
            f"| rating {p.get('rating', '')} | {p.get('description', '')}"
            for p in r.json()[:k]
        ]

    def cart(self, session_id):
        r = self.http.get(self._url(f"/api/cart/{session_id}"), timeout=30)
        r.raise_for_status()
        return r.json()

    def cart_product_names(self, session_id):
        return [
            (item.get("product") or {}).get("name", "")
            for item in self.cart(session_id)["items"]
        ]

    def reset_session(self, session_id):
        """Best-effort cleanup so chat history and cart never leak between tests."""
        for path in (f"/api/chat/{session_id}/session", f"/api/cart/{session_id}/clear"):
            try:
                self.http.delete(self._url(path), timeout=10)
            except Exception:
                pass

    def close(self):
        self.http.close()
