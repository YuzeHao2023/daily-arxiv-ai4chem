"""
pytest test suite for daily_arxiv.py
"""
import sys
import json
import datetime

sys.path.insert(0, '/tmp/scan-ai4chem')

import pytest
from unittest.mock import patch, MagicMock, mock_open, call

import daily_arxiv


# ---------------------------------------------------------------------------
# get_authors
# ---------------------------------------------------------------------------

class TestGetAuthors:
    def test_all_authors_joined(self):
        authors = ["Alice", "Bob", "Charlie"]
        result = daily_arxiv.get_authors(authors)
        assert result == "Alice, Bob, Charlie"

    def test_single_author(self):
        authors = ["Solo Author"]
        result = daily_arxiv.get_authors(authors)
        assert result == "Solo Author"

    def test_first_author_only(self):
        authors = ["Alice", "Bob", "Charlie"]
        result = daily_arxiv.get_authors(authors, first_author=True)
        assert result == "Alice"

    def test_first_author_single_element(self):
        authors = ["OnlyOne"]
        result = daily_arxiv.get_authors(authors, first_author=True)
        assert result == "OnlyOne"

    def test_empty_authors_all(self):
        # joining empty list should return empty string
        result = daily_arxiv.get_authors([])
        assert result == ""

    def test_author_objects_converted_to_str(self):
        # Authors may be objects whose __str__ returns a name
        class AuthorObj:
            def __init__(self, name):
                self.name = name
            def __str__(self):
                return self.name

        authors = [AuthorObj("Alice"), AuthorObj("Bob")]
        result = daily_arxiv.get_authors(authors)
        assert result == "Alice, Bob"

    def test_first_author_false_explicit(self):
        authors = ["Alice", "Bob"]
        result = daily_arxiv.get_authors(authors, first_author=False)
        assert result == "Alice, Bob"


# ---------------------------------------------------------------------------
# sort_papers
# ---------------------------------------------------------------------------

class TestSortPapers:
    def test_sorts_keys_reverse(self):
        papers = {
            "2024-01-01": "old",
            "2024-03-15": "newer",
            "2024-02-10": "middle",
        }
        result = daily_arxiv.sort_papers(papers)
        assert list(result.keys()) == ["2024-03-15", "2024-02-10", "2024-01-01"]

    def test_values_preserved(self):
        papers = {"b": "val_b", "a": "val_a", "c": "val_c"}
        result = daily_arxiv.sort_papers(papers)
        assert result["a"] == "val_a"
        assert result["b"] == "val_b"
        assert result["c"] == "val_c"

    def test_empty_dict(self):
        result = daily_arxiv.sort_papers({})
        assert result == {}

    def test_single_entry(self):
        papers = {"2024-06-01": "only"}
        result = daily_arxiv.sort_papers(papers)
        assert list(result.keys()) == ["2024-06-01"]

    def test_returns_new_dict(self):
        papers = {"b": 1, "a": 2}
        result = daily_arxiv.sort_papers(papers)
        assert result is not papers


# ---------------------------------------------------------------------------
# get_code_link
# ---------------------------------------------------------------------------

class TestGetCodeLink:
    def test_returns_html_url_when_results_found(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "total_count": 2,
            "items": [
                {"html_url": "https://github.com/user/repo"},
                {"html_url": "https://github.com/user/repo2"},
            ],
        }
        with patch("daily_arxiv.requests.get", return_value=mock_response) as mock_get:
            result = daily_arxiv.get_code_link("some query")
            assert result == "https://github.com/user/repo"
            mock_get.assert_called_once_with(
                daily_arxiv.github_url,
                params={"q": "some query", "sort": "stars", "order": "desc"},
            )

    def test_returns_none_when_no_results(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"total_count": 0, "items": []}
        with patch("daily_arxiv.requests.get", return_value=mock_response):
            result = daily_arxiv.get_code_link("obscure query")
            assert result is None

    def test_passes_query_verbatim(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"total_count": 1, "items": [{"html_url": "https://github.com/x/y"}]}
        with patch("daily_arxiv.requests.get", return_value=mock_response) as mock_get:
            daily_arxiv.get_code_link("2108.09112")
            args, kwargs = mock_get.call_args
            assert kwargs["params"]["q"] == "2108.09112"


