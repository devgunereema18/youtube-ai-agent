#!/usr/bin/env python3
"""
AI Video Agent - Main Entry Point
===================================
Automated pipeline for creating and publishing YouTube videos:
  1. VidIQ: Research topics & generate optimized video prompts
  2. HeyGen AI: Create professional AI avatar videos
  3. YouTube: Upload with SEO-optimized metadata

Usage:
    python main.py --topic "Artificial Intelligence" --style educational
    python main.py --topic "Python Tips" --niche programming --privacy public
    python main.py --batch topics.txt
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from agents.orchestrator import VideoAgentOrchestrator


def main():
    parser = argparse.ArgumentParser(
        description="AI Video Agent - Automate YouTube Video Creation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --topic "Machine Learning Basics" --style educational
  python main.py --topic "Fitness Tips" --niche fitness --style entertaining
  python main.py --topic "Python Tutorial" --privacy public --no-upload
  python main.py --batch topics.txt --niche technology
        """,
    )

    parser.add_argument("--topic", type=str, help="Video topic")
    parser.add_argument("--batch", type=str, help="Path to topics file (one per line)")
    parser.add_argument("--niche", type=str, default="technology",
                        help="Content niche (default: technology)")
    parser.add_argument("--style", type=str, default="educational",
                        choices=["educational", "entertaining", "tutorial", "review"],
                        help="Video style (default: educational)")
    parser.add_argument("--avatar", type=str, default=None,
                        help="HeyGen avatar ID")
    parser.add_argument("--voice", type=str, default=None,
                        help="HeyGen voice ID")
    parser.add_argument("--privacy", type=str, default="private",
                        choices=["private", "unlisted", "public"],
                        help="YouTube privacy (default: private)")
    parser.add_argument("--no-upload", action="store_true",
                        help="Skip YouTube upload")
    parser.add_argument("--list-avatars", action="store_true",
                        help="List available HeyGen avatars")
    parser.add_argument("--list-voices", action="store_true",
                        help="List available HeyGen voices")
    parser.add_argument("--validate", action="store_true",
                        help="Validate API key configuration")

    args = parser.parse_args()

    # Validate Configuration
    if args.validate:
        print("Validating configuration...")
        try:
            Config.validate()
            print("All API keys are configured!")
        except EnvironmentError as e:
            print(f"Error: {e}")
            sys.exit(1)
        return

    # List Avatars
    if args.list_avatars:
        from agents.heygen_agent import HeyGenAgent
        agent = HeyGenAgent()
        avatars = agent.list_avatars()
        print(f"\nAvailable Avatars ({len(avatars)}):")
        for avatar in avatars[:20]:
            print(f"  - {avatar.get('avatar_id', 'N/A')} | {avatar.get('avatar_name', 'Unknown')}")
        return

    # List Voices
    if args.list_voices:
        from agents.heygen_agent import HeyGenAgent
        agent = HeyGenAgent()
        voices = agent.list_voices()
        print(f"\nAvailable Voices ({len(voices)}):")
        for voice in voices[:20]:
            print(f"  - {voice.get('voice_id', 'N/A')} | {voice.get('name', 'Unknown')} | {voice.get('language', 'N/A')}")
        return

    # Run Pipeline
    if not args.topic and not args.batch:
        parser.print_help()
        print("\nError: Provide --topic or --batch to start the pipeline.")
        sys.exit(1)

    try:
        Config.validate()
    except EnvironmentError as e:
        print(f"Configuration Error:\n{e}")
        print("\nCopy .env.example to .env and fill in your API keys.")
        sys.exit(1)

    orchestrator = VideoAgentOrchestrator()

    if args.batch:
        if not os.path.exists(args.batch):
            print(f"Batch file not found: {args.batch}")
            sys.exit(1)
        with open(args.batch, "r") as f:
            topics = [line.strip() for line in f if line.strip()]
        if not topics:
            print("No topics found in batch file.")
            sys.exit(1)
        print(f"Batch mode: {len(topics)} topics loaded")
        results = orchestrator.run_batch(
            topics=topics, niche=args.niche, style=args.style,
            avatar_id=args.avatar, voice_id=args.voice,
            privacy_status=args.privacy, auto_upload=not args.no_upload,
        )
        success = sum(1 for r in results if r["status"] == "completed")
        print(f"\nBatch Complete: {success}/{len(results)} successful")
    else:
        result = orchestrator.run_pipeline(
            topic=args.topic, niche=args.niche, style=args.style,
            avatar_id=args.avatar, voice_id=args.voice,
            privacy_status=args.privacy, auto_upload=not args.no_upload,
        )
        if result["status"] == "completed":
            print("\nPipeline completed successfully!")
            if "youtube" in result["steps"] and result["steps"]["youtube"].get("url"):
                print(f"Watch your video: {result['steps']['youtube']['url']}")
        else:
            print(f"\nPipeline finished with status: {result['status']}")
            sys.exit(1)


if __name__ == "__main__":
    main()
