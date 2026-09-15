import { forwardRef, useEffect, useImperativeHandle, useRef } from "react";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
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
    const editor = useEditor({
      extensions: [
        StarterKit,
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
