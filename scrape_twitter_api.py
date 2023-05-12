"""
Script that scrapes twitter API.
Politicians followers count and new tweets are registered in database.

If politician twitter acoount is inactive notification is generated.
If twitter api rate limit is exceeded notification is generated.
"""
from config import twitter_api, db_session, send_notification
from models import Politician, Tweet, FollowersNumber
import sqlalchemy
from datetime import datetime
from dateutil.parser import parse
import tweepy


def create_tweet(tweepy_status: tweepy.models.Status) -> Tweet:
    """Creates Tweet from status returned by tweepy.

    Args:
        tweepy_status (tweepy.models.Status): Status returned by tweepy

    Returns:
        Tweet: Tweet object
    """
    tweet_dict = tweepy_status._json
    tweet = Tweet(
        id=tweet_dict["id"],
        created_at=parse(tweet_dict["created_at"]),
        text=tweet_dict["full_text"],
        source=tweet_dict["source"],
        reply_to_status_id=tweet_dict["in_reply_to_status_id"],
        reply_to_user_id=tweet_dict["in_reply_to_user_id"],
        user_id=tweet_dict["user"]["id"],
    )
    if "retweeted_status" in tweet_dict:
        tweet.retweeted_status_id = tweet_dict["retweeted_status"]["id"]
        tweet.retweeted_user_id = tweet_dict["retweeted_status"]["user"]["id"]
        tweet.text = tweet_dict["retweeted_status"]["full_text"]
    elif "quoted_status" in tweet_dict:
        tweet.quoteded_text = tweet_dict["quoted_status"]["full_text"]
        tweet.quoted_user_id = tweet_dict["quoted_status"]["user"]["id"]
        tweet.quoteded_status_id = tweet_dict["quoted_status"]["id"]
    return tweet


def check_twitter_account(
    politician: Politician, twitter_api: tweepy.API, db_session: sqlalchemy.orm.Session
) -> None:
    """Checks given politician active twitter account (if exists).
    If account marked as existing is unavaible (suspended/deleted) email notification is sent.
    If not then number of followers and new tweets (tweets created after most recent one in database)
    are downloaded and saved to database.

    Args:
        politician (Politician): Politician to check
        twitter_api (tweepy.API): twitter api used for chcecking account
        db_session (sqlalchemy.orm.Session): session with database
    """
    active_account = [
        account for account in politician.twitter_account if account.is_active
    ]
    if active_account:
        active_account = active_account[0]
        (id_of_last_tweet,) = (
            db_session.query(sqlalchemy.sql.expression.func.max(Tweet.id))
            .filter_by(user_id=active_account.id)
            .first()
        )
        try:
            user = twitter_api.get_user(user_id=active_account.id)
        except Exception as ex:
            # mark account as inactive?
            send_notification(
                "WIEJSKA ONLINE: Exception when checking twitter account",
                f"When trying to scrape data from {politician.first_name} {politician.last_name} \
                  twitter account (screen_name ={active_account.screen_name} exception occurred. \n \n \
                    Exception : {ex}",
            )

        else:
            if user.screen_name != active_account.screen_name:
                active_account.screen_name = user.screen_name
            followers_number = FollowersNumber(
                account_id=active_account.id,
                date=datetime.now(),
                number_of_followers=user.followers_count,
            )
            db_session.add(followers_number)
            if id_of_last_tweet:
                cursor = tweepy.Cursor(
                    twitter_api.user_timeline,
                    user_id=active_account.id,
                    since_id=id_of_last_tweet,
                    tweet_mode="extended",
                )
            else:
                cursor = tweepy.Cursor(
                    twitter_api.user_timeline,
                    user_id=active_account.id,
                    tweet_mode="extended",
                )
            for status in cursor.items():
                session.add(create_tweet(status))


if __name__ == "__main__":
    api = twitter_api()

    with db_session() as session:
        politicians = session.query(Politician).all()

        for politician in politicians:
            if politician.twitter_account:
                try:
                    check_twitter_account(politician, api, session)
                except tweepy.errors.TooManyRequests:
                    send_notification(
                        "WIEJSKA ONLINE: Twitter rate limit exceeded",
                        f"When downloading tweets written by {politician.first_name} {politician.last_name}  \
                        twitter api request rate limit was exceeded, manually rerun scrape_twitter_api.py script in 15 minutes",
                    )
                    break
        try:
            session.commit()
        except:
            session.rollback()
