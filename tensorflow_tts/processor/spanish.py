# -*- coding: utf-8 -*-
# Copyright 2020 TensorFlowTTS Team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Perform preprocessing and raw feature extraction for Spanish dataset."""

import os
import re

import numpy as np
import soundfile as sf
from dataclasses import dataclass
from tensorflow_tts.processor import BaseProcessor
from tensorflow_tts.utils import cleaners


_pad = "pad"

_phsymbols = ["b", "a", "D", "i+", "x", "n", "d", "o", "rf", "m", "e", "r", "a+", "j", "t", "s", "k", "e+",
            "T", "i", "l", "ng", "p", "u", "n~", "o+", "w", "V", "f", "G", "g", "L", "tS", "aU", "u+", "eI",
            "aI", "oI", "z", "eU","SIL", "END"]
            
_letters = "DurantescoviódíqlmbpáCxyfgzhjLúéEABñQPNMTYSJVHGRFIÉOÁüKUZÚwÓÍkWÅè"
_punctuation = ",.-;¡!¿?': "

# Prepend "@" to phonetic symbols to ensure uniqueness (some are the same as uppercase letters):
_phonemes = ["@" + s for s in _phsymbols]
# Export all symbols:
SPANISH_SYMBOLS = (
    [_pad] + list(_letters) + list(_punctuation) + _phonemes 
)


_curly_re = re.compile(r"(.*?)\{(.+?)\}(.*)")

@dataclass
class SpanishProcessor(BaseProcessor):
    """Spanish processor."""

    cleaner_names: str = None
    positions = {
        "wave_file": 0,
        "text": 1,
        "text_norm": 2,
    }
    train_f_name: str = "metadata.csv"

    def create_items(self):
        if self.data_dir:
            with open(
                os.path.join(self.data_dir, self.train_f_name), encoding="utf-8"
            ) as f:
                self.items = [self.split_line(self.data_dir, line, "|") for line in f]

    def split_line(self, data_dir, line, split):
        parts = line.strip().split(split)
        wave_file = parts[self.positions["wave_file"]]
        text_norm = parts[self.positions["text_norm"]]
        wav_path = os.path.join(data_dir, "wavs", f"{wave_file}.wav")
        speaker_name = "spanish"
        return text_norm, wav_path, speaker_name

    def setup_eos_token(self):
        return None

    def get_one_sample(self, item):
        text, wav_path, speaker_name = item

        # normalize audio signal to be [-1, 1], soundfile already norm.
        audio, rate = sf.read(wav_path)
        audio = audio.astype(np.float32)

        # convert text to ids
        text_ids = np.asarray(self.text_to_sequence(text), np.int32)

        sample = {
            "raw_text": text,
            "text_ids": text_ids,
            "audio": audio,
            "utt_id": os.path.split(wav_path)[-1].split(".")[0],
            "speaker_name": speaker_name,
            "rate": rate,
        }

        return sample

    def text_to_sequence(self, text):
        sequence = []
        # Check for curly braces and treat their contents as ARPAbet:
        while len(text):
            m = _curly_re.match(text)
            if not m:
                sequence += self._symbols_to_sequence(
                    self._clean_text(text, [self.cleaner_names])
                )
                break
            sequence += self._symbols_to_sequence(
                self._clean_text(m.group(1), [self.cleaner_names])
            )
            sequence += self._phonemes_to_sequence(m.group(2))
            text = m.group(3)

        return sequence

    def _symbols_to_sequence(self, symbols):
        return [self.symbol_to_id[s] for s in symbols if self._should_keep_symbol(s)]

    def _phonemes_to_sequence(self, text):
        return self._symbols_to_sequence(["@" + s for s in text.split()])

    def _should_keep_symbol(self, s):
        return s in self.symbol_to_id and s != "_" and s != "~"

    def _clean_text(self, text, cleaner_names):
        return text # No text cleaning goes on here (for now?)
