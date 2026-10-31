"use client";

import { useSyncExternalStore } from "react";

const KEY = "aod.source";
const EVENT = "aod-source";

function read(): string {
  try {
    return localStorage.getItem(KEY) ?? "app";
  } catch {
    return "app";
  }
}

function subscribe(cb: () => void) {
  window.addEventListener("storage", cb);
  window.addEventListener(EVENT, cb);
  return () => {
    window.removeEventListener("storage", cb);
    window.removeEventListener(EVENT, cb);
  };
}

export function useSource() {
  const source = useSyncExternalStore(subscribe, read, () => "app");
  const setSource = (s: string) => {
    try {
      localStorage.setItem(KEY, s);
    } catch {}
    window.dispatchEvent(new Event(EVENT));
  };
  return { source, setSource };
}
