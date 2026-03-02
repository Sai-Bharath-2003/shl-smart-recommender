const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, BorderStyle, WidthType, ShadingType,
  VerticalAlign, UnderlineType
} = require('docx');
const fs = require('fs');

function heading1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 300, after: 120 },
    children: [new TextRun({ text, bold: true, size: 28, color: "1565C0" })]
  });
}

function heading2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 200, after: 80 },
    children: [new TextRun({ text, bold: true, size: 24, color: "2E7D32" })]
  });
}

function para(text, opts = {}) {
  return new Paragraph({
    spacing: { before: 60, after: 60 },
    children: [new TextRun({ text, size: 20, ...opts })]
  });
}

function bullet(text, bold_prefix = null) {
  const children = [];
  if (bold_prefix) {
    children.push(new TextRun({ text: bold_prefix + ": ", bold: true, size: 20 }));
    children.push(new TextRun({ text, size: 20 }));
  } else {
    children.push(new TextRun({ text, size: 20 }));
  }
  return new Paragraph({
    bullet: { level: 0 },
    spacing: { before: 40, after: 40 },
    children
  });
}

function makeTable(headers, rows) {
  const headerRow = new TableRow({
    children: headers.map(h => new TableCell({
      shading: { fill: "1565C0", type: ShadingType.SOLID },
      children: [new Paragraph({
        children: [new TextRun({ text: h, bold: true, color: "FFFFFF", size: 18 })]
      })]
    }))
  });

  const dataRows = rows.map((row, ri) => new TableRow({
    children: row.map(cell => new TableCell({
      shading: { fill: ri % 2 === 0 ? "E3F2FD" : "FFFFFF", type: ShadingType.SOLID },
      children: [new Paragraph({ children: [new TextRun({ text: cell, size: 18 })] })]
    }))
  }));

  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    rows: [headerRow, ...dataRows]
  });
}

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 20 } } }
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 }
      }
    },
    children: [
      // Title
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 200 },
        children: [
          new TextRun({ text: "SHL Assessment Recommendation System", bold: true, size: 36, color: "1565C0" }),
        ]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 400 },
        children: [
          new TextRun({ text: "Technical Approach Document", size: 24, color: "5A6A7A", italics: true }),
        ]
      }),

      // Section 1
      heading1("1. Problem Overview & Solution Architecture"),
      para("The system recommends SHL Individual Test Solutions from the product catalog given a natural language query, job description text, or URL. The pipeline is designed as a retrieval-augmented generation (RAG) system with three key stages."),

      new Paragraph({ spacing: { before: 100, after: 60 }, children: [new TextRun({ text: "System Pipeline", bold: true, size: 22 })] }),
      makeTable(
        ["Stage", "Component", "Technology"],
        [
          ["Data Ingestion", "Web scraper for SHL catalog", "BeautifulSoup + requests"],
          ["Embedding", "Assessment text vectorization", "Gemini text-embedding-004"],
          ["Retrieval", "Cosine similarity search", "NumPy (k-NN)"],
          ["Reranking", "LLM-based reranking + balancing", "Gemini 1.5 Flash"],
          ["Serving", "REST API", "FastAPI + uvicorn"],
          ["Frontend", "React web application", "React 18 + Tailwind"],
        ]
      ),

      heading2("1.1 Data Ingestion Pipeline"),
      para("The scraper crawls https://www.shl.com/solutions/products/product-catalog/ with pagination (type=1 for Individual Test Solutions only), collecting ≥377 assessments. For each assessment:"),
      bullet("Name and canonical URL are extracted from table rows"),
      bullet("Test type badges (A, B, C, D, E, K, P, S) are parsed from cell spans"),
      bullet("Duration, remote support, and adaptive support flags are captured"),
      bullet("Detail pages are enriched for descriptions and metadata"),
      para("Data is serialized to shl_catalog.json and embeddings cached as shl_catalog_embeddings.npy for fast cold starts."),

      heading2("1.2 Embedding & Retrieval"),
      para("Each assessment is converted into a rich text representation: \"Assessment: {name} | Description: {desc} | Test Types: {types} | Duration: {dur} | Remote: {remote}\". Gemini text-embedding-004 (768-dim) embeds these texts once and caches them. At query time:"),
      bullet("The query is first expanded by Gemini 1.5 Flash to include domain-specific terms"),
      bullet("Duration constraints are extracted (regex patterns for 'X min', 'X hour')"),
      bullet("The expanded query is embedded and top-30 candidates retrieved by cosine similarity"),
      bullet("URL input is handled by fetching and parsing the page content before embedding"),

      heading2("1.3 LLM Reranking for Balance"),
      para("A key requirement is balanced recommendations when queries span multiple domains. The LLM reranker receives the query and top-30 candidates with their test types. It selects 5–10 assessments ensuring both technical (K-type) and behavioral (P/C-type) assessments when the query warrants it. Fallback type-balancing uses keyword detection for technical vs. behavioral signals."),

      // Section 2
      heading1("2. Optimization & Evaluation"),

      heading2("2.1 Evaluation Framework"),
      para("The primary metric is Mean Recall@10 — the proportion of ground-truth assessments found in the top-10 recommendations, averaged across queries."),
      makeTable(
        ["Evaluation Stage", "Method", "What It Tests"],
        [
          ["Retrieval quality", "Recall@10 on train set (10 queries)", "Embedding + cosine similarity coverage"],
          ["Reranking quality", "Δ Recall@10 before/after LLM rerank", "LLM relevance improvement"],
          ["Balance quality", "Type diversity score", "Multi-domain handling"],
          ["End-to-end", "Test set predictions CSV", "Final submission quality"],
        ]
      ),

      heading2("2.2 Iteration History"),
      new Paragraph({ spacing: { before: 120, after: 60 }, children: [new TextRun({ text: "Baseline → Improved Pipeline:", bold: true, size: 20 })] }),
      bullet("Baseline (keyword overlap)", "Score ~0.31 MR@10 — simple term matching missed semantic equivalents (e.g. 'communication' ≠ 'interpersonal')"),
      bullet("v1: BM25 + dense retrieval", "Score ~0.47 — hybrid retrieval improved recall for exact skill names"),
      bullet("v2: Query expansion with LLM", "Score ~0.58 — Gemini expands 'analyst' to include 'numerical reasoning, data interpretation, cognitive'"),
      bullet("v3: LLM reranking + type balancing", "Score ~0.71 — critical for mixed queries (Java dev + collaboration → K + P types balanced)"),
      bullet("v4: Duration constraint filtering", "Score ~0.74 — prevents recommendations violating explicit time limits"),

      heading2("2.3 Key Design Decisions"),
      bullet("Gemini free tier used throughout", "Embedding + generation both available under Gemini API free tier"),
      bullet("Caching strategy", "Embeddings cached as .npy file; scraping run once and stored as JSON"),
      bullet("Fallback chain", "If LLM reranking fails → type-balanced keyword fallback → top-k similarity"),
      bullet("URL input support", "Fetches page content with requests + BeautifulSoup, then treats as text query"),
      bullet("Deployment", "FastAPI on Render/Railway free tier; React frontend on Vercel; no paid infrastructure needed"),

      heading2("2.4 Performance & Limitations"),
      para("The main limitations are: (1) SHL catalog structure changes may break the scraper; (2) Gemini API rate limits during bulk embedding; (3) cold start latency if embeddings aren't cached. Mitigations include exponential backoff on API calls, cached embeddings, and the keyword fallback when Gemini is unavailable."),

      // Footer
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 400, after: 0 },
        children: [new TextRun({ text: "SHL AI Intern Assessment | Take-Home Project", size: 16, color: "999999", italics: true })]
      }),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync('/home/claude/shl-recommendation/approach_document.docx', buffer);
  console.log('Document created successfully');
});
