"""Fabrique une vidéo FEG de bout en bout.

Exemples :
  # voix Gemini masculine, accent gabonais
  python3 engine/make_video.py videos/2026-11-05_rencontre-FEG-AFD --voix Achird --tag masculine
  # voix Gemini féminine
  python3 engine/make_video.py videos/... --voix Sulafat --tag feminine
  # votre propre enregistrement
  python3 engine/make_video.py videos/... --enregistrement videos/.../voix.m4a --tag ma-voix
  # réutiliser une narration déjà générée (sans nouvel appel Gemini)
  python3 engine/make_video.py videos/... --narration videos/.../build/narration_masculine.wav --tag masculine
  # aperçu (planche d'images) seulement
  python3 engine/make_video.py videos/... --narration ... --tag masculine --apercu
"""
import argparse, json, os, subprocess, sys
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import storylib, voice, align as aligner

ENGINE = storylib.ENGINE

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video_dir")
    ap.add_argument("--tag", required=True, help="nom de la version (ex. masculine, feminine, ma-voix)")
    ap.add_argument("--voix", default="Achird", help="voix Gemini (ex. Achird, Sulafat, Charon, Puck, Aoede, Orus)")
    ap.add_argument("--modele", default="gemini-3.8-flash-tts", help="modèle Gemini TTS")
    ap.add_argument("--accent", default="gabon", choices=list(voice.ACCENTS))
    ap.add_argument("--enregistrement", help="fichier audio de votre propre voix")
    ap.add_argument("--narration", help="narration déjà prête (wav), pas de génération")
    ap.add_argument("--sans-controle", action="store_true", help="ne pas transcrire la narration pour contrôle")
    ap.add_argument("--apercu", action="store_true", help="planche d'aperçu seulement, pas de vidéo")
    a = ap.parse_args()

    vdir = os.path.abspath(a.video_dir); build = os.path.join(vdir, "build"); os.makedirs(build, exist_ok=True)
    story = storylib.load(vdir).story
    narr = os.path.join(build, f"narration_{a.tag}.wav")

    # 1. narration
    if a.narration:
        narr = os.path.abspath(a.narration)
    elif a.enregistrement:
        voice.import_recording(a.enregistrement, narr)
    else:
        print(f"[1/5] Voix Gemini {a.voix} ({a.modele}) ...", file=sys.stderr)
        voice.gemini_tts(story, narr, voice=a.voix, model=a.modele, accent=a.accent)

    # 2. contrôle : transcription (le modèle n'a-t-il rien inventé ni sauté ?)
    if not a.sans_controle and not a.narration:
        print("[2/5] Transcription de contrôle ...", file=sys.stderr)
        try:
            tr = voice.transcribe(narr)
            open(os.path.join(build, f"transcription_{a.tag}.txt"), "w").write(tr)
            print(tr)
            print("\n>>> Comparer avec le texte attendu. Si une phrase a été inventée, la retirer avec voice.cut() "
                  "puis relancer avec --narration.\n", file=sys.stderr)
        except SystemExit as e:
            print("Transcription impossible :", e, file=sys.stderr)

    # 3. alignement sur la voix de référence
    print("[3/5] Alignement ...", file=sys.stderr)
    refdir = os.path.join(build, "reference")
    refj = os.path.join(refdir, "reference.json")
    texts = dict(storylib.pieces(story))
    ref = json.load(open(refj)) if os.path.exists(refj) else None
    if not ref or any(ref.get(k, {}).get("text") != t for k, t in texts.items()) or set(ref) != set(texts):
        ref = voice.kokoro_reference(story, refdir)
    alj = os.path.join(build, f"align_{a.tag}.json")
    print(aligner.align(story, narr, ref, alj))

    # 4. rendu image
    print("[4/5] Rendu ...", file=sys.stderr)
    cmd = [sys.executable, os.path.join(ENGINE, "render.py"), vdir, a.tag, alj] + (["preview"] if a.apercu else [])
    subprocess.run(cmd, check=True)
    if a.apercu:
        print("Aperçu :", os.path.join(build, f"preview_{a.tag}.jpg")); return

    # 5. son : voix + musique + mixage
    print("[5/5] Mixage ...", file=sys.stderr)
    t = json.load(open(os.path.join(build, f"timing_{a.tag}.json"))); SR = 44100
    vo = np.zeros(int(t["total"] * SR) + SR)
    for start, f in t["voice"]:
        s, sr = sf.read(f)
        s = s if s.ndim == 1 else s.mean(1)
        x = np.interp(np.arange(0, len(s), sr / SR), np.arange(len(s)), s)
        i = int(start * SR); n = min(len(x), len(vo) - i); vo[i:i + n] += x[:n]
    vo = vo / np.max(np.abs(vo)) * 0.9
    vw, mw = os.path.join(build, f"voix_{a.tag}.wav"), os.path.join(build, f"musique_{a.tag}.wav")
    sf.write(vw, vo, SR)
    subprocess.run([sys.executable, os.path.join(ENGINE, "music.py"), str(t["total"]), json.dumps(t["cuts"]), mw, "cold"], check=True)
    outdir = os.path.join(vdir, "sortie"); os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, f"{os.path.basename(vdir)}_{a.tag}.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", os.path.join(build, f"video_{a.tag}_noaudio.mp4"), "-i", vw, "-i", mw,
                    "-filter_complex", "[2:a]volume=0.26[m];[1:a]aformat=channel_layouts=stereo,highpass=f=70,"
                    "acompressor=threshold=0.1:ratio=2.5:attack=5:release=80,volume=1.5[v];"
                    "[m][v]amix=inputs=2:normalize=0,loudnorm=I=-15:TP=-1.5:LRA=11[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-ar", "44100", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", out], check=True)
    print("Vidéo prête :", out)

if __name__ == "__main__":
    main()
