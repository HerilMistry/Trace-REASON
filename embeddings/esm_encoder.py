from transformers import AutoTokenizer

from transformers import EsmModel
import torch

MODEL = "facebook/esm2_t6_8M_UR50D"

class ESMEncoder:

    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL)
        self.model = EsmModel.from_pretrained(MODEL)

    def encode(self, sequence):

        inputs = self.tokenizer(
            sequence,
            return_tensors="pt"
        )

        with torch.no_grad():
            outputs = self.model(**inputs)

        return outputs.last_hidden_state.mean(dim=1).squeeze()
    
