import argparse
import requests
import sys

api_url = "https://anime-reactions.uzairashraf.dev/api"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--category', required=False, help='Specify your reaction category!')
    parser.add_argument('-lc', '--list-categories', action='store_true', required=False, help='Lists available categories')

    args = parser.parse_args()

    if args.category:
        req_url = f"{api_url}/reactions/random"
        get_params = {'category': args.category}
        req = requests.get(req_url, params=get_params)
        if not req.ok:
            print("Request failed!")
            sys.exit(1)
        response = req.json()
        print(response)

    if args.list_categories:
        req_url = f"{api_url}/categories"
        req = requests.get(req_url)
        if not req.ok:
            print("Request failed!")
            sys.exit(1)
        response = req.json()
        print(response)


if __name__ == '__main__':
    main()

    
