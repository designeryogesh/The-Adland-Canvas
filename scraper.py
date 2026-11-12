import os
import urllib.parse
import feedparser
from datetime import datetime
from bs4 import BeautifulSoup

def clean_text(html_content):
    if not html_content: return ""
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(separator=" ", strip=True)

def fetch_news(query, num_items, is_india=False):
    """Fetches targeted news from Google News RSS."""
    safe_query = urllib.parse.quote(query)
    # Use global news for general design, and IN specific for Indian Watch
    if is_india:
        url = f"https://news.google.com/rss/search?q={safe_query}&hl=en-IN&gl=IN&ceid=IN:en"
    else:
        url = f"https://news.google.com/rss/search?q={safe_query}&hl=en-US&gl=US&ceid=US:en"
    
    feed = feedparser.parse(url)
    return feed.entries[:num_items]

def update_cards(soup, section_id, articles, max_summary=120):
    """Safely updates a block of cards with fetched articles."""
    cards = soup.select(f'#{section_id} .card')
    for i, article in enumerate(articles):
        if i < len(cards):
            title_el = cards[i].select_one('.card-title')
            desc_el = cards[i].select_one('p')
            
            if title_el:
                title_el.string = article.title.split(' - ')[0][:60] + "..."
            if desc_el:
                desc = clean_text(getattr(article, 'summary', ''))
                if len(desc) < 20: desc = f"Read the full update regarding {article.title.split(' - ')[0]}."
                desc_el.string = desc[:max_summary] + "..."

def update_newspaper():
    # 1. Update Volume and Issue
    today = datetime.now()
    new_meta_text = f"Vol. {today.month:02d} · Issue {today.timetuple().tm_yday:03d}"
    
    try:
        with open('index.html', 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file.read(), 'html.parser')
    except FileNotFoundError:
        print("Error: index.html not found!")
        return

    # Update Meta Bar
    meta_bar = soup.find('div', class_='meta-bar')
    if meta_bar and meta_bar.find('div'):
        meta_bar.find('div').string = new_meta_text

    # 2. Fetch and Inject Data by Category
    
    # A. Lead Story (1 Item)
    lead_articles = fetch_news("Adobe MAX OR Figma OR major design news", 1)
    if lead_articles:
        lead = lead_articles[0]
        title_el = soup.select_one('#lead-story .display-title')
        body_el = soup.select_one('#lead-story .body-copy')
        if title_el: title_el.string = lead.title.split(' - ')[0]
        if body_el: body_el.string = clean_text(getattr(lead, 'summary', ''))[:450] + "..."

    # B. AI News (3 Items)
    ai_articles = fetch_news("AI image generation OR AI design tools OR Midjourney", 3)
    update_cards(soup, 'ai-section', ai_articles)

    # C. Graphic Design (3 Items)
    gd_articles = fetch_news("rebrand OR logo redesign OR typography release", 3)
    update_cards(soup, 'graphic-section', gd_articles)

    # D. UI/UX (3 Items)
    ui_articles = fetch_news("app redesign OR UX research OR OS interface update", 3)
    update_cards(soup, 'uiux-section', ui_articles)

    # E. Student (2 Items)
    student_articles = fetch_news("design competition OR creative career advice OR design students", 2)
    update_cards(soup, 'student-section', student_articles, max_summary=150)

    # F. Indian Design Watch (6 Items total split across two rows)
    india_articles = fetch_news("Indian advertising agency OR Indian ad campaign OR Indian design", 6, is_india=True)
    update_cards(soup, 'india-section-1', india_articles[:3])
    update_cards(soup, 'india-section-2', india_articles[3:])

    # 3. Save the Document
    with open('index.html', 'w', encoding='utf-8') as file:
        file.write(str(soup))
    print("Massive global layout updated successfully!")

if __name__ == "__main__":
    update_newspaper()
