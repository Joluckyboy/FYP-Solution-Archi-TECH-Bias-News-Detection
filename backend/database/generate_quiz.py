#!/usr/bin/env python3
"""
Generate Balanced Quiz Questions (20 per category)
Distributes questions equally across: bias, sentiment, emotion, propaganda, personality
"""

import requests
import time
import json
from datetime import datetime
from typing import List, Dict

# Configuration
API_URL = "http://localhost:8010"
CATEGORIES = ["bias", "sentiment", "emotion", "propaganda", "personality"]
QUESTIONS_PER_CATEGORY = 10
BATCH_SIZE = 5  # Questions per API call
DELAY = 1.0     # seconds between batches


class BalancedQuizGenerator:
    def __init__(self, api_url: str = API_URL, categories: List[str] = None, per_category: int = QUESTIONS_PER_CATEGORY):
        self.api_url = api_url
        self.categories = categories or CATEGORIES
        self.per_category = per_category
        self.batches_per_category = per_category // BATCH_SIZE
        self.successful = 0
        self.failed = 0
        self.total_questions = 0
        self.results = {cat: [] for cat in self.categories}
        self.DELAY = DELAY
        
    def check_api_health(self) -> bool:
        """Check if API is running"""
        try:
            for path in ("/", "/application"):
                try:
                    response = requests.get(f"{self.api_url}{path}", timeout=5)
                    if response.status_code == 200:
                        return True
                except Exception:
                    continue
            return False
        except Exception as e:
            print(f"API Health Check Failed: {e}")
            return False
    
    def generate_batch_for_category(self, category: str, batch_num: int) -> bool:
        """Generate one batch of questions for a specific category"""
        try:
            # All categories now use the same AI generator endpoint
            url = f"http://localhost:8011/database/quiz/generate-and-save?question_type={category}"
            
            response = requests.post(url, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                quiz_ids = data.get('quiz_ids', [])
                self.results[category].extend(quiz_ids)
                self.total_questions += len(quiz_ids)
                self.successful += 1
                return True
            else:
                print(f"  Status: {response.status_code}")
                self.failed += 1
                return False
                
        except requests.Timeout:
            print(f"  Timeout (API too slow)")
            self.failed += 1
            return False
        except Exception as e:
            print(f"  Error: {str(e)}")
            self.failed += 1
            return False
    
    def run(self):
        """Run the full generation process"""
        print("\n" + "=" * 70)
        print("Balanced Quiz Generator - Equal Distribution")
        print("=" * 70)
        print(f"API URL: {self.api_url}")
        print(f"Categories: {', '.join(self.categories)}")
        print(f"Questions per category: {self.per_category}")
        print(f"Total expected: {len(self.categories) * self.per_category} questions")
        print("=" * 70)
        
        # Step 1: Check API health
        print("\n[Step 1/3] Checking API Health...", end=" ")
        if not self.check_api_health():
            print("FAILED")
            print("\nBackend API is not running!")
            print("Start with: docker compose up -d")
            return False
        print("OK")
        
        # Step 2: Generate questions for each category
        print("\n[Step 2/3] Generating Balanced Questions...")
        print("-" * 70)
        
        start_time = time.time()
        # All categories now use AI: 5 categories * 4 batches = 20 total
        total_batches = len(self.categories) * self.batches_per_category
        current_batch = 0
        
        for category in self.categories:
            print(f"\n {category.upper()}:")
            # All categories use AI now, so all use the same batch size
            batches_for_category = self.batches_per_category
            for i in range(batches_for_category):
                current_batch += 1
                print(f"    [{current_batch:2d}/{total_batches}] Batch {i+1} ", end="")
                
                success = self.generate_batch_for_category(category, i+1)
                
                if success:
                    count = len(self.results[category])
                    print(f"Success ({count} total)")
                else:
                    print(f"Failed")
                
                # Don't delay on last batch
                if current_batch < total_batches:
                    time.sleep(self.DELAY)
        
        elapsed = time.time() - start_time
        
        # Step 3: Display results
        print("\n[Step 3/3] Generation Complete!")
        print("=" * 70)
        print(f"Successful batches: {self.successful}/{total_batches}")
        print(f"Failed batches: {self.failed}/{total_batches}")
        print(f"Total questions generated: {self.total_questions}")
        print(f"Time elapsed: {elapsed:.1f} seconds")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nBreakdown by category:")
        for cat in self.categories:
            print(f"  • {cat:12} : {len(self.results[cat]):3d} questions")
        print("=" * 70)
        
        if self.successful == total_batches:
            print("\nAll questions generated successfully!")
            return True
        else:
            print(f"\n{self.failed} batches failed. Some questions may not have been generated.")
            return False
    
    def set_delay(self, seconds: float):
        """Set delay between batches"""
        self.DELAY = seconds


def main():
    """Main entry point"""
    
    # Create generator for balanced distribution
    generator = BalancedQuizGenerator(
        per_category=QUESTIONS_PER_CATEGORY
    )
    
    # Run generation
    success = generator.run()
    
    # Summary
    if success:
        print("\nNext Steps:")
        print("   1. Refresh frontend: npm run dev or reload browser")
        print("   2. Open Chrome extension")
        print("   3. Click into each game and verify questions load")
        print("   4. All 5 games should now have balanced questions!")
    else:
        print("\nSome issues occurred. Check the output above.")


if __name__ == "__main__":
    main()
