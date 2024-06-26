# import sys
import configparser
import json
import os.path
import time

import fire
import jsonlines
import psutil
from lib.msacademic import Api


def do_extension(config=None, outfile=None, initems=None):
    t0 = time.time()
    # read configuration file
    conf = configparser.ConfigParser()
    conf.read_file(open(config))

    data_dir = conf.get("main", "data_dir")
    log_file_name = "009_extend_items.log"
    log_file_path = os.path.join(data_dir, log_file_name)

    def log(msg):
        s = json.dumps(msg)
        print(s)
        f = open(log_file_path, "a")
        f.write(s)
        f.write("\n")
        f.close()

    rest_endpoint = json.loads(conf.get("msacademic", "restEndpoint"))
    subscription_key = conf.get("msacademic", "subscriptionKey")
    include_topics = json.loads(conf.get("msacademic", "msAcademicIncludeTopicsIds"))

    api = Api(subscription_key, rest_endpoint, include_topics)
    api.FIELDS.extend(
        [
            # > B. Type. One of the following values to be chosen based on the type of the document:
            # > J-journal paper; C-conference or workshop paper; P-preprint; D-thesis; B-book chapter.
            # > OK. Let us stick to this typization: UN, JA, PT, CP, BC, BO, BR, DA, RE.
            "BT",  # BibTex document type ('a':Journal article, 'b':Book, 'c':Book chapter, 'p':Conference paper)
            "Pt",  # Publication type (0:Unknown, 1:Journal article, 2:Patent, 3:Conference paper, 4:Book chapter, 5:Book, 6:Book reference entry, 7:Dataset, 8:Repository
            #
            # > C. Venue (Journal / Series / Conference). The value is:
            # > (i) the name of the journal if the doc is a journal paper (J);
            # > the name of the book series (e.g. LNCS)  if the doc is a book chapter (B);
            # > conference name + book series (e.g. ISWC 2020; LNCS)
            # > if the doc is a conference or workshop paper (C)
            "VFN",  # Full name of the Journal or Conference venue    String    None
            "VSN",  # Short name of the Journal or Conference venue    String    None
            # 'J.JId',  # Journal ID    Int64    Equals
            "J.JN",  # Journal name    String    Equals, StartsWith
            "BV",  # BibTex venue name    String    None
            # 'C.CId',  # Conference series ID    Int64    Equals
            "C.CN",  # Conference series name    String    Equals, StartsWith
            #
            # > D. Publisher. The name of the Publisher (e.g. Springer-Nature, Elsevier, ACM, etc.)
            "PB",  # Publisher
            #
            # > E. Volume No (if available). This is the journal or series volume number.
            # > It is not available for some preprints or theses.
            "V",  # Publication volume
            #
            # > F. Issue No (if available). This is available only for journals.
            "I",  # Publication issue
            #
            # > G. Pages (if available). For J, B, C, these are the starting-ending pages
            # > within the volume. For electronic publications these might be paper
            # > No and No of pages. For manuscripts, like theses – the total no of pages.
            "FP",  # First page of paper in publication
            "LP",  # Last page of paper in publication
            #
            # > DOI. This is the DOI of the document.
            # IMPORTANT: The DOI is normalized to uppercase letters, so if querying the field
            # via evaluate/histogram ensure that the DOI value is using all uppercase letters
            "DOI",  # Digital Object Identifier
            #
            # > DOI Link. Is the URL, containing the DOI,
            # > and pointing to the original publication at the Publisher’s resource.
            "S",  # List of source URLs of the paper, sorted by relevance ?
            #
            # > MSF ID. This is the identifier of the doc in the MS Research repository.
            # Id 	Entity ID
            #
            # > Paper Title. This is the title of the document, including the sub-title, if any.
            "DN",  # Original paper title
            # > Authors. This is the semicolon-separated list of the authors of the document.
            # > Each name to be given in the format provided by MSR.
            # 'AA.DAuN',  # Original author name
            # 'AA.AuN',   # Normalized author name
            #
            # > Affiliations. This is the list of the affiliations of the document authors,
            # > semicolon –separated, as provided by MSR. The order should correspond to
            # > the order of the author names.
            # 'AA.DAfN',  # Original affiliation name
            # 'AA.AfN',  # Author affiliation name
            # **********************************************
            # > Complete Citation. This is the citation of the document as provided by MSR (APA format).
            #
            # > Abstract. This is the abstract of the document (if available) as provided by MSR
            # +
            # > P. Q. R. Category. These will be filled out in the Catalogue Partitioning Task.
            # Always will be empty at this stage
            #
            # > Key words / phrases. As provided by MSR – semicolon-separated.
            # +
            #
            # Citations (in citation network). Generated by the Snowball Sampling software.
            #
            # > Citations (GS). The citation count for the document acquired from Google Scholar.
            # > Documents to be searched by title, first author, venue, and publication year.
            # > For example, for the second entry in Example - catalogue.xlsx the Google Scholar
            # > query is: (allintitle: Data Cube: A Relational Aggregation Operator Generalizing
            # > Group-By, Cross-Tab, and Sub-Totals author:"J Gray" source:"Data Mining and
            # > Knowledge Discovery"). The Advanced search form has been filled out as follows:
            # >
            # >
            # > The result of this query is:
            # >
            # > The link for document download is available in this result.
            # > In such cases, the link should be saved in Column Y (Full text download URL).
            # >
            # > Citations per year (GS). This is the citation frequency we need for document ordering.
            # > The formula is: Citation-Count-(U) / (<current year> - Publication-Year-(A)+1).
            #
            # > Document file name (to be generated). This is the file name for the full
            # > text file of the document that is downloaded and stored locally
            # > for processing. The rule for generating the name is as follows:
            # >
            # > <Year>+”-“+<Type>+”-“+<Volume>+”(“+<Issue>+”)-(“+<Pages>+”)-“+(substring of <DOI> after ‘/’; all the <DOI> string if there is no ‘/’ in it)
            # > Year: Publication year, Column A
            # > Type: Publication type, Column B
            # > Volume: Volume No, Column E, 1 if not available
            # > Issue: Issue No, Column F, 1 if not available
            # > Pages: Column G
            # > DOI: Column H
            # todo
            #
            # > MSR Entry (URL). The URL for the document description at MSR.
            # +
            # > Full text download URL. The URL for downloading the full text of the doc.
            # S 	List of source URLs of the paper, sorted by relevance
            # Important
            #     Source attributes cannot be directly requested as a return attribute. If you need an individual attribute you must request the top level "S" attribute, i.e. to get S.U request attributes=S
            #     Source
            #     Name 	Description 	Type 	Operations
            #     Ty 	Source URL type (1:HTML, 2:Text, 3:PDF, 4:DOC, 5:PPT, 6:XLS, 7:PS) 	String 	None
            #     U 	Source URL 	String 	None
        ]
    )

    data_dir = conf.get("main", "data_dir")
    # =====================================================
    # load downloaded items
    file_path_items = f"{data_dir}/008_search_path_count_output.jsonl"
    if initems and os.path.isfile(initems):
        file_path_items = initems
    elif os.path.isfile(file_path_items):
        pass
    else:
        log("snowball output not found")
        return
    log(("infile", file_path_items))
    with jsonlines.open(file_path_items) as reader:
        items = {str(row["id"]): row for row in reader}
    # /load downloaded items
    # =====================================================

    # =====================================================
    # place to store extended item
    if outfile:
        file_path_output = outfile
    else:
        file_path_output = f"{data_dir}/009_extend_items_output.jsonl"
    log(("output", file_path_output))
    # =====================================================

    batch_size = int(conf.get("main", "batch_size"))

    def get_chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i : i + n]

    batches = list(get_chunks(list(items.keys()), batch_size))
    for batch in batches:
        for extension in api.load_by_ids(batch):
            items[str(extension["id"])].update(extension)

    with jsonlines.open(file_path_output, mode="w") as writer:
        for item_id in items:
            item = items[item_id]
            log(("id", item["id"], "year", item["year"], "title", item["title"]))
            writer.write(item)

    t1 = time.time()
    log("finished")
    log(
        (
            "time",
            t1 - t0,
        )
    )
    process = psutil.Process(os.getpid())
    log(("used RAM(bytes)=", process.memory_info().rss))  # in bytes


if __name__ == "__main__":
    fire.Fire(do_extension)
