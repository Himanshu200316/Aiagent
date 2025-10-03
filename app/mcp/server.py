from mcp.server.fastmcp import FastMCP
from typing import List, Optional

from ..storage import Storage
from ..scheduler import PostScheduler

server = FastMCP("ad-agent-mcp")
storage = Storage()
scheduler = PostScheduler(storage)


@server.tool()
def generate_ad(user_id: str, product_description: str, tone: str, target_audience: str, platforms: List[str]) -> dict:
    return scheduler.generate_and_post(user_id, product_description, tone, target_audience, platforms)


@server.tool()
def post_instagram(user_id: str, image_path: str, caption: str, as_story: bool = False) -> dict:
    cred = storage.load_credentials(user_id, "instagram")
    if not cred:
        return {"error": "missing_credentials"}
    from ..posters.instagram import InstagramPoster
    poster = InstagramPoster(cred)
    post_id = poster.post_story(image_path) if as_story else poster.post_feed(image_path, caption)
    return {"post_id": post_id}


@server.tool()
def post_twitter(user_id: str, image_path: str, caption: str) -> dict:
    cred = storage.load_credentials(user_id, "twitter")
    if not cred:
        return {"error": "missing_credentials"}
    from ..posters.twitter import TwitterPoster
    poster = TwitterPoster(cred)
    post_id = poster.post(image_path, caption)
    return {"post_id": post_id}


@server.tool()
def post_linkedin(user_id: str, image_url: str, caption: str) -> dict:
    cred = storage.load_credentials(user_id, "linkedin")
    if not cred:
        return {"error": "missing_credentials"}
    from ..posters.linkedin import LinkedInPoster
    poster = LinkedInPoster(cred)
    post_id = poster.post(image_url=image_url, caption=caption)
    return {"post_id": post_id}


if __name__ == "__main__":
    server.run()
