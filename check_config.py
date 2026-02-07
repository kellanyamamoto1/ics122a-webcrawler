import re
import os
from configparser import ConfigParser

def check_config():
    """Validate the configuration file"""
    print("=" * 80)
    print("PRE-FLIGHT CONFIGURATION CHECKER")
    print("=" * 80)
    
    errors = []
    warnings = []
    
    # Check if config.ini exists
    if not os.path.exists("config.ini"):
        errors.append("config.ini file not found!")
        return errors, warnings
    config = ConfigParser()
    config.read("config.ini")
    
    # Check USERAGENT
    print("\n[1] Checking USERAGENT...")
    useragent = config["IDENTIFICATION"]["USERAGENT"].strip()
    
    if useragent == "DEFAULT AGENT":
        errors.append("USERAGENT is still set to 'DEFAULT AGENT'")
        errors.append("You MUST change this to: IR UW26 studentID1,studentID2,studentID3")
    elif "IR UW26" not in useragent:
        warnings.append("USERAGENT should start with 'IR UW26'")
    elif not re.search(r'\d+', useragent):
        warnings.append("USERAGENT should contain student IDs (numbers)")
    else:
        print(f"USERAGENT: {useragent}")
    
    # Check connection settings
    print("\n[2] Checking CONNECTION settings...")
    host = config["CONNECTION"]["HOST"]
    port = config["CONNECTION"]["PORT"]
    
    if host != "styx.ics.uci.edu":
        warnings.append(f"HOST is set to '{host}', expected 'styx.ics.uci.edu'")
    else:
        print(f"HOST: {host}")
    
    if port != "9000":
        warnings.append(f"PORT is set to '{port}', expected '9000'")
    else:
        print(f"PORT: {port}")
    
    print("\n[3] Checking SEED URLs...")
    seed_urls = config["CRAWLER"]["SEEDURL"].split(",")
    expected_seeds = [
        "https://www.ics.uci.edu",
        "https://www.cs.uci.edu",
        "https://www.informatics.uci.edu",
        "https://www.stat.uci.edu"
    ]
    
    for url in expected_seeds:
        if url in seed_urls:
            print(f"{url}")
        else:
            warnings.append(f"Missing seed URL: {url}")
    
    print("\n[4] Checking POLITENESS...")
    politeness = config["CRAWLER"]["POLITENESS"]
    if float(politeness) < 0.5:
        errors.append(f"POLITENESS is {politeness}, must be at least 0.5 seconds")
    else:
        print(f"POLITENESS: {politeness} seconds")
    
    # Check thread count
    print("\n[5] Checking THREADCOUNT...")
    thread_count = config["LOCAL PROPERTIES"]["THREADCOUNT"]
    if int(thread_count) > 1:
        warnings.append(f"THREADCOUNT is {thread_count}. Make sure you've implemented multithreading correctly!")
    else:
        print(f"THREADCOUNT: {thread_count}")
    
    # Check dependencies
    print("\n[6] Checking dependencies...")
    try:
        import bs4
        print("beautifulsoup4 installed")
    except ImportError:
        errors.append("beautifulsoup4 not installed. Run: pip install beautifulsoup4")
    
    try:
        import lxml
        print("lxml installed")
    except ImportError:
        errors.append("lxml not installed. Run: pip install lxml")

    try:
        import cbor
        print("cbor installed")
    except ImportError:
        errors.append("cbor not installed. Run: pip install cbor")
    
    try:
        import requests
        print("requests installed")
    except ImportError:
        errors.append("requests not installed. Run: pip install requests")
    
    # Check scraper.py
    print("\n[7] Checking scraper.py...")
    if os.path.exists("scraper.py"):
        with open("scraper.py", 'r') as f:
            content = f.read()
            
        # Check for forbidden imports
        if "import requests" in content or "from requests import" in content:
            errors.append("scraper.py should NOT import 'requests' directly")
        
        if "import urllib.request" in content or "from urllib.request import" in content:
            errors.append("scraper.py should NOT import 'urllib.request'")
        
        # Check for required imports
        if "from bs4 import" in content or "import BeautifulSoup" in content:
            print("BeautifulSoup imported")
        else:
            warnings.append("BeautifulSoup not imported in scraper.py")
        
        print("scraper.py exists")
    else:
        errors.append("scraper.py not found!")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if errors:
        print("\n ERRORS (must fix before running):")
        for i, error in enumerate(errors, 1):
            print(f"   {i}. {error}")
    
    if warnings:
        print("\nWARNINGS (review these):")
        for i, warning in enumerate(warnings, 1):
            print(f"   {i}. {warning}")
    
    if not errors and not warnings:
        print("\n✓ All checks passed! You're ready to run the crawler.")
        print("\nTo start crawling:")
        print("  python3 launch.py --restart")
    elif not errors:
        print("\n✓ No critical errors. You can proceed, but review the warnings.")
        print("\nTo start crawling:")
        print("  python3 launch.py --restart")
    else:
        print("\n Please fix the errors above before running the crawler.")
    
    print("\n" + "=" * 80)
    
    return errors, warnings

if __name__ == "__main__":
    errors, warnings = check_config()
    
    if errors:
        exit(1)
    else:
        exit(0)
