RSS_URL = r'https://news.google.com/rss/search?q=("Global+Capability+Centre"+OR+"Global+Capability+Center"+OR+"GCC+India")+(intitle:incentive+OR+intitle:subsidy+OR+intitle:policy+OR+intitle:grant+OR+intitle:tax)+-"Gulf+Cooperation+Council"+-"Provider+Lens"+-"Award"+-"Leader"+when:1d&hl=en-IN&gl=IN&ceid=IN:en'

DATABASE_PATH = "data/processed_articles.db"

LOG_FILE = "logs/gcc_tracker.log"

REQUEST_TIMEOUT = 30

USER_AGENT = {
    "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}