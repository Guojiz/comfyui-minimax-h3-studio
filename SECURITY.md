# Security Policy

## Reporting a vulnerability

Open a private GitHub issue on this repository, or email `jizguo@hotmail.com`.
Include the affected file and a minimal reproduction. Do not include live API
keys, auth headers, or credentials in the report.

## Trust boundaries

- The MCP bridge is a local STDIO server for the host agent; treat it as a local
  tool, not a network service.
- A ComfyUI instance is a trust boundary: everything it returns (history,
  artifacts, queue) is untrusted data. The bridge confines local reads from
  server-reported paths to explicitly allowed output roots, blocks redirects to
  other hosts, and caps response/download sizes.
- Workflow and registry JSON are untrusted analysis data. Workflow ids,
  run names, shot/iteration labels, and delivery manifest paths are validated
  to prevent traversal; upload filenames are sanitized before entering
  multipart headers.
- Responses from external services in custom nodes are untrusted: task ids are
  validated, download hosts are allowlisted, and bearer keys are only sent to
  the configured service host.

## Non-goals

This project does not promise automatic content safety, model output filtering,
or protection against prompt injection inherent to video-generation models.
Agent-side creative gates and customer review are the intended controls.
