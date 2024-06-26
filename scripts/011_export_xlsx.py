# import sys
import configparser
import datetime
import os
import os.path
import time

import fire
import jsonlines
import pandas as pd
import psutil


def do_export(config=None, outfile=None, initems=None):
    # read configuration file
    conf = configparser.ConfigParser()
    conf.read_file(open(config))

    data_dir = conf.get("main", "data_dir")

    # =====================================================
    # place to store extended item
    if outfile:
        file_path_output = outfile
    else:
        file_path_output = f"{data_dir}/010_extend_items_google_scholar.jsonl"
    print(("output", file_path_output))
    # =====================================================

    # =====================================================
    # load downloaded items
    file_path_items = f"{data_dir}/009_extend_items_output.jsonl"
    if initems and initems == "resume":
        file_path_items = file_path_output
    elif initems and os.path.isfile(initems):
        file_path_items = initems
    elif os.path.isfile(file_path_items):
        pass
    else:
        print("input file not found")
        return
    print(("infile", file_path_items))
    with jsonlines.open(file_path_items) as reader:
        items = {str(row["id"]): row for row in reader}
    # /load downloaded items
    # =====================================================

    now_year = datetime.datetime.utcnow().year
    rows = list()
    columns = [
        "Publication Year",  # A
        "Type",  # B
        "Venue",  # C
        "Publisher",  # D
        "Volume No",  # E
        "Issue No",  # F
        "Pages",  # G
        "DOI",  # H
        #'DOI Link',                 # I
        "ID",  # J This is the identifier of the doc in the MS Research repository.
        "Paper Title",  # K
        "Authors",  # L. This is the semicolon-separated list of the authors of the document.
        "Affiliations",  # M. This is the list of the affiliations of the document authors, semicolon
        "Complete Citation",  # N BibTex
        "Abstract",  # O
        "Category1",  # P
        "Category2",  # Q
        "Category3",  # R
        "Category4 - undefined",  # R
        "Key words",  # S
        "MS Topics",  # S
        "SPC (~Citations)",  # T (in citation network). Generated by the Snowball Sampling software.
        "Citations (GS)",  # U The citation count for the document acquired from Google Scholar
        "Citations per year (GS)",  # V This is the citation frequency we need for document ordering. The
        # formula is: Citation-Count-(U) / (&lt;current year&gt; - Publication-Year-(A)+1).
        "Document file name",  # W
        "MSR Entry (URL)",  # X The URL for the document description at MSR.
        "Full text download URL",  # Y. The URL for downloading the full text of the doc.
        "Full text Downloaded",  # Z. Boolean
    ]
    for item_id in items:
        item = items[item_id]
        flat_item = list()
        #         'Publication Year',         # A
        flat_item.append(item["year"])

        #         'Type',                     # B
        flat_item.append(item["publication_type"])

        #         'Venue',                    # C
        flat_item.append(item["venue_full_name"])

        #         'Publisher',                # D
        flat_item.append(item["publisher"])

        #         'Volume No',                # E
        flat_item.append(item["volume"])

        #         'Issue No',                 # F
        flat_item.append(item["issue"])

        #         'Pages',                    # G
        flat_item.append(f"""{item["page_first"]}-{item["page_last"]}""")

        #         'DOI',                      # H
        flat_item.append(item["doi"])

        # #         'DOI Link',                 # I
        # doi_link = None
        # if item["urls"]:
        #     for u in item["urls"]:
        #         if 'doi.org/' in u["U"]:
        #             doi_link = u["U"]
        # flat_item.append(doi_link)

        #         'MSF ID',                   # J This is the identifier of the doc in the MS Research repository.
        flat_item.append(item["id"])

        #         'Paper Title',              # K
        flat_item.append(item["title"])

        #         'Authors',                  # L. This is the semicolon-separated list of the authors of the document.
        authors = list()
        for au in item["authors"]:
            authors.append(au["name"])
        flat_item.append(";".join(authors))

        #         'Affiliations',             # M. This is the list of the affiliations of the authors, semicolon
        affiliations = list()
        for au in item["authors"]:
            affiliations.append(str(au.get("affiliation")))
        flat_item.append(";".join(affiliations))

        #         'Complete Citation',        # N BibTex
        flat_item.append(get_bibtex(item))

        #         'Abstract',                 # O
        abstract = item["abstract"]
        if len(abstract) < 5:
            if "google_scholar" in item:
                try:
                    abstract = item["google_scholar"][0]["abstract"]
                except:
                    pass
        flat_item.append(abstract)

        #         'Category1',                # P
        flat_item.append("")

        #         'Category2',                # Q
        flat_item.append("")

        #         'Category3',                # R
        flat_item.append("")

        #         'Category4',                # R
        flat_item.append("")

        #         'Key words',                # S
        flat_item.append("")

        #         'MS Topics',                # S
        ms_topics = list()
        for kw in item["topics"]:
            ms_topics.append(kw["name"])
        flat_item.append(";".join(ms_topics))

        #         'SPC (~Citations)',         # T (in citation network). Generated by the Snowball Sampling software.
        flat_item.append(item["spc"])

        #         'Citations (GS)',           # U The citation count for the document acquired from Google Scholar
        citations = 0
        try:
            citations = item["raw"]["cited_by_count"]
        except:
            pass
        flat_item.append(citations)

        # 'Citations per year (GS)', # V This is the citation frequency we need for document ordering. The
        #                            # formula is: Citation-Count-(U) / (&lt;current year&gt; - Publication-Year-(A)+1).
        citations_per_year = 0
        try:
            citations_per_year = citations / (now_year - int(item["year"]) + 1)
        except:
            pass
        flat_item.append(citations_per_year)

        #         'Document file name',       # W
        flat_item.append(item.get("pdf_file_name"))

        #         'MSR Entry (URL)',          # X The URL for the document description at MSR.
        flat_item.append(item["url"])

        #         'Full text download URL',   # Y. . The URL for downloading the full text of the doc.
        flat_item.append(item.get("pdf_url"))

        #         'Full text available'
        pdf_file_name = f'{data_dir}/pdfs/{item.get("pdf_file_name")}'
        pdf_present = os.path.exists(pdf_file_name)
        print(pdf_present, pdf_file_name)
        flat_item.append(os.path.exists(pdf_file_name))

        rows.append(flat_item)

    df = pd.DataFrame(data=rows, columns=columns)
    df.to_excel(outfile)


