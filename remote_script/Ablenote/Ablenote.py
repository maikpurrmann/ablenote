"""
Ablenote – Ableton Live Remote Script
Schreibt den aktuellen Session-Status regelmäßig in eine JSON-Datei,
damit das Ablenote-Script darauf zugreifen kann.
"""

from __future__ import absolute_import

import json
import os
import time

from _Framework.ControlSurface import ControlSurface


STATE_FILE = os.path.join(os.path.expanduser("~"), ".ablenote_state.json")
WRITE_INTERVAL = 2.0  # Sekunden zwischen Schreibvorgängen


class Ablenote(ControlSurface):

    def __init__(self, c_instance):
        super(Ablenote, self).__init__(c_instance)
        self._last_write = 0.0
        self.log_message("Ablenote: Remote Script geladen")

    def update_display(self):
        """Wird ca. 10x pro Sekunde von Live aufgerufen."""
        super(Ablenote, self).update_display()
        now = time.time()
        if now - self._last_write >= WRITE_INTERVAL:
            self._last_write = now
            self._write_state()

    def _write_state(self):
        try:
            song = self.song()
            state = {
                "project": song.name,
                "tempo": round(song.tempo, 1),
                "is_playing": song.is_playing,
                "signature": f"{song.signature_numerator}/{song.signature_denominator}",
                "current_time": round(song.current_song_time, 2),
                "current_bar": song.get_current_beats_song_time().bars,
            }

            # Ausgewählter Track
            try:
                state["selected_track"] = song.view.selected_track.name
            except Exception:
                state["selected_track"] = ""

            # Ausgewählte Scene
            try:
                scenes = list(song.scenes)
                selected_scene = song.view.selected_scene
                idx = scenes.index(selected_scene) + 1
                name = selected_scene.name if selected_scene.name else f"Scene {idx}"
                state["selected_scene_index"] = idx
                state["selected_scene_name"] = name
            except Exception:
                state["selected_scene_index"] = 0
                state["selected_scene_name"] = ""

            # Ausgewählter Clip (Detail-Ansicht unten)
            try:
                detail_clip = song.view.detail_clip
                state["clip_name"] = detail_clip.name if detail_clip else ""
            except Exception:
                state["clip_name"] = ""

            # Alle Track-Namen (für Kontext)
            try:
                state["tracks"] = [t.name for t in song.visible_tracks]
            except Exception:
                state["tracks"] = []

            state["timestamp"] = time.time()

            # Atomar schreiben (tmp + rename)
            tmp_file = STATE_FILE + ".tmp"
            with open(tmp_file, "w") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            os.replace(tmp_file, STATE_FILE)

        except Exception as e:
            self.log_message(f"Ablenote: Fehler beim Schreiben: {e}")

    def disconnect(self):
        """Aufräumen wenn das Script entladen wird."""
        try:
            if os.path.exists(STATE_FILE):
                os.remove(STATE_FILE)
        except Exception:
            pass
        super(Ablenote, self).disconnect()
