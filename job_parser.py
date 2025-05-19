import html2text

def html_to_notion_blocks(html_text):
    """
    Converts HTML jobDescription into a list of Notion-compatible paragraph blocks.
    """
    md = html2text.html2text(html_text)

    blocks = []
    for line in md.strip().splitlines():
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "type": "text",
                    "text": {
                        "content": line
                    }
                }]
            }
        })

    return blocks

__all__ = ["html_to_notion_blocks"]
