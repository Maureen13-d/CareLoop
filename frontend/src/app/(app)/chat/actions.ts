"use server";

import { ApiError, api } from "@/lib/api";

export type AssistantReply = {
  reply_text: string;
  barrier_flags: { flag: string; status: "suggested" | "confirmed"; confidence: number }[];
  needs_human: boolean;
  sources: string[];
  tier: string;
  review_status: string;
};

export async function askAssistant(input: {
  text?: string;
  confirm_flag?: string;
}): Promise<AssistantReply> {
  try {
    return await api<AssistantReply>("/assistant/message", {
      method: "POST",
      body: JSON.stringify({ channel: "web", ...input }),
    });
  } catch (error) {
    const message = error instanceof ApiError ? error.message : "The chat could not reply.";
    return {
      reply_text: message,
      barrier_flags: [],
      needs_human: false,
      sources: [],
      tier: "fallback",
      review_status: "draft",
    };
  }
}
