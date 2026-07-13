import { apiFetch, API_URL } from "@/lib/api/client";
import type {
  ChunkSummary,
  TextbookChunk,
  TextbookSection,
  TextbookTopic,
} from "@/lib/api/types";

export function listSections(): Promise<TextbookSection[]> {
  return apiFetch<TextbookSection[]>("/api/textbook/sections");
}

export function listTopics(section?: string): Promise<TextbookTopic[]> {
  const query = section ? `?section=${encodeURIComponent(section)}` : "";
  return apiFetch<TextbookTopic[]>(`/api/textbook/topics${query}`);
}

export function listChunks(topic: string): Promise<ChunkSummary[]> {
  return apiFetch<ChunkSummary[]>(
    `/api/textbook/topics/${encodeURIComponent(topic)}/chunks`,
  );
}

export function getChunk(topic: string, chunkIdx: number): Promise<TextbookChunk> {
  return apiFetch<TextbookChunk>(
    `/api/textbook/topics/${encodeURIComponent(topic)}/chunks/${chunkIdx}`,
  );
}

export function getAudioUrl(topic: string, chunkIdx: number): string {
  return `${API_URL}/api/textbook/topics/${encodeURIComponent(topic)}/chunks/${chunkIdx}/audio`;
}

export async function fetchAudioBlob(topic: string, chunkIdx: number): Promise<Blob> {
  const response = await fetch(getAudioUrl(topic, chunkIdx), {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error("Failed to load audio");
  }
  return response.blob();
}
