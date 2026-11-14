"""Voix off : génération Gemini TTS, import d'un enregistrement, voix de référence Kokoro, transcription de contrôle."""
import base64, io, json, os, subprocess, sys, time, urllib.request, urllib.error
import numpy as np, soundfile as sf
import storylib

API = "https://generativelanguage.googleapis.com/v1beta/models"
CACHE = os.path.expanduser("~/.cache/feg-videos")
KOKORO_URLS = {
    "kokoro-v1.0.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
    "voices-v1.0.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
}

ACCENTS = {
    "gabon": ("- ACCENT : français parlé avec un accent africain francophone authentique, d'Afrique centrale, plus précisément gabonais "
              "(Libreville), comme un(e) présentateur/présentatrice de télévision gabonaise. Accent naturel et élégant, jamais caricatural, "
              "aucun accent européen ou parisien.\n"),
    "neutre": "",
}

def _post(model, body, timeout=300):
    headers = {"Content-Type": "application/json"}
    if os.environ.get("GEMINI_API_KEY"):  # sinon la clé est injectée par le proxy de l'environnement
        headers["x-goog-api-key"] = os.environ["GEMINI_API_KEY"]
    req = urllib.request.Request(f"{API}/{model}:generateContent", data=json.dumps(body).encode(), headers=headers)
    try:
        return json.load(urllib.request.urlopen(req, timeout=timeout))
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Erreur API Gemini ({model}) : {e.read().decode()[:600]}")

def gemini_tts(story, out_wav, voice="Achird", model="gemini-3.8-flash-tts", accent="gabon"):
    text = storylib.narration_text(story)
    prompt = ("# PROFIL AUDIO\nUn(e) journaliste gabonais(e) de Libreville, expérimenté(e), qui raconte une actualité économique à un ami, "
              "face caméra, pour une vidéo de réseaux sociaux.\n\n# NOTES DE RÉALISATION\n" + ACCENTS[accent] +
              "- Voix parfaitement humaine et naturelle : on doit entendre de vraies respirations, légères et audibles, avant les phrases et entre les idées.\n"
              "- Ton conversationnel, posé et sincère, jamais robotique ni récité ; intonation qui monte et descend naturellement, petits silences de réflexion.\n"
              "- Rythme vivant et dynamique, mais avec le temps de respirer ; appuie légèrement les mots importants.\n"
              "- La dernière phrase (l'appel à s'abonner) se dit avec un sourire dans la voix, de façon complice.\n"
              "- Prononce « Fègue » comme écrit.\n- Ne rajoute AUCUNE phrase : lis exactement le texte.\n\n"
              "# TEXTE À LIRE (ne lis que ceci)\n" + text)
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
    r = _post(model, body)
    cand = r["candidates"][0]
    if "content" not in cand:
        raise SystemExit(f"Gemini n'a pas renvoyé d'audio ({cand.get('finishReason')}). Relancer, ou changer de voix/modèle.")
    part = cand["content"]["parts"][0]["inlineData"]
    raw = base64.b64decode(part["data"])
    if raw[:4] == b"RIFF":
        s, sr = sf.read(io.BytesIO(raw), dtype="float32")
        s = s if s.ndim == 1 else s.mean(1)
    else:  # PCM 16 bits brut, 24 kHz
        s, sr = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768, 24000
    sf.write(out_wav, s, sr)
    return out_wav

def import_recording(src, out_wav):
    """Enregistrement personnel (m4a, mp3, wav...) -> wav mono 24 kHz, silences de début/fin retirés."""
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-ac", "1", "-ar", "24000",
                    "-af", "highpass=f=70,silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                           "silenceremove=start_periods=1:start_threshold=-45dB,areverse", out_wav], check=True)
    return out_wav

def _kokoro():
    os.makedirs(CACHE, exist_ok=True)
    for fn, url in KOKORO_URLS.items():
        p = os.path.join(CACHE, fn)
        if not os.path.exists(p):
            print("Téléchargement", fn, "...", file=sys.stderr)
            subprocess.run(["curl", "-sSL", "-o", p, url], check=True)
    from kokoro_onnx import Kokoro
    return Kokoro(os.path.join(CACHE, "kokoro-v1.0.onnx"), os.path.join(CACHE, "voices-v1.0.bin"))

def kokoro_reference(story, out_dir):
    """Voix de synthèse hors ligne, fragment par fragment : sert de référence pour l'alignement."""
    os.makedirs(out_dir, exist_ok=True)
    k = _kokoro(); out = {}
    for key, text in storylib.pieces(story):
        s, sr = k.create(text, voice="ff_siwis", speed=1.05, lang="fr-fr")
        s = np.asarray(s, dtype=np.float32)
        nz = np.where(np.abs(s) > 0.01 * np.max(np.abs(s)))[0]
        s = s[max(0, nz[0] - int(0.03 * sr)): min(len(s), nz[-1] + int(0.08 * sr))]
        f = os.path.join(out_dir, f"ref_{key}.wav"); sf.write(f, s, sr)
        out[key] = dict(file=f, dur=len(s) / sr, sr=sr, text=text)
    json.dump(out, open(os.path.join(out_dir, "reference.json"), "w"), indent=1, ensure_ascii=False)
    return out

def transcribe(wav, model="gemini-3.5-flash"):
    """Transcription horodatée (contrôle : le modèle de voix n'a rien inventé ni sauté)."""
    s, sr = sf.read(wav); buf = io.BytesIO(); sf.write(buf, s, sr, format="WAV")
    body = {"contents": [{"parts": [
        {"inlineData": {"mimeType": "audio/wav", "data": base64.b64encode(buf.getvalue()).decode()}},
        {"text": "Transcris mot à mot cet audio en français. Pour chaque phrase ou fragment séparé par une pause, "
                 "donne l'horodatage de début et de fin en secondes (format [ss.s - ss.s] texte). Ne commente pas."}]}]}
    r = _post(model, body, timeout=180)
    return r["candidates"][0]["content"]["parts"][0]["text"]

def cut(wav, start, end, out_wav):
    """Retire un passage (ex. phrase inventée par le modèle), à placer dans des silences."""
    s, sr = sf.read(wav)
    sf.write(out_wav, np.concatenate([s[:int(start * sr)], s[int(end * sr):]]), sr)
    return out_wav
