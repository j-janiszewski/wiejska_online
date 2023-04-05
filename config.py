import sqlalchemy
import tweepy
from cryptography.fernet import Fernet
import os
import yagmail
from models import Base


WALLET_DIR = "./wallet"
ENCRYPTED_DIR = "./encrypted"
GMAIL_NOTIFIER_ADDRESS = "wiejskaonline@gmail.com"
NOTIFICATION_RECIPIENT_ADDRESS = "jasiekj1@gmail.com"


def decrypt_file(file_path: str, output_location: str) -> None:
    """Decrypts given file using key stored in WIEJSKA_ONLINE_ENCRYPTION_KEY env var.

    Args:
        file_path (str): encrypted file path
        output_location (str): path where decrypted file should be placed
    """
    fernet = Fernet(os.environ["WIEJSKA_ONLINE_WALLET_ENCRYPTION_KEY"])
    with open(file_path, "rb") as enc_file:
        encrypted = enc_file.read()
    decrypted = fernet.decrypt(encrypted)
    with open(output_location, "wb") as dec_file:
        dec_file.write(decrypted)


def db_session(create_tables=False) -> sqlalchemy.orm.Session:
    """Creates session with oracle cloud database using local wallet file and user credentials
    from WIEJSKA_ONLINE_USER_NAME and WIEJSKA_ONLINE_PASSWORD env vars.

    Args:
        create_tables (bool, optional): If set to True then tables defined in models.py will we created. Defaults to False.

    Returns:
        sqlalchemy.orm.Session: object that represent session with database and allow you to modify its content.
    """
    if not os.path.exists(WALLET_DIR):
        os.mkdir(WALLET_DIR)
        decrypt_file(ENCRYPTED_DIR + "/ewallet.pem", WALLET_DIR + "/ewallet.pem")
        decrypt_file(ENCRYPTED_DIR + "/tnsnames.ora", WALLET_DIR + "/tnsnames.ora")

    engine = sqlalchemy.create_engine(
        f"oracle+oracledb://:@",
        connect_args={
            "user": os.environ["WIEJSKA_ONLINE_USER_NAME"],
            "password": os.environ["WIEJSKA_ONLINE_PASSWORD"],
            "dsn": os.environ["WIEJSKA_ONLINE_CS"],
            "config_dir": "./wallet",
            "wallet_location": "./wallet",
            "wallet_password": os.environ["WIEJSKA_ONLINE_WALLET_PASSWORD"],
        },
        poolclass=sqlalchemy.pool.NullPool,
    )
    if create_tables:
        Base.metadata.create_all(engine)
    session = sqlalchemy.orm.sessionmaker(bind=engine)()
    return session


def twitter_api() -> tweepy.API:
    """Creates api object allowing to communicate with Twitter API.

    Returns:
        tweepy.API: api object
    """
    authenticator = tweepy.OAuthHandler(
        os.environ["TWITTER_CONSUMER_KEY"], os.environ["TWITTER_CONSUMER_SECRET"]
    )
    authenticator.set_access_token(
        os.environ["TWITTER_ACCESS_TOKEN"], os.environ["TWITTER_ACCESS_SECRET"]
    )
    return tweepy.API(authenticator)


def send_notification(subject: str, content: str) -> None:
    """Sends email to GMAIL_NOTIFIER_ADDRESS.

    Args:
        subject (str): Email subject
        content (str): Email content
    """
    yag = yagmail.SMTP(
        GMAIL_NOTIFIER_ADDRESS,
        os.environ["GMAIL_NOTIFIER_PASSWORD"],
    )
    yag.send(
        NOTIFICATION_RECIPIENT_ADDRESS,
        subject,
        content,
    )
