import unittest

from rss_archiveorg.extractors.corporate_email import extract_emails
from rss_archiveorg.extractors.social_media import extract_social_links
from rss_archiveorg.utils import domain_from_url, email_matches_domain


class UtilsTests(unittest.TestCase):
    def test_domain_from_url(self) -> None:
        self.assertEqual(domain_from_url("https://www.example.com/path"), "example.com")

    def test_email_matches_domain(self) -> None:
        self.assertTrue(email_matches_domain("info@example.com", "example.com"))
        self.assertTrue(email_matches_domain("sales@mail.example.com", "example.com"))
        self.assertFalse(email_matches_domain("user@gmail.com", "example.com"))
        self.assertFalse(email_matches_domain("info@other.com", "example.com"))


class SocialMediaTests(unittest.TestCase):
    def test_extract_social_links(self) -> None:
        html = """
        <html><body>
          <a href="https://twitter.com/acme">Twitter</a>
          <a href="https://www.linkedin.com/company/acme">LinkedIn</a>
        </body></html>
        """
        links = extract_social_links(html)
        self.assertIn("twitter", links)
        self.assertIn("linkedin", links)


class CorporateEmailTests(unittest.TestCase):
    def test_extract_corporate_emails_from_mailto_and_text(self) -> None:
        html = """
        <html><body>
          <a href="mailto:contacto@empresa.es">Contacto</a>
          <p>Escríbenos a ventas@empresa.es o info@gmail.com</p>
          <p>soporte [at] empresa [dot] es</p>
        </body></html>
        """
        corporate, all_emails = extract_emails(html, "empresa.es")
        self.assertIn("contacto@empresa.es", corporate)
        self.assertIn("ventas@empresa.es", corporate)
        self.assertIn("soporte@empresa.es", corporate)
        self.assertIn("info@gmail.com", all_emails)
        self.assertNotIn("info@gmail.com", corporate)


if __name__ == "__main__":
    unittest.main()
