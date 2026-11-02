# Publishing workflow / Flujo de publicación

The diagrams show the standard Code Mode publication path. The agent prepares a dated queue video,
composes authorized operations in restricted Deno, and persists a proposal. The owner approves the exact
proposal through the CLI before the trusted host can activate it in the existing queue. The scheduled
runner revalidates that approval, records each provider outcome, and stops uncertain attempts for reconciliation.
Direct MCP tools retain their own workflows, including Postiz, browser and handoff; this diagram's publication
path uses official adapters only. See [Code Mode](../CODE_MODE.md) for the complete contract and limitations.

Los diagramas muestran la ruta de publicación de Code Mode, que está integrada por defecto. El agente prepara
un video en la cola fechada, combina operaciones autorizadas en Deno restringido y guarda una propuesta.
El dueño aprueba la propuesta exacta desde la CLI antes de que el servidor pueda activar la cola. El proceso
programado revalida la aprobación, conserva el resultado de cada red y detiene los intentos inciertos para
conciliarlos. Las herramientas directas mantienen sus flujos, incluidos Postiz, navegador y handoff; la ruta
dibujada usa únicamente adaptadores oficiales.

| Language / Idioma | Standalone interactive HTML | Source / Fuente | README images |
|---|---|---|---|
| Español | [Publicación autorizada](publishing-es.html) | [Archify JSON](../../assets/readme/diagrams/publishing-es.archify.json) | [Claro](../../assets/readme/diagrams/publishing-es-light.svg) · [Oscuro](../../assets/readme/diagrams/publishing-es-dark.svg) |
| English | [Authorized publication](publishing-en.html) | [Archify JSON](../../assets/readme/diagrams/publishing-en.archify.json) | [Light](../../assets/readme/diagrams/publishing-en-light.svg) · [Dark](../../assets/readme/diagrams/publishing-en-dark.svg) |

Download/open an HTML file locally to use its viewer; GitHub's file viewer displays its source.
Descarga y abre el HTML localmente para usar el visor; GitHub muestra el código del archivo.

## Regeneration

From the repository root, using an installed Archify package:

```sh
node "<ARCHIFY_DIR>/bin/archify.mjs" finalize workflow assets/readme/diagrams/publishing-es.archify.json docs/diagrams/publishing-es.html --repo-root . --quality showcase --json --out-dir .archify/publishing-es-review
node "<ARCHIFY_DIR>/bin/archify.mjs" finalize workflow assets/readme/diagrams/publishing-en.archify.json docs/diagrams/publishing-en.html --repo-root . --quality showcase --json --out-dir .archify/publishing-en-review
```

Each candidate pins its source repository revision and cites the relevant committed code. Update the evidence
when runtime behavior changes. If re-running a candidate at the same HTML path, use a fresh review directory.
Keep delivery/browser receipts locally; they contain machine-specific paths and are not source artifacts.
Export **SVG Light** and **SVG Dark** from each verified HTML viewer to the corresponding README asset paths.
Do not hand-edit rendered diagrams. The HTML and SVG files were regenerated with Archify 3.2.0, passed
automated artifact/browser checks, and the Spanish/English workflow layout was visually reviewed.
