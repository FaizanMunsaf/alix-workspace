import { request } from "./client";

export type DiffChange = {
  status: "added" | "deleted" | "modified";
  path: string;
  node_type: string;
  title: string | null;
  fields: string[];
};

export type DiffResponse = {
  added: DiffChange[];
  deleted: DiffChange[];
  modified: DiffChange[];
  summary: Record<string, number>;
};

export function diffVersions(fromVersionId: string, toVersionId: string) {
  return request<DiffResponse>("/documents/diff", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      from_version_id: fromVersionId,
      to_version_id: toVersionId,
    }),
  });
}
