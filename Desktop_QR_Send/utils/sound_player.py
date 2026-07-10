# sound_player.py
import os
import pygame
import threading

class SoundPlayer:
    def __init__(self):
        pygame.mixer.init()
        self.playing = False
        self.lock = threading.Lock()

    def play_sound(self, success):
        with self.lock:
            if self.playing:
                return

            self.playing = True

        try:
            if success:
                sound = pygame.mixer.Sound(os.path.join(os.getcwd(), "success.mp3"))
            else:
                sound = pygame.mixer.Sound(os.path.join(os.getcwd(), "warning.mp3"))

            sound.play()

            while pygame.mixer.get_busy():
                pygame.time.delay(100)

        finally:
            with self.lock:
                self.playing = False