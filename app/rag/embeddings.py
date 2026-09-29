from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

class TfidfEmbedder:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1,2))
        self.fitted = False

    def fit(self, texts: list[str]) -> None:
        self.vectorizer.fit(texts)
        self.fitted = True

    def encode(self, texts: list[str]) -> np.ndarray:
        if not self.fitted:
            raise RuntimeError("Embedding model is not fitted.")
        return self.vectorizer.transform(texts).toarray()
