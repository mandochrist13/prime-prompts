# Instructions pour Claude — fabrique de vidéos FEG

L'utilisateur (Fédération des Entreprises du Gabon) dépose dans `videos/<dossier>/` un `texte.md` (texte de publication) et des photos, parfois un enregistrement de sa voix. Ton travail : produire la vidéo verticale complète et la lui envoyer. Réponds en français.

## Mise en place (une fois par session)

```bash
cd feg-videos
pip install -r requirements.txt     # kokoro-onnx, librosa, soundfile, pillow, numpy
```
- `ffmpeg` doit être présent. Les modèles Kokoro (voix de référence pour l'alignement, ~350 Mo) se téléchargent tout seuls depuis GitHub au premier lancement dans `~/.cache/feg-videos`.
- Clé Gemini : injectée par le proxy de l'environnement (secret réseau pour `generativelanguage.googleapis.com`) ou variable `GEMINI_API_KEY`. Si l'API répond 403 sans clé, demande à l'utilisateur de l'ajouter dans les réglages de l'environnement (ne jamais la demander dans le chat).

## Étapes pour une nouvelle vidéo

1. **Préparer le dossier** : photos dans `videos/<dossier>/photos/` (renomme-les `1.jpg`, `2.jpg`… si besoin). Regarde chaque photo pour choisir les cadrages.
2. **Écrire `videos/<dossier>/story.py`** en partant de `videos/_modele/story.py` et de l'exemple `videos/2026-11-05_rencontre-FEG-AFD/story.py`. Règles :
   - Reprendre **tout** le texte de la publication, dans l'ordre, sans rien inventer.
   - Alterner plans photo (`kind="photo"`) et cartons typographiques (`kind="card"`) ; 1 titre au début, l'écran de fin standard à la fin (ne pas modifier sa phrase).
   - Sous-titres photo : fragments de 3 à 8 mots ; `(affiché, prononcé)` : dans le prononcé, **nombres et dates en toutes lettres**, « FEG » s'écrit **« Fègue »**, sigles épelés autrement selon l'usage (ex. AFD → « A F D » si on ne dit pas le nom complet).
   - Cartons : 2 à 6 lignes, mots-clés en `"script"` (rendus en Anton majuscules) avec `BRONZE` sur fond foncé, `BRONZE_FONCE` ou `VERT_LOGO` sur fond `CREME`.
   - Varier les fonds de cartons (`VERT`, `VERT_VIF`, `FORET`, `NOIR_VERT`, `CREME`) et les photos/cadrages (`pan`, `cy`) ; réutiliser une même photo avec un cadrage différent est normal.
   - Visé : 50 à 70 s.
3. **Aperçu rapide** (sans voix Gemini, avec la voix de référence) si tu veux vérifier la mise en page : générer une narration puis `--apercu`, et regarder `build/preview_<tag>.jpg`.
4. **Fabriquer** (une commande par voix) :
   ```bash
   python3 engine/make_video.py videos/<dossier> --voix Achird --tag masculine      # voix masculine validée
   python3 engine/make_video.py videos/<dossier> --voix Sulafat --tag feminine      # voix féminine validée
   python3 engine/make_video.py videos/<dossier> --enregistrement videos/<dossier>/voix.m4a --tag ma-voix
   ```
   Par défaut : modèle `gemini-3.8-flash-tts`, accent gabonais (`--accent gabon`). Si quota épuisé (429), essayer `--modele gemini-3.8-flash-lite-tts` puis `gemini-3.1-flash-tts-preview`. `gemini-2.5-pro-preview-tts` n'a pas de quota gratuit.
5. **Contrôle obligatoire** : le script imprime une transcription (`build/transcription_<tag>.txt`). La comparer au texte : les modèles TTS **inventent parfois une phrase** (déjà vu : « Et surtout, n'oubliez pas de vous abonner ! » au milieu). Si c'est le cas :
   ```python
   import sys; sys.path.insert(0, "engine"); import voice
   voice.cut("videos/<d>/build/narration_<tag>.wav", debut_s, fin_s, "videos/<d>/build/narration_<tag>_ok.wav")
   ```
   (couper dans les silences qui encadrent la phrase), puis relancer avec `--narration .../narration_<tag>_ok.wav`.
   Vérifier aussi le rapport d'alignement : une ligne `<-- À VÉRIFIER` signale un fragment anormalement long ou court.
6. **Vérifier visuellement** : extraire quelques images (`ffmpeg -ss T -i sortie/x.mp4 -frames:v 1 f.jpg`) ou une planche, puis envoyer la/les vidéo(s) de `videos/<dossier>/sortie/` à l'utilisateur. Ne pas versionner `build/` ni `sortie/`.
7. Proposer de committer `story.py` (et les photos/texte si ajoutés localement) sur la branche de travail.

## Choix validés par l'utilisateur (à respecter)
- Couleurs FEG : vert + bronze (pas de bleu, pas de rouge). Logo **toujours en haut à gauche**.
- Montage dynamique (transitions rapides, zooms, musique 126 BPM), pas « endormant ».
- Voix naturelles qui respirent, ton conversationnel, **accent d'Afrique centrale (gabonais)**. Voix retenues : Achird (masculine), Sulafat (féminine).
- « FEG » se prononce « Fègue ».
- Fin : « La Fègue, le secteur privé en action. Pense à t'abonner et à liker, pour ne rien manquer ! » — icône cloche dès « Pense à », puis cœur sur « liker », une seule icône à la fois (pas de bandeau défilant).
- Toujours livrer deux versions (voix masculine et féminine) sauf demande contraire.
