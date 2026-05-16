import json
import statistics
import os

def run_chasing_majors_engine():
    # Load the raw inputs pasted into the repo
    if not os.path.exists('raw_odds.json'):
        print("Error: raw_odds.json not found in repository.")
        return
        
    with open('raw_odds.json', 'r') as f:
        data = json.load(f)

    skus = data['skus']
    parallels = data['parallels']
    
    # Calculate pack volume estimates per SKU using serial numbered anchors
    sku_pack_estimates = {sku: [] for sku in skus}
    for p in parallels:
        if p['serial_limit'] is not None:
            total_global_cards = p['checklist_count'] * p['serial_limit']
            for sku_name, odds_ratio in p['odds'].items():
                if odds_ratio and odds_ratio > 0:
                    estimated_packs = odds_ratio * total_global_cards
                    sku_pack_estimates[sku_name].append(estimated_packs)

    # Use median filtering to smooth Topps rounding math
    true_sku_pack_volumes = {}
    print("--- SKU PRODUCTION CALCULATIONS ---")
    for sku_name, estimates in sku_pack_estimates.items():
        if estimates:
            smoothed_volume = int(statistics.median(estimates))
            true_sku_pack_volumes[sku_name] = smoothed_volume
            print(f"{sku_name.upper()}: {smoothed_volume:,} total packs.")
        else:
            true_sku_pack_volumes[sku_name] = 0
            print(f"{sku_name.upper()}: No serial anchors found.")

    # Back-calculate non-serial numbered items
    final_output = {
        "product": data["product"],
        "calculated_parallels": []
    }
    
    for p in parallels:
        total_printed_cards = 0
        for sku_name, odds_ratio in p['odds'].items():
            if odds_ratio and odds_ratio > 0 and true_sku_pack_volumes.get(sku_name, 0) > 0:
                cards_dropped = true_sku_pack_volumes[sku_name] / odds_ratio
                total_printed_cards += cards_dropped
        
        print_run_per_player = round(total_printed_cards / p['checklist_count']) if p['checklist_count'] > 0 else 0
        
        final_output["calculated_parallels"].append({
            "name": p["name"],
            "is_unserial_numbered": p['serial_limit'] is None,
            "checklist_count": p["checklist_count"],
            "stated_serial": p["serial_limit"],
            "print_run_per_player": print_run_per_player
        })

    # Output directly back into the repository for your frontend UX to fetch
    with open('final_output.json', 'w') as f:
        json.dump(final_output, indent=2)
    print("SUCCESS: Engine updated final_output.json")

if __name__ == "__main__":
    run_chasing_majors_engine()
