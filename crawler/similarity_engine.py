import couchdb
from elasticsearch import Elasticsearch
import re
import json
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime
from nltk.metrics import edit_distance
from sentence_transformers import SentenceTransformer, util
from tqdm import tqdm
from dotenv import load_dotenv
import os


#configuration vars
load_dotenv('../.env')

couchdb_ip = os.getenv("COUCHDB_IP")
couchdb_port = os.getenv("COUCHDB_PORT")
couchdb_result_database = os.getenv("COUCHDB_RESULT_DATABASE")
couchdb_username = os.getenv("COUCHDB_USERNAME")
couchdb_password = os.getenv("COUCHDB_PASSWORD")
elastic_uri = os.getenv("ELASTIC_URI")
elastic_username = os.getenv("ELASTIC_USERNAME")
elastic_password = os.getenv("ELASTIC_PASSWORD")
elastic_index_name = os.getenv("ELASTIC_INDEX_NAME")


nltk.download('punkt')
nltk.download('stopwords')

def preprocess(text):
    stop_words = set(stopwords.words('english'))
    words = nltk.word_tokenize(text)
    words = [word.lower() for word in words if word.isalnum() and word.lower() not in stop_words]
    return words


# Jaccard Similarity
def jaccard_similarity(str1, str2):
    set1 = set(preprocess(str1))
    set2 = set(preprocess(str2))
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union

# Cosine Similarity
def cosine_similarity(str1, str2):
    vectorizer = TfidfVectorizer(tokenizer=preprocess)
    tfidf_matrix = vectorizer.fit_transform([str1, str2])
    cosine_sim = (tfidf_matrix * tfidf_matrix.T).toarray()[0, 1]
    return cosine_sim


# Levenshtein Similarity
def levenshtein_similarity(str1, str2):
    dis = edit_distance(str1, str2)
    max_length = max(len(str1), len(str2))
    s = 1 - (dis / max_length)
    return s

# Using pretrained Paraphrase-MiniLM-L6-v2 pretrained model
def bert_text_similarity(text1, text2):
    model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

    # Sentences encodeing for their embeddings
    embeddings1 = model.encode(text1, convert_to_tensor=True)
    embeddings2 = model.encode(text2, convert_to_tensor=True)

    # Compute the cosine similarity between embeddings
    cosine_similarity = util.pytorch_cos_sim(embeddings1, embeddings2)[0].item()

    return cosine_similarity


# This part of code is 
couchdb_connection_string = f"http://{couchdb_username}:{couchdb_password}@{couchdb_ip}:{couchdb_port}"

server = couchdb.Server(couchdb_connection_string)
res_db_name = couchdb_result_database
if res_db_name in server:
    db = server[res_db_name]
else:
    db = server.create(res_db_name)

es = Elasticsearch(
    [elastic_uri],
    basic_auth=(elastic_username, elastic_password)
)

domain_name_pattern = r"https?://(?:\w+\.)?([\w.-]+\.[a-zA-Z]{2,})"

# Set up the intervals to fetch texts from CouchDB
to_analyze = [
    { "gte": "2023-11-18T00:00:00", "lte": "2023-11-19T00:00:00" },
    { "gte": "2023-11-19T00:00:00", "lte": "2023-11-20T00:00:00" },
    { "gte": "2023-11-20T00:00:00", "lte": "2023-11-21T00:00:00" },
    { "gte": "2023-11-21T00:00:00", "lte": "2023-11-22T00:00:00" },
    { "gte": "2023-11-22T00:00:00", "lte": "2023-11-23T00:00:00" },
]

for x in range(len(to_analyze)):
    print(x)
    query = {
        "bool": {
        "must": [
            { "range": { "doc.date": to_analyze[x] } },
            { "exists": { "field": "doc.content" } }
        ]
        }
    }

    res = es.search(index=elastic_index_name, query=query, size=10000)

    # Extract documents from the response
    docs = [doc for doc in res['hits']['hits']]
    results = []

    with tqdm(total=len(docs)) as pbar:
        for i, doc in enumerate(docs):
            #print("{} / {}".format(i, len(docs)), end="\r")
            #print(f'\x1b[32m{i}/{len(docs)}\x1b[0m')
            pbar.update(1)
            mlt_query = {
                "more_like_this": {
                    "fields": ["doc.content"],
                    "like": [
                        {
                            "_index": doc["_index"],
                            "_id": doc["_id"]
                        }
                    ],
                    "minimum_should_match": "60%",
                    "min_term_freq": 1,
                    "max_query_terms": 1000,
                    "analyzer": "english"
                    # "term_statistics": True
                }
            }

            search_results = es.search(index=elastic_index_name, query=mlt_query, size=10000)

            if not 'doc' in doc["_source"]:
                continue
            match1 = re.search(domain_name_pattern, doc["_source"]["doc"]["url"])
            domain_doc = match1.group(1)

            doc['domain'] = domain_doc
            results.append(
                {'source': {"id": doc["_id"], "url": doc["_source"]["doc"]["url"], "domain": domain_doc,
                            "published_on": doc["_source"]["doc"]['date']}, 'related': []})
            for ix, hit in enumerate(search_results["hits"]["hits"]):
                # print(f'\x1b[31m{ix}/{len(search_results["hits"]["hits"])}\x1b[0m')
                match2 = re.search(domain_name_pattern, hit["_source"]["doc"]["url"])
                domain_hit = match2.group(1)
                if domain_doc == domain_hit:
                    continue

                if any(hit["_source"]["doc"]["url"] == d['url'] for d in results[i]['related']):
                    continue

                cos_similarity = cosine_similarity(doc["_source"]["doc"]["content"], hit["_source"]["doc"]["content"])
                if cos_similarity > 0.5:
                    # print(f'cos {cos_similarity}')
                    jac_similarity = jaccard_similarity(doc["_source"]["doc"]["content"], hit["_source"]["doc"]["content"])
                    # print(f'jac {jac_similarity}')
                    #levenshtein_sim = levenshtein_similarity(doc["_source"]["doc"]["content"], hit["_source"]["doc"]["content"])
                    # print(f'lev {levenshtein_sim}')
                    bert_cos_similarity = bert_text_similarity(doc["_source"]["doc"]["content"], hit["_source"]["doc"]["content"])
                    # print(f'bert {bert_cos_similarity}')

                    if jac_similarity > 0.5 and bert_cos_similarity > 0.5:
                        r = {"id": hit["_id"], "url": hit["_source"]["doc"]["url"], "domain": domain_hit,
                            "published_on": hit["_source"]["doc"]['date'],
                            "cosine_similarity_score": cos_similarity,
                            "jaccard_similarity_score": jac_similarity,
                            #"levenshtein_similarity_score": levenshtein_sim,
                            "bert_cos_similarity_score": bert_cos_similarity
                            }
                        results[i]['related'].append(r)
    results = [result for result in results if len(result['related']) > 0]
    response = {"date": datetime.now().isoformat(), "body": results}

    x = json.dumps(response)
    print(x)
    db.save(response)

# with open('json_data2.json', 'w', encoding='utf-8') as outfile:
#     json.dump(response, outfile, ensure_ascii=False)
