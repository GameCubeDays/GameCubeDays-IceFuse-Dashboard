import sys
import os

# --- Add the 'src' directory to the Python path ---
# This is one way to fix the 'ModuleNotFound' error
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from gmod_stat_tracker.pipeline import scrape_and_merge_data
from gmod_stat_tracker.visualizations import generate_all_graphs
from gmod_stat_tracker.config import (
    BRANCH_PIVOT_OUTPUT_PATH, 
    SUBBRANCH_PIVOT_OUTPUT_PATH, 
    US_PIVOT_OUTPUT_PATH
)

def main():
    """
    Main entry point for the GMod Stat Tracker.
    
    1. Runs the data scraping and processing pipeline.
    2. Generates all visualization graphs.
    """
    print("="*60)
    print("🚀 STARTING GMOD STAT TRACKER")
    print("="*60)
    
    try:
        # Step 1: Run the data pipeline
        scrape_and_merge_data()
        
        print("\nPipeline complete. Proceeding to graph generation...")

        # Step 2: Run the graph generation
        generate_all_graphs(
            branch_pivots_csv=BRANCH_PIVOT_OUTPUT_PATH,
            subbranch_pivots_csv=SUBBRANCH_PIVOT_OUTPUT_PATH,
            us_pivots_csv=US_PIVOT_OUTPUT_PATH
        )

        print("\n" + "="*60)
        print("✅ GMOD STAT TRACKER FINISHED SUCCESSFULLY!")
        print("="*60)

    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ AN ERROR OCCURRED: {e}")
        print("="*60)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()