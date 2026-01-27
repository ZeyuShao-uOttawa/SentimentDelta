
from newspaper import Article

def get_article_text(url):
    """Extract article text."""
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text if article.text and len(article.text) > 50 else None
    except:
        return None