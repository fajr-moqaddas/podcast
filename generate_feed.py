import os
import glob
import json
from datetime import datetime
from email.utils import formatdate
from mutagen.mp3 import MP3
import xml.etree.ElementTree as ET

# --- پیکربندی پادکست ---
PODCAST_CONFIG = {
    "title": "فجر مقدس",
    "description": "روایت به روایت شش ماه پایانی منتهی به ظهور. این پادکست، یک سفر روایی و تحلیلی بر اساس کتاب «شش ماه پایانی، فجر مقدس» نوشتۀ آقای مجتبی الساده است. در این مجموعۀ ۲۵ قسمتی، با هم قدم به قدم، نشانه‌ها و وقایع سال ظهور را بر اساس آیات و روایات اهل بیت (علیهم السلام) دنبال می‌کنیم.",
    "author": "امید و نورا",
    # "email": "",
    "language": "fa",
    "category": "Religion & Spirituality",
    "subcategory": "Islam",
    "explicit": "no",
    "copyright": f"© {datetime.now().year} امید و نورا",
    "cover_art_filename": "cover.png",
    "base_url": "https://fajr-moqaddas.github.io/podcast"
}

# --- مسیر فایل‌ها ---
EPISODES_DIR = "episodes"
EPISODES_JSON_FILE = "episodes.json"
OUTPUT_RSS_FILE = "rss.xml"
OUTPUT_HTML_FILE = "index.html"

def get_mp3_metadata(filepath):
    """اطلاعات فنی یک فایل MP3 را استخراج می‌کند."""
    audio = MP3(filepath)
    metadata = {
        'duration_seconds': int(audio.info.length),
        'size_bytes': os.path.getsize(filepath),
        'pub_date': datetime.fromtimestamp(os.path.getmtime(filepath))
    }
    return metadata

def format_duration_for_html(seconds):
    """مدت زمان را برای نمایش در HTML به فرمت HH:MM:SS تبدیل می‌کند."""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02}"