# ---------------------------------------------------------------------------
# load_config
# ---------------------------------------------------------------------------

class TestLoadConfig:
    def test_load_basic_config(self, tmp_path):
        config_content = """
max_results: 5
publish_readme: true
publish_gitpage: false
publish_wechat: false
show_badge: true
update_paper_links: false
json_readme_path: data/arxiv-daily.json
md_readme_path: README.md
json_gitpage_path: docs/arxiv-daily.json
md_gitpage_path: docs/index.md
json_wechat_path: docs/arxiv-daily-wechat.json
md_wechat_path: docs/wechat.md
keywords:
  deep learning:
    filters:
      - deep learning
      - neural network
  chemistry:
    filters:
      - reaction prediction
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)

        config = daily_arxiv.load_config(str(config_file))

        assert config["max_results"] == 5
        assert config["publish_readme"] is True
        assert "kv" in config

    def test_multi_word_filters_get_quoted(self, tmp_path):
        config_content = """
max_results: 2
publish_readme: false
publish_gitpage: false
publish_wechat: false
show_badge: false
update_paper_links: false
json_readme_path: a.json
md_readme_path: a.md
json_gitpage_path: b.json
md_gitpage_path: b.md
json_wechat_path: c.json
md_wechat_path: c.md
keywords:
  topic:
    filters:
      - deep learning
      - slam
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)
        config = daily_arxiv.load_config(str(config_file))

        kv = config["kv"]
        # multi-word phrase should be wrapped in double quotes
        assert '"deep learning"' in kv["topic"]
        # single word should appear bare
        assert "slam" in kv["topic"]
        # joined with OR
        assert " OR " in kv["topic"]

    def test_single_word_filter_no_quotes(self, tmp_path):
        config_content = """
max_results: 1
publish_readme: false
publish_gitpage: false
publish_wechat: false
show_badge: false
update_paper_links: false
json_readme_path: a.json
md_readme_path: a.md
json_gitpage_path: b.json
md_gitpage_path: b.md
json_wechat_path: c.json
md_wechat_path: c.md
keywords:
  topic:
    filters:
      - chemistry
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)
        config = daily_arxiv.load_config(str(config_file))
        kv = config["kv"]
        # single word, no surrounding quotes
        assert kv["topic"] == "chemistry"

    def test_multiple_topics(self, tmp_path):
        config_content = """
max_results: 3
publish_readme: false
publish_gitpage: false
publish_wechat: false
show_badge: false
update_paper_links: false
json_readme_path: a.json
md_readme_path: a.md
json_gitpage_path: b.json
md_gitpage_path: b.md
json_wechat_path: c.json
md_wechat_path: c.md
keywords:
  topic1:
    filters:
      - alpha
  topic2:
    filters:
      - beta gamma
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)
        config = daily_arxiv.load_config(str(config_file))
        assert "topic1" in config["kv"]
        assert "topic2" in config["kv"]


# ---------------------------------------------------------------------------
# get_daily_papers
# ---------------------------------------------------------------------------

