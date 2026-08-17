"""Local perceptual hashing for instant cache hits on repeat searches."""
from PIL import Image
import imagehash


def compute_phash(path: str) -> str:
    with Image.open(path) as img:
        return str(imagehash.phash(img, hash_size=16))


def hamming_similarity(hash_a: str, hash_b: str) -> float:
    """0..100 similarity between two hex phashes of equal length."""
    try:
        a = imagehash.hex_to_hash(hash_a)
        b = imagehash.hex_to_hash(hash_b)
    except ValueError:
        return 0.0
    max_bits = len(a.hash) ** 2
    distance = a - b
    return round((1 - distance / max_bits) * 100, 1)
