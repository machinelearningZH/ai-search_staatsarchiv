import re
from tqdm import tqdm
import pandas as pd
import numpy as np
import glob
from bs4 import BeautifulSoup
import warnings
from bs4 import XMLParsedAsHTMLWarning
import spacy
from transformers import AutoTokenizer

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


def read_XML_files(folder_path, remove_memberlists=False):
    """Read XML files recursively from a directory and return a list of file paths.

    Parameters
    ----------
    folder_path : str
        The path to the directory containing the XML files.
    remove_memberlists : bool, optional
        Whether to remove files containing the word "mitgliederliste" in their name.

    Returns
    -------
    all_files : list
        A list of file paths of XML files.
    """

    xml_file_paths = []
    for filename in glob.glob(f"{folder_path}**/*.xml", recursive=True):
        xml_file_paths.append(filename)
    if remove_memberlists:
        xml_file_paths = [x for x in xml_file_paths if "mitgliederliste" not in x]
    print(f"{len(xml_file_paths):,.0f} files found.")
    return xml_file_paths


def parse_XML_files(file_paths):
    """
    Parse XML files and extract relevant information.

    Parameters
    ----------
    paths : list
        List of paths to XML files.

    Returns
    -------
    data : pd.DataFrame
        DataFrame with extracted information.
    """

    results = []
    for file_path in tqdm(file_paths):
        tmp = []
        with open(file_path) as file:
            soup = BeautifulSoup(file, "lxml")

        tmp.append(file_path)

        # Check if file is empty.
        if len(soup) == 0:
            print(file_path)
            continue

        # Parse date.
        if soup.sourcedesc.date is not None:
            tmp.append(soup.sourcedesc.date.get("when"))
            tmp.append(soup.sourcedesc.date.get("from"))
            tmp.append(soup.sourcedesc.date.get("to"))
            tmp.append(soup.sourcedesc.date.text)
        else:
            tmp.append(np.nan)
            tmp.append(np.nan)
            tmp.append(np.nan)
            tmp.append(np.nan)

        # Parse identifier.
        if soup.sourcedesc.ident is not None:
            tmp.append(soup.sourcedesc.ident.text)
        else:
            tmp.append(np.nan)

        # Parse link to search portal.
        target = soup.sourcedesc.ref.get("target")
        if target == "leer":
            tmp.append(np.nan)
        else:
            tmp.append(target)

        # Parse title.
        tmp.append(soup.sourcedesc.title.get_text())

        # Parse text taking nested tables elements into account.
        text = soup.find("text")
        tmp_text = []
        for elem in text.find_all(recursive=False):
            if elem.name == "table":
                for row in elem.find_all("row"):
                    for cell in row.find_all("cell"):
                        if cell.text:
                            tmp_text.append(cell.text)
            else:
                if elem.text:
                    tmp_text.append(elem.text)
        tmp.append(" ".join(tmp_text))

        results.append(tmp)

    data = pd.DataFrame(
        results,
        columns=[
            "path",
            "date_when",
            "date_from",
            "date_to",
            "date_text",
            "ident",
            "ref",
            "title",
            "text",
        ],
    )
    # Extract filenames from paths.
    data["filename"] = data.path.apply(lambda x: x.split("/")[-1])
    return data


def fix_missing_dates(data):
    """Fill missing dates in `date_when` with `date_from`.

    Parameters
    ----------
    data : pd.DataFrame
        Data to fix.

    Returns
    -------
    data : pd.DataFrame
        Data with missing dates filled.
    """
    to_fill = data[data.date_when.isna()].index
    data.loc[to_fill, "date_when"] = data.loc[to_fill, "date_from"]
    return data


def fix_incomplete_dates(data):
    """Add first day of month to dates in `date_when` where the day is missing.

    Parameters
    ----------
    data : pd.DataFrame
        Data to fix.

    Returns
    -------
    data : pd.DataFrame
        Data with fixed dates.
    """
    tmp = pd.to_datetime(data.date_when, errors="coerce", format="%Y-%m-%d")
    to_check = tmp[tmp.isna()].index
    data.loc[to_check, "date_when"] = data.loc[to_check, "date_when"].apply(
        lambda x: x + "-01"
    )
    return data


def add_missing_month_and_day_to_dates(data):
    """Add missing month and day to dates in `date_when` where the month and day are missing.

    Parameters
    ----------
    data : pd.DataFrame
        Data to fix.

    Returns
    -------
    data : pd.DataFrame
        Data with fixed dates.
    """
    # Successively add month and day to dates where they are missing.
    for _ in range(2):
        tmp = pd.to_datetime(data.date_when, errors="coerce", format="%Y-%m-%d")
        incomplete_dates = tmp[tmp.isna()].index
        data.loc[incomplete_dates, "date_when"] = (
            data.loc[incomplete_dates, "date_when"] + "-01"
        )
    return data


def parse_dates(data):
    """Parse dates in `date_when` column.

    Parameters
    ----------
    data : pd.DataFrame
        Data to parse.

    Returns
    -------
    data : pd.DataFrame
        Data with parsed dates.
    """
    data.date_when = pd.to_datetime(data.date_when, errors="coerce", format="%Y-%m-%d")
    return data


def clean_identifiers(data):
    """Remove line breaks from identifiers in `ident` column.

    Parameters
    ----------
    data : pd.DataFrame
        Data to clean.

    Returns
    -------
    data : pd.DataFrame
        Data with cleaned identifiers.
    """
    data.ident = data.ident.apply(lambda x: x.replace("\n", ""))
    data.ident = data.ident.apply(lambda x: re.sub(r"\s+", " ", x))
    data.ident = data.ident.apply(lambda x: x.strip())
    return data


