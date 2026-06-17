"use client";

import {
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
  type CSSProperties,
  type KeyboardEvent,
} from "react";

import { fetchAudioBlob } from "@/lib/api/textbook";

const SEEK_STEP_SECONDS = 5;

export function formatAudioTime(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) {
    return "0:00";
  }
  const total = Math.floor(seconds);
  const mins = Math.floor(total / 60);
  const secs = total % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

function PlayIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="h-5 w-5 fill-current">
      <path d="M8 5.14v13.72L19 12 8 5.14z" />
    </svg>
  );
}

function PauseIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="h-5 w-5 fill-current">
      <path d="M6 5h4v14H6V5zm8 0h4v14h-4V5z" />
    </svg>
  );
}

function CustomAudioControls({ src }: { src: string }) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const progressId = useId();
  const volumeId = useId();
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [playbackError, setPlaybackError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState("");

  const announce = useCallback((message: string) => {
    setStatusMessage(message);
  }, []);

  const togglePlayPause = useCallback(async () => {
    const audio = audioRef.current;
    if (!audio) {
      return;
    }

    try {
      if (audio.paused) {
        await audio.play();
      } else {
        audio.pause();
      }
    } catch {
      setPlaybackError("Не удалось воспроизвести аудио.");
      announce("Ошибка воспроизведения");
    }
  }, [announce]);

  const seekBy = useCallback(
    (deltaSeconds: number) => {
      const audio = audioRef.current;
      if (!audio || !Number.isFinite(audio.duration)) {
        return;
      }
      const nextTime = Math.min(
        Math.max(0, audio.currentTime + deltaSeconds),
        audio.duration,
      );
      audio.currentTime = nextTime;
      setCurrentTime(nextTime);
    },
    [],
  );

  const handlePlayerKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    const target = event.target as HTMLElement;
    const tag = target.tagName;

    if (tag === "INPUT") {
      return;
    }

    if (tag === "BUTTON" && (event.key === " " || event.key === "Enter")) {
      return;
    }

    if (event.key === " " || event.key === "Enter") {
      event.preventDefault();
      void togglePlayPause();
      return;
    }

    if (event.key === "ArrowLeft") {
      event.preventDefault();
      seekBy(-SEEK_STEP_SECONDS);
      return;
    }

    if (event.key === "ArrowRight") {
      event.preventDefault();
      seekBy(SEEK_STEP_SECONDS);
    }
  };

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) {
      return;
    }

    audio.volume = volume;

    const onTimeUpdate = () => {
      setCurrentTime(audio.currentTime);
    };
    const onLoadedMetadata = () => {
      setDuration(Number.isFinite(audio.duration) ? audio.duration : 0);
      setPlaybackError(null);
    };
    const onPlay = () => {
      setIsPlaying(true);
      announce("Воспроизведение");
    };
    const onPause = () => {
      setIsPlaying(false);
      announce("Пауза");
    };
    const onEnded = () => {
      setIsPlaying(false);
      announce("Воспроизведение завершено");
    };
    const onError = () => {
      setIsPlaying(false);
      setPlaybackError("Не удалось воспроизвести аудио.");
      announce("Ошибка воспроизведения");
    };

    audio.addEventListener("timeupdate", onTimeUpdate);
    audio.addEventListener("loadedmetadata", onLoadedMetadata);
    audio.addEventListener("play", onPlay);
    audio.addEventListener("pause", onPause);
    audio.addEventListener("ended", onEnded);
    audio.addEventListener("error", onError);

    return () => {
      audio.removeEventListener("timeupdate", onTimeUpdate);
      audio.removeEventListener("loadedmetadata", onLoadedMetadata);
      audio.removeEventListener("play", onPlay);
      audio.removeEventListener("pause", onPause);
      audio.removeEventListener("ended", onEnded);
      audio.removeEventListener("error", onError);
    };
  }, [announce, src, volume]);

  useEffect(() => {
    setCurrentTime(0);
    setDuration(0);
    setIsPlaying(false);
    setPlaybackError(null);
    setStatusMessage("");
  }, [src]);

  if (playbackError) {
    return <p className="text-sm text-red-600">{playbackError}</p>;
  }

  const progressMax = duration > 0 ? duration : 1;
  const progressValue = duration > 0 ? currentTime : 0;
  const progressPercent =
    duration > 0 ? `${(currentTime / duration) * 100}%` : "0%";

  return (
    <div
      className="chem-audio-player"
      role="group"
      aria-label="Аудиоплеер"
      tabIndex={0}
      onKeyDown={handlePlayerKeyDown}
    >
      <audio ref={audioRef} src={src} preload="metadata" />

      <button
        type="button"
        className="chem-audio-player__play"
        aria-label={isPlaying ? "Пауза" : "Воспроизведение"}
        onClick={() => {
          void togglePlayPause();
        }}
      >
        {isPlaying ? <PauseIcon /> : <PlayIcon />}
      </button>

      <div className="chem-audio-player__main">
        <input
          id={progressId}
          type="range"
          className="chem-audio-player__progress"
          min={0}
          max={progressMax}
          step={0.1}
          value={progressValue}
          disabled={duration <= 0}
          style={{ "--progress": progressPercent } as CSSProperties}
          aria-label="Прогресс воспроизведения"
          aria-valuemin={0}
          aria-valuemax={Math.floor(duration)}
          aria-valuenow={Math.floor(currentTime)}
          aria-valuetext={`${formatAudioTime(currentTime)} из ${formatAudioTime(duration)}`}
          onChange={(event) => {
            const audio = audioRef.current;
            if (!audio) {
              return;
            }
            const nextTime = Number(event.target.value);
            audio.currentTime = nextTime;
            setCurrentTime(nextTime);
          }}
        />

        <div className="chem-audio-player__meta">
          <span className="chem-audio-player__time" aria-hidden="true">
            {formatAudioTime(currentTime)} / {formatAudioTime(duration)}
          </span>

          <label className="sr-only" htmlFor={volumeId}>
            Громкость
          </label>
          <input
            id={volumeId}
            type="range"
            className="chem-audio-player__volume"
            min={0}
            max={1}
            step={0.05}
            value={volume}
            aria-label="Громкость"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={Math.round(volume * 100)}
            aria-valuetext={`${Math.round(volume * 100)}%`}
            onChange={(event) => {
              const nextVolume = Number(event.target.value);
              setVolume(nextVolume);
              if (audioRef.current) {
                audioRef.current.volume = nextVolume;
              }
            }}
          />
        </div>
      </div>

      <span className="sr-only" aria-live="polite">
        {statusMessage}
      </span>
    </div>
  );
}

export function AudioPlayer({
  topic,
  chunkIdx,
  hasAudio,
}: {
  topic: string;
  chunkIdx: number;
  hasAudio: boolean;
}) {
  const [src, setSrc] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!hasAudio) {
      setSrc(null);
      setError(null);
      setLoading(false);
      return;
    }

    let objectUrl: string | null = null;
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      setSrc(null);
      try {
        const blob = await fetchAudioBlob(topic, chunkIdx);
        if (cancelled) {
          return;
        }
        objectUrl = URL.createObjectURL(blob);
        setSrc(objectUrl);
        setError(null);
      } catch {
        if (!cancelled) {
          setError("Не удалось загрузить аудио.");
          setSrc(null);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();

    return () => {
      cancelled = true;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [topic, chunkIdx, hasAudio]);

  if (!hasAudio) {
    return null;
  }

  if (error) {
    return <p className="text-sm text-red-600">{error}</p>;
  }

  if (loading || !src) {
    return (
      <p className="text-sm text-zinc-500" aria-live="polite">
        Загрузка аудио…
      </p>
    );
  }

  return <CustomAudioControls src={src} />;
}
