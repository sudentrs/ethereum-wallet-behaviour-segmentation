from __future__ import annotations

import shutil
import zipfile
from html import escape
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
from PIL import Image


ROOT = Path(".")
OUT = ROOT / "results" / "final_academic_pack"
FIG = OUT / "figures"
REPORTS = ROOT / "reports"
PRESENTATIONS = ROOT / "presentations"


def read_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(ROOT / path)


def ensure_dirs() -> None:
    for path in [OUT, FIG, REPORTS, PRESENTATIONS]:
        path.mkdir(parents=True, exist_ok=True)


def save_bar_network_null(network: pd.DataFrame) -> Path:
    path = FIG / "network_null_comparison.png"
    x = np.arange(len(network))
    width = 0.36
    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.bar(x - width / 2, network["observed_same_cluster_ratio"], width, label="Observed")
    ax.bar(x + width / 2, network["null_mean"], width, label="Shuffled-label null mean")
    ax.set_xticks(x)
    ax.set_xticklabels(network["label_type"], rotation=25, ha="right")
    ax.set_ylabel("Same-label transaction ratio")
    ax.set_title("Network alignment: observed same-label edges vs shuffled-label null")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)
    return path


def save_correspondence_plot(correspondence: pd.DataFrame) -> Path:
    path = FIG / "k_taxonomy_signal_correspondence.png"
    pivot_ari = correspondence.pivot(index="taxonomy", columns="signal_cluster_type", values="ari")
    pivot_nmi = correspondence.pivot(index="taxonomy", columns="signal_cluster_type", values="nmi")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
    for ax, data, title in [(axes[0], pivot_ari, "ARI"), (axes[1], pivot_nmi, "NMI")]:
        im = ax.imshow(data.values, cmap="YlGnBu", vmin=0, vmax=max(0.35, float(data.values.max())))
        ax.set_xticks(np.arange(len(data.columns)))
        ax.set_xticklabels([c.replace("_cluster", "").replace("_", " ") for c in data.columns], rotation=20, ha="right")
        ax.set_yticks(np.arange(len(data.index)))
        ax.set_yticklabels(data.index)
        ax.set_title(title)
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                ax.text(j, i, f"{data.values[i, j]:.3f}", ha="center", va="center", fontsize=9)
    fig.colorbar(im, ax=axes.ravel().tolist(), fraction=0.025, pad=0.04)
    fig.suptitle("Temporal signal clusters only partly reproduce static K taxonomies", y=1.02)
    fig.tight_layout()
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return path


def save_signal_validation_plot(validation: pd.DataFrame) -> Path:
    path = FIG / "signal_cluster_validation.png"
    labels = validation["label_type"].str.replace("_cluster", "").str.replace("_", " ")
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    ax.bar(x - 0.2, validation["observed_silhouette"], 0.4, label="Observed silhouette")
    ax.bar(x + 0.2, validation["null_mean_silhouette"], 0.4, label="Null mean silhouette")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Silhouette score")
    ax.set_title("Signal clusters have stronger separation than shuffled labels")
    ax.axhline(0, color="#555555", linewidth=0.8)
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)
    return path


def save_two_step_plot(two_step: pd.DataFrame) -> Path:
    path = FIG / "two_step_return_rates.png"
    labels = two_step["month_t"].astype(str).str[-2:] + "-" + two_step["month_t2"].astype(str).str[-2:]
    fig, ax = plt.subplots(figsize=(10, 4.8))
    x = np.arange(len(two_step))
    ax.plot(x, two_step["observed_two_step_return_rate"], marker="o", label="Observed return rate")
    ax.plot(x, two_step["null_mean"], marker="s", label="Null mean")
    ax.fill_between(
        x,
        two_step["null_mean"] - 2 * two_step["null_std"],
        two_step["null_mean"] + 2 * two_step["null_std"],
        alpha=0.18,
        label="Null +/- 2 std",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_ylabel("Two-step return rate")
    ax.set_title("Wallets often return to their prior K5 state after temporary movement")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)
    return path


def save_event_context_plot(event_tests: pd.DataFrame) -> Path:
    path = FIG / "event_adjacent_context.png"
    comp = event_tests[event_tests["metric"] == "composition_l1_change"].copy()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(comp["event_month"].astype(str), comp["observed"], label="Observed event-adjacent change")
    ax.axhline(comp["non_event_mean"].iloc[0], color="#444444", linestyle="--", label="Non-event mean")
    ax.set_ylabel("Composition L1 change")
    ax.set_title("Event-adjacent months are context checks, not causal proof")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)
    return path


