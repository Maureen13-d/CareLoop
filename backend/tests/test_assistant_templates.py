import re

from app.modules.assistant.lexicon import load_barriers, load_safety, load_templates

# Phones are often shared, so approved messages must not carry sensitive words (see ai/templates/lite_en.yaml).
FORBIDDEN = ["cancer", "result", "diagnosis", "positive", "hiv", "screening"]


def test_every_template_fits_one_sms_and_uses_plain_characters():
    for tid, tpl in load_templates().items():
        text = tpl["text"]
        assert len(text) <= 160, f"{tid} is {len(text)} characters"
        assert text.isascii(), f"{tid} has non-ASCII characters"


def test_templates_use_no_sensitive_words():
    for tid, tpl in load_templates().items():
        for word in FORBIDDEN:
            assert not re.search(rf"\b{word}\b", tpl["text"].lower()), f"{tid} contains '{word}'"


def test_every_barrier_flag_and_safety_path_has_a_template():
    templates = load_templates()
    for flag in load_barriers().flags:
        assert f"lite.barrier.{flag}" in templates, flag
    for tid in (
        "safety.crisis",
        "safety.distress",
        "safety.no_diagnosis",
        "safety.symptom",
        "lite.greeting",
        "lite.unclear",
        "lite.request_human",
        "lite.opt_out",
        "lite.clarify",
    ):
        assert tid in templates, tid


def test_every_worry_menu_option_maps_to_a_real_flag():
    lex = load_barriers()
    for choice, flag in lex.worry_menu.items():
        assert flag in lex.flags, (choice, flag)


def test_placeholder_templates_are_marked_so_they_cannot_be_forgotten():
    templates = load_templates()
    assert templates["safety.crisis"]["placeholder"] is True
    assert templates["safety.symptom"]["placeholder"] is True
    for tid, tpl in templates.items():
        if "[" in tpl["text"]:
            assert tpl.get("placeholder") is True, (
                f"{tid} has brackets but is not marked placeholder"
            )


def test_lexicons_have_content():
    assert all(len(p) > 0 for p in load_safety().categories.values())
    assert len(load_barriers().flags) >= 8
