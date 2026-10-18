# arXiv Research Agent Tool

A bounded research discovery tool for agent workflows. It queries the public
arXiv Atom API, returns up to five paper records with canonical URLs and
abstracts, and packages the results as structured provenance. The core client
uses Python's standard library; a thin optional-host adapter exposes it through
the DeerFlow extension API.

## Install

Python 3.12 or later is required. Install this package into the target agent
environment, where the host provides its extension API package:

```sh
python -m pip install .
```

Enable the extension in the host configuration:

```yaml
plugins:
  - use: arxiv_research_agent.deerflow_plugin:install
    config:
      enabled: true
```

The tool is named `search_arxiv_papers`. It accepts one focused query and
returns no more than five records. The API request has a 12-second timeout and
a 2 MB response limit. The core search client uses only the standard library;
the host adapter imports the extension API supplied by the agent environment.

## Run checks

```sh
python -m unittest discover -s tests -v
python -m compileall -q src tests
```

The tests cover the standard-library client with a local Atom fixture. They do
not depend on the live arXiv service and do not establish research relevance.

## Method and limits

The client uses arXiv's public [API](https://info.arxiv.org/help/api/index.html)
and follows its relevance ordering. Search coverage is limited to arXiv, result
rank is not a quality assessment, and abstracts are not a substitute for
reading the full paper. Abstract content is treated as untrusted input by the
agent adapter. Results include source URLs so claims can be checked against
the paper record.

## License

MIT. The arXiv API and research records remain governed by their respective
terms and licenses.
