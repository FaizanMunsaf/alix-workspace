import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from "react";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Image from "@tiptap/extension-image";
import Table from "@tiptap/extension-table";
import TableRow from "@tiptap/extension-table-row";
import TableCell from "@tiptap/extension-table-cell";
import TableHeader from "@tiptap/extension-table-header";

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

type Props = {
  documentId: string | null;
  html: string;
  processingStatus: string | null;
  contentNonce: number;
  editable: boolean;
  onDirty: () => void;
  onSelectionChange: (selection: EditorSelection | null) => void;
};

export const ContractEditor = forwardRef<ContractEditorHandle, Props>(
  function ContractEditor(
    {
      documentId,
      html,
      processingStatus,
      contentNonce,
      editable,
      onDirty,
      onSelectionChange,
    },
    ref,
  ) {
    const appliedKey = useRef("");
    const [, setToolbarTick] = useState(0);
    const editor = useEditor({
      extensions: [
        StarterKit,
        Image.configure({
          inline: false,
          allowBase64: true,
        }),
        Table.configure({ resizable: false }),
        TableRow,
        TableHeader,
        TableCell,
      ],
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

    return (
      <section className="editor-page">
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

function findTextRange(
  doc: {
    descendants: (
      f: (node: { isText?: boolean; text?: string }, pos: number) => boolean | void,
    ) => void;
  },
  text: string,
): { from: number; to: number } | null {
  const raw = text.trim();
  if (!raw) return null;

  const candidates = [raw];
  if (raw.length > 120) candidates.push(raw.slice(0, 120));
  if (raw.length > 60) candidates.push(raw.slice(0, 60));

  for (const candidate of candidates) {
    let found: { from: number; to: number } | null = null;
    doc.descendants((node, pos) => {
      if (found || !node.isText || !node.text) return;
      const hit = node.text.indexOf(candidate);
      if (hit === -1) return;
      found = { from: pos + hit, to: pos + hit + candidate.length };
      return false;
    });
    if (found) return found;
  }
  return null;
}
