# ─── Export command ───────────────────────────────────────────────────────────
def cmd_export(raw_args: list):
    if not raw_args:
        warn("Usage: devref --export <tool>")
        return

    tool_query, _ = resolve_tool(raw_args)
    header_data = load_header()
    matches = find_tool_keys(tool_query, header_data)
    if not matches:
        warn(f"Tool '{tool_query}' not found.")
        return
    tool_key = matches[0]

    header_entry = header_data[tool_key]
    ref_data     = load_tool_ref(tool_key)

    export_data = {
        "id":          header_entry.get("id"),
        "name":        header_entry.get("name", tool_key),
        "description": header_entry.get("description", ""),
        "tags":        header_entry.get("tags", []),
        "topics":      ref_data.get("topics", {})
    }

    out = DEVREF_DIR / f"{tool_key}_export.json"
    save_json(out, export_data)
    success(f"Exported to: {out}")
