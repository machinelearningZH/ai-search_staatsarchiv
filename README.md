# Intelligent Document Search for the Staatsarchiv Zurich

**Enhance access to the central collections of the Staatsarchiv Zürich with an intelligent hybrid search application.**

![GitHub License](https://img.shields.io/github/license/machinelearningzh/ai-search_staatsarchiv)
[![PyPI - Python](https://img.shields.io/badge/python-v3.9+-blue.svg)](https://github.com/machinelearningZH/ai-search_staatsarchiv)
[![GitHub Stars](https://img.shields.io/github/stars/machinelearningZH/ai-search_staatsarchiv.svg)](https://github.com/machinelearningZH/ai-search_staatsarchiv/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/machinelearningZH/ai-search_staatsarchiv.svg)](https://github.com/machinelearningZH/ai-search_staatsarchiv/issues)
[![GitHub Issues](https://img.shields.io/github/issues-pr/machinelearningZH/ai-search_staatsarchiv.svg)](https://img.shields.io/github/issues-pr/machinelearningZH/ai-search_staatsarchiv)
[![Current Version](https://img.shields.io/badge/version-1.0.0-green.svg)](https://github.com/machinelearningZH/ai-search_staatsarchiv)
<a href="https://github.com/astral-sh/ruff"><img alt="linting - Ruff" class="off-glb" loading="lazy" src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json"></a>

<details>

<summary>Contents</summary>

- [Usage](#usage)
- [Project Information](#project-information)
- [What Does the App Do?](#what-does-the-app-do)
- [Findings](#findings)
- [Project Team](#project-team)
- [Contributing](#feedback-and-contributing)

</details>

![](_imgs/app_ui.png)

## Usage

This repository provides the production-ready code for our search app, which is available online [here](https://www.zentraleserien-hybridesuche.zh.ch/).

To set up the app:

- Create a [Conda](https://conda.io/projects/conda/en/latest/index.html) environment: `conda create -n search python=3.9`
- Activate the environment: `conda activate search`
- Clone this repository.
- Change into the project directory: `cd ai-search_staatsarchiv/`
- Install the required packages: `pip install -r requirements.txt`

### Run the Notebooks to Prepare the Data

- Run the notebooks. Open these either in an IDE like [Visual Studio Code](https://code.visualstudio.com/). Alternatively, you can use [Jupyter Notebook](https://docs.jupyter.org/en/latest/running.html) or [Jupyter Lab](https://jupyter.org/install).
- Use the final notebook to create the [Weaviate](https://weaviate.io/developers/weaviate/installation/embedded) search index. Data is stored by default in `.local/share/weaviate/`. If you are deploying the app on a remote machine, copy the index data to the same path on the remote machine, or change the path in the app like so:
`client = weaviate.connect_to_embedded(persistence_data_path="/your_data_path_on_your_vm/")`.

### Run the Search App

- Change into app directory: `cd _streamlit_app/`
- Start the app: `streamlit run hybrid_search_stazh.py`

> [!Note]
> The app logs user interactions locally to a file named `app.log`. If you prefer not to collect analytics, simply comment out the relevant function call in the code.

### Embedding Model

For the embeddings we use [Jina AI's](https://jina.ai/) model [jina-embeddings-v2-base-de](https://huggingface.co/jinaai/jina-embeddings-v2-base-de). The model is a German/English bilingual text embedding model supporting 8,192 sequence length. According to the model card it is designed for «high performance in mono-lingual & cross-lingual applications and trained … specifically to support mixed German-English input without bias». Technical report [here](https://arxiv.org/abs/2402.17016).

We tested several other models as well. PM-AI's [bi-encoder_msmarco_bert-base_german](https://huggingface.co/PM-AI/bi-encoder_msmarco_bert-base_german) model proved to be comparable and an excellent choice too. Jina's model offers more flexibility in terms of context (8,192 tokens vs. 350) and provides bilingual capabilities. Both models are relatively lightweight, with PM-AI's model at 440 MB and Jina's at 326 MB.

Note that we chunk all text on a sentence basis to a maximum of 500 tokens with a 100-token overlap.

## Project Information

The [Staatsarchiv Zürich](https://www.zh.ch/de/direktion-der-justiz-und-des-innern/staatsarchiv.html) manages and catalogs the «Zentralen Serien des Kantons Zürich 19. und 20. Jahrhundert» which include important historical documents such as minutes from the Cantonal Council, Government Council resolutions, collections of laws, and the Official Gazette. These records span from 1803 to the present, making them linguistically and thematically diverse.

We (the Staatsarchiv and the [Statistical Office](https://www.zh.ch/de/direktion-der-justiz-und-des-innern/statistisches-amt.html)) developed an intelligent search application that enhances access to these extensive archives.

For more information, see the following article in the magazine ABI Technik: <a href="https://www.degruyter.com/document/doi/10.1515/abitech-2025-0003/html" target="_blank">Mit Künstlicher Intelligenz zu besserer Nutzbarkeit: Die Zentralen Serien des Kantons Zürich (19. und 20. Jahrhundert) neu zugänglich gemacht</a>

## What Does the App Do?

This app allows users to search through these extensive archives using both lexical and semantic search methods. Unlike a traditional lexical search that looks for exact keywords, semantic search identifies words, sentences, or paragraphs with similar meanings, even if they don't exactly match the search term. For example, a search for «technology» might return documents containing related concepts like «digitalization», «artificial intelligence», «software development», or «computer science» even if «technology» isn't mentioned directly.

Additionally, semantic search can retrieve documents related to a reference text. For instance, entering a document reference like RRB 1804/1 will return documents with similar themes.

Semantic search leverages statistical methods and machine learning to analyze large text corpora, allowing models to learn word and sentence similarities, enabling more nuanced document retrieval. While semantic search offers significant benefits, results can sometimes be incomplete or include irrelevant matches.

## Findings

- **Hybrid search significantly improves search results compared to traditional lexical search.** , especially for complex or fuzzy queries and large corpora spanning over two centuries.
- The embedding models we tested (and the one we use in the app) are astonishingly agnostic to the historical language used in the documents. Based on our observations, these models can capture the semantic meaning of very old texts too.
- [Weaviate](https://weaviate.io/) has proven to be a reliable and efficient tool for semantic search. It is easy to use and integrates well with Python.
- The app is inexpensive to run and maintain. It can be deployed on a local machine or a virtual machine with moderate resources. At the moment we use a VM with 8 CPUs and 32 GB RAM.

## Project Team

**Rebekka Plüss** (Staatsarchiv) and **Patrick Arnecke** (Statistisches Amt, Team Data). A big thanks goes to **Sarah Murer** and **Dominik Frefel** too!

## Feedback and Contributing

We welcome your feedback! Please share your thoughts and let us know how you use the app in your institution. You can [email us](staatsarchivzh@ji.zh.ch) or contribute by opening an issue or a pull request.

Please note that we use [Ruff](https://docs.astral.sh/ruff/) for linting and code formatting with default settings.
