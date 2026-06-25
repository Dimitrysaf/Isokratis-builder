---
name: Inline AKN <ref> markup syntax
description: How to embed <ref> elements in content/intro/wrapUp fields
---

Users write `{{href|label}}` anywhere in a content/intro/wrapUp/heading field.

Example:
  Βλ. {{/gr/act/2020/4782/ell@/art_5|Ν. 4782/2020 άρθρο 5}} για λεπτομέρειες.

Renders to:
  <p>Βλ. <ref href="/gr/act/2020/4782/ell@/art_5">Ν. 4782/2020 άρθρο 5</ref> για λεπτομέρειες.</p>

**Why:** AKN 3.0 uses mixed content (text + elements) in <p>. lxml's tail attribute handles trailing text after each <ref>. The `_mixed()` helper in xml_renderer.py uses re.split on `_REF_RE` to produce correct lxml mixed content with el.text and ref_el.tail.

**How to apply:** Only implemented in _mixed() → _p(). If other inline-bearing elements (heading, num) ever need refs, extend _mixed() to those callers too. The regex pattern is `\{\{([^|{}\n]+)\|([^|{}\n]+)\}\}`.