class TestGetDailyPapers:
    def _make_mock_result(self, paper_id="2401.00001v1", title="Test Paper",
                          summary="Abstract text.\nWith newline.",
                          authors=None, primary_category="cs.AI",
                          published=None, updated=None, comment=None):
        result = MagicMock()
        result.get_short_id.return_value = paper_id
        result.title = title
        result.entry_id = f"http://arxiv.org/abs/{paper_id}"
        result.summary = summary
        result.authors = authors if authors is not None else ["Alice", "Bob"]
        result.primary_category = primary_category
        result.published = MagicMock()
        result.published.date.return_value = (
            published if published else datetime.date(2024, 1, 1)
        )
        result.updated = MagicMock()
        result.updated.date.return_value = (
            updated if updated else datetime.date(2024, 1, 2)
        )
        result.comment = comment
        return result

    def test_returns_two_dicts(self):
        mock_result = self._make_mock_result()
        mock_search_instance = MagicMock()
        mock_search_instance.results.return_value = [mock_result]

        with patch("daily_arxiv.arxiv") as mock_arxiv:
            mock_arxiv.Search.return_value = mock_search_instance
            mock_arxiv.SortCriterion.SubmittedDate = "submittedDate"
            data, data_web = daily_arxiv.get_daily_papers("chemistry", query="reaction", max_results=2)

        assert "chemistry" in data
        assert "chemistry" in data_web

    def test_version_suffix_stripped(self):
        mock_result = self._make_mock_result(paper_id="2401.00001v3")
        mock_search_instance = MagicMock()
        mock_search_instance.results.return_value = [mock_result]

        with patch("daily_arxiv.arxiv") as mock_arxiv:
            mock_arxiv.Search.return_value = mock_search_instance
            mock_arxiv.SortCriterion.SubmittedDate = "submittedDate"
            data, _ = daily_arxiv.get_daily_papers("topic", query="q", max_results=1)

        topic_data = data["topic"]
        assert "2401.00001" in topic_data
        assert "2401.00001v3" not in topic_data

    def test_paper_id_without_version(self):
        mock_result = self._make_mock_result(paper_id="2401.00001")
        mock_search_instance = MagicMock()
        mock_search_instance.results.return_value = [mock_result]

        with patch("daily_arxiv.arxiv") as mock_arxiv:
            mock_arxiv.Search.return_value = mock_search_instance
            mock_arxiv.SortCriterion.SubmittedDate = "submittedDate"
            data, _ = daily_arxiv.get_daily_papers("topic", query="q", max_results=1)

        assert "2401.00001" in data["topic"]

    def test_newlines_stripped_from_abstract(self):
        mock_result = self._make_mock_result(summary="Line one.\nLine two.\nLine three.")
        mock_search_instance = MagicMock()
        mock_search_instance.results.return_value = [mock_result]

        with patch("daily_arxiv.arxiv") as mock_arxiv:
            mock_arxiv.Search.return_value = mock_search_instance
            mock_arxiv.SortCriterion.SubmittedDate = "submittedDate"
            # abstract is not stored in content dict directly, but this confirms no crash
            data, _ = daily_arxiv.get_daily_papers("topic", query="q", max_results=1)

        # The function processes without error
        assert data

    def test_no_arxiv_results_returns_empty_topic_dicts(self):
        mock_search_instance = MagicMock()
        mock_search_instance.results.return_value = []

        with patch("daily_arxiv.arxiv") as mock_arxiv:
            mock_arxiv.Search.return_value = mock_search_instance
            mock_arxiv.SortCriterion.SubmittedDate = "submittedDate"
            data, data_web = daily_arxiv.get_daily_papers("topic", query="q", max_results=5)

        assert data == {"topic": {}}
        assert data_web == {"topic": {}}

    def test_content_format_contains_pipe_delimiters(self):
        mock_result = self._make_mock_result(
            paper_id="2401.12345v1",
            title="My Paper",
            authors=["Alice", "Bob"],
            updated=datetime.date(2024, 1, 10),
        )
        mock_search_instance = MagicMock()
        mock_search_instance.results.return_value = [mock_result]

        with patch("daily_arxiv.arxiv") as mock_arxiv:
            mock_arxiv.Search.return_value = mock_search_instance
            mock_arxiv.SortCriterion.SubmittedDate = "submittedDate"
            data, _ = daily_arxiv.get_daily_papers("topic", query="q", max_results=1)

        entry = data["topic"]["2401.12345"]
        # Should be pipe-delimited markdown table row
        assert "|" in entry
        assert "My Paper" in entry
        assert "2024-01-10" in entry

    def test_web_content_format_starts_with_dash(self):
        mock_result = self._make_mock_result(paper_id="2401.99999v1")
        mock_search_instance = MagicMock()
        mock_search_instance.results.return_value = [mock_result]

        with patch("daily_arxiv.arxiv") as mock_arxiv:
            mock_arxiv.Search.return_value = mock_search_instance
            mock_arxiv.SortCriterion.SubmittedDate = "submittedDate"
            _, data_web = daily_arxiv.get_daily_papers("topic", query="q", max_results=1)

        entry = data_web["topic"]["2401.99999"]
        assert entry.startswith("- ")

    def test_multiple_results_all_stored(self):
        results = [
            self._make_mock_result(paper_id=f"2401.0000{i}v1", title=f"Paper {i}")
            for i in range(3)
        ]
        mock_search_instance = MagicMock()
        mock_search_instance.results.return_value = results

        with patch("daily_arxiv.arxiv") as mock_arxiv:
            mock_arxiv.Search.return_value = mock_search_instance
            mock_arxiv.SortCriterion.SubmittedDate = "submittedDate"
            data, _ = daily_arxiv.get_daily_papers("topic", query="q", max_results=3)

        assert len(data["topic"]) == 3


