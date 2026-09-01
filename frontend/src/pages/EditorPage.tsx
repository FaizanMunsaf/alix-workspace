import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";

function EditorPage() {
  const editor = useEditor({
    extensions: [StarterKit],
    content: "<p>Start editing your document here...</p>",
  });

  if (!editor) {
    return null;
  }

  return (
    <section className="editor-page">
      <h2>Document Editor</h2>

      <div className="editor-toolbar">
        <button
          type="button"
          onClick={() => editor.chain().focus().toggleBold().run()}
          className={editor.isActive("bold") ? "active" : ""}
        >
          Bold
        </button>
        <button
          type="button"
          onClick={() => editor.chain().focus().toggleItalic().run()}
          className={editor.isActive("italic") ? "active" : ""}
        >
          Italic
        </button>
        <button
          type="button"
          onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
          className={editor.isActive("heading", { level: 2 }) ? "active" : ""}
        >
          Heading
        </button>
        <button
          type="button"
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          className={editor.isActive("bulletList") ? "active" : ""}
        >
          Bullet List
        </button>
      </div>

      <EditorContent editor={editor} className="editor-content" />
    </section>
  );
}

export default EditorPage;