def get_bibtex(item):
    try:
        return item["google_scholar"]["bibtex"]
    except:
        pass
    op = "{"
    cp = "}"
    bibtex = list()
    # bibtex.append(f"""@{item["bibtex_type"]}{op}ms{item["id"]}""")
    bibtex.append(f"""@{op}openalex{item["id"]}""")

    authors = list()
    for au in item["authors"]:
        authors.append(au["name"])
    authors = " and ".join(authors)

    if item["publication_type"] == "journal-article":
        """
        Статья из журнала.
        Необходимые поля: +author, +title, +journal, +year
        Дополнительные поля: volume, number, pages, month, note, key
        """
        bibtex.append(f"""author = {op}{authors}{cp}""")
        bibtex.append(f"""title = {op}{item["title"]}{cp}""")
        bibtex.append(f"""journal = {op}{item["venue_full_name"]}{cp}""")
        bibtex.append(f"""year = {op}{item["year"]}{cp}""")

        if item["volume"]:
            bibtex.append(f"""volume = {op}{item["volume"]}{cp}""")
        if item["issue"]:
            bibtex.append(f"""number = {op}{item["issue"]}{cp}""")
        if item["page_first"]:
            bibtex.append(
                f"""pages = {op}{item["page_first"]}-{item["page_last"]}{cp}"""
            )

    elif item["publication_type"] in (
        "book",
        "monograph",
        "edited-book",
        "reference-book",
    ):
        """
        Определённое издание книги.
        Необходимые поля: +author/editor, +title, +publisher, +year
        Дополнительные поля: +volume, series, address, edition, month, note, key, +pages
        """
        bibtex.append(f"""author = {op}{authors}{cp}""")
        bibtex.append(f"""title = {op}{item["title"]}{cp}""")
        if item["publisher"]:
            bibtex.append(f"""publisher = {op}{item["publisher"]}{cp}""")
        bibtex.append(f"""year = {op}{item["year"]}{cp}""")
        if item["page_first"]:
            bibtex.append(
                f"""pages = {op}{item["page_first"]}-{item["page_last"]}{cp}"""
            )
        if item["volume"]:
            bibtex.append(f"""volume = {op}{item["volume"]}{cp}""")

    elif item["publication_type"] == "booklet":
        """
        Печатная работа, которая не содержит имя издателя или организатора
        (например, самиздат).
        Необходимые поля: +title
        Дополнительные поля: +author, howpublished, address, month, +year, note, key
        """
        bibtex.append(f"""author = {op}{authors}{cp}""")
        bibtex.append(f"""title = {op}{item["title"]}{cp}""")
        bibtex.append(f"""year = {op}{item["year"]}{cp}""")

    elif item["publication_type"] in ("proceedings-article",):
        #  'conference' or item["publication_type"] == 'inproceedings':
        """
        Синоним inproceedings, оставлено для совместимости с Scribe.
        Необходимые поля: +author, +title, +booktitle, +year
        Дополнительные поля: editor, +pages, organization, +publisher, address, month, note, key
        """
        bibtex.append(f"""author = {op}{authors}{cp}""")
        bibtex.append(f"""title = {op}{item["title"]}{cp}""")
        bibtex.append(f"""year = {op}{item["year"]}{cp}""")
        bibtex.append(f"""booktitle = {op}{item["venue_full_name"]}{cp}""")
        if item["page_first"]:
            bibtex.append(
                f"""pages = {op}{item["page_first"]}-{item["page_last"]}{cp}"""
            )
        if item["publisher"]:
            bibtex.append(f"""publisher = {op}{item["publisher"]}{cp}""")

    elif item["publication_type"] in (
        "book-section",
        "book-part",
        "book-chapter",
    ):
        # 'inbook':
        """
        Часть книги, возможно без названия. Может быть главой (частью, параграфом), либо диапазоном страниц.
        Необходимые поля: +author/editor, +title, +chapter/pages, +publisher, +year
        Дополнительные поля: +volume, series, address, edition, month, note, key
        """
        bibtex.append(f"""author = {op}{authors}{cp}""")
        bibtex.append(f"""title = {op}{item["title"]}{cp}""")
        bibtex.append(f"""year = {op}{item["year"]}{cp}""")
        if item["volume"]:
            bibtex.append(f"""volume = {op}{item["volume"]}{cp}""")
        if item["page_first"]:
            bibtex.append(
                f"""pages = {op}{item["page_first"]}-{item["page_last"]}{cp}"""
            )
        if item["publisher"]:
            bibtex.append(f"""publisher = {op}{item["publisher"]}{cp}""")

    elif item["publication_type"] == "incollection":
        """
        Часть книги, имеющая собственное название (например, статья в сборнике).
        Необходимые поля: +author, +title, +booktitle, +year
        Дополнительные поля: editor, +pages, organization, +publisher, address, month, note, key
        """
        bibtex.append(f"""author = {op}{authors}{cp}""")
        bibtex.append(f"""title = {op}{item["title"]}{cp}""")
        bibtex.append(f"""booktitle = {op}{item["venue_full_name"]}{cp}""")
        if item["publisher"]:
            bibtex.append(f"""publisher = {op}{item["publisher"]}{cp}""")
        if item["page_first"]:
            bibtex.append(
                f"""pages = {op}{item["page_first"]}-{item["page_last"]}{cp}"""
            )
        bibtex.append(f"""year = {op}{item["year"]}{cp}""")

    elif item["publication_type"] == "standard-series":
        """
        Техническая документация.
        Необходимые поля: +title
        Дополнительные поля: +author, +organization, address, edition, month, +year, note, key
        """
        bibtex.append(f"""author = {op}{authors}{cp}""")
        bibtex.append(f"""title = {op}{item["title"]}{cp}""")
        if item["publisher"]:
            bibtex.append(f"""organization = {op}{item["publisher"]}{cp}""")
        bibtex.append(f"""year = {op}{item["year"]}{cp}""")

    elif item["publication_type"] == "dissertation":
        """
         диссертация.
        Необходимые поля: +author, +title, +school, +year
        Дополнительные поля: address, month, note, key
        """
        bibtex.append(f"""author = {op}{authors}{cp}""")
        bibtex.append(f"""title = {op}{item["title"]}{cp}""")
        if item["publisher"]:
            bibtex.append(f"""school = {op}{item["publisher"]}{cp}""")
        bibtex.append(f"""year = {op}{item["year"]}{cp}""")

    elif item["publication_type"] in ("proceedings", "proceedings-series"):
        """
        Сборник трудов (тезисов) конференции.
        Необходимые поля: +title, +year
        Дополнительные поля: +editor, +publisher, organization, address, month, note, key
        """
        bibtex.append(f"""editor = {op}{authors}{cp}""")
        bibtex.append(f"""title = {op}{item["title"]}{cp}""")
        bibtex.append(f"""year = {op}{item["year"]}{cp}""")
        if item["publisher"]:
            bibtex.append(f"""publisher = {op}{item["publisher"]}{cp}""")

    elif item["publication_type"] == "report":
        """
        Отчёт, опубликованный организацией, обычно пронумерованный внутри серии.
        Необходимые поля: +author, +title, +institution, +year
        Дополнительные поля: type, number, address, month, note, key
        """
        bibtex.append(f"""author = {op}{authors}{cp}""")
        bibtex.append(f"""title = {op}{item["title"]}{cp}""")
        if item["publisher"]:
            bibtex.append(f"""institution = {op}{item["publisher"]}{cp}""")
        bibtex.append(f"""year = {op}{item["year"]}{cp}""")

    else:  # item["publication_type"] == "other":
        """
        Использовать, если другие типы не подходят.
        Необходимые поля: none
        Дополнительные поля: +author, +title, howpublished, month, +year, note, key
        """
        bibtex.append(f"""author = {op}{authors}{cp}""")
        bibtex.append(f"""title = {op}{item["title"]}{cp}""")
        bibtex.append(f"""year = {op}{item["year"]}{cp}""")

    bibtex = ",\n".join(bibtex)
    bibtex += f"""{cp}"""
    return bibtex


if __name__ == "__main__":
    t0 = time.time()
    fire.Fire(do_export)
    t1 = time.time()
    print("finished")
    print(
        (
            "time",
            t1 - t0,
        )
    )
    process = psutil.Process(os.getpid())
    print("used RAM(bytes)=", process.memory_info().rss)  # in bytes
