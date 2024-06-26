# encoding: UTF-8
import configparser
import json
import os.path
import re
import time

import fire
import jsonlines
import lib.nlp as nlp
import psutil
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer


def tokenizer(config=None, outfile=None, infile=None, outdictfile=None):
    t0 = time.time()
    # read configuration file
    conf = configparser.ConfigParser()
    conf.read_file(open(config))

    data_dir = conf.get("main", "data_dir")
    log_file_path = os.path.join(data_dir, conf.get("001_tokenizer", "log_file_name"))

    min_word_length = int(conf.get("001_tokenizer", "min_word_length"))

    def log(msg):
        s = json.dumps(msg)
        print(s)
        f = open(log_file_path, "a")
        f.write(s)
        f.write("\n")
        f.close()

    # NLP tools:
    custom_tokenizer = nlp.CustomTokenizer()
    # tokenizer.stemmer = SnowballStemmer("english")
    custom_tokenizer.stemmer = PorterStemmer()

    custom_tokenizer.valid_pos_tags = {
        "NNP": 1,
        "JJ": 1,
        "NN": 1,
        "NNS": 1,
        "JJS": 1,
        "JJR": 1,
        "NNPS": 1,
    }
    # tokenizer.valid_pos_tags = {'NNP':True, 'NN' :True, 'NNS':True, 'NNPS':True,
    #                'JJS':True, 'JJR':True, 'JJ' :True,
    #                'VB':True , 'VBP':True,
    #                'RB':True};
    custom_tokenizer.tester = re.compile("^[a-zA-Z]+$")
    custom_tokenizer.stop = set(stopwords.words("english"))

    # file names
    if infile and os.path.isfile(infile):
        file_path_input = infile
    else:
        file_path_input = f"{data_dir}/000_download_output.jsonl"
    log(("input", file_path_input))

    if outfile:
        file_path_output = outfile
    else:
        file_path_output = f"{data_dir}/001_tokenizer_output.jsonl"
    log(("output", file_path_output))

    if outdictfile:
        file_path_dict = outdictfile
    else:
        file_path_dict = f"{data_dir}/001_tokenizer_dict.csv"
    log(("dictfile", file_path_dict))

    # =====================================================
    # tokenizer loop
    with jsonlines.open(file_path_input) as reader:
        with jsonlines.open(file_path_output, mode="w") as writer:
            cnt = 0
            for item in reader:

                item["tokens"] = []
                if "topics" in item and item["topics"]:
                    item["tokens"].extend(
                        [
                            it["name"]
                            for it in item["topics"]
                            if len(it["name"]) >= min_word_length
                        ]
                    )

                item["tokens"].extend(
                    [
                        x
                        for x in custom_tokenizer.extend_tokens(
                            custom_tokenizer.get_tokens(
                                str(item["title"]) + ". " + str(item["abstract"])
                            )
                        )
                        if len(x) >= min_word_length
                    ]
                )

                cnt = cnt + 1
                if cnt % 100 == 0:
                    log((cnt, item["id"], item["year"], item["title"], item["tokens"]))

                writer.write(item)

    # /tokenizer loop
    # =====================================================
    with jsonlines.open(file_path_dict, mode="w") as writer:
        for tk in custom_tokenizer.word_dictionary:
            writer.write([tk, custom_tokenizer.word_dictionary[tk]])
    t1 = time.time()
    log("finished")
    log(
        (
            "time",
            t1 - t0,
        )
    )
    process = psutil.Process(os.getpid())
    log(
        (
            "used RAM(bytes)=",
            process.memory_info().rss,
        )
    )  # in bytes


if __name__ == "__main__":
    fire.Fire(tokenizer)
