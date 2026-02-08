import re
from urllib.parse import urlparse, urljoin, urldefrag, parse_qs
from bs4 import BeautifulSoup
from collections import Counter
import json
import os

ANALYTICS_FILE = "analytics.json"
def load_analytics():
    if os.path.exists(ANALYTICS_FILE):
        with open(ANALYTICS_FILE, 'r') as f:
            data = json.load(f)
            data['unique_pages'] = set(data.get('unique_pages', []))
            data['all_words'] = Counter(data.get('all_words', {}))
            data['subdomains'] = Counter(data.get('subdomains', {}))
            return data
    return {
        'unique_pages': set(),
        'word_counts': {},
        'all_words': Counter(),
        'subdomains': Counter(),
        'longest_page': {'url': '', 'word_count': 0}
    }

def save_analytics(analytics):
    data = {
        'unique_pages': list(analytics['unique_pages']),
        'word_counts': analytics['word_counts'],
        'all_words': dict(analytics['all_words']),
        'subdomains': dict(analytics['subdomains']),
        'longest_page': analytics['longest_page']
    }
    with open(ANALYTICS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

analytics = load_analytics()

# Common English stop words
STOP_WORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 
    'aren\'t', 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both',
    'but', 'by', 'can\'t', 'cannot', 'could', 'couldn\'t', 'did', 'didn\'t', 'do', 'does', 'doesn\'t',
    'doing', 'don\'t', 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', 'hadn\'t',
    'has', 'hasn\'t', 'have', 'haven\'t', 'having', 'he', 'he\'d', 'he\'ll', 'he\'s', 'her', 'here',
    'here\'s', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'how\'s', 'i', 'i\'d', 'i\'ll',
    'i\'m', 'i\'ve', 'if', 'in', 'into', 'is', 'isn\'t', 'it', 'it\'s', 'its', 'itself', 'let\'s',
    'me', 'more', 'most', 'mustn\'t', 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once',
    'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same', 'shan\'t',
    'she', 'she\'d', 'she\'ll', 'she\'s', 'should', 'shouldn\'t', 'so', 'some', 'such', 'than', 'that',
    'that\'s', 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', 'there\'s', 'these',
    'they', 'they\'d', 'they\'ll', 'they\'re', 'they\'ve', 'this', 'those', 'through', 'to', 'too',
    'under', 'until', 'up', 'very', 'was', 'wasn\'t', 'we', 'we\'d', 'we\'ll', 'we\'re', 'we\'ve',
    'were', 'weren\'t', 'what', 'what\'s', 'when', 'when\'s', 'where', 'where\'s', 'which', 'while',
    'who', 'who\'s', 'whom', 'why', 'why\'s', 'with', 'won\'t', 'would', 'wouldn\'t', 'you', 'you\'d',
    'you\'ll', 'you\'re', 'you\'ve', 'your', 'yours', 'yourself', 'yourselves'
}

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    # Checks if the response is successful and contains data before processing
    if resp.status != 200 or not resp.raw_response or not resp.raw_response.content:
        return list()
    
    content = resp.raw_response.content
    if len(content) > 5 * 1024 * 1024:  # 5MB limit
        print(f"Skipping large file: {url} ({len(content)} bytes)")
        return list()

    found_urls = set()

    # Uses BeautifulSoup with lxml to parse the HTML, resolve relative paths,
    # and removes fragments to ensure unique URL tracking.
    try:
        soup = BeautifulSoup(content, "lxml")
        
        # Remove script, style, and other non-content elements for text extraction
        for element in soup(["script", "style", "meta", "link", "noscript"]):
            element.decompose()
        
        # Extract text content for analytics
        text = soup.get_text(separator=' ', strip=True)
        
        words = re.findall(r'\b[a-z]{2,}\b', text.lower())
        
        # Filter out stop words
        filtered_words = [w for w in words if w not in STOP_WORDS]
        
        if len(filtered_words) < 50:
            print(f"Low information content: {url} ({len(filtered_words)} words)")
            return list()
        
        # === ANALYTICS COLLECTION ===
        
        # Defragment URL for uniqueness tracking
        defragged_url, _ = urldefrag(url)
        analytics['unique_pages'].add(defragged_url)
        
        # Track word count for this page
        word_count = len(filtered_words)
        analytics['word_counts'][defragged_url] = word_count
        
        analytics['all_words'].update(filtered_words)
        
        if word_count > analytics['longest_page']['word_count']:
            analytics['longest_page'] = {
                'url': defragged_url,
                'word_count': word_count
            }
        
        parsed = urlparse(url)
        if parsed.netloc.endswith('.uci.edu'):
            analytics['subdomains'][parsed.netloc] += 1
        

        if len(analytics['unique_pages']) % 100 == 0:
            save_analytics(analytics)
            print(f"Progress: {len(analytics['unique_pages'])} unique pages crawled")


        for link in soup.find_all('a', href=True):
            href = link['href'].strip()
            
            # Skip empty hrefs, javascript, mailto, etc.
            if not href or href == '#' or href.startswith(('javascript:', 'mailto:', 'tel:')):
                continue
            
            absolute_url = urljoin(url, href)
            clean_url, _ = urldefrag(absolute_url)

            found_urls.add(clean_url)

    except Exception as e:
        print(f"Error parsing content for {url}: {e}")
        return list()

    return list(found_urls)

