import { apiFetch } from "@/lib/api/client";

export type LeadPayload = {
  name: string;
  phone: string;
  school_class: "8" | "9" | "10" | "11";
  goal: "ege" | "oge" | "school";
  comment?: string;
  source_page: string;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
};

export type LeadCreated = {
  id: string;
  status: "accepted";
};

export async function submitLead(payload: LeadPayload): Promise<LeadCreated> {
  return apiFetch<LeadCreated>("/api/leads", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
