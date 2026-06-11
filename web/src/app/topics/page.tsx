import { getSettings, getTopics } from "@/lib/api";
import { NavBar, Card } from "@/components/ui";
import { TopicsManager } from "@/components/TopicsManager";
import { SettingsPanel } from "@/components/SettingsPanel";

export const dynamic = "force-dynamic";

export default async function TopicsPage() {
  const [topics, settings] = await Promise.all([getTopics(), getSettings()]);

  return (
    <>
      <NavBar active="topics" />
      <main className="mx-auto w-full max-w-2xl flex-1 space-y-6 px-4 py-6">
        <section>
          <h1 className="mb-4 font-display text-3xl font-medium tracking-[-0.01em]">
            Topics
          </h1>
          <Card>
            <TopicsManager initial={topics} />
          </Card>
        </section>

        <section>
          <h2 className="mb-4 font-display text-xl font-medium tracking-[-0.01em]">
            Settings
          </h2>
          <Card>
            <SettingsPanel settings={settings} />
          </Card>
        </section>
      </main>
    </>
  );
}
