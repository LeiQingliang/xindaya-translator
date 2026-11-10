"""Offline regression tests for mechanics; no model translation is scored here."""
from __future__ import annotations

from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_script(module_name: str, filename: str):
    spec = importlib.util.spec_from_file_location(module_name, ROOT / "scripts" / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_script("skill_validator", "validate_skill.py")
checker = load_script("translation_guard", "check_translation.py")


class SkillValidatorTests(unittest.TestCase):
    def make_skill(self, folder: Path, body: str = "") -> Path:
        root = folder / "example-skill"
        root.mkdir()
        (root / "SKILL.md").write_text('---\nname: example-skill\ndescription: "Test skill."\n---\n' + body, encoding="utf-8")
        return root

    def test_project_package(self):
        self.assertEqual(validator.validate(ROOT), [])

    def test_minimal_skill_without_repository_files(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(validator.validate(self.make_skill(Path(temp))), [])

    def test_parse_nested_metadata(self):
        values = validator.parse_frontmatter('---\nname: example\ndescription: "Use: translation"\nmetadata:\n  version: "1.2.3"\n---\n')
        self.assertEqual(values["metadata"], {"version": "1.2.3"})

    def test_parse_folded_description(self):
        values = validator.parse_frontmatter("---\nname: example\ndescription: >-\n  Translate content\n  into Chinese.\n---\n")
        self.assertEqual(values["description"], "Translate content into Chinese.")

    def test_duplicate_and_malformed_metadata_rejected(self):
        for body in ('name: a\nname: b', 'name: "unterminated', 'metadata:\n  version: 1.0', 'metadata:\n  version: "1"\n  version: "2"', 'description: [one, two]'):
            with self.subTest(body=body), self.assertRaises(ValueError):
                validator.parse_frontmatter("---\n" + body + "\n---\n")

    def test_broken_reference_transitively_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.make_skill(Path(temp), "[Guide](references/guide.md)")
            (root / "references").mkdir()
            (root / "references/guide.md").write_text("[Missing](absent.md)", encoding="utf-8")
            self.assertTrue(any("absent.md" in issue for issue in validator.validate(root)))

    def test_outside_package_link_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "outside.md").write_text("private", encoding="utf-8")
            root = self.make_skill(Path(temp), "[Outside](../outside.md)")
            self.assertTrue(any("unsafe" in issue for issue in validator.validate(root)))

    def test_link_decodes_path_but_ignores_fragment_and_remote(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.make_skill(Path(temp), '[File](<a%20b.md#intro>) [web](https://example.com/missing)')
            (root / "a b.md").write_text("# Intro", encoding="utf-8")
            self.assertEqual(validator.validate(root), [])

    def test_invalid_fixture_id_does_not_crash(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.make_skill(Path(temp))
            (root / "tests").mkdir()
            (root / "tests/cases.json").write_text('[{"id": []}]', encoding="utf-8")
            self.assertTrue(any("field id" in issue for issue in validator.validate(root)))

    def test_invalid_utf8_is_a_finding(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.make_skill(Path(temp))
            (root / "SKILL.md").write_bytes(b"\xff")
            self.assertTrue(validator.validate(root))

    def test_missing_root_json_exit(self):
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()) as output:
            code = validator.main([str(Path(temp) / "missing"), "--json"])
            self.assertEqual(code, 2)
            self.assertEqual(json.loads(output.getvalue())["status"], "input_error")


class TranslationGuardTests(unittest.TestCase):
    def categories(self, source: str, target: str) -> set[str]:
        return {issue["category"] for issue in checker.compare(source, target)}

    def test_preserved_tokens_pass(self):
        source = 'Run `pip install -r req.txt` at https://example.com/a with {name}; use 12%.'
        target = '请在 https://example.com/a 使用 {name} 运行 `pip install -r req.txt`；数值为12%。'
        self.assertEqual(checker.compare(source, target), [])

    def test_numbers_adjacent_to_chinese_checked(self):
        self.assertEqual(checker.compare("Revenue rose 12%.", "营收增长12%。"), [])
        self.assertIn("numbers", self.categories("Revenue rose 12%.", "营收增长21%。"))

    def test_signed_decimal_and_exponent(self):
        self.assertEqual(checker.compare("Values: -0.5, +4, 1e-3", "数值：-0.5，+4，1e-3"), [])

    def test_duplicate_tokens_are_counted(self):
        self.assertIn("placeholders", self.categories("{name} {name}", "{name}"))

    def test_placeholder_forms(self):
        for value in ("{0}", "{amount:.2f}", "{item!r}", "%1$s", "%(name)s", "${PATH}", "{{key}}"):
            with self.subTest(value=value):
                self.assertIn("placeholders", self.categories("Hello " + value, "你好"))

    def test_nfkc_does_not_hide_protected_changes(self):
        for source, target, category in (("`x = 1`", "`ｘ = １`", "inline_code"), ("{name}", "｛name｝", "placeholders")):
            with self.subTest(source=source):
                self.assertIn(category, self.categories(source, target))

    def test_prose_fullwidth_numbers_allowed(self):
        self.assertEqual(checker.compare("Price: 12%", "价格：１２％"), [])

    def test_markdown_url_punctuation(self):
        self.assertEqual(checker.compare("[Docs](https://example.com/a).", "[文档](https://example.com/a)。"), [])

    def test_balanced_url_parentheses_preserved(self):
        self.assertIn("urls", self.categories("https://example.com/wiki/A_(B)", "https://example.com/wiki/A_(C)"))

    def test_unicode_url_paths_preserved(self):
        self.assertIn("urls", self.categories("https://example.com/甲", "https://example.com/乙"))

    def test_fence_content_and_info_are_checked(self):
        source = "```bash\necho hello\n```\n"
        for target in ("```bash\necho world\n```\n", "```sh\necho hello\n```\n"):
            self.assertIn("fenced_content", self.categories(source, target))

    def test_longer_fence_closer_is_valid(self):
        self.assertEqual(checker.compare("```py\nx = 1\n```\n", "```py\nx = 1\n`````\n"), [])

    def test_shorter_fence_is_content(self):
        self.assertIn("fenced_content", self.categories("````text\n```\n````\n", "````text\nchanged\n````\n"))

    def test_unclosed_fence_is_detected(self):
        self.assertIn("fenced_content", self.categories("~~~sh\necho hi\n~~~\n", "~~~sh\necho hi\n"))

    def test_multi_backtick_span(self):
        self.assertIn("inline_code", self.categories("Use ``echo `hello` ``.", "使用 ``echo `world` ``。"))

    def test_protected_numbers_not_double_reported(self):
        self.assertEqual(self.categories("`value = 1`", "`value = 2`"), {"inline_code"})

    def test_ignoring_numbers_does_not_disable_code(self):
        self.assertEqual(checker.compare("1", "2", skip_numbers=True), [])
        self.assertTrue(checker.compare("`x=1`", "`x=2`", skip_numbers=True))

    def test_newline_conventions_in_fences(self):
        self.assertEqual(checker.compare("```py\r\nx=1\r\n```\r\n", "```py\nx=1\n```\n"), [])


class JsonGuardTests(unittest.TestCase):
    def test_translated_string_values_pass(self):
        self.assertEqual(checker.compare_json({"message": "Hello {name}", "retry": 3}, {"retry": 3, "message": "你好 {name}"}), [])

    def test_changed_keys_and_scalar_types_reported(self):
        self.assertEqual(checker.compare_json({"retry": 3}, {"重试": 3})[0]["category"], "json_keys")
        self.assertEqual(checker.compare_json({"retry": 1}, {"retry": True})[0]["category"], "json_type")

    def test_array_order_and_lengths_checked(self):
        self.assertTrue(checker.compare_json([1, 2], [2, 1]))
        self.assertEqual(checker.compare_json(["a"], ["甲", "乙"])[0]["category"], "json_length")

    def test_tokens_cannot_move_between_fields(self):
        self.assertTrue(checker.compare_json({"a": "Hi {name}", "b": "Welcome"}, {"a": "你好", "b": "欢迎 {name}"}))

    def test_precise_decimals_do_not_round_to_same_value(self):
        source = checker.parse_json('{"ratio":0.123456789123456789}')
        target = checker.parse_json('{"ratio":0.123456789123456788}')
        self.assertEqual(checker.compare_json(source, target)[0]["category"], "json_value")

    def test_decimal_precision_and_signed_zero_checked(self):
        for left, right in (("1.0", "1.00"), ("0", "-0"), ("1", "1.0")):
            with self.subTest(left=left, right=right):
                self.assertTrue(checker.compare_json(checker.parse_json(left), checker.parse_json(right)))

    def test_nonstandard_or_duplicate_json_rejected(self):
        for value in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                checker.parse_json(value)

    def test_ignore_numbers_still_checks_typed_data(self):
        self.assertTrue(checker.compare_json({"count": 1}, {"count": 2}, skip_numbers=True))


class CommandLineTests(unittest.TestCase):
    def run_checker(self, source: bytes, target: bytes, extra: list[str] | None = None):
        with tempfile.TemporaryDirectory() as temp:
            left, right = Path(temp) / "source.txt", Path(temp) / "target.txt"
            left.write_bytes(source)
            right.write_bytes(target)
            with redirect_stdout(io.StringIO()) as output:
                code = checker.main([str(left), str(right), "--json", *(extra or [])])
            return code, json.loads(output.getvalue())

    def test_success_difference_and_input_error_exits(self):
        for left, right, expected in ((b"12", b"12", 0), (b"12", b"13", 1), (b"\xff", b"12", 2)):
            with self.subTest(expected=expected):
                code, report = self.run_checker(left, right)
                self.assertEqual(code, expected)
                self.assertIn("status", report)

    def test_json_mode_parse_error_is_machine_readable(self):
        code, report = self.run_checker(b'{"x":1}', b'{broken}', ["--format", "json"])
        self.assertEqual((code, report["status"]), (2, "input_error"))

    def test_deep_json_is_an_input_error(self):
        nested = b"[" * 2000 + b"0" + b"]" * 2000
        code, report = self.run_checker(nested, nested, ["--format", "json"])
        self.assertEqual((code, report["status"]), (2, "input_error"))

    def test_utf8_bom_accepted(self):
        self.assertEqual(self.run_checker(b"\xef\xbb\xbf12", b"12")[0], 0)


if __name__ == "__main__":
    unittest.main()
