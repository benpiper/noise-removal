"""Whisper transcription and evaluation"""

import math
import whisper
import warnings

# Suppress FP16 warning on CPU
warnings.filterwarnings(
    "ignore", message="FP16 is not supported on CPU; using FP32 instead"
)


class WhisperEvaluator:
    """Evaluates audio using OpenAI Whisper to generate transcripts and confidence scores."""

    def __init__(self, model_size="tiny"):
        """
        Initialize the Whisper model. Wait for it to load into CPU/GPU.
        """
        self.is_faster = model_size.startswith("faster-whisper-")
        if self.is_faster:
            import faster_whisper

            model_name = model_size.replace("faster-whisper-", "")
            print(f"Loading Faster Whisper model '{model_name}'...")
            self.model = faster_whisper.WhisperModel(
                model_name, device="auto", compute_type="default"
            )
        else:
            print(f"Loading Whisper model '{model_size}'...")
            self.model = whisper.load_model(model_size)

    def evaluate(self, audio_path: str) -> dict:
        """
        Transcribe the audio and compute a confidence score.

        Args:
            audio_path: Path to the audio file to transcribe

        Returns:
            Dictionary containing 'text', 'segments', 'confidence', and 'srt'
        """
        # Transcribe audio with strong hallucination mitigation parameters (V2)
        # 1. condition_on_previous_text=False prevents recursive looping
        # 2. temperature=0.0 forces greedy/deterministic output instead of guessing
        # 3. compression_ratio_threshold=2.4 asks whisper to reject segments if the output compresses too much.
        if self.is_faster:
            segments_generator, info = self.model.transcribe(
                audio_path,
                condition_on_previous_text=False,
                temperature=0.0,
                no_speech_threshold=0.6,
                logprob_threshold=-1.0,
                compression_ratio_threshold=2.4,
                language="en",
            )
            # Faster Whisper returns a generator of Segment objects, convert to standard dicts
            segments = []
            for s in list(segments_generator):
                segments.append(
                    {
                        "start": s.start,
                        "end": s.end,
                        "text": s.text,
                        "no_speech_prob": s.no_speech_prob,
                        "avg_logprob": s.avg_logprob,
                    }
                )
        else:
            result = self.model.transcribe(
                audio_path,
                condition_on_previous_text=False,
                temperature=0.0,
                no_speech_threshold=0.6,
                logprob_threshold=-1.0,
                compression_ratio_threshold=2.4,
                language="en",
                fp16=False,  # ensure CPU compatibility without warnings
            )
            segments = result.get("segments", [])

        # Calculate overall confidence
        if not segments:
            return {"text": "", "segments": [], "confidence": 0.0, "srt": ""}

        total_duration = 0
        weighted_prob_sum = 0.0

        srt_content = []
        valid_text = []
        valid_segments = []

        for i, segment in enumerate(segments):
            duration = segment.get("end", 0) - segment.get("start", 0)

            # Skip segments that Whisper is confident have no speech
            if segment.get("no_speech_prob", 0.0) > 0.6:
                continue

            text_str = segment.get("text", "").strip()
            if not text_str:
                continue

            # calculate confidence for this segment. avg_logprob is log probability
            # of the sequence. math.exp(avg_logprob) gives linear probability 0-1.
            prob = math.exp(segment.get("avg_logprob", -10))

            total_duration += duration
            weighted_prob_sum += prob * duration

            valid_text.append(text_str)
            valid_segments.append(segment)

            # Format SRT
            start_time = self._format_timestamp(segment["start"])
            end_time = self._format_timestamp(segment["end"])
            # Re-index SRT based on valid segments
            srt_content.append(
                f"{len(valid_segments)}\n{start_time} --> {end_time}\n{text_str}\n"
            )

        overall_confidence = (
            weighted_prob_sum / total_duration if total_duration > 0 else 0.0
        )

        return {
            "text": " ".join(valid_text),
            "segments": valid_segments,
            "confidence": overall_confidence,
            "srt": "\n".join(srt_content),
        }

    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds into SRT timestamp format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        msecs = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{msecs:03d}"
