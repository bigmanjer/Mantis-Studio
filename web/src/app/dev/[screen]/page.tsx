// Development-only design previews of signed-in screens with sample data.
// Returns 404 in production builds. Saving/AI calls won't work here (no database).
import { notFound } from "next/navigation";
import AppShell from "@/components/app/AppShell";
import ProjectsView from "@/components/app/ProjectsView";
import SettingsView from "@/components/app/SettingsView";
import { ConfirmProvider } from "@/components/ui/ConfirmDialog";
import Workspace from "@/components/workspace/Workspace";
import { PLANS } from "@/lib/plans";
import { SAMPLE_CHAPTERS, SAMPLE_ENTITIES, SAMPLE_PROJECT, SAMPLE_PROJECTS } from "./sample";

const user = { email: "writer@example.com", planId: "free" as const, planName: "Free", aiUsed: 9_400, aiLimit: 25_000 };

export default async function DevPreview({ params }: { params: Promise<{ screen: string }> }) {
  if (process.env.NODE_ENV === "production") notFound();
  const { screen } = await params;

  switch (screen) {
    case "dashboard":
      return (
        <AppShell user={user}>
          <ProjectsView projects={SAMPLE_PROJECTS} planName="Free" maxProjects={2} email={user.email} />
        </AppShell>
      );
    case "dashboard-empty":
      return (
        <AppShell user={user}>
          <ProjectsView projects={[]} planName="Free" maxProjects={2} email={user.email} />
        </AppShell>
      );
    case "settings":
      return (
        <AppShell user={user}>
          <SettingsView
            data={{
              email: user.email,
              plan: PLANS.free,
              subscriptionStatus: null,
              periodEnd: null,
              hasBillingAccount: false,
              aiUsed: user.aiUsed,
              aiProvider: "groq",
              aiModel: "",
              maskedKey: null,
            }}
            flash={{}}
          />
        </AppShell>
      );
    case "workspace":
      return (
        <ConfirmProvider>
          <Workspace initialProject={SAMPLE_PROJECT} initialChapters={SAMPLE_CHAPTERS} initialEntities={SAMPLE_ENTITIES}
            initialLinks={[]}
            autoAllowed art="on" docxExport={false} />
        </ConfirmProvider>
      );
    default:
      notFound();
  }
}
