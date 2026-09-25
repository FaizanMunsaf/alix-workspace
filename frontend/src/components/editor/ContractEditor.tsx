import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from "react";
import { Extension } from "@tiptap/core";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Image from "@tiptap/extension-image";
import Table from "@tiptap/extension-table";
import TableRow from "@tiptap/extension-table-row";
import TableCell from "@tiptap/extension-table-cell";
import TableHeader from "@tiptap/extension-table-header";
import { Plugin, PluginKey } from "@tiptap/pm/state";
import { Decoration, DecorationSet } from "@tiptap/pm/view";

export type EditorSelection = {
  from: number;
  to: number;
  text: string;
};

export type ContractEditorHandle = {
  getHTML: () => string;
  getSelection: () => EditorSelection | null;
  jumpToText: (text: string) => boolean;
};

export type PendingRedline = {
  before: string;
  after: string;
};

type Props = {
  documentId: string | null;
  html: string;
  processingStatus: string | null;
  contentNonce: number;
  editable: boolean;
  pendingRedlines?: PendingRedline[];
  onDirty: () => void;
  onSelectionChange: (selection: EditorSelection | null) => void;
};

const pendingRedlineKey = new PluginKey("pendingRedlines");

function PendingRedlineExtension(getRedlines: () => PendingRedline[]) {
  return Extension.create({
    name: "pendingRedlines",
    addProseMirrorPlugins() {
      return [
        new Plugin({
          key: pendingRedlineKey,
          props: {
            decorations(state) {
              const redlines = getRedlines().filter(
                (item) => item.before.trim() || item.after.trim(),
              );
              if (!redlines.length) return DecorationSet.empty;
              const decorations = [];
              for (const redline of redlines) {
                const range = findTextRange(state.doc, redline.before);
                if (!range) continue;
                decorations.push(
                  Decoration.inline(range.from, range.to, {
                    class: "redline-deleted",
                  }),
                );
                if (redline.after.trim()) {
                  decorations.push(
                    Decoration.widget(range.to, () => {
                      const mark = document.createElement("span");
                      mark.className = "redline-inserted";
                      mark.textContent = redline.after;
                      mark.title = "Proposed replacement (pending)";
                      return mark;
                    }),
                  );
                }
              }
              return DecorationSet.create(state.doc, decorations);
            },
          },
        }),
      ];
    },
  });
}

