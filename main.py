import argparse
import json
import os
import requests
import spacy
import sys
import time

from bs4 import BeautifulSoup
from decouple import config
from LeIA import SentimentIntensityAnalyzer
from rich.console import Console
from rich.table import Table

api_url = "https://anime-reactions.uzairashraf.dev/api"


def get_mastodon_local_timeline_toots():
    MASTODON_ACCESS_TOKEN = config("MASTODON_ACCESS_TOKEN", default=None)
    MASTODON_INSTANCE_URL = config("MASTODON_INSTANCE_URL", default=None)
    if not MASTODON_ACCESS_TOKEN or not MASTODON_INSTANCE_URL:
        print(
            "Configure both MASTODON_ACCESS_TOKEN and MASTODON_INSTANCE_URL env variables!"
        )
        sys.exit(1)
    # if the toots.json file is younger than 5min, don't make a request
    if os.path.exists("toots.json"):
        if time.time() - os.path.getmtime("toots.json") < 300:
            with open("toots.json", "r", encoding="utf-8") as f:
                return json.load(f)

    req_url = f"{MASTODON_INSTANCE_URL}/api/v1/timelines/public?local=true"
    req = requests.get(
        req_url,
        headers={
            "Authorization": f"Bearer {MASTODON_ACCESS_TOKEN}",
        },
    )
    if not req.ok:
        print(f"Request failed! {req.content}")
        sys.exit(1)
    with open("toots.json", "w", encoding="utf-8") as f:
        json.dump(req.json(), f, ensure_ascii=False, indent=4)
    return req.json()


def list_categories():
    req_url = f"{api_url}/categories"
    req = requests.get(req_url)
    if not req.ok:
        print("Request failed!")
        sys.exit(1)
    return req.json()


def get_random_reaction_from_category(category):
    req_url = f"{api_url}/reactions/random"
    get_params = {"category": category}
    req = requests.get(req_url, params=get_params)
    if not req.ok:
        print("Request failed!")
        sys.exit(1)
    return req.json()


def get_leia_sentiment(message):
    s = SentimentIntensityAnalyzer()
    # see https://github.com/cjhutto/vaderSentiment#about-the-scoring for more info
    polarity_scores = s.polarity_scores(message)
    print(polarity_scores)
    if polarity_scores["compound"] >= 0.05:
        return "Positive"
    if polarity_scores["compound"] <= -0.05:
        return "Negative"
    return "Neutral"


def get_sentiment_subset(sentiment):
    emotions_lemmas = json.load(open("emotion_lemmas.json", "r", encoding="utf-8"))
    if sentiment == "Positive":
        lemmas_subset = {"yes", "happy", "surprised", "smug"}
    elif sentiment == "Negative":
        lemmas_subset = {"angry", "sad", "embarrassed", "no"}
    else:
        lemmas_subset = {"nervous", "confused", "thinking"}

    sentiment_subset = {
        k: emotions_lemmas[k] for k in emotions_lemmas.keys() & lemmas_subset
    }
    return sentiment_subset


def get_emotion_from_message(message, emotions_lemmas):
    nlp = spacy.load("pt_core_news_sm")

    # parse the message with spaCy
    doc = nlp(message)

    emotion_points = {}

    table = Table(title="SpaCy Analysis")

    table.add_column("Text")
    table.add_column("Lemma")
    table.add_column("POS")
    table.add_column("Emotion")

    # iterate through the words in the message
    for word in doc:
        if word.is_stop or word.is_punct:
            continue
        row = [word.text, word.lemma_, word.pos_]
        # iterate through available emotions lemmasin the mapping
        for emotion, lemmas in emotions_lemmas.items():
            # iterate through the words in the key
            if word.lemma_ in lemmas:
                # if the word lemma is in the emotion's list, increase the emotion's points
                emotion_points[emotion] = emotion_points.get(emotion, 0) + 1
                row.append(emotion)
        if len(row) == 3:
            row.append("None")
        table.add_row(*row)

    console = Console()
    console.print(table)

    if len(emotion_points) == 0:
        return None
    # return the emotion with the highest points
    return max(emotion_points, key=emotion_points.get)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--category", required=False, help="Specify your reaction category!"
    )
    parser.add_argument(
        "-lc",
        "--list-categories",
        action="store_true",
        required=False,
        help="Lists available categories",
    )
    parser.add_argument(
        "-m",
        "--message",
        required=False,
        help="Specify a message to react to!",
    )
    parser.add_argument(
        "-s",
        "--spacy",
        required=False,
        help="Specify a message to parse with spaCy!",
    )
    parser.add_argument(
        "-cel",
        "--create-emotion-lemmas",
        action="store_true",
        required=False,
        help="Creates a file containing lemmas for each emotion",
    )
    parser.add_argument("-l", "--leia", required=False, help="LeIA sentiment analysis")
    parser.add_argument("-t", "--toots", action="store_true", required=False)

    args = parser.parse_args()

    if args.category:
        reaction = get_random_reaction_from_category(args.category)
        print(reaction["reaction"])
        sys.exit(0)

    if args.list_categories:
        categories = list_categories()
        print(
            f"Available categories: {''.join([f'{category}, ' for category in categories])[:-2]}"
        )
        sys.exit(0)

    if args.message:
        message = args.message
        sentiment = get_leia_sentiment(message)
        emotions_lemmas = get_sentiment_subset(sentiment)
        emotion = get_emotion_from_message(message, emotions_lemmas)

        if emotion is None:
            print("No emotion detected!")
            sys.exit(1)
        print(f"Detected emotion: {emotion}")
        reaction = get_random_reaction_from_category(emotion)
        print(reaction["reaction"])
        sys.exit(0)

    if args.create_emotion_lemmas:
        emotions_mapping = json.load(open("emotions_dir.json", "r"))
        nlp = spacy.load("pt_core_news_sm")
        emotion_lemmas = {}
        for key, words in emotions_mapping.items():
            emotion_lemmas[key] = []
            for word in words:
                doc = nlp(word)
                for token in doc:
                    if token.is_stop:
                        continue
                    if token.lemma_ not in emotion_lemmas[key]:
                        emotion_lemmas[key].append(token.lemma_)
        with open("emotion_lemmas.json", "w", encoding="utf-8") as f:
            json.dump(emotion_lemmas, f, ensure_ascii=False, indent=4)
        sys.exit(0)

    if args.spacy:
        table = Table(title="SpaCy Analysis")

        table.add_column("Text")
        table.add_column("Lemma")
        table.add_column("POS")
        table.add_column("Tag")
        table.add_column("Dependency")
        table.add_column("Shape")
        table.add_column("Is Alpha")
        table.add_column("Is Stop")

        nlp = spacy.load("pt_core_news_sm")
        doc = nlp(args.spacy)
        print(doc.text)
        for token in doc:
            table.add_row(
                token.text,
                token.lemma_,
                token.pos_,
                token.tag_,
                token.dep_,
                token.shape_,
                str(token.is_alpha),
                str(token.is_stop),
            )
        console = Console()
        console.print(table)
        sys.exit(0)

    if args.leia:
        print(get_leia_sentiment(args.leia))
        sys.exit(0)

    if args.toots:
        toots = get_mastodon_local_timeline_toots()
        if toots is None:
            print("No toots found!")
            sys.exit(1)
        for toot in toots:
            toot_soup = BeautifulSoup(toot["content"], "html.parser")
            toot_text = toot_soup.get_text()
            toot_sentiment = get_leia_sentiment(toot_text)
            print(toot_sentiment + "---" + toot_text + "\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
