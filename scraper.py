import os
import urllib.parse
import feedparser
from datetime import datetime
from bs4 import BeautifulSoup

def clean_text(html_content):
    """Cleans messy HTML to extract readable paragraph text."""
    if not html_content: return ""
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(separator=" ", strip=True)

def fetch_news(query, num_items):
    """Fetches targeted news from Bing News RSS which includes full paragraph context."""
    safe_query = urllib.parse.quote(query)
    # Bing News provides much better summaries/descriptions than Google News
    url = f"https://www.bing.com/news/search?q={safe_query}&format=rss"
    
    feed = feedparser.parse(url)
    return feed.entries[:num_items]

def update_cards(soup, section_id, articles, max_summary=200):
    """Safely updates a block of cards with fetched articles and expanded text limits."""
    cards = soup.select(f'#{section_id} .card')
    for i, article in enumerate(articles):
        if i < len(cards):
            title_el = cards[i].select_one('.card-title')
            desc_el = cards[i].select_one('p')
            
            if title_el:
                # Keep headlines clean
                title_el.string = article.title[:65] + ("..." if len(article.title) > 65 else "")
            
            if desc_el:
                # Grab Bing's description which contains the actual article context
                desc = clean_text(getattr(article, 'description', getattr(article, 'summary', '')))
                
                # Fallback only if the snippet is completely broken
                if len(desc) < 30: 
                    desc = f"New developments reported regarding {article.title}. Click the source link to read the full context of this industry update."
                
                # Inject the much longer context paragraph
                desc_el.string = desc[:max_summary] + ("..." if len(desc) > max_summary else "")

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
    
    # A. Lead Story (1 Item - Gets a massive 600 character context limit)
    lead_articles = fetch_news("Adobe MAX OR Figma OR major design news", 1)
    if lead_articles:
        lead = lead_articles[0]
        title_el = soup.select_one('#lead-story .display-title')
        body_el = soup.select_one('#lead-story .body-copy')
        if title_el: title_el.string = lead.title[:80] + ("..." if len(lead.title) > 80 else "")
        if body_el: 
            desc = clean_text(getattr(lead, 'description', getattr(lead, 'summary', '')))
            if len(desc) < 50: desc = f"Major industry shifts announced today regarding {lead.title}. Read the full editorial for complete context."
            body_el.string = desc[:600] + ("..." if len(desc) > 600 else "")

    # B. AI News (3 Items)
    ai_articles = fetch_news("AI image generation OR AI design tools OR Midjourney", 3)
    update_cards(soup, 'ai-section', ai_articles, max_summary=220)

    # C. Graphic Design (3 Items)
    gd_articles = fetch_news("rebrand OR logo redesign OR typography release", 3)
    update_cards(soup, 'graphic-section', gd_articles, max_summary=180)

    # D. UI/UX (3 Items)
    ui_articles = fetch_news("app redesign OR UX research OR OS interface update", 3)
    update_cards(soup, 'uiux-section', ui_articles, max_summary=180)

    # E. Student (2 Items)
    student_articles = fetch_news("design competition OR creative career advice OR design students", 2)
    update_cards(soup, 'student-section', student_articles, max_summary=250)

    # F. Indian Design Watch (6 Items total split safely across two rows)
    india_articles = fetch_news("Indian advertising agency OR Indian ad campaign OR Indian design", 6)
    first_row = india_articles[:3] if len(india_articles) >= 3 else india_articles
    second_row = india_articles[3:] if len(india_articles) > 3 else []
    
    update_cards(soup, 'india-section-1', first_row, max_summary=180)
    update_cards(soup, 'india-section-2', second_row, max_summary=180)

    # 3. Save the Document
    with open('index.html', 'w', encoding='utf-8') as file:
        file.write(str(soup))
    print("Massive global layout updated with full news context!")

if __name__ == "__main__":
    update_newspaper()
