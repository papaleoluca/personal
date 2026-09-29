"""Locate every translatable text unit in the generated spec HTML by exact byte span.

A unit is the inner HTML of a title/h1-h3/p/li/th/td element, or of an SVG <text>.
Spans index the original string, so substitution leaves every other byte untouched.
"""
from html.parser import HTMLParser

UNIT_TAGS = {"title", "h1", "h2", "h3", "p", "li", "th", "td", "text"}
VOID = {"br", "img", "meta", "hr", "input", "link", "col"}


class _Spans(HTMLParser):
    def __init__(self, src):
        super().__init__(convert_charrefs=True)
        self.src = src
        self.line_starts = [0]
        for i, ch in enumerate(src):
            if ch == "\n":
                self.line_starts.append(i + 1)
        self.stack = []  # (tag, inner_start, svg_depth_at_open)
        self.units = []  # (inner_start, inner_end, tag, in_svg)
        self.svg_depth = 0
        self.stray = []  # direct text outside any unit

    def _off(self):
        line, col = self.getpos()
        return self.line_starts[line - 1] + col

    def handle_starttag(self, tag, attrs):
        start = self._off()
        end = start + len(self.get_starttag_text())
        if tag == "svg":
            self.svg_depth += 1
        if tag in VOID:
            return
        self.stack.append((tag, end))

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        start = self._off()
        while self.stack:
            t, inner_start = self.stack.pop()
            if t == tag:
                break
        else:
            raise ValueError(f"unmatched </{tag}> at {start}")
        if tag == "svg":
            self.svg_depth -= 1
        if tag in UNIT_TAGS and not any(t in UNIT_TAGS for t, _ in self.stack):
            self.units.append((inner_start, start, tag, self.svg_depth > 0))

    def handle_data(self, data):
        if data.strip() and not any(t in UNIT_TAGS or t == "style" for t, _ in self.stack):
            self.stray.append((self._off(), data.strip()[:80]))


def find_units(src):
    p = _Spans(src)
    p.feed(src)
    p.close()
    units = sorted(p.units)
    for (a0, a1, *_), (b0, *_ ) in zip(units, units[1:]):
        assert a1 <= b0, "overlapping units"
    return units, p.stray