export const ContractEditor = forwardRef<ContractEditorHandle, Props>(
  function ContractEditor(
    {
      documentId,
      html,
      processingStatus,
      contentNonce,
      editable,
      pendingRedlines = [],
      onDirty,
      onSelectionChange,
    },
    ref,
  ) {
    const appliedKey = useRef("");
    const pendingRef = useRef(pendingRedlines);
    pendingRef.current = pendingRedlines;
    const [, setToolbarTick] = useState(0);

    const extensions = useMemo(
      () => [
        StarterKit,
        Image.configure({
          inline: false,
          allowBase64: true,
        }),
        Table.configure({ resizable: false }),
        TableRow,
        TableHeader,
        TableCell,
        PendingRedlineExtension(() => pendingRef.current),
      ],
      [],
    );

    const editor = useEditor({
      extensions,
      content: "<p></p>",
      editable,
      editorProps: {
        attributes: { class: "tiptap" },
      },
      onUpdate: () => onDirty(),
      onTransaction: () => setToolbarTick((value) => value + 1),
      onSelectionUpdate: ({ editor: current }) => {
        const { from, to, empty } = current.state.selection;
        if (empty) {
          onSelectionChange(null);
          return;
        }
        onSelectionChange({
          from,
          to,
          text: current.state.doc.textBetween(from, to, " "),
        });
      },
    });

    useImperativeHandle(ref, () => ({
      getHTML: () => editor?.getHTML() ?? "",
      getSelection: () => {
        if (!editor) return null;
        const { from, to, empty } = editor.state.selection;
        if (empty) return null;
        return {
          from,
          to,
          text: editor.state.doc.textBetween(from, to, " "),
        };
      },
      jumpToText: (text: string) => {
        if (!editor) return false;
        const range = findTextRange(editor.state.doc, text);
        if (!range) return false;
        editor.chain().focus().setTextSelection(range).scrollIntoView().run();
        onSelectionChange({
          from: range.from,
          to: range.to,
          text: editor.state.doc.textBetween(range.from, range.to, " "),
        });
        return true;
      },
    }));

    useEffect(() => {
      editor?.setEditable(editable);
    }, [editor, editable]);

    useEffect(() => {
      if (!editor || !documentId) return;
      if (processingStatus === "pending" || processingStatus === "processing") return;
      const key = `${documentId}:${processingStatus}:${contentNonce}`;
      if (appliedKey.current === key) return;
      editor.commands.setContent(html || "<p></p>", false);
      appliedKey.current = key;
    }, [documentId, processingStatus, contentNonce, html, editor]);

    useEffect(() => {
      if (!editor) return;
      // Force decoration rebuild when pending redlines change.
      editor.view.dispatch(editor.state.tr.setMeta(pendingRedlineKey, Date.now()));
    }, [editor, pendingRedlines]);

    if (!documentId) {
      return (
        <div className="editor-empty">
          <h2>No contract open</h2>
          <p>Upload a .docx file or select a stored document to edit it.</p>
        </div>
      );
    }

    if (processingStatus === "pending" || processingStatus === "processing") {
      return (
        <div className="editor-empty">
          <h2>Parsing contract…</h2>
          <p>The document is being imported. The editor will open when that finishes.</p>
        </div>
      );
    }

    if (processingStatus === "failed") {
      return (
        <div className="editor-empty">
          <h2>Import failed</h2>
          <p>This file could not be parsed. Try another .docx.</p>
        </div>
      );
    }

    const pendingCount = pendingRedlines.filter((item) => item.before.trim()).length;

    return (
      <section className="editor-page">
        {pendingCount > 0 && (
          <p className="pending-redline-banner">
            {pendingCount} pending AI redline{pendingCount === 1 ? "" : "s"}: struck text is
            original, green insert is the proposal — Accept or Reject in Edit / History.
          </p>
        )}
        {editor && (
          <div className="editor-toolbar">
            <button
              type="button"
              disabled={!editor.can().undo()}
              onClick={() => editor.chain().focus().undo().run()}
            >
              Undo
            </button>
            <button
              type="button"
              disabled={!editor.can().redo()}
              onClick={() => editor.chain().focus().redo().run()}
            >
              Redo
            </button>
            <button
              type="button"
              className={editor.isActive("bold") ? "active" : ""}
              onClick={() => editor.chain().focus().toggleBold().run()}
            >
              Bold
            </button>
            <button
              type="button"
              className={editor.isActive("italic") ? "active" : ""}
              onClick={() => editor.chain().focus().toggleItalic().run()}
            >
              Italic
            </button>
            <button
              type="button"
              className={editor.isActive("heading", { level: 1 }) ? "active" : ""}
              onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
            >
              H1
            </button>
            <button
              type="button"
              className={editor.isActive("heading", { level: 2 }) ? "active" : ""}
              onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
            >
              H2
            </button>
            <button
              type="button"
              className={editor.isActive("bulletList") ? "active" : ""}
              onClick={() => editor.chain().focus().toggleBulletList().run()}
            >
              List
            </button>
            <button
              type="button"
              className={editor.isActive("orderedList") ? "active" : ""}
              onClick={() => editor.chain().focus().toggleOrderedList().run()}
            >
              Numbered
            </button>
          </div>
        )}
        <EditorContent editor={editor} className="editor-content" />
      </section>
    );
  },
);

type TextDoc = {
  descendants: (
    f: (node: { isText?: boolean; text?: string }, pos: number) => boolean | void,
  ) => void;
};

function findTextRange(
  doc: TextDoc,
  text: string,
): { from: number; to: number } | null {
  const raw = text.trim();
  if (!raw) return null;

  const candidates = [raw];
  if (raw.length > 160) candidates.push(raw.slice(0, 160));
  if (raw.length > 80) candidates.push(raw.slice(0, 80));
  if (raw.length > 40) candidates.push(raw.slice(0, 40));

  // Join text nodes so matches work across bold/italic runs in the same clause.
  const chars: number[] = [];
  let plain = "";
  doc.descendants((node, pos) => {
    if (!node.isText || !node.text) return;
    for (let i = 0; i < node.text.length; i += 1) {
      chars.push(pos + i);
      plain += node.text[i];
    }
  });

  for (const candidate of candidates) {
    const hit = plain.indexOf(candidate);
    if (hit === -1) continue;
    const end = hit + candidate.length - 1;
    if (end >= chars.length) continue;
    return { from: chars[hit], to: chars[end] + 1 };
  }
  return null;
}
