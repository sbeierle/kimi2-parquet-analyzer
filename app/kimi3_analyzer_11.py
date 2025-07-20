import gradio as gr
import pandas as pd
import pyarrow.parquet as pq
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud

# --- Laden der Parquet-Datei ---
def load_parquet(file_path):
    try:
        df = pq.read_table(file_path).to_pandas()
        return (
            f"<span style='color:green;'>✅ {Path(file_path).name} geladen mit {len(df)} Zeilen</span>",
            df.head(15),
            df,
            gr.update(choices=list(df.columns)),
            gr.update(choices=list(df.columns)),
            gr.update(choices=list(df.columns))
        )
    except Exception as e:
        return (
            f"<span style='color:red;'>❌ Fehler beim Laden: {str(e)}</span>",
            pd.DataFrame(),
            pd.DataFrame(),
            gr.update(choices=[]),
            gr.update(choices=[]),
            gr.update(choices=[])
        )

# --- Filtern des DataFrames ---
def filter_df(df, column, value):
    if df is None or column is None or value.strip() == "":
        return df.head(15)
    try:
        return df[df[column].astype(str).str.contains(value, case=False, na=False)].head(15)
    except Exception:
        return df.head(15)

# --- Sortieren des DataFrames ---
def sort_df(df, column, ascending):
    if df is None or column is None:
        return df.head(15)
    try:
        return df.sort_values(by=column, ascending=ascending).head(15)
    except Exception:
        return df.head(15)

# --- Zellklick: Inhalt anzeigen ---
def show_cell_content(evt: gr.SelectData, df):
    try:
        row, col = evt.index
        value = str(df.iloc[row, col])
        return f"""
        <div style=\"max-height: 400px; overflow-y: auto; padding: 10px; background: #f9f9f9; border: 1px solid #ccc; white-space: pre-wrap; font-size: 14px;\">
        <strong>Zellinhalt:</strong><br>{value}
        </div>
        """
    except:
        return ""

# --- Histogramm erstellen ---
def plot_histogram(df, column):
    if df is None or column is None:
        return None
    fig, ax = plt.subplots(figsize=(8, 4))
    value_counts = df[column].astype(str).value_counts()
    sns.barplot(x=value_counts.index, y=value_counts.values, ax=ax, palette="pastel")
    ax.set_title(f"Häufigste Werte in '{column}'")
    ax.set_xlabel("Wert")
    ax.set_ylabel("Anzahl")
    ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    return fig

# --- Wordcloud erstellen ---
def plot_wordcloud(df, column):
    if df is None or column is None:
        return None
    text = " ".join(df[column].dropna().astype(str).tolist())
    wordcloud = WordCloud(width=800, height=400, background_color="white").generate(text)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis("off")
    ax.set_title(f"Wordcloud aus '{column}'")
    return fig

# --- Parquet-Dateien laden ---
parquet_files = sorted([str(p) for p in Path("results/screenshots").glob("*.parquet")])

# --- Gradio App ---
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("## 🧠 Kimi3 Parquet Prompt Analyzer v10")
    gr.Markdown("Analysiere `.parquet`-Dateien mit Filter, Sortierung, Visualisierungen und Zell-Popup.")

    with gr.Row():
        parquet_dropdown = gr.Dropdown(choices=parquet_files, label="📁 Wähle eine Parquet-Datei", scale=3)
        load_button = gr.Button("📄 Laden", variant="primary", scale=1)

    status = gr.HTML(label="🧠 Status")

    with gr.Group():
        gr.Markdown("### 🔎 Vorschau (max. 15 Zeilen)")
        preview_table = gr.Dataframe(wrap=True)

        hidden_df = gr.State()

        with gr.Row():
            filter_column = gr.Dropdown(label="🔍 Spalte filtern", scale=2)
            filter_value = gr.Textbox(label="🎯 Filterwert", scale=2)
            apply_filter = gr.Button("📌 Filter anwenden", scale=1)

        with gr.Row():
            sort_column = gr.Dropdown(label="📊 Spalte sortieren", scale=2)
            sort_ascending = gr.Checkbox(label="⬆️ Aufsteigend", value=True, scale=1)
            apply_sort = gr.Button("📁 Sortieren", scale=1)

    with gr.Accordion("📋 Zellinhalt anzeigen", open=False):
        cell_popup = gr.HTML(label="📌 Inhalt der ausgewählten Zelle")

    with gr.Tab("📈 Visualisierung"):
        gr.Markdown("### Histogramm & Wordcloud für ausgewählte Spalten")

        with gr.Row():
            visualize_column = gr.Dropdown(label="📊 Spalte für Visualisierung", scale=2)
            generate_histogram = gr.Button("📊 Histogramm erstellen", scale=1)
            generate_wordcloud = gr.Button("🎈 Wordcloud erstellen", scale=1)

        with gr.Row():
            histogram_plot = gr.Plot(label="📊 Histogramm")
            wordcloud_plot = gr.Plot(label="🎈 Wordcloud")

    def load_and_prepare(path):
        status, df, full_df, cols1, cols2, cols3 = load_parquet(path)
        return status, df, full_df, cols1, cols2, cols3

    load_button.click(
        fn=load_and_prepare,
        inputs=[parquet_dropdown],
        outputs=[status, preview_table, hidden_df, filter_column, sort_column, visualize_column]
    )

    apply_filter.click(
        fn=filter_df,
        inputs=[hidden_df, filter_column, filter_value],
        outputs=[preview_table]
    )

    apply_sort.click(
        fn=sort_df,
        inputs=[hidden_df, sort_column, sort_ascending],
        outputs=[preview_table]
    )

    preview_table.select(fn=show_cell_content, inputs=[hidden_df], outputs=[cell_popup])

    generate_histogram.click(
        fn=plot_histogram,
        inputs=[hidden_df, visualize_column],
        outputs=[histogram_plot]
    )

    generate_wordcloud.click(
        fn=plot_wordcloud,
        inputs=[hidden_df, visualize_column],
        outputs=[wordcloud_plot]
    )

if __name__ == "__main__":
    demo.launch()
