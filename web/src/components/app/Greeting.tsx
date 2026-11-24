"use client";
import { useEffect, useState } from "react";

/** Greets by the writer's own clock (the server runs on UTC, so this must render in the browser). */
export default function Greeting({ name }: { name: string }) {
  const [greeting, setGreeting] = useState("Welcome back");
  useEffect(() => {
    const hour = new Date().getHours();
    setGreeting(hour < 5 ? "Writing late" : hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening");
  }, []);
  return (
    <>
      {greeting}, {name}
    </>
  );
}
