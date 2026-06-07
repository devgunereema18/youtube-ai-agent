"""
VidIQ Agent Module
==================
Uses VidIQ API to research trending topics, generate optimized video prompts,
titles, descriptions, and tags for YouTube content.
"""

import requests
from typing import Optional
from config import Config


class VidIQAgent:
    """Handles VidIQ integration for video prompt and metadata generation."""

    def __init__(self):
        self.api_key = Config.VIDIQ_API_KEY
        self.base_url = Config.VIDIQ_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def get_trending_topics(self, niche: str, count: int = 5) -> list:
        """Fetch trending topics from VidIQ for a given niche."""
        try:
            response = requests.get(
                f"{self.base_url}/keywords/trending",
                headers=self.headers,
                params={"query": niche, "limit": count},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
        except requests.exceptions.RequestException as e:
            print(f"[VidIQ] Error fetching trending topics: {e}")
            return [{"keyword": niche, "score": 0}]

    def get_keyword_stats(self, keyword: str) -> dict:
        """Get search volume and competition data for a keyword."""
        try:
            response = requests.get(
                f"{self.base_url}/keywords/stats",
                headers=self.headers,
                params={"keyword": keyword},
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[VidIQ] Error fetching keyword stats: {e}")
            return {"keyword": keyword, "search_volume": "N/A", "competition": "N/A"}

    def generate_video_prompt(self, topic: str, style: str = "educational") -> dict:
        """
        Generate a complete video prompt including title, description, script,
        and tags optimized for YouTube SEO.
        """
        keyword_data = self.get_keyword_stats(topic)
        video_prompt = self._build_video_prompt(topic, style, keyword_data)
        print(f"[VidIQ] Generated video prompt for topic: '{topic}'")
        return video_prompt

    def _build_video_prompt(self, topic: str, style: str, keyword_data: dict) -> dict:
        """Build comprehensive video prompt with SEO optimization."""
        title = self._generate_title(topic, style)
        description = self._generate_description(topic, style)
        tags = self._generate_tags(topic, keyword_data)
        script = self._generate_script(topic, style)
        return {
            "topic": topic,
            "style": style,
            "title": title,
            "description": description,
            "tags": tags,
            "script": script,
            "keyword_data": keyword_data,
            "seo_score": self._calculate_seo_score(title, description, tags),
        }

    def _generate_title(self, topic: str, style: str) -> str:
        """Generate an SEO-optimized YouTube title."""
        style_prefixes = {
            "educational": "Learn",
            "entertaining": "You Won't Believe",
            "tutorial": "How To",
            "review": "Honest Review:",
        }
        prefix = style_prefixes.get(style, "")
        title = f"{prefix} {topic} - Complete Guide {self._get_year()}"
        return title[:70]

    def _generate_description(self, topic: str, style: str) -> str:
        """Generate a YouTube-optimized description."""
        return (
            f"In this video, we dive deep into {topic}.\n\n"
            f"Whether you're a beginner or experienced, this {style} video "
            f"will help you understand everything about {topic}.\n\n"
            f"Key Topics Covered:\n"
            f"- What is {topic}?\n"
            f"- Why {topic} matters in today's world\n"
            f"- Practical tips and insights\n"
            f"- Expert recommendations\n\n"
            f"Don't forget to Like, Subscribe, and hit the Bell icon!\n\n"
            f"#{''.join(topic.split())} #YouTube #AI"
        )

    def _generate_tags(self, topic: str, keyword_data: dict) -> list:
        """Generate optimized YouTube tags."""
        return [
            topic.lower(),
            f"{topic} tutorial",
            f"{topic} explained",
            f"{topic} {self._get_year()}",
            f"learn {topic}",
            f"{topic} tips",
            f"{topic} for beginners",
            "ai generated",
        ][:15]

    def _generate_script(self, topic: str, style: str) -> str:
        """Generate a video script suitable for HeyGen AI avatar."""
        return (
            f"Hey everyone! Welcome back to the channel. "
            f"Today, we're going to talk about {topic}. "
            f"This is something that's been getting a lot of attention lately, "
            f"and I want to break it down for you in a simple, easy-to-understand way.\n\n"
            f"First, let me explain what {topic} is all about. "
            f"It's a fascinating subject that impacts many areas of our lives. "
            f"Whether you're just hearing about this for the first time, "
            f"or you've been following it for a while, "
            f"I promise you'll learn something new today.\n\n"
            f"Now, let me share the key points you need to know. "
            f"There are several important aspects of {topic} that make it "
            f"particularly relevant right now. "
            f"The technology and landscape around this topic is evolving rapidly, "
            f"and staying informed is crucial.\n\n"
            f"To wrap up, {topic} is definitely something to keep an eye on. "
            f"If you found this video helpful, please give it a thumbs up "
            f"and subscribe to the channel for more content like this. "
            f"Drop a comment below telling me what you'd like to learn about next. "
            f"Thanks for watching, and I'll see you in the next video!"
        )

    def _calculate_seo_score(self, title: str, description: str, tags: list) -> int:
        """Calculate a basic SEO score (0-100)."""
        score = 0
        if 50 <= len(title) <= 70:
            score += 30
        elif 30 <= len(title) < 50:
            score += 20
        if len(description) > 200:
            score += 30
        elif len(description) > 100:
            score += 15
        if 8 <= len(tags) <= 15:
            score += 25
        elif 5 <= len(tags) < 8:
            score += 15
        if "2024" in title or "2025" in title or "2026" in title:
            score += 15
        return min(score, 100)

    def _get_year(self) -> str:
        """Get current year string."""
        from datetime import datetime
        return str(datetime.now().year)
