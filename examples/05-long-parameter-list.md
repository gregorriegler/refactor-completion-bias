# Example 5: Long parameter list

```python
def create_report(title, author, start_date, end_date, include_charts,
                  include_tables, include_summary, include_appendix,
                  format_type, output_path, header_color, footer_color,
                  page_size, language, timezone):
    header = f"# {title}\nby {author} ({language})\n"
    header += f"Period: {start_date} - {end_date} ({timezone})\n"
    body = ""
    if include_summary:
        body += "## Summary\n...\n"
    if include_charts:
        body += "## Charts\n...\n"
    if include_tables:
        body += "## Tables\n...\n"
    if include_appendix:
        body += "## Appendix\n...\n"
    footer = f"<footer style='color:{footer_color}'>{page_size}</footer>"
    doc = header + body + footer
    if format_type == "html":
        doc = f"<html style='color:{header_color}'>{doc}</html>"
    with open(output_path, "w") as f:
        f.write(doc)
```
