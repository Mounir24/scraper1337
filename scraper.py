#!/usr/bin/python

# IMPORT THE REQUIRED MODULES
from bs4 import BeautifulSoup
import requests
from colorama import Fore
import optparse
import pymongo
import certifi


# CONFIG OBJECT
CONFIG_OPTIONS = {
    "DB_CONNECTION": "mongodb://public:passforpub@cluster0-shard-00-00.3a89u.mongodb.net:27017,cluster0-shard-00-01.3a89u.mongodb.net:27017,cluster0-shard-00-02.3a89u.mongodb.net:27017/SCRAPER?ssl=true&replicaSet=atlas-5d234p-shard-0&authSource=admin&retryWrites=true&w=majority",
    "PROXIES": {
        'http': 'http://188.65.237.46:49733',
        'http': 'http://85.25.99.106:5566',
        'http': 'http://171.5.133.207:8080'
    }
}

# START DB CONNECTION


def DB_CONNECT(DB_URL):
    try:
        # DB CONNECTION STRING
        CONNECTION_STR = DB_URL
        # INITIATE THE MONGO CLIENT INSTANCE
        CLIENT = pymongo.MongoClient(
            CONNECTION_STR, serverSelectionTimeoutMS=5000, tlsCAFile=certifi.where())
        return CLIENT
    except:
        print(f'FAILED TO CONNECT TO DB SERVER :(')
        exit(0)


# SAVE SCRAPED DATA FUNCTION
def SAVE_SCRAPED_DATA(CONTENT):
    # CHECK IF THE PROVIDED CONTENT DATA NOT EMPTY
    if (CONTENT == None) or (CONTENT == ''):
        print('[!!] NOTE: EMPTY CONTENT ! YOU MAY LOSE YOUR EXCTRACTED DATA !!')
        return

    try:
        # EXECUTE THE DB_CONNECTION FUNCTION
        CLIENT = DB_CONNECT(CONFIG_OPTIONS['DB_CONNECTION'])
        # GET THE DB NAME
        DB = CLIENT.SCRAPER
        # GET: TITLE & BODY CONTENT
        TITLE = CONTENT[0]
        BODY_CONTENT = CONTENT[1]

        # CERATE DICTIONARY OBJECT
        ARTICLE_OBJ = {
            "title": TITLE.strip('\n\t'),
            "body": BODY_CONTENT.strip('\n\t')
        }

        # CREATE A COLLECTION OR SWITCH TO EXISTING COLLECTION IN DB
        COLLECTION = DB.Articles
        # INSERT A NEW SCRAPED ARTICLE CONTENT TO COLLECTION ===> Articles
        SAVED_ARTICLE = COLLECTION.insert_one(ARTICLE_OBJ)
        # PRINT THE SAVED  RESULT
        print(f'ARTICLE CONTENT HAS BEEN SAVED: {SAVED_ARTICLE}')

        # SHOW THE COLLECTION DATA
        """CURSOR = COLLECTION.find()
        for RECORD in CURSOR:
            print(RECORD)
        """
    except:
        print(f'[!!] FAILE TO SAVE THE ARTICLE CONTENT :(')


