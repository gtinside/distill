"use server";

import { revalidatePath } from "next/cache";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import * as api from "./api";
import { RateLimitError } from "./api";
import { DEMO_COOKIE } from "./demo";

export type ActionResult = { ok: true } | { ok: false; error: string };

export async function addTopicAction(phrase: string): Promise<ActionResult> {
  const trimmed = phrase.trim();
  if (trimmed.length < 3 || trimmed.length > 60) {
    return { ok: false, error: "Topic must be 3–60 characters." };
  }
  try {
    await api.createTopic(trimmed);
    revalidatePath("/topics");
    revalidatePath("/");
    return { ok: true };
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e.message : "Failed to add topic." };
  }
}

// Follow a trending Topic = add it to the user's list (reuses validation + cap).
export async function followTopicAction(phrase: string): Promise<ActionResult> {
  try {
    await api.createTopic(phrase.trim());
    revalidatePath("/");
    revalidatePath("/topics");
    return { ok: true };
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Couldn’t follow this topic.";
    return { ok: false, error: msg.includes("10") ? "You’re at the 10-topic limit." : msg };
  }
}

export async function deleteTopicAction(id: string): Promise<ActionResult> {
  await api.deleteTopic(id);
  revalidatePath("/topics");
  revalidatePath("/");
  return { ok: true };
}

export async function reorderTopicsAction(orderedIds: string[]): Promise<ActionResult> {
  await api.reorderTopics(orderedIds);
  revalidatePath("/topics");
  revalidatePath("/");
  return { ok: true };
}

export async function refreshCardAction(topicId: string): Promise<ActionResult> {
  try {
    await api.refreshCard(topicId);
    revalidatePath("/");
    return { ok: true };
  } catch (e) {
    if (e instanceof RateLimitError) return { ok: false, error: e.message };
    return { ok: false, error: "Refresh failed. Try again." };
  }
}

// Kick off digest generation (runs in the background on the API) and return
// immediately — the client polls by refreshing until cards appear.
export async function generateDigestAction(): Promise<ActionResult> {
  try {
    await api.generateDigest();
    return { ok: true };
  } catch (e) {
    return {
      ok: false,
      error: e instanceof Error ? e.message : "Couldn’t start digest generation.",
    };
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
    revalidatePath("/");
    revalidatePath("/topics");
    return { ok: true };
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e.message : "Onboarding failed." };
  }
}

// --- Demo session (no real auth) ---

export async function enterDemoAction() {
  const store = await cookies();
  store.set(DEMO_COOKIE, "1", { path: "/", maxAge: 60 * 60 * 24 * 30 });
  redirect("/");
}

export async function exitDemoAction() {
  const store = await cookies();
  store.delete(DEMO_COOKIE);
  redirect("/");
}
