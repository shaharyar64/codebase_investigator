"use client";

import * as React from "react";

/**
 * AbortController for the in-flight chat stream; abort on unmount or new send.
 */
export function useChatStreamAbort() {
  const controllerRef = React.useRef<AbortController | null>(null);

  React.useEffect(() => {
    return () => {
      controllerRef.current?.abort();
    };
  }, []);

  const refreshController = React.useCallback(() => {
    controllerRef.current?.abort();
    const next = new AbortController();
    controllerRef.current = next;
    return next;
  }, []);

  return { controllerRef, refreshController };
}
