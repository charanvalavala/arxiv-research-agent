from __future__ import annotations

import io
import unittest
from unittest.mock import patch

from arxiv_research_agent.client import ArxivSearchError, search_papers


def atom_feed(count: int, *, first_id: str = "http://arxiv.org/abs/2601.00000v1") -> bytes:
    entries = []
    for index in range(count):
        paper_id = first_id if index == 0 else f"https://arxiv.org/abs/2601.{index:05d}v1"
        entries.append(
            f"<entry><id>{paper_id}</id><title>Paper {index}</title>"
            f"<summary>Abstract {index}</summary><published>2026-01-01T00:00:00Z</published>"
            f"<updated>2026-01-02T00:00:00Z</updated><author><name>Author {index}</name></author></entry>"
        )
    return f'<feed xmlns="http://www.w3.org/2005/Atom">{"".join(entries)}</feed>'.encode()


class ArxivClientTests(unittest.TestCase):
    def test_caps_results_and_normalizes_canonical_urls(self):
        response = io.BytesIO(atom_feed(8))
        with patch("arxiv_research_agent.client.urllib.request.urlopen", return_value=response) as open_url:
            papers = search_papers("tool-using research agents")

        self.assertEqual(len(papers), 5)
        self.assertEqual(papers[0].url, "https://arxiv.org/abs/2601.00000v1")
        self.assertEqual(papers[0].authors, ("Author 0",))
        self.assertIn("max_results=5", open_url.call_args.args[0].full_url)
        self.assertEqual(open_url.call_args.kwargs["timeout"], 12)

    def test_rejects_non_arxiv_record_urls(self):
        with patch(
            "arxiv_research_agent.client.urllib.request.urlopen",
            return_value=io.BytesIO(atom_feed(1, first_id="https://example.com/paper/1")),
        ):
            self.assertEqual(search_papers("agents"), [])

    def test_rejects_blank_and_oversized_queries_before_network(self):
        with patch("arxiv_research_agent.client.urllib.request.urlopen") as open_url:
            with self.assertRaises(ValueError):
                search_papers("  ")
            with self.assertRaises(ValueError):
                search_papers("x" * 201)
        open_url.assert_not_called()

    def test_rejects_malformed_feed(self):
        with patch(
            "arxiv_research_agent.client.urllib.request.urlopen",
            return_value=io.BytesIO(b"<feed>"),
        ):
            with self.assertRaises(ArxivSearchError):
                search_papers("agents")


if __name__ == "__main__":
    unittest.main()