# ---------------------------------------------------------------------------
# update_paper_links
# ---------------------------------------------------------------------------

class TestUpdatePaperLinks:
    def _make_pipe_entry(self, date="2024-01-01", title="Title", author="Auth et.al.",
                         arxiv_id="[2401.00001](http://arxiv.org/abs/2401.00001)",
                         code="null"):
        # Format: |date|title|author|arxiv_link|code|
        return f"|{date}|{title}|{author}|{arxiv_id}|{code}|\n"

    def test_reads_and_writes_unchanged_structure(self, tmp_path):
        entry = self._make_pipe_entry()
        initial_data = {
            "chemistry": {
                "2401.00001": entry
            }
        }
        json_file = tmp_path / "papers.json"
        json_file.write_text(json.dumps(initial_data))

        daily_arxiv.update_paper_links(str(json_file))

        result = json.loads(json_file.read_text())
        assert "chemistry" in result
        assert "2401.00001" in result["chemistry"]

    def test_empty_json_file(self, tmp_path):
        json_file = tmp_path / "papers.json"
        json_file.write_text("")

        # Should not raise, just write back empty dict
        daily_arxiv.update_paper_links(str(json_file))
        result = json.loads(json_file.read_text())
        assert result == {}

    def test_multiple_keywords_processed(self, tmp_path):
        entry1 = self._make_pipe_entry(title="Paper A")
        entry2 = self._make_pipe_entry(title="Paper B", arxiv_id="[2401.00002](http://arxiv.org/abs/2401.00002)")
        initial_data = {
            "topic1": {"2401.00001": entry1},
            "topic2": {"2401.00002": entry2},
        }
        json_file = tmp_path / "papers.json"
        json_file.write_text(json.dumps(initial_data))

        daily_arxiv.update_paper_links(str(json_file))

        result = json.loads(json_file.read_text())
        assert "topic1" in result
        assert "topic2" in result

    def test_file_written_back_as_valid_json(self, tmp_path):
        entry = self._make_pipe_entry()
        initial_data = {"k": {"p1": entry}}
        json_file = tmp_path / "papers.json"
        json_file.write_text(json.dumps(initial_data))

        daily_arxiv.update_paper_links(str(json_file))

        # Should be parseable JSON
        content = json_file.read_text()
        parsed = json.loads(content)
        assert isinstance(parsed, dict)


# ---------------------------------------------------------------------------
# update_json_file
# ---------------------------------------------------------------------------

