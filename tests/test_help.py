import os, sys
from pathlib import Path

os.environ["LANGFUSE_TRACING_ENABLED"] = "false"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import help_pages  # noqa: E402


def test_every_section_has_its_own_link():
    page = help_pages.render("handbook")
    for anchor in ("delivery", "returns", "sale-and-outlet", "late-deliveries-in-peak-season"):
        assert f'id="{anchor}"' in page and f'href="#{anchor}"' in page
    page = help_pages.render("product-guide")
    assert 'id="tromso-coffee-table"' in page and 'id="malmo-sideboard"' in page


def test_the_internal_playbook_is_not_published():
    assert help_pages.render("customer-care-playbook") is None
    assert "playbook" not in help_pages.index().lower()


def test_faq_links_to_handbook_sections_that_exist():
    import re
    faq = help_pages.render("faq")
    handbook = help_pages.render("handbook")
    anchors = set(re.findall(r'href="/help/handbook#([^"]+)"', faq))
    assert anchors and all(f'id="{a}"' in handbook for a in anchors)