def generate_rss_feed(episodes_metadata):
    """فایل rss.xml را بر اساس اطلاعات قسمت‌ها تولید می‌کند."""
    print("Generating RSS feed...")

    ns = {
        'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd',
        'atom': 'http://www.w3.org/2005/Atom',
        'content': 'http://purl.org/rss/1.0/modules/content/'
    }
    ET.register_namespace('itunes', ns['itunes'])
    ET.register_namespace('atom', ns['atom'])
    ET.register_namespace('content', ns['content'])
    
    rss = ET.Element('rss', version='2.0', attrib={
        'xmlns:itunes': ns['itunes'], 'xmlns:atom': ns['atom'], 'xmlns:content': ns['content']
    })
    channel = ET.SubElement(rss, 'channel')

    # --- Channel Tags ---
    ET.SubElement(channel, 'title').text = PODCAST_CONFIG['title']
    ET.SubElement(channel, 'link').text = PODCAST_CONFIG['base_url']
    ET.SubElement(channel, 'description').text = PODCAST_CONFIG['description']
    ET.SubElement(channel, 'language').text = PODCAST_CONFIG['language']
    ET.SubElement(channel, 'copyright').text = PODCAST_CONFIG['copyright']
    ET.SubElement(channel, 'atom:link', {
        'href': f"{PODCAST_CONFIG['base_url']}/{OUTPUT_RSS_FILE}", 'rel': 'self', 'type': 'application/rss+xml'
    })
    ET.SubElement(channel, 'itunes:author').text = PODCAST_CONFIG['author']
    ET.SubElement(channel, 'itunes:type').text = 'episodic'
    ET.SubElement(channel, 'itunes:summary').text = PODCAST_CONFIG['description']
    ET.SubElement(channel, 'itunes:explicit').text = PODCAST_CONFIG['explicit']
    ET.SubElement(channel, 'itunes:image', href=f"{PODCAST_CONFIG['base_url']}/{PODCAST_CONFIG['cover_art_filename']}")
    itunes_category = ET.SubElement(channel, 'itunes:category', text=PODCAST_CONFIG['category'])
    ET.SubElement(itunes_category, 'itunes:category', text=PODCAST_CONFIG['subcategory'])
    owner = ET.SubElement(channel, 'itunes:owner')
    ET.SubElement(owner, 'itunes:name').text = PODCAST_CONFIG['author']
    # ET.SubElement(owner, 'itunes:email').text = PODCAST_CONFIG['email']

    # --- Episode Items ---
    sorted_episodes = sorted(episodes_metadata, key=lambda x: x['filename'])

    for meta in sorted_episodes:
        item = ET.SubElement(channel, 'item')
        
        ET.SubElement(item, 'title').text = f"{PODCAST_CONFIG['title']} - {meta['episode_number']}: {meta['title']}"
        ET.SubElement(item, 'description').text = meta['summary']
        ET.SubElement(item, 'link').text = f"{PODCAST_CONFIG['base_url']}/#episode-{meta['episode_number']}"
        ET.SubElement(item, 'guid', isPermaLink='false').text = f"{PODCAST_CONFIG['base_url']}/{EPISODES_DIR}/{meta['filename']}"
        ET.SubElement(item, 'pubDate').text = formatdate(meta['pub_date'].timestamp(), usegmt=True)
        ET.SubElement(item, 'itunes:author').text = PODCAST_CONFIG['author']
        ET.SubElement(item, 'itunes:duration').text = str(meta['duration_seconds'])
        ET.SubElement(item, 'itunes:episode').text = meta['episode_number']
        ET.SubElement(item, 'itunes:episodeType').text = 'full'
        ET.SubElement(item, 'itunes:explicit').text = PODCAST_CONFIG['explicit']
        ET.SubElement(item, 'itunes:summary').text = meta['summary']
        ET.SubElement(item, 'itunes:image', href=f"{PODCAST_CONFIG['base_url']}/{PODCAST_CONFIG['cover_art_filename']}")
        
        content_encoded = ET.SubElement(item, 'content:encoded')
        content_encoded.text = f"<![CDATA[<p>{meta['summary']}</p>]]>"

        ET.SubElement(item, 'enclosure', {
            'url': f"{PODCAST_CONFIG['base_url']}/{EPISODES_DIR}/{meta['filename']}",
            'length': str(meta['size_bytes']),
            'type': 'audio/mpeg'
        })

    tree = ET.ElementTree(rss)
    tree.write(OUTPUT_RSS_FILE, encoding='UTF-8', xml_declaration=True)
    print(f"✅ RSS feed saved to {OUTPUT_RSS_FILE}")