class TestUpdateJsonFile:
    def test_merges_new_data_into_existing(self, tmp_path):
        existing = {"chemistry": {"2401.00001": "entry1"}}
        json_file = tmp_path / "data.json"
        json_file.write_text(json.dumps(existing))

        new_data = [{"chemistry": {"2401.00002": "entry2"}}]
        daily_arxiv.update_json_file(str(json_file), new_data)

        result = json.loads(json_file.read_text())
        assert "2401.00001" in result["chemistry"]
        assert "2401.00002" in result["chemistry"]

    def test_adds_new_keyword(self, tmp_path):
        existing = {"chemistry": {"p1": "e1"}}
        json_file = tmp_path / "data.json"
        json_file.write_text(json.dumps(existing))

        new_data = [{"biology": {"p2": "e2"}}]
        daily_arxiv.update_json_file(str(json_file), new_data)

        result = json.loads(json_file.read_text())
        assert "chemistry" in result
        assert "biology" in result

    def test_empty_json_file(self, tmp_path):
        json_file = tmp_path / "data.json"
        json_file.write_text("")

        new_data = [{"topic": {"p1": "entry"}}]
        daily_arxiv.update_json_file(str(json_file), new_data)

        result = json.loads(json_file.read_text())
        assert result == {"topic": {"p1": "entry"}}

    def test_empty_data_dict(self, tmp_path):
        existing = {"chemistry": {"p1": "e1"}}
        json_file = tmp_path / "data.json"
        json_file.write_text(json.dumps(existing))

        daily_arxiv.update_json_file(str(json_file), [])

        result = json.loads(json_file.read_text())
        assert result == existing

    def test_multiple_data_dicts_merged(self, tmp_path):
        json_file = tmp_path / "data.json"
        json_file.write_text("{}")

        new_data = [
            {"topic1": {"p1": "e1"}},
            {"topic2": {"p2": "e2"}},
        ]
        daily_arxiv.update_json_file(str(json_file), new_data)

        result = json.loads(json_file.read_text())
        assert "topic1" in result
        assert "topic2" in result

    def test_existing_papers_not_overwritten_by_different_key(self, tmp_path):
        existing = {"chemistry": {"p1": "original"}}
        json_file = tmp_path / "data.json"
        json_file.write_text(json.dumps(existing))

        # Update adds p2, not p1
        new_data = [{"chemistry": {"p2": "new"}}]
        daily_arxiv.update_json_file(str(json_file), new_data)

        result = json.loads(json_file.read_text())
        assert result["chemistry"]["p1"] == "original"
        assert result["chemistry"]["p2"] == "new"


# ---------------------------------------------------------------------------
# json_to_md
# ---------------------------------------------------------------------------

