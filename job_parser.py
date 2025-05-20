from bs4 import BeautifulSoup, NavigableString, Tag

__all__ = ["html_to_notion_blocks"]

def html_to_notion_blocks(html_text):
    """
    Converts jobDescription HTML into a list of Notion-compatible blocks.
    Supports: paragraphs, headings, unordered/ordered lists.
    """
    soup = BeautifulSoup(html_text, "html.parser")
    blocks = []

    MAX_LEN = 2000

    def create_rich_text_chunks(text, base_annotations):
       chunks = []
       text = text.strip()
       while text:
           chunk = text[:MAX_LEN]
           chunks.append({
               "type": "text",
               "text": {"content": chunk},
               "annotations": base_annotations.copy(),
           })
           text = text[MAX_LEN:]
       return chunks
    
    def extract_rich_text_from_element(tag, inherited_annotations=None):
        spans = []

        if inherited_annotations is None:
            inherited_annotations = {
                "bold": False,
                "italic": False,
                "underline": False,
                "code": False,
                "strikethrough": False,
                "color": "default"
            }

        for child in tag.children:
            if isinstance(child, NavigableString):
                text = child.strip()
                if text:
                    chunks = create_rich_text_chunks(text, inherited_annotations)
                    spans.extend(chunks)

            elif isinstance(child, Tag):
                tag_name = child.name.lower()
                child_annotations = inherited_annotations.copy()

                if tag_name in ["b", "strong"]:
                    child_annotations["bold"] = True
                if tag_name in ["i", "em"]:
                    child_annotations["italic"] = True
                if tag_name == "u":
                    child_annotations["underline"] = True
                if tag_name == "code":
                    child_annotations["code"] = True
                if tag_name == "s":
                    child_annotations["strikethrough"] = True

                child_spans = extract_rich_text_from_element(child, child_annotations)
                spans.extend(child_spans)

        return spans

    def walk_and_parse(element):
        # Handle plain text outside tags
        if isinstance(element, NavigableString):
            text = element.strip()
            if text:
                chunks = create_rich_text_chunks(text, {
                    "bold": False, "italic": False, "underline": False,
                    "code": False, "strikethrough": False, "color": "default"
                })
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": chunks
                    }
                })
            return

        # Skip empty or non-visible elements
        if not isinstance(element, Tag) or element.name in ["style", "script"]:
            return
        
        # Extract and handle block tags
        tag = element.name.lower()
        text = element.get_text(strip=True)

        if not text:
            return  # Skip empty content

        rich_text = extract_rich_text_from_element(element)

        if tag in ["h1", "h2", "h3"]:
            block_type = f"heading_{min(int(tag[-1]), 3)}"
            blocks.append({
                "object": "block",
                "type": block_type,
                block_type: {
                    "rich_text": rich_text
                }
            })

        elif tag == "p":
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": rich_text
                }
            })

        elif tag == "li":
            parent = element.find_parent()
            if parent and parent.name == "ul":
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": rich_text
                    }
                })
            elif parent and parent.name == "ol":
                blocks.append({
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {
                        "rich_text": rich_text
                    }
                })

        elif tag in ["ul", "ol"]:
            # Recurse into list items
            for child in element.children:
                walk_and_parse(child)
            return

        else:
            # Recurse into generic containers (div, span, etc.)
            for child in element.children:
                walk_and_parse(child)

    # Begin traversal
    for child in soup.body.children if soup.body else soup.children:
        walk_and_parse(child)

    return blocks
