"use client";

import { useState, useTransition } from "react";
import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  arrayMove,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import type { Topic } from "@/lib/types";
import { TOPIC_LIMIT, TOPIC_MAX, TOPIC_MIN } from "@/lib/types";
import {
  addTopicAction,
  deleteTopicAction,
  reorderTopicsAction,
} from "@/lib/actions";
import { Button } from "./ui";

function SortableRow({
  topic,
  onDelete,
}: {
  topic: Topic;
  onDelete: (id: string) => void;
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: topic.id });

  return (
    <li
      ref={setNodeRef}
      style={{ transform: CSS.Transform.toString(transform), transition }}
      className={`flex items-center gap-3 rounded-lg border border-border bg-surface px-3 py-2.5 ${
        isDragging ? "shadow-lg" : ""
      }`}
    >
      <button
        {...attributes}
        {...listeners}
        className="cursor-grab touch-none text-muted hover:text-foreground"
        aria-label="Drag to reorder"
      >
        ⠿
      </button>
      <span className="flex-1 text-sm">{topic.phrase}</span>
      <button
        onClick={() => onDelete(topic.id)}
        className="text-muted hover:text-danger"
        aria-label={`Delete ${topic.phrase}`}
      >
        ✕
      </button>
    </li>
  );
}

export function TopicsManager({ initial }: { initial: Topic[] }) {
  const [topics, setTopics] = useState<Topic[]>(initial);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [, startTransition] = useTransition();
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 4 } }));

  const draftValid =
    draft.trim().length >= TOPIC_MIN && draft.trim().length <= TOPIC_MAX;
  const atLimit = topics.length >= TOPIC_LIMIT;

  async function add(e: React.FormEvent) {
    e.preventDefault();
    if (!draftValid || atLimit) return;
    const phrase = draft.trim();
    setError(null);
    setDraft("");
    const res = await addTopicAction(phrase);
    if (!res.ok) {
      setError(res.error);
      return;
    }
    // Optimistic; server is source of truth on next load.
    setTopics((prev) => [
      ...prev,
      { id: `tmp-${Date.now()}`, phrase, display_order: prev.length },
    ]);
  }

  function remove(id: string) {
    setTopics((prev) => prev.filter((t) => t.id !== id));
    startTransition(() => {
      deleteTopicAction(id);
    });
  }

  function onDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const oldIndex = topics.findIndex((t) => t.id === active.id);
    const newIndex = topics.findIndex((t) => t.id === over.id);
    const next = arrayMove(topics, oldIndex, newIndex);
    setTopics(next);
    startTransition(() => {
      reorderTopicsAction(next.map((t) => t.id));
    });
  }

  return (
    <div>
      <form className="flex gap-2" onSubmit={add}>
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          maxLength={TOPIC_MAX}
          placeholder={atLimit ? "Topic limit reached" : "Add a topic…"}
          disabled={atLimit}
          className="flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-accent disabled:opacity-50"
        />
        <Button type="submit" disabled={!draftValid || atLimit}>
          Add
        </Button>
      </form>
      {error && <p className="mt-2 text-sm text-danger">{error}</p>}
      <p className="mt-2 text-xs text-muted">
        {topics.length}/{TOPIC_LIMIT} topics · drag to reorder
      </p>

      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={onDragEnd}>
        <SortableContext items={topics.map((t) => t.id)} strategy={verticalListSortingStrategy}>
          <ul className="mt-4 space-y-2">
            {topics.map((t) => (
              <SortableRow key={t.id} topic={t} onDelete={remove} />
            ))}
          </ul>
        </SortableContext>
      </DndContext>

      {topics.length === 0 && (
        <p className="mt-4 text-sm text-muted">No topics yet. Add your first above.</p>
      )}
    </div>
  );
}
