import json
import os

benchmark_enzymes = [
    "LRRK2",
    "GSK3B",
    "CDK5",
    "BACE1",
    "CASP3",
    "HDAC6",
    "PDE4D",
    "MAOB",
    "ACHE",
    "BCHE"
]

enzyme_classes = {
    "LRRK2": "Kinase",
    "GSK3B": "Kinase",
    "CDK5": "Kinase",
    "BACE1": "Protease",
    "CASP3": "Protease",
    "HDAC6": "HDAC",
    "PDE4D": "PDE",
    "MAOB": "Oxidoreductase",
    "ACHE": "Cholinesterase",
    "BCHE": "Cholinesterase"
}

diseases = {
    "LRRK2": "Parkinson's Disease",
    "GSK3B": "Alzheimer's Disease",
    "CDK5": "Alzheimer's Disease",
    "BACE1": "Alzheimer's Disease",
    "CASP3": "ALS",
    "HDAC6": "Huntington's Disease",
    "PDE4D": "Multiple Sclerosis",
    "MAOB": "Parkinson's Disease",
    "ACHE": "Alzheimer's Disease",
    "BCHE": "Alzheimer's Disease"
}

if __name__ == "__main__":
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(data_dir, exist_ok=True)

    benchmark_data = []
    for enzyme in benchmark_enzymes:
        benchmark_data.append({
            "gene_symbol": enzyme,
            "enzyme_class": enzyme_classes[enzyme],
            "disease_indication": diseases[enzyme]
        })

    output_path = os.path.join(data_dir, "benchmark_enzymes.json")
    with open(output_path, "w") as f:
        json.dump(benchmark_data, f, indent=2)
    
    print(f"Created benchmark_enzymes.json with {len(benchmark_data)} enzymes")
