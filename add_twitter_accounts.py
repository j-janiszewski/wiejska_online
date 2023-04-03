import argparse
import json
from models import Politician, TwitterAccount
from config import db_session, twitter_api

parser = argparse.ArgumentParser(
    description="Script for adding new twitter account to database \n \
    Either provide name of json file with politician ids and twitter screen names or single politician id and twitter screen name",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)

parser.add_argument(
    "-f", "--file", help="json file with politician id and twitter screennames"
)
# Example of file content structure:
#  [
#     [
#         politician_id,
#         politician_twitter_screen_name
#     ]
# ]
#

parser.add_argument("-id", "--politician-id", help="politician id")
parser.add_argument("-sn", "--screen-name", help="politician twitter screen name")

args = parser.parse_args()
args = vars(args)


if args["file"]:
    with open(args["file"], "r") as f:
        accounts_to_add = json.load(f)
elif args["screen_name"] and args["politician_id"]:
    accounts_to_add = [[args["screen_name"], args["politician_id"]]]
else:
    raise RuntimeError(
        "You must either specify json file or id and screen name of single politician"
    )


with db_session() as session:
    api = twitter_api()
    politicians = session.query(Politician).all()

    for politician_id, twitter_screen_name in accounts_to_add:
        politician = (
            session.query(Politician).filter(Politician.id == politician_id).first()
        )
        twitter_user = api.get_user(screen_name=twitter_screen_name)
        twitter_account = TwitterAccount(
            id=twitter_user._json["id"],
            screen_name=twitter_screen_name,
            is_active=True,
            politician_id=politician.id,
        )
        politician.twitter_account = [twitter_account]
    try:
        session.commit()
    except:
        session.rollback()
