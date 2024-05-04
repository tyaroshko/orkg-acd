# import sys
import configparser
import json
import os.path
import random
import sys
import time
import traceback

import fire
import jsonlines
import psutil
import scholarly
from scholarly import ProxyGenerator

YOUR_SCRAPER_API_KEY = "0a149bb950244d639f5f81e4a89ba5fe"


def get_optional(
    path,
    tree,
    default_value=None,
):
    """
    Extract branch from tree using path
    """
    if tree is None:
        return default_value
    res = tree
    for p in path:
        try:
            res = res[p]
        except (TypeError, IndexError, KeyError):
            return default_value
    if res is None:
        return default_value
    return res


def do_extension(
    config=None,
    outfile=None,
    initems=None,
    searchauthor="1",
    searchtitle="1",
    searchvenue="0",
):
    t0 = time.time()

    # read configuration file
    conf = configparser.ConfigParser()
    conf.read_file(open(config))

    save_period = int(conf.get("main", "save_period"))

    data_dir = conf.get("main", "data_dir")
    log_file_path = os.path.join(
        data_dir, conf.get("009_extend_items_google_scholar", "log_file_name")
    )

    def log(msg):
        s = json.dumps(msg)
        print(s)
        f = open(log_file_path, "a")
        f.write(s)
        f.write("\n")
        f.close()

    # =====================================================
    # place to store extended item
    if outfile:
        file_path_output = outfile
    else:
        file_path_output = f"{data_dir}/009_extend_items_google_scholar.jsonl"
    log(("output", file_path_output))
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
        log("input file not found")
        return
    log(("infile", file_path_items))
    with jsonlines.open(file_path_items) as reader:
        items = {str(row["id"]): row for row in reader}
    # /load downloaded items
    # =====================================================

    # place here Google Scholar calls to extract citation index
    # ! maybe proxy is needed
    # proxy = conf.get('009_extend_items_google_scholar', 'proxy')
    # if proxy and len(proxy) > 0:
    #     pg = scholarly.ProxyGenerator()
    #     http = proxy if 'http://' in proxy else None
    #     https = proxy if 'https://' in proxy else None
    #     pg.SingleProxy(http=http, https=https)
    #     scholarly.scholarly.use_proxy(pg)
    # else:
    #     pg = scholarly.ProxyGenerator()
    #     pg.FreeProxies()
    #     scholarly.scholarly.use_proxy(pg)
    pg = scholarly.ProxyGenerator()
    success = pg.ScraperAPI(YOUR_SCRAPER_API_KEY)
    # import requests
    # r = requests.get("http://api.scraperapi.com/account", params={'api_key': YOUR_SCRAPER_API_KEY}).json()

    # r["requestLimit"] = int(r["requestLimit"])
    # print("requestLimit", r["requestLimit"])
    # print("requestCount", r["requestCount"])
    if not success:
        pg = scholarly.ProxyGenerator()
        pg.FreeProxies()
        scholarly.scholarly.use_proxy(pg)
    scholarly.scholarly.use_proxy(pg)

    scholarly.scholarly.set_retries(1)

    n_errors = 0
    cnt = 0
    random.seed()

    pubs = []
    for item_id in items:
        cnt += 1
        log(("extending", "cnt", cnt, "item_id", item_id))

        if "google_scholar" in items[item_id]:
            log(
                (
                    "skip",
                    "item_id",
                    item_id,
                )
            )
            continue

        # if random.random() > 1.0:
        #     log(('dropout', 'item_id', item_id, ))
        #     continue

        google_search_string = list()
        if searchtitle == "1":
            try:
                item_title = items[item_id]["title"]
                google_search_string.append(f"""allintitle: {item_title}""")
            except:
                pass

        if searchauthor == "1":
            try:
                item_author = items[item_id]["authors"][0]["name"]
                google_search_string.append(f'''author:"{item_author}"''')
            except:
                pass

        if searchvenue == "1":
            try:
                item_venue = items[item_id]["venue_full_name"]
                google_search_string.append(f'''source:"{item_venue}"''')
            except:
                pass

        if len(google_search_string) > 0:
            google_search_string = " ".join(google_search_string)
            log(
                (
                    "searching",
                    "google_search_string",
                    google_search_string,
                )
            )
            try:
                search_query = scholarly.scholarly.search_pubs(google_search_string)
                pub = next(search_query, None)
                # print(pub)
            except:
                n_errors += 1
                ex = sys.exc_info()
                log(("ERROR", str(ex[0]), str(ex[1]), str(ex[2])))
                traceback.print_exc(file=sys.stdout)
                pub = None
                if n_errors > 10:
                    __save_items(file_path_output, items)
                    break

            if pub:
                pubs.append(pub)
                # print(pubs)
                # items[item_id]["google_scholar"] = (get_optional(["bib"], pub, {}),)
                items[item_id]["google_scholar"] = get_optional(["bib"], pub, {})
                # print(items[item_id]["google_scholar"])
                items[item_id]["google_scholar"]["pub_url"] = get_optional(
                    ["pub_url"], pub, ""
                )
                items[item_id]["google_scholar"]["eprint_url"] = get_optional(
                    ["eprint_url"], pub, ""
                )
                items[item_id]["google_scholar"] = (items[item_id]["google_scholar"],)

                log(items[item_id]["google_scholar"])
                # log(items[item_id]["google_scholar"]["pub_url"])
                # log(items[item_id]["google_scholar"]["eprint_url"])
                n_errors = 0
            time.sleep((30 - 5) * random.random() + 5)  # from 5 to 30 seconds
        else:
            log(("ERROR", "message", "google_search_string is empty"))

        if cnt % save_period == 0:
            __save_items(file_path_output, items)

    __save_items(file_path_output, items)

    for item_id in items:
        item = items[item_id]

        log(("id", item["id"], "year", item["year"], "title", item["title"]))

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


def __save_items(file_path_output, items):
    print(("__save_items", "file_path_output", file_path_output))
    with jsonlines.open(file_path_output, mode="w") as writer:
        for item_id in items:
            item = items[item_id]
            writer.write(item)


if __name__ == "__main__":
    fire.Fire(do_extension)
