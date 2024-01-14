import argparse
import json
import requests
import sys

api_url = "https://anime-reactions.uzairashraf.dev/api"


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


def get_emotion_from_message(message):
    # open emotions_dir.json and get the mapping of words to emotions
    emotions_mapping = json.load(open("emotions_dir.json", "r"))
    # split the message into words
    msg_words = message.split()

    emotion_points = {}

    # iterate through the words in the message
    for word in msg_words:
        # iterate through available emotions in the mapping
        for emotion, emotion_words in emotions_mapping.items():
            # iterate through the words in the key
            if word in emotion_words:
                # if the word is in the key, return the emotion
                emotion_points[emotion] = emotion_points.get(emotion, 0) + 1

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
        emotion = get_emotion_from_message(args.message)
        if emotion is None:
            print("No emotion detected!")
            sys.exit(1)
        print(f"Detected emotion: {emotion}")
        reaction = get_random_reaction_from_category(emotion)
        print(reaction["reaction"])
        sys.exit(0)


if __name__ == "__main__":
    main()