def generate_html_page(episodes_metadata):
    """صفحه index.html را تولید می‌کند."""
    print("Generating HTML page...")

    sorted_episodes = sorted(episodes_metadata, key=lambda x: x['filename'])
    
    image_meta = {
        "url": f"{PODCAST_CONFIG['base_url']}/{PODCAST_CONFIG['cover_art_filename']}",
        "type": "image/png",
        "width": "1200",
        "height": "630",
        "alt": f"کاور آرت پادکست {PODCAST_CONFIG['title']}"
    }

    html = f"""
<!DOCTYPE html>
<html lang="{PODCAST_CONFIG['language']}" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{PODCAST_CONFIG['title']}</title>
    <meta name="description" content="{PODCAST_CONFIG['description']}">

    <!-- Social Media Meta Tags (Open Graph & Twitter) -->
    <meta property="og:title" content="{PODCAST_CONFIG['title']}">
    <meta property="og:description" content="{PODCAST_CONFIG['description']}">
    <meta property="og:url" content="{PODCAST_CONFIG['base_url']}">
    <meta property="og:site_name" content="{PODCAST_CONFIG['title']}">
    <meta property="og:locale" content="fa_IR">
    <meta property="og:type" content="website">
    <meta property="og:image" content="{image_meta['url']}">
    <meta property="og:image:type" content="{image_meta['type']}">
    <meta property="og:image:width" content="{image_meta['width']}">
    <meta property="og:image:height" content="{image_meta['height']}">
    <meta property="og:image:alt" content="{image_meta['alt']}">
    
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{PODCAST_CONFIG['title']}">
    <meta name="twitter:description" content="{PODCAST_CONFIG['description']}">
    <meta name="twitter:image" content="{image_meta['url']}">

    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; margin: 0; background-color: #f8f9fa; color: #333; }}
        .container {{ max-width: 800px; margin: 20px auto; padding: 20px; background-color: #fff; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        header {{ text-align: center; border-bottom: 1px solid #eee; padding-bottom: 20px; margin-bottom: 20px; }}
        header img {{ max-width: 200px; border-radius: 8px; }}
        header h1 {{ margin: 10px 0 5px; }}
        header p.main-desc {{ color: #666; font-size: 1.1em; }}
        .subscribe-button {{ display: inline-block; background-color: #9c27b0; color: #fff; padding: 12px 24px; border-radius: 5px; text-decoration: none; font-weight: bold; margin-top: 15px; }}
        .episode-list {{ list-style: none; padding: 0; }}
        .episode {{ border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 15px; background-color: #fdfdfd; scroll-margin-top: 20px; }}
        .episode h3 {{ margin: 0 0 10px; }}
        .episode p.summary {{ font-size: 1em; color: #555; margin: 10px 0; }}
        .episode-meta {{ font-size: 0.9em; color: #888; margin-bottom: 10px; }}
        audio {{ width: 100%; margin-top: 10px; }}
        footer a {{ color: #555; text-decoration: none; }}
        footer a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <img src="{PODCAST_CONFIG['cover_art_filename']}" alt="{image_meta['alt']}">
            <h1>{PODCAST_CONFIG['title']}</h1>
            <p class="main-desc">{PODCAST_CONFIG['description']}</p>
            <a href="{PODCAST_CONFIG['base_url']}/{OUTPUT_RSS_FILE}" class="subscribe-button">دنبال کردن (RSS Feed)</a>
        </header>
        <ul class="episode-list">
    """
    for meta in sorted_episodes:
        episode_html = f"""
            <li class="episode" id="episode-{meta['episode_number']}">
                <h3>{meta['episode_number']}: {meta['title']}</h3>
                <p class="summary">{meta['summary']}</p>
                <div class="episode-meta">
                    <span>تاریخ انتشار: {meta['pub_date'].strftime('%Y-%m-%d')}</span> | <span>مدت زمان: {format_duration_for_html(meta['duration_seconds'])}</span>
                </div>
                <audio controls preload="none">
                    <source src="{PODCAST_CONFIG['base_url']}/{EPISODES_DIR}/{meta['filename']}" type="audio/mpeg">
                    Your browser does not support the audio element.
                </audio>
            </li>
        """
        html += episode_html
    html += f"""
        </ul>
        <footer>
            <p style="text-align:center; color:#aaa;">{PODCAST_CONFIG['copyright']} | Published under the <a href="https://www.gnu.org/licenses/gpl-3.0.html" target="_blank" rel="noopener noreferrer">GNU GPL v3.0</a>.</p>
        </footer>
    </div>
</body>
</html>
    """
    with open(OUTPUT_HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ HTML page saved to {OUTPUT_HTML_FILE}")

if __name__ == "__main__":
    if not os.path.exists(EPISODES_JSON_FILE):
        print(f"Error: Metadata file '{EPISODES_JSON_FILE}' not found.")
        exit()
    with open(EPISODES_JSON_FILE, 'r', encoding='utf-8') as f:
        episodes_data = json.load(f)
    episodes_map = {e['episode_number']: e for e in episodes_data}

    if not os.path.exists(EPISODES_DIR):
        print(f"Error: Directory '{EPISODES_DIR}' not found.")
        exit()
        
    mp3_files = glob.glob(os.path.join(EPISODES_DIR, "*.mp3"))
    if not mp3_files:
        print(f"Error: No MP3 files found in '{EPISODES_DIR}' directory.")
    else:
        all_metadata = []
        for f in mp3_files:
            filename = os.path.basename(f)
            episode_num = os.path.splitext(filename)[0]

            if episode_num not in episodes_map:
                print(f"Warning: No metadata found for episode '{episode_num}' in {EPISODES_JSON_FILE}. Skipping.")
                continue

            mp3_meta = get_mp3_metadata(f)
            json_meta = episodes_map[episode_num]
            
            combined_meta = mp3_meta.copy()
            combined_meta.update(json_meta)
            combined_meta['filename'] = filename
            
            all_metadata.append(combined_meta)
        
        if all_metadata:
            generate_rss_feed(all_metadata)
            generate_html_page(all_metadata)
            print("\nAll files generated successfully!")
        else:
            print("No valid episodes found to process.")
