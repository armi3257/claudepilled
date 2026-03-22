#!/usr/bin/env python3
"""
Local TikTok slideshow uploader.
Opens a visible browser with a persistent profile.
Waits at every step — never closes until YOU tell it to.
"""

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERROR: playwright not installed. Run: pip install playwright && python -m playwright install chromium")
    sys.exit(1)


def post_slideshow(image_paths: list, caption: str, hashtags: list):
    full_caption = f"{caption}\n\n{' '.join(hashtags)}"
    user_data_dir = os.path.join(os.path.expanduser("~"), ".tiktok-poster-profile")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1280, "height": 720},
        )

        page = context.pages[0] if context.pages else context.new_page()

        try:
            # Step 1: Go to TikTok
            print("\n[Step 1] Opening TikTok...")
            page.goto("https://www.tiktok.com", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)

            # Step 2: Login check — WAIT as long as needed
            print("\n[Step 2] Check the browser window.")
            print("  If you're NOT logged in:")
            print("    - Log into @claudepilled")
            print("    - Complete any verification codes")
            print("    - Wait until you see the TikTok feed")
            print("  If you ARE already logged in, just continue.")
            input("\n  >>> Press Enter here when you're logged in and see the feed...\n")

            # Step 3: Navigate to upload — try multiple URLs
            print("[Step 3] Going to upload page...")
            upload_urls = [
                "https://www.tiktok.com/tiktokstudio/upload",
                "https://www.tiktok.com/creator#/upload",
                "https://www.tiktok.com/upload",
            ]
            for url in upload_urls:
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=15000)
                    page.wait_for_timeout(3000)
                    # Check if we actually landed on an upload page
                    if "upload" in page.url.lower() or "studio" in page.url.lower() or "creator" in page.url.lower():
                        print(f"  Loaded: {page.url}")
                        break
                except:
                    continue

            print("  If the upload page didn't load, navigate to it manually in the browser.")
            print("  You can click the Upload/+ button on TikTok, or go to tiktok.com/upload")
            input("  >>> Press Enter when you're on the upload page...\n")

            # Step 4: Switch to photo mode
            print("[Step 4] Looking for Photo/Carousel mode...")
            switched = False
            for label in ["Photo", "Carousel", "Photos"]:
                try:
                    tab = page.locator(f'text="{label}"').first
                    if tab.is_visible(timeout=2000):
                        tab.click()
                        page.wait_for_timeout(2000)
                        print(f"  Switched to {label} mode")
                        switched = True
                        break
                except:
                    continue

            if not switched:
                print("  Could not find Photo/Carousel tab automatically.")
                print("  Please click it manually in the browser if needed.")
                input("  >>> Press Enter when you're in photo/slideshow upload mode...\n")

            # Step 5: Upload images
            print(f"[Step 5] Uploading {len(image_paths)} slides...")
            try:
                file_input = page.locator('input[type="file"]').first
                file_input.set_input_files(image_paths)
                page.wait_for_timeout(5000)
                print("  Images uploaded!")
            except Exception as e:
                print(f"  Auto-upload failed: {e}")
                print("  Please drag the images into the browser manually.")

            input("  >>> Press Enter when all slides are uploaded and visible...\n")

            # Step 6: Caption
            print("[Step 6] Adding caption...")
            caption_added = False
            for selector in ['[contenteditable="true"]', '[data-e2e="upload-caption"]', '.public-DraftEditor-content']:
                try:
                    box = page.locator(selector).first
                    if box.is_visible(timeout=2000):
                        box.click()
                        page.keyboard.press("Control+a")
                        page.keyboard.press("Backspace")
                        page.wait_for_timeout(300)
                        page.keyboard.type(full_caption, delay=15)
                        print("  Caption typed!")
                        caption_added = True
                        break
                except:
                    continue

            if not caption_added:
                print("  Could not find caption box automatically.")
                print(f"  Please paste this caption manually:\n\n{full_caption}\n")

            input("  >>> Press Enter when the caption looks correct...\n")

            # Step 7: Review
            print("=" * 50)
            print("[Step 7] REVIEW YOUR POST in the browser.")
            print("  - Check slides are in the right order")
            print("  - Check caption and hashtags")
            print("  - Make any manual adjustments")
            print("=" * 50)
            input("\n  >>> Press Enter to POST (or Ctrl+C to cancel)...\n")

            # Step 8: Post
            print("[Step 8] Clicking Post...")
            posted = False
            for selector in ['button:has-text("Post")', '[data-e2e="upload-btn"]', 'button:has-text("Publish")']:
                try:
                    btn = page.locator(selector).first
                    if btn.is_visible(timeout=2000):
                        btn.click()
                        posted = True
                        print("  Post button clicked!")
                        break
                except:
                    continue

            if not posted:
                print("  Could not find Post button automatically.")
                print("  Please click Post/Publish manually in the browser.")

            input("  >>> Press Enter after the post is published...\n")
            print("\n✓ Done! Check @claudepilled to verify it's live.")

        except KeyboardInterrupt:
            print("\n\nCancelled. Browser stays open — close it manually when ready.")
            input("Press Enter to exit the script...\n")
        except Exception as e:
            print(f"\n✗ Error: {e}")
            debug_path = f"tiktok_debug_{int(time.time())}.png"
            try:
                page.screenshot(path=debug_path)
                print(f"  Debug screenshot saved to {debug_path}")
            except:
                pass
            print("\n  Browser stays open. You can finish manually.")
            input("  Press Enter to exit the script...\n")
        finally:
            context.close()


def main():
    parser = argparse.ArgumentParser(description="Post slideshow to TikTok (local)")
    parser.add_argument("--images", required=True, help="Directory containing slide images")
    parser.add_argument("--caption", required=True, help="Post caption")
    parser.add_argument("--hashtags", default="", help="Space-separated hashtags")
    args = parser.parse_args()

    image_dir = Path(args.images)
    image_paths = sorted(image_dir.glob("slide_*.png"))
    if not image_paths:
        image_paths = sorted(image_dir.glob("*.png"))
    if not image_paths:
        image_paths = sorted(image_dir.glob("*.jpg"))
    if not image_paths:
        print(f"No images found in {args.images}")
        sys.exit(1)

    image_paths = [str(p) for p in image_paths]
    print(f"Found {len(image_paths)} slides: {[os.path.basename(p) for p in image_paths]}")

    hashtag_list = args.hashtags.split() if args.hashtags else []
    post_slideshow(image_paths, args.caption, hashtag_list)


if __name__ == "__main__":
    main()
