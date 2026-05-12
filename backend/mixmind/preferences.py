"""
AI preference learning.

Approach:
- User rates tracks: -1 dislike / 0 neutral / 1 like / 2 love.
- We build a feature matrix from the stored `feature_vector` + BPM + energy
  + brightness + danceability (so mood/genre-ish signals all in one).
- For recommendations, we use cosine-similarity between a "taste centroid"
  (mean of liked tracks' vectors) and candidate tracks.
- Once >= 20 ratings exist, we also train a RandomForest to refine scoring.

Model is pickled to MODEL_PATH so it's warm on subsequent runs.
"""
import json
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from mixmind import database as db
from mixmind.config import MODEL_PATH


def _track_to_vector(track: Dict[str, Any]) -> Optional[np.ndarray]:
    fv_json = track.get("feature_vector")
    if not fv_json:
        return None
    try:
        fv = json.loads(fv_json)
    except (TypeError, ValueError):
        return None
    extras = [
        float(track.get("bpm") or 120) / 200,
        float(track.get("energy") or 5) / 10,
        float(track.get("brightness") or 0.5),
        float(track.get("danceability") or 0.5),
    ]
    return np.array(fv + extras, dtype=np.float32)


def _normalize_matrix(X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    mean = X.mean(axis=0)
    std = X.std(axis=0) + 1e-6
    return (X - mean) / std, mean, std


def train_preference_model() -> Dict[str, Any]:
    """
    Train a preference model using liked/disliked tracks.
    Returns a summary dict.
    """
    import joblib
    from sklearn.ensemble import RandomForestClassifier

    all_tracks = db.get_analyzed_tracks()
    X_list = []
    y_list = []
    for t in all_tracks:
        vec = _track_to_vector(t)
        if vec is None:
            continue
        rating = t.get("rating") or 0
        if rating >= 1:
            X_list.append(vec)
            y_list.append(1)
        elif rating == -1:
            X_list.append(vec)
            y_list.append(0)

    if len(X_list) < 5:
        return {
            "trained": False,
            "reason": "Need at least 5 rated tracks (mix of likes & dislikes).",
            "liked": sum(y_list),
            "disliked": len(y_list) - sum(y_list),
        }

    X = np.stack(X_list)
    y = np.array(y_list)
    X_norm, mean, std = _normalize_matrix(X)

    # If all one class, skip classifier (use centroid only)
    if len(set(y.tolist())) < 2:
        joblib.dump({"mean": mean, "std": std, "model": None}, MODEL_PATH)
        return {
            "trained": True,
            "mode": "centroid-only",
            "liked": int(sum(y)),
            "disliked": int(len(y) - sum(y)),
        }

    model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
    model.fit(X_norm, y)
    joblib.dump({"mean": mean, "std": std, "model": model}, MODEL_PATH)
    return {
        "trained": True,
        "mode": "random-forest",
        "liked": int(sum(y)),
        "disliked": int(len(y) - sum(y)),
        "score": float(model.score(X_norm, y)),
    }


def _load_model():
    import joblib
    if not MODEL_PATH.exists():
        return None
    return joblib.load(MODEL_PATH)


def recommend(limit: int = 20, exclude_rated: bool = True) -> List[Dict[str, Any]]:
    """
    Recommend tracks based on learned preferences.

    Strategy:
    - Compute a "taste centroid" from liked tracks.
    - Score candidates by cosine similarity to the centroid.
    - If a trained model exists, blend: 0.6 * centroid_sim + 0.4 * model_prob.
    """
    liked = db.get_liked_tracks()
    if not liked:
        return []

    liked_vecs = [v for v in (_track_to_vector(t) for t in liked) if v is not None]
    if not liked_vecs:
        return []

    taste = np.mean(np.stack(liked_vecs), axis=0)
    taste_norm = taste / (np.linalg.norm(taste) + 1e-8)

    model_bundle = _load_model()

    candidates = db.get_analyzed_tracks()
    scored: List[Tuple[float, Dict[str, Any]]] = []
    liked_ids = {t["id"] for t in liked}

    for t in candidates:
        if exclude_rated and t["id"] in liked_ids:
            continue
        if exclude_rated and (t.get("rating") or 0) == -1:
            continue
        vec = _track_to_vector(t)
        if vec is None:
            continue
        vec_n = vec / (np.linalg.norm(vec) + 1e-8)
        sim = float(np.dot(vec_n, taste_norm))

        if model_bundle and model_bundle.get("model") is not None:
            mean, std = model_bundle["mean"], model_bundle["std"]
            x = ((vec - mean) / std).reshape(1, -1)
            prob = float(model_bundle["model"].predict_proba(x)[0][1])
            score = 0.6 * sim + 0.4 * prob
        else:
            score = sim

        scored.append((score, t))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for score, t in scored[:limit]:
        d = dict(t)
        d["similarity_score"] = round(float(score), 4)
        results.append(d)
    return results


def find_similar(track_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    """Find tracks similar to a given one, by feature cosine similarity."""
    target = db.get_track(track_id)
    if not target:
        return []
    target_vec = _track_to_vector(target)
    if target_vec is None:
        return []
    target_n = target_vec / (np.linalg.norm(target_vec) + 1e-8)

    scored = []
    for t in db.get_analyzed_tracks():
        if t["id"] == track_id:
            continue
        vec = _track_to_vector(t)
        if vec is None:
            continue
        vec_n = vec / (np.linalg.norm(vec) + 1e-8)
        sim = float(np.dot(vec_n, target_n))
        scored.append((sim, t))

    scored.sort(key=lambda x: x[0], reverse=True)
    out = []
    for sim, t in scored[:limit]:
        d = dict(t)
        d["similarity_score"] = round(sim, 4)
        out.append(d)
    return out