def copy_existing_figures() -> dict[str, Path]:
    copied = {}
    sources = {
        "frequency_power_by_wavelength_cluster": ROOT / "results" / "temporal_signal_analysis_edge_sample_10k" / "figures" / "frequency_power_by_wavelength_cluster.png",
        "flow_frequency_power_by_wavelength_cluster": ROOT / "results" / "temporal_signal_analysis_edge_sample_10k" / "figures" / "flow_frequency_power_by_wavelength_cluster.png",
        "trajectory_type_shares": ROOT / "results" / "k5_academic_strengthening" / "trajectory_type_shares.png",
        "monthly_centroid_drift": ROOT / "results" / "k5_academic_strengthening" / "monthly_centroid_drift.png",
    }
    for name, src in sources.items():
        if src.exists():
            dst = FIG / f"{name}.png"
            shutil.copyfile(src, dst)
            copied[name] = dst
    return copied


def build_robustness_summary(
    correspondence: pd.DataFrame,
    signal_validation: pd.DataFrame,
    signal_network: pd.DataFrame,
    k_network: pd.DataFrame,
    two_step: pd.DataFrame,
) -> Path:
    path = OUT / "robustness_summary.md"
    best_time = correspondence[correspondence["signal_cluster_type"] == "time_domain_cluster"].sort_values("ari", ascending=False).iloc[0]
    best_wave = correspondence[correspondence["signal_cluster_type"] == "wavelength_cluster"].sort_values("ari", ascending=False).iloc[0]
    lines = [
        "# Robustness And Claim Calibration Summary",
        "",
        "## What is robust enough to claim",
        "",
        "- K5 remains a defensible main taxonomy because it balances interpretability, static feature separation, temporal validation, and downstream comparison results.",
        f"- K5 has the strongest signal correspondence among K4/K5/K6 for wavelength clusters (ARI {best_wave['ari']:.3f}) and time-domain clusters (ARI {best_time['ari']:.3f}), but the values are not high enough to say the signal clusters reproduce K5.",
        f"- Wavelength clusters show feature-space structure (silhouette {signal_validation.loc[signal_validation['label_type'] == 'wavelength_cluster', 'observed_silhouette'].iloc[0]:.3f}) and network alignment above the shuffled-label null.",
        f"- Two-step return behaviour is consistently above the null model across monthly triples, with observed-minus-null ranging from {two_step['observed_minus_null'].min():.3f} to {two_step['observed_minus_null'].max():.3f}.",
        "",
        "## What must be worded carefully",
        "",
        "- Time-domain clusters are useful as burst/gap/persistence states, but in the 10k edge-aware network test they do not have stronger same-cluster edge concentration than the shuffled-label null.",
        "- Event-adjacent results are contextual checks, not causal event studies.",
        "- Cluster labels describe behavioural states from transaction data, not verified real-world identities.",
        "",
        "## Key tables",
        "",
        "K-taxonomy vs signal-cluster correspondence:",
        "",
        correspondence.to_markdown(index=False),
        "",
        "Signal cluster validation:",
        "",
        signal_validation.to_markdown(index=False),
        "",
        "Network null tests:",
        "",
        k_network.to_markdown(index=False),
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def build_contribution_note() -> Path:
    path = OUT / "paper_contribution_note.md"
    lines = [
        "# Paper Contribution Note",
        "",
        "## Core research question",
        "",
        "Can Ethereum externally owned account wallet behaviour be represented as a layered structure combining aggregate roles, temporal activity rhythms, activity-state dynamics, and transaction-network position?",
        "",
        "## Gap addressed",
        "",
        "Many wallet-clustering workflows stop after static feature clustering or graph description. Our project adds a validation-oriented bridge between static behavioural taxonomies, temporal signal analysis, and network null testing.",
        "",
        "## Main contribution",
        "",
        "We propose a layered empirical framework for Ethereum wallet behaviour segmentation:",
        "",
        "1. Remove contract addresses to focus on EOAs.",
        "2. Build static aggregate wallet roles using K4/K5/K6 comparisons.",
        "3. Select K5 as the main interpretable taxonomy.",
        "4. Represent sampled wallets as daily time signals.",
        "5. Extract frequency-domain and time-domain features.",
        "6. Compare signal clusters with K4/K5/K6.",
        "7. Validate labels using transaction-network shuffled-label null tests.",
        "8. Use temporal transitions and two-step return tests to study state persistence.",
        "",
        "## Strongest conclusion",
        "",
        "Wallet behaviour is not one-dimensional. Static aggregate roles, temporal rhythms, burst/gap states, and network structure overlap but do not collapse into the same taxonomy.",
        "",
        "## Careful claim boundary",
        "",
        "The work identifies behavioural roles and states from public transaction data. It does not identify real users, prove intent, or establish causal links to market events.",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def png_size_px(path: Path) -> tuple[int, int]:
    with Image.open(path) as im:
        return im.size


def docx_paragraph(text: str, style: str = "Body") -> str:
    style_xml = {
        "Title": '<w:pStyle w:val="Title"/>',
        "Subtitle": '<w:pStyle w:val="Subtitle"/>',
        "Heading1": '<w:pStyle w:val="Heading1"/>',
        "Heading2": '<w:pStyle w:val="Heading2"/>',
        "Bullet": '<w:pStyle w:val="ListBullet"/>',
        "Body": "",
    }[style]
    bullet = '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>' if style == "Bullet" else ""
    return f"<w:p><w:pPr>{style_xml}{bullet}</w:pPr><w:r><w:t xml:space=\"preserve\">{escape(text)}</w:t></w:r></w:p>"


def docx_table(df: pd.DataFrame, columns: list[str], max_rows: int | None = None) -> str:
    shown = df[columns].head(max_rows) if max_rows else df[columns]
    rows = []
    header = "".join(f"<w:tc><w:p><w:r><w:rPr><w:b/></w:rPr><w:t>{escape(col)}</w:t></w:r></w:p></w:tc>" for col in columns)
    rows.append(f"<w:tr>{header}</w:tr>")
    for _, row in shown.iterrows():
        cells = []
        for col in columns:
            val = row[col]
            text = f"{val:.4f}" if isinstance(val, float) else str(val)
            cells.append(f"<w:tc><w:p><w:r><w:t>{escape(text)}</w:t></w:r></w:p></w:tc>")
        rows.append(f"<w:tr>{''.join(cells)}</w:tr>")
    return (
        '<w:tbl><w:tblPr><w:tblW w:w="9360" w:type="dxa"/>'
        '<w:tblBorders><w:top w:val="single" w:sz="4" w:color="CCCCCC"/>'
        '<w:left w:val="single" w:sz="4" w:color="CCCCCC"/>'
        '<w:bottom w:val="single" w:sz="4" w:color="CCCCCC"/>'
        '<w:right w:val="single" w:sz="4" w:color="CCCCCC"/>'
        '<w:insideH w:val="single" w:sz="4" w:color="CCCCCC"/>'
        '<w:insideV w:val="single" w:sz="4" w:color="CCCCCC"/></w:tblBorders></w:tblPr>'
        + "".join(rows)
        + "</w:tbl>"
    )


def docx_image(rel_id: str, path: Path, width_in: float = 6.2) -> str:
    px_w, px_h = png_size_px(path)
    height_in = width_in * px_h / px_w
    cx = int(width_in * 914400)
    cy = int(height_in * 914400)
    return f"""
    <w:p><w:r><w:drawing><wp:inline xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" distT="0" distB="0" distL="0" distR="0">
      <wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="1" name="{escape(path.name)}"/>
      <a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
      <pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="0" name="{escape(path.name)}"/><pic:cNvPicPr/></pic:nvPicPr>
      <pic:blipFill><a:blip r:embed="{rel_id}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>
      <pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>
      </a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>
    """


def build_docx_report(
    figures: dict[str, Path],
    correspondence: pd.DataFrame,
    signal_validation: pd.DataFrame,
    k_network: pd.DataFrame,
    two_step: pd.DataFrame,
) -> Path:
    path = REPORTS / "Final_Academic_Project_Report_Ethereum_Wallet_Behaviour.docx"
    image_items = [
        ("rIdImage1", figures["correspondence"]),
        ("rIdImage2", figures["signal_validation"]),
        ("rIdImage3", figures["network_null"]),
        ("rIdImage4", figures["two_step"]),
    ]
    body = [
        docx_paragraph("Ethereum Wallet Behaviour Segmentation", "Title"),
        docx_paragraph("Final academic synthesis report", "Subtitle"),
        docx_paragraph("Executive Summary", "Heading1"),
        docx_paragraph("This project studies Ethereum externally owned account behaviour as a layered structure. After removing contract addresses, we compare static K4/K5/K6 behavioural taxonomies, select K5 as the main interpretable role layer, and extend the analysis with temporal signal features and transaction-network validation."),
        docx_paragraph("The strongest result is not that one clustering method explains everything. Static aggregate roles, wavelength-style temporal rhythms, time-domain activity states, and network position provide related but distinct views of wallet behaviour."),
        docx_paragraph("Research Question", "Heading1"),
        docx_paragraph("Can Ethereum EOA wallet behaviour be represented as a layered structure combining aggregate roles, temporal activity rhythms, activity-state dynamics, and transaction-network position?"),
        docx_paragraph("Method Overview", "Heading1"),
    ]
    for item in [
        "Removed contract addresses and focused on externally owned accounts.",
        "Compared K4, K5, and K6 static wallet taxonomies.",
        "Used K5 as the main interpretable behavioural role layer.",
        "Built daily 2022 wallet signals for an edge-aware sample of 10,000 wallets.",
        "Extracted frequency-domain and time-domain features.",
        "Validated labels with shuffled-label transaction-network null tests and temporal transition tests.",
    ]:
        body.append(docx_paragraph(item, "Bullet"))
    body.extend(
        [
            docx_paragraph("Core Result: Temporal Signals Add A Separate Layer", "Heading1"),
            docx_paragraph("Temporal signal clusters only partly reproduce the static K4/K5/K6 roles. K5 has the strongest correspondence, but the agreement is still low to moderate."),
            docx_table(correspondence, ["taxonomy", "signal_cluster_type", "ari", "nmi"]),
            docx_image("rIdImage1", figures["correspondence"]),
            docx_paragraph("Signal Cluster Validation", "Heading1"),
            docx_paragraph("Both signal representations show positive silhouette scores and are stronger than shuffled-label null models. Their seed stability is moderate, so they should be presented as exploratory temporal states rather than fixed wallet identities."),
            docx_table(signal_validation, ["label_type", "observed_silhouette", "null_mean_silhouette", "p_value_upper", "seed_stability_mean_ari", "seed_stability_mean_nmi"]),
            docx_image("rIdImage2", figures["signal_validation"]),
            docx_paragraph("Network-Science Validation", "Heading1"),
            docx_paragraph("K4, K5, and K6 all show strong same-label transaction concentration relative to shuffled labels. Wavelength clusters also show network alignment. Time-domain clusters do not exceed the null model in the 10,000-wallet edge-aware test."),
            docx_table(k_network, ["label_type", "edge_count", "observed_same_cluster_ratio", "null_mean", "p_value_upper"]),
            docx_image("rIdImage3", figures["network_null"]),
            docx_paragraph("Temporal Stability And Two-Step Return", "Heading1"),
            docx_paragraph("Across monthly triples, wallets that left their original K5 state often returned two months later more frequently than expected under the null model."),
            docx_table(two_step, ["month_t", "month_t1", "month_t2", "observed_two_step_return_rate", "null_mean", "p_value_upper"], max_rows=10),
            docx_image("rIdImage4", figures["two_step"]),
            docx_paragraph("Academic Contribution", "Heading1"),
            docx_paragraph("The project contributes a reproducible validation framework for wallet behaviour segmentation. It connects static EOA wallet roles, temporal signal analysis, transaction-network null tests, and temporal stability checks into a single empirical workflow."),
            docx_paragraph("Limitations", "Heading1"),
        ]
    )
    for item in [
        "Labels describe behavioural states, not verified real-world identities.",
        "Event-adjacent checks are contextual and should not be framed as causal evidence.",
        "The edge-aware signal analysis is sample-based, not full-population signal assignment.",
        "Time-domain states are structured in feature space but not strongly network-assortative in the 10k test.",
    ]:
        body.append(docx_paragraph(item, "Bullet"))

    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Default Extension="png" ContentType="image/png"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""
    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
    doc_rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">']
    for i, (rid, img) in enumerate(image_items, start=1):
        doc_rels.append(f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image{i}.png"/>')
    doc_rels.append("</Relationships>")
    styles = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:style w:type="paragraph" w:styleId="Normal"><w:name w:val="Normal"/><w:rPr><w:rFonts w:ascii="Calibri"/><w:sz w:val="22"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:rPr><w:b/><w:sz w:val="40"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Subtitle"><w:name w:val="Subtitle"/><w:rPr><w:i/><w:sz w:val="24"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:rPr><w:b/><w:color w:val="1F4D78"/><w:sz w:val="32"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="ListBullet"><w:name w:val="List Bullet"/><w:rPr><w:sz w:val="22"/></w:rPr></w:style>
</w:styles>"""
    document = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<w:body>{''.join(body)}<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr></w:body></w:document>"""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", document)
        z.writestr("word/styles.xml", styles)
        z.writestr("word/_rels/document.xml.rels", "".join(doc_rels))
        for i, (_, img) in enumerate(image_items, start=1):
            z.write(img, f"word/media/image{i}.png")
    return path


def pptx_text_box(text: str, x: int, y: int, cx: int, cy: int, size: int = 1800, bold: bool = False) -> str:
    b = "<a:b/>" if bold else ""
    return f"""
    <p:sp><p:nvSpPr><p:cNvPr id="{x + y + cx + cy}" name="Text"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr><p:txBody><a:bodyPr wrap="square"/><a:lstStyle/><a:p><a:r><a:rPr lang="en-US" sz="{size}">{b}</a:rPr><a:t>{escape(text)}</a:t></a:r></a:p></p:txBody></p:sp>
    """


def pptx_image(rel_id: str, name: str, x: int, y: int, cx: int, cy: int) -> str:
    return f"""
    <p:pic><p:nvPicPr><p:cNvPr id="{x + y + cx + cy}" name="{escape(name)}"/><p:cNvPicPr/><p:nvPr/></p:nvPicPr>
    <p:blipFill><a:blip r:embed="{rel_id}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
    <p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>
    """


def slide_xml(title: str, bullets: list[str], image_rel: str | None = None, image_name: str = "") -> str:
    shapes = [pptx_text_box(title, 457200, 274320, 11277600, 685800, 2800, True)]
    bullet_text = "\n".join([f"- {b}" for b in bullets])
    shapes.append(pptx_text_box(bullet_text, 609600, 1219200, 5181600 if image_rel else 10972800, 4876800, 1650))
    if image_rel:
        shapes.append(pptx_image(image_rel, image_name, 6096000, 1219200, 6096000, 4572000))
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>{''.join(shapes)}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>"""


def build_advisor_deck(figures: dict[str, Path]) -> Path:
    path = PRESENTATIONS / "Final_Academic_Project_Advisor_Deck.pptx"
    slides = [
        ("Ethereum wallet behaviour is best treated as layered", ["Goal: segment Ethereum EOA wallets into defensible behavioural roles.", "Main result: static roles, temporal rhythms, activity states, and network position overlap but do not collapse into one taxonomy.", "Academic contribution: a validation workflow, not just a clustering output."], None),
        ("The project moved from application idea to empirical foundation", ["Initial idea: AI-governed crypto-bank simulator with agents and explainable decisions.", "Pivot: real Ethereum wallet behaviour needed to be understood before simulation assumptions could be trusted.", "Final direction: derive behavioural roles from data, then validate them with independent evidence."], None),
        ("Temporal signal analysis adds a second evidence layer", ["Built daily 2022 wallet signals for a 10,000-wallet edge-aware sample.", "Frequency-domain features capture rhythms in transaction and flow activity.", "Time-domain features capture active days, inactive gaps, bursts, streaks, and switching."], figures["frequency"]),
        ("Signal clusters are structured but do not simply reproduce K5", ["K5 has the highest correspondence with signal clusters among K4/K5/K6.", "The agreement remains low to moderate, so the signal layer is not a duplicate of static roles.", "This gives the paper a stronger layered-behaviour argument."], figures["correspondence"]),
        ("Network validation separates stronger and weaker claims", ["Static K taxonomies show strong same-label transaction concentration.", "Wavelength clusters also exceed the shuffled-label null.", "Time-domain clusters do not exceed the null in the 10k test, so that claim must be cautious."], figures["network_null"]),
        ("Temporal transitions show temporary movement and return", ["Monthly K5 transitions show moderate persistence rather than fixed identities.", "Two-step return rates are consistently above null expectations.", "Wallets may temporarily leave a state and later return, but we do not infer intent."], figures["two_step"]),
        ("The paper contribution is a validation framework", ["Layer 1: static aggregate roles from EOA wallet features.", "Layer 2: temporal rhythms from frequency-domain signals.", "Layer 3: burst/gap/persistence states from time-domain signals.", "Layer 4: transaction-network evidence through shuffled-label null tests.", "Layer 5: temporal stability through transition and two-step return tests."], None),
        ("Next work should strengthen claims, not multiply outputs", ["Finalize paper figures from the audited figure pack.", "Manually review role labels before writing final public descriptions.", "Use formal event-study methods if causal event language is desired.", "Scale temporal signal assignment beyond the sample if compute budget allows."], None),
    ]
    content_types = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/><Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>']
    rel_entries = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">']
    pres_slide_ids = []
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for idx, (_, _, img) in enumerate(slides, start=1):
            content_types.append(f'<Override PartName="/ppt/slides/slide{idx}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>')
            rel_entries.append(f'<Relationship Id="rId{idx}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{idx}.xml"/>')
            pres_slide_ids.append(f'<p:sldId id="{255 + idx}" r:id="rId{idx}"/>')
        content_types.append("</Types>")
        rel_entries.append("</Relationships>")
        z.writestr("[Content_Types].xml", "".join(content_types))
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/></Relationships>')
        z.writestr("ppt/_rels/presentation.xml.rels", "".join(rel_entries))
        z.writestr("ppt/presentation.xml", f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:sldSz cx="12192000" cy="6858000" type="wide"/><p:sldIdLst>{"".join(pres_slide_ids)}</p:sldIdLst></p:presentation>')
        media_idx = 1
        for idx, (title, bullets, img) in enumerate(slides, start=1):
            rel_id = None
            if img:
                rel_id = "rIdImg1"
                z.write(img, f"ppt/media/image{media_idx}.png")
                z.writestr(f"ppt/slides/_rels/slide{idx}.xml.rels", f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="{rel_id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/image{media_idx}.png"/></Relationships>')
                media_idx += 1
            else:
                z.writestr(f"ppt/slides/_rels/slide{idx}.xml.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>')
            z.writestr(f"ppt/slides/slide{idx}.xml", slide_xml(title, bullets, rel_id, img.name if img else ""))
    return path


def add_pdf_slide(pdf: PdfPages, title: str, bullets: list[str], image: Path | None = None) -> None:
    fig = plt.figure(figsize=(13.333, 7.5))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.text(0.055, 0.92, title, fontsize=24, fontweight="bold", va="top")
    bullet_x = 0.07
    bullet_top = 0.78
    line_gap = 0.095 if len(bullets) <= 4 else 0.075
    max_width = 75 if image else 115
    for i, bullet in enumerate(bullets):
        wrapped = []
        words = bullet.split()
        line = ""
        for word in words:
            if len(line) + len(word) + 1 > max_width:
                wrapped.append(line)
                line = word
            else:
                line = f"{line} {word}".strip()
        wrapped.append(line)
        ax.text(bullet_x, bullet_top - i * line_gap, "- " + ("\n  ".join(wrapped)), fontsize=15.5, va="top")
    if image:
        im = plt.imread(image)
        img_ax = fig.add_axes([0.52, 0.18, 0.42, 0.62])
        img_ax.imshow(im)
        img_ax.axis("off")
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def build_advisor_deck_pdf(figures: dict[str, Path]) -> Path:
    path = PRESENTATIONS / "Final_Academic_Project_Advisor_Deck.pdf"
    slides = [
        ("Ethereum wallet behaviour is best treated as layered", ["Goal: segment Ethereum EOA wallets into defensible behavioural roles.", "Main result: static roles, temporal rhythms, activity states, and network position overlap but do not collapse into one taxonomy.", "Academic contribution: a validation workflow, not just a clustering output."], None),
        ("The project moved from application idea to empirical foundation", ["Initial idea: AI-governed crypto-bank simulator with agents and explainable decisions.", "Pivot: real Ethereum wallet behaviour needed to be understood before simulation assumptions could be trusted.", "Final direction: derive behavioural roles from data, then validate them with independent evidence."], None),
        ("Temporal signal analysis adds a second evidence layer", ["Built daily 2022 wallet signals for a 10,000-wallet edge-aware sample.", "Frequency-domain features capture rhythms in transaction and flow activity.", "Time-domain features capture active days, inactive gaps, bursts, streaks, and switching."], figures["frequency"]),
        ("Signal clusters are structured but do not simply reproduce K5", ["K5 has the highest correspondence with signal clusters among K4/K5/K6.", "The agreement remains low to moderate, so the signal layer is not a duplicate of static roles.", "This gives the paper a stronger layered-behaviour argument."], figures["correspondence"]),
        ("Network validation separates stronger and weaker claims", ["Static K taxonomies show strong same-label transaction concentration.", "Wavelength clusters also exceed the shuffled-label null.", "Time-domain clusters do not exceed the null in the 10k test, so that claim must be cautious."], figures["network_null"]),
        ("Temporal transitions show temporary movement and return", ["Monthly K5 transitions show moderate persistence rather than fixed identities.", "Two-step return rates are consistently above null expectations.", "Wallets may temporarily leave a state and later return, but we do not infer intent."], figures["two_step"]),
        ("The paper contribution is a validation framework", ["Layer 1: static aggregate roles from EOA wallet features.", "Layer 2: temporal rhythms from frequency-domain signals.", "Layer 3: burst/gap/persistence states from time-domain signals.", "Layer 4: transaction-network evidence through shuffled-label null tests.", "Layer 5: temporal stability through transition and two-step return tests."], None),
        ("Next work should strengthen claims, not multiply outputs", ["Finalize paper figures from the audited figure pack.", "Manually review role labels before writing final public descriptions.", "Use formal event-study methods if causal event language is desired.", "Scale temporal signal assignment beyond the sample if compute budget allows."], None),
    ]
    with PdfPages(path) as pdf:
        for title, bullets, image in slides:
            add_pdf_slide(pdf, title, bullets, image)
    return path


def main() -> None:
    ensure_dirs()
    correspondence = read_csv("results/temporal_signal_k_taxonomy_comparison/k_taxonomy_signal_correspondence.csv")
    signal_validation = read_csv("results/temporal_signal_analysis_edge_sample_10k/signal_cluster_validation_summary.csv")
    signal_network = read_csv("results/temporal_signal_analysis_edge_sample_10k/network_signal_cluster_null_tests.csv")
    k_network = read_csv("results/temporal_signal_k_taxonomy_comparison/k_taxonomy_signal_network_null_tests.csv")
    two_step = read_csv("results/academic_paper_pack/k5/k5_two_step_return_null_tests.csv")
    event_tests = read_csv("results/academic_paper_pack/k5/k5_event_adjacent_rank_tests.csv")

    copied = copy_existing_figures()
    figures = {
        "network_null": save_bar_network_null(k_network),
        "correspondence": save_correspondence_plot(correspondence),
        "signal_validation": save_signal_validation_plot(signal_validation),
        "two_step": save_two_step_plot(two_step),
        "event_context": save_event_context_plot(event_tests),
        "frequency": copied["frequency_power_by_wavelength_cluster"],
    }
    figures.update(copied)

    robustness = build_robustness_summary(correspondence, signal_validation, signal_network, k_network, two_step)
    contribution = build_contribution_note()
    report = build_docx_report(figures, correspondence, signal_validation, k_network, two_step)
    deck = build_advisor_deck(figures)
    deck_pdf = build_advisor_deck_pdf(figures)

    manifest = OUT / "final_deliverable_manifest.md"
    manifest.write_text(
        "\n".join(
            [
                "# Final Academic Deliverable Pack",
                "",
                f"- Robustness summary: `{robustness}`",
                f"- Contribution note: `{contribution}`",
                f"- Academic report DOCX: `{report}`",
                f"- Advisor deck PPTX: `{deck}`",
                f"- Advisor deck PDF: `{deck_pdf}`",
                f"- Figure folder: `{FIG}`",
            ]
        ),
        encoding="utf-8",
    )
    print(f"Saved final academic deliverable pack to {OUT.resolve()}")
    print(f"Report: {report.resolve()}")
    print(f"Deck: {deck.resolve()}")
    print(f"Deck PDF: {deck_pdf.resolve()}")


if __name__ == "__main__":
    main()
