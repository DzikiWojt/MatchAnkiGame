from aqt.sound import play, av_player
from typing import List
import re

# Regex pattern to extract filename from [sound:filename.mp3]
SOUND_TAG_REGEX = r"\[sound:(.*?)\]"


def play_sound_from_media_folder(filename: str) -> None:
    # Plays a single audio file directly from the media collection folder.
    if filename:
        play(filename)


def play_audio_from_card_field(field_content: str) -> List[str]:
    # Extracts and plays all embedded audio files from the card field text.
    played_files = []

    # Find all sound tags in the field content
    matches = re.findall(SOUND_TAG_REGEX, field_content)

    for filename in matches:
        if filename:
            # The 'play' function automatically searches in collection.media
            play(filename)
            played_files.append(filename)

    return played_files