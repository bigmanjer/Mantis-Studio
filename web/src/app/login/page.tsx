import { Suspense } from "react";
import AuthForm from "@/components/AuthForm";
import SiteHeader from "@/components/SiteHeader";

export default function Page() {
  return (
    <>
      <SiteHeader />
      <main className="flex min-h-[calc(100vh-4rem)] items-center justify-center px-4 py-12">
        <Suspense>
          <AuthForm mode="login" />
        </Suspense>
      </main>
    </>
  );
}
