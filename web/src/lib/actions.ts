"use server";

import { revalidatePath } from "next/cache";
import * as api from "./api";
import { RateLimitError } from "./api";

export type ActionResult = { ok: true } | { ok: false; error: string };

export async function addTopicAction(phrase: string): Promise<ActionResult> {
  const trimmed = phrase.trim();
  if (trimmed.length < 3 || trimmed.length > 60) {
    return { ok: false, error: "Topic must be 3–60 characters." };
  }
  try {
    await api.createTopic(trimmed);
    revalidatePath("/topics");
    revalidatePath("/digest");
    return { ok: true };
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e.message : "Failed to add topic." };
  }
}

export async function deleteTopicAction(id: string): Promise<ActionResult> {
  await api.deleteTopic(id);
  revalidatePath("/topics");
  revalidatePath("/digest");
  return { ok: true };
}

export async function reorderTopicsAction(orderedIds: string[]): Promise<ActionResult> {
  await api.reorderTopics(orderedIds);
  revalidatePath("/topics");
  revalidatePath("/digest");
  return { ok: true };
}

export async function refreshCardAction(
  topicId: string
): Promise<ActionResult> {
  try {
    await api.refreshCard(topicId);
    revalidatePath("/digest");
    return { ok: true };
  } catch (e) {
    if (e instanceof RateLimitError) {
      return { ok: false, error: e.message };
    }
    return { ok: false, error: "Refresh failed. Try again." };
  }
}

export async function updateSettingsAction(data: {
  delivery_time?: string;
  timezone?: string;
}): Promise<ActionResult> {
  await api.updateSettings(data);
  revalidatePath("/topics");
  return { ok: true };
}

export async function completeOnboardingAction(
  phrases: string[],
  deliveryTime: string,
  timezone: string
): Promise<ActionResult> {
  try {
    for (const phrase of phrases) {
      const trimmed = phrase.trim();
      if (trimmed.length >= 3 && trimmed.length <= 60) {
        await api.createTopic(trimmed);
      }
    }
    await api.updateSettings({ delivery_time: deliveryTime, timezone });
    await api.generateDigest();
    revalidatePath("/digest");
    revalidatePath("/topics");
    return { ok: true };
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e.message : "Onboarding failed." };
  }
}
