"use client";

import { AlertTriangle, ShieldCheck, ShieldX } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { AuditResult } from "@/types/api";

interface AuditPanelProps {
  audit: AuditResult;
}

export function AuditPanel({ audit }: AuditPanelProps) {
  return (
    <div className="space-y-2 rounded-md border bg-muted/30 p-3">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-sm font-medium">
          {audit.verified ? (
            <ShieldCheck className="h-4 w-4 text-emerald-600" />
          ) : (
            <ShieldX className="h-4 w-4 text-red-600" />
          )}
          <span>Audit</span>
        </div>
        <Badge variant={audit.verified ? "success" : "warning"}>
          {audit.verified ? "verified" : "review"}
        </Badge>
      </div>
      {audit.details ? (
        <p className="text-sm text-muted-foreground">{audit.details}</p>
      ) : null}
      {[...audit.warnings, ...audit.unsupported_claims].length ? (
        <div className="space-y-1">
          {[...audit.warnings, ...audit.unsupported_claims].map((warning) => (
            <div
              key={warning}
              className="flex gap-2 text-sm text-amber-700"
            >
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{warning}</span>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

