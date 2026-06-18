import json
import os
from typing import List, Dict, Any
from src.config import DATA_DIR

class EnzymeDataset:
    def __init__(self):
        self.enzymes = self._load_dataset()
        self.benchmark = self._load_benchmark()

    def _load_dataset(self) -> List[Dict[str, Any]]:
        enzyme_path = os.path.join(DATA_DIR, "enzymes.json")
        if not os.path.exists(enzyme_path):
            return []
        
        with open(enzyme_path, "r") as f:
            return json.load(f)

    def _load_benchmark(self) -> List[Dict[str, Any]]:
        benchmark_path = os.path.join(DATA_DIR, "benchmark_enzymes.json")
        if not os.path.exists(benchmark_path):
            return []
        
        with open(benchmark_path, "r") as f:
            return json.load(f)

    def get_enzyme_by_name(self, name: str) -> Dict[str, Any]:
        for enzyme in self.enzymes:
            if enzyme.get("enzyme_name") == name or enzyme.get("gene_symbol") == name:
                return enzyme
        return {}

    def get_benchmark_enzymes(self) -> List[Dict[str, Any]]:
        return self.benchmark

    def get_all_enzymes(self) -> List[Dict[str, Any]]:
        return self.enzymes

class DataIngestion:
    def __init__(self, dataset: EnzymeDataset):
        self.dataset = dataset

    def get_enzyme_metadata(self, gene_symbol: str) -> Dict[str, Any]:
        enzyme = self.dataset.get_enzyme_by_name(gene_symbol)
        if not enzyme:
            return {}
        
        return {
            "gene_symbol": enzyme.get("gene_symbol"),
            "enzyme_name": enzyme.get("enzyme_name"),
            "uniprot_id": enzyme.get("uniprot_id"),
            "ec_number": enzyme.get("ec_number"),
            "disease_indication": enzyme.get("disease_indication"),
            "canonical_sequence": enzyme.get("canonical_sequence"),
        }

    def get_enzyme_details(self, gene_symbol: str) -> Dict[str, Any]:
        enzyme = self.dataset.get_enzyme_by_name(gene_symbol)
        if not enzyme:
            return {}
        
        return {
            "metadata": self.get_enzyme_metadata(gene_symbol),
            "substrates": enzyme.get("substrates", []),
            "products": enzyme.get("products", []),
            "cofactors": enzyme.get("cofactors", []),
            "pathogenic_variants": enzyme.get("key_pathogenic_variants", []),
            "inhibitors": enzyme.get("key_inhibitors", []),
            "target_form": enzyme.get("target_form"),
            "clinical_stage": enzyme.get("clinical_stage"),
        }