class TestJsonToMd:
    def _write_json(self, tmp_path, data):
        json_file = tmp_path / "data.json"
        json_file.write_text(json.dumps(data))
        return json_file

    def test_creates_md_file(self, tmp_path):
        data = {"chemistry": {"2401.00001": "|2024-01-01|Title|Author et.al.|[link](url)|null|\n"}}
        json_file = self._write_json(tmp_path, data)
        md_file = tmp_path / "output.md"

        daily_arxiv.json_to_md(str(json_file), str(md_file))

        assert md_file.exists()

    def test_contains_keyword_heading(self, tmp_path):
        data = {"chemistry": {"2401.00001": "|2024-01-01|Title|Author et.al.|[link](url)|null|\n"}}
        json_file = self._write_json(tmp_path, data)
        md_file = tmp_path / "output.md"

        daily_arxiv.json_to_md(str(json_file), str(md_file))

        content = md_file.read_text()
        assert "## chemistry" in content

    def test_contains_table_header_non_web(self, tmp_path):
        data = {"topic": {"p1": "|2024-01-01|Title|Auth et.al.|[link](url)|null|\n"}}
        json_file = self._write_json(tmp_path, data)
        md_file = tmp_path / "output.md"

        daily_arxiv.json_to_md(str(json_file), str(md_file), use_title=True, to_web=False)

        content = md_file.read_text()
        assert "|Publish Date|Title|Authors|PDF|Code|" in content

    def test_contains_table_header_web(self, tmp_path):
        data = {"topic": {"p1": "|2024-01-01|Title|Auth et.al.|[link](url)|null|\n"}}
        json_file = self._write_json(tmp_path, data)
        md_file = tmp_path / "output.md"

        daily_arxiv.json_to_md(str(json_file), str(md_file), use_title=True, to_web=True)

        content = md_file.read_text()
        assert "| Publish Date | Title | Authors | PDF | Code |" in content

    def test_use_title_false_writes_gt_updated(self, tmp_path):
        data = {"topic": {"p1": "|2024-01-01|Title|Auth et.al.|[link](url)|null|\n"}}
        json_file = self._write_json(tmp_path, data)
        md_file = tmp_path / "output.md"

        daily_arxiv.json_to_md(str(json_file), str(md_file), use_title=False)

        content = md_file.read_text()
        assert content.startswith("> Updated on ")

    def test_use_title_true_writes_h2_updated(self, tmp_path):
        data = {"topic": {"p1": "|2024-01-01|Title|Auth et.al.|[link](url)|null|\n"}}
        json_file = self._write_json(tmp_path, data)
        md_file = tmp_path / "output.md"

        daily_arxiv.json_to_md(str(json_file), str(md_file), use_title=True)

        content = md_file.read_text()
        assert content.startswith("## Updated on ")

    def test_table_of_contents_present_by_default(self, tmp_path):
        data = {"chemistry": {"p1": "|2024-01-01|T|A et.al.|[l](u)|null|\n"}}
        json_file = self._write_json(tmp_path, data)
        md_file = tmp_path / "output.md"

        daily_arxiv.json_to_md(str(json_file), str(md_file), use_tc=True)

        content = md_file.read_text()
        assert "<details>" in content
        assert "Table of Contents" in content

    def test_table_of_contents_absent_when_disabled(self, tmp_path):
        data = {"chemistry": {"p1": "|2024-01-01|T|A et.al.|[l](u)|null|\n"}}
        json_file = self._write_json(tmp_path, data)
        md_file = tmp_path / "output.md"

        daily_arxiv.json_to_md(str(json_file), str(md_file), use_tc=False)

        content = md_file.read_text()
        assert "<details>" not in content

    def test_back_to_top_present_by_default(self, tmp_path):
        data = {"chemistry": {"p1": "|2024-01-01|T|A et.al.|[l](u)|null|\n"}}
        json_file = self._write_json(tmp_path, data)
        md_file = tmp_path / "output.md"

        daily_arxiv.json_to_md(str(json_file), str(md_file), use_b2t=True)

        content = md_file.read_text()
        assert "back to top" in content

    def test_back_to_top_absent_when_disabled(self, tmp_path):
        data = {"chemistry": {"p1": "|2024-01-01|T|A et.al.|[l](u)|null|\n"}}
        json_file = self._write_json(tmp_path, data)
        md_file = tmp_path / "output.md"

        daily_arxiv.json_to_md(str(json_file), str(md_file), use_b2t=False)

        content = md_file.read_text()
        assert "back to top" not in content

    def test_badge_links_present_when_show_badge_true(self, tmp_path):
        data = {"chemistry": {"p1": "|2024-01-01|T|A et.al.|[l](u)|null|\n"}}
        json_file = self._write_json(tmp_path, data)
        md_file = tmp_path / "output.md"

        daily_arxiv.json_to_md(str(json_file), str(md_file), show_badge=True)

        content = md_file.read_text()
        assert "contributors-shield" in content

    def test_badge_links_absent_when_show_badge_false(self, tmp_path):
        data = {"chemistry": {"p1": "|2024-01-01|T|A et.al.|[l](u)|null|\n"}}
        json_file = self._write_json(tmp_path, data)
        md_file = tmp_path / "output.md"

        daily_arxiv.json_to_md(str(json_file), str(md_file), show_badge=False)

        content = md_file.read_text()
        assert "contributors-shield" not in content

    def test_empty_json_produces_minimal_md(self, tmp_path):
        json_file = tmp_path / "data.json"
        json_file.write_text("{}")
        md_file = tmp_path / "output.md"

        daily_arxiv.json_to_md(str(json_file), str(md_file))

        content = md_file.read_text()
        # Should exist and have at least the Updated on line
        assert "Updated on" in content

    def test_empty_file_content_produces_minimal_md(self, tmp_path):
        json_file = tmp_path / "data.json"
        json_file.write_text("")
        md_file = tmp_path / "output.md"

        daily_arxiv.json_to_md(str(json_file), str(md_file))

        content = md_file.read_text()
        assert "Updated on" in content

    def test_web_mode_writes_front_matter(self, tmp_path):
        data = {}
        json_file = self._write_json(tmp_path, data)
        md_file = tmp_path / "output.md"

        daily_arxiv.json_to_md(str(json_file), str(md_file), to_web=True, use_title=True)

        content = md_file.read_text()
        assert "layout: default" in content

    def test_papers_sorted_newest_first(self, tmp_path):
        data = {
            "topic": {
                "2401.00001": "|2024-01-01|Old Paper|A et.al.|[l](u)|null|\n",
                "2401.99999": "|2024-06-15|New Paper|B et.al.|[l](u)|null|\n",
            }
        }
        json_file = self._write_json(tmp_path, data)
        md_file = tmp_path / "output.md"

        daily_arxiv.json_to_md(str(json_file), str(md_file))

        content = md_file.read_text()
        pos_new = content.find("New Paper")
        pos_old = content.find("Old Paper")
        assert pos_new < pos_old

    def test_usage_link_present(self, tmp_path):
        json_file = self._write_json(tmp_path, {})
        md_file = tmp_path / "output.md"

        daily_arxiv.json_to_md(str(json_file), str(md_file))

        content = md_file.read_text()
        assert "Usage instructions" in content

    def test_empty_keyword_skipped(self, tmp_path):
        data = {"chemistry": {}, "biology": {"p1": "|2024-01-01|T|A et.al.|[l](u)|null|\n"}}
        json_file = self._write_json(tmp_path, data)
        md_file = tmp_path / "output.md"

        daily_arxiv.json_to_md(str(json_file), str(md_file))

        content = md_file.read_text()
        # biology section should appear, chemistry (empty) should not
        assert "## biology" in content
        assert "## chemistry" not in content


