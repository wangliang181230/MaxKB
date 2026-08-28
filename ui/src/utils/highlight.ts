export function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

export function escapeRegExp(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

export function highlightTextHtml(
  text: string,
  keywords: string[] | undefined,
): string {
  const escaped = escapeHtml(text)
  if (!keywords || keywords.length === 0) return escaped
  const pattern = keywords
    .map((k) => escapeRegExp(escapeHtml(k)))
    .filter((k) => k.length > 0)
    .join('|')
  if (!pattern) return escaped
  return escaped.replace(
    new RegExp(`(${pattern})`, 'gi'),
    '<mark class="highlight-keyword">$1</mark>',
  )
}

export function extractKeywords(searchText: string): string[] {
  if (!searchText?.trim()) return []
  let parts: string[]
  if (searchText.includes('&')) {
    parts = searchText.split('&')
  } else if (searchText.includes('|')) {
    parts = searchText.split('|')
  } else {
    parts = [searchText]
  }
  return parts.map((p) => p.trim()).filter((p) => p.length > 0)
}

export function highlightDomTextNodes(
  root: HTMLElement,
  keywords: string[],
): void {
  if (!keywords || keywords.length === 0) return
  const pattern = keywords
    .map((k) => escapeRegExp(k))
    .filter((k) => k.length > 0)
    .join('|')
  if (!pattern) return
  const regex = new RegExp(`(${pattern})`, 'gi')
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null)
  const textNodes: Text[] = []
  let node: Node | null
  while ((node = walker.nextNode())) {
    let parent: Node | null = node.parentNode
    let skip = false
    while (parent && parent !== root) {
      if (
        parent instanceof HTMLElement &&
        (parent.tagName === 'PRE' ||
          parent.tagName === 'CODE' ||
          parent.tagName === 'SCRIPT' ||
          parent.tagName === 'STYLE' ||
          parent.classList.contains('highlight-keyword'))
      ) {
        skip = true
        break
      }
      parent = parent.parentNode
    }
    if (!skip && node.textContent && regex.test(node.textContent)) {
      textNodes.push(node as Text)
    }
    regex.lastIndex = 0
  }
  textNodes.forEach((textNode) => {
    const text = textNode.textContent || ''
    const frag = document.createDocumentFragment()
    let lastIndex = 0
    let match: RegExpExecArray | null
    regex.lastIndex = 0
    while ((match = regex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        frag.appendChild(
          document.createTextNode(text.slice(lastIndex, match.index)),
        )
      }
      const mark = document.createElement('mark')
      mark.className = 'highlight-keyword'
      mark.textContent = match[1]
      frag.appendChild(mark)
      lastIndex = regex.lastIndex
    }
    if (lastIndex < text.length) {
      frag.appendChild(document.createTextNode(text.slice(lastIndex)))
    }
    textNode.parentNode?.replaceChild(frag, textNode)
  })
}
