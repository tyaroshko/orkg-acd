# import sys
import configparser
import csv
import json
import os
import re
import time
from os import listdir
from os.path import isfile, join

import fire
import jsonlines
import lib.ate as ate
import psutil


def do_get_terms(
    config=None, in_dir_dataset=None, out_dir_terms=None, stopwords=None, trace=0  #
):
    """

    :param config:
    :param in_dataset: input TXT file
    :param out_terms: output CSV file containing terms
    :param stopwords: text file containing stopwords, one word per row
    :param term_patterns: text file containing term patterns, one word per row
    :param min_term_words: number of words in one term
    :param min_term_length: minimal number of characters in the term
    :param trace: show detailed information about execution
    :return:
    """
    t0 = time.time()

    conf = configparser.ConfigParser()
    conf.read_file(open(config))

    data_dir = conf.get("main", "data_dir")
    log_file_name = "015_ate_get_terms.log"
    log_file_path = os.path.join(data_dir, log_file_name)

    def log(msg):
        s = json.dumps(msg)
        print(s)
        f = open(log_file_path, "a")
        f.write(s)
        f.write("\n")
        f.close()

    if not os.path.isdir(out_dir_terms):
        log(f"pdf dir {out_dir_terms} not found. Creating")
        os.mkdir(out_dir_terms)

    min_term_words = int(conf.get("ate", "min_term_words"))
    min_term_length = int(conf.get("ate", "min_term_length"))
    term_patterns = json.loads(conf.get("ate", "term_patterns"))
    trace = int(trace) == 1

    f_stopwords = open(stopwords, "r")
    stopwords = [r.strip() for r in f_stopwords.readlines() if len(r.strip()) > 0]
    f_stopwords.close()

    in_dataset_files = sorted(
        [f for f in listdir(in_dir_dataset) if f.lower().endswith(".txt")]
    )

    for in_dataset_file in in_dataset_files:
        t2 = time.time()
        in_dataset = join(in_dir_dataset, in_dataset_file)
        log(in_dataset)
        if not isfile(in_dataset):
            continue

        fp = open(in_dataset, "r")
        doc_txt = fp.read()
        fp.close()
        doc_txt = doc_txt.replace("\ufffd", "_")
        doc_txt = re.sub(r"et +al\.", "et al", doc_txt)
        doc_txt = re.split(r"[\r\n]", doc_txt)

        # log('len(text)=' + str( len(doc_txt) ) )

        term_extractor = ate.TermExtractor(
            stopwords=stopwords,
            term_patterns=term_patterns,
            min_term_words=min_term_words,
            min_term_length=min_term_length,
        )
        terms = term_extractor.extract_terms(doc_txt, trace=trace)
        log("len(terms)=" + str(len(terms)))
        if trace:
            # log terms[:10]
            log("Term extraction finished")

        c_values = term_extractor.c_values(terms, trace=trace)  # replace this line

        out_terms_file = join(out_dir_terms, "T" + in_dataset_file[1:])
        with jsonlines.open(out_terms_file, mode="w") as writer:
            for cv in c_values:
                writer.write(cv)
        t1 = time.time()
        log(
            (
                "time",
                t1 - t2,
            )
        )

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
    fire.Fire(do_get_terms)
