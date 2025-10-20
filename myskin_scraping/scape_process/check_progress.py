#!/usr/bin/env python3
"""
Quick progress checker for parallel scraping
"""

import os
import glob
import json

def check_progress():
    """Check current scraping progress"""
    print("📊 MySkinRecipes Parallel Scraper - Progress Check")
    print("=" * 60)

    # Check if scraper is running
    log_file = "scraping_log.txt"
    results_dir = "myskin_scraping/results"

    if os.path.exists(log_file):
        # Get file size to estimate progress
        log_size = os.path.getsize(log_file)
        print(f"📝 Log file: {log_size:,} bytes ({log_size/1024/1024:.1f} MB)")

        # Get latest progress from log
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Track completed categories and current progress
        total_categories_completed = 0
        current_categories = {}
        total_products_found = 0

        # Look for completion messages and current progress
        for line in lines:  # Check entire file for progress messages
            line = line.strip()

            # Count completed categories - format: "✅ CategoryName: X products | Progress: Y categories, Z total products"
            if "✅" in line and "Progress:" in line:
                try:
                    # Extract total progress from end of line
                    progress_part = line.split("Progress: ")[1]
                    completed_count = int(progress_part.split(" categories")[0])
                    total_products = int(progress_part.split(", ")[1].split(" total products")[0])

                    # Keep the highest numbers found (most recent)
                    total_categories_completed = max(total_categories_completed, completed_count)
                    total_products_found = max(total_products_found, total_products)
                except:
                    continue

            # Track current processing
            elif "🔄 Processing:" in line:
                try:
                    category_name = line.split("🔄 Processing: ")[1]
                    current_categories[category_name] = "Starting..."
                except:
                    continue

            # Track current product progress
            elif "Product" in line and "/" in line and "https://" in line:
                try:
                    parts = line.split("Product ")[1].split(":")[0]
                    current, total = parts.split("/")

                    # Extract category from URL
                    if "/shop/th/" in line:
                        url_part = line.split("/shop/th/")[1]
                        category = url_part.split("/")[0].replace("-", " ").replace("amp", "&")

                        current_categories[category] = f"{current}/{total} ({int(current)/int(total)*100:.1f}%)"
                except:
                    continue

        # Load total categories for comparison
        total_categories = 1570  # We know this from the file
        try:
            import json
            with open("myskin_scraping/results/discovered_categories.json", 'r') as f:
                all_cats = json.load(f)
                total_categories = len(all_cats)
        except:
            pass

        print(f"\n📊 SCRAPING PROGRESS SUMMARY:")
        print(f"   ✅ Completed categories: {total_categories_completed}/{total_categories} ({total_categories_completed/total_categories*100:.1f}%)")
        print(f"   📦 Products found: {total_products_found:,}")
        print(f"   🔄 Currently processing: {len(current_categories)} categories")

        if current_categories:
            print(f"\n🔄 Current Active Categories:")
            # Show up to 8 most recent
            recent_categories = list(current_categories.items())[-8:]
            for category, progress in recent_categories:
                print(f"   {category}: {progress}")

        # Progress estimates
        remaining_categories = total_categories - total_categories_completed
        avg_products_per_category = total_products_found / total_categories_completed if total_categories_completed > 0 else 6.5
        estimated_final_products = int(total_categories * avg_products_per_category)

        print(f"\n📈 Progress Analysis:")
        print(f"   Categories remaining: {remaining_categories:,}")
        print(f"   Average products/category: {avg_products_per_category:.1f}")
        print(f"   Estimated final total: ~{estimated_final_products:,} products")

        # Time estimates
        if total_categories_completed > 50:  # Only estimate if we have decent sample
            categories_per_hour = total_categories_completed / (len(lines) / 3600) if len(lines) > 3600 else 0
            if categories_per_hour > 0:
                hours_remaining = remaining_categories / categories_per_hour
                print(f"   Estimated time remaining: {hours_remaining:.1f} hours")

    # Check for result files
    if os.path.exists(results_dir):
        result_files = glob.glob(f"{results_dir}/*.json")
        if result_files:
            print(f"\n💾 Result Files Found:")
            for file_path in result_files:
                file_size = os.path.getsize(file_path)
                filename = os.path.basename(file_path)
                print(f"   📄 {filename}")
                print(f"   📊 Size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")

                # Try to count products
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        print(f"   📦 Products: {len(data)}")
                except:
                    print(f"   📦 Products: Still writing...")
        else:
            print(f"\n📂 Results directory exists but no files yet")
            print(f"   Location: {os.path.abspath(results_dir)}")
    else:
        print(f"\n📂 Results will be saved to:")
        print(f"   {os.path.abspath('myskin_scraping/results/')}")

    # Process summary
    total_lines = len(lines) if 'lines' in locals() else 0
    print(f"\n📈 Summary:")
    print(f"   📝 Log entries: {total_lines:,}")
    print(f"   🔄 Status: {'Running' if total_lines > 100 else 'Starting/Completed'}")
    print(f"   💾 Save location: myskin_scraping/results/")

if __name__ == "__main__":
    check_progress()