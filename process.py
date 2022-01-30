import os
import time
from multiprocessing import Pool
from typing import List, TypedDict

# pip install feedparser requests
import feedparser
import requests


class Author(TypedDict):
    name: str


class SummaryDetail(TypedDict):
    type: str
    language: None
    base: str
    value: str


class Image(TypedDict):
    href: str


class Link(TypedDict):
    type: str
    href: str
    rel: str
    # length: Optional[int] = None


class Entry(TypedDict):
    links: List[Link]
    title: str
    title_detail: SummaryDetail
    id: str
    guidislink: bool
    link: str
    authors: List[Author]
    author: str
    author_detail: Author
    itunes_duration: str
    itunes_explicit: None
    itunes_season: int
    podcast_season: int
    itunes_episode: int
    podcast_episode: int
    itunes_episodetype: str
    image: Image
    summary: str
    summary_detail: SummaryDetail
    content: List[SummaryDetail]
    published: str
    published_parsed: List[int]


MAX_RETRY = 3


def save_retry_download(url: str, save_path: str) -> bool:
    retry_times = 0
    while retry_times <= MAX_RETRY:
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(save_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            return True
        except Exception:
            print("failed")
            retry_times += 1
            time.sleep(retry_times * retry_times)
            continue
    return False


TPL = """# {title}

<figure>
    <figcaption></figcaption>
    <audio
        controls
        src="./audio.mp3">
            Your browser does not support the
            <code>audio</code> element.
    </audio>
</figure>

{content}
"""

TPL_WITH_BG = """# {title}

![](./image.jpeg)

<figure>
    <figcaption></figcaption>
    <audio
        controls
        src="./audio.mp3">
            Your browser does not support the
            <code>audio</code> element.
    </audio>
</figure>

{content}
"""


def download_and_save(entry: Entry):
    url = ""
    for link in entry["links"]:
        if link["type"] == "audio/mpeg":
            url = link["href"]
            break
    if url == "":
        return
    date = "-".join([str(i) for i in entry["published_parsed"][:3]])
    clean_title = entry["title"].replace("/", "_")
    file_dir = f"{date}_{clean_title}"
    if not os.path.isdir(file_dir):
        os.mkdir(file_dir)

    local_filename = f"{file_dir }/audio.mp3"
    if not os.path.exists(local_filename):
        ok = save_retry_download(url, local_filename)
        if not ok:
            print(f"failed to download {url} to {local_filename}")

    try:
        bg_url = entry["image"]["href"]
    except Exception:
        bg_url = ""
    local_cover_bg = f"{file_dir }/image.jpeg"
    if bg_url != "" and not os.path.exists(local_cover_bg):
        ok = save_retry_download(bg_url, local_cover_bg)
        if not ok:
            print(f"failed to download {bg_url} to {local_cover_bg}")

    if bg_url == "":
        readme = TPL.format(title=clean_title, content=entry["content"][0]["value"])
    else:
        readme = TPL_WITH_BG.format(title=clean_title, content=entry["content"][0]["value"])
    with open(f"{file_dir}/README.md", "w") as f:
        f.write(readme)


if __name__ == "__main__":
    with Pool() as p:
        d = feedparser.parse("https://loudmurmursfm.com/feed/audio.xml")
        p.map(download_and_save, d["entries"])
