import requests
import time
import json
from datetime import datetime,timezone
from dateutil import parser

BASE_URL = "https://discourse.onlinedegree.iitm.ac.in"
CATEGORY_SLUG = "courses/tds-kb"
CATEGORY_ID = 34  # You can confirm this from the category JSON

# Date range for filtering
START_DATE = datetime(2025, 1, 1, tzinfo=timezone.utc)
END_DATE = datetime(2025, 4, 14, tzinfo=timezone.utc)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "cookie":"_t=45LOjl4wSiVfEe%2FOc0IhVQ4yfQiWY%2F6yg187PcWfvURS7IaqW53L1PZd5t6x3I2oUvNp1C3CQOnssdsm8RgOng1gYy9Gtt6ry%2BoBKu8nofrnaXkuluJZUxw8tWRl8aymCcd%2BOsoFZ7K2LFHKBGXHtVDyiIU6TCTBHdmZQu3zf23UCaVe2SbWt6vFLlMT9iztLaWXrgmZ0scDuosmEGLCWKQ4ZfGLJn8iURpEEkmsHiaOlNkZzAMuigXWMbP29wXHf9ejrLWegPkD%2F4Q6Ta3xZC%2BPPJYo94nWJCSZUAVzVhY%2BUUP6NyAkL1RTSiAK1KQaC3RVig%3D%3D--w4ebGIop32r421eQ--OwCg%2BZxbRiLHBIGhF1UJVw%3D%3D; _bypass_cache=true; _forum_session=GuQ%2FbJXMHvjeURhzFxRDi7mgOh0uem0TbJS5xWMbm%2FT9QqBGSVRwVoeg%2FuKgIxdRejaGElU8WJ6FTQTlcoBb7JqSjdW7hT1ZrfPKXrJp1uVJIF1FfWZTLFaXgR1yJnDB2ewjhyVE9NhhXUc%2Fs824PLgb8Sa9dKv2MLEAn%2BOB36vriC8cXbw9p2pM9QsAp5zECskK4HH3vG%2F5GAolOEkyxRkkcxVPgkYzoYo424k%2BQCXePfJM4GXDYrXPJWZczVKO%2FMQOIr7KI2QjYqUQ%2BWSOAvt4kNSkbcPFZq7Q33FTRn8Oy6q5NdFeI3bUvjHPJCJCr4qv7A1Aznw5DvRJFUy7Zu%2BgxdaUePpvgSqQQRMXMYv3sm3ehZFxY3zC0uMBTw%3D%3D--9BLhGW4T%2BptzPusX--jkCcOQ%2FvMEtAmSZtA%2B9mfg%3D%3D"
}

def get_all_topic_ids():
    topic_ids = []
    page = 0
    print("Fetching topics...")
    while True:
        url = f"{BASE_URL}/c/{CATEGORY_SLUG}/{CATEGORY_ID}.json?page={page}"
        print(f"Trying page {page}: {url}")
        try:
            res = requests.get(url, headers=headers)
            if res.status_code != 200:
                print(f"Failed to fetch page {page} | Status code: {res.status_code}")
                break

            data = res.json()
            topics = data.get("topic_list", {}).get("topics", [])
            if not topics:
                print("No more topics.")
                break

            for topic in topics:
                created_at =  parser.isoparse(topic['created_at']) 
                if START_DATE <= created_at <= END_DATE:
                    topic_ids.append(topic["id"])
            page += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"Error on page {page}: {e}")
            break
    print(f"Total topics found: {len(topic_ids)}")
    return topic_ids

def fetch_topic_content(topic_id):
    url = f"{BASE_URL}/t/{topic_id}.json"
    print(f"Fetching topic {topic_id}...")
    try:
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            print(f"Failed to fetch topic {topic_id} | Status code: {res.status_code}")
            return None
        data = res.json()
        content = []
        for post in data.get("post_stream", {}).get("posts", []):
            content.append(post["cooked"])
        return {
            "title": data.get("title", ""),
            "content": "\n\n".join(content),
            "url": f"{BASE_URL}/t/{topic_id}"
        }
    except Exception as e:
        print(f"Error fetching topic {topic_id}: {e}")
        return None

def save_all_topics():
    topic_ids = get_all_topic_ids()
    if not topic_ids:
        print("No topic IDs fetched.")
        return

    with open("discourse_posts.jsonl", "w", encoding="utf-8") as f:
        for tid in topic_ids:
            post = fetch_topic_content(tid)
            if post:
                f.write(json.dumps(post) + "\n")
                print(f" Saved: {post['title']}")
            else:
                print(f" Skipped topic {tid}")

if __name__ == "__main__":
    save_all_topics()
