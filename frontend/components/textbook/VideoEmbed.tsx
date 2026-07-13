const ALLOWED_HOSTS = new Set([
  "youtube.com",
  "www.youtube.com",
  "youtu.be",
  "m.youtube.com",
  "vk.com",
  "www.vk.com",
  "vkvideo.ru",
  "www.vkvideo.ru",
]);

export function parseVideoEmbedUrl(videoUrl: string): string | null {
  let parsed: URL;
  try {
    parsed = new URL(videoUrl);
  } catch {
    return null;
  }

  if (parsed.protocol !== "https:") {
    return null;
  }

  const host = parsed.hostname.toLowerCase();
  if (!ALLOWED_HOSTS.has(host)) {
    return null;
  }

  if (host === "youtu.be") {
    const videoId = parsed.pathname.replace(/^\//, "");
    return videoId ? `https://www.youtube.com/embed/${videoId}` : null;
  }

  if (host.includes("youtube.com")) {
    const videoId = parsed.searchParams.get("v");
    if (videoId) {
      return `https://www.youtube.com/embed/${videoId}`;
    }
    const embedMatch = parsed.pathname.match(/^\/embed\/([^/]+)/);
    if (embedMatch?.[1]) {
      return `https://www.youtube.com/embed/${embedMatch[1]}`;
    }
    return null;
  }

  const vkMatch = parsed.pathname.match(/\/video(-?\d+)_(\d+)/);
  if (vkMatch) {
    const oid = vkMatch[1];
    const id = vkMatch[2];
    return `https://vk.com/video_ext.php?oid=${oid}&id=${id}&hd=2`;
  }

  return null;
}

export function VideoEmbed({ videoUrl }: { videoUrl: string }) {
  const embedSrc = parseVideoEmbedUrl(videoUrl);
  if (!embedSrc) {
    return null;
  }

  return (
    <div className="chem-video-embed">
      <iframe
        src={embedSrc}
        title="Видео к теме"
        loading="lazy"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
        sandbox="allow-scripts allow-same-origin allow-presentation allow-popups"
      />
    </div>
  );
}
