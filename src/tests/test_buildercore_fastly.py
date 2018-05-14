from buildercore.terraform import fastly
from . import base

class TestFastlyCustomVCL(base.BaseCase):
    def test_includes_in_template_snippets_that_will_be_expanded_in_place(self):
        snippet = fastly.FastlyVCLSnippet(
            name='do-some-magic',
            content='...',
            type='fetch'
        )
        original_main_vcl = fastly.FastlyVCL.from_string("""
sub vcl_fetch {
  #FASTLY fetch

  if (...) {
    do_something_else()
  }
}
""")
        expected_main_vcl = fastly.FastlyVCL.from_string("""
sub vcl_fetch {
  #FASTLY fetch

  // BEGIN builder do-some-magic
  include "do-some-magic"
  // END builder do-some-magic

  if (...) {
    do_something_else()
  }
}
""")
        self.assertEqual(
            snippet.insert_include(original_main_vcl),
            expected_main_vcl
        )

    def test_stops_generation_if_an_inclusion_section_cannot_be_found(self):
        snippet = fastly.FastlyVCLSnippet(
            name='do-some-magic',
            content='...',
            type='hit'
        )
        original_main_vcl = fastly.FastlyVCL.from_string("""
        sub vcl_fetch {
          ...
        }
        """)
        self.assertRaises(
            fastly.FastlyCustomVCLGenerationError,
            lambda: snippet.insert_include(original_main_vcl),
        )