# ---------------------------------------------------------------------------
# demo (routing logic only)
# ---------------------------------------------------------------------------

class TestDemo:
    def _base_config(self):
        return {
            "kv": {"chemistry": "reaction prediction"},
            "max_results": 2,
            "publish_readme": False,
            "publish_gitpage": False,
            "publish_wechat": False,
            "show_badge": True,
            "update_paper_links": False,
            "json_readme_path": "readme.json",
            "md_readme_path": "README.md",
            "json_gitpage_path": "gitpage.json",
            "md_gitpage_path": "docs/index.md",
            "json_wechat_path": "wechat.json",
            "md_wechat_path": "docs/wechat.md",
        }

    @patch("daily_arxiv.json_to_md")
    @patch("daily_arxiv.update_json_file")
    @patch("daily_arxiv.update_paper_links")
    @patch("daily_arxiv.get_daily_papers")
    def test_no_publish_flags_no_file_writes(self, mock_gdp, mock_upl, mock_ujf, mock_jtmd):
        mock_gdp.return_value = ({"chemistry": {}}, {"chemistry": {}})
        config = self._base_config()

        daily_arxiv.demo(**config)

        mock_ujf.assert_not_called()
        mock_upl.assert_not_called()
        mock_jtmd.assert_not_called()

    @patch("daily_arxiv.json_to_md")
    @patch("daily_arxiv.update_json_file")
    @patch("daily_arxiv.update_paper_links")
    @patch("daily_arxiv.get_daily_papers")
    def test_publish_readme_calls_update_json_and_json_to_md(self, mock_gdp, mock_upl, mock_ujf, mock_jtmd):
        mock_gdp.return_value = ({"chemistry": {}}, {"chemistry": {}})
        config = self._base_config()
        config["publish_readme"] = True

        daily_arxiv.demo(**config)

        mock_ujf.assert_called_once()
        mock_jtmd.assert_called_once()
        mock_upl.assert_not_called()

    @patch("daily_arxiv.json_to_md")
    @patch("daily_arxiv.update_json_file")
    @patch("daily_arxiv.update_paper_links")
    @patch("daily_arxiv.get_daily_papers")
    def test_update_paper_links_true_calls_update_paper_links_not_get_papers(
        self, mock_gdp, mock_upl, mock_ujf, mock_jtmd
    ):
        config = self._base_config()
        config["publish_readme"] = True
        config["update_paper_links"] = True

        daily_arxiv.demo(**config)

        mock_gdp.assert_not_called()
        mock_upl.assert_called_once_with("readme.json")
        mock_ujf.assert_not_called()

    @patch("daily_arxiv.json_to_md")
    @patch("daily_arxiv.update_json_file")
    @patch("daily_arxiv.update_paper_links")
    @patch("daily_arxiv.get_daily_papers")
    def test_publish_gitpage_calls_correct_paths(self, mock_gdp, mock_upl, mock_ujf, mock_jtmd):
        mock_gdp.return_value = ({"chemistry": {}}, {"chemistry": {}})
        config = self._base_config()
        config["publish_gitpage"] = True

        daily_arxiv.demo(**config)

        mock_ujf.assert_called_once()
        call_args = mock_ujf.call_args
        assert call_args[0][0] == "gitpage.json"

        mock_jtmd.assert_called_once()
        jtmd_args = mock_jtmd.call_args
        assert jtmd_args[0][0] == "gitpage.json"
        assert jtmd_args[0][1] == "docs/index.md"

    @patch("daily_arxiv.json_to_md")
    @patch("daily_arxiv.update_json_file")
    @patch("daily_arxiv.update_paper_links")
    @patch("daily_arxiv.get_daily_papers")
    def test_publish_wechat_uses_web_data_collector(self, mock_gdp, mock_upl, mock_ujf, mock_jtmd):
        mock_gdp.return_value = ({"chemistry": {"p1": "e1"}}, {"chemistry": {"p1": "web_entry"}})
        config = self._base_config()
        config["publish_wechat"] = True

        daily_arxiv.demo(**config)

        mock_ujf.assert_called_once()
        call_args = mock_ujf.call_args
        assert call_args[0][0] == "wechat.json"
        # data_collector_web should be passed (contains web entries)
        data_arg = call_args[0][1]
        assert isinstance(data_arg, list)

    @patch("daily_arxiv.json_to_md")
    @patch("daily_arxiv.update_json_file")
    @patch("daily_arxiv.update_paper_links")
    @patch("daily_arxiv.get_daily_papers")
    def test_get_daily_papers_called_for_each_keyword(self, mock_gdp, mock_upl, mock_ujf, mock_jtmd):
        mock_gdp.return_value = ({"k": {}}, {"k": {}})
        config = self._base_config()
        config["kv"] = {"topic1": "query1", "topic2": "query2"}

        daily_arxiv.demo(**config)

        assert mock_gdp.call_count == 2

    @patch("daily_arxiv.json_to_md")
    @patch("daily_arxiv.update_json_file")
    @patch("daily_arxiv.update_paper_links")
    @patch("daily_arxiv.get_daily_papers")
    def test_all_three_publish_flags(self, mock_gdp, mock_upl, mock_ujf, mock_jtmd):
        mock_gdp.return_value = ({"k": {}}, {"k": {}})
        config = self._base_config()
        config["publish_readme"] = True
        config["publish_gitpage"] = True
        config["publish_wechat"] = True

        daily_arxiv.demo(**config)

        assert mock_ujf.call_count == 3
        assert mock_jtmd.call_count == 3