def is_valid(url):

    try:
        parsed = urlparse(url)

        if parsed.scheme not in set(["http", "https"]):
            return False

        allowed_domains = [
            "ics.uci.edu", 
            "cs.uci.edu", 
            "informatics.uci.edu", 
            "stat.uci.edu"
        ]
        if not any(parsed.netloc.endswith(domain) for domain in allowed_domains):
            return False

        path_parts = [part for part in parsed.path.split('/') if part]
        for folder in path_parts:
            if path_parts.count(folder) >= 3:
                return False
        
        if len(url) > 150:
            return False
        
        query_params = parse_qs(parsed.query)
        
        for param_key in query_params.keys():
            param_lower = param_key.lower()
            if any(ui in param_lower for ui in ['tab', 'view', 'mode', 'do', 'action', 'sort', 'filter', 'page', 'display', 'show', 'format']):
                return False
        
        trap_params = ['date', 'cal', 'calendar', 'share', 'replytocom', 'print', 'offset', 'month', 'year', 'day']
        if any(param in query_params for param in trap_params):
            return False
        
        if len(query_params) > 3:
            return False
        
        trap_patterns = [
            r'/calendar/',
            r'/wp-json/',
            r'/feed/',
            r'/print/',
            r'/download/',
            r'/wp-content/uploads/',
        ]
        
        if any(re.search(pattern, parsed.path.lower()) for pattern in trap_patterns):
            return False
         
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())
    
    

    except TypeError:
        print ("TypeError for ", parsed)
        raise

def generate_report():
    """
    Generate the final report with analytics
    """
    save_analytics(analytics)
    
    report = []
    report.append("=" * 80)
    report.append("WEB CRAWLER REPORT")
    report.append("=" * 80)
    report.append("")
    
    report.append(f"1. Number of unique pages found: {len(analytics['unique_pages'])}")
    report.append("")
    
    report.append(f"2. Longest page (by word count):")
    report.append(f"   URL: {analytics['longest_page']['url']}")
    report.append(f"   Word count: {analytics['longest_page']['word_count']}")
    report.append("")
    

    report.append("3. 50 most common words:")
    most_common = analytics['all_words'].most_common(50)
    for i, (word, count) in enumerate(most_common, 1):
        report.append(f"   {i:2}. {word:20} - {count:6} occurrences")
    report.append("")
    

    report.append("4. Subdomains in uci.edu domain:")
    sorted_subdomains = sorted(analytics['subdomains'].items())
    for subdomain, count in sorted_subdomains:
        report.append(f"   {subdomain}, {count}")
    report.append("")
    
    report.append("=" * 80)
    report_text = "\n".join(report)
    with open("REPORT.txt", 'w') as f:
        f.write(report_text)
    
    print(report_text)
    print("\nReport saved to REPORT.txt")

if __name__ == "__main__":
    analytics = load_analytics()
    generate_report()