def WEB_SCRAPER(URL, DOM_ELE):
    # SET THE HEADER FOR RESUEST
    REQ_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9"
    }
    try:
        # FLY A REQUEST TO THE TARGET URL
        URL_PAGE = requests.get(URL, headers=REQ_HEADERS)
        # CHECK HTTP RESPONSE STATUS CODE
        if URL_PAGE.status_code == 200:
            PAGE_CONTENT = BeautifulSoup(URL_PAGE.text, 'html.parser')
            # SEARCH FOR A DOM ELEMENT
            BODY_CONTAINER = PAGE_CONTENT.find('body')

            # GET THE ARTICLE TITLE
            ARTICLE_TITLE = PAGE_CONTENT.find('title')

            # GET ALL TITLES WITH META TAG --> H1
            #CONTENT = BODY_CONTAINER.find('body')
            # CHECK IF THE PROVIED ARGUMENT NONE/EMPTY
            if DOM_ELE == None or DOM_ELE[0] == 'body':
                # GATHER BODY DOM ELEMENT ONLY
                # SAVE THE GATHERED DOM ELEMENT TO DB
                #SCHEMA: {source: url, element: dom_element, title: title}
                return [ARTICLE_TITLE.text, BODY_CONTAINER.text]
            else:
                TAGS_CONTENT = None
                for ELEMENT in DOM_ELE:
                    TAGS_CONTENT = BODY_CONTAINER.find_all(ELEMENT)

                # STRUCTUR THE HTML TAGS CONTENT
                if len(TAGS_CONTENT) > 0:
                    for ELEMENT_CONTENT in TAGS_CONTENT:
                        # SAVE THE GATHERED DOM ELEMENT TO DB
                        #SCHEMA: {source: url, element: dom_element, title: title}
                        return [ARTICLE_TITLE.text.strip('\n'), ELEMENT_CONTENT.text.strip('\n')]

        else:
            print(f'URL TARGET: {URL} - RESPONSE: {URL_PAGE.status_code}')
    except requests.exceptions.MissingSchema:
        print(
            f'{Fore.LIGHTYELLOW_EX}Invalid URL {URL}: No schema supplied. Perhaps you meant http|https://{URL}?')
        exit(0)


def main():
    parser = optparse.OptionParser(f'USAGE PROGRAM: \n\t -U <TARGET URL > ')
    parser.add_option('-U', dest="URL_TARGET", type="string",
                      help="PROVIDE TARGET URL (ex: https://www.example.com)")
    parser.add_option('--elements', dest="ELEMENTS", type="string",
                      help="PROVIDE AN DOM ELEMENT TAGS LIKE: (H1, P, MAIN, SECTION, FOOTER, H3, H3), separated by comma.")

    # GET ARGS VARIABLES
    (options, args) = parser.parse_args()
    # CHECK IF THE PROVIED -- ELEMENTS ARG EMPTY
    if options.ELEMENTS == None:
        print(
            f'[!!] DOM ELEMENTS NOT PROVIDED ! (IMPORTANT)')
        print(parser.usage)
        exit(0)
        #WEB_SCRAPER(options.URL_TARGET, DOM_ELE=['body'])

    # CHECK IF THE GIVEN ARGS ARE EMPTY VALUES
    if (options.URL_TARGET == None) or (options.URL_TARGET == ''):
        print(f'{Fore.LIGHTBLUE_EX}{parser.usage}')
        exit(0)

    else:
        # START THE SCRAPING FUNCTION
        print(f'======= WEB SCRAPER STARTED =======')
        DOM_ELE_ARR = options.ELEMENTS.split(',')
        DOM_ELE_ARR = [TAG.lower() for TAG in DOM_ELE_ARR]

        if len(DOM_ELE_ARR) > 0:
            ARTICLE_CONTENT = WEB_SCRAPER(
                options.URL_TARGET, DOM_ELE=DOM_ELE_ARR)
            # SAVE THE THE EXCTRACTED DATA TO DB COLLECTION
            SAVE_SCRAPED_DATA(ARTICLE_CONTENT)
        else:
            print(
                f'[!] DOM ELEMENTS NOT SPECIFIED ! DEFAULT: WHOLE BODY DOM ELEMENT WILL BE GATHERD')
            ARTICLE_CONTENT = WEB_SCRAPER(options.URL_TARGET, DOM_ELE=None)
            # SAVE THE THE EXCTRACTED DATA TO DB COLLECTION
            SAVE_SCRAPED_DATA(ARTICLE_CONTENT)


# EXECUTE GLOBAL MAIN FUNCTION
if __name__ == '__main__':
    main()
