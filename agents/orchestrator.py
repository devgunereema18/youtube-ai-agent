"""
AI Video Agent Orchestrator
=============================
Coordinates the full pipeline:
1. VidIQ -> Topic research & prompt generation
2. HeyGen -> AI video creation
3. YouTube -> Video upload with optimized metadata
"""

import json
import os
import time
from typing import Optional
from config import Config
from agents.vidiq_agent import VidIQAgent
from agents.heygen_agent import HeyGenAgent
from agents.youtube_agent import YouTubeAgent


class VideoAgentOrchestrator:
    """
    Main orchestrator for the AI Video Pipeline.

    Workflow:
        1. Use VidIQ to research topics and generate video prompts
        2. Send the script to HeyGen AI to create the video
        3. Upload the rendered video to YouTube with optimized metadata
    """

    def __init__(self):
        self.vidiq = VidIQAgent()
        self.heygen = HeyGenAgent()
        self.youtube = YouTubeAgent()
        self.output_dir = Config.OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)

    def run_pipeline(
        self,
        topic: str,
        niche: str = "technology",
        style: str = "educational",
        avatar_id: Optional[str] = None,
        voice_id: Optional[str] = None,
        privacy_status: str = "private",
        auto_upload: bool = True,
    ) -> dict:
        """
        Execute the full video creation pipeline.

        Args:
            topic: The main video topic
            niche: Content niche for trending research
            style: Video style (educational, entertaining, tutorial, review)
            avatar_id: HeyGen avatar ID (optional)
            voice_id: HeyGen voice ID (optional)
            privacy_status: YouTube privacy status
            auto_upload: Whether to upload to YouTube automatically

        Returns:
            Dictionary with pipeline results
        """
        result = {
            "topic": topic,
            "status": "started",
            "steps": {},
            "timestamps": {"start": time.time()},
        }

        print("=" * 60)
        print("  AI VIDEO AGENT - PIPELINE STARTED")
        print("=" * 60)

        # STEP 1: VidIQ - Generate Video Prompt
        print("\n[STEP 1] VidIQ - Generating Video Prompt...")
        print("-" * 40)

        try:
            video_prompt = self.vidiq.generate_video_prompt(topic, style)
            result["steps"]["vidiq"] = {
                "status": "success",
                "title": video_prompt["title"],
                "seo_score": video_prompt["seo_score"],
                "tags_count": len(video_prompt["tags"]),
            }
            print(f"  Title: {video_prompt['title']}")
            print(f"  SEO Score: {video_prompt['seo_score']}/100")
            print(f"  Tags: {len(video_prompt['tags'])} generated")
            print(f"  Script Length: {len(video_prompt['script'])} characters")
        except Exception as e:
            print(f"  VidIQ Error: {e}")
            result["steps"]["vidiq"] = {"status": "failed", "error": str(e)}
            result["status"] = "failed"
            return result

        # STEP 2: HeyGen - Create AI Video
        print("\n[STEP 2] HeyGen - Creating AI Video...")
        print("-" * 40)

        try:
            create_result = self.heygen.create_video(
                script=video_prompt["script"],
                title=video_prompt["title"],
                avatar_id=avatar_id,
                voice_id=voice_id,
            )

            if "error" in create_result:
                raise Exception(create_result["error"])

            video_id = create_result["video_id"]
            print(f"  Video creation initiated. ID: {video_id}")

            print(f"  Waiting for video to render...")
            status_result = self.heygen.wait_for_video(video_id)

            if status_result["status"] != "completed":
                raise Exception(f"Video rendering failed: {status_result['status']}")

            video_path = self.heygen.download_video(status_result["video_url"])
            if not video_path:
                raise Exception("Failed to download rendered video")

            result["steps"]["heygen"] = {
                "status": "success",
                "video_id": video_id,
                "video_path": video_path,
                "video_url": status_result["video_url"],
                "duration": status_result.get("duration", 0),
            }
            print(f"  Video rendered and downloaded: {video_path}")

        except Exception as e:
            print(f"  HeyGen Error: {e}")
            result["steps"]["heygen"] = {"status": "failed", "error": str(e)}
            result["status"] = "failed"
            return result

        # STEP 3: YouTube - Upload Video
        if auto_upload:
            print("\n[STEP 3] YouTube - Uploading Video...")
            print("-" * 40)

            try:
                upload_result = self.youtube.upload_video(
                    video_path=video_path,
                    title=video_prompt["title"],
                    description=video_prompt["description"],
                    tags=video_prompt["tags"],
                    privacy_status=privacy_status,
                )

                if "error" in upload_result:
                    raise Exception(upload_result["error"])

                result["steps"]["youtube"] = {
                    "status": "success",
                    "video_id": upload_result["video_id"],
                    "url": upload_result["url"],
                    "privacy_status": privacy_status,
                }
                print(f"  Uploaded to YouTube!")
                print(f"  Video URL: {upload_result['url']}")

            except Exception as e:
                print(f"  YouTube Error: {e}")
                result["steps"]["youtube"] = {"status": "failed", "error": str(e)}
                result["status"] = "partial"
        else:
            print("\n[STEP 3] YouTube upload skipped (auto_upload=False)")
            result["steps"]["youtube"] = {"status": "skipped"}

        # PIPELINE SUMMARY
        result["timestamps"]["end"] = time.time()
        elapsed = result["timestamps"]["end"] - result["timestamps"]["start"]
        result["elapsed_seconds"] = round(elapsed, 2)

        if result["status"] != "failed":
            result["status"] = "completed"

        print(f"\n{'=' * 60}")
        print("  PIPELINE SUMMARY")
        print("=" * 60)
        print(f"  Topic: {topic}")
        print(f"  Status: {result['status']}")
        print(f"  Duration: {elapsed:.1f} seconds")
        for step_name, step_data in result["steps"].items():
            icon = "[OK]" if step_data["status"] == "success" else "[FAIL]"
            print(f"  {icon} {step_name}: {step_data['status']}")
        print("=" * 60)

        self._save_result(result)
        return result

    def run_batch(self, topics: list, **kwargs) -> list:
        """Run the pipeline for multiple topics."""
        results = []
        for i, topic in enumerate(topics, 1):
            print(f"\n{'#' * 60}")
            print(f"# BATCH JOB {i}/{len(topics)}: {topic}")
            print(f"{'#' * 60}")
            r = self.run_pipeline(topic=topic, **kwargs)
            results.append(r)
            if i < len(topics):
                print("\n  Waiting 30s before next job...")
                time.sleep(30)
        return results

    def _save_result(self, result: dict):
        """Save pipeline result to JSON file."""
        filename = f"pipeline_result_{int(time.time())}.json"
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\n  Results saved: {filepath}")
