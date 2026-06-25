"""
Aegis RAG - Enhanced Voice Processor with Local Speaker Diarization
=====================================================================
Using Faster-Whisper for transcription and MFCC-based speaker embeddings.
Falls back gracefully when SpeechBrain is not available.
"""
import os
import sys
import warnings
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import logging

warnings.filterwarnings("ignore")

# Torchaudio compatibility fix for newer versions
try:
    import torchaudio
    if not hasattr(torchaudio, 'list_audio_backends'):
        def _list_audio_backends():
            return ['soundfile', 'sox']
        torchaudio.list_audio_backends = _list_audio_backends
    if not hasattr(torchaudio, 'get_audio_backend'):
        def _get_audio_backend():
            return 'soundfile'
        torchaudio.get_audio_backend = _get_audio_backend
    if not hasattr(torchaudio, 'set_audio_backend'):
        def _set_audio_backend(backend):
            pass
        torchaudio.set_audio_backend = _set_audio_backend
except ImportError:
    pass

import numpy as np
import librosa
from sklearn.cluster import SpectralClustering, AgglomerativeClustering
from sklearn.metrics import silhouette_score
from scipy.ndimage import median_filter

from .base import BaseProcessor, Chunk
from ..config import config

logger = logging.getLogger("AegisRAG-Voice")


