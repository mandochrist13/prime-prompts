"""Chargement d'un storyboard (videos/<dossier>/story.py) et liste des fragments parlés."""
import importlib.util, os, sys

ENGINE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ENGINE)
if ENGINE not in sys.path:
    sys.path.insert(0, ENGINE)

def load(video_dir):
    spec = importlib.util.spec_from_file_location("story", os.path.join(video_dir, "story.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def pieces(story):
    """Fragments parlés dans l'ordre : [(clé, texte)]."""
    out = []
    for i, sc in enumerate(story):
        if sc["kind"] == "photo":
            for j, (_, sp) in enumerate(sc["chunks"]):
                out.append((f"{i}_{j}", sp))
        else:
            out.append((f"{i}", sc["say"]))
    return out

def narration_text(story):
    return " ".join(t for _, t in pieces(story))
