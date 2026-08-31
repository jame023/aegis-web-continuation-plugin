from __future__ import annotations

import json
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "aegis-web-continuation"
SKILL = PLUGIN / "skills" / "aegis-web-continuation"


class PackageTests(unittest.TestCase):
    def test_plugin_manifest_is_skills_only_and_versioned(self) -> None:
        manifest = json.loads((PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual("aegis-web-continuation", manifest["name"])
        self.assertEqual("1.0.0", manifest["version"])
        self.assertEqual("./skills/", manifest["skills"])
        self.assertNotIn("mcpServers", manifest)
        self.assertNotIn("apps", manifest)

    def test_skill_has_no_scaffold_placeholders_and_declares_real_boundaries(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("[TODO:", text)
        for required in (
            "does not grant GitHub",
            "cannot bypass a ChatGPT/Codex usage limit",
            "BLOCKED_REPO_ACCESS",
            "BLOCKED_STALE_STATE",
            "BLOCKED_SECURITY_CONFLICT",
            "READY_REVIEW",
            "progressive context",
        ):
            self.assertIn(required, text)

    def test_reference_requires_identity_approval_and_verification(self) -> None:
        text = (SKILL / "references" / "security-and-handoff.md").read_text(encoding="utf-8")
        for required in ("Repository/branch/commit", "Mutation Plan", "verification", "Do not auto-merge"):
            self.assertIn(required, text)

    def test_installers_are_preview_first_and_do_not_touch_external_systems(self) -> None:
        installer = (ROOT / "Install-AEGISWebContinuation.ps1").read_text(encoding="utf-8")
        uninstaller = (ROOT / "Uninstall-AEGISWebContinuation.ps1").read_text(encoding="utf-8")
        for script in (installer, uninstaller):
            self.assertIn("[switch]$Apply", script)
            self.assertIn("PREVIEW_ONLY", script)
            self.assertIn("Get-TreeFingerprint", script)
            self.assertNotRegex(script, r"(?i)git\s+(?:commit|push|fetch|pull)")
            self.assertNotRegex(script, r"(?i)\b(?:Invoke-WebRequest|Invoke-RestMethod|curl|wget)\b")
            self.assertNotRegex(script, r"(?i)gh\s+(?:api|auth|repo|secret)")
        self.assertLess(installer.index("if (-not $Apply)"), installer.index("Copy-Item -LiteralPath $sourcePlugin"))
        self.assertIn("aegis-backup", installer)
        self.assertIn("PLUGIN_MODIFIED", uninstaller)

    def test_marketplace_writes_utf8_without_bom(self) -> None:
        for name in ("Install-AEGISWebContinuation.ps1", "Uninstall-AEGISWebContinuation.ps1"):
            script = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn("UTF8Encoding($false)", script)
            self.assertIn("[IO.File]::WriteAllText", script)
            self.assertNotRegex(script, r"Set-Content[^\r\n]+-Encoding\s+UTF8")

    def test_openai_metadata_has_invocation_policy(self) -> None:
        text = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("allow_implicit_invocation: true", text)
        self.assertIn("$aegis-web-continuation", text)

    def test_thai_user_guide_covers_install_mobile_and_fallback(self) -> None:
        text = (ROOT / "docs" / "USER_GUIDE_TH.md").read_text(encoding="utf-8")
        for required in (
            "PREVIEW_ONLY",
            "Install-AEGISWebContinuation.ps1 -Apply",
            "เชื่อม GitHub กับ Codex cloud",
            "สั่งงานจากโทรศัพท์",
            "เมื่อ Codex CLI token/usage หมด",
            "BLOCKED_STALE_STATE",
            "ห้ามอ้างว่า mobile พร้อมใช้งาน",
            "https://learn.chatgpt.com/docs/build-skills",
        ):
            self.assertIn(required, text)
        self.assertNotIn("git add .\n", text)

    def test_visual_assets_and_pdf_are_packaged(self) -> None:
        images = ROOT / "docs" / "images"
        expected = {
            "01-system-overview.svg",
            "02-install-flow.svg",
            "03-mobile-handoff.svg",
            "04-cli-fallback.svg",
        }
        self.assertEqual(expected, {path.name for path in images.glob("*.svg")})
        for name in expected:
            svg = images / name
            root = ET.fromstring(svg.read_text(encoding="utf-8"))
            self.assertTrue(root.tag.endswith("svg"))
            self.assertEqual("1200", root.attrib["width"])
            self.assertEqual("675", root.attrib["height"])
        pdf = ROOT / "output" / "pdf" / "AEGIS-Web-Continuation-Visual-Guide.pdf"
        self.assertTrue(pdf.read_bytes().startswith(b"%PDF"))
        self.assertGreater(pdf.stat().st_size, 100_000)


if __name__ == "__main__":
    unittest.main()
