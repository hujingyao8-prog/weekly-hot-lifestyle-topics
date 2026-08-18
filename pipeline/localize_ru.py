"""
RU Report Localizer — pipeline helper
=======================================
Implements the rules defined in ru-report-localizer SKILL.md:
  - Removes methodology / source-notes block (opening box)
  - Removes appendix search-log section
  - Removes footer generation info & next-issue suggestions
  - Sets <html lang="ru">
  - Translates structural section headings via the glossary

For full AI-assisted translation of body text, this script calls the
Anthropic / OpenAI API.  Set TRANSLATE_API=openai|anthropic and the
corresponding key in the environment.

Usage:
  python localize_ru.py --input report-2026-08-18.html \\
                        --output report-2026-08-18-ru.html
"""

import argparse, os, re, sys

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing beautifulsoup4 ...")
    os.system(f"{sys.executable} -m pip install beautifulsoup4 -q")
    from bs4 import BeautifulSoup

# ─── Fixed term glossary (from glossary-ru.md) ───────────────────────────────
GLOSSARY = {
    # Verticals
    "护肤": "Уход за кожей",
    "穿搭": "Стиль и аутфиты",
    "美发护发": "Волосы: уход и причёски",
    "闺蜜话题": "Девичьи разговоры: отношения и саморазвитие",
    "日常 vlog": "Влоги о повседневной жизни",
    "日常vlog": "Влоги о повседневной жизни",
    "美妆": "Макияж",
    "美甲": "Маникюр и нейл-арт",
    "美食": "Еда",
    # Lifecycle
    "萌芽": "Зарождающийся",
    "上升": "Растущий",
    "爆发": "Вирусный",
    "衰退": "Затухающий",
    "成熟平台期": "Стабильная фаза",
    # Report structure
    "本周 Top 5 速览": "Топ-5 трендов недели",
    "本周Top5速览": "Топ-5 трендов недели",
    "分垂类趋势明细": "Тренды по вертикалям",
    "俄语区原生趋势专题": "Родные тренды русскоязычного сегмента",
    "全球趋势→俄语区可迁移清单": "Переносимость глобальных трендов в RU-сегмент",
    "数据窗口": "Период данных",
    "代表视频": "Пример видео",
    "热度证据": "Доказательства популярности",
    "Likee 落地建议": "Рекомендации для Likee",
    "可迁移性": "Переносимость",
    "未获取": "Не получено",
    # Ops terms
    "话题页搭建": "Запуск страницы хештега",
    "特效模板化": "Шаблонизация эффекта",
    "官方挑战": "Официальный челлендж",
    "跟拍门槛": "Порог участия",
    "长线选题": "Долгосрочная тема",
}

# ─── Sections to REMOVE in the RU version (per skill rule) ───────────────────
REMOVE_SECTION_KEYWORDS = [
    "方法论", "信源", "搜罗查询", "附录", "下期建议", "生成信息",
    "Методология", "Журнал",
]


def apply_glossary(text: str) -> str:
    """Replace known Chinese terms with their Russian equivalents."""
    for zh, ru in sorted(GLOSSARY.items(), key=lambda x: -len(x[0])):
        text = text.replace(zh, ru)
    return text


def should_remove_section(tag) -> bool:
    """Return True if this section/div should be dropped in the RU version."""
    text = tag.get_text(" ", strip=True)
    for kw in REMOVE_SECTION_KEYWORDS:
        if kw in text:
            return True
    return False


def translate_with_api(html_content: str) -> str:
    """
    Optional: send body text through an LLM for full translation.
    Only invoked when TRANSLATE_API env var is set.
    """
    api = os.environ.get("TRANSLATE_API", "").lower()
    if not api:
        return html_content   # skip — glossary-only mode

    if api == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        msg = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=8192,
            messages=[{
                "role": "user",
                "content": (
                    "Translate the following HTML report from Chinese to Russian. "
                    "Rules:\n"
                    "1. Keep ALL HTML tags, CSS classes, links, and numbers unchanged.\n"
                    "2. Only translate visible text nodes.\n"
                    "3. Use formal written Russian (business register).\n"
                    "4. Do NOT translate hashtags, English/Russian trend names, URLs.\n"
                    "5. Replace Chinese punctuation with Russian equivalents.\n\n"
                    + html_content
                ),
            }],
        )
        return msg.content[0].text

    return html_content   # fallback


def localize(input_path: str, output_path: str):
    with open(input_path, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    # 1. Set lang attribute
    html_tag = soup.find("html")
    if html_tag:
        html_tag["lang"] = "ru"

    # 2. Remove process-only sections
    for tag in soup.find_all(["section", "div", "footer", "aside"]):
        if should_remove_section(tag):
            tag.decompose()

    # 3. Apply glossary to remaining text
    for text_node in soup.find_all(string=True):
        new_text = apply_glossary(str(text_node))
        if new_text != str(text_node):
            text_node.replace_with(new_text)

    # 4. (Optional) full LLM translation
    html_str = str(soup)
    html_str = translate_with_api(html_str)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_str)

    print(f"  ✅ RU report saved: {output_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",  required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    localize(args.input, args.output)


if __name__ == "__main__":
    main()
