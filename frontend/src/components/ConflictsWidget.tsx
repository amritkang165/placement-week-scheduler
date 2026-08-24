import { useEffect, useState } from "react";
import { ShieldAlert } from "lucide-react";
import { api } from "@/lib/api";
import type { Conflict } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const TYPE_VARIANT: Record<string, "success" | "destructive" | "warning" | "info"> = {
  STUDENT_CLASH: "destructive",
  ROOM_CLASH: "warning",
  PANEL_CLASH: "warning",
};

export default function ConflictsWidget() {
  const [conflicts, setConflicts] = useState<Conflict[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getConflicts()
      .then((c) => setConflicts(c))
      .catch(() => setConflicts([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <Card className={conflicts.length > 0 ? "border-red-200" : undefined}>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <ShieldAlert className="h-4 w-4" />
          Conflicts
        </CardTitle>
        <Badge variant={conflicts.length === 0 ? "success" : "destructive"}>
          {loading ? "…" : `${conflicts.length} issue${conflicts.length === 1 ? "" : "s"}`}
        </Badge>
      </CardHeader>
      <CardContent className="p-0">
        {!loading && conflicts.length === 0 ? (
          <p className="p-4 text-sm text-muted-foreground">
            No clashes detected. Every student, room, and panel is exclusively booked.
          </p>
        ) : (
          <ul className="divide-y">
            {conflicts.map((c) => (
              <li key={c.conflict_id} className="flex items-start gap-3 px-4 py-2.5 text-sm">
                <Badge variant={TYPE_VARIANT[c.type]} className="mt-0.5 shrink-0">
                  {c.type.replace("_", " ")}
                </Badge>
                <div>
                  <p className="font-medium">{c.message}</p>
                  <p className="text-xs text-muted-foreground">
                    Interviews: {c.interview_ids.join(", ")}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