class EnhancedVoiceProcessor(BaseProcessor):
    """
    Enhanced voice processor with local speaker diarization.
    Uses Faster-Whisper for transcription and MFCC clustering for speaker identification.
    """
    
    @property
    def supported_extensions(self) -> List[str]:
        return [".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm", ".aac"]
    
    @property
    def doc_type(self) -> str:
        return "voice"
    
    def __init__(
        self,
        whisper_model: str = None,
        use_diarization: bool = True,
        min_speakers: int = 1,
        max_speakers: int = 10
    ):
        """
        Initialize enhanced voice processor.
        
        Args:
            whisper_model: Whisper model size (tiny/base/small/medium/large-v2)
            use_diarization: Whether to use speaker diarization
            min_speakers: Minimum expected speakers
            max_speakers: Maximum expected speakers
        """
        self.whisper_model = whisper_model or config.WHISPER_MODEL
        self.use_diarization = use_diarization
        self.min_speakers = min_speakers
        self.max_speakers = max_speakers
        
        self._whisper = None
        self._embedder = None
        self.sample_rate = 16000
        self._device = self._detect_device()
    
    def _detect_device(self) -> str:
        """Detect available compute device."""
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
        except ImportError:
            pass
        return "cpu"
    
    def _get_whisper(self):
        """Lazy load Faster-Whisper or Groq client."""
        if config.DEPLOYMENT_MODE == "cloud":
            if self._whisper is None:
                from groq import Groq
                if not config.GROQ_API_KEY:
                    logger.error("GROQ_API_KEY not set for cloud voice processing")
                    return None
                self._whisper = Groq(api_key=config.GROQ_API_KEY)
                self._whisper_type = "groq"
            return self._whisper
            
        if self._whisper is not None:
            return self._whisper
        
        try:
            from faster_whisper import WhisperModel
            
            compute_type = "float16" if self._device == "cuda" else "int8"
            
            logger.info(f"Loading Faster-Whisper model: {self.whisper_model}")
            self._whisper = WhisperModel(
                self.whisper_model,
                device=self._device,
                compute_type=compute_type,
                download_root=str(config.MODELS_DIR / "whisper")
            )
            self._whisper_type = "faster-whisper"
            logger.info("Faster-Whisper model loaded successfully")
            return self._whisper
            
        except ImportError:
            logger.warning("faster-whisper not installed, trying openai-whisper")
            try:
                import whisper
                self._whisper = whisper.load_model(self.whisper_model)
                self._whisper_type = "openai-whisper"
                logger.info("OpenAI Whisper model loaded successfully")
                return self._whisper
            except ImportError:
                logger.error("No Whisper implementation available")
                return None
        except Exception as e:
            logger.error(f"Failed to load faster-whisper: {e}")
            return None
    
    def process(self, file_path: Path, document_id: Optional[str] = None) -> List[Chunk]:
        """
        Process an audio file and extract chunks with speaker diarization.
        
        Args:
            file_path: Path to the audio file
            document_id: Optional document identifier
            
        Returns:
            List of Chunk objects with transcribed text and speaker labels
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        document_id = document_id or self._generate_document_id(file_path)
        
        # Perform diarization
        result = self.diarize(str(file_path))
        
        # Convert to chunks
        chunks = []
        for segment in result.get("segments", []):
            chunks.append(Chunk(
                content=segment["text"].strip(),
                document_id=document_id,
                doc_type=self.doc_type,
                source_file=str(file_path),
                timestamp_start=segment["start"],
                timestamp_end=segment["end"],
                speaker=segment.get("speaker", "Unknown"),
                metadata={
                    "language": result.get("metadata", {}).get("language", "unknown"),
                    "confidence": segment.get("confidence", 1.0),
                    "speaker_count": result.get("speaker_count", 1)
                }
            ))
        
        return chunks
    
    def diarize(
        self,
        audio_path: str,
        language: str = None,
        num_speakers: int = None
    ) -> Dict[str, Any]:
        """
        Perform complete speaker diarization on an audio file.
        
        Args:
            audio_path: Path to audio file
            language: Language code or None for auto-detection
            num_speakers: Number of speakers or None for auto-detection
            
        Returns:
            Dictionary with diarization results
        """
        file_name = os.path.basename(audio_path)
        logger.info(f"Starting diarization for: {file_name}")
        
        # Step 1: Transcribe
        logger.info("Step 1/3: Transcribing audio...")
        transcribed_segments = self._transcribe(audio_path, language)
        
        if not transcribed_segments:
            return {
                "segments": [],
                "speakers": [],
                "speaker_count": 0,
                "duration": self._get_audio_duration(audio_path),
                "file_name": file_name,
                "metadata": {"error": "No speech detected"}
            }
        
        if not self.use_diarization:
            # Return transcription without speaker labels
            segments = [{
                "speaker": "Speaker 1",
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"],
                "confidence": 1.0
            } for seg in transcribed_segments]
            
            return {
                "segments": segments,
                "speakers": ["Speaker 1"],
                "speaker_count": 1,
                "duration": self._get_audio_duration(audio_path),
                "file_name": file_name,
                "metadata": {"diarization": "disabled"}
            }
        
        # Step 2: Extract speaker embeddings
        logger.info("Step 2/3: Extracting speaker embeddings...")
        segment_embeddings = self._extract_embeddings(audio_path, transcribed_segments)
        
        if not segment_embeddings:
            # Fallback to single speaker
            segments = [{
                "speaker": "Speaker 1",
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"],
                "confidence": 1.0
            } for seg in transcribed_segments]
            
            return {
                "segments": segments,
                "speakers": ["Speaker 1"],
                "speaker_count": 1,
                "duration": self._get_audio_duration(audio_path),
                "file_name": file_name,
                "metadata": {"note": "Single speaker assumed"}
            }
        
        # Step 3: Cluster speakers
        logger.info("Step 3/3: Clustering speakers...")
        embeddings = [emb for _, emb in segment_embeddings]
        speaker_labels = self._cluster_speakers(embeddings, num_speakers)
        
        # Build result
        segments = []
        for (seg, _), label in zip(segment_embeddings, speaker_labels):
            segments.append({
                "speaker": f"Speaker {label + 1}",
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"],
                "confidence": 1.0
            })
        
        # Merge consecutive segments from same speaker
        merged = self._merge_consecutive_segments(segments)
        
        # Get unique speakers
        speakers = []
        seen = set()
        for seg in merged:
            if seg["speaker"] not in seen:
                speakers.append(seg["speaker"])
                seen.add(seg["speaker"])
        
        return {
            "segments": merged,
            "speakers": speakers,
            "speaker_count": len(speakers),
            "duration": self._get_audio_duration(audio_path),
            "file_name": file_name,
            "metadata": {
                "total_segments": len(merged),
                "language": language or "auto-detected",
                "model": self.whisper_model
            }
        }
    
    def _transcribe(self, audio_path: str, language: str = None) -> List[Dict]:
        """Transcribe audio with Groq, Faster-Whisper, or OpenAI Whisper."""
        whisper = self._get_whisper()
        if whisper is None:
            return []
        
        try:
            whisper_type = getattr(self, '_whisper_type', None)
            
            if whisper_type == "groq":
                logger.info("Transcribing with Groq API...")
                import json
                with open(audio_path, "rb") as file:
                    transcription = whisper.audio.transcriptions.create(
                        file=file,
                        model="whisper-large-v3-turbo",
                        response_format="verbose_json",
                        timestamp_granularities=["segment"],
                        language=language
                    )
                
                # Check if transcription is an object or dict
                if hasattr(transcription, "segments"):
                    segs = transcription.segments
                else:
                    segs = transcription.get("segments", [])
                
                result = []
                for segment in segs:
                    if isinstance(segment, dict):
                        result.append({
                            "start": segment["start"],
                            "end": segment["end"],
                            "text": segment["text"].strip()
                        })
                    else:
                        result.append({
                            "start": segment.start,
                            "end": segment.end,
                            "text": segment.text.strip()
                        })
                logger.info(f"Groq transcription complete: {len(result)} segments")
                return result
                
            elif whisper_type == "faster-whisper":
                # Faster-Whisper returns (generator, info)
                segments, info = whisper.transcribe(
                    audio_path,
                    language=language,
                    word_timestamps=True,
                    vad_filter=True
                )
                
                result = []
                for segment in segments:
                    result.append({
                        "start": segment.start,
                        "end": segment.end,
                        "text": segment.text.strip()
                    })
                
                logger.info(f"Transcription complete (faster-whisper): {len(result)} segments")
                return result
            else:
                # OpenAI Whisper returns dict
                result = whisper.transcribe(audio_path, language=language)
                segments = result.get("segments", []) if isinstance(result, dict) else []
                return [{"start": s["start"], "end": s["end"], "text": s["text"]}
                        for s in segments]
                
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return []
    
    def _extract_embeddings(
        self,
        audio_path: str,
        segments: List[Dict],
        min_duration: float = 0.5
    ) -> List[Tuple[Dict, np.ndarray]]:
        """Extract MFCC-based speaker embeddings for each segment."""
        try:
            audio, sr = librosa.load(audio_path, sr=self.sample_rate)
        except Exception as e:
            logger.error(f"Failed to load audio: {e}")
            return []
        
        results = []
        
        for segment in segments:
            duration = segment["end"] - segment["start"]
            if duration < min_duration:
                continue
            
            start_sample = int(segment["start"] * sr)
            end_sample = int(segment["end"] * sr)
            segment_audio = audio[start_sample:end_sample]
            
            if len(segment_audio) < sr * min_duration:
                continue
            
            try:
                embedding = self._extract_mfcc_embedding(segment_audio)
                results.append((segment, embedding))
            except Exception as e:
                logger.warning(f"Failed to extract embedding: {e}")
                continue
        
        logger.info(f"Extracted {len(results)} embeddings from {len(segments)} segments")
        return results
    
    def _extract_mfcc_embedding(self, audio: np.ndarray) -> np.ndarray:
        """Extract MFCC-based speaker embedding."""
        # Normalize audio
        audio = audio / (np.max(np.abs(audio)) + 1e-8)
        
        # Extract MFCCs
        mfccs = librosa.feature.mfcc(y=audio, sr=self.sample_rate, n_mfcc=20)
        
        # Extract delta and delta-delta
        delta_mfccs = librosa.feature.delta(mfccs)
        delta2_mfccs = librosa.feature.delta(mfccs, order=2)
        
        # Compute statistics
        features = []
        for feat in [mfccs, delta_mfccs, delta2_mfccs]:
            features.extend([
                np.mean(feat, axis=1),
                np.std(feat, axis=1),
                np.min(feat, axis=1),
                np.max(feat, axis=1)
            ])
        
        embedding = np.concatenate(features)
        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
        
        return embedding
    
    def _cluster_speakers(
        self,
        embeddings: List[np.ndarray],
        num_speakers: int = None
    ) -> List[int]:
        """Cluster embeddings into speaker groups."""
        if len(embeddings) == 0:
            return []
        if len(embeddings) == 1:
            return [0]
        
        embeddings_array = np.array(embeddings)
        
        # Compute similarity matrix
        norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
        normalized = embeddings_array / (norms + 1e-8)
        similarity = np.dot(normalized, normalized.T)
        similarity = np.clip(similarity, -1, 1)
        
        # Estimate number of speakers if not provided
        if num_speakers is None:
            num_speakers = self._estimate_num_speakers(similarity)
        
        num_speakers = max(self.min_speakers, min(num_speakers, len(embeddings)))
        
        if num_speakers == 1:
            return [0] * len(embeddings)
        
        # Spectral clustering
        try:
            affinity = (similarity + 1) / 2
            clustering = SpectralClustering(
                n_clusters=num_speakers,
                affinity="precomputed",
                random_state=42
            )
            labels = clustering.fit_predict(affinity)
        except Exception:
            # Fallback to agglomerative
            distance = 1 - similarity
            clustering = AgglomerativeClustering(
                n_clusters=num_speakers,
                metric="precomputed",
                linkage="average"
            )
            labels = clustering.fit_predict(distance)
        
        # Smooth labels
        if len(labels) > 3:
            labels = median_filter(labels.astype(float), size=3, mode='nearest').astype(int)
        
        return labels.tolist()
    
    def _estimate_num_speakers(self, similarity_matrix: np.ndarray) -> int:
        """Estimate optimal number of speakers."""
        n = similarity_matrix.shape[0]
        if n < 2:
            return 1
        
        max_clusters = min(self.max_speakers, n - 1)
        if max_clusters < 2:
            return 1
        
        distance = 1 - similarity_matrix
        best_score = -1
        best_n = 2
        
        for k in range(2, max_clusters + 1):
            try:
                clustering = AgglomerativeClustering(
                    n_clusters=k,
                    metric="precomputed",
                    linkage="average"
                )
                labels = clustering.fit_predict(distance)
                
                if len(set(labels)) < 2:
                    continue
                
                score = silhouette_score(distance, labels, metric="precomputed")
                if score > best_score:
                    best_score = score
                    best_n = k
            except Exception:
                continue
        
        return best_n
    
    def _merge_consecutive_segments(
        self,
        segments: List[Dict],
        max_gap: float = 1.0
    ) -> List[Dict]:
        """Merge consecutive segments from the same speaker."""
        if not segments:
            return []
        
        # Sort by start time
        segments = sorted(segments, key=lambda x: x["start"])
        
        merged = [segments[0].copy()]
        
        for seg in segments[1:]:
            last = merged[-1]
            
            if seg["speaker"] == last["speaker"] and (seg["start"] - last["end"]) <= max_gap:
                merged[-1] = {
                    "speaker": last["speaker"],
                    "start": last["start"],
                    "end": seg["end"],
                    "text": f"{last['text']} {seg['text']}".strip(),
                    "confidence": min(last.get("confidence", 1.0), seg.get("confidence", 1.0))
                }
            else:
                merged.append(seg.copy())
        
        return merged
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration in seconds."""
        try:
            return round(librosa.get_duration(path=audio_path), 2)
        except Exception:
            return 0.0


# Keep the original VoiceProcessor for backwards compatibility
VoiceProcessor = EnhancedVoiceProcessor