def reformat_rrb_ids(data):
    """
    Reformat rrb_id to standard of [year]-[decision number]-[document number].
    Several hundert RRBs consist of several documents.
    Retrieve consecutive nummber of additional docs that belong to the RRB as integer.

    Parameters
    ----------
    data : pd.DataFrame
        DataFrame containing the data.

    Returns
    -------
    pd.DataFrame
        DataFrame with reformatted rrb_id.
    """

    data["rrb_year"] = data.rrb_id.apply(lambda x: x.split("_")[0])
    data["rrb_no"] = data.rrb_id.apply(lambda x: x.split("_")[1])
    data["rrb_no_add"] = data.rrb_no.apply(lambda x: x[4:])
    data.rrb_no = data.rrb_no.apply(lambda x: x[:4])

    additional_id = sorted([x for x in data.rrb_no_add.unique()])
    mapping = dict(zip(additional_id, range(1, len(additional_id) + 2)))

    data.rrb_no_add = data.rrb_no_add.map(mapping)
    data.rrb_id = (
        data.rrb_year.astype(str)
        + "-"
        + data.rrb_no.astype(str)
        + "-"
        + data.rrb_no_add.astype(str)
    )
    data.drop(columns=["rrb_year", "rrb_no", "rrb_no_add"], inplace=True)
    return data


BASE_DOC_LINK_RRB = "https://archives-quickaccess.ch/stazh/rrb/ref/"


def create_rrb_doc_link(fn):
    """Create link to online version of RRBs by parsing the filename and adding a base link.

    Parameters
    ----------
    fn : str
        Filename of the RRB document.

    Returns
    -------
    link : str
        Link to the online version of the RRB document.
    """
    fn = fn.split("_")
    band = fn[1:3]
    band = ".".join(band)
    year = fn[4]
    doc_no = fn[5].replace(".xml", "")
    link = f"{BASE_DOC_LINK_RRB}MM+{band}+RRB+{year}/{doc_no}"
    return link


pattern = r"(\x04|\x1a|\xa0|\x00|\ue83a|\x19|\uf06c|\x10|\x17|\x13|\x11|<space>|\x16|\x18|\x1b|\x15|\t\b|\f)"
ESCAPE_SEQS = re.compile(pattern)

pattern = (
    r"(?<=\s)(I.|II.|III.|IV.|V.|VI.|VII.|VIII.|IX.|X.|XI.|XII.|XIII.|XIV.|XV.)(?=\s)"
)
ROMAN_NUMERALS = re.compile(pattern)


def generic_text_cleaning(d):
    """
    Clean some generic text issues.

    Parameters
    ----------
    d : str
        Text to be cleaned.

    Returns
    -------
    d : str
        Cleaned text.
    """

    d = d.strip()

    # Remove non breaking spaces and escape sequences.
    d = re.sub(ESCAPE_SEQS, " ", d)

    # Remove punctuations.
    d = re.sub(r"[;«»„“:()\[\]]", " ", d)

    # Remove multiple dots.
    d = re.sub(r"\.{2,}", " ", d)

    # Remove roman numerals.
    d = re.sub(ROMAN_NUMERALS, " ", d)

    # Replace several symbolic chars with actual word.
    d = re.sub(r"&", " und ", d)
    d = re.sub(r"§", " Paragraph ", d)
    d = re.sub(r"=", " gleich ", d)

    # Replace multiple spaces with single space.
    d = re.sub(r"\s+", " ", d)

    # Again strip whitespace after all cleaning operations.
    d = d.strip()

    return d


nlp = spacy.load("de_core_news_lg")
# https://huggingface.co/jinaai/jina-embeddings-v2-base-de
model_path = "jinaai/jina-embeddings-v2-base-de"
tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True)


def chunk_text(data, max_token_count=512, overlap_tokens=50):
    """Chunk text into parts of max_token_count tokens with overlap_sents sentences overlap.

    Parameters
    ----------
    data : pd.DataFrame
        DataFrame containing the data.
    max_token_count : int, optional
        The maximum number of tokens per chunk, by default 512.
    overlap_sents : int, optional
        The number of sentences to overlap between chunks, by default 5.

    Returns
    -------
    list
        List of tuples containing the identifier and the chunked text.
    """

    # Sentencize text.
    doc = nlp(data.text)
    sents = [sent.text for sent in doc.sents]

    # Count tokens in each sentence.
    # TODO: Sentences can potentially be longer than max_token_count. Find a way to handle this.
    tokens = [len(tokenizer.tokenize(sent)) for sent in sents]

    # Create chunks by adding full sentences until max_token_count is reached.
    chunks = []
    current_chunk_start = 0
    current_sent = 0
    current_chunk = []
    current_tokens = 0

    while True:
        if current_sent >= len(sents):
            chunks.append(" ".join(current_chunk))
            break

        current_tokens += tokens[current_sent]
        if current_tokens < max_token_count:
            current_chunk.append(sents[current_sent])
            current_sent += 1
        else:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_tokens = 0

            # Go back n sents until we create an overlap of overlap_tokens or more.
            count_back_tokens = 0
            count_back_sents = 0
            while True:
                count_back_tokens += tokens[current_sent]
                count_back_sents += 1
                if count_back_tokens > overlap_tokens:
                    break
                current_sent -= 1
            current_sent -= count_back_sents

            # Avoid endless loop if overlap_sents is too high.
            if current_sent <= current_chunk_start:
                current_sent = current_chunk_start + 1
            current_chunk_start = current_sent

    return [(data.identifier, chunk) for chunk in chunks]
