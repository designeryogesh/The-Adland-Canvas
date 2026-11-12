import os
import feedparser
from datetime import datetime
from bs4 import BeautifulSoup

def clean_text(html_content):
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(separator=" ", strip=True)

def update_newspaper():
    today = datetime.now()
    new_meta_text = f"Vol. {today.month:02d} · Issue {today.timetuple().tm_yday:03d}"
    
    rss_url = "https://news.google.com/rss/search?q=Indian+advertising+agency+campaign+OR+mandate+OR+account+win&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(rss_url)
    articles = feed.entries[:6]
    
    try:
        with open('index.html', 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file.read(), 'html.parser')
    except FileNotFoundError:
        print("Error: index.html not found!")
        return

    meta_bar = soup.find('div', class_='meta-bar')
    if meta_bar:
        vol_div = meta_bar.find('div')
        if vol_div:
            vol_div.string = new_meta_text
            
    if len(articles) >= 6:
        def get_summary(article, max_length):
            desc = getattr(article, 'summary', getattr(article, 'description', ''))
            clean = clean_text(desc)
            if len(clean) < 15 or clean.startswith(article.title[:20]):
                clean = f"The Indian advertising industry sees new movement today as {article.title.split(' - ')[0]}. Full details reported by {getattr(article.source, 'title', 'industry sources')}."
            return clean[:max_length] + "..." if len(clean) > max_length else clean

        lead_title = soup.select_one('.lead-story .display-title')
        lead_body = soup.select_one('.lead-story .body-copy')
        if lead_title and lead_body:
            lead_title.string = articles[0].title.split(' - ')[0] 
            lead_body.string = get_summary(articles[0], 400)
            
        sidebar_cards = soup.select('.sidebar .card:not(.accent)')
        if len(sidebar_cards) >= 2:
            sidebar_cards[0].select_one('.card-title').string = articles[1].title.split(' - ')[0][:50] + "..."
            sidebar_cards[0].select_one('p').string = get_summary(articles[1], 120)
            
            sidebar_cards[1].select_one('.card-title').string = articles[2].title.split(' - ')[0][:50] + "..."
            sidebar_cards[1].select_one('p').string = get_summary(articles[2], 120)

        bottom_cards = soup.select('.bottom-section .card')
        if len(bottom_cards) >= 3:
            for i in range(3):
                bottom_cards[i].select_one('.card-title').string = articles[i+3].title.split(' - ')[0][:40] + "..."
                bottom_cards[i].select_one('p').string = get_summary(articles[i+3], 100)

    with open('index.html', 'w', encoding='utf-8') as file:
        file.write(str(soup))
    print("Newspaper updated successfully with full content paragraphs!")

if __name__ == "__main__":
    update_newspaper()
