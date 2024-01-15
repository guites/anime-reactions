import argparse
import json
import os
import requests
import sys
import time

from bs4 import BeautifulSoup
from decouple import config
from LeIA import SentimentIntensityAnalyzer


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


def get_leia_sentiment(message):
    s = SentimentIntensityAnalyzer()
    # see https://github.com/cjhutto/vaderSentiment#about-the-scoring for more info
    polarity_scores = s.polarity_scores(message)
    if polarity_scores["compound"] >= 0.05:
        return "Positive"
    if polarity_scores["compound"] <= -0.05:
        return "Negative"
    return "Neutral"


class HTMLBuilder:
    def __init__(self):
        self.html = ""
        self.rows_html = ""

        self.add_head()

    def add_head(self):
        self.html += f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/andrewh0/okcss@1/dist/ok.min.css" />
            <title>Toot analist</title>
            <style>
                td {{ max-width: 60ch; }}
                .flex {{ display: flex; }}
                .justify-center {{ justify-content: center; }}
                .text-center {{ text-align: center; }}
                .p-2 {{ padding: 0.5rem; }}
            </style>
        </head>
        <body>
        """

    def add_footer(self):
        self.html += """
        <footer></footer>
        </html>
        """

    def add_table(self, tbody):
        self.html += f"""
            <table>
                <caption>LeIA Sentiment Analysis</caption>
                <thead>
                    <tr>
                        <th>Message</th>
                        <th>Sentiment</th>
                    </tr>
                </thead>
                <tbody>
                { tbody }
                </tbody>
            </table>
        """

    def add_table_row(self, toot_html, sentiment, image_data=None):
        self.rows_html += "<tr>"

        if image_data:
            self.rows_html += f"<td>{ toot_html }"
            for image in image_data:
                self.rows_html += f"""
                    <a target="_blank" href="{ image['url'] }">
                        <figure>
                            <img width="{ image['meta']['small']['width'] }" height="{ image['meta']['small']['height'] }" src="{ image['preview_url'] }" alt="{ image['description'] }" />
                            <figcaption>{ image['description'] }</figcaption>
                        </figure>
                    </a>
                """
            self.rows_html += "</td>"
        else:
            self.rows_html += f"<td>{ toot_html }</td>"

        self.rows_html += f"<td>{ sentiment }</td>"
        self.rows_html += "</tr>"

    def add_sentiment_counter(self, sentiment_distribution):
        self.html += f"""
            <div class="flex justify-center">
                <div class="p-2">
                    <h2>Positive</h2>
                    <h3 class="text-center">😊 { sentiment_distribution['Positive'] }</h3>
                </div>
                <div class="p-2">
                    <h2>Neutral</h2>
                    <h3 class="text-center">😐 { sentiment_distribution['Neutral'] }</h3>
                </div>
                <div class="p-2">
                    <h2>Negative</h2>
                    <h3 class="text-center">😠 { sentiment_distribution['Negative'] }</h3>
                </div>
            </div>
        """

    def build(self):
        self.add_table(self.rows_html)
        self.add_footer()
        return self.html


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--toots", action="store_true", required=False)

    args = parser.parse_args()

    if args.toots:
        html_builder = HTMLBuilder()
        toots = get_mastodon_local_timeline_toots()
        if toots is None:
            print("No toots found!")
            sys.exit(1)
        sentiment_distribution = {"Positive": 0, "Negative": 0, "Neutral": 0}
        for toot in toots:
            toot_soup = BeautifulSoup(toot["content"], "html.parser")
            toot_text = toot_soup.get_text()
            toot_sentiment = get_leia_sentiment(toot_text)
            sentiment_distribution[toot_sentiment] += 1
            html_builder.add_table_row(
                toot_soup.prettify(), toot_sentiment, toot["media_attachments"]
            )
        html_builder.add_sentiment_counter(sentiment_distribution)
        print(html_builder.build())
        sys.exit(0)


if __name__ == "__main__":
    main()
