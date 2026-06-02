import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import pickle
import os
from typing import Tuple

from modules.sentinel.patterns import (
    ALL_ATTACK_EMBEDDINGS,
    BENIGN_EMBEDDINGS,
    PROMPT_INJECTION_EMBEDDINGS,
    JAILBREAK_EMBEDDINGS,
    IDENTITY_SPOOFING_EMBEDDINGS,
    DATA_EXFILTRATION_EMBEDDINGS,
)
from core.config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

MODEL_CACHE_PATH = "/tmp/phantom_classifier.pkl"


class AttackClassifier:
    def __init__(self):
        self.encoder: SentenceTransformer | None = None
        self.pipeline: Pipeline | None = None
        self.is_ready = False
        self.attack_embeddings: np.ndarray | None = None
        self.attack_labels: list[str] = []

    async def initialize(self):
        logger.info("Initializing attack classifier...")
        try:
            self.encoder = SentenceTransformer(settings.embedding_model)
            self._build_reference_embeddings()
            self._train_classifier()
            self.is_ready = True
            logger.info("Attack classifier initialized successfully")
        except Exception as e:
            logger.error(f"Classifier initialization failed: {e}")
            self.is_ready = False

    def _build_reference_embeddings(self):
        labeled_data = []
        labels = []

        for text in PROMPT_INJECTION_EMBEDDINGS:
            labeled_data.append(text)
            labels.append("PROMPT_INJECTION")
        for text in JAILBREAK_EMBEDDINGS:
            labeled_data.append(text)
            labels.append("JAILBREAK")
        for text in IDENTITY_SPOOFING_EMBEDDINGS:
            labeled_data.append(text)
            labels.append("IDENTITY_SPOOFING")
        for text in DATA_EXFILTRATION_EMBEDDINGS:
            labeled_data.append(text)
            labels.append("DATA_EXFILTRATION")
        for text in BENIGN_EMBEDDINGS:
            labeled_data.append(text)
            labels.append("BENIGN")

        self.attack_embeddings = self.encoder.encode(labeled_data, show_progress_bar=False)
        self.attack_labels = labels

    def _train_classifier(self):
        self.pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("svm", SVC(kernel="rbf", C=10.0, gamma="scale", probability=True)),
        ])
        self.pipeline.fit(self.attack_embeddings, self.attack_labels)

    def classify(self, text: str) -> Tuple[str, float]:
        if not self.is_ready or self.encoder is None:
            return "UNKNOWN", 0.5

        embedding = self.encoder.encode([text], show_progress_bar=False)
        predicted_class = self.pipeline.predict(embedding)[0]
        probabilities = self.pipeline.predict_proba(embedding)[0]
        confidence = float(max(probabilities))

        return predicted_class, confidence

    def get_semantic_score(self, text: str) -> float:
        if not self.is_ready or self.encoder is None:
            return 0.0

        query_embedding = self.encoder.encode([text], show_progress_bar=False)
        attack_only_embs = self.encoder.encode(
            ALL_ATTACK_EMBEDDINGS, show_progress_bar=False
        )

        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity(query_embedding, attack_only_embs)
        return float(np.max(similarities))

    def encode(self, text: str) -> list[float]:
        if not self.is_ready or self.encoder is None:
            return [0.0] * 384
        return self.encoder.encode([text], show_progress_bar=False)[0].tolist()


_classifier_instance: AttackClassifier | None = None


async def get_classifier() -> AttackClassifier:
    global _classifier_instance
    if _classifier_instance is None or not _classifier_instance.is_ready:
        _classifier_instance = AttackClassifier()
        await _classifier_instance.initialize()
    return _classifier_instance
