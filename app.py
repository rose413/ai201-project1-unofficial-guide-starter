"""
app.py

Milestone 5 — Gradio user interface for the SCU Off-Campus Housing RAG system.

This file is intentionally thin: it owns only the UI layout and wires user
events to rag_pipeline() from generator.py.  All retrieval, generation, and
source-formatting logic lives in generator.py.

Usage:
    python app.py
    # Then open http://127.0.0.1:7860 in your browser
"""

import gradio as gr

from generator import rag_pipeline

# ── Gradio UI ─────────────────────────────────────────────────────────────────

with gr.Blocks(title="SCU Off-Campus Housing Assistant") as demo:

    gr.Markdown(
        """
        # SCU Off-Campus Housing Assistant
        Ask questions about off-campus housing near **Santa Clara University**.
        Answers are grounded strictly in the ingested documents — no outside knowledge.
        """
    )

    with gr.Row():
        query_box = gr.Textbox(
            label="Your Question",
            placeholder='e.g. "What apartments are closest to SCU?" or "Are there any summer subleases available?"',
            lines=3,
        )

    submit_btn = gr.Button("Submit", variant="primary")

    answer_box = gr.Textbox(
        label="Answer",
        lines=8,
        interactive=False,
    )

    sources_md = gr.Markdown()

    # ── Event wiring ──────────────────────────────────────────────────────────
    #
    # Both the Submit button click and pressing Enter in the text box trigger
    # the same pipeline so the interface feels natural to use.
    #
    # rag_pipeline() returns (answer: str, sources_markdown: str).
    # Gradio maps the tuple positionally to [answer_box, sources_md].

    submit_btn.click(
        fn=rag_pipeline,
        inputs=[query_box],
        outputs=[answer_box, sources_md],
    )

    query_box.submit(
        fn=rag_pipeline,
        inputs=[query_box],
        outputs=[answer_box, sources_md],
    )

# ── Launch ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    demo.launch()
