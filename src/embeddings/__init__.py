import torch
import numpy as np
import os
import json
import hashlib
from typing import Dict, Tuple, List
from transformers import AutoTokenizer, AutoModel
from src.config import EMBEDDING_MODEL, DEVICE, EMBEDDING_CACHE_DIR, CACHE_EMBEDDINGS

class ESMEncoder:
    def __init__(self, model_name: str = EMBEDDING_MODEL, use_cache: bool = CACHE_EMBEDDINGS):
        self.model_name = model_name
        self.use_cache = use_cache
        self.device = DEVICE if torch.cuda.is_available() else "cpu"
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)
        self.model.eval()

    def _get_cache_key(self, sequence: str) -> str:
        return hashlib.md5(sequence.encode()).hexdigest()

    def _get_cached_embedding(self, sequence: str) -> np.ndarray:
        if not self.use_cache:
            return None
        
        cache_key = self._get_cache_key(sequence)
        cache_file = os.path.join(EMBEDDING_CACHE_DIR, f"{cache_key}.npy")
        
        if os.path.exists(cache_file):
            return np.load(cache_file)
        return None

    def _save_cached_embedding(self, sequence: str, embedding: np.ndarray):
        if not self.use_cache:
            return
        
        cache_key = self._get_cache_key(sequence)
        cache_file = os.path.join(EMBEDDING_CACHE_DIR, f"{cache_key}.npy")
        np.save(cache_file, embedding)

    def encode(self, sequence: str) -> np.ndarray:
        cached = self._get_cached_embedding(sequence)
        if cached is not None:
            return cached

        inputs = self.tokenizer(sequence, return_tensors="pt", max_length=1024, truncation=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            embeddings = outputs.last_hidden_state.mean(dim=1).cpu().numpy()

        embedding = embeddings[0].astype(np.float32)
        self._save_cached_embedding(sequence, embedding)
        
        return embedding

    def encode_batch(self, sequences: List[str]) -> List[np.ndarray]:
        return [self.encode(seq) for seq in sequences]

class MutationGenerator:
    def __init__(self, encoder: ESMEncoder):
        self.encoder = encoder
        self.hydrophobic = set("AILMFVPW")
        self.charged = {"D", "E", "K", "R", "H"}
        self.polar = set("STNQC")

    def _get_substitution(self, wildtype: str, mutation_type: str) -> str:
        if mutation_type == "benign":
            if wildtype in self.hydrophobic:
                return np.random.choice(list(self.hydrophobic - {wildtype}))
            elif wildtype in self.charged:
                return np.random.choice(list(self.charged - {wildtype}))
            elif wildtype in self.polar:
                return np.random.choice(list(self.polar - {wildtype}))
            else:
                return np.random.choice(list("ACDEFGHIKLMNPQRSTVWY"))
        
        elif mutation_type == "moderate":
            if wildtype in self.hydrophobic:
                candidates = (self.polar | self.charged) - {wildtype}
                return np.random.choice(list(candidates))
            else:
                candidates = set("ACDEFGHIKLMNPQRSTVWY") - {wildtype}
                return np.random.choice(list(candidates))
        
        elif mutation_type == "disruptive":
            if wildtype in self.hydrophobic:
                return np.random.choice(list(self.charged))
            elif wildtype in self.charged:
                return np.random.choice(list(self.hydrophobic))
            else:
                candidates = set("ACDEFGHIKLMNPQRSTVWY") - {wildtype}
                return np.random.choice(list(candidates))

    def generate_mutation(self, sequence: str, position: int, mutation_type: str) -> str:
        if position < 0 or position >= len(sequence):
            position = len(sequence) // 2
        
        wildtype = sequence[position]
        substitution = self._get_substitution(wildtype, mutation_type)
        
        mutant = sequence[:position] + substitution + sequence[position+1:]
        return mutant

    def compute_delta(self, wt_embedding: np.ndarray, mutant_embedding: np.ndarray) -> Dict[str, float]:
        cosine_sim = np.dot(wt_embedding, mutant_embedding) / (
            np.linalg.norm(wt_embedding) * np.linalg.norm(mutant_embedding)
        )
        euclidean = float(np.linalg.norm(wt_embedding - mutant_embedding))
        delta_norm = float(np.linalg.norm(mutant_embedding - wt_embedding))
        
        return {
            "cosine_similarity": float(cosine_sim),
            "euclidean_distance": euclidean,
            "delta_norm": delta_norm,
        }

    def generate_mutation_set(self, sequence: str) -> Dict[str, any]:
        results = {
            "wt_embedding": self.encoder.encode(sequence).tolist(),
        }
        
        for mutation_type in ["benign", "moderate", "disruptive"]:
            position = np.random.randint(0, len(sequence))
            mutant_seq = self.generate_mutation(sequence, position, mutation_type)
            mutant_emb = self.encoder.encode(mutant_seq)
            
            wt_emb = self.encoder.encode(sequence)
            delta = self.compute_delta(wt_emb, mutant_emb)
            
            results[mutation_type] = {
                "sequence": mutant_seq,
                "position": int(position),
                "embedding": mutant_emb.tolist(),
                "delta": delta,
            }
        
        return results
